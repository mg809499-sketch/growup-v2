begin;

create schema if not exists extensions;
create extension if not exists pgtap with schema extensions;
grant usage on schema extensions to app_rw;
grant execute on all functions in schema extensions to app_rw;
set search_path = public, extensions;

select plan(9);

select app.create_tenant('inv-a', 'inv-a.growup.com', 'Inv A') as tenant_a \gset
select app.create_tenant('inv-b', 'inv-b.growup.com', 'Inv B') as tenant_b \gset

select id as location_a
from app.locations
where tenant_id = :'tenant_a' and is_default
\gset

select id as location_b
from app.locations
where tenant_id = :'tenant_b' and is_default
\gset

set local role app_rw;
select set_config('app.tenant_id', :'tenant_a', true);

insert into app.products (tenant_id, slug, name, status)
values (:'tenant_a', 'camiseta-inv', 'Camiseta', 'active')
returning id as product_a \gset

insert into app.product_variants (tenant_id, product_id, sku, name, price_cents)
values (:'tenant_a', :'product_a', 'SKU-INV-1', 'M', 1000)
returning id as variant_a \gset

insert into app.inventory_levels (tenant_id, variant_id, location_id, available)
values (:'tenant_a', :'variant_a', :'location_a', 10);

select lives_ok(
    format(
        'insert into app.inventory_reservations '
        '(tenant_id, variant_id, location_id, quantity, expires_at) '
        'values (%L, %L, %L, 2, now() + interval ''15 minutes'')',
        :'tenant_a', :'variant_a', :'location_a'
    ),
    'reserva válida con ubicación explícita'
);

select id as reservation_a
from app.inventory_reservations
where tenant_id = :'tenant_a'
limit 1
\gset

select throws_ok(
    format(
        'insert into app.inventory_reservations '
        '(tenant_id, variant_id, location_id, quantity, expires_at) '
        'values (%L, %L, null, 1, now() + interval ''15 minutes'')',
        :'tenant_a', :'variant_a'
    ),
    '23502',
    null,
    'location_id es obligatorio'
);

select throws_ok(
    format(
        'insert into app.inventory_reservations '
        '(tenant_id, variant_id, location_id, quantity, expires_at) '
        'values (%L, %L, %L, 0, now() + interval ''15 minutes'')',
        :'tenant_a', :'variant_a', :'location_a'
    ),
    '23514',
    null,
    'quantity debe ser positiva'
);

select throws_ok(
    format(
        'insert into app.inventory_reservations '
        '(tenant_id, variant_id, location_id, quantity, expires_at) '
        'values (%L, %L, %L, 1, now() + interval ''15 minutes'')',
        :'tenant_a', :'variant_a', :'location_b'
    ),
    '23503',
    null,
    'no se reserva con ubicación de otro tenant'
);

select throws_ok(
    format(
        'update app.inventory_levels set reserved = available + 1 '
        'where tenant_id = %L and variant_id = %L',
        :'tenant_a', :'variant_a'
    ),
    '23514',
    null,
    'reserved no puede superar available'
);

select set_config('app.tenant_id', :'tenant_b', true);

select throws_ok(
    format(
        'insert into app.inventory_reservations '
        '(tenant_id, variant_id, location_id, quantity, expires_at) '
        'values (%L, %L, %L, 1, now() + interval ''15 minutes'')',
        :'tenant_a', :'variant_a', :'location_a'
    ),
    '42501',
    null,
    'inserción con tenant ajeno falla por RLS'
);

select is(
    (
        select count(*)::int
        from app.inventory_reservations
    ),
    0,
    'tenant B no ve reservas de A'
);

update app.inventory_reservations
set quantity = 9
where tenant_id = :'tenant_a' and id = :'reservation_a';

reset role;

select is(
    (
        select quantity
        from app.inventory_reservations
        where id = :'reservation_a'
    ),
    2,
    'tenant B no actualiza reservas de A'
);

set local role app_rw;
select set_config('app.tenant_id', :'tenant_b', true);

delete from app.inventory_reservations
where tenant_id = :'tenant_a' and id = :'reservation_a';

reset role;

select is(
    (
        select count(*)::int
        from app.inventory_reservations
        where id = :'reservation_a'
    ),
    1,
    'tenant B no borra reservas de A'
);

select * from finish();
rollback;
