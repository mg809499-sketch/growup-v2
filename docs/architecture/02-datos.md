# Arquitectura — Modelo de datos

> Basado en ADR-0003 (tenancy/RLS), ADR-0004 (pagos), ADR-0005 (contenido), D-06 (COP/IVA) y D-08 (piloto).
> Convenciones: `uuid` PK, `timestamptz` UTC, dinero en `bigint` de centavos, `tenant_id` obligatorio en tablas de negocio.

## 1. Convenciones transversales

| Tema | Regla |
|---|---|
| Dinero | `*_cents bigint`, moneda `COP`; nunca `float` |
| Impuestos | Precio mostrado con IVA 19%; snapshot de `subtotal`, `tax`, `shipping`, `total` |
| IDs | `uuid default gen_random_uuid()` |
| Slugs | minúsculas, URL-safe, único por tenant |
| Emails | `citext` o índice `lower(email)` |
| Estados | `text` + `check` constraint (evita migraciones de enums) |
| Auditoría | `created_at`, `updated_at`; `updated_at` por trigger |
| Borrado | `status='archived'` o `deleted_at`; hard delete solo auditado |
| RLS | `ENABLE` + `FORCE`; política `tenant_id = app.current_tenant()` |
| Búsqueda | `tsvector` + GIN; `pg_trgm` para fuzzy |

Plantilla RLS:

```sql
alter table <tabla> enable row level security;
alter table <tabla> force row level security;

create policy tenant_isolation on <tabla>
  using (tenant_id = app.current_tenant())
  with check (tenant_id = app.current_tenant());
```

Excepciones documentadas:

- `tenants` y `domains`: resolución por `app.resolve_tenant(host)` `SECURITY DEFINER`; sin `USING (true)`.
- `plans`: catálogo de plataforma, lectura para staff; escritura solo platform admin.
- `platform_admins`: plataforma; acceso auditado.

## 2. Plataforma y tenancy

### `tenants`

| Campo | Tipo | Nota |
|---|---|---|
| `id` | uuid | PK |
| `slug` | text | único; subdominio `{slug}.growup.com` |
| `name` | text | Nombre comercial |
| `legal_name` | text | Razón social |
| `status` | text | `trialing`, `active`, `past_due`, `suspended`, `canceled` |
| `plan_id` | uuid | FK `plans` |
| `trial_ends_at` | timestamptz | 14 días |
| `created_at`, `updated_at` | timestamptz | |

### `domains`

| Campo | Tipo | Nota |
|---|---|---|
| `id` | uuid | PK |
| `tenant_id` | uuid | FK |
| `host` | text | único global; `ropa.growup.com` |
| `type` | text | `subdomain`, `custom` |
| `is_primary` | boolean | |
| `verified_at` | timestamptz | null para subdominios gestionados |
| `created_at` | timestamptz | |

### `tenant_settings`

| Campo | Tipo | Nota |
|---|---|---|
| `tenant_id` | uuid | PK, FK |
| `currency` | text | `COP` |
| `locale` | text | `es-CO` |
| `navigation` | jsonb | Menús validados |
| `seo_defaults` | jsonb | title, description, OG |
| `shipping_zones` | jsonb | Zonas y tarifas planas |
| `contact` | jsonb | email, phone, address |
| `social` | jsonb | links allowlist |
| `updated_at` | timestamptz | |

### `tenant_features`

| Campo | Tipo | Nota |
|---|---|---|
| `tenant_id` | uuid | PK compuesta |
| `feature_key` | text | PK compuesta |
| `enabled` | boolean | |
| `limit_value` | jsonb | límites por plan |
| `updated_at` | timestamptz | |

### `plans`

| Campo | Tipo | Nota |
|---|---|---|
| `id` | uuid | PK |
| `code` | text | único (`starter`, `pro`) |
| `name` | text | |
| `price_cents` | bigint | Suscripción |
| `currency` | text | `COP` |
| `interval` | text | `month` |
| `trial_days` | int | 14 |
| `features` | jsonb | Límites y capacidades |
| `is_active` | boolean | |
| `created_at`, `updated_at` | timestamptz | |

### `platform_subscriptions`

| Campo | Tipo | Nota |
|---|---|---|
| `id` | uuid | PK |
| `tenant_id` | uuid | FK |
| `plan_id` | uuid | FK |
| `stripe_customer_id` | text | único |
| `stripe_subscription_id` | text | único |
| `status` | text | `trialing`, `active`, `past_due`, `canceled`, `incomplete` |
| `trial_ends_at` | timestamptz | |
| `current_period_start`, `current_period_end` | timestamptz | |
| `cancel_at_period_end` | boolean | |
| `created_at`, `updated_at` | timestamptz | |

### `platform_invoices`

| Campo | Tipo | Nota |
|---|---|---|
| `id` | uuid | PK |
| `tenant_id` | uuid | FK |
| `stripe_invoice_id` | text | único |
| `amount_cents` | bigint | |
| `currency` | text | |
| `status` | text | `draft`, `open`, `paid`, `void`, `uncollectible` |
| `pdf_url` | text | firmada |
| `period_start`, `period_end` | timestamptz | |
| `created_at` | timestamptz | |

### `billing_events`

| Campo | Tipo | Nota |
|---|---|---|
| `id` | uuid | PK |
| `tenant_id` | uuid | FK |
| `provider` | text | `stripe` |
| `provider_event_id` | text | único por tenant/provider |
| `type` | text | |
| `payload_hash` | text | SHA-256 |
| `status` | text | `processed`, `ignored`, `failed` |
| `processed_at` | timestamptz | |

## 3. Identidad

### `memberships`

| Campo | Tipo | Nota |
|---|---|---|
| `id` | uuid | PK |
| `tenant_id` | uuid | FK |
| `user_id` | uuid | `auth.users.id` de Supabase |
| `email` | citext | |
| `role` | text | `owner`, `manager`, `treasurer`, `packer`, `support` |
| `status` | text | `invited`, `active`, `disabled` |
| `created_at`, `updated_at` | timestamptz | |

Único `(tenant_id, user_id)`; único `(tenant_id, lower(email))` para invitaciones.

### `customers`

| Campo | Tipo | Nota |
|---|---|---|
| `id` | uuid | PK |
| `tenant_id` | uuid | FK |
| `auth_user_id` | uuid | nullable; se llena con magic link |
| `email` | citext | |
| `name` | text | |
| `phone` | text | |
| `default_address_id` | uuid | nullable |
| `created_at`, `updated_at` | timestamptz | |

Único `(tenant_id, lower(email))` cuando `auth_user_id` no es null; invitados pueden repetir email hasta reclamar.

### `addresses`

| Campo | Tipo | Nota |
|---|---|---|
| `id` | uuid | PK |
| `tenant_id` | uuid | FK |
| `customer_id` | uuid | nullable (invitado) |
| `name`, `phone` | text | |
| `line1`, `line2` | text | |
| `city`, `state`, `postal_code` | text | |
| `country` | text | `CO` |
| `is_default` | boolean | |
| `created_at` | timestamptz | |

### `auth_events`

Append-only: `id`, `tenant_id` nullable, `event_type`, `actor_id`, `ip`, `user_agent`, `result`, `trace_id`, `created_at`. Sin PII cruda.

### `platform_admins`

`user_id` (PK), `email`, `role` (`support`, `ops`, `owner`), `created_at`. Acceso auditado.

## 4. Catálogo e inventario

### `categories`

`id`, `tenant_id`, `parent_id` nullable, `slug`, `name`, `description`, `position`, `seo jsonb`, timestamps. Único `(tenant_id, slug)`.

### `collections`

`id`, `tenant_id`, `slug`, `name`, `description`, `type` (`manual`), `seo jsonb`, timestamps. Único `(tenant_id, slug)`.

### `products`

| Campo | Tipo | Nota |
|---|---|---|
| `id` | uuid | PK |
| `tenant_id` | uuid | FK |
| `slug` | text | único por tenant |
| `name` | text | |
| `description` | text | Markdown restringido |
| `status` | text | `draft`, `active`, `archived` |
| `category_id` | uuid | nullable |
| `brand` | text | |
| `tags` | text[] | |
| `seo` | jsonb | |
| `min_price_cents` | bigint | denormalizado |
| `max_price_cents` | bigint | denormalizado |
| `search_vector` | tsvector | trigger desde producto + variantes |
| `created_at`, `updated_at`, `published_at` | timestamptz | |

Índices: `(tenant_id, status)`, GIN `search_vector`, GIN `tags`, `(tenant_id, min_price_cents)`.

### `product_options` / `product_option_values`

`product_options`: `id`, `tenant_id`, `product_id`, `name` (`Talla`, `Color`), `position`.
`product_option_values`: `id`, `tenant_id`, `option_id`, `value`, `position`. Único `(option_id, value)`.

### `product_variants`

| Campo | Tipo | Nota |
|---|---|---|
| `id` | uuid | PK |
| `tenant_id` | uuid | FK |
| `product_id` | uuid | FK |
| `sku` | text | único por tenant |
| `name` | text | |
| `price_cents` | bigint | |
| `compare_at_price_cents` | bigint | nullable |
| `cost_cents` | bigint | nullable, solo staff |
| `currency` | text | `COP` |
| `weight_grams` | int | |
| `option_values` | jsonb | `{"Talla":"M","Color":"Negro"}` |
| `position` | int | |
| `is_active` | boolean | |
| `created_at`, `updated_at` | timestamptz | |

Índices: `(tenant_id, product_id)`, único `(tenant_id, sku)`.

### `product_media`

`id`, `tenant_id`, `product_id`, `media_asset_id`, `position`, `is_primary`, `created_at`. Único `(product_id, media_asset_id)`.

### `product_collections`

`tenant_id`, `product_id`, `collection_id`, `position`, `created_at`. PK `(product_id, collection_id)`.

### `media_assets` / `media_variants`

`media_assets`: `id`, `tenant_id`, `r2_key`, `mime`, `size_bytes`, `width`, `height`, `alt`, `blurhash`, `status` (`uploading`, `ready`, `failed`), timestamps.

`media_variants`: `id`, `tenant_id`, `media_asset_id`, `format` (`avif`, `webp`), `width`, `height`, `r2_key`, `size_bytes`. Único `(media_asset_id, format, width)`.

### `locations`

`id`, `tenant_id`, `name`, `address jsonb`, `is_default`, `created_at`.

### `inventory_levels`

| Campo | Tipo | Nota |
|---|---|---|
| `id` | uuid | PK |
| `tenant_id` | uuid | FK |
| `variant_id` | uuid | FK |
| `location_id` | uuid | FK |
| `available` | int | `>= 0` |
| `reserved` | int | `>= 0` |
| `safety_stock` | int | `>= 0` |
| `updated_at` | timestamptz | |

Único `(tenant_id, variant_id, location_id)`; check `available >= 0 and reserved >= 0`.

### `inventory_reservations`

`id`, `tenant_id`, `variant_id`, `cart_id` nullable, `order_id` nullable, `quantity`, `status` (`active`, `confirmed`, `released`, `expired`), `expires_at`, `created_at`. Índice `(tenant_id, variant_id, status, expires_at)`.

Regla: la suma de reservas activas + `reserved` no supera `available`. Se confirma en el webhook `paid`; se libera por TTL.

### `inventory_movements`

Append-only: `id`, `tenant_id`, `variant_id`, `delta`, `reason` (`sale`, `return`, `adjustment`, `restock`), `reference_type`, `reference_id`, `created_at`.

## 5. Contenido

### `pages`

`id`, `tenant_id`, `slug`, `title`, `status` (`draft`, `published`, `archived`), `draft_version_id`, `published_version_id`, `created_by`, `updated_by`, `created_at`, `updated_at`, `published_at`. Único `(tenant_id, slug)`.

### `page_versions`

`id`, `tenant_id`, `page_id`, `version_number`, `layout jsonb`, `schema_version`, `created_by`, `created_at`, `published_at`, `notes`. Único `(page_id, version_number)`. Inmutable cuando `published_at` no es null.

### `themes`

`id`, `tenant_id`, `name`, `preset` (`ropa`, `joyeria`, `custom`), `tokens jsonb`, `is_active`, `created_at`, `updated_at`. Único `(tenant_id, name)`; índice parcial único `(tenant_id) where is_active`.

### `redirects`

`id`, `tenant_id`, `from_path`, `to_path`, `status_code` (`301`, `302`), `created_at`. Único `(tenant_id, from_path)`.

### `outbox_events`

`id`, `tenant_id` nullable, `event_type`, `aggregate_type`, `aggregate_id`, `payload jsonb`, `status` (`pending`, `processing`, `done`, `failed`), `attempts`, `available_at`, `created_at`, `processed_at`.

## 6. Comercio

### `shipping_methods`

`id`, `tenant_id`, `name`, `zone` (`nacional`, `principal`, `otra`), `price_cents`, `min_order_cents` nullable, `max_order_cents` nullable, `is_active`, timestamps.

### `carts`

`id`, `tenant_id`, `token` (uuid, cookie), `customer_id` nullable, `status` (`active`, `converted`, `abandoned`), `currency`, `subtotal_cents`, `total_cents`, `expires_at`, `created_at`, `updated_at`. Único `(tenant_id, token)`.

### `cart_items`

`id`, `tenant_id`, `cart_id`, `variant_id`, `quantity`, `unit_price_cents`, `total_cents`, `created_at`, `updated_at`. Único `(cart_id, variant_id)`; check `quantity > 0`.

### `orders`

| Campo | Tipo | Nota |
|---|---|---|
| `id` | uuid | PK |
| `tenant_id` | uuid | FK |
| `order_number` | text | único por tenant |
| `public_token` | uuid | único; consulta pública de estado |
| `customer_id` | uuid | nullable |
| `email`, `phone` | text | |
| `status` | text | `pending_payment`, `paid`, `fulfilled`, `cancelled`, `refunded` |
| `payment_status` | text | `pending`, `paid`, `failed`, `refunded` |
| `fulfillment_status` | text | `unfulfilled`, `partial`, `fulfilled` |
| `currency` | text | `COP` |
| `subtotal_cents` | bigint | |
| `discount_cents` | bigint | `0` en MVP |
| `tax_cents` | bigint | IVA 19% |
| `shipping_cents` | bigint | |
| `total_cents` | bigint | |
| `shipping_address` | jsonb | snapshot |
| `billing_address` | jsonb | snapshot |
| `notes` | text | |
| `tracking_number`, `tracking_url` | text | fulfillment |
| `placed_at`, `paid_at`, `fulfilled_at`, `cancelled_at` | timestamptz | |
| `created_at`, `updated_at` | timestamptz | |

Índices: `(tenant_id, status, created_at desc)`, `(tenant_id, email)`, único `(tenant_id, order_number)`.

### `order_items`

`id`, `tenant_id`, `order_id`, `variant_id` nullable, `product_name`, `variant_name`, `sku`, `quantity`, `unit_price_cents`, `total_cents`, `tax_cents`, `tax_rate`, `metadata jsonb`. Snapshot inmutable.

### `order_events`

Append-only: `id`, `tenant_id`, `order_id`, `type`, `payload jsonb`, `actor`, `created_at`.

### `idempotency_keys`

`id`, `tenant_id`, `key`, `request_hash`, `response jsonb`, `created_at`, `expires_at`. Único `(tenant_id, key)`.

## 7. Pagos

### `tenant_payment_accounts`

`id`, `tenant_id`, `provider` (`wompi`), `status` (`pending`, `connected`, `error`), `provider_account_id`, `credentials_encrypted bytea`, `webhook_key uuid`, `created_at`, `updated_at`. Único `(tenant_id, provider)`; único `webhook_key`.

### `payments`

`id`, `tenant_id`, `order_id`, `provider`, `provider_payment_id`, `status` (`pending`, `authorized`, `paid`, `failed`, `expired`, `refunded`, `partially_refunded`), `amount_cents`, `currency`, `fee_cents` nullable, `provider_status`, `checkout_url`, `idempotency_key`, `created_at`, `updated_at`, `paid_at`. Único `(tenant_id, provider, provider_payment_id)`, único `(tenant_id, idempotency_key)`.

### `payment_events`

`id`, `tenant_id`, `provider`, `provider_event_id`, `type`, `payload_hash`, `status`, `processed_at`, `created_at`. Único `(tenant_id, provider, provider_event_id)`.

### `refunds`

`id`, `tenant_id`, `payment_id`, `provider_refund_id`, `amount_cents`, `reason`, `status`, `created_at`, `updated_at`. Único `(tenant_id, provider_refund_id)`.

## 8. Facturación DIAN

### `invoices`

`id`, `tenant_id`, `order_id`, `provider`, `provider_invoice_id`, `status` (`pending`, `issued`, `failed`, `voided`), `cufe`, `number`, `issued_at`, `pdf_url`, `xml_url`, `total_cents`, `tax_cents`, `error_code`, `created_at`, `updated_at`. Único `(tenant_id, provider_invoice_id)`.

### `invoice_events`

`id`, `tenant_id`, `invoice_id`, `type`, `payload_hash`, `created_at`. Append-only.

## 9. Gobernanza y operación

### `decision_logs`

Ver ADR-0007. Campos: `id`, `tenant_id`, `actor_type`, `actor_id`, `action`, `resource_type`, `resource_id`, `policy_id`, `policy_version`, `decision`, `reason_code`, `input_hash`, `context_summary jsonb`, `latency_ms`, `trace_id`, `created_at`, `prev_hash`, `hash`. Append-only, cadena por tenant.

### `approval_tasks`

`id`, `tenant_id`, `action`, `resource_type`, `resource_id`, `requested_by`, `assigned_role`, `status` (`pending`, `approved`, `rejected`, `expired`), `reason`, `expires_at`, `resolved_by`, `resolved_at`, `created_at`.

### `audit_chain_state`

`tenant_id` PK, `last_hash`, `last_log_id`, `updated_at`. Serializa appends con advisory lock.

### `job_runs`

`id`, `tenant_id` nullable, `job_name`, `status` (`running`, `succeeded`, `failed`), `started_at`, `finished_at`, `error`, `metadata jsonb`.

### `reconciliation_reports`

`id`, `tenant_id`, `provider`, `period_start`, `period_end`, `matched_count`, `mismatch_count`, `total_cents`, `status`, `created_at`.

## 10. Orden de migraciones

1. Extensiones (`pgcrypto`, `citext`, `pg_trgm`, `unaccent`), schema `app`, funciones `current_tenant()`, `resolve_tenant(host)`, `set_updated_at()`.
2. `tenants`, `domains`, `plans`, `tenant_settings`, `tenant_features`.
3. `memberships`, `customers`, `addresses`, `auth_events`, `platform_admins`.
4. `media_assets`, `media_variants`.
5. Catálogo: `categories`, `collections`, `products`, `product_options`, `product_option_values`, `product_variants`, `product_media`, `product_collections`, `locations`, `inventory_levels`, `inventory_reservations`, `inventory_movements`.
6. Contenido: `pages`, `page_versions`, `themes`, `redirects`, `outbox_events`.
7. Comercio: `shipping_methods`, `carts`, `cart_items`, `orders`, `order_items`, `order_events`, `idempotency_keys`.
8. Pagos: `tenant_payment_accounts`, `payments`, `payment_events`, `refunds`.
9. Billing: `platform_subscriptions`, `platform_invoices`, `billing_events`.
10. Facturas: `invoices`, `invoice_events`.
11. Gobernanza: `decision_logs`, `approval_tasks`, `audit_chain_state`.
12. Operación: `job_runs`, `reconciliation_reports`.

Cada migración incluye RLS, índices y tests. Sin `DROP` destructivo en el mismo deploy que el código.

## 11. Retención y datos personales

| Dato | Retención | Nota |
|---|---|---|
| Órdenes y facturas | 5 años | Obligación contable/DIAN |
| `decision_logs` | 5 años | Gobernanza |
| `auth_events` | 1 año | Seguridad |
| Carritos abandonados | 30 días | Luego anonimizar |
| Media huérfana | 30 días | Limpieza por job |
| Logs de aplicación | 30-90 días | Sin PII |

## 12. Pendientes

- Validar el modelo con el export de v0 (bloques y tokens reales).
- Confirmar el tratamiento de IVA del envío con contador (D-06).
- Definir si `customers` se crea en el primer checkout o solo al reclamar el magic link.
- Definir numeración de orden por tenant (secuencia vs timestamp).

## Enlaces

- [Overview](00-overview.md)
- [Tenancy](03-tenancy.md)
- [ADR-0003](../adr/0003-identidad-tenancy-rls.md)
- [ADR-0004](../adr/0004-pagos-checkout-merchant-of-record.md)
- [ADR-0005](../adr/0005-contenido-y-publishing.md)
