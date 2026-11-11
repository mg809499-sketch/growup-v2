begin;

create schema if not exists extensions;
create extension if not exists pgtap with schema extensions;
grant usage on schema extensions to app_rw;
grant execute on all functions in schema extensions to app_rw;
set search_path = public, extensions;

select plan(9);

-- Setup como postgres (superuser)
select app.create_tenant('ropa', 'ropa.growup.com', 'Ropa') as ropa_id \gset
select app.create_tenant('joyeria', 'joyeria.growup.com', 'Joyería') as joyeria_id \gset

select is(
  (select status from app.tenants where id = :'ropa_id'),
  'trialing',
  'el tenant ropa queda en trialing por defecto'
);

update app.tenants set status = 'suspended' where id = :'ropa_id';
select is(
  (select count(*)::int from app.resolve_tenant('ropa.growup.com')),
  0,
  'tenant suspendido no resuelve'
);

update app.tenants set status = 'past_due' where id = :'ropa_id';
select is(
  (select count(*)::int from app.resolve_tenant('ropa.growup.com')),
  1,
  'tenant past_due aún resuelve (período de gracia)'
);

update app.tenants set status = 'active' where id = :'ropa_id';
select is(
  (select count(*)::int from app.resolve_tenant('ropa.growup.com')),
  1,
  'tenant activo resuelve'
);

-- FK compuesta (probada como superuser: es la defensa en profundidad, no RLS)
insert into app.customers (tenant_id, email) values (:'joyeria_id', 'cliente@joyeria.test');
prepare cross_tenant_address as
  insert into app.addresses (tenant_id, customer_id, name, line1, city, state)
  select :'ropa_id'::uuid, c.id, 'Intruso', 'Calle 1', 'Bogotá', 'DC'
  from app.customers c
  where c.tenant_id = :'joyeria_id'::uuid;
select throws_ok(
  'cross_tenant_address',
  '23503',
  'FK compuesta rechaza dirección a customer de otro tenant'
);

-- app_rw ya no puede mutar columnas de negocio de tenants
set local role app_rw;
select set_config('app.tenant_id', :'ropa_id', true);
prepare escalate_tenant as
  update app.tenants set status = 'suspended' where id = :'ropa_id'::uuid;
select throws_ok(
  'escalate_tenant',
  '42501',
  'app_rw no puede mutar columnas de negocio de tenants'
);
reset role;

select has_index('app', 'memberships', 'memberships_user_idx', 'memberships_user_idx existe');
select has_index('app', 'media_variants', 'media_variants_tenant_asset_idx', 'media_variants_tenant_asset_idx existe');
select has_index('app', 'media_variants', 'media_variants_tenant_id_uidx', 'media_variants_tenant_id_uidx existe');

select * from finish();
rollback;
