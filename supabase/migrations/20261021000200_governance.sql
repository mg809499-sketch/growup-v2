-- Gobernanza: decisiones auditables, cadena de hash y onboarding atómico.
-- Depende de core_tenancy y catalog.

-- ---------------------------------------------------------------------------
-- Tablas
-- ---------------------------------------------------------------------------

create table app.decision_logs (
    seq bigserial unique,
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid references app.tenants(id) on delete set null,
    -- Clave inmutable de la cadena: uuid del tenant o 'platform'. No cambia si
    -- el tenant se borra (tenant_id pasa a NULL) y mantiene la cadena verificable.
    chain_key text not null,
    actor_type text not null
        check (actor_type in ('staff', 'customer', 'system', 'ai', 'platform_admin')),
    actor_id text,
    action text not null,
    resource_type text,
    resource_id text,
    policy_id text not null,
    policy_version text not null,
    decision text not null check (decision in ('ALLOW', 'DENY', 'HANDOFF')),
    reason_code text not null,
    input_hash text not null,
    context_summary jsonb not null default '{}'::jsonb,
    latency_ms integer not null default 0 check (latency_ms >= 0),
    trace_id text,
    created_at timestamptz not null default now(),
    prev_hash text not null,
    hash text not null,
    unique (hash)
);

create index decision_logs_tenant_created_idx
    on app.decision_logs (tenant_id, created_at desc);
create index decision_logs_chain_seq_idx
    on app.decision_logs (chain_key, seq);
create index decision_logs_policy_decision_idx
    on app.decision_logs (policy_id, decision);
create index decision_logs_trace_idx
    on app.decision_logs (trace_id);

create table app.audit_chain_state (
    chain_key text primary key,
    last_hash text not null,
    last_log_id uuid,
    updated_at timestamptz not null default now()
);

create table app.approval_tasks (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    action text not null,
    resource_type text,
    resource_id text,
    requested_by text not null,
    assigned_role text not null
        check (assigned_role in ('owner', 'manager', 'treasurer', 'support', 'platform_admin')),
    status text not null default 'pending'
        check (status in ('pending', 'approved', 'rejected', 'expired')),
    reason text not null,
    expires_at timestamptz not null,
    resolved_by text,
    resolved_at timestamptz,
    created_at timestamptz not null default now()
);

create index approval_tasks_tenant_status_idx
    on app.approval_tasks (tenant_id, status, expires_at);

-- ---------------------------------------------------------------------------
-- Append-only
-- ---------------------------------------------------------------------------

create or replace function app.prevent_decision_log_mutation()
returns trigger
language plpgsql
as $$
begin
    -- ON DELETE SET NULL actualiza tenant_id dentro del trigger interno de la FK
    -- (profundidad 2). Se permite porque chain_key es inmutable y sostiene la
    -- cadena; cualquier UPDATE directo (profundidad 1) se bloquea.
    if tg_op = 'UPDATE' and pg_trigger_depth() > 1 then
        return new;
    end if;
    raise exception 'decision_logs es append-only';
end;
$$;

create trigger decision_logs_append_only
before update or delete on app.decision_logs
for each row execute function app.prevent_decision_log_mutation();

-- ---------------------------------------------------------------------------
-- Append y verificación de la cadena
-- ---------------------------------------------------------------------------

create or replace function app.append_decision_log(
    p_tenant_id uuid,
    p_actor_type text,
    p_actor_id text,
    p_action text,
    p_resource_type text,
    p_resource_id text,
    p_policy_id text,
    p_policy_version text,
    p_decision text,
    p_reason_code text,
    p_input_hash text,
    p_context_summary jsonb,
    p_latency_ms integer,
    p_trace_id text
)
returns uuid
language plpgsql
security definer
set search_path = pg_catalog, app, extensions
as $$
declare
    v_id uuid := gen_random_uuid();
    v_created_at timestamptz := clock_timestamp();
    v_chain_key text := coalesce(p_tenant_id::text, 'platform');
    v_prev_hash text;
    v_hash text;
begin
    if p_tenant_id is not null
       and p_tenant_id is distinct from app.current_tenant() then
        raise exception 'TENANT_MISMATCH: append_decision_log'
            using errcode = '42501';
    end if;

    if p_tenant_id is null and app.current_tenant() is not null then
        raise exception 'PLATFORM_DECISION_IN_TENANT: append_decision_log'
            using errcode = '42501';
    end if;

    perform pg_advisory_xact_lock(hashtext(v_chain_key));

    select last_hash into v_prev_hash
    from app.audit_chain_state
    where chain_key = v_chain_key;

    if v_prev_hash is null then
        v_prev_hash := repeat('0', 64);
    end if;

    v_hash := encode(
        digest(
            concat_ws(
                '|',
                v_prev_hash,
                v_id::text,
                v_chain_key,
                p_actor_type,
                coalesce(p_actor_id, ''),
                p_action,
                coalesce(p_resource_type, ''),
                coalesce(p_resource_id, ''),
                p_policy_id,
                p_policy_version,
                p_decision,
                p_reason_code,
                p_input_hash,
                coalesce(p_context_summary, '{}'::jsonb)::text,
                greatest(coalesce(p_latency_ms, 0), 0)::text,
                coalesce(p_trace_id, ''),
                v_created_at::text
            ),
            'sha256'
        ),
        'hex'
    );

    insert into app.decision_logs (
        id, tenant_id, chain_key, actor_type, actor_id, action, resource_type,
        resource_id, policy_id, policy_version, decision, reason_code, input_hash,
        context_summary, latency_ms, trace_id, created_at, prev_hash, hash
    )
    values (
        v_id, p_tenant_id, v_chain_key, p_actor_type, p_actor_id, p_action,
        p_resource_type, p_resource_id, p_policy_id, p_policy_version, p_decision,
        p_reason_code, p_input_hash, coalesce(p_context_summary, '{}'::jsonb),
        greatest(coalesce(p_latency_ms, 0), 0), p_trace_id, v_created_at,
        v_prev_hash, v_hash
    );

    insert into app.audit_chain_state (chain_key, last_hash, last_log_id, updated_at)
    values (v_chain_key, v_hash, v_id, now())
    on conflict (chain_key) do update
    set last_hash = excluded.last_hash,
        last_log_id = excluded.last_log_id,
        updated_at = excluded.updated_at;

    return v_id;
end;
$$;

create or replace function app.verify_decision_chain(p_chain_key text)
returns boolean
language plpgsql
security definer
set search_path = pg_catalog, app, extensions
as $$
declare
    r record;
    v_prev_hash text := repeat('0', 64);
    v_hash text;
begin
    for r in
        select *
        from app.decision_logs
        where chain_key = p_chain_key
        order by seq
    loop
        if r.prev_hash <> v_prev_hash then
            return false;
        end if;

        v_hash := encode(
            digest(
                concat_ws(
                    '|',
                    v_prev_hash,
                    r.id::text,
                    r.chain_key,
                    r.actor_type,
                    coalesce(r.actor_id, ''),
                    r.action,
                    coalesce(r.resource_type, ''),
                    coalesce(r.resource_id, ''),
                    r.policy_id,
                    r.policy_version,
                    r.decision,
                    r.reason_code,
                    r.input_hash,
                    r.context_summary::text,
                    r.latency_ms::text,
                    coalesce(r.trace_id, ''),
                    r.created_at::text
                ),
                'sha256'
            ),
            'hex'
        );

        if v_hash <> r.hash then
            return false;
        end if;

        v_prev_hash := r.hash;
    end loop;

    return true;
end;
$$;

-- ---------------------------------------------------------------------------
-- Onboarding atómico: tenant + owner
-- ---------------------------------------------------------------------------

create or replace function app.create_tenant_with_owner(
    p_slug text,
    p_host text,
    p_name text,
    p_legal_name text,
    p_plan_id uuid,
    p_owner_user_id uuid,
    p_owner_email text
)
returns uuid
language plpgsql
security definer
set search_path = pg_catalog, app
as $$
declare
    v_tenant_id uuid;
begin
    insert into app.tenants (slug, name, legal_name, plan_id, status, trial_ends_at)
    values (p_slug, p_name, p_legal_name, p_plan_id, 'trialing', now() + interval '14 days')
    returning id into v_tenant_id;

    insert into app.domains (tenant_id, host, type, is_primary)
    values (v_tenant_id, lower(p_host), 'subdomain', true);

    insert into app.tenant_settings (tenant_id)
    values (v_tenant_id);

    insert into app.tenant_features (tenant_id, feature_key, enabled)
    values
        (v_tenant_id, 'storefront', true),
        (v_tenant_id, 'checkout', true),
        (v_tenant_id, 'invoices', true);

    insert into app.locations (tenant_id, name, is_default)
    values (v_tenant_id, 'Principal', true);

    insert into app.memberships (tenant_id, user_id, email, role, status)
    values (v_tenant_id, p_owner_user_id, lower(p_owner_email), 'owner', 'active');

    return v_tenant_id;
end;
$$;

-- ---------------------------------------------------------------------------
-- RLS
-- ---------------------------------------------------------------------------

alter table app.decision_logs enable row level security;
alter table app.decision_logs force row level security;
create policy decision_logs_tenant_read on app.decision_logs
    for select
    using (tenant_id = app.current_tenant());

alter table app.audit_chain_state enable row level security;
alter table app.audit_chain_state force row level security;
-- Sin política: solo las funciones SECURITY DEFINER acceden.

alter table app.approval_tasks enable row level security;
alter table app.approval_tasks force row level security;
create policy approval_tasks_tenant_isolation on app.approval_tasks
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

-- ---------------------------------------------------------------------------
-- Grants
-- ---------------------------------------------------------------------------

grant select on app.decision_logs to app_rw;
grant select, insert, update on app.approval_tasks to app_rw;

revoke all on function app.append_decision_log(
    uuid, text, text, text, text, text, text, text, text, text, text, jsonb, integer, text
) from public;
revoke all on function app.verify_decision_chain(text) from public;
revoke all on function app.create_tenant_with_owner(
    text, text, text, text, uuid, uuid, text
) from public;

grant execute on function app.append_decision_log(
    uuid, text, text, text, text, text, text, text, text, text, text, jsonb, integer, text
) to app_rw;
grant execute on function app.verify_decision_chain(text) to app_rw;
grant execute on function app.create_tenant_with_owner(
    text, text, text, text, uuid, uuid, text
) to app_rw;
