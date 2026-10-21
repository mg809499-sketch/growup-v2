begin;

create schema if not exists extensions;
create extension if not exists pgtap with schema extensions;
grant usage on schema extensions to app_rw;
grant execute on all functions in schema extensions to app_rw;
set search_path = public, extensions;

select plan(17);

-- Setup como postgres (superuser): crea dos tenants vía la función controlada.
select app.create_tenant('ropa', 'ropa.growup.com', 'Ropa') as ropa_id \gset
select app.create_tenant('joyeria', 'joyeria.growup.com', 'Joyería') as joyeria_id \gset

-- Resolución de host.
select is(
    (select id from app.resolve_tenant('ropa.growup.com')),
    :'ropa_id'::uuid,
    'resolve_tenant resuelve ropa'
);
select is(
    (select id from app.resolve_tenant('JOYERIA.GROWUP.COM')),
    :'joyeria_id'::uuid,
    'resolve_tenant normaliza mayúsculas'
);
select is(
    (select count(*)::int from app.resolve_tenant('nadie.growup.com')),
    0::int,
    'resolve_tenant devuelve vacío para host desconocido'
);

-- Contexto del tenant A como app_rw (sin BYPASSRLS).
set local role app_rw;
select set_config('app.tenant_id', :'ropa_id', true);

select is(
    (select count(*)::int from app.plans),
    2,
    'app_rw puede leer el catálogo de planes'
);

select is(
    (select count(*)::int from app.tenants),
    1::int,
    'tenant A ve solo su tenant'
);
select is(
    (select count(*)::int from app.domains),
    1::int,
    'tenant A ve solo su dominio'
);
select is(
    (select count(*)::int from app.tenant_settings),
    1::int,
    'tenant A ve solo sus settings'
);
select is(
    (select count(*)::int from app.memberships),
    0::int,
    'tenant A no ve memberships ajenas'
);
select is(
    (select count(*)::int from app.customers),
    0::int,
    'tenant A no ve customers ajenos'
);
select is(
    (select count(*)::int from app.domains where tenant_id = :'joyeria_id'::uuid),
    0::int,
    'tenant A no ve dominios de B'
);

select throws_ok(
    format(
        'insert into app.domains (tenant_id, host) values (%L, %L)',
        :'joyeria_id',
        'hack.growup.com'
    ),
    '42501',
    null,
    'RLS bloquea insert cross-tenant'
);

select throws_ok(
    $$ insert into app.tenants (slug, name) values ('hack', 'Hack') $$,
    '42501',
    null,
    'app_rw no puede insertar tenants directamente'
);

select ok(
    (select not rolbypassrls from pg_roles where rolname = 'app_rw'),
    'app_rw no tiene BYPASSRLS'
);

-- Contexto del tenant B.
select set_config('app.tenant_id', :'joyeria_id', true);

select is(
    (select count(*)::int from app.tenants),
    1::int,
    'tenant B ve solo su tenant'
);
select is(
    (select count(*)::int from app.domains),
    1::int,
    'tenant B ve solo su dominio'
);
select is(
    (select count(*)::int from app.customers),
    0::int,
    'tenant B no ve customers ajenos'
);

-- La función SECURITY DEFINER permite crear tenants; la autorización de
-- plataforma se valida en la API antes de llamarla.
select lives_ok(
    format(
        'select app.create_tenant(%L, %L, %L)',
        'nuevo',
        'nuevo.growup.com',
        'Nuevo'
    ),
    'app_rw puede crear tenant vía función'
);

select * from finish();
rollback;
