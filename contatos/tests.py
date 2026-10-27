import uuid

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APITestCase

from pessoas.models import Pessoa

from .models import Contato
from .serializers import ContatoSerializer


class ContatoModelTests(TestCase):
    def setUp(self):
        self.pessoa = Pessoa.objects.create(
            nome="Pessoa de Teste",
            sexo="M",
            estadoCivil="S",
        )

    def test_contato_principal_default_true(self):
        contato = Contato.objects.create(
            pessoa=self.pessoa,
            tipo_telefone="CELULAR",
            telefone="11999999999",
        )

        self.assertTrue(contato.contato_principal)

    def test_campos_opcionais_persistidos(self):
        contato = Contato.objects.create(
            pessoa=self.pessoa,
            email="pessoa@example.com",
            observacao="Contato somente por e-mail",
        )
        contato.refresh_from_db()

        self.assertEqual(contato.email, "pessoa@example.com")
        self.assertEqual(contato.observacao, "Contato somente por e-mail")
        self.assertIsNone(contato.telefone)
        self.assertIsNone(contato.tipo_telefone)

    def test_constraint_impede_dois_principais_por_pessoa(self):
        Contato.objects.create(
            pessoa=self.pessoa,
            tipo_telefone="CELULAR",
            telefone="11999999999",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Contato.objects.create(
                    pessoa=self.pessoa,
                    tipo_telefone="RESIDENCIAL",
                    telefone="1133334444",
                )

        self.assertEqual(
            Contato.objects.filter(
                pessoa=self.pessoa, contato_principal=True).count(),
            1,
        )


class ContatoSerializerTests(TestCase):
    def setUp(self):
        self.pessoa = Pessoa.objects.create(
            nome="Pessoa de Teste",
            sexo="F",
            estadoCivil="S",
        )

    def _salvar(self, **dados):
        dados.setdefault("pessoa_id", self.pessoa.pk)
        serializer = ContatoSerializer(data=dados)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        return serializer.save(), serializer

    def test_criacao_expoe_campos_e_nulos(self):
        contato, serializer = self._salvar(email="pessoa@example.com")

        self.assertEqual(
            serializer.data,
            {
                "id": contato.pk,
                "pessoa_id": self.pessoa.pk,
                "tipo_telefone": None,
                "telefone": None,
                "contato_principal": True,
                "email": "pessoa@example.com",
                "observacao": None,
            },
        )

    def test_rejeita_contato_sem_canal(self):
        serializer = ContatoSerializer(
            data={"pessoa_id": self.pessoa.pk, "observacao": "Sem canal"})

        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_rejeita_email_invalido(self):
        serializer = ContatoSerializer(
            data={"pessoa_id": self.pessoa.pk, "email": "email-invalido"})

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_exige_tipo_quando_ha_telefone(self):
        serializer = ContatoSerializer(
            data={"pessoa_id": self.pessoa.pk, "telefone": "11999999999"})

        self.assertFalse(serializer.is_valid())
        self.assertIn("tipo_telefone", serializer.errors)

    def test_rejeita_tipo_invalido(self):
        serializer = ContatoSerializer(
            data={
                "pessoa_id": self.pessoa.pk,
                "telefone": "11999999999",
                "tipo_telefone": "FIXO",
            },
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("tipo_telefone", serializer.errors)

    def test_rejeita_tipo_sem_telefone(self):
        serializer = ContatoSerializer(
            data={
                "pessoa_id": self.pessoa.pk,
                "email": "pessoa@example.com",
                "tipo_telefone": "CELULAR",
            },
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("tipo_telefone", serializer.errors)

    def test_normaliza_strings_vazias_para_nulo(self):
        contato, _ = self._salvar(
            telefone="   ",
            email="pessoa@example.com",
            tipo_telefone="",
            observacao="",
        )

        self.assertIsNone(contato.telefone)
        self.assertIsNone(contato.tipo_telefone)
        self.assertIsNone(contato.observacao)

    def test_criacao_promove_novo_principal(self):
        anterior, _ = self._salvar(
            tipo_telefone="CELULAR", telefone="11999999999")
        novo, _ = self._salvar(
            tipo_telefone="RESIDENCIAL", telefone="1133334444")

        anterior.refresh_from_db()
        self.assertFalse(anterior.contato_principal)
        self.assertTrue(novo.contato_principal)

    def test_patch_promove_contato_existente(self):
        anterior, _ = self._salvar(
            tipo_telefone="CELULAR", telefone="11999999999")
        secundario, _ = self._salvar(
            tipo_telefone="RESIDENCIAL",
            telefone="1133334444",
            contato_principal=False,
        )

        serializer = ContatoSerializer(
            secundario, data={"contato_principal": True}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        anterior.refresh_from_db()
        secundario.refresh_from_db()
        self.assertFalse(anterior.contato_principal)
        self.assertTrue(secundario.contato_principal)

    def test_patch_sem_indicador_preserva_principal(self):
        principal, _ = self._salvar(
            tipo_telefone="CELULAR", telefone="11999999999")
        secundario, _ = self._salvar(
            tipo_telefone="RESIDENCIAL",
            telefone="1133334444",
            contato_principal=False,
        )

        serializer = ContatoSerializer(
            principal, data={"observacao": "Atualizado"}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        principal.refresh_from_db()
        secundario.refresh_from_db()
        self.assertTrue(principal.contato_principal)
        self.assertFalse(secundario.contato_principal)

    def test_permite_pessoa_sem_principal(self):
        principal, _ = self._salvar(
            tipo_telefone="CELULAR", telefone="11999999999")

        serializer = ContatoSerializer(
            principal, data={"contato_principal": False}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        principal.refresh_from_db()

        self.assertFalse(principal.contato_principal)

    def test_permite_tipos_repetidos_para_mesma_pessoa(self):
        primeiro, _ = self._salvar(
            tipo_telefone="CELULAR", telefone="11999999999")
        segundo, _ = self._salvar(
            tipo_telefone="CELULAR",
            telefone="11888888888",
            contato_principal=False,
        )

        self.assertEqual(primeiro.tipo_telefone, segundo.tipo_telefone)
        self.assertEqual(
            Contato.objects.filter(pessoa=self.pessoa,
                                   tipo_telefone="CELULAR").count(),
            2,
        )


class ContatoAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="teste", password="teste123")
        self.client.force_authenticate(user=self.user)
        self.pessoa = Pessoa.objects.create(
            nome="Pessoa Um", sexo="M", estadoCivil="S")
        self.outra_pessoa = Pessoa.objects.create(
            nome="Pessoa Dois", sexo="F", estadoCivil="C")
        self.url = "/api/contatos/"

    def _url_criacao(self, pessoa=None):
        return f"/api/pessoas/{(pessoa or self.pessoa).uuid}/contatos/"

    def _criar(self, pessoa=None, **dados):
        dados.pop("pessoa_id", None)
        response = self.client.post(
            self._url_criacao(pessoa), dados, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        return response

    def test_cria_e_lista_contato(self):
        response = self._criar(
            tipo_telefone="CELULAR", telefone="11999999999")

        self.assertEqual(response.data["pessoa_id"], self.pessoa.pk)
        self.assertEqual(response.data["tipo_telefone"], "CELULAR")
        self.assertEqual(response.data["telefone"], "11999999999")
        self.assertTrue(response.data["contato_principal"])
        self.assertIsNone(response.data["email"])
        self.assertIsNone(response.data["observacao"])

        listagem = self.client.get(self.url)
        self.assertEqual(listagem.status_code, 200)
        self.assertEqual(listagem.data["total"], 1)
        self.assertEqual(listagem.data["data"][0]["id"], response.data["id"])

    def test_detalhe_pessoa_inclui_contatos(self):
        criado = self._criar(
            tipo_telefone="CELULAR", telefone="11999999999")

        response = self.client.get(f"/api/pessoas/{self.pessoa.uuid}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["contatos"]), 1)
        self.assertEqual(
            response.data["contatos"][0]["id"], criado.data["id"])
        self.assertEqual(
            response.data["contatos"][0]["telefone"], "11999999999")

    def test_lista_aninhada_traz_pessoa_e_contatos(self):
        primeiro = self._criar(
            tipo_telefone="CELULAR", telefone="11999999999")
        segundo = self._criar(
            tipo_telefone="RESIDENCIAL",
            telefone="1133334444",
            contato_principal=False,
        )
        self._criar(
            self.outra_pessoa,
            tipo_telefone="COMERCIAL",
            telefone="1144445555",
        )

        response = self.client.get(self._url_criacao())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pessoa"]["uuid"], str(self.pessoa.uuid))
        self.assertEqual(response.data["pessoa"]["nome"], self.pessoa.nome)
        self.assertNotIn("contatos", response.data["pessoa"])
        self.assertEqual(response.data["total"], 2)
        self.assertEqual(
            {item["id"] for item in response.data["data"]},
            {primeiro.data["id"], segundo.data["id"]},
        )

    def test_lista_aninhada_de_pessoa_inexistente(self):
        response = self.client.get(
            f"/api/pessoas/{uuid.uuid4()}/contatos/")

        self.assertEqual(response.status_code, 404)

    def test_criacao_usa_uuid_da_rota_e_ignora_pessoa_id_do_corpo(self):
        response = self.client.post(
            self._url_criacao(self.pessoa),
            {
                "pessoa_id": self.outra_pessoa.pk,
                "email": "pessoa@example.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["pessoa_id"], self.pessoa.pk)
        self.assertEqual(
            Contato.objects.get(pk=response.data["id"]).pessoa, self.pessoa)

    def test_rejeita_pessoa_inexistente(self):
        response = self.client.post(
            f"/api/pessoas/{uuid.uuid4()}/contatos/",
            {"email": "pessoa@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Contato.objects.count(), 0)

    def test_rota_plana_de_criacao_desabilitada(self):
        response = self.client.post(
            self.url,
            {
                "pessoa_id": self.pessoa.pk,
                "email": "pessoa@example.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 405)

    def test_autenticacao_obrigatoria(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        criacao = self.client.post(
            self._url_criacao(),
            {"email": "pessoa@example.com"},
            format="json",
        )
        listagem_aninhada = self.client.get(self._url_criacao())

        self.assertEqual(response.status_code, 401)
        self.assertEqual(criacao.status_code, 401)
        self.assertEqual(listagem_aninhada.status_code, 401)

    def test_crud_completo(self):
        criado = self._criar(email="pessoa@example.com")
        detalhe_url = f"{self.url}{criado.data['id']}/"

        detalhe = self.client.get(detalhe_url)
        self.assertEqual(detalhe.status_code, 200)
        self.assertIsNone(detalhe.data["telefone"])
        self.assertIsNone(detalhe.data["tipo_telefone"])

        patch = self.client.patch(
            detalhe_url, {"observacao": "Atualizado"}, format="json")
        self.assertEqual(patch.status_code, 200)
        self.assertEqual(patch.data["observacao"], "Atualizado")

        put = self.client.put(
            detalhe_url,
            {
                "pessoa_id": self.pessoa.pk,
                "email": "pessoa@example.com",
                "telefone": None,
                "tipo_telefone": None,
                "contato_principal": False,
                "observacao": "Via PUT",
            },
            format="json",
        )
        self.assertEqual(put.status_code, 200, put.data)
        self.assertFalse(put.data["contato_principal"])
        self.assertEqual(put.data["observacao"], "Via PUT")

        delete = self.client.delete(detalhe_url)
        self.assertEqual(delete.status_code, 204)
        self.assertEqual(self.client.get(detalhe_url).status_code, 404)

    def test_filtros(self):
        primeiro = self._criar(
            tipo_telefone="CELULAR", telefone="11999999999")
        segundo = self._criar(
            tipo_telefone="RESIDENCIAL",
            telefone="1133334444",
            contato_principal=False,
        )
        terceiro = self._criar(
            self.outra_pessoa,
            tipo_telefone="COMERCIAL",
            telefone="1144445555",
        )

        por_pessoa = self.client.get(
            self.url, {"pessoa_id": self.pessoa.pk})
        self.assertEqual(por_pessoa.data["total"], 2)
        self.assertEqual(
            {item["id"] for item in por_pessoa.data["data"]},
            {primeiro.data["id"], segundo.data["id"]},
        )

        por_uuid = self.client.get(
            self.url, {"pessoa_uuid": str(self.pessoa.uuid)})
        self.assertEqual(por_uuid.data["total"], 2)

        por_tipo = self.client.get(self.url, {"tipo_telefone": "CELULAR"})
        self.assertEqual(por_tipo.data["total"], 1)
        self.assertEqual(por_tipo.data["data"][0]["id"], primeiro.data["id"])

        principais = self.client.get(
            self.url, {"contato_principal": "true"})
        self.assertEqual(principais.data["total"], 2)
        self.assertEqual(
            {item["id"] for item in principais.data["data"]},
            {primeiro.data["id"], terceiro.data["id"]},
        )

        secundarios = self.client.get(
            self.url, {"contato_principal": "false"})
        self.assertEqual(secundarios.data["total"], 1)
        self.assertEqual(secundarios.data["data"][0]["id"], segundo.data["id"])

    def test_patch_promove_contato_existente(self):
        principal = self._criar(
            tipo_telefone="CELULAR", telefone="11999999999")
        secundario = self._criar(
            tipo_telefone="RESIDENCIAL",
            telefone="1133334444",
            contato_principal=False,
        )

        response = self.client.patch(
            f"{self.url}{secundario.data['id']}/",
            {"contato_principal": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        principal_obj = Contato.objects.get(pk=principal.data["id"])
        secundario_obj = Contato.objects.get(pk=secundario.data["id"])
        self.assertFalse(principal_obj.contato_principal)
        self.assertTrue(secundario_obj.contato_principal)

    def test_patch_sem_indicador_preserva_principal(self):
        principal = self._criar(
            tipo_telefone="CELULAR", telefone="11999999999")
        self._criar(
            tipo_telefone="RESIDENCIAL",
            telefone="1133334444",
            contato_principal=False,
        )

        response = self.client.patch(
            f"{self.url}{principal.data['id']}/",
            {"observacao": "Somente observação"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["contato_principal"])

    def test_exclusao_em_cascata(self):
        self._criar(tipo_telefone="CELULAR", telefone="11999999999")
        self._criar(
            self.outra_pessoa,
            tipo_telefone="RESIDENCIAL",
            telefone="1133334444",
        )

        self.pessoa.delete()

        response = self.client.get(self.url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(
            response.data["data"][0]["pessoa_id"], self.outra_pessoa.pk)

    def test_permite_tipos_repetidos(self):
        self._criar(tipo_telefone="CELULAR", telefone="11999999999")
        response = self._criar(
            tipo_telefone="CELULAR",
            telefone="11888888888",
            contato_principal=False,
        )

        self.assertEqual(response.data["tipo_telefone"], "CELULAR")
        self.assertEqual(
            Contato.objects.filter(
                pessoa=self.pessoa, tipo_telefone="CELULAR").count(),
            2,
        )
