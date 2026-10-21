begin;

create schema if not exists extensions;
create extension if not exists pgtap with schema extensions;
grant usage on schema extensions to app_rw;
grant execute on all functions in schema extensions to app_rw;
set search_path = public, extensions;

select plan(14);

select app.create_tenant('cat-a', 'cat-a.growup.com', 'Cat A') as tenant_a \gset
select app.create_tenant('cat-b', 'cat-b.growup.com', 'Cat B') as tenant_b \gset

set local role app_rw;
select set_config('app.tenant_id', :'tenant_a', true);

insert into app.categories (tenant_id, slug, name)
values (:'tenant_a', 'ropa', 'Ropa')
returning id as category_a \gset

insert into app.products (tenant_id, category_id, slug, name, status)
values (:'tenant_a', :'category_a', 'camiseta', 'Camiseta', 'active')
returning id as product_a \gset

insert into app.product_variants (tenant_id, product_id, sku, name, price_cents)
values (:'tenant_a', :'product_a', 'CAM-1', 'M', 8900000)
returning id as variant_a \gset

select id as location_a
from app.locations
where tenant_id = :'tenant_a' and is_default
\gset

insert into app.inventory_levels (tenant_id, variant_id, location_id, available)
values (:'tenant_a', :'variant_a', :'location_a', 10);

select is(
    (select count(*)::int from app.categories),
    1,
    'tenant A ve su categoría'
);
select is(
    (select count(*)::int from app.products),
    1,
    'tenant A ve su producto'
);
select is(
    (select count(*)::int from app.product_variants),
    1,
    'tenant A ve su variante'
);
select is(
    (select min_price_cents::int from app.products where id = :'product_a'),
    8900000,
    'el trigger actualiza el precio mínimo'
);
select is(
    (select available from app.inventory_levels where variant_id = :'variant_a'),
    10,
    'el stock inicial queda disponible'
);
select is(
    (select count(*)::int from app.locations),
    1,
    'el tenant tiene una ubicación default'
);

-- Contexto B: no ve nada de A.
select set_config('app.tenant_id', :'tenant_b', true);

select is(
    (select count(*)::int from app.categories),
    0,
    'tenant B no ve categorías de A'
);
select is(
    (select count(*)::int from app.products),
    0,
    'tenant B no ve productos de A'
);
select is(
    (select count(*)::int from app.product_variants),
    0,
    'tenant B no ve variantes de A'
);

select throws_ok(
    format(
        'insert into app.categories (tenant_id, slug, name) values (%L, %L, %L)',
        :'tenant_a',
        'hack',
        'Hack'
    ),
    '42501',
    null,
    'RLS bloquea categoría cross-tenant'
);

select throws_ok(
    format(
        'insert into app.products (tenant_id, category_id, slug, name) values (%L, %L, %L, %L)',
        :'tenant_a',
        :'category_a',
        'hack',
        'Hack'
    ),
    '42501',
    null,
    'RLS bloquea producto cross-tenant'
);

-- Crea una categoría de B para probar la FK compuesta.
insert into app.categories (tenant_id, slug, name)
values (:'tenant_b', 'joyeria', 'Joyería')
returning id as category_b \gset

select is(
    (select count(*)::int from app.categories),
    1,
    'tenant B ve su propia categoría'
);

-- Vuelve a A e intenta usar la categoría de B: la FK compuesta lo impide.
select set_config('app.tenant_id', :'tenant_a', true);

select throws_ok(
    format(
        'insert into app.products (tenant_id, category_id, slug, name) values (%L, %L, %L, %L)',
        :'tenant_a',
        :'category_b',
        'hack-fk',
        'Hack FK'
    ),
    '23503',
    null,
    'FK compuesta impide categoría de otro tenant'
);

select is(
    (select count(*)::int from app.categories),
    1,
    'tenant A sigue viendo solo su categoría'
);

select * from finish();
rollback;
