-- E5.1 Reorden de inventario heurístico
-- Objetivo: detectar variantes activas con stock bajo y generar
-- sugerencias pendientes de aprobación humana (sin IA generativa).
alter table app.product_variants
    add column if not exists min_stock_threshold integer not null default 5;

create table if not exists app.ai_suggestions (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references app.tenants(id) on delete cascade,
    type text not null check (type in ('reorder')),
    payload jsonb not null default '{}'::jsonb,
    status text not null default 'pending'
        check (status in ('pending', 'accepted', 'dismissed', 'applied')),
    proposed_at timestamptz not null default now(),
    resolved_at timestamptz
);

create unique index if not exists ai_suggestions_tenant_type_variant_idx
    on app.ai_suggestions (tenant_id, type, (payload->>'variant_id'))
    where status in ('pending', 'accepted', 'applied', 'dismissed');

alter table app.ai_suggestions enable row level security;
alter table app.ai_suggestions force row level security;

create policy ai_suggestions_tenant_isolation on app.ai_suggestions
    using (tenant_id = app.current_tenant())
    with check (tenant_id = app.current_tenant());

grant select, insert, update, delete on app.ai_suggestions to app_rw;

-- Función determinista: variantes activas con stock disponible < umbral
-- y sin sugerencia pendiente reciente.
create or replace function app.detect_reorder_candidates(
    p_tenant_id uuid,
    p_min_stock integer default 5
)
returns table (
    tenant_id uuid,
    variant_id uuid,
    sku text,
    product_name text,
    stock_available bigint,
    threshold integer
)
language sql
stable
security definer
set search_path = pg_catalog, app
as $$
    select
        il.tenant_id,
        il.variant_id,
        pv.sku,
        p.name as product_name,
        sum(il.available)::bigint as stock_available,
        coalesce(nullif(pv.min_stock_threshold, 0), p_min_stock) as threshold
    from app.inventory_levels il
    join app.product_variants pv
      on pv.tenant_id = il.tenant_id and pv.id = il.variant_id and pv.is_active = true
    join app.products p
      on p.tenant_id = pv.tenant_id and p.id = pv.product_id and p.status = 'active'
    where il.tenant_id = p_tenant_id
    group by il.tenant_id, il.variant_id, pv.sku, p.name, pv.min_stock_threshold
    having sum(il.available)::bigint < coalesce(nullif(pv.min_stock_threshold, 0), p_min_stock)
       and not exists (
            select 1
            from app.ai_suggestions s
            where s.tenant_id = il.tenant_id
              and s.type = 'reorder'
              and s.status in ('pending', 'accepted', 'applied')
              and (s.payload->>'variant_id')::uuid = il.variant_id
              and s.proposed_at > now() - interval '7 days'
       );
$$;

revoke all on function app.detect_reorder_candidates(uuid, integer) from public;
grant execute on function app.detect_reorder_candidates(uuid, integer) to app_rw;
