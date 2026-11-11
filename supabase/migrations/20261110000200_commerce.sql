-- Comercio (Wave 4): carrito guest, órdenes, pagos y webhooks idempotentes.
-- Dinero en centavos BIGINT, COP. Snapshot de totales en la orden.

create table app.carts (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    customer_id uuid references app.customers(id) on delete set null,
    status text not null default 'open' check (status in ('open', 'converted', 'abandoned')),
    expires_at timestamptz not null default (now() + interval '30 days'),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
alter table app.carts enable row level security;
alter table app.carts force row level security;
create policy carts_tenant_isolation on app.carts
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());
grant select, insert, update on app.carts to app_rw;
create index carts_tenant_status_idx on app.carts (tenant_id, status, updated_at desc);

create table app.cart_items (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    cart_id uuid not null references app.carts(id) on delete cascade,
    variant_id uuid not null references app.product_variants(id) on delete cascade,
    quantity integer not null check (quantity > 0),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (tenant_id, cart_id, variant_id)
);
alter table app.cart_items enable row level security;
alter table app.cart_items force row level security;
create policy cart_items_tenant_isolation on app.cart_items
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());
grant select, insert, update, delete on app.cart_items to app_rw;

create table app.orders (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    customer_id uuid references app.customers(id) on delete set null,
    cart_id uuid references app.carts(id) on delete set null,
    email text not null,
    status text not null default 'pending'
        check (status in ('pending', 'paid', 'failed', 'expired', 'cancelled',
                          'preparing', 'shipped', 'delivered', 'refund_pending', 'refunded')),
    subtotal_cents bigint not null check (subtotal_cents >= 0),
    tax_cents bigint not null default 0 check (tax_cents >= 0),
    shipping_cents bigint not null default 0 check (shipping_cents >= 0),
    total_cents bigint not null check (total_cents >= 0),
    tax_rate_bps integer not null default 1900 check (tax_rate_bps between 0 and 10000),
    shipping_zone text,
    shipping_name text,
    shipping_line1 text,
    shipping_line2 text,
    shipping_city text,
    shipping_state text,
    shipping_postal_code text,
    shipping_country text not null default 'CO',
    dispute_status text not null default 'none'
        check (dispute_status in ('none', 'reported', 'evidence_submitted', 'won', 'lost')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
alter table app.orders enable row level security;
alter table app.orders force row level security;
create policy orders_tenant_isolation on app.orders
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());
grant select, insert, update on app.orders to app_rw;
create index orders_tenant_status_created_idx on app.orders (tenant_id, status, created_at desc);
create index orders_tenant_email_idx on app.orders (tenant_id, lower(email));
create unique index orders_tenant_id_id_key on app.orders (tenant_id, id);

create table app.order_items (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    order_id uuid not null,
    variant_id uuid references app.product_variants(id) on delete set null,
    product_name text not null,
    variant_sku text,
    variant_title text,
    quantity integer not null check (quantity > 0),
    unit_price_cents bigint not null check (unit_price_cents >= 0),
    created_at timestamptz not null default now(),
    foreign key (tenant_id, order_id) references app.orders (tenant_id, id) on delete cascade
);
alter table app.order_items enable row level security;
alter table app.order_items force row level security;
create policy order_items_tenant_isolation on app.order_items
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());
grant select, insert on app.order_items to app_rw;

create table app.tenant_payment_accounts (
    tenant_id uuid primary key references app.tenants(id) on delete cascade,
    provider text not null default 'wompi' check (provider in ('wompi')),
    public_key text not null,
    events_secret_encrypted text not null,
    integrity_key_encrypted text not null,
    mode text not null default 'sandbox' check (mode in ('sandbox', 'production')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
alter table app.tenant_payment_accounts enable row level security;
alter table app.tenant_payment_accounts force row level security;
create policy tenant_payment_accounts_tenant_isolation on app.tenant_payment_accounts
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());
grant select, insert, update on app.tenant_payment_accounts to app_rw;

create table app.payments (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    order_id uuid not null,
    provider text not null default 'wompi' check (provider in ('wompi')),
    provider_reference text not null,
    status text not null default 'pending'
        check (status in ('pending', 'approved', 'declined', 'voided', 'error')),
    amount_cents bigint not null check (amount_cents >= 0),
    method text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (tenant_id, provider_reference),
    foreign key (tenant_id, order_id) references app.orders (tenant_id, id) on delete cascade
);
alter table app.payments enable row level security;
alter table app.payments force row level security;
create policy payments_tenant_isolation on app.payments
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());
grant select, insert, update on app.payments to app_rw;

create table app.webhook_events (
    id uuid primary key default gen_random_uuid(),
    provider text not null check (provider in ('wompi', 'stripe', 'resend', 'factus')),
    event_id text not null,
    tenant_id uuid references app.tenants(id) on delete set null,
    payload jsonb not null,
    processed_at timestamptz,
    created_at timestamptz not null default now(),
    unique (provider, event_id)
);
alter table app.webhook_events enable row level security;
alter table app.webhook_events force row level security;
-- Sin grants directos a app_rw para filas cross-tenant: solo inserción por funciones acotadas.
grant select, insert, update on app.webhook_events to app_rw;
-- Lectura: solo eventos del propio tenant. Inserción: admite eventos sin tenant
-- (p. ej. suscripciones de plataforma, aún no correlacionadas) solo vía webhook verificado.
create policy webhook_events_tenant_read on app.webhook_events
    for select using (tenant_id = app.current_tenant());
create policy webhook_events_insert on app.webhook_events
    for insert with check (tenant_id = app.current_tenant() or tenant_id is null);
create policy webhook_events_update on app.webhook_events
    for update using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

create table app.platform_subscriptions (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null unique references app.tenants(id) on delete cascade,
    plan_id uuid references app.plans(id) on delete set null,
    provider text not null default 'stripe' check (provider in ('stripe', 'mercadopago')),
    provider_customer_id text,
    provider_subscription_id text,
    status text not null default 'trialing'
        check (status in ('trialing', 'active', 'past_due', 'suspended', 'canceled')),
    current_period_end timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
alter table app.platform_subscriptions enable row level security;
alter table app.platform_subscriptions force row level security;
create policy platform_subscriptions_tenant_isolation on app.platform_subscriptions
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());
grant select on app.platform_subscriptions to app_rw;

create or replace function app.payment_by_reference(p_reference text)
returns table(tenant_id uuid, order_id uuid, provider_reference text)
language sql
security definer
set search_path = pg_catalog, app
as $$
    select p.tenant_id, p.order_id, p.provider_reference
    from app.payments p
    where p.provider_reference = p_reference
$$;
revoke all on function app.payment_by_reference(text) from public;
grant execute on function app.payment_by_reference(text) to app_rw;

create trigger set_updated_at_carts before update on app.carts
    for each row execute function app.set_updated_at();
create trigger set_updated_at_orders before update on app.orders
    for each row execute function app.set_updated_at();
