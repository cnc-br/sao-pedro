import django_filters

from .models import Contato


class ContatoFilter(django_filters.FilterSet):
    pessoa_id = django_filters.NumberFilter(field_name="pessoa")
    pessoa_uuid = django_filters.UUIDFilter(field_name="pessoa__uuid")
    tipo_telefone = django_filters.ChoiceFilter(
        choices=Contato.TIPO_TELEFONE_CHOICES)
    contato_principal = django_filters.BooleanFilter(
        field_name="contato_principal")

    class Meta:
        model = Contato
        fields = [
            "pessoa_id",
            "pessoa_uuid",
            "tipo_telefone",
            "contato_principal",
        ]
