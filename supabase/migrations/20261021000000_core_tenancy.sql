-- Core de tenancy: schema app, funciones, tablas y RLS forzado.
-- Orden: extensiones -> tablas -> funciones -> triggers -> RLS -> grants.

create schema if not exists app;

create extension if not exists pgcrypto;
create extension if not exists pg_trgm;

-- ---------------------------------------------------------------------------
-- Rol de la API: sin BYPASSRLS, sin DDL.
-- ---------------------------------------------------------------------------

do $$
begin
    if not exists (select 1 from pg_roles where rolname = 'app_rw') then
        create role app_rw nologin;
    end if;
end;
$$;

alter role app_rw nobypassrls;
grant usage on schema app to app_rw;

-- Permite que el rol administrativo `postgres` pueda impersonar a la API en
-- tests y tareas operativas auditadas. No otorga BYPASSRLS.
do $$
begin
    if exists (select 1 from pg_roles where rolname = 'postgres') then
        execute 'grant app_rw to postgres';
    end if;
end;
$$;

-- ---------------------------------------------------------------------------
-- Catálogo de plataforma
-- ---------------------------------------------------------------------------

create table app.plans (
    id uuid primary key default gen_random_uuid(),
    code text not null unique,
    name text not null,
    price_cents bigint not null default 0 check (price_cents >= 0),
    currency text not null default 'COP' check (currency = 'COP'),
    billing_interval text not null default 'month' check (billing_interval in ('month')),
    trial_days integer not null default 14 check (trial_days >= 0),
    features jsonb not null default '{}'::jsonb,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

comment on table app.plans is 'Catálogo de planes de la plataforma; no es dato de tenant.';

-- ---------------------------------------------------------------------------
-- Tenants y dominios
-- ---------------------------------------------------------------------------

create table app.tenants (
    id uuid primary key default gen_random_uuid(),
    slug text not null unique,
    name text not null,
    legal_name text,
    status text not null default 'trialing'
        check (status in ('trialing', 'active', 'past_due', 'suspended', 'canceled')),
    plan_id uuid references app.plans(id) on delete restrict,
    trial_ends_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint tenants_slug_format
        check (slug ~ '^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$'),
    constraint tenants_slug_reserved
        check (
            slug not in (
                'admin', 'api', 'app', 'assets', 'billing', 'cdn', 'checkout',
                'docs', 'mail', 'pay', 'platform', 'static', 'status', 'store',
                'support', 'www'
            )
        )
);

create table app.domains (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    host text not null unique,
    type text not null default 'subdomain' check (type in ('subdomain', 'custom')),
    is_primary boolean not null default false,
    verified_at timestamptz,
    created_at timestamptz not null default now(),
    constraint domains_host_lower check (host = lower(host)),
    constraint domains_host_length check (char_length(host) between 3 and 253)
);

create index domains_tenant_id_idx on app.domains (tenant_id);
create unique index domains_primary_idx on app.domains (tenant_id) where is_primary;

create table app.tenant_settings (
    tenant_id uuid primary key references app.tenants(id) on delete cascade,
    currency text not null default 'COP' check (currency = 'COP'),
    locale text not null default 'es-CO',
    navigation jsonb not null default '{}'::jsonb,
    seo_defaults jsonb not null default '{}'::jsonb,
    shipping_zones jsonb not null default '[]'::jsonb,
    contact jsonb not null default '{}'::jsonb,
    social jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default now()
);

create table app.tenant_features (
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    feature_key text not null,
    enabled boolean not null default true,
    limit_value jsonb,
    updated_at timestamptz not null default now(),
    primary key (tenant_id, feature_key)
);

-- ---------------------------------------------------------------------------
-- Identidad
-- ---------------------------------------------------------------------------

create table app.memberships (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    user_id uuid not null,
    email text not null,
    role text not null check (role in ('owner', 'manager', 'treasurer', 'packer', 'support')),
    status text not null default 'invited' check (status in ('invited', 'active', 'disabled')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (tenant_id, user_id)
);

create unique index memberships_tenant_email_idx
    on app.memberships (tenant_id, lower(email));

create table app.customers (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    auth_user_id uuid,
    email text not null,
    name text,
    phone text,
    default_address_id uuid,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index customers_tenant_email_lookup_idx
    on app.customers (tenant_id, lower(email));

create unique index customers_tenant_email_auth_idx
    on app.customers (tenant_id, lower(email))
    where auth_user_id is not null;

create unique index customers_tenant_auth_idx
    on app.customers (tenant_id, auth_user_id)
    where auth_user_id is not null;

create table app.addresses (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    customer_id uuid references app.customers(id) on delete cascade,
    name text not null,
    phone text,
    line1 text not null,
    line2 text,
    city text not null,
    state text not null,
    postal_code text,
    country text not null default 'CO' check (country = 'CO'),
    is_default boolean not null default false,
    created_at timestamptz not null default now()
);

create index addresses_tenant_customer_idx on app.addresses (tenant_id, customer_id);
create unique index addresses_default_idx
    on app.addresses (tenant_id, customer_id)
    where is_default;

-- FK compuesta para impedir que un cliente apunte a una dirección de otro tenant.
alter table app.addresses
    add constraint addresses_tenant_id_id_key unique (tenant_id, id);

alter table app.customers
    add constraint customers_default_address_fk
    foreign key (tenant_id, default_address_id)
    references app.addresses (tenant_id, id)
    on delete set null;

create table app.auth_events (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid references app.tenants(id) on delete set null,
    event_type text not null,
    actor_id text,
    ip inet,
    user_agent text,
    result text not null,
    trace_id text,
    created_at timestamptz not null default now()
);

create index auth_events_tenant_created_idx
    on app.auth_events (tenant_id, created_at desc);

create table app.platform_admins (
    user_id uuid primary key,
    email text not null unique,
    role text not null check (role in ('support', 'ops', 'owner')),
    created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Funciones de contexto y resolución
-- ---------------------------------------------------------------------------

create or replace function app.current_tenant()
returns uuid
language sql
stable
as $$
    select nullif(current_setting('app.tenant_id', true), '')::uuid;
$$;

comment on function app.current_tenant() is
    'Tenant actual de la transacción; NULL si no se fijó con set_config(..., true).';

create or replace function app.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create or replace function app.resolve_tenant(p_host text)
returns table (id uuid, slug text, name text, status text)
language sql
stable
security definer
set search_path = app, public
as $$
    select t.id, t.slug, t.name, t.status
    from app.domains d
    join app.tenants t on t.id = d.tenant_id
    where d.host = lower(p_host)
    limit 1;
$$;

create or replace function app.is_platform_admin(p_user_id uuid)
returns boolean
language sql
stable
security definer
set search_path = app, public
as $$
    select exists (
        select 1 from app.platform_admins where user_id = p_user_id
    );
$$;

create or replace function app.create_tenant(
    p_slug text,
    p_host text,
    p_name text,
    p_legal_name text default null,
    p_plan_id uuid default null
)
returns uuid
language plpgsql
security definer
set search_path = app, public
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

    return v_tenant_id;
end;
$$;

-- ---------------------------------------------------------------------------
-- Triggers de updated_at
-- ---------------------------------------------------------------------------

create trigger plans_set_updated_at
before update on app.plans
for each row execute function app.set_updated_at();

create trigger tenants_set_updated_at
before update on app.tenants
for each row execute function app.set_updated_at();

create trigger tenant_settings_set_updated_at
before update on app.tenant_settings
for each row execute function app.set_updated_at();

create trigger tenant_features_set_updated_at
before update on app.tenant_features
for each row execute function app.set_updated_at();

create trigger memberships_set_updated_at
before update on app.memberships
for each row execute function app.set_updated_at();

create trigger customers_set_updated_at
before update on app.customers
for each row execute function app.set_updated_at();

-- ---------------------------------------------------------------------------
-- RLS forzado
-- ---------------------------------------------------------------------------

-- `plans` es catálogo de plataforma, no dato de tenant: sin RLS.
-- app_rw solo recibe SELECT; service_role administra los planes.

alter table app.tenants enable row level security;
alter table app.tenants force row level security;
create policy tenants_self on app.tenants
    using (id = app.current_tenant())
    with check (id = app.current_tenant());

alter table app.domains enable row level security;
alter table app.domains force row level security;
create policy domains_tenant_isolation on app.domains
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

alter table app.tenant_settings enable row level security;
alter table app.tenant_settings force row level security;
create policy tenant_settings_tenant_isolation on app.tenant_settings
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

alter table app.tenant_features enable row level security;
alter table app.tenant_features force row level security;
create policy tenant_features_tenant_isolation on app.tenant_features
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

alter table app.memberships enable row level security;
alter table app.memberships force row level security;
create policy memberships_tenant_isolation on app.memberships
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

alter table app.customers enable row level security;
alter table app.customers force row level security;
create policy customers_tenant_isolation on app.customers
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

alter table app.addresses enable row level security;
alter table app.addresses force row level security;
create policy addresses_tenant_isolation on app.addresses
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

alter table app.auth_events enable row level security;
alter table app.auth_events force row level security;
create policy auth_events_tenant_isolation on app.auth_events
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

alter table app.platform_admins enable row level security;
alter table app.platform_admins force row level security;
-- Sin política para app_rw: solo la función SECURITY DEFINER puede consultar.

-- ---------------------------------------------------------------------------
-- Grants
-- ---------------------------------------------------------------------------

grant select on app.plans to app_rw;

grant select, update on app.tenants to app_rw;

grant select, insert, update, delete on app.domains to app_rw;
grant select, insert, update, delete on app.tenant_settings to app_rw;
grant select, insert, update, delete on app.tenant_features to app_rw;
grant select, insert, update, delete on app.memberships to app_rw;
grant select, insert, update, delete on app.customers to app_rw;
grant select, insert, update, delete on app.addresses to app_rw;

-- Auditoría append-only: sin UPDATE/DELETE.
grant select, insert on app.auth_events to app_rw;

revoke all on function app.current_tenant() from public;
revoke all on function app.resolve_tenant(text) from public;
revoke all on function app.is_platform_admin(uuid) from public;
revoke all on function app.create_tenant(text, text, text, text, uuid) from public;

grant execute on function app.current_tenant() to app_rw;
grant execute on function app.resolve_tenant(text) to app_rw;
grant execute on function app.is_platform_admin(uuid) to app_rw;
grant execute on function app.create_tenant(text, text, text, text, uuid) to app_rw;
