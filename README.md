# São Pedro
API de Pessoas

## Pessoas
Cadastro de pessoas. O detalhe `GET /api/pessoas/{uuid}/` inclui a lista de `contatos` da pessoa, além dos `enderecos`.

## Contatos

Cada pessoa pode ter vários contatos de telefone e e-mail, armazenados na tabela `contatos`. Todos os campos usam snake_case.

### Endpoints

- `GET /api/pessoas/{uuid}/contatos/` — lista paginada dos contatos da pessoa, com os dados da pessoa no campo `pessoa`
- `POST /api/pessoas/{uuid}/contatos/` — cria um contato para a pessoa identificada pelo UUID
- `GET /api/contatos/` — lista paginada de contatos
- `GET /api/contatos/{id}/` — detalha um contato
- `PUT /api/contatos/{id}/` — atualiza um contato
- `PATCH /api/contatos/{id}/` — atualiza parcialmente um contato
- `DELETE /api/contatos/{id}/` — exclui um contato

A criação é feita somente pela rota aninhada da pessoa; `POST /api/contatos/` responde `405 Method Not Allowed`.

Todos exigem autenticação JWT (`Authorization: Bearer <token>`).

### Payload

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

- `tipo_telefone` — `CELULAR`, `RESIDENCIAL` ou `COMERCIAL`; obrigatório quando `telefone` é informado e deve ficar vazio quando não há telefone.
- `telefone` — opcional, até 20 caracteres.
- `email` — opcional e validado como e-mail.
- `observacao` — opcional.
- `contato_principal` — booleano, padrão `true`.

O contato precisa ter pelo menos `telefone` ou `email`.

### Contato principal

Cada pessoa tem no máximo um contato com `contato_principal: true`, garantido por constraint no banco. Ao criar um contato como principal — inclusive quando o campo é omitido, por causa do padrão `true` — ou ao promover um contato existente, o principal anterior é desmarcado automaticamente na mesma transação.

Para criar um contato secundário sem rebaixar o principal atual, envie explicitamente `"contato_principal": false`.

### Filtros da listagem

- `pessoa_id` — ID interno da pessoa.
- `pessoa_uuid` — UUID da pessoa.
- `tipo_telefone` — tipo do telefone.
- `contato_principal` — `true` ou `false`.

Exemplo:

```text
GET /api/contatos/?pessoa_uuid=<uuid>&contato_principal=true
```

A resposta segue a paginação padrão da API: `server`, `total`, `page`, `limit` e `data`.

### Contatos com dados da pessoa

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

O endpoint aceita os mesmos filtros da listagem plana. UUID inexistente retorna `404`.