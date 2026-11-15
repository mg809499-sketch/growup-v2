# Verificación de Estado Real — Monorepo Growup (WP-00)

- **Fecha:** 2026-11-15
- **Entorno:** Windows (`win32`), Node/pnpm + Turbo `2.11.10`, Python + `uv` (`services/api/.venv`)
- **Objetivo:** Verificar el estado real de las suites de lint, tipos, contratos, compilación y pruebas unitarias antes de ejecutar los paquetes de trabajo de Nova y Nivel 2.

---

## 1. Resumen de Resultados

| Comando | Directorio | Estado | Resultado real medido |
|---|---|---|---|
| `uv run ruff check .` | `services/api` | **PASS** | `All checks passed!` |
| `uv run mypy app` | `services/api` | **PASS** | `Success: no issues found in 94 source files` |
| `uv run pytest -rf --tb=no` | `services/api` | **PASS** | `295 passed, 39 skipped, 1 warning in 3.75s` (los 39 `skipped` corresponden a pruebas de integración que requieren `GROWUP_TEST_DATABASE_URL` activa) |
| `pnpm lint` | raíz | **PASS** | `Tasks: 3 successful, 3 total` (`@growup/admin`, `@growup/storefront`, `@growup/web`) |
| `pnpm typecheck` | raíz | **PASS** | `Tasks: 5 successful, 5 total` (`@growup/admin`, `@growup/config`, `@growup/contracts`, `@growup/storefront`, `@growup/web`) |
| `pnpm contracts:check` | raíz | **PASS** | Exporta `openapi.json` desde FastAPI, regenera `packages/contracts/src/schema.d.ts` con `openapi-typescript 7.13.0` y verifica `git diff --exit-code` sin diferencias |
| `pnpm build` | raíz | **PASS** | Compila `@growup/storefront` (Next.js 16.4.3), `@growup/web` (19 páginas SSG) y `@growup/admin` (20 rutas + Proxy middleware) |

---

## 2. Reconciliación con Documentación Histórica (Base para WP-01)

1. **`docs/plan/plan-maestro-growup.md` §0 (escrito el 2026-11-10):**
   - Declaraba como `0%`: builder/bloques/contenido/publish y carrito/checkout/órdenes/pagos.
   - **Estado real verificado en código (2026-11-15):**
     - `services/api/app/domains/content/` implementa los 16 bloques (`blocks.py`), 7 plantillas (`templates.py`), `pages`/`page_versions`/`themes` (`repository.py`, `service.py`), preview HMAC y publish atómico, cubiertos por `tests/domains/content/`.
     - `apps/admin/app/(dashboard)/builder/` implementa el editor visual de 3 columnas con DnD, autosave, control optimista `expected_version` (`409 VERSION_CONFLICT`) e iframe `/preview`.
     - `services/api/app/domains/commerce/` implementa carrito, checkout, órdenes y webhook Wompi (`test_wompi.py`, `test_commerce_flow.py`).
     - `apps/admin/app/(dashboard)/platform/` implementa la Super Consola v1 (`overview`, `tenants`, export CSV) y `/planes` + `/suggestions`.
2. **Brechas técnicas confirmadas para resolver en Bloque 0:**
   - **C-1 (`GROWUP_DEFAULT_THEME`):** `apps/storefront/lib/format.ts` seleccionaba el tema por variable de entorno en lugar del `bootstrap.theme` del tenant resuelto por `Host`. Se corrige en **WP-02**.
   - **C-2 (`ThemeTokensV1`):** `services/api/app/domains/content/schemas.py` validaba límites estructurales genéricos pero carecía de un modelo tipado `ThemeTokensV1` sincronizado con un registro cerrado de fuentes y presets (`ropa`, `joyeria`, `nova`). Se corrige en **WP-03**.
   - **C-3 (Carga de fuentes):** Se incorpora la pareja tipográfica de **Nova** (`Unbounded`, `Geist`, `Geist Mono`) y la resolución dinámica del preset por tenant en **WP-22 / WP-23**.
