# Tasks

## 1. Estrutura do app e configuração

- [x] 1.1 Criar o app `contatos` com `python manage.py startapp contatos` e verificar que `contatos/apps.py`, `models.py`, `views.py` e `migrations/` existem
- [x] 1.2 Adicionar `'contatos'` a `INSTALLED_APPS` em `sao_pedro/settings.py` e verificar com `python manage.py check` que não há erros de configuração

## 2. Model e migração

- [x] 2.1 Implementar `Contato` em `contatos/models.py` com todos os campos em snake_case — FK `pessoa` (CASCADE, `related_name="contatos"`), `tipo_telefone` com choices `CELULAR`/`RESIDENCIAL`/`COMERCIAL`, `telefone`, `email`, `observacao` e `contato_principal` default `True` —, `db_table="contatos"` e constraint parcial `unique_contato_principal_por_pessoa`; verificar com `python manage.py makemigrations contatos --dry-run` que a migração é detectada
- [x] 2.2 Gerar as migrações `contatos/migrations/0001_initial.py` e `0002_alter_contato_table.py`, revisar a FK, as choices, a `UniqueConstraint` com `condition` e o nome final da tabela (`contatos`), e verificar com `python manage.py migrate` que a tabela é criada
- [x] 2.3 Adicionar testes de model em `contatos/tests.py` para o default `contato_principal=True`, persistência dos campos opcionais e rejeição de dois principais para a mesma pessoa pela constraint; verificar com `python manage.py test contatos -v 2`

## 3. Serializer, validações e regra de principal

- [x] 3.1 Implementar `ContatoSerializer` expondo `id`, `pessoa_id` (`source="pessoa"`), `tipo_telefone`, `telefone`, `contato_principal`, `email` e `observacao`; verificar com um teste de criação que a resposta contém esses campos e `null` nos opcionais vazios
- [x] 3.2 Implementar a validação condicional: pelo menos um entre `telefone` e `email`, e-mail válido, `tipo_telefone` obrigatório quando há `telefone` e vazio quando não há, normalizando strings vazias para `None`; verificar com testes de `400` para contato sem canal, e-mail inválido, tipo ausente e tipo inválido
- [x] 3.3 Implementar a promoção automática em `ContatoSerializer.create`/`update` com `transaction.atomic()` e `select_for_update` na `Pessoa`, desmarcando o principal anterior; verificar com testes de criação do segundo contato como principal, promoção via `PATCH` e preservação do principal em `PATCH` que não envia `contato_principal`
- [x] 3.4 Adicionar teste garantindo que dois contatos da mesma pessoa com o mesmo `tipo_telefone` são aceitos; verificar com `python manage.py test contatos -v 2`

## 4. Filtros, viewset e rotas

- [x] 4.1 Implementar `ContatoFilter` em `contatos/filters.py` com `pessoa_id`, `pessoa_uuid` (`pessoa__uuid`), `tipo_telefone` e `contato_principal`; verificar com testes de listagem filtrando por cada parâmetro
- [x] 4.2 Implementar `ContatoViewSet` em `contatos/views.py` com queryset ordenado por `-id`, `select_related("pessoa")`, `DjangoFilterBackend` e `filterset_class`, exceto `POST` (criação fica na rota aninhada); verificar com testes de CRUD completo (`POST` aninhado, `GET`, `PUT`/`PATCH`, `DELETE`) em `/api/contatos/`
- [x] 4.3 Registrar `ContatoViewSet` no `DefaultRouter` em `sao_pedro/urls.py` como `r"contatos"` e verificar que `GET /api/contatos/` autenticado responde `200` e sem autenticação responde `401`
- [x] 4.4 Adicionar teste de exclusão em cascata: excluir a pessoa remove seus contatos de `GET /api/contatos/`; verificar com `python manage.py test contatos -v 2`

## 5. Documentação e verificação final

- [x] 5.1 Documentar no `README.md` os endpoints de contatos, o payload aceito, os filtros e o comportamento de `contato_principal` default `true` rebaixando o principal anterior; verificar que os exemplos usam os mesmos nomes de campo e rotas implementados
- [x] 5.2 Rodar a suíte completa com `python manage.py test` e verificar que todos os testes passam, incluindo os testes existentes de pessoas e endereços
- [x] 5.3 Rodar `openspec validate add-contatos --strict` e verificar que o change está válido

## 6. Rota aninhada de criação

- [x] 6.1 Implementar `PessoaContatoView` em `contatos/views.py` resolvendo a pessoa pelo UUID da URL e ignorando `pessoa_id` do corpo; verificar com teste de criação aninhada e de UUID inexistente (`404`)
- [x] 6.2 Registrar `POST /api/pessoas/{uuid}/contatos/` em `sao_pedro/urls.py` e desabilitar `POST /api/contatos/` com `405`; verificar com testes de rota, autenticação e CRUD
- [x] 6.3 Atualizar o `README.md` com a rota aninhada de criação e o payload sem `pessoa_id`; verificar que os exemplos correspondem às rotas implementadas
- [x] 6.4 Rodar a suíte completa e `openspec validate add-contatos --strict`; verificar que todos os testes e a validação passam
- [x] 6.5 Manter `db_table="contatos"` e a migração `0002_alter_contato_table.py`; verificar nas bases local e de teste que a tabela se chama `contatos`

## 7. Contatos nas respostas de pessoa

- [x] 7.1 Adicionar `contatos` como lista somente leitura em `PessoaSerializer`; verificar com teste de `GET /api/pessoas/{uuid}/` contendo os contatos
- [x] 7.2 Criar `PessoaInfoSerializer` sem `contatos` para reutilização na listagem aninhada; verificar que o objeto `pessoa` da resposta não duplica a lista de contatos
- [x] 7.3 Estender `PessoaContatoView` para `GET`, com paginação, filtros e objeto `pessoa` no nível raiz; verificar com testes de listagem aninhada, `404` e autenticação
- [x] 7.4 Atualizar README, spec e design; rodar a suíte completa e `openspec validate add-contatos --strict`
