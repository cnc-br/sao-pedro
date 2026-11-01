# AGENTS.md — Diretrizes para Agentes de IA (São Pedro)

Este documento orienta todos os agentes de IA (Antigravity/Gemini, GitHub Copilot, Cursor, Claude Code e Hermes) operando no repositório `sao-pedro`.

---

## 1. Contexto do Repositório
- **Papel**: Serviço central de Identidade, Autenticação e Gestão de Pessoas (LGPD).
- **Stack**: Django 5.2, DRF, SimpleJWT, Python 3.12+, PostgreSQL 17.
- **Porta Local**: `8000`. **Produção**: Roteado pelo Nginx em `/auth/`.
- **Governança Canônica**: [gestao-devsecops/specs/004-identidade-saopedro/SPEC.md](https://github.com/cnc-br/gestao-devsecops/blob/main/specs/004-identidade-saopedro/SPEC.md).

---

## 2. Regras Mandatórias de Engenharia

### 2.1 Rigor TDD (Test-Driven Development)
- Toda nova funcionalidade ou correção de bug exige teste automatizado correspondente antes da implementação.
- Execute sempre:
  ```bash
  python manage.py test
  ```

### 2.2 Isolamento de Banco e LGPD (Multi-Schema)
- O São Pedro opera estritamente no schema `saopedro` dentro do banco `db_gestao`.
- Nunca crie modelos ou queries direcionadas a outros schemas (`ambrosio`).
- Migrations devem ser seguras e reversíveis:
  ```bash
  python manage.py makemigrations --check --dry-run
  ```

### 2.3 Zero Hardcoded Secrets
- Proibido armazenar credenciais ou tokens em código.
- Todas as variáveis devem ser lidas via `environ` a partir do `.env` local.
- Utilize `.env.example` como modelo canônico.

---

## 3. Glossário Ubíquo (DDD)
- **Usuário**: Credencial de acesso (email, WhatsApp, papel). *Evitar: conta, login, acesso*.
- **Pessoa**: Fiel cadastrado na base (dados civis e religiosos). *Evitar: membro, cadastro, cliente*.
- **Papel**: Nível de permissão (`ADMIN`, `SECRETARIA_CNC`, `NAO_IDENTIFICADO`). *Evitar: perfil, tipo*.
