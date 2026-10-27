# Proposal

## Why

Hoje o cadastro de pessoas não possui um lugar estruturado para armazenar telefones e e-mails: a API só expõe endereços. Sem contatos, o sistema não consegue registrar os canais de comunicação de cada pessoa nem distinguir qual telefone deve ser usado como principal.

## What Changes

- Criar o app Django `contatos`, seguindo o padrão do app `enderecos`, com o model `Contato` na tabela `contatos`.
- Usar snake_case em todos os campos da nova tabela (`pessoa_id`, `tipo_telefone`, `telefone`, `email`, `observacao`, `contato_principal`) e nos nomes expostos pela API.
- Campos do contato:
  - `pessoa`: chave estrangeira para `Pessoa` (coluna `pessoa_id`), com exclusão em cascata.
  - `tipo_telefone`: enum com `CELULAR`, `RESIDENCIAL` e `COMERCIAL`.
  - `telefone`: opcional, permitindo contatos somente com e-mail.
  - `contato_principal`: booleano, padrão `true`.
  - `email`: opcional, validado como e-mail.
  - `observacao`: texto livre opcional.
- Garantir, no banco e na API, no máximo um contato principal por pessoa.
- Ao criar ou atualizar um contato como principal, desmarcar automaticamente o principal anterior da mesma pessoa na mesma transação.
- Permitir vários contatos da mesma pessoa com o mesmo `tipo_telefone` (sem unicidade por pessoa + tipo).
- Expor a criação de contatos em `POST /api/pessoas/{uuid}/contatos/` e manter listagem, consulta, atualização e exclusão em `/api/contatos/`, com filtros por pessoa, UUID da pessoa, tipo de telefone e indicador de principal. A rota plana `POST /api/contatos/` fica desabilitada.
- Incluir os contatos na resposta de detalhe da pessoa (`GET /api/pessoas/{uuid}/`).
- Retornar os dados da pessoa junto da listagem aninhada (`GET /api/pessoas/{uuid}/contatos/`), além dos contatos paginados.
- Registrar o app em `INSTALLED_APPS` e as rotas no router da API.

## Capabilities

### New Capabilities

- `contatos`: gerenciamento dos contatos (telefone, e-mail e observação) vinculados a uma pessoa, incluindo a regra de contato principal único e a promoção automática de um novo principal.

### Modified Capabilities

Nenhuma. O projeto ainda não possui specs em `openspec/specs/`.

## Impact

- **Novo app**: `contatos/` (`models.py`, `serializers.py`, `views.py`, `filters.py`, `migrations/0001_initial.py`, `tests.py`).
- **Configuração**: `sao_pedro/settings.py` (`INSTALLED_APPS`) e `sao_pedro/urls.py` (registro do `ContatoViewSet`).
- **Banco**: nova tabela `contatos`, com FK para `pessoas` e constraint parcial de principal único por pessoa; requer migração.
- **API**: criação em `POST /api/pessoas/{uuid}/contatos/`; listagem, detalhe, atualização e exclusão em `/api/contatos/` e `/api/contatos/{id}/`; autenticação e paginação herdadas das configurações globais do DRF.
- **Sem quebra de contrato**: endpoints e models existentes de pessoas e endereços permanecem inalterados.
