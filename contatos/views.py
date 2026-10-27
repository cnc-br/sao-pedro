from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, viewsets
from rest_framework.response import Response

from pessoas.models import Pessoa
from pessoas.serializers import PessoaInfoSerializer

from .filters import ContatoFilter
from .models import Contato
from .serializers import ContatoSerializer


class ContatoViewSet(viewsets.ModelViewSet):
    queryset = Contato.objects.select_related("pessoa").order_by("-id")
    serializer_class = ContatoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ContatoFilter
    http_method_names = ["get", "put", "patch", "delete", "head", "options"]


class PessoaContatoView(generics.ListCreateAPIView):
    serializer_class = ContatoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ContatoFilter

    def get_pessoa(self):
        if not hasattr(self, "_pessoa"):
            self._pessoa = get_object_or_404(
                Pessoa, uuid=self.kwargs["uuid"])
        return self._pessoa

    def get_queryset(self):
        return (
            Contato.objects.filter(pessoa=self.get_pessoa())
            .select_related("pessoa")
            .order_by("-id")
        )

    def list(self, request, *args, **kwargs):
        pessoa = self.get_pessoa()
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data["pessoa"] = PessoaInfoSerializer(pessoa).data
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "pessoa": PessoaInfoSerializer(pessoa).data,
            "data": serializer.data,
        })

    def create(self, request, *args, **kwargs):
        dados = request.data.copy()
        dados["pessoa_id"] = self.get_pessoa().pk

        serializer = self.get_serializer(data=dados)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )
