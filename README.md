# Growup — Plataforma de comercio multi-tenant

Repositorio del storefront engine y la API de la plataforma Cordiasolve V2.

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | Next.js 16 (App Router), TypeScript, Tailwind CSS 4 |
| Backend | FastAPI (Python 3.12+), Pydantic v2, asyncpg |
| Base de datos | PostgreSQL (Supabase) con RLS forzado |
| Caché / colas | Redis + ARQ |
| Media | Cloudflare R2 (S3 compatible) |
| Búsqueda | PostgreSQL FTS (MVP) → Meilisearch (fase posterior) |
| Observabilidad | Sentry + OpenTelemetry |

## Estructura

```text
growup/
├─ apps/
│  ├─ storefront/        # Next.js: resuelve host→tenant y renderiza bloques publicados
│  └─ admin/             # Next.js: builder, catálogo, pedidos, ajustes
├─ services/
│  └─ api/               # FastAPI: core + dominios + workers
├─ packages/             # UI, contratos OpenAPI, configuración compartida
├─ supabase/             # Migraciones, seeds y tests pgTAP
├─ docs/
│  ├─ adr/               # Decisiones de arquitectura
│  ├─ architecture/      # Overview, datos y tenancy
│  ├─ prompts/           # Prompts reproducibles (v0, etc.)
│  └─ decisiones-pendientes.md
└─ .kiro/                # Steering, specs y skills
```

## Estado

- [x] Documentos de arquitectura V2 en `docs/`
- [x] Prompt de v0 en `docs/prompts/v0-storefront.md`
- [x] Bootstrap del monorepo
- [x] ADR-0001 (producto) y ADR-0002 (repositorio)
- [x] Decisiones de negocio (`docs/decisiones-pendientes.md`)
- [x] ADRs técnicos 0001-0008
- [x] Specs en `.kiro/specs/storefront-platform-v2/`
- [x] Núcleo de seguridad: errores, host, JWT/JWKS, algoritmo asimétrico
- [x] Migración base de tenancy, RLS forzado y 17 tests pgTAP
- [x] Pool asyncpg con `SET LOCAL ROLE app_rw` + `SET LOCAL app.tenant_id` y `/readyz`
- [x] Pipeline OpenAPI → TypeScript (`packages/contracts`)
- [x] `/v1/storefront/bootstrap` con resolución host→tenant, settings y caché local
- [x] Auth de staff: JWKS, memberships, roles/permisos y `/v1/admin/me`
- [x] Catálogo: migración, API admin/storefront, FTS, inventario inicial y 14 tests pgTAP
- [x] Inventario: reservas atómicas por ubicación, confirmación/liberación/expiración y test de 40 reservas concurrentes sin overselling
- [x] Gobernanza: `decide()` con políticas versionadas, `decision_logs` append-only con cadena por tenant/plataforma y verificación de integridad
- [x] Platform admin: `POST /v1/platform/tenants` atómico con `create_tenant_with_owner` + auditoría, y `GET /v1/platform/tenants` paginado con búsqueda
- [x] Media: URL prefirmada a R2, worker ARQ, AVIF/WebP 320-1600, strip de EXIF, blurhash, alt obligatorio, asociación a producto, gestión (listar/editar/borrar) y limpieza de uploads huérfanos
- [x] Aislamiento: 10 vectores cross-tenant automatizados sobre HTTP real (RLS + schemas cerrados)
- [x] Auditoría: `GET /v1/admin/audit` paginado por `seq` y `GET /v1/admin/audit/verify` sobre la cadena de hashes
- [x] Hardening HTTP: headers de seguridad (nosniff, frame-options, referrer, CSP en `/v1`, HSTS fuera de local) y límite de cuerpo configurable
- [ ] Wave 0 / Wave 1: frontend y contenido

## Inicio rápido — API

```bash
# Base de datos local (requiere Docker)
pnpm dlx supabase start
pnpm dlx supabase db reset

cd services/api
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload
# http://localhost:8000/healthz
# http://localhost:8000/readyz
# Worker de media (requiere Redis y R2 configurados)
uv run arq app.workers.media.WorkerSettings
```

Tests:

```bash
cd services/api
uv run pytest
uv run ruff check .
uv run mypy app
```

Tests de integración contra Supabase local:

```bash
# PowerShell
$env:GROWUP_TEST_DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
uv run pytest
```

Tests RLS con pgTAP:

```bash
pnpm dlx supabase test db
```

## Inicio rápido — Frontend

Pendiente de integrar el export de v0 en `apps/storefront`. Ver `docs/prompts/v0-storefront.md`.

## Documentación

- [Arquitectura V2 (documento base)](docs/arquitectura-plataforma-inteligente-cordiasolve-v2.md)
- [Overview de arquitectura](docs/architecture/00-overview.md)
- [Modelo de datos](docs/architecture/02-datos.md)
- [Tenancy y threat model](docs/architecture/03-tenancy.md)
- [Decisiones de negocio](docs/decisiones-pendientes.md)
- [ADRs](docs/adr/README.md)
- [Spec del MVP](.kiro/specs/storefront-platform-v2/requirements.md)
- [Steering para agentes](.kiro/steering/)
- [Reglas para agentes](AGENTS.md)

## Regla de convivencia

El proyecto hermano `../multitiendas` es **solo lectura**: se usa como referencia y donante de código, pero no se modifica, mueve ni renombra desde este repositorio.
