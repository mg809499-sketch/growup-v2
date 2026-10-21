# Supabase

Base de datos PostgreSQL gestionada. La API nunca permite acceso directo del navegador a Supabase; todo pasa por FastAPI.

## Estado

Las migraciones comienzan después de cerrar:

- **D-04** (cuentas de cliente) — define `customers` y el modelo de identidad.
- **D-07** (dominios y TLS) — define `domains` y la resolución host→tenant.

## Reglas

- Migraciones numeradas en `supabase/migrations/`.
- Nunca crear tablas a mano desde el dashboard.
- Toda tabla de negocio: `tenant_id UUID NOT NULL`, `ENABLE` + `FORCE ROW LEVEL SECURITY`.
- Política base: `tenant_id = app.current_tenant()` en `USING` y `WITH CHECK`.
- Prohibido `USING (true)` en tablas de negocio.
- El rol de la API no debe tener `BYPASSRLS`.
- `service_role` solo para workers y tareas auditadas.

## Comandos previstos

```bash
supabase init
supabase start
supabase db reset
supabase db diff --check
```
