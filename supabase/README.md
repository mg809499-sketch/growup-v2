# Supabase

Base de datos PostgreSQL gestionada. La API nunca permite acceso directo del navegador a Supabase; todo pasa por FastAPI.

## Estado

- Migración base aplicada en local: `migrations/20261021000000_core_tenancy.sql`.
- Tests pgTAP: `tests/tenancy.sql` (17 assertions).
- `app_rw` existe sin `BYPASSRLS`; la API fija por transacción:
  - `SET LOCAL ROLE app_rw`
  - `SELECT set_config('app.tenant_id', $1, true)`
- `tenants`, `domains`, `tenant_settings`, `tenant_features`, `memberships`, `customers`, `addresses` y `auth_events` tienen RLS `ENABLE` + `FORCE`.
- `plans` es catálogo de plataforma (sin `tenant_id`); `app_rw` solo tiene `SELECT`.
- `platform_admins` no es accesible directamente por `app_rw`; se consulta con `app.is_platform_admin(uuid)`.

## Reglas

- Migraciones numeradas en `supabase/migrations/`.
- Nunca crear tablas a mano desde el dashboard.
- Toda tabla de negocio: `tenant_id UUID NOT NULL`, `ENABLE` + `FORCE ROW LEVEL SECURITY`.
- Política base: `tenant_id = app.current_tenant()` en `USING` y `WITH CHECK`.
- Prohibido `USING (true)` en tablas de negocio.
- El rol de la API no debe tener `BYPASSRLS`.
- `service_role` solo para workers y tareas auditadas.
- En producción, el rol de login de la API debe ser miembro de `app_rw` y no superusuario.

## Comandos

```bash
pnpm dlx supabase start
pnpm dlx supabase db reset
pnpm dlx supabase test db
pnpm dlx supabase stop
```

## Tests

- pgTAP: `supabase test db`.
- Integración desde la API:

```bash
cd services/api
# PowerShell
$env:GROWUP_TEST_DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
uv run pytest
```

## Pendiente

- Migraciones de catálogo, contenido, comercio, pagos, billing, facturas y gobernanza.
- Seed de dos tenants demo con usuarios de Auth.
- Política de `platform_admins` y acceso de soporte auditado.
