# Supabase

Base de datos PostgreSQL gestionada. La API nunca permite acceso directo del navegador a Supabase; todo pasa por FastAPI.

## Estado

- Migraciones aplicadas en local: `20261021000000_core_tenancy.sql` a `20261021000900_harden_inventory_and_worker_access.sql`.
- Tests pgTAP: tenancy (17), catálogo (14), gobernanza (21), inventario (11), media (14), plataforma (8) y seguridad (10); 95 en total.
- `app_rw` y `app_worker` existen sin `BYPASSRLS`; la API fija por transacción:
  - `SET LOCAL ROLE app_rw`
  - `SELECT set_config('app.tenant_id', $1, true)`
- El worker de media usa `GROWUP_WORKER_DATABASE_URL` con un login distinto del API, miembro de `app_rw` y `app_worker`. No se debe conceder `app_worker` al login de la API.
- `tenants`, `domains`, `tenant_settings`, `tenant_features`, `memberships`, `customers`, `addresses` y `auth_events` tienen RLS `ENABLE` + `FORCE`.
- `plans` es catálogo de plataforma (sin `tenant_id`); `app_rw` solo tiene `SELECT`.
- `platform_admins` no es accesible directamente por `app_rw`; se consulta con `app.is_platform_admin(uuid)`.
- `decision_logs` es append-only y usa `chain_key` (UUID del tenant o `platform`) para que la cadena sobreviva al borrado del tenant. `audit_chain_state` no tiene política RLS: solo lo tocan funciones `SECURITY DEFINER`.
- `create_tenant_with_owner` crea tenant, dominio, settings, features, ubicación default y membership owner en una sola transacción.
- Las reservas de inventario usan `location_id` explícito, `UPDATE ... WHERE available - reserved >= quantity` atómico, `reserved <= available` y triggers diferidos que validan el total activo; `expire` libera las vencidas.
- `media_assets`, `media_variants` y `product_media` tienen RLS forzado. El prefijo de R2 es `tenant/{tenant_id}/...`; `original_filename` es metadata y nunca forma parte de la clave.
- `app.list_tenants()` (SECURITY DEFINER) compara el actor con el contexto verificado por la API y exige que exista en `platform_admins`; el listado incluye host primario, plan, trial y paginación.
- `app.expire_stale_uploads()` (SECURITY DEFINER, `search_path` fijo) solo es ejecutable por `app_worker` y marca como `failed` los uploads que nunca se completaron; la ejecuta el worker ARQ cada hora.
- Las funciones `SECURITY DEFINER` usan `search_path = pg_catalog, app` (sin `public`); lo verifica `tests/security.sql`.

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

- Migraciones de contenido, comercio, pagos, billing y facturas.
- Configurar R2 y ARQ en staging y correr el E2E real de upload; el E2E con S3-compatible (moto) ya cubre el flujo en CI.
- Seed de dos tenants demo con usuarios de Auth.
- Configurar Supabase local con signing keys asimétricas (JWKS) para probar login real; el verificador rechaza HS256 por diseño.
- Política de `platform_admins` y acceso de soporte auditado.
- Listar/suspender tenants, bandeja de `approval_tasks` y job diario de verificación de cadena.
- Conectar reservas de inventario al checkout (Wave 4) y worker de expiración por tenant.
