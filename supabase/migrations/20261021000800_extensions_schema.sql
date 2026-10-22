-- Mueve las extensiones al schema `extensions`.
--
-- En Supabase local ya viven ahí, pero en un Postgres vanilla `create
-- extension pgcrypto` (sin schema) las instala en `public`. Las funciones de
-- gobernanza usan `search_path = pg_catalog, app, extensions` y llaman
-- `digest(...)`, así que la extensión debe estar en `extensions` para que CI
-- (Postgres plano) y producción se comporten igual.

create schema if not exists extensions;

grant usage on schema extensions to app_rw;

do $$
declare
    extension_name text;
    extension_schema text;
begin
    foreach extension_name in array array['pgcrypto', 'pg_trgm'] loop
        select n.nspname
        into extension_schema
        from pg_extension e
        join pg_namespace n on n.oid = e.extnamespace
        where e.extname = extension_name;

        if extension_schema is not null and extension_schema <> 'extensions' then
            execute format(
                'alter extension %I set schema extensions',
                extension_name
            );
        end if;
    end loop;
end;
$$;
