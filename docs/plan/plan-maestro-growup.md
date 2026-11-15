# Plan Maestro — Growup (SaaS multi-tenant de comercio)

> Fecha: 2026-11-10 · Autor: auditoría + plan · Basado en `docs/decisiones-pendientes((1)).md`, ADRs 0001-0011 y auditoría 2026-11-10 · Objetivo: llevar Growup desde "núcleo sólido + catálogo" hasta **piloto ropa+joyería en Q1 2027** con calidad operable.

## Documentos de este plan

| Archivo | Contenido |
|---|---|
| `decisiones-proveedores-growup.md` | Cierre de todas las decisiones/propuestas abiertas con proveedor elegido, justificación de eficiencia, gates y responsables |
| `guias-pendientes-growup.md` | Guías paso a paso (comandos, criterios de listo) de cada unidad de trabajo pendiente |
| `plan-maestro-growup.md` | Este documento: fases, tareas con IDs, DoD, dependencias, cronograma y métricas |

## 0. Estado real contra el que planeamos (de la auditoría)

**Ya existe y es sólido:** RLS forzado en 22/23 tablas (95 asserts pgTAP), JWT/JWKS, RBAC desde membresía, dinero en `bigint` COP, catálogo completo, inventario atómico sin oversell, media a R2 con worker ARQ, gobernanza con hash chain, contratos OpenAPI→TS, CI verde, storefront/admin bases.

**No existe (foto del 2026-11-10):** builder/bloques/contenido/publish (0%), carrito/checkout/órdenes/pagos (0%), billing/Stripe/suspensión (0%), DIAN (0%), emails (0%), infraestructura desplegada (no Dockerfile, no staging, no runbooks), observabilidad (sin métricas/traces exportables), tests frontend (0), suspensión de tenant por impago (rota).

> **Reconciliación verificada (2026-11-15 — WP-00 / WP-01, ver `docs/estado/verificacion-2026-11-15.md`):**
> Entre el 2026-11-10 y el 2026-11-15 se implementaron en código y pruebas unitarias (`295 passed` en `pytest`, `pnpm lint/typecheck/contracts:check/build` verdes):
> - **Contenido y Builder (`ADR-0005`):** 16 bloques tipados (`blocks.py`), 7 plantillas de 1 clic (`templates.py`), publish atómico, preview HMAC y editor visual de 3 columnas en `apps/admin/app/(dashboard)/builder/`.
> - **Comercio y Super Consola:** dominio `commerce` (carrito, checkout, órdenes y webhook Wompi), `Dockerfile` + `Dockerfile.worker`, Super Consola v1 (`/platform/overview`, `/platform/tenants`), editor de planes (`/planes`) y sugerencias de reorden (`/suggestions`).
> - **Sistema Visual Nova (`ADR-0020`):** dirección visual técnica total (`Unbounded` + `Geist` + `Geist Mono`) y resolución dinámica de tema por tenant (`ThemeTokensV1`).
> - **Siguientes bloqueos reales:** ratificación legal/contable (`D-09..D-16`, `D-06`), cuentas sandbox externas (`D-03` Factus, `D-15` Resend, Wompi/Stripe en staging) y suite de integración con `GROWUP_TEST_DATABASE_URL`.

**Decisiones congeladas que bloquean olas enteras:** ADR-0005 (contenido) en Propuesta; D-09 a D-16 en Propuesta; D-03 sin proveedor DIAN; derivados de D-01 (precio/límites), D-06 (IVA envío), D-07 (DNS/TLS), D-08 (fecha/responsable), D-02 (cuenta Stripe/Wompi).

**Regla de oro del plan:** ninguna tarea de producto (Wave 4+) empieza antes de cerrar las puertas legales y de infraestructura de Fase 0–2. Un piloto real exige: despliegue + cobro + suspensión + legal + emails + soporte.

---

## 1. Principios de ejecución

1. **Desplegar antes que construir.** Nada se acumula en local; cada fase termina con algo corriendo en staging (Vercel preview + Fly staging + Supabase staging).
2. **Fail-closed y evidencia.** Cada control de seguridad/legal llega con su test (pgTAP/integración/E2E). Sin evidencia, no se marca hecho.
3. **Cero custodia de fondos.** Wompi (checkout) + Stripe Billing (suscripción), merchant of record = tenant/plataforma según D-02. Nunca tocar PAN; hosted/redirect.
4. **El dueño de la decisión es quien firma.** Producto/legal ratifican textos y precios; ingeniería implementa y verifica. Este plan propone valores por defecto; cada decisión muestra su gate de ratificación en `decisiones-proveedores-growup.md`.
5. **MVP-recortado, no MVP-recortado-en-silencio.** Toda omisión frente a "tipo Shopify" queda registrada en §10 (fuera de alcance explícito).
6. **Orden de merge:** migración expand → código compatible → deploy → migración contract → verificación. Nunca DROP destructivo en el mismo deploy.
7. **SOC 2-ready, no certificado** (D-18): evidence folder `docs/compliance/` desde el día 1.

---

## 2. Fases y objetivos

```text
F0 Decisiones y limpieza (1-2 sem)     → todas las propuestas cerradas o con fecha+gate
F1 Infraestructura y despliegue (2-3)  → staging vivo, CI/CD, observabilidad, backups
F2 Hardening backend/DB (1-2)          → P0 de la auditoría corregidos y testeados
F3 Contenido y builder (3-4)           → Wave 1+3: pages/blocks/publish/ISR (ADR-0005)
F4 Comercio (4-6)                      → Wave 4: cart→checkout→órdenes→pagos→DIAN→billing
F5 Legal, seguridad operativa y SOC2 (2-3, paralela) → DPA/DSR/política/breach/soporte
F6 Piloto ropa+joyería (3-4)           → Wave 8: dados, QA, criterios de aceptación, go-live
F7 Post-piloto                         → retroalimentación, métricas, decisión de fase 2
```

Estimación total: **~16–22 semanas** para piloto controlado (Q1 2027 con margen). Dos personas + apoyo de abogado/contador (por horas).

---

## 3. Fase 0 — Decisiones y limpieza (Semana 1–2)

**Objetivo:** ninguna tarea posterior queda bloqueada por una decisión abierta; repositorio limpio y docs veraces.

| ID | Tarea | DoD | Depende |
|---|---|---|---|
| F0-01 | Ratificar en acta todas las decisiones de `decisiones-proveedores-growup.md` (abogado/contador/equipo): D-03 proveedor, D-06 IVA envío, D-07 DNS/TLS, D-09, D-10, D-11, D-12, D-13, D-14, D-15, D-16, D-01 precio/límites, D-08 fecha/responsable | Acta firmada en `docs/decisiones-pendientes.md` (edición explícita, nada en silencio); estados CERRADA | — |
| F0-02 | Cerrar ADR-0005 (pasar a **Aceptada**): ratificar lista de bloques MVP (16 bloques del prompt v0 + `marqee` decidir), schema de tokens, publish atómico con outbox+purge, preview con token firmado, retención drafts | ADR-0005 actualizado a Aceptada + commit | F0-01 |
| F0-03 | Crear ADR-0012 "Proveedores y región": sa-east-1 (Supabase+Fly+Upstash), Cloudflare(DNS/WAF), Resend(email), Factus(DIAN), Wompi(checkout), Stripe(subscripciones), Sentry+Grafana Cloud (obs) | ADR aceptada; `.kiro/steering` y README alineados | F0-01 |
| F0-04 | Borrar zombies: `apps/frontend/`, `packages/brand/`; mover `frontend/` legacy a `docs/prototypes/legacy-html/` o borrarla; decidir y dejar unificado | `pnpm install --frozen-lockfile` verde; lockfile sin fantasmas; README actualizado | — |
| F0-05 | Documentación veraz: README estado real (Waves), borrar/unificar `decisiones-pendientes (1).md` → fusionar en `decisiones-pendientes.md` con estados correctos; eliminar referencias a `.kiro/` o crear `.kiro/steering/` mínimo (6 archivos) — decisión: **eliminar referencias y archivar steering en `docs/steering/`** | `grep -ri kiro` solo en docs archivadas; README refleja la realidad | — |
| F0-06 | Renombrar/unificar `formatPrice`/`formatDate` en `packages/config` (o dejar duplicado con TODO — decidir: **crear `packages/config` compartido**) | `apps/*` importan de `@growup/config` | F0-04 |
| F0-07 | Fijar fecha y responsable del piloto; criterio de aceptación escrito (§8) | D-08 cerrado en el registro | F0-01 |
| F0-08 | Configurar cuentas proveedoras sandbox: Wompi (checkout), Stripe (billing, confirmar entidad legal CO/US), Factus (DIAN sandbox), Resend, Supabase prod/dev, Fly, Vercel, Cloudflare, R2, Upstash, Sentry | Cada cuenta/entorno existe; credenciales en vault/`.env` local + GitHub Environments; **cero secretos en repo** | — |
| F0-09 | Plan de cuentas/entornos: local / staging / prod con proyectos, buckets, claves y presupuestos separados; quién tiene acceso (2 personas + principio mínimo privilegio) | `docs/operations/environments.md` creado | F0-08 |

**Criterio de salida de F0:** git limpio de fantasmas; docs veraces; todas las propuestas con decisión o fecha+gate; cuentas sandbox creadas; ADR-0005 aceptada.

---

## 4. Fase 1 — Infraestructura y despliegue (Semana 2–4)

**Objetivo:** staging vivo y pipeline de producción definido antes de escribir features.

| ID | Tarea | DoD | Depende |
|---|---|---|---|
| F1-01 | Dockerfile API + .dockerignore (uv, python 3.12, usuario no-root, `uv.lock`, healthcheck `/healthz`); mismo para worker (`arq app.workers.media.WorkerSettings`); imagen < 200 MB | Build local; Trivy sin críticos; usuario no-root | F0-08 |
| F1-02 | `fly.toml` staging + `fly.toml.production`: región `gru`, 1 máquina staging, 2 prod, sin ingress en worker, health checks, `auto_stop_machines` staging, secrets vía `fly secrets` | `fly deploy` staging OK; `/readyz` 200 en staging | F1-01 |
| F1-03 | Proyectos Vercel: `growup-storefront` y `growup-admin`, wildcard `*.growup.com` (Vercel wildcard cert) y `admin.growup.com`; preview protection en proyectos; `NEXT_PUBLIC_*` y SSR env por ambiente | Storefront staging sirve en `staging.growup.com` o subdominio preview | F0-08 |
| F1-04 | Supabase prod (sa-east-1): proyecto, roles `app_rw`/`app_worker` con login separado (no superuser para API), pooler transaccional habilitado para API, direct connection para migraciones, PITR, backups diarios a R2 | `GROWUP_DATABASE_URL` (pooler) y `GROWUP_MIGRATION_URL` (direct) configuradas; restore test documentado | F0-08 |
| F1-05 | DNS Cloudflare: zona `growup.com`, CNAMEs a Vercel/Fly, proxy naranja con WAF + rate limiting (5 reglas: auth, admin, api global, storefront burst, login), página de "tenant suspendido" opcional | DNS propaga; WAF bloquea patrón de prueba | F1-03 |
| F1-06 | Upstash Redis (sa-east-1): bases separadas `cache`, `queue`, `ratelimit` con TLS y ACLs | Conexión desde Fly staging OK | F0-08 |
| F1-07 | CI/CD expandido (`.github/workflows/ci.yml`): jobs `api` (+`pip-audit`), `db` (+`supabase db diff --check` anti-drift en staging), `contracts`, `frontend` (+`pnpm audit --prod`), `docker` (build + Trivy), `e2e` (Playwright contra staging, solo main), `deploy-staging` auto en main (Vercel vía Git, Fly vía `flyctl deploy`), `deploy-production` manual con checklist (runbooks, backup verificado, ventana, on-call) | Pipeline completo verde en PR y main; staging se actualiza solo | F1-01..F1-06, F0-08 |
| F1-08 | Branch protection: PR obligatorio, checks verdes obligatorios (api, db, contracts, frontend), sin force-push, CODEOWNERS (personas A y B) | Configurado en GitHub; probado con PR de prueba | F0-08 |
| F1-09 | Plantillas: PR template (evidencia, migraciones expand/contract, secretos check), ISSUE templates, `docs/operations/environments.md`, `docs/operations/deploy.md` (orden: migraciones → API → frontend; rollback: Vercel instant, Fly release anterior) | Repo contiene los 4 archivos; README enlaza | F1-07 |
| F1-10 | Observabilidad día 1: Sentry (storefront, admin, API, worker) con `send_default_pii=False`, releases, `trace_id`; OpenTelemetry instrumentación FastAPI + Next.js (`@vercel/otel`); export OTLP a Grafana Cloud (free tier, región us-east… usar `grafanacloud-free`); dashboards: 5xx por ruta, p95, pool DB, cola ARQ, cache hit, login failures; alertas: 5xx>2% 5min, `readyz` fail, `decision_logs` tamper | Traces storefront→API→worker visibles; alerta de prueba dispara | F1-02..F1-06 |
| F1-11 | `/readyz` completo: DB `SELECT 1`, Redis ping, JWKS alcanzable (HEAD con timeout), R2 head bucket (opcional, no bloquea); liveness `/healthz` siempre 200 | Tests + staging verificado | F1-06 |
| F1-12 | Costos y presupuestos: alertas de billing en Vercel, Fly, Supabase, Upstash, Cloudflare, R2 (30% sobre baseline); documento `docs/operations/cost.md` con baseline mensual estimado (< USD 150 staging+prod inicial) | Alertas configuradas; documento creado | F0-09 |

**Criterio de salida de F1:** storefront y admin responden en staging desde el monorepo vía pipeline; WAF activo; observabilidad con trazas; backups verificados con una restauración de prueba en staging; deploy rollback documentado y ensayado al menos una vez.

---

## 5. Fase 2 — Hardening backend y base de datos (Semana 3–5, paralela a F1)

**Objetivo:** cerrar los hallazgos P0/P1 de la auditoría con tests.

| ID | Tarea | DoD | Depende |
|---|---|---|---|
| F2-01 | Suspensión de tenant efectiva: `resolve_tenant` filtra `status='active'` (y `trialing` según entitlement); `TenantResolver` chequea `status`; invalidación de caché por evento (suspend/activate) vía Redis pub/sub o TTL corto (60s) para estados no activos | Test integración: tenant suspended → 404 en storefront y 403 en admin; pgTAP actualizado | F1-04 |
| F2-02 | Onboarding entitlement: compuerta `pending_legal` (ver F5-02) y `past_due` con período de gracia 3 días → luego `suspended`; transición atómica en BD + auditada | pgTAP + integración de transiciones de estado | F5-02, F4-06 |
| F2-03 | DB fix: FK compuesta `addresses(tenant_id, customer_id) → customers(tenant_id, id)`; añadir `unique (tenant_id, id)` en customers; grants a nivel columna sobre `app.tenants` (`update (name, legal_name)` para app_rw; plan/status solo vía SECURITY DEFINER) | Migración expand; pgTAP que prueba intento de update directo de `plan_id` → 42501; FK funciona | — |
| F2-04 | JWKS: `JWKSCache.get` con singleflight (asyncio lock por kid) + negative caching (60s) + cooldown global tras refresh (300s) + máximo 1 refresh concurrente | Test unit: 100 requests con kid desconocido → 1 fetch remoto; métricas expuestas | — |
| F2-05 | Rate limiting: middleware/librería en API (slowapi o Redis token bucket vía Upstash): `/v1/storefront/*` 300 req/min/IP, `/v1/admin/*` 120 req/min/token, login/magic-link 10 req/min/IP+email; 429 con `Retry-After`; bypass solo desde healthchecks internos | Tests de límites; 429 verificado en staging; WAF complementa | F1-06 |
| F2-06 | Body limit: rechazar `Transfer-Encoding: chunked` sin `Content-Length` cuando `GROWUP_ENV=production` (o limitar en el edge y documentarlo); validar `X-Request-ID` (≤64 chars, charset `[A-Za-z0-9-]`), truncar/reemplazar inválidos | Tests de middleware; header sanitizado en respuesta y logs | — |
| F2-07 | Errores 422 Pydantic dentro del envelope `AppError` (`VALIDATION_ERROR` con detalles saneados); OpenAPI `components` actualizado; contrato regenerado | Test de contrato; frontend consume un solo formato de error | — |
| F2-08 | Unificar contexto admin: media e identity routers migran a `get_tenant_context`; `request.state.tenant_id` siempre seteado; eliminar chequeos manuales `_tenant_id` duplicados | Tests; logs de media/identity con tenant_id | — |
| F2-09 | `/docs` y OpenAPI: `docs_url=None` en producción (gate `GROWUP_ENV`); health no expone `environment`; `X-Request-ID` no se refleja sin validar (F2-06) | Deploy staging/prod verificado; checklist F1-02 lo incluye | F1-02 |
| F2-10 | `Cache-Control: no-store` en todas las respuestas `/v1/admin/*` y `/v1/platform/*`; `private, no-cache` en storefront bootstrap sensible | Test de headers | — |
| F2-11 | Wiring de inventario: exponer `InventoryService` por HTTP admin (`GET /v1/admin/inventory`, `POST .../reserve|confirm|release` solo interno/worker) o marcarlo como interno-only explícitamente; registrar en runtime | OpenAPI actualizado; test de rutas | — |
| F2-12 | SQL dinámico: mapa fijo columna→placeholder en `update_product`/`update_variant` y reservations; eliminar f-strings residuales | Review de código; grep sin patrones | — |
| F2-13 | Logging/PII: `trace_id` reinyectado en respuesta `traceparent`; cron/ARQ job `verify_decision_chain` diario con métrica y alerta; `inventory` balance check como job semanal | Job registrado; alerta de prueba | F1-10 |
| F2-14 | Índices y constraints: `memberships (user_id)`, `(tenant_id, status)`; `media_variants` unique `(tenant_id, r2_key)` y unique `(tenant_id, id)`; GIN tenant-scoped si FTS lo pide; `decision_logs` documentar dependencia `pg_trigger_depth` o refactor a trigger dedicado | Migración + pgTAP; query plans sanos | — |
| F2-15 | Tenant cache: TTL 60s; invalidación en suspend/activate/publish; inner cache con Redis para compartir entre réplicas (`cache` base F1-06) | Test con 2 workers: invalidación visible < 2s | F1-06 |

**Criterio de salida de F2:** todos los hallazgos "Altos" de la auditoría en verde con tests; staging endurecido; pentest interno ligero (checklist OWASP ASVS L1) documentado.

---

## 6. Fase 3 — Contenido y builder (Semana 5–9) — ADR-0005

**Objetivo:** storefront dirigido por bloques publicados; admin con editor. Es la ola más grande.

| ID | Tarea | DoD | Depende |
|---|---|---|---|
| F3-01 | Migración contenido: `pages`, `page_versions` (JSONB `layout` con array de bloques, `version` monotónica), `themes` (tokens JSONB: color, fonts, radii, spacing), `tenant_settings` ya existe, `legal_documents`/`legal_acceptances` (F5-02 las crea) | pgTAP: RLS A/B, FK compuestas, unpublish atómico | F2-03 |
| F3-02 | Schemas Pydantic v2 discriminated unions para los 16 bloques MVP: header, footer, hero, editorial_split, product_grid, product_carousel, collection_grid, image_banner, rich_text (subconjunto Markdown saneado server-side), quote, gallery, video_embed (allowlist YouTube/Vimeo), faq, newsletter, spacer, columns. Límites de items, `alt` obligatorio en imágenes, `rich_text` sin HTML | `block-review` skill ejecutada; tests de schema (válido/inválido/XSS payloads) | F0-02 |
| F3-03 | API contenido: `GET /v1/storefront/pages/{slug}` (publicada, cacheable), `POST /v1/admin/pages`, `PUT .../draft`, `POST .../publish` (atómico: nueva `page_versions` + `pages.published_version_id` swap + outbox `content.published`), `GET .../preview?token=` (token firmado HMAC, TTL 15 min), `POST .../unpublish` | OpenAPI→contracts; tests integración; publish atómico verificado con transacción abortada | F3-01, F3-02 |
| F3-04 | Outbox + purga: tabla `outbox_events`; worker ARQ `publish_purge` llama Vercel deploy hook/`revalidateTag`; storefront usa ISR con `revalidate` + tags por tenant-page; purge < 5s | E2E: publish visible < 10s; rollback de publish en 1 comando | F3-03, F1-03 |
| F3-05 | Storefront `BlockRenderer` + componentes `components/blocks/*` (RSC): sin estado cliente salvo newsletter/faq-accordion; fallback seguro para bloque desconocido (oculto + log, nunca crash); `next/image`, alt obligatorio; LCP móvil < 2.5s (Lighthouse en CI) | `block-review` en verde; Playwright smoke por bloque | F3-03 |
| F3-06 | Temas: `tenant.themes.tokens` aplicado en SSR (`data-theme` + CSS vars inyectadas en `layout`); fuentes por tema cargadas dinámicamente (`next/font` subset) — ropa/joyería como temas default sembrados | Tokens desde API; cambiar token en admin → visible tras publish | F3-03 |
| F3-07 | Admin builder MVP: ruta `/(dashboard)/builder`; editor de bloques con drag-and-drop (HTML5 DnD, sin librerías nuevas pesadas — o `@dnd-kit/core`, permitido pues no es UI kit), autosave (debounce 2s), indicador "guardado/cambios sin publicar", concurrencia por `If-Match: version` (409 en conflicto), preview en iframe con token, publish button con confirmación | E2E Playwright del ciclo editar→publicar→ver en storefront; conflicto de versión probado | F3-03..F3-06 |

> **Estado F3-07 (2026-11-13, rama `feat/builder-visual`):** implementado — árbol de bloques con HTML5 DnD + ↑/↓ + duplicar, 16 formularios de props cerrados (matriz de bloques validada contra Pydantic server-side), autosave 2 s con debounce, indicador de estado (sin borrador / cambios sin guardar / guardando / sincronizado / conflicto), `expected_version` opcional en `PageDraftRequest` (409 `VERSION_CONFLICT` con `{expected, latest}` tanto en publish como al guardar), preview en iframe same-window con token HMAC y recarga post-autosave, `CSP frame-ancestors` + `no-store` en `/preview` del storefront. Verificación: `pytest` (287 unit + 29 integración + 10 aislamiento), `ruff`/`mypy`, `contracts:check`, build Next.js admin y storefront; flujo preview verificado contra tenant demo seedado en DB desechable (API 200 + HTML con hero/grid + token HMAC). Pendiente: E2E Playwright automatizado del ciclo completo (requiere OAuth de admin en CI); el conflicto de versión está probado en tests de servicio (`test_create_draft_*`). |
| F3-08 | Páginas seed ropa+joyería: home, colección, PDP existentes migradas a bloques; footer con política de devolución (F5-04) y contacto | `ropa.growup.com` y `joyeria.growup.com` renderizan desde bloques publicados | F3-05, F5-04 |
| F3-09 | SEO: `sitemap.ts` por tenant, `robots.txt` por host, metadata dinámica desde tenant/página, JSON-LD `Product` en PDP, canonical por tenant | Lighthouse SEO ≥ 90; sitemap válido | F3-05 |
| F3-10 | Analítica mínima propia: eventos `page_view`, `add_to_cart`, `begin_checkout`, `purchase` a `collector` propio (tabla `analytics_events`, agregado diario) — sin cookies de terceros; dashboard admin básico | Eventos visibles en admin; decisión de proveedor diferida | F4-01 |

**Criterio de salida de F3:** piloto renderizable 100% desde el builder; admin publica con purge < 10s; rollback de publicación ensayado.

---

## 7. Fase 4 — Comercio end-to-end (Semana 8–14)

**Objetivo:** carrito → checkout → orden → pago → factura → email → suscripción de la plataforma.

| ID | Tarea | DoD | Depende |
|---|---|---|---|
| F4-01 | DDL comercio: `carts`, `cart_items`, `orders`, `order_items` (snapshot `subtotal_cents`, `tax_cents`, `shipping_cents`, `total_cents`, tasa), `shipments`/`zones` (2 zonas MVP: Bogotá / resto del país), `payments`, `webhook_events` (idempotencia `provider+event_id`), `tenant_payment_accounts` (Wompi por tenant), `platform_subscriptions`, `tenant_usage` | pgTAP; RLS; FK compuestas; migración expand | F2 |
| F4-02 | Carrito: `POST /v1/storefront/cart` (guest, cookie httpOnly firmada, TTL 30 días), add/update/remove/get; merge guest→magic-link al reclamar historial; precios siempre re-leídos de BD (snapshot solo en order) | Tests; carrito sobrevive refresh; sin drift de precio | F4-01 |
| F4-03 | Checkout: draft order desde carrito → validación stock (reserva 15 min) → redirect a **Wompi Checkout hosted** (redirect puro; cero JS de Wompi en nuestro origen todavía) con `reference=order_id`, monto, firma integrity | E2E sandbox: redirect OK; orden `pending` creada | F0-08, F4-01, F4-02 |
| F4-04 | Webhooks Wompi: verificación de firma (events secret), idempotencia por `event_id`, transiciones `pending→paid/failed/expired`, confirmación de reserva de inventario, liberación en expired/failed, email de confirmación (F4-08), creación de factura (F4-07); worker ARQ `process_wompi_webhook` con reintentos y DLQ | `payment-webhook-review` skill; test de duplicado/firma inválida/orden de eventos; E2E sandbox completo | F4-03 |
| F4-05 | Órdenes admin: lista, detalle, transición de fulfillment (`paid→preparing→shipped→delivered`), cancelación con reembolso vía API Wompi (manual-assist con confirmación), notas internas; vistas tenant-scoped | E2E admin; RBAC (`orders:read`, `orders:fulfill`); auditoría de cada transición | F4-04 |
| F4-06 | Billing plataforma (Stripe Billing): productos Starter/Pro + trial 14 días; checkout de suscripción hosted para el owner del tenant; webhook `invoice.payment_failed` → `past_due` (gracia 3 días) → `suspended` vía F2-01; `customer.subscription.deleted` → `suspended`; portal de facturas Stripe embebido en admin (`billing:manage`) | Test con Stripe CLI (`listen`, `trigger`); ciclo trial→past_due→suspended→reactivated | F0-08, F2-01 |
| F4-07 | DIAN (Factus): adaptador `FactusClient` (auth OAuth2, emisión factura cf/01, nota crédito nc/02); orden `paid` → ARQ `emit_invoice` → guardar `electronic_ref` + PDF URL; reintentos con backoff; fallo → tarea `approval_tasks` manual (HANDOFF); nota crédito automática en refund si factura emitida | Sandbox Factus: factura emitida y validada; nota crédito en refund; fallback HANDOFF probado | F0-08, F4-04, F0-03 |
| F4-08 | Emails transaccionales (Resend, subdominio por tenant `mail.{slug}.growup.com`, DKIM/SPF/DMARC auto-verificados vía API; fallback dominio compartido): confirmación de orden, orden enviada, magic link (Supabase SMTP vía Resend), factura disponible, dunning de suscripción; registro en `email_events` (sin cuerpo en logs); supresión por rebote/queja | Test envío real en staging a mailbox de prueba; rebote simulado; SPF/DKIM/DMARC `pass` | F0-08, F4-04 |
| F4-09 | DSR tooling (D-10): rol `platform_dsr` con `legal:dsr`; runbook ejecutable `docs/operations/dsr-runbook.md` (verificar identidad → localizar por email/customer → clasificar por matriz → anonimizar campos (nombre, direcciones, teléfono) conservando órdenes/facturas fiscales; `decision_logs` sin tocar; respuesta al titular < 15 días hábiles); registro `dsr_requests` append-only | DSR simulado en staging con datos sintéticos; pgTAP del rol; runbook ensayado | F5-01..F5-03 |
| F4-10 | Fraude (D-14): 3DS obligatorio para tarjetas cuando Wompi lo permita; flags de riesgo en orden (IP/país ≠ envío, velocity por email); ToS asigna disputa al comerciante; campos `dispute_status`, `dispute_evidence` en `orders`; plantilla de evidencia en admin | Docs ToS; test de flujo de disputa manual | F4-03, F4-05 |
| F4-11 | Conciliación (PAY-04 lite): reporte diario admin: órdenes pagadas vs webhooks recibidos vs Wompi settlement (CSV manual en MVP; API en fase 2); alerta de discrepancias | Job diario; alerta staging | F4-04 |
| F4-12 | Rechazo de PII en logs/analytics: scan CI (grep patterns) para PAN/CVV; `payment_method` solo tipo y últimos 4 si Wompi lo expone; ningún campo de tarjeta en BD (verificado en migración) | CI gate nuevo `no-pan`; revisión manual | F4-03 |

**Criterio de salida de F4:** compra completa E2E en sandbox (storefront → Wompi → webhook → orden → factura Factus → email), ciclo de suscripción de plataforma con suspensión por impago, en staging.

---

## 8. Fase 5 — Legal, cumplimiento y operación SOC 2-ready (paralelo desde F0)

**Objetivo:** capacidad de firmar DPAs y atender obligaciones con clientes reales.

| ID | Tarea | DoD | Depende |
|---|---|---|---|
| F5-01 | Abogado colombiano: contratar (2-4h) por paquete — revisar DPA, política de privacidad, ToS, política de devoluciones, contrato de suscripción, cláusula "no facilitador" (D-17), textos de aceptación clickwrap | Textos firmados/aprobados; factura archivada en `docs/legal/` | F0-01 |
| F5-02 | `legal_acceptances` + `legal_documents`: tablas inmutables (append-only, sin update/delete), tipo+versión+hash, actor, tenant, IP/UA como hash con sal (no se promete anonimización); estado `pending_legal` bloquea publicación y checkout; gate en publish (F3-03) y billing (F4-06); aceptación solo por owner en primer acceso post-login | pgTAP; test: tenant sin aceptación → publish 403 y checkout 403; aceptación duplicada no rompe | F1-04 |
| F5-03 | Matriz de retención (aprobada por abogado/contador): órdenes/facturas/`decision_logs` ≥ 5 años (fiscal CO), datos personales de cuenta/marketing 2 años tras cancelación, logs app 90 días, `auth_events` 1 año, carritos 30 días, backups PITR 7 días; anonimización por campo; comunicación "backups no se borran retroactivamente" | Matriz en `docs/legal/retencion.md`; jobs de purga ARQ (`purge_jobs`) con pgTAP | F5-01 |
| F5-04 | Política de devoluciones (D-13): plantilla Estatuto del Consumidor (retracto 5 días hábiles, garantía legal mínimo 1 año, exclusiones explícitas), campos editables acotados por tenant en settings (plazos, exclusiones, productos retornables), página `/legal/devoluciones` en storefront (bloque `rich_text` seedeado), enlace en footer y checkout | Publicada en ropa y joyería; campos funcionan; abogado aprueba | F3-05 |
| F5-05 | DPA clickwrap (D-09): texto, flujo owner→aceptar→activar tenant, registro en `legal_acceptances`, versión/hash visibles en admin ("Aceptado v1.2 el …"), email de confirmación al owner; renovación automática si versión cambia (re-acceptance gate) | Flujo E2E; auditoría `legal.document_accepted` en `decision_logs` | F5-02 |
| F5-06 | Breach protocol (D-12): responsable interino (persona A) + backup; severidad S1-S4; SLA: detección→tenant ≤ 24h (contractual), autoridad (SIC) ≤ 72h; plantillas de notificación (tenant, titular, autoridad) en `docs/legal/breach-templates/`; detección: alertas Sentry/WAF/chain-verify/auth-anomalies; runbook y simulacro en staging (game day) | Runbook `docs/operations/breach-runbook.md`; simulacro documentado con tiempos reales | F1-10, F5-01 |
| F5-07 | Soporte (D-16): `soporte@growup.com` (Google Workspace/Shared mailbox) + `github.com/growup-soporte` privado como ticket lite; FAQ mínima `docs/soporte/faq.md` (10 artículos: alta, dominio, pagos, factura, reembolso, suspensión, exportar datos, DSR); SLA: primera respuesta ≤ 8 h hábiles CO, sin compromiso de resolución; acceso de soporte a datos: temporal, motivo, consentimiento del tenant registrado en `decision_logs`, expiración 24h | Runbook acceso soporte (W1-07) implementado; FAQ publicada | F3, F4 |
| F5-08 | SOC 2-ready evidence (D-18): `docs/compliance/` con matriz de controles (change mgmt: PR+CI+migraciones; acceso MFA+min privilegio; vendor review anual; inventario de activos; IR; backups probados), registro vendor risk anual (Supabase, Wompi, Stripe, Cloudflare, Fly, R2, Resend, Sentry, Vercel, Upstash, Factus), checklist onboarding/offboarding de accesos | Matriz completa; primera vendor review hecha; revisión trimestral calendada | F0-08 |
| F5-09 | Privacidad storefront: banner/aviso de datos (sin cookies de terceros; analytics propio F3-10), política de privacidad por tenant (plantilla), página `/legal/privacidad` | Publicada; abogado aprueba | F3-05 |
| F5-10 | Residencia de datos: confirmar sa-east-1 en Supabase/Fly/Upstash; emails Resend en US (documentar transferencia internacional en DPA, cláusulas estándar), DPA con sub-encargados listados (Wompi, Stripe, Cloudflare, Resend, Factus, Supabase, Fly, Vercel, Sentry, Grafana) | Anexo sub-encargados en DPA; registro actualizado | F5-01, F0-03 |

**Criterio de salida de F5:** DPA firmable; DSR ensayado < 1 día; breach runbook con simulacro; FAQ y soporte operativos; evidence folder inicial.

---

## 9. Fase 6 — Piloto ropa + joyería (Semana 14–18)

| ID | Tarea | DoD |
|---|---|---|
| F6-01 | Seed demo ropa/joyería (B-01): `supabase/seed.demo.sql` + `services/api/scripts/seed_demo.py` (idempotente), 2 tenants, 3 categorías y 6 productos cada uno, 2 variantes/producto, precios COP centavos, `status=active` | `db reset` + seed → tiendas navegables; pgTAP verdes |
| F6-02 | Contenido real: copy, 12 productos, fotos (media pipeline real), páginas publicadas con bloques; themes ajustados por tenant | Stakeholders firman vista previa |
| F6-03 | Playwright E2E suite (B-02): home/colección/PDP, 404, `alt`, aislamiento host A/B, flujo compra completo sandbox (redirect Wompi → mock webhook), carrito tras refresh, Lighthouse CI (perf ≥ 80 móvil, SEO ≥ 90, a11y ≥ 90) | Suite verde contra staging; corre en CI en main |
| F6-04 | QA funcional: matriz módulos × roles (owner/manager/packer/support); regresión completa; `tenant-isolation-check` skill | Sign-off de QA |
| F6-05 | Criterios de aceptación piloto (D-08): 2 tiendas públicas con TLS, compra real sandbox de extremo a extremo, factura DIAN emitida, email recibido, suspensión de prueba (impago simulado), DSR simulado, restore de backup en < RTO, Lighthouse OK, cero hallazgos críticos OWASP | Checklist `docs/acceptance/piloto.md` firmado |
| F6-06 | Go-live controlado: DNS `ropa.growup.com`/`joyeria.growup.com`, comunicado a los 2 comercios, monitoreo 72h vigilancia activa, on-call | Post-mortem-lite a los 7 días; decisión go/no-go fase 2 |

## 10. Fase 7 — Post-piloto (Fase 2, Q2 2027+)

Fuera del alcance del piloto (registrar como decisiones futuras): dominio custom (Cloudflare for SaaS), marketplace/comisión (reabrir D-17 con asesoría fiscal), returns/RMA software (D-05 diferido), analítica propia avanzada, white-label themes, multi-moneda, Meilisearch, self-service onboarding.

---

## 11. Riesgos y mitigaciones

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| Abogado/contador demora el cierre de D-09/D-10/D-06 | Alta | Bloquea F3/F4/F5 | Contratar YA en F0 con paquete cerrado y fecha límite; avance con textos propuestos + revisión |
| Wompi/Stripe no habilitan cuentas a tiempo | Media | Bloquea F4 | Crear cuentas en F0; sandbox temprano (B-06); método alternativo temporal: MercadoPago preapproval como fallback de suscripción |
| ADR-0005 mal ratificado → rework de bloques | Media | Retrabajo F3 | Ratificar inventario de bloques con v0 antes de programar; congelar schema v1 |
| Equipo de 2 personas saturado | Alta | Cronograma | Lotes por fase; PR pequeños; nada de multitarea de olas; postergar F7 explícitamente |
| Latencia Colombia→gru | Media | UX | Medir p95 real; evaluar `us-east-1` para Redis/workers si gru falla; R2 es global; Vercel edge cache mitiga storefront |
| Fuga cross-tenant en features nuevas | Media | Crítico | `block-review`/`tenant-isolation-check` obligatorios; tests A/B por feature |
| Factus sin sandbox estable | Baja | F4-07 | Fallback: Alegra como proveedor DIAN (mismo patrón de adaptador aislado) |
| Costos Vercel/Fly/Supabase superan presupuesto | Media | Financiero | Alertas F1-12; staging scale-to-zero; ISR agresivo; imágenes en R2 no en Vercel |

---

## 12. Cronograma indicativo

```text
Sem 1-2   F0 decisiones/limpieza ───────────────┐
Sem 2-4   F1 infraestructura/staging ───┐       │
Sem 3-5   F2 hardening ────────────────┤       │ (F5 arranca aquí, paralela)
Sem 5-9   F3 builder/contenido ────────┤       │
Sem 8-14  F4 comercio ─────────────────┤       │
Sem 2-16  F5 legal/cumplimiento ───────┘       │
Sem 14-18 F6 piloto ───────────────────────────┘
→ Q1 2027: piloto controlado (objetivo D-08)
```

---

## 13. Métricas de progreso

- % tareas completadas por fase (este documento como tablero).
- pgTAP + integration + E2E verdes; cobertura API ≥ 80%; 0 críticos Trivy/pip-audit/pnpm audit.
- p95 API < 500 ms staging; LCP móvil storefront < 2.5 s; purge de publish < 10 s.
- 100% de P0 auditoría cerrados con test; 0 decisiones en Propuesta sin fecha+gate.
- Uptime staging ≥ 99% en 30 días; restore de backup ensayado ≤ RTO 2h.

## 14. Protocolo de actualización

1. Toda tarea completada → PR + checklist marcado aquí.
2. Toda decisión nueva → `docs/decisiones-pendientes.md` + actualizar `decisiones-proveedores-growup.md`.
3. Cambio de alcance → solo vía decisión explícita registrada; nunca en silencio.
4. Revisión semanal de 30 min (persona A+B) con este documento abierto.
