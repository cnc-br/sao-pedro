from django.db import transaction
from rest_framework import serializers

from pessoas.models import Pessoa

from .models import Contato


class ContatoSerializer(serializers.ModelSerializer):
    pessoa_id = serializers.PrimaryKeyRelatedField(
        source="pessoa",
        queryset=Pessoa.objects.all(),
    )

    class Meta:
        model = Contato
        fields = [
            "id",
            "pessoa_id",
            "tipo_telefone",
            "telefone",
            "contato_principal",
            "email",
            "observacao",
        ]

    def to_internal_value(self, data):
        data = data.copy()
        for field in ("telefone", "email", "observacao", "tipo_telefone"):
            if field in data and isinstance(data[field], str) and not data[field].strip():
                data[field] = None
        return super().to_internal_value(data)

    def validate(self, attrs):
        telefone = attrs.get("telefone", getattr(self.instance, "telefone", None))
        email = attrs.get("email", getattr(self.instance, "email", None))
        tipo_telefone = attrs.get(
            "tipo_telefone", getattr(self.instance, "tipo_telefone", None))

        if isinstance(telefone, str):
            telefone = telefone.strip()
        if isinstance(email, str):
            email = email.strip()
        if isinstance(tipo_telefone, str):
            tipo_telefone = tipo_telefone.strip()

        if not telefone and not email:
            raise serializers.ValidationError(
                "Informe pelo menos telefone ou email.")

        if telefone and not tipo_telefone:
            raise serializers.ValidationError({
                "tipo_telefone": "O tipo de telefone é obrigatório quando há telefone."
            })

        if not telefone and tipo_telefone:
            raise serializers.ValidationError({
                "tipo_telefone": "O tipo de telefone deve ficar vazio quando não há telefone."
            })

        for field, value in (
            ("telefone", telefone),
            ("email", email),
            ("tipo_telefone", tipo_telefone),
        ):
            if field in attrs:
                attrs[field] = value

        return attrs

    def create(self, validated_data):
        pessoa = validated_data["pessoa"]
        contato_principal = validated_data.get("contato_principal", True)

        with transaction.atomic():
            Pessoa.objects.select_for_update().get(pk=pessoa.pk)
            if contato_principal:
                Contato.objects.filter(
                    pessoa=pessoa, contato_principal=True
                ).update(contato_principal=False)
            return Contato.objects.create(**validated_data)

    def update(self, instance, validated_data):
        pessoa = validated_data.get("pessoa", instance.pessoa)
        mudou_de_pessoa = pessoa.pk != instance.pessoa_id
        principal_final = validated_data.get(
            "contato_principal", instance.contato_principal)
        deve_promover = validated_data.get(
            "contato_principal") is True or (mudou_de_pessoa and principal_final)

        with transaction.atomic():
            Pessoa.objects.select_for_update().get(pk=pessoa.pk)
            if deve_promover:
                Contato.objects.filter(
                    pessoa=pessoa, contato_principal=True
                ).exclude(pk=instance.pk).update(contato_principal=False)

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
