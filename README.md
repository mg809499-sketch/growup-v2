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
├─ supabase/             # Migraciones y seeds
├─ docs/
│  ├─ adr/               # Decisiones de arquitectura
│  ├─ prompts/           # Prompts reproducibles (v0, etc.)
│  └─ decisiones-pendientes.md
└─ .kiro/                # Steering, specs y skills
```

## Estado

- [x] Documentos de arquitectura V2 en `docs/`
- [x] Prompt de v0 en `docs/prompts/v0-storefront.md`
- [x] Bootstrap del monorepo
- [x] ADR-0001 (producto) y ADR-0002 (repositorio)
- [ ] Decisiones de negocio (`docs/decisiones-pendientes.md`)
- [ ] ADRs técnicos restantes
- [ ] Specs en `.kiro/specs/`
- [ ] Wave 0 / Wave 1

## Inicio rápido — API

```bash
cd services/api
uv sync
uv run uvicorn app.main:app --reload
# http://localhost:8000/healthz
```

## Inicio rápido — Frontend

Pendiente de integrar el export de v0 en `apps/storefront`. Ver `docs/prompts/v0-storefront.md`.

## Documentación

- [Arquitectura V2 (documento base)](docs/arquitectura-plataforma-inteligente-cordiasolve-v2.md)
- [Decisiones de negocio pendientes](docs/decisiones-pendientes.md)
- [ADRs](docs/adr/README.md)
- [Steering para agentes](.kiro/steering/)
- [Reglas para agentes](AGENTS.md)

## Regla de convivencia

El proyecto hermano `../multitiendas` es **solo lectura**: se usa como referencia y donante de código, pero no se modifica, mueve ni renombra desde este repositorio.
