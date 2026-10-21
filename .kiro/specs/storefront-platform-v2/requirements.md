# Requirements — Storefront Platform V2

- **Estado:** Borrador para revisión
- **Fecha:** 2026-10-21
- **Decisiones:** D-01 a D-08 cerradas
- **ADRs:** 0001-0008
- **Alcance:** MVP comercial con dos tenants piloto (ropa y joyería), lanzamiento Q1 2027

## 1. Propósito

Construir la plataforma SaaS multi-tenant que permite a un comerciante crear su tienda, cargar catálogo, editar páginas con un builder de bloques, publicar en `{slug}.growup.com` y vender con checkout invitado y pagos Wompi, mientras Growup cobra una suscripción mensual.

## 2. Personas

| Persona | Necesidad |
|---|---|
| Comprador | Encontrar productos, comprar rápido y confiar en el pago |
| Comerciante (owner) | Publicar su tienda sin depender de un desarrollador |
| Manager | Gestionar catálogo, contenido y pedidos |
| Treasurer | Ver pagos, facturas y conciliación |
| Packer | Ver pedidos pagados y marcar fulfillment |
| Support | Atender compradores sin ver datos sensibles innecesarios |
| Platform admin | Operar tenants, planes, soporte y auditoría |

## 3. Glosario

- **Tenant:** comerciante con datos aislados.
- **Storefront:** tienda pública en `{slug}.growup.com`.
- **Admin:** backoffice del comerciante.
- **Bloque:** unidad de contenido con schema cerrado.
- **Versión publicada:** snapshot inmutable de una página.
- **Merchant of record:** comerciante que vende y recibe el dinero.
- **Entitlement:** capacidad habilitada por plan/suscripción.

## 4. Requisitos funcionales

### 4.1 Tenancy y onboarding (TEN)

**TEN-01 — Crear tenant** *(Must)*
Como platform admin, quiero crear un tenant con nombre, slug y plan para dejarlo operativo.
- Given un slug único y válido, when creo el tenant, then se crean `tenant`, `domain {slug}.growup.com`, settings, tema por defecto y suscripción en trial.
- Given un slug reservado (`admin`, `api`, `www`, `app`, `mail`), then `400 SLUG_RESERVED`.
- Given un slug duplicado, then `409 SLUG_TAKEN`.
- El tenant nuevo no puede publicar hasta completar onboarding.

**TEN-02 — Resolver tenant por host** *(Must)*
- Given `Host: ropa.growup.com`, then se resuelve el tenant `ropa`.
- Given un host desconocido, then `404 TENANT_NOT_FOUND`.
- Given mayúsculas, puerto o punto final, then se normaliza y resuelve igual.
- La resolución se cachea y se invalida al cambiar `domains`.

**TEN-03 — Settings del tenant** *(Must)*
- Moneda `COP`, locale `es-CO`, navegación, SEO defaults, zonas de envío y contacto.
- Los cambios se validan con schema y se auditan.

**TEN-04 — Entitlements** *(Must)*
- El plan define límites (productos, media, usuarios, storage).
- Un límite excedido devuelve `402 PLAN_LIMIT_REACHED` o degradación definida.
- La suspensión por impago bloquea publish y checkout, no la lectura del storefront.

### 4.2 Identidad y acceso (AUTH)

**AUTH-01 — Login de staff** *(Must)*
- Supabase Auth; JWT verificado por JWKS.
- Solo memberships `active` acceden.
- Token inválido/expirado → `401 TOKEN_INVALID` / `TOKEN_EXPIRED`.

**AUTH-02 — Tenant match** *(Must)*
- El claim `tenant_id` debe coincidir con el host resuelto.
- Mismatch → `403 TENANT_MISMATCH` + `auth_event`.

**AUTH-03 — Roles** *(Must)*
- `owner`: todo, incluye equipo y billing.
- `manager`: catálogo, contenido, pedidos; no billing ni roles.
- `treasurer`: pagos, facturas, conciliación; no contenido.
- `packer`: pedidos pagados y fulfillment.
- `support`: lectura de pedidos y clientes enmascarados; sin mutaciones.
- Un rol inferior no puede escalar; `403 FORBIDDEN`.

**AUTH-04 — Comprador invitado + magic link** *(Must)*
- Checkout sin cuenta.
- Magic link opcional para ver historial; vincula `customers.auth_user_id`.
- Sin contraseñas de comprador.
- Link expirado → `401 MAGIC_LINK_EXPIRED`.

**AUTH-05 — Platform admin** *(Must)*
- Rol separado, `tenant_id = null`.
- Acceso cross-tenant solo con razón y auditoría.
- Sin `BYPASSRLS`.

### 4.3 Catálogo e inventario (CAT)

**CAT-01 — Categorías y colecciones** *(Must)*
- CRUD con slug único por tenant, jerarquía de categorías y colecciones manuales.

**CAT-02 — Productos** *(Must)*
- CRUD con estado `draft`, `active`, `archived`.
- Slug único por tenant; SEO; descripción Markdown restringido.
- Un producto solo se publica si tiene al menos una variante activa y una imagen.

**CAT-03 — Variantes y opciones** *(Must)*
- Opciones (Talla, Color) y valores.
- Variante con SKU único por tenant, precio en centavos, stock y `option_values`.
- Precio > 0; `compare_at_price` >= precio.

**CAT-04 — Media** *(Must)*
- Upload por URL firmada; MIME real, tamaño y dimensiones.
- Variantes AVIF/WebP; strip EXIF; alt text obligatorio.
- Reordenar; una primaria por producto.

**CAT-05 — Inventario** *(Must)*
- `available`, `reserved`, `safety_stock`; nunca negativo.
- Ajustes con motivo y movimiento append-only.
- Reserva temporal en checkout y confirmación en pago.

**CAT-06 — Búsqueda** *(Must)*
- FTS en español, tolerancia a tildes y errores con `pg_trgm`.
- Filtros por categoría, precio, atributos y disponibilidad.
- Solo productos `active`; paginación por cursor.

**CAT-07 — Catálogo en storefront** *(Must)*
- Listado, detalle, colección y búsqueda.
- Precio con IVA incluido, disponibilidad por variante, imágenes optimizadas.
- JSON-LD de producto y breadcrumbs.

### 4.4 Contenido y builder (CONT)

**CONT-01 — Tema** *(Must)*
- Tokens cerrados (color, tipografía, espaciado, radios, sombras).
- Presets `ropa` y `joyeria`; un tema activo por tenant.
- Cambiar tokens no requiere republicar páginas.

**CONT-02 — Páginas** *(Must)*
- CRUD con slug único, título, estado y SEO.
- Home obligatoria en `/`.

**CONT-03 — Bloques** *(Must)*
- Registry cerrado con los tipos del ADR-0005.
- Schema Pydantic/Zod; límites; alt text; links validados.
- Sin HTML, scripts, iframes libres ni CSS arbitrario.

**CONT-04 — Builder** *(Must)*
- Drag-and-drop, edición de props, reordenar, duplicar y eliminar.
- Autosave con control optimista; conflicto → `409 VERSION_CONFLICT`.
- Preview del borrador.

**CONT-05 — Preview** *(Must)*
- Token firmado de corta duración; no indexable.
- Renderiza el borrador o una versión específica.

**CONT-06 — Publish** *(Must)*
- Valida schema, permisos y render.
- Crea versión inmutable y actualiza `published_version_id` en una transacción.
- Purga caché por tenant/página.
- Falla sin cambiar nada si hay error.

**CONT-07 — Rollback** *(Must)*
- Apuntar a una versión anterior y purgar caché.
- No se borra la versión nueva.

**CONT-08 — Render del storefront** *(Must)*
- Solo versiones publicadas.
- Bloque desconocido → fallback seguro.
- SEO, sitemap, robots, canonical y accesibilidad.
- LCP móvil < 2.5 s en las páginas piloto.

### 4.5 Carrito y checkout (CART/CHK)

**CART-01 — Carrito** *(Must)*
- Agregar, actualizar cantidad y eliminar.
- Valida stock y precio en servidor.
- Carrito por cookie/token; expira a los 30 días.

**CART-02 — Revalidación** *(Must)*
- Al abrir checkout se recalculan precios, impuestos y envío.
- Si un precio cambió, se informa antes de pagar.

**CHK-01 — Checkout invitado** *(Must)*
- Email, teléfono, dirección y envío.
- Sin cuenta; email válido; teléfono CO.
- No se acepta precio ni total del cliente.

**CHK-02 — Reserva de stock** *(Must)*
- Reserva atómica con TTL de 15 minutos.
- Si no hay stock → `409 INSUFFICIENT_STOCK` con variante.
- Pago confirmado → reserva confirmada; fallo/expiración → liberada.
- Bajo concurrencia no hay overselling.

**CHK-03 — Idempotencia** *(Must)*
- `checkout_idempotency_key` único por intento.
- Reintento devuelve la misma orden/pago, no duplica.

**CHK-04 — Pago** *(Must)*
- Wompi Web Checkout con credenciales del tenant.
- Redirect de vuelta a la confirmación; la orden sigue `pending_payment` hasta el webhook.
- El navegador nunca confirma el pago.

**CHK-05 — Confirmación** *(Must)*
- Página de gracias con número de orden y estado.
- Email de confirmación.
- Sin datos de tarjeta.

### 4.6 Pagos (PAY)

**PAY-01 — Cuenta de pagos del tenant** *(Must)*
- Conectar Wompi; validar credenciales; estado `connected`/`error`.
- Credenciales cifradas; nunca se devuelven al cliente.

**PAY-02 — Webhook Wompi** *(Must)*
- Verificar firma y timestamp; idempotencia por `provider_event_id`.
- Resolver tenant por `webhook_key`; `SET LOCAL`.
- Monto/moneda distinto → `PAYMENT_MISMATCH`, no fulfillment.

**PAY-03 — Refunds** *(Must)*
- Registro idempotente; estado; motivo.
- Sobre umbral → `HANDOFF` (ADR-0007).

**PAY-04 — Conciliación** *(Should)*
- Reporte diario por tenant; mismatches y alerta.

**PAY-05 — PCI** *(Must)*
- Sin PAN/CVV; hosted checkout; logs sin secretos.

### 4.7 Órdenes (ORD)

**ORD-01 — Crear orden** *(Must)*
- Snapshot de ítems, precios, impuestos, envío y direcciones.
- Número único por tenant.
- Estados y timestamps.

**ORD-02 — Admin de pedidos** *(Must)*
- Lista con filtros y búsqueda; detalle con timeline.
- `packer` ve solo pagados; `support` ve PII enmascarada.

**ORD-03 — Fulfillment** *(Must)*
- Marcar `fulfilled` con tracking opcional.
- No se puede fulfillment sin pago.

**ORD-04 — Cancelación** *(Must)*
- Antes de fulfillment; libera stock; refund si estaba pagada.
- Después de fulfillment → `409 ORDER_ALREADY_FULFILLED`.

**ORD-05 — Emails** *(Must)*
- Confirmación de orden y de envío.
- Reintentos y registro de rebotes.

### 4.8 Facturación DIAN (INV)

**INV-01 — Emisión** *(Must)*
- Al confirmar pago, encolar emisión con proveedor certificado.
- Guardar `provider_invoice_id`, CUFE, número, PDF/XML.
- Reintentos con backoff; estado `pending`/`issued`/`failed`.

**INV-02 — Acceso** *(Must)*
- PDF/XML por URL firmada; el comprador puede descargar.
- Sin exposición pública.

**INV-03 — Nota crédito** *(Should)*
- Refund después de factura emitida genera nota crédito.
- Si el proveedor no lo soporta, `HANDOFF` manual.

**INV-04 — Resiliencia** *(Must)*
- Proveedor caído no bloquea la orden; la factura queda pendiente y alerta.

### 4.9 Suscripción de plataforma (BILL)

**BILL-01 — Planes** *(Must)*
- Starter y Pro; trial 14 días; 0% comisión.
- Límites por plan en `tenant_features`.

**BILL-02 — Stripe Billing** *(Must)*
- Checkout Session y Customer Portal.
- Webhooks firmados e idempotentes.

**BILL-03 — Entitlements** *(Must)*
- `trialing`, `active`, `past_due` (gracia), `canceled`.
- `past_due` alerta; `canceled` suspende publish/checkout tras la gracia.

**BILL-04 — Facturas de plataforma** *(Should)*
- Listar y descargar PDF.

**BILL-05 — Dunning** *(Should)*
- Emails de cobro fallido; reintentos de Stripe.

### 4.10 Gobernanza (GOV)

**GOV-01 — `decide()`** *(Must)*
- Interfaz determinista; políticas versionadas; `ALLOW`/`DENY`/`HANDOFF`.
- Endpoints sensibles cubiertos por test.

**GOV-02 — Auditoría** *(Must)*
- `decision_logs` append-only con hash chain por tenant.
- Verificación diaria; fallo → alerta y bloqueo de mutaciones sensibles.

**GOV-03 — Aprobaciones** *(Must)*
- Reembolsos altos y accesos cross-tenant requieren cuatro ojos.
- Expiración y resolución auditadas.

**GOV-04 — IA-ready** *(Should)*
- Contrato de `ActionProposal`; sin IA en el MVP.

### 4.11 Operación (OPS)

**OPS-01 — Salud y observabilidad** *(Must)*
- `/healthz`, `/readyz`; Sentry; OTel; logs con `tenant_id`/`trace_id`.

**OPS-02 — CI/CD** *(Must)*
- Lint, tipos, tests, contratos, migraciones, seguridad.
- Staging automático; producción con aprobación.

**OPS-03 — Backups** *(Must)*
- PITR + dump diario; restauración trimestral.

**OPS-04 — Borde** *(Must)*
- WAF, rate limit, HSTS, CSP, CORS.

**OPS-05 — Runbooks** *(Must)*
- Incidentes, restore, rotación de claves, webhook caído.

## 5. Requisitos no funcionales

| Categoría | Requisito |
|---|---|
| Performance | LCP móvil p75 < 2.5 s; CLS < 0.1; INP < 200 ms; API p95 < 300 ms; búsqueda p95 < 300 ms |
| Disponibilidad | Storefront/API 99.9%; admin 99.5% |
| Escala | 100 tenants, 10.000 productos/tenant, 1.000 usuarios concurrentes |
| Seguridad | OWASP ASVS L2; 12 vectores cross-tenant en CI; sin PII en logs; PCI SAQ A |
| Accesibilidad | WCAG 2.2 AA; 0 violaciones críticas en axe |
| SEO | SSR, sitemap, canonical, JSON-LD, OG |
| Datos | RPO ≤ 15 min; RTO ≤ 2 h |
| Observabilidad | 100% requests con `trace_id`; alertas de 5xx, cola, webhooks, cadena |
| Costo | Alertas de presupuesto por proveedor |

## 6. Fuera de alcance

Returns/RMA, bespoke, promociones/descuentos, envío blindado, IA/WhatsApp, L402, multi-moneda, dominios custom, comisión por venta/marketplace, app móvil, multi-idioma, reviews, wishlist. Ver D-05.

## 7. Pendientes

| Tema | Estado | No bloquea |
|---|---|---|
| Proveedor DIAN concreto (Factus/Siigo/Alegra) | Por definir antes de Wave 5 | Catálogo, builder, checkout |
| IVA del envío y redondeos | Confirmar con contador | Checkout puede usar regla provisional |
| Stripe para entidad colombiana | Verificar | Billing; respaldo MercadoPago |
| Fecha exacta y responsable de contenido | Por definir dentro de Q1 2027 | Waves 0-6 |
| Export de v0 | Pendiente de recibir | Integración visual de Wave 3 |
| Proveedor de email y región | Por definir | Wave 4/8 |

## 8. Criterios de aceptación del MVP

1. Dos tenants (ropa y joyería) publican su home con temas distintos sin redeploy.
2. Catálogo con variantes, media, inventario y búsqueda.
3. Checkout invitado con Wompi sandbox; 100 compras concurrentes sin overselling.
4. Pago confirmado → orden pagada + email + factura DIAN emitida (sandbox).
5. Suscripción con trial de 14 días vía Stripe sandbox; entitlements correctos.
6. Los 12 vectores cross-tenant pasan; cero fugas.
7. LCP móvil < 2.5 s y WCAG 2.2 AA en las páginas piloto.
8. Restauración de backup probada dentro del RTO.
9. Runbooks y alertas operativas listas.
10. Ningún secreto ni PII en logs o repositorio.
