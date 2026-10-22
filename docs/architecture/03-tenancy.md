# Tenancy y threat model

> Aplica a todo el sistema. Se complementa con ADR-0003 y `.kiro/steering/security.md`.
> Regla base: **el tenant se resuelve en el servidor y se impone en PostgreSQL; nunca se confía en el cliente.**

## 1. Modelo de tenancy

- SaaS multi-tenant con base de datos compartida y aislamiento por **Row Level Security**.
- Resolución: `Host` normalizado → `domains.host` → `tenant_id`.
- El JWT de staff lleva `app_metadata.tenant_id` y `app_metadata.role`.
- El comprador es invitado; si usa magic link, su `auth_user_id` se vincula a `customers`.
- `X-Tenant-ID` es un hint interno entre servicios; nunca es fuente de verdad.
- Platform admin tiene `tenant_id = null` y acceso cross-tenant solo por endpoints auditados.

## 2. Fronteras de confianza

```text
Internet
  │  TLS
  ▼
Cloudflare / Vercel  ──► Storefront (RSC) ──► API
  │                                            │
  │                                            ├─► PostgreSQL (app_rw, RLS)
  │                                            ├─► Redis (cache/colas)
  │                                            ├─► R2 (URLs firmadas)
  │                                            └─► Wompi / Stripe (webhooks)
  │
  └─► Admin (JWT) ───────────────────────────► API

Workers (sin ingress) ──► PostgreSQL / Redis / R2 / email / DIAN
```

| Frontera | Amenaza principal | Control |
|---|---|---|
| Internet → Storefront | Host spoofing, XSS, scraping | TLS, normalización de host, CSP, rate limit |
| Admin → API | JWT robado, escalada de rol | JWKS, cookies HttpOnly, roles, RLS |
| API → DB | Fuga cross-tenant, SQL injection | `app_rw` sin bypass, RLS, consultas parametrizadas |
| Webhooks → API | Eventos falsos, replay | Firma, timestamp, idempotencia |
| API → Workers | Contexto de tenant perdido | Jobs con `tenant_id` explícito, `SET LOCAL` |
| Platform admin → API | Acceso indebido | Rol separado, auditoría, cuatro ojos |
| Supabase dashboard | Acceso humano directo | MFA, least privilege, auditoría, break-glass |

## 3. STRIDE

| Categoría | Amenaza | Mitigación | Verificación |
|---|---|---|---|
| **Spoofing** | Host de otro tenant | Normalizar host; `domains` verificado; TLS wildcard | Test de subdominio ajeno → 404/403 |
| **Spoofing** | JWT falsificado | Verificar firma JWKS, `iss`, `aud`, `exp` | Test firma inválida/`alg:none` |
| **Spoofing** | Webhook falsificado | Firma del proveedor + timestamp | Test firma inválida |
| **Spoofing** | `X-Tenant-ID` manipulado | Ignorar o validar contra host/JWT | Test header spoofeado → 403 |
| **Tampering** | `tenant_id` en body | Servidor asigna el tenant; schema lo prohíbe | Test create con tenant B → 422/403 |
| **Tampering** | Update cross-tenant | RLS `WITH CHECK` | Test update → 0 filas/403 |
| **Tampering** | XSS en contenido | Bloques cerrados, Markdown saneado, CSP | Test payload `<script>` → rechazado |
| **Tampering** | SQL injection | Consultas parametrizadas; sin SQL concatenado | Fuzzing de filtros |
| **Repudiation** | Acción sensible sin rastro | `decision_logs` hash chain | Test de verificación de cadena |
| **Information disclosure** | IDOR con UUID ajeno | RLS + tenant scope en repository | 12 vectores cross-tenant |
| **Information disclosure** | Caché mezclada | Clave de caché incluye tenant + página | Test A/B con hosts distintos |
| **Information disclosure** | URL firmada filtrada | TTL corto, prefijo por tenant | Test expiración |
| **Information disclosure** | PII en logs | Scrubber, allowlist de campos | Test de logs |
| **Denial of service** | Búsqueda costosa | Límites, GIN, cursor, rate limit | Test query gigante |
| **Denial of service** | Upload bomb | MIME/tamaño/dimensiones, antivirus | Test EICAR/imagen 100MP |
| **Denial of service** | Checkout flood | Rate limit, reservas TTL | Test de carga |
| **Elevation of privilege** | Cambio de rol | Solo `owner`; política `identity.change_role` | Test manager → owner |
| **Elevation of privilege** | `service_role` expuesto | Solo workers; nunca en API | Revisión de config/CI |
| **Elevation of privilege** | Platform admin sin auditoría | Endpoints auditados, cuatro ojos | Test de acceso cross-tenant |

## 4. Los 12 vectores cross-tenant

Fixtures: tenant A (`ropa`) y tenant B (`joyeria`), un owner y un packer por tenant, un producto, una página y una orden por tenant.

| # | Vector | Resultado esperado |
|---|---|---|
| 1 | Autenticado en A, cambiar `Host` a B | `403 TENANT_MISMATCH` |
| 2 | JWT de A + `X-Tenant-ID: B` | Se ignora el header; el tenant sale del JWT o del host |
| 3 | `GET /v1/products/{uuid_de_B}` con JWT de A | `404` (no filtrar existencia) |
| 4 | `POST /v1/products` con `tenant_id: B` en body | `422` (campo prohibido) o `403` |
| 5 | `PATCH` de producto de B con JWT de A | `404`/`403`, 0 filas |
| 6 | `GET /v1/products` sin filtro de tenant | Solo productos de A |
| 7 | `GET /v1/search?q=...&tenant_id=B` | Ignora el parámetro; solo A |
| 8 | Webhook con `webhook_key` de B y payload de A | `403`/`404`; no actualiza A |
| 9 | Webhook Stripe con `metadata.tenant_id` de B | `403`/`404`; no actualiza B |
| 10 | Preview token de B usado en host de A | `401 PREVIEW_INVALID` |
| 11 | Cache poisoning: página de A con host B | Respuesta de B o 404; nunca A |
| 12 | `r2_key` con `tenant/A/../B/...` | `403`; validación de prefijo |
| 13 | Job de A con contexto de B | Falla `TENANT_CONTEXT_MISMATCH` |
| 14 | Platform admin sin `reason`/auditoría | `403`/`422`; evento registrado |
| 15 | Token de A con `app_metadata.tenant_id` editado | `401 TOKEN_INVALID` |
| 16 | Membership desactivada con JWT vigente | `403 FORBIDDEN` en ruta sensible |

> Los vectores 1-12 son obligatorios en CI. Los 13-16 se añaden en la Wave 1 de seguridad.

Cobertura automatizada a hoy (`services/api/tests/security/test_tenant_isolation.py`, 10 tests sobre HTTP y RLS reales con dos tenants):

| Vector | Test | Estado |
|---|---|---|
| 2 | `test_x_tenant_id_header_is_ignored` | Cubierto (el header se ignora) |
| 3 | `test_admin_cannot_read_product_of_other_tenant` | Cubierto (`404`, sin filtrar existencia) |
| 4 | `test_body_cannot_force_another_tenant` | Cubierto (`422`: los schemas de entrada prohíben campos extra) |
| 5 | `test_admin_cannot_update_product_of_other_tenant` | Cubierto (`404` y 0 filas afectadas) |
| 6 | `test_admin_list_only_returns_own_tenant_products` | Cubierto |
| 7 | `test_storefront_ignores_tenant_id_query` | Cubierto (el tenant sale del host) |
| 11 (parcial) | `test_storefront_resolves_tenant_by_host` | Cubierto para el catálogo; falta la caché del storefront |
| 12 | `test_media_of_other_tenant_cannot_be_attached` | Cubierto (`404 MEDIA_NOT_FOUND`) |
| Extra | `test_media_list_only_returns_own_tenant`, `test_platform_admin_has_no_tenant_scope` | Sin fuga por media ni por platform admin |

Pendientes de automatizar cuando existan los endpoints que los exponen: vector 1 (binding host+JWT en rutas autenticadas), 8 y 9 (webhooks de pago), 10 (preview de contenido) y 11 completo (caché del storefront).

## 5. Capas de enforcement

1. **Borde:** TLS, WAF, rate limit, normalización de host.
2. **API:** resolución host→tenant, verificación JWKS, match de claim, autorización por rol, validación de schemas, headers de seguridad y límite de tamaño del cuerpo.
3. **Dominio:** servicios reciben `tenant_id` como parámetro explícito; repositories nunca construyen queries sin él.
4. **DB:** `app_rw` sin `BYPASSRLS`, RLS `ENABLE` + `FORCE`, políticas `USING`/`WITH CHECK`, constraints.
5. **Contenido:** schemas cerrados, Markdown saneado, CSP.
6. **Media:** prefijo `tenant/{id}/`, MIME real, URLs firmadas.
7. **Observabilidad:** logs con `tenant_id`, sin PII; alertas de `TENANT_MISMATCH`.

## 6. Checklist para una tabla nueva

- [ ] `tenant_id uuid not null references tenants(id)`.
- [ ] Índice por `tenant_id` (y compuestos según consultas).
- [ ] `ENABLE` + `FORCE ROW LEVEL SECURITY`.
- [ ] Política `tenant_id = app.current_tenant()` en `USING` y `WITH CHECK`.
- [ ] Sin `USING (true)`.
- [ ] Repository siempre recibe `tenant_id`; nunca lo lee del body.
- [ ] Tests A/B: SELECT, INSERT, UPDATE, DELETE.
- [ ] Si hay caché, la clave incluye `tenant_id`.
- [ ] Si hay media, el prefijo incluye `tenant_id`.
- [ ] Si hay endpoint sensible, pasa por `decide()` y auditoría.

## 7. Implementación actual (2026-10-21)

- Migración: `supabase/migrations/20261021000000_core_tenancy.sql`.
- `app_rw` sin `BYPASSRLS`; `tenants`, `domains`, `tenant_settings`, `tenant_features`, `memberships`, `customers`, `addresses` y `auth_events` con RLS `ENABLE` + `FORCE`.
- `public_transaction` fija `SET LOCAL ROLE app_rw` sin tenant para `app.resolve_tenant`/`app.create_tenant`; `tenant_transaction` añade `SET LOCAL app.tenant_id`.
- La API fija por transacción:
  ```sql
  SET LOCAL ROLE app_rw;
  SELECT set_config('app.tenant_id', $1, true);
  ```
  El rol se resetea al terminar la transacción; el pool nunca opera como superusuario.
- Tests pgTAP: `supabase/tests/tenancy.sql` (17) + `supabase/tests/catalog.sql` (14); 31 en total.
- Catálogo: `categories`, `products`, `product_variants`, `media_assets`, `media_variants`, `product_media`, `locations`, `inventory_levels`, `inventory_movements` e `inventory_reservations` con RLS forzado.
- Test de integración: `services/api/tests/integration/test_tenant_transaction.py` y `test_storefront_bootstrap.py` (requieren `GROWUP_TEST_DATABASE_URL`).
- `AuthService`: verifica JWKS, exige membership `active` y toma el rol de la base de datos (no del JWT). `/v1/admin/me` expone actor y permisos.
- `plans` es catálogo de plataforma y no usa `tenant_id`; `platform_admins` se consulta con `app.is_platform_admin(uuid)`.

## 8. Riesgos residuales

| Riesgo | Mitigación |
|---|---|
| Platform admin comprometido | MFA, cuatro ojos, auditoría, sesiones cortas |
| `service_role` mal usado en workers | Revisión de código, permisos mínimos, alertas |
| Acceso humano al dashboard de Supabase | MFA, roles, auditoría, break-glass |
| Pooler transaccional pierde `SET LOCAL` | Tests de integración, conexión directa para migraciones |
| Bug de RLS no detectado | Tests A/B en CI + pen-test de 12 vectores |
| Fuga por caché CDN | Tags por tenant, purga en publish, pruebas con dos hosts |

## 9. Incidente de fuga

1. Detectar por alerta de `TENANT_MISMATCH` o reporte.
2. Contener: revocar tokens/sesiones, deshabilitar endpoint o tenant afectado.
3. Preservar evidencia: `decision_logs`, `auth_events`, logs y trazas.
4. Notificar según Habeas Data y contratos.
5. Postmortem sin culpables y test de regresión del vector.

## Enlaces

- [ADR-0003](../adr/0003-identidad-tenancy-rls.md)
- [Modelo de datos](02-datos.md)
- [Security steering](../../.kiro/steering/security.md)
