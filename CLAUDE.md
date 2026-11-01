# CLAUDE.md — Diretrizes para Claude Code (São Pedro)

## Comandos Essenciais
```bash
# Executar testes
python manage.py test

# Verificar migrations
python manage.py makemigrations --check --dry-run

# Executar servidor local
python manage.py runserver 0.0.0.0:8000
```

## Regras Críticas
1. **TDD**: Testes automatizados antes de regras de negócio.
2. **Multi-Schema**: Operar exclusivamente no schema `saopedro` de `db_gestao`.
3. **Zero Secrets**: Credenciais via `.env` não versionado.
