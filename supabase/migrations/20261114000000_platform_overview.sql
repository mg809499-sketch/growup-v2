-- Panel ejecutivo (super consola) del staff: KPIs agregados, snapshot por tenant
-- y alertas derivadas. Todo vía funciones SECURITY DEFINER con un gate explícito
-- de platform admin (app.platform_admins), igual que app.list_tenants.
--
-- Convención: no se hace join abierto a tablas medidas en el RPC; se agrega con
-- CTEs internas para mantener el coste plano independientemente del número de
-- tenants (fine en el piloto, escala sin reescribir).

-- Tabla de descartes de alertas: solo el staff la escribe/lee vía funciones.
create table if not exists app.alert_dismissals (
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    alert_key text not null,
    dismissed_by uuid not null,
    dismissed_at timestamptz not null default now(),
    primary key (tenant_id, alert_key)
);

alter table app.alert_dismissals enable row level security;
alter table app.alert_dismissals force row level security;

revoke all on app.alert_dismissals from public;
revoke all on app.alert_dismissals from app_rw;

-- 1) Overview agregado del ecosistema.
create or replace function app.platform_overview(p_actor_id uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, app
as $$
begin
    if not app.is_platform_admin(p_actor_id) then
        raise exception 'platform admin required' using errcode = '42501';
    end if;

    return (
        select jsonb_build_object(
            'tenants_total', (select count(*) from app.tenants),
            'tenants_active', (select count(*) from app.tenants where status = 'active'),
            'tenants_trialing', (select count(*) from app.tenants where status = 'trialing'),
            'tenants_suspended', (select count(*) from app.tenants where status = 'suspended'),
            'tenants_canceled', (select count(*) from app.tenants where status = 'canceled'),
            'trials_ending_7d', (
                select count(*) from app.tenants
                where status = 'trialing'
                  and trial_ends_at is not null
                  and trial_ends_at <= now() + interval '7 days'
            ),
            'gmv_last_7d_cents', coalesce((
                select sum(total_cents) from app.orders
                where created_at >= now() - interval '7 days'
                  and status in ('paid', 'preparing', 'shipped', 'delivered')
            ), 0),
            'gmv_last_30d_cents', coalesce((
                select sum(total_cents) from app.orders
                where created_at >= now() - interval '30 days'
                  and status in ('paid', 'preparing', 'shipped', 'delivered')
            ), 0),
            'orders_last_30d', coalesce((
                select count(*) from app.orders
                where created_at >= now() - interval '30 days'
                  and status in ('paid', 'preparing', 'shipped', 'delivered')
            ), 0),
            'products_total', (select count(*) from app.products where status = 'active'),
            'media_bytes_total', coalesce((
                select sum(size_bytes) from app.media_assets where status = 'ready'
            ), 0),
            'media_failed', (select count(*) from app.media_assets where status = 'failed'),
            'outbox_stuck', (
                select count(*) from app.outbox_events e
                where e.processed_at is null
                  and e.created_at < now() - interval '5 minutes'
            ),
            'audit_decisions_last_7d', (
                select count(*) from app.decision_logs d
                where d.created_at >= now() - interval '7 days'
            ),
            'audit_denied_last_7d', (
                select count(*) from app.decision_logs d
                where d.created_at >= now() - interval '7 days'
                  and d.decision = 'DENY'
            ),
            'subscriptions_active', (
                select count(*) from app.platform_subscriptions
                where status in ('active', 'trialing')
            ),
            'computed_at', now()
        )
    );
end;
$$;

revoke all on function app.platform_overview(uuid) from public;
grant execute on function app.platform_overview(uuid) to app_rw;

-- 2) Snapshot de un tenant (para la watchlist / página de detalle).
create or replace function app.tenant_overview(p_actor_id uuid, p_tenant_id uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, app
as $$
declare
    t record;
    s record;
begin
    if not app.is_platform_admin(p_actor_id) then
        raise exception 'platform admin required' using errcode = '42501';
    end if;

    select id, slug, name, status, created_at, trial_ends_at, plan_id
    into t
    from app.tenants
    where id = p_tenant_id;

    if not found then
        raise exception 'tenant not found' using errcode = 'P0002';
    end if;

    select ps.provider, ps.status, ps.current_period_end, ps.created_at
    into s
    from app.platform_subscriptions ps
    where ps.tenant_id = p_tenant_id;

    return jsonb_build_object(
        'tenant', jsonb_build_object(
            'id', t.id,
            'slug', t.slug,
            'name', t.name,
            'status', t.status,
            'created_at', t.created_at,
            'trial_ends_at', t.trial_ends_at,
            'host', (
                select d.host from app.domains d
                where d.tenant_id = t.id and d.is_primary
                limit 1
            ),
            'plan', (
                select jsonb_build_object('id', p.id, 'code', p.code, 'name', p.name)
                from app.plans p
                where p.id = t.plan_id
                limit 1
            )
        ),
        'subscription', case
            when s is null then null
            else jsonb_build_object(
                'provider', s.provider,
                'status', s.status,
                'current_period_end', s.current_period_end,
                'created_at', s.created_at
            )
        end,
        'gmv_last_7d_cents', coalesce((
            select sum(total_cents) from app.orders
            where tenant_id = t.id
              and created_at >= now() - interval '7 days'
              and status in ('paid', 'preparing', 'shipped', 'delivered')
        ), 0),
        'gmv_last_30d_cents', coalesce((
            select sum(total_cents) from app.orders
            where tenant_id = t.id
              and created_at >= now() - interval '30 days'
              and status in ('paid', 'preparing', 'shipped', 'delivered')
        ), 0),
        'orders_last_30d', coalesce((
            select count(*) from app.orders
            where tenant_id = t.id
              and created_at >= now() - interval '30 days'
              and status in ('paid', 'preparing', 'shipped', 'delivered')
        ), 0),
        'products_total', (
            select count(*) from app.products
            where tenant_id = t.id and status = 'active'
        ),
        'media_bytes_total', coalesce((
            select sum(size_bytes) from app.media_assets
            where tenant_id = t.id and status = 'ready'
        ), 0),
        'media_failed', (
            select count(*) from app.media_assets
            where tenant_id = t.id and status = 'failed'
        ),
        'outbox_stuck', (
            select count(*) from app.outbox_events e
            where e.tenant_id = t.id
              and e.processed_at is null
              and e.created_at < now() - interval '5 minutes'
        ),
        'audit_decisions_last_7d', (
            select count(*) from app.decision_logs d
            where d.tenant_id = t.id
              and d.created_at >= now() - interval '7 days'
        ),
        'audit_denied_last_7d', (
            select count(*) from app.decision_logs d
            where d.tenant_id = t.id
              and d.created_at >= now() - interval '7 days'
              and d.decision = 'DENY'
        ),
        'audit_chain_valid', app.verify_decision_chain(t.id::text),
        'computed_at', now()
    );
end;
$$;

revoke all on function app.tenant_overview(uuid, uuid) from public;
grant execute on function app.tenant_overview(uuid, uuid) to app_rw;

-- 3) Alertas derivadas. Se listدان solo las que no están descartadas.
create or replace function app.platform_alerts(p_actor_id uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, app
as $$
declare
    v_alerts jsonb;
begin
    if not app.is_platform_admin(p_actor_id) then
        raise exception 'platform admin required' using errcode = '42501';
    end if;

    with base as (
        -- Trials que vencen en 7 días.
        select
            'trial_ending_7d'::text as type,
            'trial_ending_7d:' || t.id::text as alert_key,
            t.id as tenant_id,
            t.slug,
            t.name,
            'El trial de ' || t.name || ' vence pronto' as message,
            'warning'::text as severity
        from app.tenants t
        where t.status = 'trialing'
          and t.trial_ends_at is not null
          and t.trial_ends_at <= now() + interval '7 days'

        union all

        -- Outbox atascado por tenant.
        select
            'outbox_stuck',
            'outbox_stuck:' || t.id::text,
            t.id,
            t.slug,
            t.name,
            'Hay ' || count(*)::text || ' eventos de outbox sin procesar hace más de 5 min',
            'critical'
        from app.tenants t
        join app.outbox_events e on e.tenant_id = t.id
        where e.processed_at is null
          and e.created_at < now() - interval '5 minutes'
        group by t.id, t.slug, t.name

        union all

        -- Media fallida.
        select
            'media_failed',
            'media_failed:' || t.id::text,
            t.id,
            t.slug,
            t.name,
            'Hay ' || count(*)::text || ' asset(s) en estado failed',
            'warning'
        from app.tenants t
        join app.media_assets m on m.tenant_id = t.id
        where m.status = 'failed'
        group by t.id, t.slug, t.name

        union all

        -- Decisiones denegadas en 7d.
        select
            'audit_denied',
            'audit_denied:' || t.id::text,
            t.id,
            t.slug,
            t.name,
            count(*)::text || ' acciones denegadas en los últimos 7 días',
            'warning'
        from app.tenants t
        join app.decision_logs d on d.tenant_id = t.id
        where d.created_at >= now() - interval '7 days'
          and d.decision = 'DENY'
        group by t.id, t.slug, t.name

        union all

        -- Chain de auditoría rota.
        select
            'audit_chain_invalid',
            'audit_chain_invalid:' || t.id::text,
            t.id,
            t.slug,
            t.name,
            'La cadena de integridad de decision_logs NO verifica',
            'critical'
        from app.tenants t
        where not app.verify_decision_chain(t.id::text)
    ),
    filtered as (
        select b.*
        from base b
        where not exists (
            select 1
            from app.alert_dismissals ad
            where ad.tenant_id = b.tenant_id
              and ad.alert_key = b.alert_key
        )
    )
    select coalesce(
        jsonb_agg(
            jsonb_build_object(
                'type', f.type,
                'alert_key', f.alert_key,
                'tenant_id', f.tenant_id,
                'slug', f.slug,
                'name', f.name,
                'message', f.message,
                'severity', f.severity
            )
            order by
                case f.severity when 'critical' then 0 when 'warning' then 1 else 2 end,
                f.slug
        ),
        '[]'::jsonb
    ) into v_alerts
    from filtered f;

    return v_alerts;
end;
$$;

revoke all on function app.platform_alerts(uuid) from public;
grant execute on function app.platform_alerts(uuid) to app_rw;

-- 4) Descartar una alerta (solo plataforma; nunca de un comercio).
create or replace function app.dismiss_platform_alert(
    p_actor_id uuid,
    p_tenant_id uuid,
    p_alert_key text
)
returns void
language plpgsql
security definer
set search_path = pg_catalog, app
as $$
begin
    if not app.is_platform_admin(p_actor_id) then
        raise exception 'platform admin required' using errcode = '42501';
    end if;

    insert into app.alert_dismissals(tenant_id, alert_key, dismissed_by)
    values (p_tenant_id, p_alert_key, p_actor_id)
    on conflict (tenant_id, alert_key) do nothing;
end;
$$;

revoke all on function app.dismiss_platform_alert(uuid, uuid, text) from public;
grant execute on function app.dismiss_platform_alert(uuid, uuid, text) to app_rw;
