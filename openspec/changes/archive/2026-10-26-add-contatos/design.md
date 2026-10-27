# Design

## Context

Ver `proposal.md` para motivação. O projeto é uma API Django REST Framework com apps por domínio (`pessoas`, `enderecos`, `health`). O app `enderecos` já estabelece o padrão de app satélite com FK para `Pessoa`, `ModelViewSet`, serializer e registro no `DefaultRouter`. A tabela `pessoas` é gerenciada pelo app `pessoas`; não há specs existentes em `openspec/specs/`.

Restrições relevantes do código atual:

- `Pessoa` usa `uuid` como `lookup_field` na API, mas a PK interna continua numérica.
- Campos de `Pessoa` usam camelCase (`conhecidoPor`, `dataNascimento`), enquanto `Endereco` usa snake_case.
- Autenticação JWT e paginação customizada são globais (`REST_FRAMEWORK`), portanto herdadas por qualquer novo viewset.
- O banco é PostgreSQL (via `DATABASE_URL`) com `search_path=saopedro`.

## Goals / Non-Goals

**Goals:**

- Adicionar o domínio de contatos com model, serializer, filtros, viewset e rota, seguindo o padrão de `enderecos`.
- Garantir a invariante "no máximo um principal por pessoa" tanto na API quanto no banco.
- Manter o contrato de API explícito e em snake_case: `pessoa_id`, `tipo_telefone`, `telefone`, `contato_principal`, `email`, `observacao`.

**Non-Goals:**

- UI HTML/templates, admin Django ou frontend.
- Aninhar contatos em operações de escrita de `Pessoa`; o campo `contatos` é somente leitura.
- Unicidade de telefone ou e-mail (a mesma pessoa pode repetir tipo e número; pessoas diferentes podem compartilhar e-mail).
- Migração ou alteração de dados existentes.
- Endpoint específico para "definir principal"; a promoção acontece no create/update do próprio contato.

## Decisions

### Nov app `contatos`, não model dentro de `pessoas`

Criar `contatos/` com `apps.py`, `models.py`, `serializers.py`, `views.py`, `filters.py`, `migrations/` e `tests.py`.

**Por quê:** replica a separação já usada por `enderecos`, mantém `pessoas` focado no cadastro principal e evita import circular (o app novo importa `Pessoa`; `pessoas` não importa `contatos`).

**Alternativa descartada:** colocar `Contato` em `pessoas/models.py`. Menos arquivos, porém mistura domínios e diverge do padrão do repositório.

### Nomenclatura snake_case na nova tabela

Todos os campos do model `Contato`, as colunas da tabela `contatos` e os nomes expostos pela API MUST usar snake_case: `pessoa_id`, `tipo_telefone`, `telefone`, `email`, `observacao`, `contato_principal`.

**Por quê:** a nova tabela segue o padrão já usado por `Endereco` e evita a mistura de convenções que existe em `Pessoa` (campos legados em camelCase). `Pessoa` e `Endereco` não são alterados.

**Alternativa descartada:** manter `contatoPrincipal` por ser o nome usado no pedido original. Foi descartado para padronizar toda a nova tabela e o contrato da API em snake_case.

### Model `Contato`

- `pessoa = ForeignKey(Pessoa, on_delete=CASCADE, related_name="contatos")` → coluna `pessoa_id`, atendendo ao nome de campo pedido sem abandonar a convenção Django de FK.
- `tipo_telefone = CharField(max_length=11, choices=..., blank=True, null=True)` com `CELULAR`, `RESIDENCIAL`, `COMERCIAL`.
- `telefone = CharField(max_length=20, blank=True, null=True)`.
- `email = EmailField(blank=True, null=True)`.
- `observacao = TextField(blank=True, null=True)`.
- `contato_principal = BooleanField(default=True)`.
- `db_table = "contatos"`, `__str__` com pessoa e canal.

`tipo_telefone` fica opcional no banco porque contatos somente de e-mail não têm tipo; a obrigatoriedade condicional é validada na API (ver abaixo).

### Constraint parcial de principal único

```python
models.UniqueConstraint(
    fields=["pessoa"],
    condition=Q(contato_principal=True),
    name="unique_contato_principal_por_pessoa",
)
```

**Por quê:** a regra é "no máximo um `true` por pessoa", não "um registro por pessoa". A constraint parcial permite vários contatos secundários e protege contra escritas fora da API (shell, scripts, admin futuro).

**Alternativa descartada:** `unique_together = ("pessoa", "contato_principal")`. Isso limitaria cada pessoa a um único secundário, contrariando o requisito de múltiplos contatos.

### Promoção automática no serializer, em transação com lock

No `ContatoSerializer.create` e `.update`, dentro de `transaction.atomic()`:

1. Obter a pessoa do `validated_data` (ou da instância, no update).
2. Executar `Pessoa.objects.select_for_update().get(pk=pessoa.pk)` para serializar alterações concorrentes de principal da mesma pessoa.
3. Se `contato_principal` for verdadeiro, executar `Contato.objects.filter(pessoa=pessoa, contato_principal=True).exclude(pk=instance.pk).update(contato_principal=False)`.
4. Salvar o contato.

**Por quê:** o comportamento é uma regra de aplicação (desmarcar o anterior + gravar o novo), e o serializer é o ponto por onde passam create/update da API. O lock na linha da pessoa evita que duas requisições concorrentes promovam contatos diferentes e colidam na constraint.

**Alternativa descartada:** sobrescrever `Contato.save()`. Funcionaria em qualquer caller, mas esconderia efeitos colaterais de escrita, dificultaria testes e não teria o `Pessoa` disponível de forma explícita. A constraint no banco continua como rede de segurança.

### Default `true` sem desmarcar em PATCH parcial

`contato_principal` tem `default=True` no model e no serializer. No `create`, o valor chega em `validated_data` e a promoção roda. No `PATCH` que não envia o campo, `validated_data` não contém `contato_principal`, então nenhum outro contato é alterado. No `PUT`, o cliente deve enviar o campo (comportamento padrão do DRF para campos obrigatórios); se enviar `true`, a promoção roda.

Consequência aceita: criar um segundo contato sem informar `contato_principal` torna-o principal e rebaixa o anterior. Isso segue a decisão do usuário e o default solicitado, mas deve ser documentado no README/PR para o cliente da API.

### Validação condicional dos canais

No `ContatoSerializer.validate`, considerando a instância em updates parciais:

- Pelo menos um entre `telefone` e `email` deve estar preenchido; caso contrário, erro de validação.
- Se `telefone` estiver preenchido, `tipo_telefone` é obrigatório.
- Se `telefone` estiver vazio, `tipo_telefone` deve ser nulo/vazio.
- Strings vazias são normalizadas para `None` antes da validação, para que `""` não conte como preenchido.
- `email` usa `EmailField`, que já valida o formato; não há unicidade.

**Por quê:** manter a API coerente com a decisão de permitir contato somente com e-mail, sem gravar registros sem nenhum canal.

### Criação aninhada na pessoa

A criação de contato acontece em `POST /api/pessoas/{uuid}/contatos/`, atendida por `PessoaContatoView` no app `contatos`. A view resolve a pessoa pelo `uuid`, injeta o `pessoa_id` correspondente nos dados e usa o mesmo `ContatoSerializer`; qualquer `pessoa_id` enviado no corpo é sobrescrito. UUID inexistente retorna `404`.

As demais operações continuam na coleção plana: `GET /api/contatos/`, `GET /api/contatos/{id}/`, `PUT`, `PATCH` e `DELETE`. O `ContatoViewSet` não aceita `POST` (`405`), para que exista um único caminho de criação.

**Por quê:** a rota aninhada expressa a posse do contato pela pessoa, usa o UUID que já é o identificador público de `Pessoa` e evita que o cliente escolha uma pessoa divergente no corpo.

**Alternativa descartada:** manter `POST /api/contatos/` exigindo `pessoa_id` no corpo. Foi descartado por duplicar a identificação da pessoa e permitir divergência entre URL e payload.

### Contatos nas respostas de pessoa

`PessoaSerializer` passa a incluir `contatos` como lista somente leitura, serializada pelo `ContatoSerializer`. A base `PessoaInfoSerializer` mantém os dados cadastrais e `enderecos` sem `contatos`, evitando recursão e duplicação na resposta aninhada de contatos.

`GET /api/pessoas/{uuid}/contatos/` usa `PessoaContatoView`, que resolve a pessoa pelo UUID, filtra os contatos por ela, aplica a paginação e os mesmos filtros da coleção plana, e acrescenta o objeto `pessoa` (via `PessoaInfoSerializer`) ao envelope paginado. O `POST` no mesmo endpoint reutiliza a lógica de criação aninhada.

**Por quê:** o consumidor que já tem o UUID da pessoa passa a obter os contatos e o cadastro em uma única chamada, sem duplicar o objeto `pessoa` dentro de cada contato.

**Alternativa descartada:** retornar `pessoa` dentro de cada item de contato. Foi descartado por repetir o mesmo objeto em todas as linhas e aumentar a resposta sem ganho de informação.

### Contrato da API

- Criação: `POST /api/pessoas/{uuid}/contatos/`; o corpo não precisa de `pessoa_id` e um valor enviado é ignorado.
- Detalhe da pessoa: `GET /api/pessoas/{uuid}/` inclui `contatos` (somente leitura), além de `enderecos`.
- Listagem aninhada: `GET /api/pessoas/{uuid}/contatos/` retorna o envelope paginado (`server`, `total`, `page`, `limit`, `data`) acrescido de `pessoa`.
- Model FK: `pessoa`; campo serializado: `pessoa_id` (`PrimaryKeyRelatedField(source="pessoa", queryset=Pessoa.objects.all())`).
- Payload/resposta: `id`, `pessoa_id`, `tipo_telefone`, `telefone`, `contato_principal`, `email`, `observacao`.
- Listagem/detalhe/atualização/exclusão: `api/contatos/` e `api/contatos/{id}/` (PK numérica; o UUID continua sendo o identificador de `Pessoa`). A tabela chama-se `contatos` (plural); o app, a rota e o `related_name` também usam `contatos`.
- Viewset: `ContatoViewSet(viewsets.ModelViewSet)` com `http_method_names` sem `post`, `queryset = Contato.objects.select_related("pessoa").order_by("-id")`, `DjangoFilterBackend`, `filterset_class = ContatoFilter`.
- Filtros: `pessoa_id` → `pessoa_id`; `pessoa_uuid` → `pessoa__uuid`; `tipo_telefone` com as choices; `contato_principal` booleano.

**Por quê:** `pessoa_id` foi o nome pedido explicitamente; expor o UUID da pessoa como filtro mantém compatibilidade com o lookup usado em `/api/pessoas/{uuid}/`.

### Testes

Usar `APITestCase` em `contatos/tests.py`, cobrindo: criação pela rota aninhada, UUID inexistente, `POST` plano retornando `405`, `GET` aninhado com dados da pessoa, detalhe de pessoa com contatos, criação com e sem telefone, validação de canal vazio, e-mail inválido, tipo obrigatório/ inválido, múltiplos contatos do mesmo tipo, default principal, promoção no create e no PATCH, preservação em PATCH sem o campo, constraint do banco, filtros e cascata ao excluir pessoa. Autenticação nos testes via `force_authenticate` para isolar a regra de contatos do fluxo JWT.

## Risks / Trade-offs

- **Default `true` rebaixa silenciosamente o principal anterior** → comportamento intencional; documentar no README e garantir teste explícito. Clientes que queiram criar secundário devem enviar `contato_principal: false`.
- **Concorrência na promoção** → lock em `Pessoa` dentro da transação; constraint parcial como última barreira. Sob PostgreSQL o lock serializa as promoções da mesma pessoa.
- **Constraint parcial depende de suporte a índices parciais** → PostgreSQL (banco do projeto) e SQLite (testes) suportam; não há suporte no MySQL, que não é usado.
- **`select_for_update` em testes SQLite é no-op** → o teste de concorrência real fica limitado; a constraint e os testes sequenciais continuam válidos.
- **Mudança de contrato na criação** → `POST /api/contatos/` deixa de existir e responde `405`; clientes devem migrar para `POST /api/pessoas/{uuid}/contatos/`, que dispensa `pessoa_id` no corpo.
- **Respostas de pessoa maiores** → o detalhe e a listagem aninhada carregam contatos; o `PessoaViewSet` usa `prefetch_related("enderecos", "contatos")` para reduzir consultas. Em pessoas com muitos contatos, a resposta cresce proporcionalmente.
- **Padrão misto no projeto legado** → a nova tabela e a API de contatos usam snake_case; os campos camelCase de `Pessoa` permanecem inalterados para não quebrar o contrato existente.
- **Sem unicidade de telefone/e-mail** → duplicatas são permitidas por decisão de escopo; se necessário no futuro, vira outra mudança de spec.

## Migration Plan

1. Criar o app `contatos` e adicionar `'contatos'` a `INSTALLED_APPS`.
2. Rodar `python manage.py makemigrations contatos` e revisar a migração (tabela `contatos`, FK, choices e constraint parcial).
3. Rodar `python manage.py migrate` (cria apenas a nova tabela; não altera `pessoas` ou `enderecos`).
4. Registrar `ContatoViewSet` no router de `sao_pedro/urls.py` e implantar a API.
5. Rollback: reverter o deploy do código e rodar `python manage.py migrate contatos zero` para remover a tabela. Como a mudança é aditiva, não há perda de dados de pessoas/endereços.

## Open Questions

Nenhuma.
