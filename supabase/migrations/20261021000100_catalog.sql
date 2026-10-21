-- Catálogo: categorías, productos, variantes, media e inventario.
-- Depende de la migración core_tenancy.

-- ---------------------------------------------------------------------------
-- Categorías
-- ---------------------------------------------------------------------------

create table app.categories (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    parent_id uuid,
    slug text not null,
    name text not null,
    description text,
    position integer not null default 0,
    seo jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (tenant_id, slug),
    constraint categories_slug_format
        check (slug ~ '^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$')
);

alter table app.categories
    add constraint categories_tenant_id_id_key unique (tenant_id, id);

alter table app.categories
    add constraint categories_parent_fk
    foreign key (tenant_id, parent_id)
    references app.categories (tenant_id, id);

create index categories_tenant_position_idx
    on app.categories (tenant_id, position);

-- ---------------------------------------------------------------------------
-- Productos y variantes
-- ---------------------------------------------------------------------------

create table app.products (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    category_id uuid,
    slug text not null,
    name text not null,
    description text,
    status text not null default 'draft'
        check (status in ('draft', 'active', 'archived')),
    brand text,
    tags text[] not null default '{}',
    seo jsonb not null default '{}'::jsonb,
    min_price_cents bigint not null default 0 check (min_price_cents >= 0),
    max_price_cents bigint not null default 0 check (max_price_cents >= 0),
    search_vector tsvector generated always as (
        setweight(to_tsvector('spanish', coalesce(name, '')), 'A') ||
        setweight(to_tsvector('spanish', coalesce(description, '')), 'B')
    ) stored,
    published_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (tenant_id, slug),
    constraint products_slug_format
        check (slug ~ '^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$')
);

alter table app.products
    add constraint products_tenant_id_id_key unique (tenant_id, id);

alter table app.products
    add constraint products_category_fk
    foreign key (tenant_id, category_id)
    references app.categories (tenant_id, id);

create index products_tenant_status_created_idx
    on app.products (tenant_id, status, created_at desc, id desc);
create index products_search_idx
    on app.products using gin (search_vector);
create index products_tags_idx
    on app.products using gin (tags);
create index products_category_idx
    on app.products (tenant_id, category_id);

create table app.product_variants (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    product_id uuid not null,
    sku text not null,
    name text not null,
    price_cents bigint not null check (price_cents > 0),
    compare_at_price_cents bigint
        check (compare_at_price_cents is null or compare_at_price_cents >= price_cents),
    cost_cents bigint check (cost_cents is null or cost_cents >= 0),
    currency text not null default 'COP' check (currency = 'COP'),
    weight_grams integer check (weight_grams is null or weight_grams >= 0),
    option_values jsonb not null default '{}'::jsonb,
    position integer not null default 0,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (tenant_id, sku),
    unique (tenant_id, id)
);

alter table app.product_variants
    add constraint product_variants_product_fk
    foreign key (tenant_id, product_id)
    references app.products (tenant_id, id)
    on delete cascade;

create index product_variants_tenant_product_idx
    on app.product_variants (tenant_id, product_id);

-- ---------------------------------------------------------------------------
-- Media
-- ---------------------------------------------------------------------------

create table app.media_assets (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    r2_key text not null,
    mime text not null,
    size_bytes bigint not null check (size_bytes >= 0),
    width integer check (width is null or width > 0),
    height integer check (height is null or height > 0),
    alt text,
    blurhash text,
    status text not null default 'uploading'
        check (status in ('uploading', 'ready', 'failed')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (tenant_id, r2_key),
    unique (tenant_id, id)
);

create index media_assets_tenant_status_idx
    on app.media_assets (tenant_id, status);

create table app.media_variants (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    media_asset_id uuid not null,
    format text not null check (format in ('avif', 'webp')),
    width integer not null check (width > 0),
    height integer not null check (height > 0),
    r2_key text not null,
    size_bytes bigint not null check (size_bytes >= 0),
    unique (media_asset_id, format, width),
    unique (tenant_id, id)
);

alter table app.media_variants
    add constraint media_variants_asset_fk
    foreign key (tenant_id, media_asset_id)
    references app.media_assets (tenant_id, id)
    on delete cascade;

create table app.product_media (
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    product_id uuid not null,
    media_asset_id uuid not null,
    position integer not null default 0,
    is_primary boolean not null default false,
    created_at timestamptz not null default now(),
    primary key (tenant_id, product_id, media_asset_id)
);

alter table app.product_media
    add constraint product_media_product_fk
    foreign key (tenant_id, product_id)
    references app.products (tenant_id, id)
    on delete cascade;

alter table app.product_media
    add constraint product_media_asset_fk
    foreign key (tenant_id, media_asset_id)
    references app.media_assets (tenant_id, id)
    on delete cascade;

create unique index product_media_primary_idx
    on app.product_media (tenant_id, product_id)
    where is_primary;

-- ---------------------------------------------------------------------------
-- Inventario
-- ---------------------------------------------------------------------------

create table app.locations (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    name text not null,
    address jsonb not null default '{}'::jsonb,
    is_default boolean not null default false,
    created_at timestamptz not null default now(),
    unique (tenant_id, id)
);

create unique index locations_default_idx
    on app.locations (tenant_id)
    where is_default;

create table app.inventory_levels (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    variant_id uuid not null,
    location_id uuid not null,
    available integer not null default 0 check (available >= 0),
    reserved integer not null default 0 check (reserved >= 0),
    safety_stock integer not null default 0 check (safety_stock >= 0),
    updated_at timestamptz not null default now(),
    unique (tenant_id, variant_id, location_id)
);

alter table app.inventory_levels
    add constraint inventory_levels_variant_fk
    foreign key (tenant_id, variant_id)
    references app.product_variants (tenant_id, id)
    on delete cascade;

alter table app.inventory_levels
    add constraint inventory_levels_location_fk
    foreign key (tenant_id, location_id)
    references app.locations (tenant_id, id)
    on delete cascade;

create index inventory_levels_tenant_variant_idx
    on app.inventory_levels (tenant_id, variant_id);

create table app.inventory_movements (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    variant_id uuid not null,
    delta integer not null,
    reason text not null
        check (reason in ('sale', 'return', 'adjustment', 'restock', 'reservation', 'release')),
    reference_type text,
    reference_id uuid,
    created_at timestamptz not null default now()
);

alter table app.inventory_movements
    add constraint inventory_movements_variant_fk
    foreign key (tenant_id, variant_id)
    references app.product_variants (tenant_id, id)
    on delete cascade;

create index inventory_movements_tenant_variant_created_idx
    on app.inventory_movements (tenant_id, variant_id, created_at desc);

create table app.inventory_reservations (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    variant_id uuid not null,
    cart_id uuid,
    order_id uuid,
    quantity integer not null check (quantity > 0),
    status text not null default 'active'
        check (status in ('active', 'confirmed', 'released', 'expired')),
    expires_at timestamptz not null,
    created_at timestamptz not null default now()
);

alter table app.inventory_reservations
    add constraint inventory_reservations_variant_fk
    foreign key (tenant_id, variant_id)
    references app.product_variants (tenant_id, id)
    on delete cascade;

create index inventory_reservations_tenant_variant_status_idx
    on app.inventory_reservations (tenant_id, variant_id, status, expires_at);

-- ---------------------------------------------------------------------------
-- Ubicación por defecto
-- ---------------------------------------------------------------------------

insert into app.locations (tenant_id, name, is_default)
select t.id, 'Principal', true
from app.tenants t
where not exists (
    select 1 from app.locations l where l.tenant_id = t.id
);

-- ---------------------------------------------------------------------------
-- Funciones
-- ---------------------------------------------------------------------------

create or replace function app.refresh_product_price_range()
returns trigger
language plpgsql
as $$
declare
    v_product_id uuid;
    v_tenant_id uuid;
begin
    if tg_op = 'DELETE' then
        v_product_id := old.product_id;
        v_tenant_id := old.tenant_id;
    else
        v_product_id := new.product_id;
        v_tenant_id := new.tenant_id;
    end if;

    update app.products p
    set min_price_cents = coalesce(
            (
                select min(price_cents)
                from app.product_variants
                where tenant_id = v_tenant_id
                  and product_id = v_product_id
                  and is_active
            ),
            0
        ),
        max_price_cents = coalesce(
            (
                select max(price_cents)
                from app.product_variants
                where tenant_id = v_tenant_id
                  and product_id = v_product_id
                  and is_active
            ),
            0
        )
    where p.tenant_id = v_tenant_id
      and p.id = v_product_id;

    return null;
end;
$$;

create trigger product_variants_price_range
after insert or update or delete on app.product_variants
for each row execute function app.refresh_product_price_range();

-- Reemplaza create_tenant para que todo tenant nuevo tenga ubicación default.
create or replace function app.create_tenant(
    p_slug text,
    p_host text,
    p_name text,
    p_legal_name text default null,
    p_plan_id uuid default null
)
returns uuid
language plpgsql
security definer
set search_path = app, public
as $$
declare
    v_tenant_id uuid;
begin
    insert into app.tenants (slug, name, legal_name, plan_id, status, trial_ends_at)
    values (p_slug, p_name, p_legal_name, p_plan_id, 'trialing', now() + interval '14 days')
    returning id into v_tenant_id;

    insert into app.domains (tenant_id, host, type, is_primary)
    values (v_tenant_id, lower(p_host), 'subdomain', true);

    insert into app.tenant_settings (tenant_id)
    values (v_tenant_id);

    insert into app.tenant_features (tenant_id, feature_key, enabled)
    values
        (v_tenant_id, 'storefront', true),
        (v_tenant_id, 'checkout', true),
        (v_tenant_id, 'invoices', true);

    insert into app.locations (tenant_id, name, is_default)
    values (v_tenant_id, 'Principal', true);

    return v_tenant_id;
end;
$$;

revoke all on function app.create_tenant(text, text, text, text, uuid) from public;
grant execute on function app.create_tenant(text, text, text, text, uuid) to app_rw;

-- ---------------------------------------------------------------------------
-- Triggers de updated_at
-- ---------------------------------------------------------------------------

create trigger categories_set_updated_at
before update on app.categories
for each row execute function app.set_updated_at();

create trigger products_set_updated_at
before update on app.products
for each row execute function app.set_updated_at();

create trigger product_variants_set_updated_at
before update on app.product_variants
for each row execute function app.set_updated_at();

create trigger media_assets_set_updated_at
before update on app.media_assets
for each row execute function app.set_updated_at();

create trigger inventory_levels_set_updated_at
before update on app.inventory_levels
for each row execute function app.set_updated_at();

-- ---------------------------------------------------------------------------
-- RLS forzado
-- ---------------------------------------------------------------------------

alter table app.categories enable row level security;
alter table app.categories force row level security;
create policy categories_tenant_isolation on app.categories
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

alter table app.products enable row level security;
alter table app.products force row level security;
create policy products_tenant_isolation on app.products
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

alter table app.product_variants enable row level security;
alter table app.product_variants force row level security;
create policy product_variants_tenant_isolation on app.product_variants
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

alter table app.media_assets enable row level security;
alter table app.media_assets force row level security;
create policy media_assets_tenant_isolation on app.media_assets
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

alter table app.media_variants enable row level security;
alter table app.media_variants force row level security;
create policy media_variants_tenant_isolation on app.media_variants
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

alter table app.product_media enable row level security;
alter table app.product_media force row level security;
create policy product_media_tenant_isolation on app.product_media
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

alter table app.locations enable row level security;
alter table app.locations force row level security;
create policy locations_tenant_isolation on app.locations
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

alter table app.inventory_levels enable row level security;
alter table app.inventory_levels force row level security;
create policy inventory_levels_tenant_isolation on app.inventory_levels
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

alter table app.inventory_movements enable row level security;
alter table app.inventory_movements force row level security;
create policy inventory_movements_tenant_isolation on app.inventory_movements
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

alter table app.inventory_reservations enable row level security;
alter table app.inventory_reservations force row level security;
create policy inventory_reservations_tenant_isolation on app.inventory_reservations
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

-- ---------------------------------------------------------------------------
-- Grants
-- ---------------------------------------------------------------------------

grant select, insert, update, delete on app.categories to app_rw;
grant select, insert, update, delete on app.products to app_rw;
grant select, insert, update, delete on app.product_variants to app_rw;
grant select, insert, update, delete on app.media_assets to app_rw;
grant select, insert, update, delete on app.media_variants to app_rw;
grant select, insert, update, delete on app.product_media to app_rw;
grant select, insert, update, delete on app.locations to app_rw;
grant select, insert, update, delete on app.inventory_levels to app_rw;
grant select, insert, update, delete on app.inventory_reservations to app_rw;

-- Movimientos append-only.
grant select, insert on app.inventory_movements to app_rw;
