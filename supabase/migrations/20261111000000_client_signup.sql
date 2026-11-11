-- Signup self-service de comerciantes (ADR-0019, 2026-11-11).
--
-- app.clients: CRM de comerciantes de la plataforma (no es dato de tenant, como
-- app.plans). Identidad del alta = user_id = auth.users.id; sin FK a auth.users
-- por paridad con app.memberships (ningun FK cross-schema a auth).
--
-- app.complete_client_signup(): alta atomica
--   usuarios (JWT Google, sub) -> tenant (trialing) -> membership owner
--   -> app.clients -> auth.users.raw_app_meta_data (tenant_id, role)
-- Todo en una transaccion; si cualquier paso falla, no queda nada creado.
-- app.clients no tiene grants para app_rw: toda escritura pasa por esta
-- funcion SECURITY DEFINER acotada (mismo patron que app.platform_admins).

create table app.clients (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null unique,
    email text not null,
    full_name text not null,
    phone text not null,
    doc_type text not null check (doc_type in ('CC', 'CE', 'NIT', 'PP')),
    doc_number text not null,
    store_name text not null,
    store_type text not null check (store_type in ('ropa', 'joyeria', 'otro')),
    plan_code text not null references app.plans(code),
    role text not null default 'owner' check (role = 'owner'),
    desired_slug text not null,
    domain_choice text not null check (domain_choice in ('subdomain', 'custom')),
    wants_subdomain boolean not null default false,
    custom_domain text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    constraint clients_custom_domain_required
        check (domain_choice <> 'custom' or custom_domain is not null),
    constraint clients_custom_domain_format
        check (custom_domain is null or custom_domain = lower(custom_domain))
);

comment on table app.clients is 'CRM de comerciantes de la plataforma Growup (altas self-service). No es dato de tenant.';

create trigger clients_set_updated_at
before update on app.clients
for each row execute function app.set_updated_at();

alter table app.clients enable row level security;
alter table app.clients force row level security;
-- Sin politica para app_rw: solo la funcion SECURITY DEFINER accede.

revoke all on app.clients from public;
-- Sin grant a app_rw (paridad con app.platform_admins).

create index clients_plan_code_idx on app.clients (plan_code);

-- ---------------------------------------------------------------------------
-- Alta atomica de comerciante
-- ---------------------------------------------------------------------------

create or replace function app.complete_client_signup(
    p_user_id uuid,
    p_email text,
    p_full_name text,
    p_phone text,
    p_doc_type text,
    p_doc_number text,
    p_store_name text,
    p_store_type text,
    p_plan_code text,
    p_slug text,
    p_host text,
    p_domain_choice text,
    p_custom_domain text,
    p_wants_subdomain boolean
)
returns uuid
language plpgsql
security definer
set search_path = pg_catalog, app
as $$
declare
    v_plan_id uuid;
    v_tenant_id uuid;
begin
    select id into v_plan_id from app.plans where code = p_plan_code and is_active;
    if v_plan_id is null then
        raise exception 'PLAN_NOT_FOUND';
    end if;

    v_tenant_id := app.create_tenant_with_owner(
        p_slug, p_host, p_store_name, null, v_plan_id, p_user_id, p_email
    );

    if p_domain_choice = 'custom' then
        insert into app.domains (tenant_id, host, type, is_primary, verified_at)
        values (v_tenant_id, lower(p_custom_domain), 'custom', false, null);
    end if;

    insert into app.clients (
        user_id, email, full_name, phone, doc_type, doc_number,
        store_name, store_type, plan_code, role,
        desired_slug, domain_choice, wants_subdomain, custom_domain
    ) values (
        p_user_id, lower(p_email), p_full_name, p_phone, p_doc_type, p_doc_number,
        p_store_name, p_store_type, p_plan_code, 'owner',
        p_slug, p_domain_choice, coalesce(p_wants_subdomain, false),
        case when p_domain_choice = 'custom' then lower(p_custom_domain) else null end
    );

    update auth.users
    set raw_app_meta_data = coalesce(raw_app_meta_data, '{}'::jsonb)
        || jsonb_build_object('tenant_id', v_tenant_id, 'role', 'owner')
    where id = p_user_id;

    return v_tenant_id;
end;
$$;

revoke all on function app.complete_client_signup(
    uuid, text, text, text, text, text, text, text, text, text, text, text, text, boolean
) from public;

grant execute on function app.complete_client_signup(
    uuid, text, text, text, text, text, text, text, text, text, text, text, text, boolean
) to app_rw;
