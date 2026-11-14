-- Extensiones de planes para el editor 3D y pausa de tenants (staff).
-- Aditivo: nada se borra; estrecha y amplia columnas existentes.

alter table app.plans
    add column if not exists active boolean not null default true;

alter table app.plans
    add column if not exists badge text not null default '';

alter table app.plans
    add column if not exists description text;

alter table app.plans
    add column if not exists sort_order integer not null default 100;

alter table app.plans
    add column if not exists list_price_cop_cents bigint;

alter table app.plans
    add column if not exists list_price_usd_cents bigint;

-- RPC acotado para editar el catálogo de planes; enforce en SECURITY DEFINER.
create or replace function app.update_plan_admin(
    p_actor_id uuid,
    p_plan_id uuid,
    p_name text,
    p_price_cents integer,
    p_currency text,
    p_billing_interval text,
    p_trial_days integer,
    p_features jsonb,
    p_active boolean,
    p_badge text,
    p_description text,
    p_sort_order integer,
    p_list_price_cop_cents bigint,
    p_list_price_usd_cents bigint
)
returns app.plans
language plpgsql
security definer
set search_path = pg_catalog, app
as $$
declare
    row_data app.plans;
begin
    if not app.is_platform_admin(p_actor_id) then
        raise exception 'platform admin required' using errcode = '42501';
    end if;

    update app.plans
       set name = coalesce(p_name, name),
           price_cents = coalesce(p_price_cents, price_cents),
           currency = coalesce(p_currency, currency),
           billing_interval = coalesce(p_billing_interval, billing_interval),
           trial_days = coalesce(p_trial_days, trial_days),
           features = coalesce(p_features, features),
           active = coalesce(p_active, active),
           badge = coalesce(p_badge, badge),
           description = coalesce(p_description, description),
           sort_order = coalesce(p_sort_order, sort_order),
           list_price_cop_cents = coalesce(p_list_price_cop_cents, list_price_cop_cents),
           list_price_usd_cents = coalesce(p_list_price_usd_cents, list_price_usd_cents),
           updated_at = now()
     where id = p_plan_id
     returning *
    into row_data;

    if not found then
        raise exception 'plan not found' using errcode = 'P0002';
    end if;
    return row_data;
end;
$$;

revoke all on function app.update_plan_admin(
    uuid, uuid, text, integer, text, text, integer, jsonb,
    boolean, text, text, integer, bigint, bigint
) from public;
grant execute on function app.update_plan_admin(
    uuid, uuid, text, integer, text, text, integer, jsonb,
    boolean, text, text, integer, bigint, bigint
) to app_rw;

-- RPC acotado para pausar/activar tenant desde super consola (staff only).
create or replace function app.pause_tenant_admin(
    p_actor_id uuid,
    p_tenant_id uuid,
    p_status text
)
returns app.tenants
language plpgsql
security definer
set search_path = pg_catalog, app
as $$
declare
    row_data app.tenants;
begin
    if not app.is_platform_admin(p_actor_id) then
        raise exception 'platform admin required' using errcode = '42501';
    end if;

    if p_status not in ('active', 'suspended') then
        raise exception 'invalid status' using errcode = '22023';
    end if;

    update app.tenants
       set status = p_status,
           updated_at = now()
     where id = p_tenant_id
     returning *
    into row_data;

    if not found then
        raise exception 'tenant not found' using errcode = 'P0002';
    end if;

    insert into app.auth_events (tenant_id, event_type, actor_id, result)
    values (p_tenant_id, 'platform.pause_toggle', p_actor_id::text, p_status);

    return row_data;
end;
$$;

revoke all on function app.pause_tenant_admin(uuid, uuid, text) from public;
grant execute on function app.pause_tenant_admin(uuid, uuid, text) to app_rw;
