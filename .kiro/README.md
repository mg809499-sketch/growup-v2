# Kiro kit

Este directorio contiene las reglas persistentes, las especificaciones ejecutables, los checks reutilizables y las automatizaciones del proyecto.

```text
.kiro/
├─ steering/     # Reglas que Kiro carga en cada sesión (inclusion: always)
├─ specs/        # SDD: requirements → design → tasks
├─ skills/       # Checks reutilizables (SKILL.md)
├─ hooks/        # Automatizaciones event-driven (JSON v1)
└─ README.md
```

## Steering

Seis archivos, todos `inclusion: always`:

- `product.md` — qué es Growup y alcance del MVP.
- `tech-stack.md` — stack, convenciones y prohibiciones.
- `security.md` — identidad, tenancy, RLS, media y secretos.
- `governance.md` — `decide()`, auditoría, pagos e IA.
- `structure.md` — mapa del repo, fronteras y naming.
- `testing.md` — pirámide de tests, comandos y evidencia.

Índice: [`steering/README.md`](steering/README.md).

## Specs

- [`specs/storefront-platform-v2/`](specs/storefront-platform-v2/README.md) — requirements, design y tasks.
- Estado: decisiones cerradas, arquitectura documentada, migración de tenancy aplicada.

## Skills

| Skill | Uso |
|---|---|
| [`tenant-isolation-check`](skills/tenant-isolation-check/SKILL.md) | RLS, tenancy, JWT, webhooks, caché, media |
| [`block-review`](skills/block-review/SKILL.md) | Bloques, temas, builder, publish, a11y |
| [`payment-webhook-review`](skills/payment-webhook-review/SKILL.md) | Wompi, Stripe, DIAN, checkout, refunds |

Índice: [`skills/README.md`](skills/README.md).

## Hooks

Formato Kiro 1.0: `.kiro/hooks/<nombre>.json` con `version: "v1"`.

| Hook | Trigger | Acción |
|---|---|---|
| `session-start-context` | `SessionStart` | `git status` + último commit |
| `api-quality` | `PostFileSave` en `services/api/**/*.py` | `ruff` + `mypy` |
| `migration-review` | `PostFileCreate`/`PostFileSave` en `supabase/migrations/*.sql` | Revisión con `tenant-isolation-check` |
| `post-task-tests` | `PostTaskExec` | `pytest` |
| `env-security-check` | `PostFileSave` en `.env`/Docker | Revisión de secretos y PII |

## Orden de trabajo

1. Leer `docs/decisiones-pendientes.md`.
2. Leer `docs/adr/`.
3. Leer `steering/`.
4. Leer la spec y tomar una tarea de `tasks.md`.
5. Implementar por olas, con tests y evidencia.
6. Ejecutar la skill correspondiente si el cambio es sensible.

## Comandos

```bash
# API
cd services/api
uv run ruff check .
uv run mypy app
uv run pytest

# RLS
pnpm dlx supabase db reset
pnpm dlx supabase test db

# Contratos
pnpm typecheck
pnpm contracts:check
```

## Estado

- `steering/` completo (6 archivos).
- `specs/storefront-platform-v2/` completo.
- `skills/` completo (3 skills).
- `hooks/` completo (5 hooks).
- Próximo: olas 1-2 (auth de staff, catálogo, contenido).
