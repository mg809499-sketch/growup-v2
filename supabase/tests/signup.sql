begin;

create schema if not exists extensions;
create extension if not exists pgtap with schema extensions;
grant usage on schema extensions to app_rw;
grant execute on all functions in schema extensions to app_rw;
set search_path = public, extensions;

select plan(11);

select app.complete_client_signup(
    'a1111111-1111-4111-8111-111111111111',
    'OwnerSignup@Example.com',
    'Duena Signup',
    '+57 300 123 4567',
    'CC',
    '1234567890',
    'Tienda Signup',
    'ropa',
    'starter',
    'signup-test',
    'signup-test.growup.com',
    'subdomain',
    null,
    true
) as tenant_id \gset

select ok(:'tenant_id' <> '', 'complete_client_signup devuelve un tenant');

select is(
    (select role from app.clients where user_id = 'a1111111-1111-4111-8111-111111111111'),
    'owner',
    'el alta crea la fila en clients con rol owner'
);

select is(
    (
        select email from app.clients
        where user_id = 'a1111111-1111-4111-8111-111111111111'
    ),
    'ownersignup@example.com',
    'el correo se normaliza a minúsculas'
);

select is(
    (
        select status from app.memberships
        where tenant_id = :'tenant_id'
          and user_id = 'a1111111-1111-4111-8111-111111111111'
    ),
    'active',
    'la membership owner queda activa'
);

select is(
    (
        select host from app.domains
        where tenant_id = :'tenant_id' and is_primary
    ),
    'signup-test.growup.com',
    'el subdominio growup.com queda como dominio principal'
);

select app.complete_client_signup(
    'a2222222-2222-4222-8222-222222222222',
    'custom@example.com',
    'Duena Dominio',
    '+57 300 765 4321',
    'NIT',
    '900123456',
    'Tienda Custom',
    'joyeria',
    'pro',
    'signup-custom',
    'signup-custom.growup.com',
    'custom',
    'www.mitienda.co',
    false
) as tenant_custom \gset

select is(
    (
        select host from app.domains
        where tenant_id = :'tenant_custom' and type = 'custom' and not is_primary
    ),
    'www.mitienda.co',
    'el dominio propio queda registrado, sin verificar, como secundario'
);

select throws_ok(
    format(
        'select app.complete_client_signup(%L, %L, %L, %L, %L, %L, %L, %L, %L, %L, %L, %L, %L, %L)',
        'a1111111-1111-4111-8111-111111111111',
        'otro@example.com', 'Otra Persona', '3001112233', 'CC', '111222333',
        'Tienda Reintentada', 'ropa', 'starter', 'signup-otro',
        'signup-otro.growup.com', 'subdomain', null, false
    ),
    '23505',
    null,
    'un segundo alta con el mismo usuario falla (idempotencia)'
);

select throws_ok(
    format(
        'select app.complete_client_signup(%L, %L, %L, %L, %L, %L, %L, %L, %L, %L, %L, %L, %L, %L)',
        'a3333333-3333-4333-8333-333333333333',
        'slug@example.com', 'Slug Tomado', '3001112233', 'CC', '111222333',
        'Otra Tienda', 'ropa', 'starter', 'signup-test',
        'signup-test.growup.com', 'subdomain', null, false
    ),
    '23505',
    null,
    'un slug ya tomado falla'
);

select throws_ok(
    format(
        'select app.complete_client_signup(%L, %L, %L, %L, %L, %L, %L, %L, %L, %L, %L, %L, %L, %L)',
        'a4444444-4444-4444-8444-444444444444',
        'plan@example.com', 'Plan Malo', '3001112233', 'CC', '111222333',
        'Tienda Plan', 'ropa', 'plan-inexistente', 'signup-plan',
        'signup-plan.growup.com', 'subdomain', null, false
    ),
    'P0001',
    'PLAN_NOT_FOUND',
    'un plan inexistente o inactivo falla'
);

set local role app_rw;
select throws_ok(
    'select * from app.clients',
    '42501',
    null,
    'app_rw no tiene acceso directo a app.clients'
);
reset role;

select ok(
    (
        select proconfig::text like '%pg_catalog%'
           and proconfig::text not like '%public%'
        from pg_proc
        where oid = 'app.complete_client_signup(uuid, text, text, text, text, text, text, text, text, text, text, text, text, boolean)'::regprocedure
    ),
    'complete_client_signup usa pg_catalog y app, sin public'
);

select * from finish();
rollback;
