-- Endurece el search_path de funciones SECURITY DEFINER previas.
-- Solo pg_catalog y app: se elimina public para evitar shadowing de funciones.

alter function app.resolve_tenant(text) set search_path = pg_catalog, app;
alter function app.is_platform_admin(uuid) set search_path = pg_catalog, app;
alter function app.create_tenant(text, text, text, text, uuid)
    set search_path = pg_catalog, app;
