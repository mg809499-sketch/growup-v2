---
name: tenant-isolation-check
description: Verifica aislamiento multi-tenant, RLS forzado, contexto de tenant y ausencia de fugas cross-tenant antes de mergear cambios de base de datos, API, caché o media. Úsala siempre que se toque tenancy, RLS, migraciones, repositorios, webhooks, JWT o endpoints con tenant.
---

# Tenant Isolation Check

## Objetivo

Demostrar con evidencia que un cambio no permite leer ni mutar datos de otro tenant, y que el contexto de tenant se impone en la base de datos, no solo en el código.

## Cuándo usarla

- Migración nueva o modificada.
- Tabla, índice, política RLS o función `SECURITY DEFINER`.
- Endpoint, repositorio o worker que recibe `tenant_id`.
- Resolución de host, JWT, webhook o caché.
- Cambio en media, URLs firmadas o prefijos R2.

## Checklist

### Base de datos

- [ ] La tabla tiene `tenant_id uuid not null references app.tenants(id)`.
- [ ] Existe índice por `tenant_id` (y compuestos según consultas).
- [ ] `ENABLE` + `FORCE ROW LEVEL SECURITY`.
- [ ] Política `USING (tenant_id = app.current_tenant())` y `WITH CHECK` igual.
- [ ] No hay `USING (true)` en tablas de negocio.
- [ ] `app_rw` no tiene `BYPASSRLS`.
- [ ] `plans`/`platform_admins` están documentadas como catálogo/plataforma, no como dato de tenant.
- [ ] Las funciones `SECURITY DEFINER` tienen `search_path` fijo y superficie mínima.

### API y transacciones

- [ ] La transacción ejecuta `SET LOCAL ROLE app_rw`.
- [ ] La transacción ejecuta `set_config('app.tenant_id', $1, true)`; nunca `SET` de sesión.
- [ ] El `tenant_id` viene del contexto (host/JWT), no del body ni del query.
- [ ] `X-Tenant-ID` no se confía desde internet.
- [ ] El claim del JWT coincide con el host/tenant resuelto.
- [ ] Los errores no filtran existencia de recursos ajenos (`404` antes que `403` cuando aplica).

### Caché y media

- [ ] La clave de caché incluye `tenant_id` o un host único.
- [ ] La purga es por tenant/página, no global.
- [ ] El prefijo de R2 es `tenant/{tenant_id}/...`.
- [ ] Una URL firmada no permite cambiar el prefijo.

### Tests

- [ ] RLS A/B: SELECT, INSERT, UPDATE, DELETE.
- [ ] Inserción con `tenant_id` ajeno → `42501`.
- [ ] Sin `app.tenant_id` no se ven filas.
- [ ] `app_rw` no puede `BYPASSRLS`.
- [ ] Los 12 vectores de `docs/architecture/03-tenancy.md` siguen cubiertos.
- [ ] Test de integración con Postgres real.

## Comandos

```bash
pnpm dlx supabase db reset
pnpm dlx supabase test db

cd services/api
uv run ruff check .
uv run mypy app

# PowerShell
$env:GROWUP_TEST_DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
uv run pytest tests/integration
```

Búsquedas rápidas:

```bash
rg "USING \(true\)|BYPASSRLS|SET app\.tenant_id|set_config\('app\.tenant_id'|SECURITY DEFINER" supabase services/api
rg "tenant_id" services/api/app/domains services/api/app/api
```

## Salida esperada

```text
TENANT ISOLATION: PASS | FAIL
- Migración: <archivo>
- Tablas nuevas: <lista>
- RLS: <evidencia>
- Tests: <comando + resultado>
- Vectores: <1-12 cubiertos / faltantes>
- Riesgo residual: <ninguno | descripción>
```

Si algo falla, no se mergea. Se corrige y se vuelve a ejecutar el check.
