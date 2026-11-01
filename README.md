# São Pedro — Serviço Central de Identidade, Autenticação e Pessoas

Módulo central de autenticação, emissão de tokens JWT e gestão de dados pessoais (em conformidade com a LGPD) do ecossistema **CNC-Gestão**.

---

## 1. Visão Geral

O **São Pedro** é a autoridade central de identidade do ecossistema:
- **Autenticação**: Emissão e validação de tokens JWT (`SimpleJWT`) com claims curtos de acesso e rotação de refresh token.
- **Base de Pessoas e Contatos**: Fonte única da verdade para dados civis, contatos e endereços de fiéis cadastrados no Caminho Neocatecumenal.
- **Isolamento de Dados (LGPD)**: Em produção, opera exclusivamente dentro do schema `saopedro` no banco unificado `db_gestao` (`PostgreSQL 17`), com permissões restritas e RBAC.

---

## 2. Stack Tecnológica

- **Linguagem**: Python 3.12+
- **Framework Web**: Django 5.2 & Django REST Framework (DRF)
- **Autenticação**: `djangorestframework-simplejwt`
- **Banco de Dados**: PostgreSQL 17 (schema `saopedro`)
- **Filtros e Paginação**: `django-filter` e paginação personalizada
- **Servidor em Produção**: Gunicorn / PM2 sob Nginx (rota `/auth/`)

---

## 3. Instalação e Execução Local

### Opção A: Execução Local com Python Virtualenv

1. **Criar e ativar o ambiente virtual**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Instalar dependências**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variáveis de ambiente**:
   ```bash
   cp .env.example .env
   # Ajuste os valores em .env conforme seu ambiente local
   ```

4. **Aplicar Migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Iniciar o servidor de desenvolvimento**:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

### Opção B: Execução via Docker e Makefile

1. **Iniciar os serviços de banco e infra Docker**:
   ```bash
   docker compose up -d --remove-orphans
   ```

2. **Executar a aplicação via Make**:
   ```bash
   make run
   ```

---

## 4. Testes Automatizados (TDD)

O projeto adota o ciclo estrito de TDD. Todos os testes devem passar antes de qualquer commit:

```bash
# Executar todos os testes
python manage.py test

# Verificar se não há migrations pendentes
python manage.py makemigrations --check --dry-run
```

---

## 5. Endpoints Principais

| Método | Rota Local | Rota em Produção (Nginx) | Descrição |
| :--- | :--- | :--- | :--- |
| `GET` | `/health/` | `/auth/health/` | Endpoint de verificação de saúde da aplicação e banco |
| `GET` | `/api/health/` | `/auth/api/health/` | Health check da API REST |
| `POST` | `/api/token/` | `/auth/api/token/` | Obtenção de Access Token e Refresh Token JWT |
| `POST` | `/api/token/refresh/` | `/auth/api/token/refresh/` | Rotação e renovação de token JWT |
| `GET/POST`| `/api/pessoas/` | `/auth/api/pessoas/` | Gestão de pessoas cadastradas (requer JWT) |

---

## 6. Documentação da API: Pessoas e Contatos

### 6.1 Pessoas
Cadastro de pessoas. O detalhe `GET /api/pessoas/{uuid}/` inclui a lista de `contatos` da pessoa, além dos `enderecos`.

### 6.2 Contatos
Cada pessoa pode ter vários contatos de telefone e e-mail, armazenados na tabela `contatos`. Todos os campos usam `snake_case`.

#### Endpoints
- `GET /api/pessoas/{uuid}/contatos/` — lista paginada dos contatos da pessoa, com os dados da pessoa no campo `pessoa`
- `POST /api/pessoas/{uuid}/contatos/` — cria um contato para a pessoa identificada pelo UUID
- `GET /api/contatos/` — lista paginada de contatos
- `GET /api/contatos/{id}/` — detalha um contato
- `PUT /api/contatos/{id}/` — atualiza um contato
- `PATCH /api/contatos/{id}/` — atualiza parcialmente um contato
- `DELETE /api/contatos/{id}/` — exclui um contato

> [!NOTE]
> A criação é feita somente pela rota aninhada da pessoa; `POST /api/contatos/` responde `405 Method Not Allowed`.
> Todos os endpoints exigem autenticação JWT (`Authorization: Bearer <token>`).

#### Payload de Exemplo
```json
{
  "tipo_telefone": "CELULAR",
  "telefone": "11999999999",
  "contato_principal": true,
  "email": "pessoa@example.com",
  "observacao": "Prefere contato por WhatsApp"
}
```

A pessoa é identificada pelo `uuid` na URL de criação; `pessoa_id` não precisa ser enviado e, se enviado, é ignorado. A resposta inclui `pessoa_id` com o ID interno da pessoa.

Campos:
- `tipo_telefone`: `CELULAR`, `RESIDENCIAL` ou `COMERCIAL`; obrigatório quando `telefone` é informado.
- `telefone`: opcional, até 20 caracteres.
- `email`: opcional e validado como e-mail.
- `observacao`: opcional.
- `contato_principal`: booleano, padrão `true`.

#### Contato Principal
Cada pessoa tem no máximo um contato com `contato_principal: true`, garantido por constraint no banco. Ao criar um contato como principal — inclusive quando o campo é omitido, por causa do padrão `true` — ou ao promover um contato existente, o principal anterior é desmarcado automaticamente na mesma transação.

Para criar um contato secundário sem rebaixar o principal atual, envie explicitamente `"contato_principal": false`.

#### Filtros da Listagem
- `pessoa_id`: ID interno da pessoa.
- `pessoa_uuid`: UUID da pessoa.
- `tipo_telefone`: tipo do telefone.
- `contato_principal`: `true` ou `false`.

Exemplo:
```text
GET /api/contatos/?pessoa_uuid=<uuid>&contato_principal=true
```

#### Retorno com Dados da Pessoa
`GET /api/pessoas/{uuid}/contatos/` retorna os contatos da pessoa e inclui o objeto `pessoa` no nível raiz:
```json
{
  "server": "http://localhost:8000/api/pessoas/<uuid>/contatos/",
  "total": 2,
  "page": 1,
  "limit": 50,
  "data": [
    {
      "id": 1,
      "pessoa_id": 10,
      "tipo_telefone": "CELULAR",
      "telefone": "11999999999",
      "contato_principal": true,
      "email": "pessoa@example.com",
      "observacao": null
    }
  ],
  "pessoa": {
    "id": 10,
    "uuid": "<uuid>",
    "nome": "Pessoa Um",
    "enderecos": []
  }
}
```

---

## 7. Governança e Regras de Agentes IA

Consulte as diretrizes arquiteturais e de DevSecOps centralizadas em:
- [AGENTS.md](AGENTS.md)
- [SPEC 004: Diretrizes do São Pedro](https://github.com/cnc-br/gestao-devsecops/blob/main/specs/004-identidade-saopedro/SPEC.md)
- [Regras de IA no gestao-devsecops](https://github.com/cnc-br/gestao-devsecops)
