import uuid
from django.db import models
from django.db.models import Q


class Pessoa(models.Model):
    SEXO_CHOICES = [
        ("M", "Masculino"),
        ("F", "Feminino"),
    ]

    ESTADO_CIVIL_CHOICES = [
        ("S", "Solteiro"),
        ("C", "Casado"),
        ("D", "Divorciado"),
        ("V", "Viúvo"),
        ("N", "Não Informado"),
    ]

    ESCOLARIDADE = [
        ('nao_informado', 'Não informado'),
        ('analfabeto', 'Analfabeto'),
        ('fundamental', 'Ensino Fundamental'),
        ('fundamental_incompleto', 'Ensino Fundamental Incompleto'),
        ('medio', 'Ensino Médio'),
        ('medio_incompleto', 'Ensino Médio Incompleto'),
        ('superior', 'Ensino Superior'),
        ('superior_incompleto', 'Ensino Superior Incompleto'),
        ('pos_graduacao', 'Pós-Graduação'),
        ('mestrado', 'Mestrado'),
        ('doutorado', 'Doutorado'),
        ('pos_doutorado', 'Pós-Doutorado'),
    ]

    uuid = models.UUIDField(unique=True, editable=False,
                            auto_created=True, db_index=True, default=uuid.uuid4)
    nome = models.CharField(max_length=150)
    conhecidoPor = models.CharField(max_length=100, blank=True, null=True)
    cpf = models.CharField(max_length=11, blank=True, null=True)
    dataNascimento = models.DateField(blank=True, null=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    estadoCivil = models.CharField(max_length=1, choices=ESTADO_CIVIL_CHOICES)
    escolaridade = models.CharField(
        max_length=30, choices=ESCOLARIDADE, blank=True, null=True)
    nacionalidade = models.CharField(max_length=100, blank=True, null=True)
    foto = models.CharField(max_length=255, blank=True, null=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

    class Meta:
        db_table = "pessoas"
        constraints = [
            models.UniqueConstraint(
                fields=["cpf"],
                condition=~Q(cpf=""),
                name="unique_cpf_when_filled"
            )
        ]
