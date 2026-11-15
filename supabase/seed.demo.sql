-- Seed demo (B-01): tenants ropa y joyeria con catálogo y páginas publicadas.
-- Idempotente. Ejecutar DESPUÉS de aplicar migraciones:
--   psql "$GROWUP_MIGRATION_URL" -f supabase/seed.demo.sql
-- NOTA: los textos de política legal están PENDIENTES de aprobación de abogado.

\set ON_ERROR_STOP on
\set QUIET on

begin;

do $$
declare
  rid uuid;
  jid uuid;
  cat_id uuid;
  prod_id uuid;
  v_page_id uuid;
  v_version_id uuid;
  t record;
  i int;
  p int;
  cat_names text[] := array['Categoría 1', 'Categoría 2', 'Categoría 3'];
  layout jsonb;
begin
  -- Tenants (idempotente)
  select id into rid from app.tenants where slug = 'ropa';
  if rid is null then
    rid := app.create_tenant('ropa', 'ropa.growup.com', 'Ropa');
  end if;
  select id into jid from app.tenants where slug = 'joyeria';
  if jid is null then
    jid := app.create_tenant('joyeria', 'joyeria.growup.com', 'Joyería');
  end if;
  update app.tenants set status = 'active' where id in (rid, jid);

  -- Settings básicos
  insert into app.tenant_settings (tenant_id, currency, locale)
  values (rid, 'COP', 'es-CO'), (jid, 'COP', 'es-CO')
  on conflict (tenant_id) do nothing;

  -- Temas por tenant (ThemeTokensV1: preset nova en claro, reversión inmediata a ropa/joyeria)
  insert into app.themes (tenant_id, tokens) values
    (rid, '{"schema_version":1,"preset":"nova","color_scheme":"light","font_display":"Unbounded","font_body":"Geist","font_mono":"Geist Mono","colors":{"surface":"#ffffff","surface_2":"#f4f6fb","ink":"#0d0d0d","signal":"#111111","muted":"#525866","hairline":"#e2e8f0"},"radius_px":16,"clip_angle_px":0,"motion":"technical"}'::jsonb),
    (jid, '{"schema_version":1,"preset":"nova","color_scheme":"light","font_display":"Unbounded","font_body":"Geist","font_mono":"Geist Mono","colors":{"surface":"#ffffff","surface_2":"#f4f6fb","ink":"#0d0d0d","signal":"#111111","muted":"#525866","hairline":"#e2e8f0"},"radius_px":16,"clip_angle_px":0,"motion":"technical"}'::jsonb)
  on conflict (tenant_id) do update set tokens = excluded.tokens;

  -- Catálogo
  for t in select id, slug from (select rid as id, 'ropa' as slug union all select jid, 'joyeria') s
  loop
    for i in 1..3 loop
      insert into app.categories (tenant_id, name, slug, position)
      values (t.id, cat_names[i], t.slug || '-cat-' || i, i)
      on conflict do nothing;
    end loop;

    for p in 1..6 loop
      select id into cat_id from app.categories
      where tenant_id = t.id order by position limit 1 offset ((p - 1) % 3);

      insert into app.products (tenant_id, category_id, slug, name, status, published_at)
      values (
        t.id, cat_id, t.slug || '-producto-' || p,
        case when t.slug = 'ropa' then 'Pieza ' || p else 'Joya ' || p end,
        'active', now()
      )
      on conflict (tenant_id, slug) do nothing;

      select id into prod_id from app.products
      where tenant_id = t.id and slug = t.slug || '-producto-' || p;

      insert into app.product_variants (tenant_id, product_id, sku, name, price_cents)
      values
        (t.id, prod_id, t.slug || '-P' || p || '-A', 'Talla A', 99000 + (p * 10000)),
        (t.id, prod_id, t.slug || '-P' || p || '-B', 'Talla B', 99000 + (p * 10000))
      on conflict do nothing;

      update app.product_variants set is_active = true
      where tenant_id = t.id and product_id = prod_id;

      insert into app.inventory_levels (tenant_id, variant_id, location_id, available, reserved)
      select t.id, v.id, (select id from app.locations where tenant_id = t.id and is_default), 12, 0
      from app.product_variants v
      where v.tenant_id = t.id and v.product_id = prod_id
      on conflict do nothing;
    end loop;

    -- Página home publicada (bloques ADR-0005)
    insert into app.pages (tenant_id, slug, title, status)
    values (t.id, 'home', 'Inicio', 'published')
    on conflict (tenant_id, slug) do update set status = 'published'
    returning id into v_page_id;

    if v_page_id is null then
      select id into v_page_id from app.pages where tenant_id = t.id and slug = 'home';
    end if;

    if not exists (
      select 1 from app.page_versions
      where tenant_id = t.id and page_id = v_page_id
    ) then
      layout := jsonb_build_object(
        'version', 1,
        'blocks', jsonb_build_array(
          jsonb_build_object(
            'id', 'hero-1', 'type', 'hero',
            'eyebrow', 'Temporada 01',
            'title', case when t.slug = 'ropa' then 'Archivo Ropa' else 'Joyería Obsidiana' end,
            'subtitle', 'Series cortas y piezas seleccionadas.',
            'align', 'left',
            'cta', jsonb_build_object('label', 'Ver colección', 'href', '/collection')
          ),
          jsonb_build_object('id', 'grid-1', 'type', 'product_grid', 'title', 'Últimas piezas',
                             'source', 'latest', 'limit', 8, 'show_price', true)
        )
      );
      insert into app.page_versions (tenant_id, page_id, version, layout)
      values (t.id, v_page_id, 1, layout)
      returning id into v_version_id;
      perform app.publish_page(t.id, v_page_id, v_version_id, null);
    end if;
  end loop;
end $$;

commit;
\echo 'seed.demo: tenants ropa y joyeria listos'
