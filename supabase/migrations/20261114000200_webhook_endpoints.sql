-- Webhooks outbound para tenants (owner/manager): registro de apps suscritas a
-- eventos de comercio (orders.paid, etc.). Lectura/escritura solo para dueños
-- del tenant via RLS; no existe ruta pública.

create table app.webhook_endpoints (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    event text not null,
    target_url text not null,
    secret text not null,
    active boolean not null default true,
    fail_count integer not null default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint webhook_endpoints_event_check
        check (event in ('orders.paid', 'orders.created')),
    constraint webhook_endpoints_url_check
        check (target_url ~ '^https?://')
);

create index webhook_endpoints_tenant_event_idx
    on app.webhook_endpoints (tenant_id, event)
    where active;

alter table app.webhook_endpoints enable row level security;
alter table app.webhook_endpoints force row level security;

create policy webhook_endpoints_tenant_isolation on app.webhook_endpoints
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

grant select on app.webhook_endpoints to app_rw;
grant insert, update, delete on app.webhook_endpoints to app_rw;

-- Relaja el check de app.outbox_events: se usa la outbox como canal de fan-out.
alter table app.outbox_events
    drop constraint outbox_events_type_check;

alter table app.outbox_events
    add constraint outbox_events_type_check
    check (type in ('content.published', 'content.unpublished', 'orders.paid'));
