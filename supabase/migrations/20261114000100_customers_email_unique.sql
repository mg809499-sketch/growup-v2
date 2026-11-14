-- Añade unicidad incondicional de (tenant_id, email) para upsert de compradores.
-- Los índices existentes solo cubrían el caso parcial (`auth_user_id IS NOT NULL`);
-- este índice cubre todas las filas y habilita ON CONFLICT seguro en el checkout.

create unique index if not exists customers_tenant_email_unique
    on app.customers (tenant_id, lower(email));
