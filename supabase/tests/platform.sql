begin;

create schema if not exists extensions;
create extension if not exists pgtap with schema extensions;
grant usage on schema extensions to app_rw;
grant execute on all functions in schema extensions to app_rw;
set search_path = public, extensions;

select plan(8);

select app.create_tenant(
    'platform-list-a',
    'platform-list-a.growup.com',
    'Platform List A'
) as tenant_a \gset

select app.create_tenant(
    'platform-list-b',
    'platform-list-b.growup.com',
    'Platform List B'
) as tenant_b \gset

insert into app.platform_admins (user_id, email, role)
values (
    '00000000-0000-0000-0000-000000000001',
    'platform-list@example.com',
    'owner'
);

set local role app_rw;
select set_config('app.actor_id', '00000000-0000-0000-0000-000000000001', true);

select is(
    (
        select count(*)::int
        from app.list_tenants('00000000-0000-0000-0000-000000000001')
    ),
    2,
    'platform admin ve todos los tenants'
);

select is(
    (
        select host
        from app.list_tenants('00000000-0000-0000-0000-000000000001')
        where slug = 'platform-list-a'
    ),
    'platform-list-a.growup.com',
    'el listado resuelve el host primario'
);

select is(
    (
        select count(*)::int
        from app.list_tenants(
            '00000000-0000-0000-0000-000000000001',
            null,
            'Platform List A'
        )
    ),
    1,
    'la búsqueda filtra por nombre'
);

select is(
    (
        select total_count
        from app.list_tenants(
            '00000000-0000-0000-0000-000000000001',
            null,
            null,
            1,
            1
        )
    ),
    2::bigint,
    'total_count refleja el total antes de paginar'
);

select is(
    (
        select count(*)::int
        from app.list_tenants(
            '00000000-0000-0000-0000-000000000001',
            null,
            null,
            1,
            1
        )
    ),
    1,
    'limit y offset paginan el listado'
);

select set_config('app.actor_id', '00000000-0000-0000-0000-000000000002', true);
select throws_ok(
    format(
        'select * from app.list_tenants(%L)',
        '00000000-0000-0000-0000-000000000002'
    ),
    '42501',
    'platform admin required',
    'un usuario sin platform admin no lista tenants'
);

select set_config('app.actor_id', '00000000-0000-0000-0000-000000000001', true);
select throws_ok(
    format(
        'select * from app.list_tenants(%L)',
        '00000000-0000-0000-0000-000000000002'
    ),
    '42501',
    'platform admin required',
    'el actor del argumento debe coincidir con la identidad verificada'
);

select throws_ok(
    format(
        'select * from app.list_tenants(%L, null, null, 0)',
        '00000000-0000-0000-0000-000000000001'
    ),
    'P0001',
    'limit must be between 1 and 100',
    'un límite fuera de rango falla'
);

select * from finish();
rollback;
