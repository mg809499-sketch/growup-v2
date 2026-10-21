# Tasks — Storefront Platform V2

- **Estado:** En ejecución
- **Fecha:** 2026-10-21
- **Objetivo:** MVP comercial con ropa + joyería en Q1 2027
- **Referencias:** [requirements.md](requirements.md) · [design.md](design.md) · [ADR-0008](../../../docs/adr/0008-topologia-despliegue.md)

## Resumen de olas

| Ola | Foco | Ventana indicativa | Salida |
|---|---|---|---|
| 0 | Fundación | Nov 2026 (1-2 sem) | CI, staging, migraciones base, contratos |
| 1 | Tenancy e identidad | Nov-Dic 2026 (2 sem) | Login, resolución de tenant, RLS probado |
| 2 | Catálogo y media | Dic 2026 (3 sem) | Productos, variantes, media, búsqueda |
| 3 | Contenido y storefront | Dic-Ene 2027 (3 sem) | Builder, publish, dos homes |
| 4 | Carrito, checkout y pagos | Ene 2027 (3 sem) | Compra sandbox end-to-end |
| 5 | Billing y facturas | Feb 2027 (2 sem) | Trial, suscripción, factura DIAN |
| 6 | Gobernanza y platform admin | Feb 2027 (1-2 sem) | `decide()`, auditoría, soporte |
| 7 | Hardening | Feb-Mar 2027 (2 sem) | NFRs, seguridad, restore |
| 8 | Piloto | Mar 2027 (2 sem) | Dos tenants publicados |

> Supuesto: 1-2 ingenieros full-time con apoyo de diseño/contenido. Si la capacidad baja, recortar Wave 6 a lo mínimo y mover la fecha; no recortar aislamiento, tests de overselling ni restore.

## Estado actual (2026-10-21)

| Tarea | Estado | Evidencia |
|---|---|---|
| W0-02 | Hecho | Migración `20261021000000_core_tenancy.sql`; `supabase db reset` limpio |
| W0-03 | Hecho | `Database` con `SET LOCAL ROLE app_rw` + `app.tenant_id`; `/readyz`; tests unitarios e integración |
| W0-04 | Hecho | `packages/contracts` + `pnpm contracts:check` + job CI |
| W0-05 | Pendiente | Espera export de v0 |
| W0-06 | Pendiente | Playwright |
| W0-07 | Pendiente | Sentry/OTel |
| W0-08 | Pendiente | Spikes Wompi/Stripe |
| W1-01 | Parcial | Tenancy core con RLS; faltan tablas de olas 2-5 |
| W1-02 | Hecho | `TenantResolver` + `PostgresTenantRepository` + `/v1/storefront/bootstrap`; tests unitarios, API e integración |
| W1-03 | Hecho | JWT/JWKS + `AuthService` + memberships + roles/permisos + `/v1/admin/me` |
| W1-04 | Pendiente | Login admin con Supabase SSR y cookies (frontend) |
| W1-05 | Hecho | `POST /v1/platform/tenants` con `decide()` + `create_tenant_with_owner` + auditoría; tests unitarios e integración |
| W1-06 | Parcial | 67 pgTAP (17 tenancy + 14 catálogo + 21 gobernanza + 9 inventario + 6 seguridad) + integración; faltan los 12 vectores HTTP |
| W1-07 | Parcial | `is_platform_admin` y rol; falta support access temporal |
| W1-08 | Pendiente | `auth_events` + alertas de mismatch |
| W2-01 | Hecho | Migración de catálogo + 14 tests pgTAP (67 en total) |
| W2-02 | Parcial | API create/list/get/update de productos y variantes; faltan update/delete de variantes y opciones normalizadas |
| W2-03 | Pendiente | Upload de media a R2 y procesamiento de variantes |
| W2-04 | Hecho | `inventory_reservations` con `location_id`, check `reserved <= available`, reserva/confirmación/liberación/expiración + 9 pgTAP |
| W2-05 | Parcial | FTS español + filtros + cursor; faltan facetas |
| W2-06 | Parcial | Listado y detalle storefront; faltan colecciones e imágenes |
| W2-07 | Parcial | API admin de catálogo; falta UI |
| W2-08 | Hecho | 40 reservas concurrentes sobre stock 10: 10 éxitos, 30 `INSUFFICIENT_STOCK`, sin negativos |
| W2-09 | Pendiente | Seed de catálogo piloto |
| W6-01 | Hecho | `decide()` determinista con políticas versionadas y fail-closed; tests table-driven |
| W6-02 | Hecho | `decision_logs` + cadena por `chain_key` + `verify_decision_chain`; 21 pgTAP, tamper detectado y guard de contexto de tenant |
| W6-03 | Parcial | Tabla `approval_tasks` con RLS; falta bandeja/UI y handoff desde `decide()` |
| W6-04 | Parcial | `POST /v1/platform/tenants`; faltan listar/suspender y UI |

## Definition of Done (por tarea)

- [ ] Tests unitarios/integración; RLS A/B si toca tabla de tenant.
- [ ] `ruff`, `mypy`, `pytest`; `tsc`, `next build` si toca frontend.
- [ ] Contratos OpenAPI regenerados.
- [ ] Sin secretos ni PII en logs.
- [ ] Documentación/ADR actualizado si cambió una decisión.
- [ ] Evidencia en el PR (test, captura, métrica o runbook).

---

## Wave 0 — Fundación

| ID | Tarea | Depende | Aceptación / evidencia |
|---|---|---|---|
| W0-01 | Verificar monorepo, CI y reglas de agentes | — | `ruff`, `mypy`, `pytest` en verde; CI en GitHub |
| W0-02 | Supabase local + migración base (`app`, extensiones, `current_tenant`, `resolve_tenant`, `set_updated_at`) | W0-01 | `supabase db reset` limpio; tests de funciones |
| W0-03 | Core API: config, DB async, contexto de tenant, errores, `/healthz`, `/readyz` | W0-02 | Health/ready en staging; error envelope testeado |
| W0-04 | Contratos OpenAPI → `packages/contracts` + check en CI | W0-03 | Tipos generados; CI falla si hay drift |
| W0-05 | Scaffolding Next 16: storefront y admin, Tailwind 4, tokens base | W0-01 | `pnpm build` en verde; deploy preview |
| W0-06 | Playwright + fixtures de dos tenants | W0-05 | Smoke test de dos hosts |
| W0-07 | Observabilidad base: Sentry, OTel, logs JSON, `trace_id` | W0-03 | Traza visible Next→API; alerta de prueba |
| W0-08 | Spikes Wompi y Stripe sandbox | W0-03 | Documento con API real, webhooks y limitaciones |
| W0-09 | Definir región Supabase/Fly y medir latencia Colombia | W0-03 | Medición y decisión documentada |

## Wave 1 — Tenancy e identidad

| ID | Tarea | Depende | Aceptación / evidencia |
|---|---|---|---|
| W1-01 | Migraciones `tenants`, `domains`, `tenant_settings`, `tenant_features`, `plans` + RLS | W0-02 | RLS A/B; sin `USING (true)` |
| W1-02 | `TenantResolver`: normalización de host, caché Redis, invalidación | W1-01 | Tests de host con puerto/mayúsculas/desconocido |
| W1-03 | Auth JWKS + memberships + roles + permisos | W1-01 | Firma inválida/`alg:none`/expirado → 401 |
| W1-04 | Login admin con Supabase SSR y cookies HttpOnly | W1-03 | Login/logout; `/admin/me` |
| W1-05 | Onboarding de tenant + seed ropa/joyería | W1-01, W1-03 | Crear tenant sin redeploy; slugs reservados |
| W1-06 | 12 vectores cross-tenant + tests de integración | W1-01 a W1-05 | Todos pasan; documentados en `03-tenancy.md` |
| W1-07 | Platform admin + support access auditado | W1-03 | Acceso con razón y expiración; evento |
| W1-08 | `auth_events` + alertas de mismatch | W1-03 | Evento en mismatch; alerta configurada |

## Wave 2 — Catálogo y media

| ID | Tarea | Depende | Aceptación / evidencia |
|---|---|---|---|
| W2-01 | Migraciones de catálogo, media e inventario + RLS | W1-01 | RLS A/B en todas las tablas |
| W2-02 | CRUD productos/opciones/variantes | W2-01 | Slug/SKU únicos; validaciones de precio |
| W2-03 | Upload de media: URL firmada, worker, variantes, EXIF | W2-01 | Imagen válida → AVIF/WebP; EICAR/PDF rechazado |
| W2-04 | Inventario: niveles, reservas, movimientos | W2-01 | `available`/`reserved` nunca negativos |
| W2-05 | Búsqueda FTS + facets + cursor | W2-02 | Español/tildes/typos; p95 < 300 ms |
| W2-06 | Storefront: listado, detalle, colección | W2-02, W2-03 | Dos tenants con catálogo; JSON-LD |
| W2-07 | Admin de catálogo | W2-02, W2-03 | Crear producto completo desde UI |
| W2-08 | Tests de concurrencia de inventario | W2-04 | 100 reservas simultáneas sin negativo |
| W2-09 | Seed de catálogo piloto | W2-07 | Productos de ropa y joyería cargados |

## Wave 3 — Contenido y storefront

| ID | Tarea | Depende | Aceptación / evidencia |
|---|---|---|---|
| W3-01 | Migraciones `pages`, `page_versions`, `themes`, `redirects`, `outbox_events` + RLS | W1-01 | RLS A/B; versión publicada inmutable |
| W3-02 | Block registry Pydantic + tipos TS + componentes base | W3-01 | Schemas cerrados; sin HTML; tests de contrato |
| W3-03 | API de draft/autosave con control optimista | W3-01 | `409 VERSION_CONFLICT` en concurrencia |
| W3-04 | Publish/rollback + outbox + purge | W3-03 | Publish atómico; rollback sirve versión anterior |
| W3-05 | Builder UI (drag/drop, props, duplicar, eliminar) | W3-02, W3-03 | Editar y guardar sin recargar |
| W3-06 | Preview firmado | W3-04 | Token expirado → 401; noindex |
| W3-07 | Temas/tokens + presets ropa/joyería | W3-01 | Dos temas distintos sobre el mismo motor |
| W3-08 | Storefront rendering + SEO + a11y | W3-02, W3-04 | Home publicada; axe crítico 0; LCP < 2.5 s |
| W3-09 | Integrar export de v0 | W3-02, W3-07 | Componentes y tokens alineados al prototipo |
| W3-10 | Purga de caché end-to-end | W3-04 | Publicar cambia el storefront en < 60 s |

## Wave 4 — Carrito, checkout, pagos y órdenes

| ID | Tarea | Depende | Aceptación / evidencia |
|---|---|---|---|
| W4-01 | Migraciones de carrito, órdenes, envío, idempotencia + RLS | W2-04 | RLS A/B; snapshots de orden |
| W4-02 | API de carrito + cookie/token | W4-01 | Agregar/editar/eliminar; stock validado |
| W4-03 | Checkout + reserva + idempotencia | W4-01, W4-02 | Reintento no duplica; TTL libera stock |
| W4-04 | Wompi adapter + Web Checkout | W0-08, W4-03 | Redirect sandbox; monto correcto |
| W4-05 | Webhook Wompi + máquina de estados | W4-04 | Firma/replay/monto; pago solo por webhook |
| W4-06 | Órdenes admin + emails + fulfillment | W4-05 | Orden pagada visible; email enviado |
| W4-07 | Refunds + conciliación | W4-05 | Refund idempotente; reporte diario |
| W4-08 | E2E de compra sandbox con dos tenants | W4-06 | Compra completa; orden confirmada |
| W4-09 | Load test de checkout concurrente | W4-03 | 100 compras simultáneas sin overselling |
| W4-10 | Página de confirmación + `public_token` | W4-05 | Estado consultable sin exponer IDs secuenciales |

## Wave 5 — Billing y facturas

| ID | Tarea | Depende | Aceptación / evidencia |
|---|---|---|---|
| W5-01 | Migraciones de suscripción y facturas de plataforma + RLS | W1-01 | RLS A/B; plan/tenant |
| W5-02 | Stripe Billing + webhooks + entitlements | W0-08, W5-01 | Trial 14 días; `past_due`/`canceled` |
| W5-03 | Admin billing + Customer Portal | W5-02 | Suscribir/cancelar; facturas visibles |
| W5-04 | DIAN adapter + job de emisión | W4-05 | Factura emitida en sandbox; reintentos |
| W5-05 | PDF/XML privado + URL firmada | W5-04 | Descarga con TTL; sin acceso público |
| W5-06 | Nota crédito o handoff | W5-04, W4-07 | Refund post-factura resuelto |
| W5-07 | Dunning y emails de cobro | W5-02 | Cobro fallido → email; gracia |
| W5-08 | Gate de features por plan | W5-02 | Límite excedido → `402 PLAN_LIMIT_REACHED` |

## Wave 6 — Gobernanza y platform admin

| ID | Tarea | Depende | Aceptación / evidencia |
|---|---|---|---|
| W6-01 | `decide()` + políticas del MVP | W1-03 | Tests table-driven; `DENY` por defecto |
| W6-02 | `decision_logs` + hash chain + verificador | W6-01 | Tamper detectado; job diario |
| W6-03 | `approval_tasks` + UI de handoff | W6-02 | Reembolso alto → handoff; expiración |
| W6-04 | Platform admin: tenants, planes, auditoría | W1-07 | Crear/suspender tenant; auditoría |
| W6-05 | Cobertura de endpoints sensibles | W6-01 | Test falla si falta `decide()` |
| W6-06 | Alertas de gobernanza | W6-02 | DENY/HANDOFF anómalo; cadena rota |

## Wave 7 — Hardening

| ID | Tarea | Depende | Aceptación / evidencia |
|---|---|---|---|
| W7-01 | Performance: LCP/CLS/INP en las dos homes | W3-08 | p75 móvil < 2.5 s; CLS < 0.1 |
| W7-02 | Load test: búsqueda, publish, checkout | W4-09 | p95 API < 300 ms; sin caídas |
| W7-03 | Pen-test de 12 vectores + ZAP baseline | W1-06 | 0 críticos; remediaciones cerradas |
| W7-04 | Auditoría a11y WCAG 2.2 AA | W3-08 | 0 críticas en axe; manual checklist |
| W7-05 | Restore drill + backups | W0-02 | Restauración dentro del RTO |
| W7-06 | Runbooks: incidente, webhook, restore, rotación | W7-05 | Runbooks en `docs/operations/` |
| W7-07 | SEO audit: sitemap, canonical, JSON-LD | W3-08 | Sin errores en Search Console |
| W7-08 | Dependency/secret scan | W0-01 | 0 secretos; vulnerabilidades altas cerradas |

## Wave 8 — Piloto

| ID | Tarea | Depende | Aceptación / evidencia |
|---|---|---|---|
| W8-01 | Contenido final ropa y joyería | W3-09 | Homes y páginas aprobadas |
| W8-02 | Carga de catálogo y media real | W2-09 | Productos, variantes y fotos completos |
| W8-03 | UAT con stakeholders | W8-01, W8-02 | Checklist firmado; bugs críticos cerrados |
| W8-04 | Go-live: DNS, TLS, Wompi/Stripe prod | W8-03 | `*.growup.com` y pagos verificados |
| W8-05 | Monitoreo y soporte de lanzamiento | W7-06 | Guardia activa; alertas verdes |
| W8-06 | Retrospectiva y backlog post-MVP | W8-05 | Decisiones de fase 2 documentadas |

## Backlog diferido (D-05)

Returns/RMA, bespoke, promociones, envío blindado, IA/WhatsApp, L402, multi-moneda, dominios custom, comisión por venta/marketplace, reviews, wishlist, multi-idioma, app móvil.

## Riesgos y mitigaciones

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| Export de v0 tarde | Media | Alto | Avanzar con tokens/registry; integrar al final de Wave 3 |
| Wompi con API distinta | Media | Alto | Spike en Wave 0; adapter aislado |
| Stripe no apto para la entidad | Media | Medio | Respaldo MercadoPago preapproval |
| IVA del envío sin definir | Alta | Medio | Confirmar con contador antes de Wave 4 |
| Conexiones Supabase | Media | Alto | Pooler, límites, load test |
| Capacidad del equipo | Media | Alto | Recortar Wave 6/7; no recortar seguridad |
| Contenido del piloto | Media | Medio | Responsable asignado en Wave 3 |

## Hitos de aceptación

1. **M1 (fin Wave 1):** dos tenants resuelven por host, login admin y 12 vectores en verde.
2. **M2 (fin Wave 2):** catálogo completo con media, inventario y búsqueda.
3. **M3 (fin Wave 3):** dos homes publicadas con temas distintos y LCP < 2.5 s.
4. **M4 (fin Wave 4):** compra sandbox end-to-end sin overselling.
5. **M5 (fin Wave 5):** trial, suscripción y factura DIAN sandbox.
6. **M6 (fin Wave 7):** seguridad, restore y NFRs verificados.
7. **M7 (fin Wave 8):** piloto en producción.

## Enlaces

- [Requirements](requirements.md)
- [Design](design.md)
- [Decisiones](../../../docs/decisiones-pendientes.md)
- [ADRs](../../../docs/adr/README.md)
