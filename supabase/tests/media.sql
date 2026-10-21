begin;

create schema if not exists extensions;
create extension if not exists pgtap with schema extensions;
grant usage on schema extensions to app_rw;
grant execute on all functions in schema extensions to app_rw;
set search_path = public, extensions;

select plan(8);

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

select * from finish();
rollback;
