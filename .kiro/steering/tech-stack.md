# Tech stack y convenciones

## Monorepo

- `pnpm` + Turborepo para el frontend; `uv` para Python.
- Node solo en `apps/*` y `packages/*`. Python solo en `services/api`.
- Backend con Screaming Architecture: `services/api/domains/{tenants,catalog,content,commerce,...}`.
- Contratos OpenAPI generados por FastAPI → `packages/contracts`.

## Frontend

- Next.js 16 App Router, React 19, TypeScript estricto.
- Tailwind CSS 4 con tokens en CSS variables.
- Server Components por defecto; Client Components solo para carrito, menús y variantes.
- Sin librerías de UI (shadcn, MUI, Chakra). Componentes propios.
- `next/font` y `next/image` obligatorios.
- Accesibilidad WCAG 2.2 AA y Core Web Vitals como criterio de aceptación.

## Backend

- FastAPI + Pydantic v2 + asyncpg.
- `ruff` + `mypy --strict` + `pytest`.
- Dinero en centavos (`int`), nunca `float`.
- Errores de dominio con códigos estables (`TENANT_MISMATCH`, `INSUFFICIENT_STOCK`, `GOVERNANCE_DENIED`).
- Idempotencia obligatoria en webhooks y checkout.

## Datos e infraestructura

- PostgreSQL en Supabase con RLS forzado.
- Redis para caché y colas; ARQ para workers.
- Cloudflare R2 para media, con URLs firmadas.
- Búsqueda: PostgreSQL FTS en MVP; Meilisearch cuando el catálogo lo justifique.
- Observabilidad: Sentry + OpenTelemetry + logs estructurados con `tenant_id` y `trace_id`.
- Despliegue: Vercel (Next) + Fly.io/Render (API y workers) + Supabase + Upstash + R2.

## Prohibiciones

- Node/Express/Nest en el backend.
- `service_role` en la API.
- Acceso directo del navegador a Supabase.
- HTML arbitrario en bloques del builder.
- Dependencias nuevas sin justificación y sin ADR si cambian la arquitectura.
