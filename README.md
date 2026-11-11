# Growup — Plataforma de comercio multi-tenant

Repositorios del storefront engine y la API de la plataforma Cordiasolve V2.

> **Lectura obligada para entender el estado real y el trabajo pendiente:** [`docs/plan/README.md`](docs/plan/README.md) (auditoría 2026-11-10 + plan maestro F0–F7). Todas las decisiones de proveedores y los pasos de ejecución están documentados ahí y en [`docs/decisiones-pendientes.md`](docs/decisiones-pendientes.md).

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | Next.js 16 (App Router), TypeScript, Tailwind CSS 4 |
| Backend | FastAPI (Python 3.12+), Pydantic v2, asyncpg |
| Base de datos | PostgreSQL (Supabase) con RLS forzado |
| Caché / colas | Redis + ARQ |
| Media | Cloudflare R2 (S3 compatible) |
| Búsqueda | PostgreSQL FTS (MVP) → Meilisearch (fase posterior) |
| Observabilidad | Sentry + OpenTelemetry → Grafana Cloud (plan F1) |

## Estado (2026-11-10)

Implementado y verificado:

- Núcleo multi-tenant: RLS forzado, resolución host→tenant (suspendidos no resuelven), JWT/JWKS con singleflight, RBAC desde membresía, aislamiento probado contra Postgres real (pgTAP + pytest integración, 262 passed).
- Catálogo, variantes, inventario atómico, media (R2 + worker ARQ), gobernanza con hash chain.
- Contratos OpenAPI → TypeScript (`packages/contracts`) + `@growup/config` compartido.
- **Contenido/builder (ADR-0005, implementación completa de backend + storefront + admin):** tablas `pages`/`page_versions`/`themes`/`outbox_events`, 16 bloques con esquemas cerrados, publicar atómico, preview con token HMAC, render en storefront, ISR + purga por tags, páginas ejemplo `ropa`/`joyeria` vía `seed.demo.sql`.
- **Comercio (Wave 4, núcleo):** carrito guest, checkout con redirect a Wompi (SAQ A), órdenes, webhook Wompi firmado e idempotente, admin de pedidos, configuración de cuenta Wompi por tenant (cifrada).
- **Infraestructura:** Dockerfiles API/worker (no-root), `fly.toml` staging/producción, compose local endurecido, CI con jobs de seguridad (gitleaks, pip-audit, pnpm audit, Trivy) y workflow de deploy.
- **Frontend:** storefront con catálogo, bloques, carrito, previsualización y navegación; admin con login, catálogo, media, auditoría, builder de páginas, pedidos y tenants.
- E2E Playwright (`apps/storefront/e2e/`, 6 tests en verde contra stack local).

Pendiente (ver plan): deploys reales a staging/prod, DIAN (Factus), Stripe Billing + suspensión por impago, emails (Resend), DPA/DSR/legal (abogado), observabilidad en producción, piloto Q1 2027.

## Estructura

```text
growup/
├─ apps/
│  ├─ storefront/        # Next.js: renderiza bloques publicados; carrito y checkout
│  ├─ admin/             # Next.js: catálogo, media, builder, pedidos, auditoría, tenants
│  └─ web/               # Next.js: sitio público growup.com (marketing del SaaS)
├─ services/
│  └─ api/               # FastAPI: core + dominios + workers
├─ packages/             # contracts (OpenAPI→TS), config (utilidades compartidas)
├─ infra/                # compose local (Redis+MinIO), fly.toml (staging/prod)
├─ supabase/             # Migraciones, seed.demo.sql, tests pgTAP
├─ docs/
│  ├─ adr/               # Decisiones de arquitectura (0001-0011; 0005 en propuesta)
│  ├─ plan/              # Plan maestro F0–F7, decisiones de proveedores, guías ejecutables
│  ├─ prototypes-legacy-html/  # Mockups visuales históricos (no usar)
│  ├─ legal/, regulatory/, architecture/
├─ .github/workflows/    # ci.yml (api, db, contracts, frontend, security, docker)
└─ AGENTS.md             # Reglas para agentes
```

## Inicio rápido — API

```bash
# Base de datos local (requiere Docker)
pnpm dlx supabase start
pnpm dlx supabase db reset

# Datos demo: tenants ropa y joyeria con catálogo y home publicada
psql "$GROWUP_MIGRATION_URL" -f supabase/seed.demo.sql

# Redis + MinIO para media local (opcional)
docker compose -f infra/docker-compose.yml up -d

cd services/api
cp .env.example .env   # completa GROWUP_DATABASE_URL, GROWUP_PREVIEW_SECRET, ...
python -m uv sync
python -m uv run uvicorn app.main:app --reload
# http://localhost:8000/healthz
# http://localhost:8000/readyz
```

Tests:

```bash
cd services/api
python -m uv run pytest                # unit + integración (con GROWUP_TEST_DATABASE_URL)
python -m uv run ruff check .
python -m uv run mypy app
```

E2E storefront (con API y storefront corriendo):

```bash
cd apps/storefront
pnpm exec playwright install chromium
STOREFRONT_URL=http://localhost:3000 pnpm test:e2e
```

Build local de imágenes:

```bash
docker build -f services/api/Dockerfile services/api -t growup-api:local
docker build -f services/api/Dockerfile.worker services/api -t growup-worker:local
```

CI (`.github/workflows/ci.yml`): API (ruff/mypy/pytest con Postgres real), pgTAP, contratos, frontend (lint/typecheck/build), seguridad (gitleaks/pip-audit/pnpm audit), Docker (build + Trivy). Deploy: `.github/workflows/deploy.yml` (staging automático en main; producción manual con `environment: production`).

## Equipo

Somos dos personas. El reparto histórico está en [`docs/reparto-trabajo.md`](docs/reparto-trabajo.md); el plan vigente está en [`docs/plan/`](docs/plan/README.md).

## Regla de convivencia

El proyecto hermano `../multitiendas` es **solo lectura**.
