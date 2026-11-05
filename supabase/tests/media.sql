begin;

create schema if not exists extensions;
create extension if not exists pgtap with schema extensions;
grant usage on schema extensions to app_rw;
grant execute on all functions in schema extensions to app_rw;
grant usage on schema extensions to app_worker;
grant execute on all functions in schema extensions to app_worker;
set search_path = public, extensions;

select plan(14);

select app.create_tenant('media-a', 'media-a.growup.com', 'Media A') as tenant_a \gset
select app.create_tenant('media-b', 'media-b.growup.com', 'Media B') as tenant_b \gset

set local role app_rw;
select set_config('app.tenant_id', :'tenant_a', true);

insert into app.media_assets
    (tenant_id, r2_key, mime, size_bytes, original_filename)
values (
    :'tenant_a',
    'tenant/' || :'tenant_a' || '/originals/a.jpg',
    'image/jpeg',
    100,
    'a.jpg'
)
returning id as asset_a \gset

select is(
    (select count(*)::int from app.media_assets),
    1,
    'tenant A ve su media asset'
);

select set_config('app.tenant_id', :'tenant_b', true);

select is(
    (select count(*)::int from app.media_assets),
    0,
    'tenant B no ve media assets de A'
);

select throws_ok(
    format(
        'insert into app.media_assets '
        '(tenant_id, r2_key, mime, size_bytes) '
        'values (%L, %L, %L, 100)',
        :'tenant_a', 'tenant/otro/originals/b.jpg', 'image/jpeg'
    ),
    '42501',
    null,
    'tenant B no inserta un asset de A'
);

update app.media_assets
set alt = 'hacked'
where tenant_id = :'tenant_a' and id = :'asset_a';

delete from app.media_assets
where tenant_id = :'tenant_a' and id = :'asset_a';

reset role;

select is(
    (select alt from app.media_assets where id = :'asset_a'),
    null,
    'tenant B no actualiza el asset de A'
);

select is(
    (select count(*)::int from app.media_assets where id = :'asset_a'),
    1,
    'tenant B no borra el asset de A'
);

set local role app_rw;
select set_config('app.tenant_id', :'tenant_a', true);

insert into app.media_variants
    (tenant_id, media_asset_id, format, width, height, r2_key, size_bytes)
values (
    :'tenant_a',
    :'asset_a',
    'webp',
    320,
    240,
    'tenant/' || :'tenant_a' || '/variants/a/320.webp',
    10
);

select is(
    (select count(*)::int from app.media_variants),
    1,
    'tenant A ve su variante'
);

select set_config('app.tenant_id', :'tenant_b', true);

select is(
    (select count(*)::int from app.media_variants),
    0,
    'tenant B no ve variantes de A'
);

select throws_ok(
    format(
        'insert into app.media_variants '
        '(tenant_id, media_asset_id, format, width, height, r2_key, size_bytes) '
        'values (%L, %L, %L, 320, 240, %L, 10)',
        :'tenant_a', :'asset_a', 'webp', 'tenant/otro/variants/a/320.webp'
    ),
    '42501',
    null,
    'tenant B no inserta una variante de A'
);

select set_config('app.tenant_id', :'tenant_a', true);

insert into app.products (tenant_id, slug, name, status)
values (:'tenant_a', 'media-product-a', 'Media Product A', 'draft')
returning id as product_a \gset

insert into app.products (tenant_id, slug, name, status)
values (:'tenant_a', 'media-product-a2', 'Media Product A2', 'draft')
returning id as product_a2 \gset

insert into app.product_media
    (tenant_id, product_id, media_asset_id, position, is_primary)
values (:'tenant_a', :'product_a', :'asset_a', 0, true);

select is(
    (select count(*)::int from app.product_media),
    1,
    'tenant A ve su asociación producto-media'
);

select set_config('app.tenant_id', :'tenant_b', true);

select is(
    (select count(*)::int from app.product_media),
    0,
    'tenant B no ve asociaciones de A'
);

select throws_ok(
    format(
        'insert into app.product_media '
        '(tenant_id, product_id, media_asset_id, position, is_primary) '
        'values (%L, %L, %L, 0, false)',
        :'tenant_a', :'product_a2', :'asset_a'
    ),
    '42501',
    null,
    'tenant B no inserta una asociación de A'
);

select set_config('app.tenant_id', :'tenant_a', true);

insert into app.media_assets
    (tenant_id, r2_key, mime, size_bytes, original_filename, status, updated_at)
values (
    :'tenant_a',
    'tenant/' || :'tenant_a' || '/originals/stale.jpg',
    'image/jpeg',
    100,
    'stale.jpg',
    'uploading',
    now() - interval '2 hours'
)
returning id as asset_stale \gset

insert into app.media_assets
    (tenant_id, r2_key, mime, size_bytes, original_filename, status)
values (
    :'tenant_a',
    'tenant/' || :'tenant_a' || '/originals/fresh.jpg',
    'image/jpeg',
    100,
    'fresh.jpg',
    'uploading'
)
returning id as asset_fresh \gset

reset role;
set local role app_worker;
select app.expire_stale_uploads(3600);
reset role;
set local role app_rw;
select set_config('app.tenant_id', :'tenant_a', true);

select is(
    (select status from app.media_assets where id = :'asset_stale'),
    'failed',
    'el upload vencido queda en failed'
);

select is(
    (select status from app.media_assets where id = :'asset_fresh'),
    'uploading',
    'el upload reciente sigue uploading'
);

reset role;
set local role app_worker;
select throws_ok(
    'select app.expire_stale_uploads(10)',
    'P0001',
    'max_age_seconds must be at least 60',
    'la limpieza exige un TTL mínimo de 60 segundos'
);
reset role;

select * from finish();
rollback;
