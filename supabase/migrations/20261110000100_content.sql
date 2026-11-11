-- Contenido y publishing (ADR-0005, en propuesta — implementar tras ratificación).
-- pages: una página lógica por slug/tenant. page_versions: versiones inmutables del layout.
-- themes: tokens de tema por tenant. outbox_events: fan-out para purga de caché/ISR.

create table app.themes (
    tenant_id uuid primary key references app.tenants(id) on delete cascade,
    tokens jsonb not null,
    updated_at timestamptz not null default now()
);
alter table app.themes enable row level security;
alter table app.themes force row level security;
create policy themes_tenant_isolation on app.themes
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());
grant select, update, insert on app.themes to app_rw;

create table app.pages (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    slug text not null check (slug ~ '^[a-z0-9](?:[a-z0-9/-]{0,126}[a-z0-9])?$'),
    title text not null check (char_length(title) between 1 and 200),
    status text not null default 'draft' check (status in ('draft', 'published', 'archived')),
    published_version_id uuid,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (tenant_id, slug)
);
alter table app.pages enable row level security;
alter table app.pages force row level security;
create policy pages_tenant_isolation on app.pages
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());
grant select, insert, update on app.pages to app_rw;

create table app.page_versions (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    page_id uuid not null references app.pages(id) on delete cascade,
    version integer not null check (version > 0),
    layout jsonb not null,
    created_by uuid,
    created_at timestamptz not null default now(),
    unique (tenant_id, page_id, version)
);
alter table app.page_versions enable row level security;
alter table app.page_versions force row level security;
create policy page_versions_tenant_isolation on app.page_versions
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());
grant select, insert on app.page_versions to app_rw;
create index page_versions_tenant_page_idx on app.page_versions (tenant_id, page_id, version desc);

-- FK compuesta anti cross-tenant para la versión publicada de una página
alter table app.pages
    add constraint pages_tenant_id_id_key unique (tenant_id, id);
alter table app.page_versions
    add constraint page_versions_tenant_page_fk
    foreign key (tenant_id, page_id)
    references app.pages (tenant_id, id)
    on delete cascade;

alter table app.pages
    add constraint pages_published_version_fk
    foreign key (published_version_id)
    references app.page_versions (id)
    on delete set null;

-- Outbox: eventos de dominio para fan-out asíncrono (purga de caché, emails futuros).
create table app.outbox_events (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid references app.tenants(id) on delete set null,
    type text not null check (type in ('content.published', 'content.unpublished')),
    payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    processed_at timestamptz
);
alter table app.outbox_events enable row level security;
alter table app.outbox_events force row level security;
create policy outbox_events_tenant_isolation on app.outbox_events
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());
grant select, insert, update on app.outbox_events to app_rw;
create index outbox_events_unprocessed_idx
    on app.outbox_events (created_at)
    where processed_at is null;

-- Publish atómico: swap de la versión publicada + evento en outbox, en una transacción.
create or replace function app.publish_page(
    p_tenant_id uuid,
    p_page_id uuid,
    p_version_id uuid,
    p_actor uuid
)
returns void
language sql
security definer
set search_path = pg_catalog, app
as $$
    update app.pages
    set published_version_id = p_version_id,
        status = 'published',
        updated_at = now()
    where tenant_id = p_tenant_id
      and id = p_page_id
      and exists (
          select 1 from app.page_versions v
          where v.id = p_version_id
            and v.tenant_id = p_tenant_id
            and v.page_id = p_page_id
      );
    insert into app.outbox_events (tenant_id, type, payload)
    values (
        p_tenant_id,
        'content.published',
        jsonb_build_object('page_id', p_page_id, 'version_id', p_version_id, 'actor', p_actor)
    );
$$;
revoke all on function app.publish_page(uuid, uuid, uuid, uuid) from public;
grant execute on function app.publish_page(uuid, uuid, uuid, uuid) to app_rw;

create or replace function app.unpublish_page(
    p_tenant_id uuid,
    p_page_id uuid,
    p_actor uuid
)
returns void
language sql
security definer
set search_path = pg_catalog, app
as $$
    update app.pages
    set status = 'draft',
        updated_at = now()
    where tenant_id = p_tenant_id
      and id = p_page_id;
    insert into app.outbox_events (tenant_id, type, payload)
    values (
        p_tenant_id,
        'content.unpublished',
        jsonb_build_object('page_id', p_page_id, 'actor', p_actor)
    );
$$;
revoke all on function app.unpublish_page(uuid, uuid, uuid) from public;
grant execute on function app.unpublish_page(uuid, uuid, uuid) to app_rw;
