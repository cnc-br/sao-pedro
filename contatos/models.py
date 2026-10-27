from django.db import models
from django.db.models import Q

from pessoas.models import Pessoa


class Contato(models.Model):
    TIPO_TELEFONE_CHOICES = [
        ("CELULAR", "Celular"),
        ("RESIDENCIAL", "Residencial"),
        ("COMERCIAL", "Comercial"),
    ]

    pessoa = models.ForeignKey(
        Pessoa, on_delete=models.CASCADE, related_name="contatos")
    tipo_telefone = models.CharField(
        max_length=11,
        choices=TIPO_TELEFONE_CHOICES,
        blank=True,
        null=True,
    )
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    observacao = models.TextField(blank=True, null=True)
    contato_principal = models.BooleanField(default=True)

    def __str__(self):
        canal = self.telefone or self.email or "sem canal"
        return f"{self.pessoa.nome} - {canal}"

    class Meta:
        db_table = "contatos"
        constraints = [
            models.UniqueConstraint(
                fields=["pessoa"],
                condition=Q(contato_principal=True),
                name="unique_contato_principal_por_pessoa",
            )
        ]
