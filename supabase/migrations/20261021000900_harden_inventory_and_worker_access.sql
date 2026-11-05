-- Cierra permisos cross-tenant del worker, enlaza identidad de plataforma y
-- mantiene consistente el contador de reservas con sus filas activas.

do $$
begin
    if not exists (select 1 from pg_roles where rolname = 'app_worker') then
        create role app_worker nologin;
    end if;
end;
$$;

alter role app_worker nobypassrls;
grant usage on schema app to app_worker;

do $$
begin
    if exists (select 1 from pg_roles where rolname = 'postgres') then
        execute 'grant app_worker to postgres';
    end if;
end;
$$;

revoke all on function app.expire_stale_uploads(integer) from public, app_rw;
grant execute on function app.expire_stale_uploads(integer) to app_worker;

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
    if p_actor_id is null
       or p_actor_id::text is distinct from nullif(current_setting('app.actor_id', true), '')
       or not exists (
           select 1
           from app.platform_admins pa
           where pa.user_id = p_actor_id
       )
    then
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

alter table app.customers
    drop constraint customers_default_address_fk;

alter table app.customers
    add constraint customers_default_address_fk
    foreign key (tenant_id, default_address_id)
    references app.addresses (tenant_id, id)
    on delete set null (default_address_id);

create or replace function app.assert_inventory_reservation_balance(
    p_tenant_id uuid,
    p_variant_id uuid,
    p_location_id uuid
)
returns void
language plpgsql
set search_path = pg_catalog, app
as $$
declare
    v_reserved bigint;
    v_active_reservations bigint;
begin
    select coalesce(sum(r.quantity), 0)
    into v_active_reservations
    from app.inventory_reservations r
    where r.tenant_id = p_tenant_id
      and r.variant_id = p_variant_id
      and r.location_id = p_location_id
      and r.status = 'active';

    select l.reserved
    into v_reserved
    from app.inventory_levels l
    where l.tenant_id = p_tenant_id
      and l.variant_id = p_variant_id
      and l.location_id = p_location_id;

    if not found then
        v_reserved := 0;
    end if;

    if v_reserved::bigint <> v_active_reservations then
        raise exception 'inventory reservation balance mismatch'
            using errcode = '23514';
    end if;
end;
$$;

create or replace function app.check_inventory_reservation_balance()
returns trigger
language plpgsql
set search_path = pg_catalog, app
as $$
begin
    if tg_table_name = 'inventory_levels' then
        if tg_op = 'DELETE' then
            perform app.assert_inventory_reservation_balance(
                old.tenant_id, old.variant_id, old.location_id
            );
        else
            perform app.assert_inventory_reservation_balance(
                new.tenant_id, new.variant_id, new.location_id
            );
        end if;
    elsif tg_op = 'DELETE' then
        perform app.assert_inventory_reservation_balance(
            old.tenant_id, old.variant_id, old.location_id
        );
    else
        perform app.assert_inventory_reservation_balance(
            new.tenant_id, new.variant_id, new.location_id
        );
        if tg_op = 'UPDATE'
           and (
               old.tenant_id is distinct from new.tenant_id
               or old.variant_id is distinct from new.variant_id
               or old.location_id is distinct from new.location_id
           )
        then
            perform app.assert_inventory_reservation_balance(
                old.tenant_id, old.variant_id, old.location_id
            );
        end if;
    end if;
    return null;
end;
$$;

create constraint trigger inventory_levels_reservation_balance
after insert or update or delete on app.inventory_levels
deferrable initially deferred
for each row execute function app.check_inventory_reservation_balance();

create constraint trigger inventory_reservations_balance
after insert or update or delete on app.inventory_reservations
deferrable initially deferred
for each row execute function app.check_inventory_reservation_balance();
