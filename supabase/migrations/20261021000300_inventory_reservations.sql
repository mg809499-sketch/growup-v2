-- Reservas de inventario con ubicación explícita e invariantes de stock.
-- Depende de catalog y governance.

-- Garantiza una ubicación default para tenants con reservas previas.
insert into app.locations (tenant_id, name, is_default)
select distinct r.tenant_id, 'Principal', true
from app.inventory_reservations r
where not exists (
    select 1
    from app.locations l
    where l.tenant_id = r.tenant_id
      and l.is_default
);

alter table app.inventory_reservations
    add column location_id uuid;

update app.inventory_reservations r
set location_id = l.id
from app.locations l
where l.tenant_id = r.tenant_id
  and l.is_default
  and r.location_id is null;

alter table app.inventory_reservations
    alter column location_id set not null;

alter table app.inventory_reservations
    add constraint inventory_reservations_location_fk
    foreign key (tenant_id, location_id)
    references app.locations (tenant_id, id)
    on delete restrict;

-- Una reserva nunca puede superar el stock físico disponible.
alter table app.inventory_levels
    add constraint inventory_levels_reserved_within_available
    check (reserved <= available);

create index inventory_reservations_tenant_status_expires_idx
    on app.inventory_reservations (tenant_id, status, expires_at);
