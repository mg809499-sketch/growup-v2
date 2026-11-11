-- Hardening 2026-11-10: FK compuesta en direcciones, grants a nivel columna en tenants,
-- índice memberships(user_id), unicidades y índices en media_variants, filtro de estado en resolve_tenant.

-- F2-03a: la FK de direcciones pasa al patrón (tenant_id, ...) → customers (tenant_id, id).
alter table app.customers
  add constraint customers_tenant_id_id_key unique (tenant_id, id);

alter table app.addresses
  drop constraint addresses_customer_id_fkey,
  add constraint addresses_tenant_customer_fk
    foreign key (tenant_id, customer_id)
    references app.customers (tenant_id, id)
    on delete cascade;

-- F2-03b: el rol de la API ya no puede mutar columnas de negocio de app.tenants
-- (plan_id, status, trial_ends_at, slug, ...). Las transiciones viven en funciones
-- SECURITY DEFINER (create_tenant_with_owner, suspensiones vía billing/worker).
revoke update on app.tenants from app_rw;

-- F2-14a: memberships por usuario ("mis tenants") y por estado dentro del tenant.
create index if not exists memberships_user_idx on app.memberships (user_id);
create index if not exists memberships_tenant_status_idx on app.memberships (tenant_id, status);

-- F2-14b: media_variants integridad y consulta por tenant/asset.
create unique index if not exists media_variants_tenant_id_uidx on app.media_variants (tenant_id, id);
create index if not exists media_variants_tenant_asset_idx on app.media_variants (tenant_id, media_asset_id);

-- F2-01: los tenants suspendidos/cancelados no resuelven en el storefront ni en bootstrap.
-- Estados que sirven: trialing (en prueba) y active. past_due aún sirve (período de gracia).
create or replace function app.resolve_tenant(p_host text)
returns table (id uuid, slug text, name text, status text)
language sql
security definer
set search_path = pg_catalog, app
as $$
  select t.id, t.slug, t.name, t.status
  from app.domains d
  join app.tenants t on t.id = d.tenant_id
  where d.host = lower(p_host)
    and t.status in ('trialing', 'active', 'past_due')
$$;
