---
inclusion: always
---

# Testing y evidencia

## Regla

**Sin test no hay merge.** Un cambio sin test no se considera terminado, aunque compile.

## Niveles

| Nivel | Herramienta | Qué cubre |
|---|---|---|
| Unitario | `pytest` | Servicios, políticas, money, state machines, schemas |
| Integración | `pytest` + Postgres real | RLS, inventario concurrente, webhooks, idempotencia |
| RLS | pgTAP (`supabase test db`) | Aislamiento A/B, políticas, funciones |
| Contratos | `openapi-typescript` + CI | Tipos TS alineados al OpenAPI |
| E2E | Playwright | Storefront/admin, dos tenants, checkout sandbox |
| Carga | k6 | Checkout concurrente, búsqueda, publish |
| Seguridad | pytest + ZAP | 12 vectores, headers, dependencias |
| Accesibilidad | axe | WCAG 2.2 AA en páginas piloto |
| Visual | Playwright screenshots | Dos temas distintos |

## Comandos

```bash
# API
cd services/api
uv run ruff check .
uv run mypy app
uv run pytest

# Integración contra Supabase local (PowerShell)
$env:GROWUP_TEST_DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
uv run pytest

# RLS
pnpm dlx supabase db reset
pnpm dlx supabase test db

# Contratos
pnpm typecheck
pnpm contracts:check

# Frontend
pnpm lint
pnpm build
```

## Qué testear por cambio

| Cambio | Tests obligatorios |
|---|---|
| Tabla nueva | RLS A/B, `tenant_id`, `USING`/`WITH CHECK`, índice |
| Endpoint de tenant | Token válido, mismatch, rol insuficiente, recurso ajeno |
| Repositorio | Contexto de tenant, no aceptar `tenant_id` del body |
| Checkout | Idempotencia, stock, monto, webhook firmado, replay |
| Webhook | Firma, timestamp, `provider_event_id`, tenant correcto |
| Publish | Schema inválido, versión inmutable, rollback, purga |
| Bloque | Props inválidas, XSS, alt text, fallback, a11y |
| Dinero | Centavos, redondeo, snapshot de totales |
| Migración | `supabase db reset` + pgTAP + expand/contract |

## Evidencia en el PR

- Comando ejecutado y resultado.
- Test nuevo o actualizado.
- Captura/métrica si es UI o performance.
- ADR/spec actualizado si cambió una decisión.

## CI

- `api`: ruff, mypy, pytest con Postgres real y migración aplicada.
- `contracts`: OpenAPI regenerado y `git diff --exit-code`.
- `frontend`: lint, typecheck, build (cuando exista `apps/storefront`).
- Seguridad: dependency audit y secret scanning.
