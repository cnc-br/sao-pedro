from rest_framework import serializers

from contatos.serializers import ContatoSerializer
from enderecos.serializers import EnderecoSerializer
from .models import Pessoa


class PessoaInfoSerializer(serializers.ModelSerializer):
    enderecos = EnderecoSerializer(many=True, read_only=True)

    class Meta:
        model = Pessoa
        fields = [
            "id",
            "uuid",
            "nome",
            "conhecidoPor",
            "cpf",
            "dataNascimento",
            "sexo",
            "estadoCivil",
            "escolaridade",
            "nacionalidade",
            "foto",
            "enderecos",
            "ativo",
        ]


class PessoaSerializer(PessoaInfoSerializer):
    contatos = ContatoSerializer(many=True, read_only=True)

    class Meta(PessoaInfoSerializer.Meta):
        fields = PessoaInfoSerializer.Meta.fields + ["contatos"]

    def validate_cpf(self, value):
        """
        Garante que o CPF seja único apenas se preenchido.
        """
        if value:
            qs = Pessoa.objects.filter(cpf=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "Este CPF já está cadastrado.")
        return value
