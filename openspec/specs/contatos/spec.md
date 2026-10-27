# contatos Specification

## Purpose

Permitir que cada pessoa tenha múltiplos contatos de telefone e e-mail, com no máximo um contato principal por pessoa, usado como canal preferencial.

## Requirements

### Requirement: CRUD de contatos vinculados a uma pessoa

A API SHALL criar contatos por `POST /api/pessoas/{uuid}/contatos/` e SHALL listar, consultar, atualizar e excluir contatos por `/api/contatos/`. Todo contato MUST referenciar uma pessoa existente; a criação MUST obter a pessoa pelo `uuid` da URL e MUST rejeitar um UUID inexistente com `404 Not Found`. A exclusão da pessoa SHALL excluir em cascata os seus contatos. A rota `POST /api/contatos/` MUST NOT criar contatos.

#### Scenario: Criar contato para pessoa existente

- **WHEN** um cliente autenticado envia `POST /api/pessoas/{uuid}/contatos/` com o UUID de uma pessoa existente e os demais dados do contato
- **THEN** a API responde `201 Created` com o contato criado, incluindo o `id` e o `pessoa_id`, e o contato passa a aparecer em `GET /api/contatos/`

#### Scenario: UUID da rota prevalece sobre pessoa_id do corpo

- **WHEN** um cliente envia `POST /api/pessoas/{uuid}/contatos/` com um `pessoa_id` diferente no corpo
- **THEN** o contato é criado para a pessoa identificada pelo `uuid` da URL

#### Scenario: Rejeitar pessoa inexistente

- **WHEN** um cliente envia `POST /api/pessoas/{uuid}/contatos/` com um UUID que não existe
- **THEN** a API responde `404 Not Found` e nenhum contato é criado

#### Scenario: Rota plana de criação desabilitada

- **WHEN** um cliente envia `POST /api/contatos/`
- **THEN** a API responde `405 Method Not Allowed` e nenhum contato é criado

#### Scenario: Exclusão em cascata ao remover a pessoa

- **WHEN** uma pessoa que possui contatos é excluída
- **THEN** todos os contatos dessa pessoa são excluídos e deixam de ser retornados por `GET /api/contatos/`

### Requirement: Canais de contato

Cada contato SHALL aceitar `telefone` e `email` opcionais e `observacao` opcional. O contato MUST conter pelo menos um entre `telefone` e `email`. Quando informado, o `email` MUST ser um endereço de e-mail válido.

#### Scenario: Contato somente com e-mail

- **WHEN** um cliente cria um contato com `email` preenchido, sem `telefone`
- **THEN** a API responde `201 Created` e persiste o contato com `telefone` nulo

#### Scenario: Rejeitar contato sem canal

- **WHEN** um cliente tenta criar ou atualizar um contato deixando `telefone` e `email` vazios
- **THEN** a API responde `400 Bad Request` e não persiste a alteração

#### Scenario: Rejeitar e-mail inválido

- **WHEN** um cliente envia um `email` com formato inválido
- **THEN** a API responde `400 Bad Request` com erro no campo `email`

#### Scenario: Persistir observação

- **WHEN** um cliente cria um contato com `observacao` preenchida
- **THEN** a resposta e as consultas posteriores retornam a mesma observação

### Requirement: Tipo de telefone

`tipo_telefone` SHALL aceitar somente os valores `CELULAR`, `RESIDENCIAL` e `COMERCIAL`. O campo MUST ser informado quando `telefone` estiver preenchido e MUST ficar vazio quando não houver `telefone`. Uma pessoa PODE ter vários contatos com o mesmo `tipo_telefone`.

#### Scenario: Permitir tipos repetidos para a mesma pessoa

- **WHEN** um cliente cria dois contatos para a mesma pessoa, ambos com `tipo_telefone` igual a `CELULAR`
- **THEN** a API responde `201 Created` nos dois pedidos e mantém os dois contatos

#### Scenario: Exigir tipo quando há telefone

- **WHEN** um cliente envia um contato com `telefone` preenchido e sem `tipo_telefone`
- **THEN** a API responde `400 Bad Request` com erro no campo `tipo_telefone`

#### Scenario: Rejeitar tipo inválido

- **WHEN** um cliente envia `tipo_telefone` com valor diferente de `CELULAR`, `RESIDENCIAL` ou `COMERCIAL`
- **THEN** a API responde `400 Bad Request` com erro no campo `tipo_telefone`

### Requirement: Contato principal único por pessoa

Cada pessoa SHALL ter no máximo um contato com `contato_principal` verdadeiro. O campo `contato_principal` SHALL ser booleano e ter valor padrão `true`. O banco de dados MUST impedir a existência de dois contatos principais para a mesma pessoa.

#### Scenario: Primeiro contato nasce principal

- **WHEN** um cliente cria o primeiro contato de uma pessoa sem informar `contato_principal`
- **THEN** o contato é criado com `contato_principal` igual a `true`

#### Scenario: Banco impede dois principais simultâneos

- **WHEN** uma operação tenta gravar dois contatos com `contato_principal` verdadeiro para a mesma pessoa sem passar pela regra de promoção
- **THEN** a constraint do banco rejeita a gravação e apenas um contato permanece principal

### Requirement: Promoção automática a contato principal

Ao criar um contato com `contato_principal` verdadeiro, ou ao atualizar um contato para `contato_principal` verdadeiro, a API MUST desmarcar o principal anterior da mesma pessoa e persistir o novo principal na mesma transação. Uma atualização que não altere `contato_principal` MUST NOT desmarcar o principal atual.

#### Scenario: Novo principal desmarca o anterior

- **WHEN** uma pessoa já possui um contato principal e um cliente cria outro contato com `contato_principal` igual a `true`
- **THEN** o contato anterior passa a ter `contato_principal` igual a `false` e o novo contato fica principal

#### Scenario: Atualização promove contato existente

- **WHEN** um cliente envia `PATCH /api/contatos/{id}/` com `contato_principal` igual a `true` para um contato secundário
- **THEN** o principal anterior da mesma pessoa passa a `false` e o contato atualizado fica principal

#### Scenario: Atualização sem tocar no indicador preserva o principal

- **WHEN** um cliente atualiza apenas `observacao` de um contato principal sem enviar `contato_principal`
- **THEN** o contato continua principal e nenhum outro contato é alterado

#### Scenario: Permitir pessoa sem principal

- **WHEN** um cliente envia `PATCH /api/contatos/{id}/` com `contato_principal` igual a `false` para o único contato principal da pessoa
- **THEN** a API responde `200 OK` e a pessoa passa a não ter contato principal

### Requirement: Consulta e filtros de contatos

A API SHALL expor `GET /api/contatos/` e `GET /api/contatos/{id}/` com autenticação obrigatória e paginação padrão do projeto. A listagem SHALL permitir filtrar por `pessoa_id`, `pessoa_uuid`, `tipo_telefone` e `contato_principal`.

#### Scenario: Filtrar por pessoa

- **WHEN** um cliente consulta `GET /api/contatos/?pessoa_id=<id>` para uma pessoa com contatos
- **THEN** a resposta contém somente contatos daquela pessoa

#### Scenario: Filtrar por UUID da pessoa

- **WHEN** um cliente consulta `GET /api/contatos/?pessoa_uuid=<uuid>` com o UUID de uma pessoa
- **THEN** a resposta contém somente contatos daquela pessoa

#### Scenario: Filtrar por principal

- **WHEN** um cliente consulta `GET /api/contatos/?contato_principal=true`
- **THEN** a resposta contém somente contatos marcados como principais

#### Scenario: Exigir autenticação

- **WHEN** um cliente não autenticado consulta `GET /api/contatos/`
- **THEN** a API responde `401 Unauthorized`

### Requirement: Detalhe da pessoa inclui contatos

A resposta de `GET /api/pessoas/{uuid}/` SHALL incluir o campo `contatos` com todos os contatos da pessoa, mantendo os demais campos e a lista de `enderecos`.

#### Scenario: Pessoa com contatos

- **WHEN** um cliente consulta `GET /api/pessoas/{uuid}/` de uma pessoa que possui contatos
- **THEN** a resposta `200 OK` inclui a lista `contatos` com os dados dos contatos da pessoa

#### Scenario: Pessoa sem contatos

- **WHEN** um cliente consulta `GET /api/pessoas/{uuid}/` de uma pessoa sem contatos
- **THEN** a resposta `200 OK` inclui `contatos` como lista vazia

### Requirement: Consulta aninhada de contatos com dados da pessoa

`GET /api/pessoas/{uuid}/contatos/` SHALL listar paginadamente os contatos da pessoa e SHALL incluir um objeto `pessoa` com seus dados cadastrais no nível raiz da resposta. UUID inexistente MUST retornar `404 Not Found`. A listagem aninhada SHALL aceitar os mesmos filtros da coleção plana.

#### Scenario: Listar contatos com dados da pessoa

- **WHEN** um cliente autenticado consulta `GET /api/pessoas/{uuid}/contatos/`
- **THEN** a resposta `200 OK` contém o objeto `pessoa`, o total e somente os contatos daquela pessoa no campo `data`

#### Scenario: UUID inexistente na listagem aninhada

- **WHEN** um cliente consulta `GET /api/pessoas/{uuid}/contatos/` com um UUID que não existe
- **THEN** a API responde `404 Not Found`

#### Scenario: Filtrar contatos na rota aninhada

- **WHEN** um cliente consulta `GET /api/pessoas/{uuid}/contatos/?tipo_telefone=CELULAR`
- **THEN** a resposta contém somente os contatos da pessoa com o tipo informado

### Requirement: Representação do contato na API

As respostas de contato SHALL incluir `id`, `pessoa_id`, `tipo_telefone`, `telefone`, `contato_principal`, `email` e `observacao`. Os campos opcionais não preenchidos SHALL ser retornados como `null`.

#### Scenario: Resposta completa do contato

- **WHEN** um cliente consulta `GET /api/contatos/{id}/` de um contato existente
- **THEN** a resposta `200 OK` contém todos os campos da representação, com `null` nos opcionais vazios
