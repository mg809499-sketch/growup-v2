# Decisiones y proveedores — cierre de propuestas pendientes (Growup)

> Fecha: 2026-11-10 · Basado en la auditoría y en `docs/decisiones-pendientes((1)).md` · **Todas las elecciones son propuestas para ratificación explícita por el equipo/abogado/contador en la sesión F0-01; ninguna se aplica en silencio.** Una vez ratificadas, se edita `docs/decisiones-pendientes.md` y los ADRs según el protocolo del repo.

## Resumen ejecutivo de cierres propuestos

| ID | Tema | Decisión propuesta | Proveedor / valor elegido | Gate de ratificación |
|---|---|---|---|---|
| D-01 der. | Precios y límites de plan | Starter COP 49.000/mes · Pro COP 129.000/mes · 14 días trial · anual = 2 meses gratis | Stripe Billing | Equipo (producto) |
| D-02 der. | Entidad legal Stripe | **Confirmar en F0**; fallback MercadoPago preapproval | Stripe (o MP) | Equipo + contador |
| D-03 | DIAN proveedor | **Factus** (API-first, sandbox gratis, factura + nota crédito) | Factus · fallback Alegra | Abogado/contador |
| D-06 der. | IVA envío + zonas + redondeo | IVA 19% sobre envío **solo si el contador confirma** (supuesto de trabajo: incluido); 2 zonas (Bogotá / resto del país); redondeo half-up a centavo, total mostrado en pesos enteros | Reglas A | Contador |
| D-07 der. | DNS/TLS + borde | **Cloudflare** (DNS + proxy WAF) + wildcard TLS por Vercel + Fly detrás de Cloudflare | Cloudflare | Equipo |
| D-08 der. | Fecha piloto, responsable, criterios | 2027-02-15 (dentro de Q1) · responsable contenido: persona A · criterios en plan §9 | — | Equipo |
| D-09 | DPA processor/controller | **A** — clickwrap por el owner; `legal_documents`/`legal_acceptances`; `pending_legal` bloquea publish/checkout/billing | Plantilla: abogado CO | Abogado |
| D-10 | DSR y retención | **A** — manual asistido por platform admin; matriz de retención (≥5 años fiscal); anonimización por campo; región única **sa-east-1** | Reduce a runbook + rol `platform_dsr` | Abogado/contador |
| D-11 | PCI / página de pago | **A** — SAQ A con redirect hosted de Wompi; cero terceros; CSP estricta; inventario de scripts versionado; ASV solo si A-EP | Wompi Checkout | Seguridad (post-spike) |
| D-12 | Brecha 72h | **A** — DPO interino (persona A) + backup; SLA 24h tenant / 72h SIC; plantillas; game day | Runbook + on-call | Abogado |
| D-13 | Devoluciones | **A** — plantilla Estatuto del Consumidor + campos acotados por tenant; operación manual del reembolso vía Wompi | Plantilla F5-04 | Abogado |
| D-14 | Fraude/chargebacks | **A** — delegar a antifraude Wompi + 3DS (tarjetas); ToS: disputa a cargo del comerciante; campos de evidencia en admin; B en fase 2 | Wompi 3DS | Seguridad + abogado |
| D-15 | Email transaccional | **Resend** — API de dominios con verificación DKIM/SPF/DMARC automatizable, webhooks rebote/queja, región US (transferencia internacional documentada en DPA) | Resend · fallback Postmark | Equipo (spike B-05) |
| D-16 | Soporte y SLA | **A** — `soporte@growup.com` + GitHub privado como tracker; primera respuesta ≤ 8 h hábiles CO; sin SLA de resolución; acceso de soporte temporal + auditado (W1-07) | Google Workspace shared mailbox | Equipo |
| D-17 | Marketplace facilitator | Cerrada (2026-10-26) — no facilitador en MVP | — | Cerrada |
| D-18 | SOC 2 | Cerrada (2026-10-26) — postura alineada, evidence folder `docs/compliance/` | — | Cerrada |
| ADR-0005 | Contenido/publishing | Ratificar opción A del ADR con lista de bloques MVP del prompt v0 (16 bloques); publish atómico; preview token firmado | — | Producto |
| ADR-0009 | Privacidad/DPA/DSR | Aceptada tras compuertas (abogado + controles F5-02/F5-03/F5-05) | — | Abogado + Ingeniería |
| ADR-0010 | Checkout PCI | Aceptada con opción redirect; SAQ A definitivo tras spike Wompi | — | Seguridad |
| ADR-0011 | Email | Aceptada con Resend; subdominio por tenant; ARQ | Resend | Equipo |
| Nuevo | Región de datos | **sa-east-1** (São Paulo) en Supabase, Fly y Upstash; R2 global (sin región); Resend/Sentry/Grafana en US con cláusulas de transferencia en DPA | sa-east-1 | Equipo + abogado |
| Nuevo | Observabilidad | Sentry (errores+trazas, free→Team) + OpenTelemetry → Grafana Cloud Free (métricas/logs/dashboards) | Sentry + Grafana Cloud | Equipo |

---

## D-01 derivado — Precio y límites de plan (propuesta)

**Contexto:** D-01 cerrada (suscripción, trial 14 días, 0% comisión). Falta precio y límites, necesarios antes del onboarding y para seed de `plans`.

**Propuesta (eficiencia: precio simple, dos planes, sin contador de uso complejo en MVP):**

| | Starter | Pro |
|---|---|---|
| Precio | COP 49.000/mes | COP 129.000/mes |
| Anual | 2 meses gratis (COP 490.000/año) | 2 meses gratis (COP 1.290.000/año) |
| Productos | hasta 200 | hasta 3.000 |
| Staff/usuarios admin | 2 | 10 |
| Storage media | 2 GB | 25 GB |
| Órdenes/mes | 500 | ilimitadas |
| Soporte | email, 8h hábiles | email prioritario, 4h hábiles |
| Dominio | subdominio `*.growup.com` | subdominio + (fase 3) dominio custom |

**Por qué:** dos planes minimizan soporte y decisión del cliente; límites por contador simple (query count) evitan infraestructura de metering; precio anclado al costo incremental de un tenant pequeño en Supabase/Fly/R2 (< USD 5/mes por tenant) con margen sano. **No se cobra comisión ni % del GMV** (D-01).

**Alternativa rechazada:** plan gratuito permanente (soporte y abuso sin pago); comisión por venta (rompe D-01/D-17); tres+ planes (decisión y soporte innecesario en MVP).

**Gate:** ratificación de persona A + contador (impuestos sobre suscripción: IVA 19% sobre el precio? confirmar tratamiento fiscal de SaaS). Actualizar `seed.sql` (reemplazar placeholder `{"placeholder": true}`), `plans` con precios reales y `docs/comercial/planes.md`.

---

## D-02 derivado — Cuenta Stripe y régimen de suscripción

**Propuesta:** confirmar en F0-08 que la entidad legal de Growup puede contratar Stripe (Colombia soportada para cuentas de empresa). **Si no:** MercadoPago preapproval como respaldo (misma abstracción `SubscriptionProvider` en código; flag `GROWUP_BILLING_PROVIDER=stripe|mercadopago`). Suscripción acepta **solo tarjeta** (PSE/Nequi no recurrentes fiables). La suscripción cobra IVA 19% sobre el precio mensual (confirmar con contador).

**Gate:** decisión de entidad en la sesión F0-01. El checkout del cliente final sigue siendo Wompi; Stripe solo cobra la suscripción de la plataforma.

---

## D-03 (cierra el pendiente) — DIAN: Factus como proveedor

**Comparativa:**

| Criterio | Factus | Siigo | Alegra |
|---|---|---|---|
| API developer-first | ★★★★★ (OAuth2, REST, webhooks) | ★★★ (API orientada a integración Siigo, más pesada) | ★★★★ (API REST, docs en español) |
| Sandbox gratis | Sí | Limitado/demo | Sí |
| Nota crédito por API | Sí (nc/02) | Sí | Sí |
| Costo por documento | Bajo (paquetes por volumen) | Mayor (suscripción contable completa) | Medio (planes con tope de docs) |
| Es suite contable | No (especializado DIAN) | Sí (ERP contable completo) | Sí (contable + inventario) |
| Overhead operativo | Mínimo | Alto | Medio |
| Riesgo de lock-in contable | Ninguno | Alto (su datos viven en su ERP) | Medio |

**Elección: Factus.** Es el único diseñado para embeberse en un SaaS por API; Siigo/Alegra implican adoptar su modelo de datos contable, innecesario aquí (Growup no es contabilidad, es comercio). **Adaptador aislado** (`app/domains/invoices/factus_client.py`) con interfaz `InvoiceProvider` para poder migrar a Alegra sin tocar dominio. Fallback declarado: Alegra.

**Flujo D-03 + nota crédito (cierra el sub-pendiente de D-03):**
1. Orden `paid` → ARQ `emit_invoice` → Factus factura cf/01 → persistir `electronic_ref`, `pdf_url`, `cufe` en `invoices`.
2. Refund posterior con factura emitida → ARQ `emit_credit_note` → Factus nc/02 referenciando cf/01.
3. Fallo de emisión tras 3 reintentos → `approval_tasks` estado `pending` con payload → notificación a soporte → emisión manual o HANDOFF.
4. **Nunca** se bloquea el flujo de dinero por la DIAN; el documento fiscal es asíncrono y compensable.

**Gate:** contador/abogado confirman proveedor + reglas de no-factura (exportación, régimen). Cuenta Factus sandbox en F0-08.

---

## D-06 derivado — IVA en envío, zonas y redondeo

**Propuesta:**
- **Zonas (MVP):** Zona 1 = Bogotá D.C. (tarifa plana COP 8.000); Zona 2 = resto del país (COP 15.000). Tarifas editables por tenant (`shipping_zones` en BD); valores por defecto seedeados.
- **IVA envío:** supuesto de trabajo = **IVA 19% incluido también en el envío** (el envío es un servicio accesorio gravable en la operación típica). **Confirmar con contador antes de F4-01;** si la conclusión es otra (p.ej. excluido por ser transporte de carga nacional), se ajusta una sola constante (`SHIPPING_TAXABLE`) y los tests asociados. Hasta confirmar, ningún total real sale a producción (bloqueo de go-live, no de desarrollo).
- **Redondeo:** cálculo interno en centavos con redondeo **half-up**; presentación en pesos enteros COP; snapshot en `order_items` y `orders` (`subtotal_cents`, `tax_cents`, `shipping_cents`, `total_cents`, `tax_rate_bps=1900`).
- Todos los productos del piloto gravados al 19% (validar con contador el caso de joyería — joyería de oro está gravada; artesanías pueden estar excluidas — **decisión de contador por tenant**: flag `products.tax_exempt` preparado pero apagado en MVP).

**Gate:** contador. Sin esto, F4-03 no mergea a producción.

---

## D-07 derivado — DNS/TLS y borde

**Elección: Cloudflare (free plan) como DNS autoritativo + proxy WAF en delante, Vercel para wildcard TLS del storefront, Fly.io detrás de Cloudflare para la API.**

Diseño:
```text
*.growup.com      → Cloudflare (proxied) → Vercel (wildcard cert automático)
growup.com (apex) → Vercel
admin.growup.com  → Vercel (proyecto admin)
api.growup.com    → Cloudflare (proxied, WAF+rate limit) → Fly origin (Origin CA cert o Full strict)
mail.*.growup.com → Resend (MX/DKIM CNAMEs directos, sin proxy)
```

**Por qué Cloudflare:** DNS gratis, wildcard flexible, WAF/rate limiting/reglas sin costo inicial, protección DDoS, y es el único con edge global cerca de Colombia en el plan free. Vercel emite el wildcard automáticamente; no hace falta Cloudflare for SaaS todavía (D-07 difiere dominios custom a fase 3).

**Alternativa rechazada:** Vercel-only DNS (sin WAF ni rate limiting serios); Cloudflare for SaaS ahora (costo y complejidad prematura); DNS en el registrador (sin WAF).

**Gate:** equipo. Acción F0-08/F1-05: crear zona, migrar NS del dominio a Cloudflare (si el dominio ya existe; si no, comprarlo en Cloudflare Registrar).

---

## D-08 derivado — Fecha, responsable y criterios del piloto

- **Fecha objetivo:** 2027-02-15 (Q1 2027, con 4 semanas de colchón frente a cierre fiscal/IVA).
- **Responsable de contenido:** persona A; supervisión persona B en QA.
- **Criterios de aceptación (gate go/no-go):** los de plan § Fase 6 F6-05. En particular: compra E2E real en sandbox + factura DIAN emitida + email recibido + suspensión simulada + DSR simulado + restore de backup < RTO.
- **Tenants:** ropa + joyería tal como están seededados.

**Gate:** equipo (confirmación en F0-07).

---

## D-09 — DPA: opción A con clickwrap del owner

**Especificación para implementación (F5-02/F5-05):**
1. Tablas inmutables: `legal_documents(id, type, version, title, body_md, sha256, published_at, retired_at)` y `legal_acceptances(tenant_id, document_id, actor_user_id, accepted_at, method='clickwrap', evidence jsonb)` — sin UPDATE/DELETE (revocar grants; solo INSERT vía función).
2. Estado en tenant: `tenants.legal_status ∈ ('pending_legal','active')`. `pending_legal` bloquea: publicar páginas, activar checkout, crear suscripciones. El storefront público en `pending_legal` muestra placeholder "Tienda en configuración" (no datos del tenant).
3. Quién acepta: **solo el owner del tenant** (rol `owner` + `app_metadata` + membresía verificada), no el platform admin creador.
4. Renovación: si `legal_documents` publica nueva versión, `legal_status` vuelve a `pending_legal` hasta re-acceptance (banner admin + bloqueo de publish).
5. Registro en `decision_logs`: `policy_id='legal.document_accepted'` (payload redactado: tipos/ids/versión/hash, nunca contenido libre).
6. Sub-encargados (anexo DPA): Supabase, AWS/Fly, Cloudflare, Vercel, Resend, Wompi, Stripe, Factus, Sentry, Grafana, Upstash, R2 — lista mantenida en `docs/legal/subencargados.md`.
7. Retención: `legal_acceptances` permanente (prueba contractual); `legal_documents` permanente.

**Textos:** abogado colombiano entrega DPA + ToS + política privacidad + política devoluciones + contrato de suscripción. Presupuesto est. 2–4h × tarifa del abogado; facturar en F0.

**Gate:** firma del abogado. **No hay datos reales de compradores antes de esta firma.**

---

## D-10 — DSR y retención: opción A manual asistida

**Especificación:**
1. Rol `platform_dsr` (permiso `legal:dsr`), nunca `service_role` general; ejecución por función con `SECURITY DEFINER` revisada o por SQL supervisado en consola — en MVP: **procedimiento manual supervisado por persona A**, documentado línea a línea en `docs/operations/dsr-runbook.md`; automatización en fase 2.
2. Verificación de identidad del titular (email del pedido + datos de envío + número de orden; llamada/correo de confirmación si dudas).
3. Matriz de retención (aprobar con abogado/contador):

| Dato | Retención | Acción al expirar |
|---|---|---|
| Órdenes, facturas, `decision_logs` | ≥ 5 años (fiscal CO) | Conservar (anónimo permitido), nunca borrar |
| Datos cuenta comprador (nombre, email, teléfonos) | 2 años tras cierre de cuenta | Anonimizar (`nombre='Titular', email='anon-{hash}@deleted.growup.com'`) |
| Direcciones | 2 años | Anonimizar campos línea/barrio/teléfono |
| `auth_events`, logs app | 90 días–1 año | Borrar |
| Carritos | 30 días | Borrar |
| `legal_acceptances` | Permanente | Conservar |
| Backups (PITR 7 días / dumps) | 7 días | Documentar: backups no se borran retroactivamente; al restaurar, aplicar retención de nuevo |
| Analytics events agregados | 25 meses | Borrar (agregados sin PII se conservan) |

4. Plazos: respuesta al titular ≤ **15 días hábiles** (holgura frente a 10 días hábiles del Habeas Data CO; GDPR 1 mes).
5. Región: **sa-east-1** única. Resend (US) documentado como transferencia internacional con cláusulas estándar en el DPA. Sentry/Grafana idem.
6. `decision_logs` jamás se altera (rompería hash chain); los identificadores en logs van seudonimizados por diseño (ya implementado: allowlist + hash).

**Gate:** abogado/contador aprueba matriz + Habeas Data checklist. Runbook ensayado antes del go-live (F6-05).

---

## D-11 — PCI: SAQ A con redirect (confirmado, no condicionado más)

**Elección: opción A.** Checkout = redirect puro a Wompi Checkout (hosted). Regla dura permanente:
- **Cero scripts de terceros en `/checkout`** (ni analytics propio con terceros, ni pixels, ni GTM, ni mapas de calor). CSP de checkout: `default-src 'self'; script-src 'self'; connect-src 'self' api.wompi.co; img-src 'self' data:; style-src 'self' 'unsafe-inline'` (sin unsafe-inline si es posible).
- Inventario de scripts del storefront versionado (`docs/security/script-inventory.md`); test CI que falle si aparece un dominio externo no aprobado en `/checkout`.
- Redirect, no iframe/widget. Si Wompi exigiera widget (no es su checkout estándar), se reevalúa A-EP + ASV — decisión solo post-spike.
- **SAQ A** anual presentada a la marca/adquirente; responsable: persona A; evidencia: inventario + CSP test + política de cambios con PR obligatorio en checkout.
- MFA en accesos administrativos (Vercel/Fly/Supabase/GitHub con TOTP obligatorio) y change management PR+CI (ya existe).
- 3DS: ver D-14.

**Gate:** spike Wompi confirma redirect viable (B-06). Hasta entonces, regla dura vigente sin excepciones.

---

## D-12 — Brecha: opción A formal con responsable y SLA

**Especificación:**
- **Responsable interino:** persona A (seguridad) · **Backup:** persona B. Revisión formal de nombramiento en sesión F0-01; pasa a DPO/seguridad cuando exista esa figura o exigencia enterprise.
- **Detección:** alertas Sentry (5xx burst), WAF Cloudflare (reglas OWASP), verificación diaria de cadena de auditoría (job F2-13), anomalías Auth (rate de fallos JWKS/login), `readyz` fail, alertas Fly/Vercel. Canal: WhatsApp/Telegram on-call + email a `seguridad@growup.com`.
- **Severidad:** S1 (datos sensibles confirmados exfiltrados) → notificar tenant ≤ 24h y SIC ≤ 72h; S2 (incidente contenido) → tenant ≤ 48h; S3 (sin datos) → registro interno; S4 (falso positivo) → cerrar con nota.
- **Plantillas** en `docs/legal/breach-templates/` (tenant, SIC, titular) — redacta el abogado en el paquete de F5-01.
- **SLA contractual:** 24h a tenants (objetivo, no ley; la ley de notificación a titular/SIC aplica según caso) — el texto legal lo fija el abogado; el SLA interno es de ingeniería.
- **Game day:** simulacro en staging antes del go-live (F5-06): detección → clasificación → notificación simulada → postmortem sin culpables.

**Gate:** abogado valida el protocolo y si el plazo a SIC es aplicable en el caso colombiano.

---

## D-13 — Devoluciones: opción A plantilla + campos acotados

**Especificación:**
- Plantilla base conforme Estatuto del Consumidor (Ley 1480/2011): derecho de retracto (5 días hábiles desde entrega o firma de contrato, a elección del consumidor), garantía legal mínima (1 año sobre calidad), mecanismos y tiempos de reembolso (30 días calendario para devolver dinero), exclusiones (perecederos, bajo pedido expreso personalizado) — **textos exactos por abogado**.
- Campos editables por tenant (acotados): plazo de retracto (default 5 días hábiles), exclusiones (multi-select de categorías), productos retornables s/n, dirección de devolución, correo/WhatsApp de gestión. Sin campo de texto libre legal no revisado — solo ajustes sobre plantilla aprobada.
- Publicación: bloque `rich_text` seedeado en página `/legal/devoluciones` + enlace en footer y en cada PDP; versión y tenant visibles.
- **Operación MVP:** reembolso **manual** desde el panel de Wompi por el comerciante; Growup muestra estado `refund_pending`/`refund_done` (operado a mano), sin API de refunds en MVP salvo lo básico de F4-05. Nota crédito DIAN: ver F4-07 (Factus nc/02).
- Umbrales de aceptación: ninguna tienda pasa a producción (F6-06) sin política publicada y visible.

**Gate:** abogado aprueba plantilla y campos.

---

## D-14 — Fraude y chargebacks: opción A con 3DS

**Especificación:**
- Wompi ofrece antifraude y 3DS dinámico según riesgo de tarjeta. **MVP:** delegar scoring a Wompi; exigir 3DS (desafío o flow automático) para tarjetas cuando el BIN lo soporte; PSE/Nequi no tienen 3DS (documentado).
- Señales registradas (solo si Wompi las expone en webhook/API): `fraud_score`, `threeDS_status`, `payment_method_type`. Nunca PAN/CVV.
- ToS + DPA: el comerciante (merchant of record) asume disputas y chargebacks; Growup no intermedia ni honra disputas de compradores.
- Campos en `orders`: `dispute_status ∈ (none, reported, evidence_submitted, won, lost)`, `dispute_evidence jsonb` (referencias a order, envíos, comunicaciones). Plantilla de evidencia en admin ("Descargar paquete de evidencia" en PDF generado: order + items + envío + logs redactados).
- Alerta a tenant cuando `dispute_status=reported` (email F4-08) con plazo de respuesta (7 días).
- Fase 2: capa propia de señales + cola de revisión (opción B) registrada como decisión futura, sin fecha.

**Gate:** spike Wompi confirma campos disponibles (B-06). Abogado incluye cláusula en ToS.

---

## D-15 — Email: Resend (con Postmark como fallback)

**Comparativa evaluada por eficiencia:**

| Criterio | Resend | Postmark | SES |
|---|---|---|---|
| API y DX | Excelente (REST simple, React Email, ARQ-friendly) | Excelente (muy maduro) | Verboso, credenciales AWS |
| Verificación de dominio por API | **Sí** (create domain → registros DNS → verify) | Sí (server/domain API) | Sí (vía AWS SDK, más pasos) |
| Subdominio por tenant | Sí | Sí | Sí (con más setup) |
| Webhooks rebote/queja | Sí | Sí (excelente) | Sí (SNS, complejo) |
| Precio a 50k emails/mes | ~USD 20/mo | ~USD 50-60/mo | ~USD 5/mo (más operación) |
| Región | US (eu disponible en plan alto) | US/EU (elegir servidor) | us-east-1/eu-west-1/… elegible |
| Supabase Auth SMTP | Compatible | Compatible | Compatible |
| Riesgo operacional | Bajo | Bajo | Medio-alto (reputación a tu cargo) |

**Elección: Resend** — mejor relación DX/costo, verificación automática de subdominios por tenant (encaja con D-15/ADR-0011: `mail.{slug}.growup.com`), webhooks simples hacia ARQ. **Región US documentada como transferencia internacional en DPA** (D-10). Si el spike B-05 mide entregabilidad < 95% o la API de dominios resulta insuficiente → migrar a Postmark (adaptador `EmailProvider` aislado; el código no cambia).

**Configuración (F4-08):**
1. Cuenta Resend; dominio base `growup.com` verificado (DKIM/SPF/DMARC `_dmarc` política `p=quarantine`; subdominios `mail.{slug}.growup.com` con DKIM propio vía API en onboarding).
2. Supabase Auth → SMTP custom Resend (magic links, invites) o canal propio — decidir en spike; propuesta: **mismo Resend**, remitente `noresponder@auth.growup.com`.
3. ARQ worker `send_email`: idempotencia por `email_events(provider_id)`; reintentos 5× con backoff; rebotes → supresión en `email_suppressions` por tenant; métricas entregadas/fallidas en admin.
4. Cuerpo del email **nunca** en logs; solo `message_id`, template, estado. Templates: orden confirmada, orden enviada, magic link (vía Supabase), factura emitida, dunning (día 1/3/7 de past_due), bienvenida al owner, DSR confirmado.

**Gate:** spike B-05 entrega `docs/spikes/email.md` con números; D-15 pasa a CERRADA tras ratificación.

---

## D-16 — Soporte: opción A con SLA realista

**Especificación:**
- Canal: `soporte@growup.com` (Google Workspace shared mailbox, accesible por A y B) + tracker en repo privado `growup-soporte` (GitHub issues = tickets, etiquetados). Chat widget **no** en MVP.
- SLA: primera respuesta **≤ 8 horas hábiles** (lun–vie 8–18 Colombia); sin compromiso de resolución; escalamiento a on-call solo S1 (caída total o fuga de datos), vía WhatsApp.
- FAQ mínima (10 artículos) publicada en `help.growup.com` (o página estática en `growup.com/ayuda`): empezar tienda, elegir plan, DNS/subdominio, Wompi onboarding, factura DIAN, reembolso manual, suspensión por impago, exportar datos (CSV), solicitar DSR, contacto.
- Acceso de soporte a datos de tenant: solo con **consentimiento registrado** (ticket con aceptación explícita del owner), **motivo** y **expiración ≤ 24h**; acceso vía rol `support` + log obligatorio en `decision_logs` (`support.access_opened`/`closed`), nunca credenciales compartidas — staff del tenant usa su propia cuenta.
- Post-MVP: migrar a Freshdesk/Zendesk cuando > 20 tenants o SLA por plan (Pro 4h).

**Gate:** equipo ratifica SLA y canal; FAQ redactada por persona B.

---

## ADR-0005 — Contenido y publishing: ratificación

**Decisión propuesta:** aceptar ADR-0005 con estos detalles (ya consistentes con el diseño existente):
- Bloques MVP = los 16 del prompt v0 (`header, footer, hero, editorial_split, product_grid, product_carousel, collection_grid, image_banner, rich_text, quote, gallery, video_embed, faq, newsletter, spacer, columns`). `marqee` opcional fase 2.
- `page_versions.layout` JSONB: `{ "version": int, "blocks": [ { id, type, props, children? } ] }`; esquemas Pydantic con `extra='forbid'`; `rich_text` = Markdown subset saneado server-side (sin HTML); `video_embed` allowlist `youtube.com|player.vimeo.com`.
- Publish atómico: transacción swap `pages.published_version_id` + outbox `content.published`; worker ARQ purga tag ISR de Next; rollback = re-point a versión anterior (guardada).
- Preview: token HMAC firmado (`GROWUP_PREVIEW_SECRET`), TTL 15 min, scope `page_id`, solo lectura.
- Retención de drafts: 90 días (job purga).
- Storefront ISR `revalidate=3600` + tags; publish purga bajo demanda.

**Gate:** producto (persona A) acepta inventario de bloques; nadie empieza F3 antes de este cierre.

---

## ADR-0009 / ADR-0010 / ADR-0011 — Compuertas para pasar a Aceptada

- **ADR-0009 (Privacidad):** cerrar D-09 y D-10 en F0-01; implementar F5-02/F5-03/F5-05 con sus pgTAP/integración; **entonces** pasa a Aceptada. Hasta entonces, ningún dato real de compradores.
- **ADR-0010 (PCI):** redirect hosted ratificado ahora; decisión final SAQ A vs A-EP tras spike Wompi (B-06); pasa a Aceptada al primer E2E sandbox verde con CSP verificada (F4-04).
- **ADR-0011 (Email):** Resend elegido; pasa a Aceptada cuando DKIM/SPF/DMARC de `mail.{slug}.growup.com` estén en verde en staging (F4-08) y el spike B-05 entregue `docs/spikes/email.md`.

---

## Nuevo — Región de datos: sa-east-1

**Elección:** Supabase (proyecto `growup-prod`) en **sa-east-1 (São Paulo)**; Fly.io `gru`; Upstash sa-east-1 (o us-east-1 si gru no disponible en plan — verificar); R2 (global, bucket con jurisdicción por defecto); Cloudflare edge (global); Resend/Sentry/Grafana en US (transferencia internacional documentada y con cláusulas tipo en DPA).

**Por qué:** es la región más cercana a Colombia disponible con todos los proveedores (~35–60 ms BOG→GRU vs ~120–180 ms a us-east-1), cumple la preferencia de D-10 (una sola región, la del proyecto Supabase), y mantiene coherencia cómputo↔datos (Fly y DB co-locados) eliminando latencia por query chatty. Medir p95 real en staging y re-evaluar solo si datos objetivos lo exigen.

**Gate:** confirmación de disponibilidad en todos los proveedores en F0-08; anexo de transferencias internacionales revisado por abogado (F5-10).

---

## Nuevo — Sentry + Grafana Cloud para observabilidad

**Elección:** Sentry (errores y trazas; plan Developer/Team según volumen) + OpenTelemetry → **Grafana Cloud Free** (métricas, logs, dashboards, alertas). **Por qué:** costo casi cero al inicio, OTel estándar (sin lock-in), dashboards compartibles, y Sentry ya integrado opcionalmente en el código. Alertas S1 → on-call vía WhatsApp/PagerDuty (PagerDuty free tier solo si hay guardia real; si no, WhatsApp manual documentado).

**Alternativa rechazada:** Datadog (costo prohibitivo), solo Sentry (sin métricas de pool/cola), solo CloudWatch (no aplica, Supabase no es AWS nativo para logs de app).

**Gate:** equipo; implementación en F1-10.

---

## Registro de decisiones derivadas a documentar en el repo tras ratificación

1. `docs/decisiones-pendientes.md`: marcar D-03, D-06-der, D-07-der, D-08-der, D-09..D-16 como CERRADA con fecha 2026-11 (post-sesión F0-01).
2. `docs/adr/0012-proveedores-y-region.md`: nueva ADR con región, Cloudflare, Resend, Factus, sa-east-1, Sentry/Grafana, precios de plan.
3. Actualizar ADR-0005 → Aceptada; ADR-0009/0010/0011 → Aceptada al cumplir compuertas.
4. README y `reparto-trabajo.md` alineados; eliminar `decisiones-pendientes (1).md` (contenido fusionado con estados correctos).
5. Seed `plans` con precios reales (D-01-der) y `features` sin placeholder.
