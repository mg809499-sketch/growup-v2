# Design — Storefront Platform V2

- **Estado:** Borrador para revisión
- **Fecha:** 2026-10-21
- **Requirements:** [requirements.md](requirements.md)
- **Arquitectura:** [00-overview](../../../docs/architecture/00-overview.md) · [02-datos](../../../docs/architecture/02-datos.md) · [03-tenancy](../../../docs/architecture/03-tenancy.md)
- **ADRs:** [0001-0008](../../../docs/adr/README.md)

## 1. Vista de contenedores

```text
Browser
  ├─► Storefront (Vercel, Next 16 RSC) ──► API (Fly, FastAPI) ──► Supabase Postgres (RLS)
  └─► Admin (Vercel, Next 16) ──────────► API ──► Redis (cache/colas)
                                              ├─► R2 (media)
                                              ├─► Wompi (checkout)
                                              ├─► Stripe (suscripción)
                                              └─► DIAN provider (facturas)

Workers (ARQ, Fly) ──► Postgres / Redis / R2 / email / DIAN
```

## 2. Contexto de request

### 2.1 Orden del pipeline

1. `request_id` + `trace_id` (OTel).
2. Normalización de host.
3. Resolución de tenant:
   - **Storefront:** host → `domains` → tenant. El Next server reenvía el host original en `X-Storefront-Host`; es un hint público, no autenticación.
   - **Admin:** tenant desde el claim del JWT; el host debe ser `admin.growup.com`.
   - **Platform:** `platform_admin`, sin tenant; el tenant objetivo se fija tras auditar.
4. Verificación JWT (si aplica) con JWKS.
5. Match host/claim y autorización por rol.
6. Transacción DB con `SET LOCAL app.tenant_id`.
7. Handler de dominio.
8. Log + métrica + traza.

### 2.2 Dependencias de contexto

```python
@dataclass(frozen=True)
class RequestContext:
    tenant_id: UUID
    actor: Actor | None
    role: Role | None
    permissions: frozenset[str]
    trace_id: str
    request_id: str
```

- Ningún repository acepta `tenant_id` desde el body o query.
- El `tenant_id` se pasa explícito desde el contexto.
- `X-Tenant-ID` se ignora en el borde; solo se usa entre servicios internos y se valida contra el claim.

### 2.3 BFF del storefront

El navegador no llama directamente a FastAPI para mutaciones. El storefront usa Route Handlers/Server Actions como BFF:

1. El navegador llama a `{slug}.growup.com/api/...` (mismo origen, cookie de carrito).
2. Next normaliza el host y firma `X-Storefront-Host` + timestamp + path con `STOREFRONT_SHARED_SECRET`.
3. FastAPI valida la firma y el timestamp en mutaciones públicas (carrito, checkout, magic link).
4. Para lecturas públicas la firma es opcional; el tenant sigue resolviéndose por host.

Esto evita que un cliente llame directo a la API para crear carritos u órdenes masivas y mantiene el secreto fuera del navegador. El admin usa el JWT del staff y no depende de esta firma.

### 2.4 Errores

```json
{
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "No hay stock suficiente para Talla M / Negro",
    "details": {"variant_id": "...", "available": 0, "requested": 1},
    "request_id": "..."
  }
}
```

Códigos estables: `TENANT_MISMATCH`, `TENANT_NOT_FOUND`, `TOKEN_INVALID`, `TOKEN_EXPIRED`, `FORBIDDEN`, `VERSION_CONFLICT`, `INSUFFICIENT_STOCK`, `PAYMENT_MISMATCH`, `PLAN_LIMIT_REACHED`, `GOVERNANCE_DENIED`, `ORDER_ALREADY_FULFILLED`, `SLUG_TAKEN`, `SLUG_RESERVED`.

## 3. Superficie API

Base `/v1`. Versionado por prefijo; cambios breaking → `/v2`.

### 3.1 Storefront (público, tenant por host)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/storefront/bootstrap` | Tenant público, tema, navegación, settings, flags |
| GET | `/storefront/pages/{slug}` | Página publicada + versión |
| GET | `/storefront/products` | Listado con filtros y cursor |
| GET | `/storefront/products/{slug}` | Detalle con variantes y media |
| GET | `/storefront/collections/{slug}` | Colección + productos |
| GET | `/storefront/search` | Búsqueda + facets |
| POST | `/storefront/carts` | Crear carrito; devuelve token |
| GET | `/storefront/carts/{token}` | Carrito actual |
| PATCH | `/storefront/carts/{token}` | Agregar/actualizar/eliminar ítems |
| POST | `/storefront/checkout` | Crear orden + pago; `Idempotency-Key` |
| GET | `/storefront/orders/{public_token}` | Estado de la orden |
| POST | `/storefront/auth/magic-link` | Enviar magic link |
| POST | `/storefront/auth/claim` | Reclamar historial con sesión Supabase |

### 3.2 Admin (JWT + tenant)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/admin/me` | Usuario, tenant, rol, permisos |
| GET/POST/PATCH | `/admin/products` | Catálogo |
| GET/POST/PATCH | `/admin/products/{id}/variants` | Variantes |
| GET/POST/PATCH | `/admin/categories` | Categorías |
| GET/POST/PATCH | `/admin/collections` | Colecciones |
| GET/POST/PATCH | `/admin/inventory` | Niveles y ajustes |
| POST | `/admin/media/upload-url` | URL firmada |
| POST | `/admin/media/complete` | Confirmar upload y encolar procesamiento |
| GET/POST/PATCH | `/admin/pages` | Páginas y borradores |
| POST | `/admin/pages/{id}/publish` | Publicar |
| POST | `/admin/pages/{id}/rollback` | Rollback a versión |
| GET/POST/PATCH | `/admin/themes` | Temas y tokens |
| GET | `/admin/orders` | Lista con filtros |
| GET | `/admin/orders/{id}` | Detalle + timeline |
| POST | `/admin/orders/{id}/fulfill` | Fulfillment |
| POST | `/admin/orders/{id}/cancel` | Cancelación |
| POST | `/admin/orders/{id}/refund` | Refund |
| GET/PUT | `/admin/payments/account` | Cuenta Wompi (secretos write-only) |
| POST | `/admin/payments/account/validate` | Validar credenciales |
| GET | `/admin/billing` | Suscripción y facturas |
| POST | `/admin/billing/checkout` | Stripe Checkout |
| POST | `/admin/billing/portal` | Customer Portal |
| GET/POST/PATCH | `/admin/team` | Memberships |
| GET/PATCH | `/admin/settings` | Settings del tenant |
| GET | `/admin/audit` | Decisiones (owner) |

### 3.3 Platform admin

| Método | Ruta | Descripción |
|---|---|---|
| GET/POST | `/platform/tenants` | Listar/crear |
| GET | `/platform/tenants/{id}` | Detalle |
| POST | `/platform/tenants/{id}/suspend` | Suspender con razón |
| POST | `/platform/tenants/{id}/support-access` | Acceso temporal auditado |
| GET/PATCH | `/platform/plans` | Planes |
| GET | `/platform/audit` | Auditoría cross-tenant |
| GET | `/platform/reconciliation` | Reportes |

### 3.4 Webhooks

| Método | Ruta | Seguridad |
|---|---|---|
| POST | `/webhooks/wompi/{webhook_key}` | Firma Wompi + timestamp |
| POST | `/webhooks/stripe` | `Stripe-Signature` |
| POST | `/webhooks/dian/{provider}` | Secreto/firma del proveedor |
| POST | `/webhooks/email` | Firma del proveedor |

### 3.5 Ops

`GET /healthz`, `GET /readyz`, `GET /metrics` (red interna/token).

## 4. Diseño por dominio

### 4.1 Tenancy e identidad

- `TenantResolver`: normaliza host, consulta caché Redis, cae a `app.resolve_tenant(host)`.
- `AuthService`: JWKS cache, validación de claims, carga de membership y permisos.
- `OnboardingService`: crea tenant + domain + settings + tema + trial en una transacción; idempotente por slug.
- `EntitlementService`: evalúa plan, límites y estado de suscripción.
- Soporte: `support_access` emite token temporal con `reason`, `tenant_id`, `exp`; cada request queda auditado.

### 4.2 Catálogo e inventario

- Agregado `Product` con opciones, variantes y media.
- `InventoryService`:
  - Reservar: `UPDATE inventory_levels SET reserved = reserved + $qty WHERE variant_id = $id AND available - reserved >= $qty RETURNING ...`; si 0 filas → `INSUFFICIENT_STOCK`.
  - Insertar `inventory_reservations` con TTL.
  - Confirmar: `available -= qty`, `reserved -= qty`, reserva `confirmed`, movimiento `sale`.
  - Liberar: `reserved -= qty`, reserva `released`.
  - Job de expiración cada minuto.
- `SearchService`: `websearch_to_tsquery('spanish', q)`, ranking `ts_rank`, fallback `similarity` con `pg_trgm`; facets por categoría, talla, color y rango de precio.
- `MediaService`: URL firmada, validación en worker, variantes, CDN.

### 4.3 Contenido

- `PageService`: draft, autosave, control optimista, preview.
- `PublishService`: validación de schema + permisos + render; transacción; outbox; purge.
- `BlockRegistry`: Pydantic discriminated unions y componentes TS espejo.
- `ThemeService`: tokens cerrados; presets.
- Preview: JWT firmado (`PREVIEW_SECRET`) con `tenant_id`, `page_id`, `version_id`, `exp`, `scope=preview`.
- Revalidación: worker llama a `POST /api/revalidate` del storefront con `REVALIDATE_SECRET` y tags.

### 4.4 Carrito, checkout y órdenes

- Carrito por token UUID en cookie `HttpOnly` del dominio del tenant; TTL 30 días.
- Checkout:
  1. Validar carrito y re-precios en servidor.
  2. Reservar stock en transacción.
  3. Crear `order` + `order_items` snapshot + `payment` + `public_token`.
  4. Devolver URL de Wompi Web Checkout.
- Webhook `paid`:
  1. Verificar firma y monto.
  2. Marcar pago/orden pagados.
  3. Confirmar reserva y descontar stock.
  4. Encolar email + factura.
  5. Registrar `order_event`.
- Idempotencia: `Idempotency-Key` en checkout/refund; tabla `idempotency_keys`; replay devuelve la misma respuesta.
- Máquina de estados explícita; transiciones inválidas → `409`.

### 4.5 Pagos

- `PaymentProvider` port; `WompiProvider` con Web Checkout.
- Credenciales por tenant cifradas con AES-GCM y clave en secreto (`PAYMENT_CREDENTIALS_KEY`); `key_id` para rotación.
- Webhook: resolver tenant por `webhook_key`; `SET LOCAL`; `payment_events` único; transacción; outbox.
- Refunds: idempotentes, con `provider_refund_id`; sobre umbral → `HANDOFF`.
- Conciliación: job diario; reporte; alerta.

### 4.6 Billing

- `BillingProvider` port; `StripeBillingProvider`.
- Checkout Session con trial 14 días; Customer Portal.
- Webhook Stripe: `metadata.tenant_id` + `stripe_customer_id`; actualiza suscripción; recalcula entitlements.
- Gracia `past_due` 5 días; luego `suspended`: bloquea publish/checkout, mantiene lectura.
- Respaldo `MercadoPagoProvider` si Stripe no opera para la entidad.

### 4.7 Facturas DIAN

- `InvoiceProvider` port; adaptador Factus/Siigo/Alegra (por definir).
- Al pagar: job `invoice.issue`; guarda `provider_invoice_id`, CUFE, número, PDF/XML en bucket privado.
- Reintentos con backoff; `failed` alerta; no bloquea la orden.
- Refund post-factura → nota crédito o `HANDOFF`.

### 4.8 Gobernanza

- `decide(policy_id, input)`; políticas versionadas.
- `decision_logs` append-only con hash chain; verificación diaria.
- `approval_tasks` para handoff; cuatro ojos.
- Endpoints sensibles instrumentados; test de cobertura.

### 4.9 Notificaciones

- Outbox → worker → proveedor de email.
- Plantillas versionadas; texto plano; rebotes y quejas por webhook.
- Reintentos con backoff y dead-letter.

## 5. Flujos

### 5.1 Bootstrap del storefront

```text
GET {slug}.growup.com
→ Next server: host = ropa.growup.com
→ GET api.growup.com/v1/storefront/bootstrap (X-Storefront-Host: ropa.growup.com)
→ API resuelve tenant, carga settings/tema, cachea
→ Next renderiza layout + página
```

### 5.2 Checkout

```text
POST /v1/storefront/checkout (Idempotency-Key)
→ valida carrito, stock y precios
→ reserva stock (TTL 15 min)
→ crea order + payment
→ devuelve checkout_url de Wompi
→ comprador paga en Wompi
→ Wompi → POST /webhooks/wompi/{webhook_key}
→ verifica firma/monto, marca paid, confirma stock
→ outbox: email, invoice
→ GET /storefront/orders/{public_token} muestra confirmación
```

### 5.3 Publish

```text
PUT /admin/pages/{id} (expected_version)
→ 409 si conflicto
POST /admin/pages/{id}/publish
→ valida schema/permisos/render
→ crea page_version + published_version_id
→ outbox → worker purge tag
```

## 6. Modelo de datos

Ver [02-datos.md](../../../docs/architecture/02-datos.md). El modelo incluye en `orders`:

- `public_token uuid unique not null` para consulta pública.
- `tracking_number text` y `tracking_url text` para fulfillment.

## 7. Caché

| Dato | TTL | Invalidación |
|---|---|---|
| Tenant por host | 5 min | Cambio de domain |
| Bootstrap (tema/settings) | 60 s | Cambio de theme/settings |
| Página publicada | 60 s + SWR | Publish/rollback |
| Listado de productos | 30 s | Cambio de producto/stock |
| Detalle de producto | 60 s | Cambio de producto |
| Carrito/checkout | Sin caché | — |
| Admin | Sin caché | — |

Claves siempre incluyen `tenant_id`. Purga por tag `tenant:{id}:page:{slug}`.

## 8. Seguridad

- ADR-0003 y [03-tenancy.md](../../../docs/architecture/03-tenancy.md).
- `app_rw` sin `BYPASSRLS`; `service_role` solo workers.
- Webhooks firmados, timestamp e idempotencia.
- Secretos write-only; cifrado de credenciales de pago.
- CSP, HSTS, CORS allowlist, rate limit.
- 12 vectores cross-tenant en CI.

## 9. Observabilidad

- Sentry por servicio; OTel traces; logs JSON con `tenant_id`, `trace_id`, `request_id`.
- Métricas: requests, latencia, 5xx, checkout conversion, stock reservations, webhook failures, queue depth, publish duration.
- Alertas según ADR-0006/0008.

## 10. Testing

| Nivel | Herramienta | Cobertura |
|---|---|---|
| Unit | pytest | Servicios, políticas, money, state machines |
| Integración | pytest + Postgres | RLS, inventario concurrente, webhooks, idempotencia |
| Contratos | openapi-typescript | Tipos generados al día |
| E2E | Playwright | Storefront/admin, dos tenants, checkout sandbox |
| Carga | k6 | Checkout concurrente, búsqueda, publish |
| Seguridad | pytest + ZAP | 12 vectores, headers, dependency audit |
| A11y | axe | Páginas piloto |
| Visual | Playwright screenshots | Dos temas |

## 11. Despliegue

Ver ADR-0008. Staging automático desde `main`; producción con aprobación; migraciones expand/contract; rollback de Vercel/Fly.

## 12. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Export de v0 tarde | Retrasa Wave 3 | Tokens y registry se pueden construir con el prompt |
| API de Wompi distinta a lo previsto | Retrasa checkout | Spike en Wave 0; adapter aislado |
| Stripe no opera para la entidad | Bloquea billing | Respaldo MercadoPago |
| Reglas de IVA del envío | Totales incorrectos | Confirmar con contador antes de Wave 4 |
| Connection limits de Supabase | Caídas en picos | Pooler transaccional, límites, load test |
| Equipo pequeño | Retrasa Q1 2027 | Olas con alcance mínimo y recortes explícitos |

## 13. Decisiones abiertas

- Proveedor DIAN concreto.
- IVA del envío y redondeo.
- Stripe vs MercadoPago para la entidad.
- Proveedor de email y región.
- Contenido y fecha exacta del piloto.

## Enlaces

- [Requirements](requirements.md)
- [Tasks](tasks.md)
- [ADRs](../../../docs/adr/README.md)
