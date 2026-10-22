-- Listado de tenants para platform admins.
--
-- La tabla app.tenants tiene RLS forzado, así que el listado cross-tenant vive
-- en una función SECURITY DEFINER. La función vuelve a comprobar que el actor
-- sea platform admin: no confía solo en el permiso del JWT.

create or replace function app.list_tenants(
    p_actor_id uuid,
    p_status text default null,
    p_query text default null,
    p_limit integer default 50,
    p_offset integer default 0
)
returns table (
    id uuid,
    slug text,
    name text,
    status text,
    host text,
    plan_id uuid,
    trial_ends_at timestamptz,
    created_at timestamptz,
    total_count bigint
)
language plpgsql
stable
security definer
set search_path = pg_catalog, app
as $$
begin
    if not exists (
        select 1
        from app.platform_admins pa
        where pa.user_id = p_actor_id
    ) then
        raise exception 'platform admin required' using errcode = '42501';
    end if;

    if p_limit < 1 or p_limit > 100 then
        raise exception 'limit must be between 1 and 100';
    end if;

    if p_offset < 0 then
        raise exception 'offset must be greater than or equal to 0';
    end if;

    return query
    select
        t.id,
        t.slug,
        t.name,
        t.status,
        d.host,
        t.plan_id,
        t.trial_ends_at,
        t.created_at,
        count(*) over () as total_count
    from app.tenants t
    left join lateral (
        select dom.host
        from app.domains dom
        where dom.tenant_id = t.id
          and dom.is_primary
        order by dom.created_at
        limit 1
    ) d on true
    where (p_status is null or t.status = p_status)
      and (
          p_query is null
          or p_query = ''
          or t.slug ilike '%' || p_query || '%'
          or t.name ilike '%' || p_query || '%'
      )
    order by t.created_at desc, t.id desc
    limit p_limit
    offset p_offset;
end;
$$;

revoke all on function app.list_tenants(uuid, text, text, integer, integer) from public;
grant execute on function app.list_tenants(uuid, text, text, integer, integer) to app_rw;
