from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from pessoas.filters import PessoaFilter
from .models import Pessoa
from .serializers import PessoaSerializer


class PessoaViewSet(viewsets.ModelViewSet):
    queryset = Pessoa.objects.prefetch_related(
        "enderecos", "contatos").order_by("-id")
    serializer_class = PessoaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PessoaFilter
    lookup_field = 'uuid'
