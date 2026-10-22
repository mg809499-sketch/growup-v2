-- Limpieza de uploads huérfanos: assets que nunca se completaron.
--
-- La función es SECURITY DEFINER porque el job es cross-tenant: el worker
-- llama a `app.expire_stale_uploads()` sin contexto de tenant y la función
-- toca todos los assets vencidos. `search_path` queda fijo en pg_catalog, app.

create or replace function app.expire_stale_uploads(
    p_max_age_seconds integer default 3600
)
returns integer
language plpgsql
security definer
set search_path = pg_catalog, app
as $$
declare
    v_count integer;
begin
    if p_max_age_seconds < 60 then
        raise exception 'max_age_seconds must be at least 60';
    end if;

    update app.media_assets
    set status = 'failed',
        updated_at = now()
    where status = 'uploading'
      and updated_at < now() - make_interval(secs => p_max_age_seconds);

    get diagnostics v_count = row_count;
    return v_count;
end;
$$;

revoke all on function app.expire_stale_uploads(integer) from public;
grant execute on function app.expire_stale_uploads(integer) to app_rw;
