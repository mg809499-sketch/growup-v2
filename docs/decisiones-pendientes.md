# Decisiones de negocio pendientes

> **Estado:** 8 cerradas (D-03 con proveedor por definir) · **Última actualización:** 2026-10-21
> **Regla:** ninguna de estas decisiones se asume en silencio. Cada una se cierra con una respuesta explícita y, cuando aplique, un ADR.
> **Nota (2026-10-26):** D-09 a D-18 están en **propuesta** en `docs/decisiones-pendientes (1).md`; no se consideran cerradas. Cubren DPA, DSR/retención, PCI/SAQ, brechas, devoluciones, fraude, email, soporte, marketplace facilitator y SOC 2. El detalle, los riesgos y la secuencia están en ese archivo.

## Resumen

| ID | Decisión | Prioridad | Bloquea | Estado |
|---|---|---|---|---|
| D-01 | Modelo de cobro a comerciantes | **IMPORTANTE** | `design.md`, admin, onboarding | **CERRADA** (2026-10-21) |
| D-02 | Pasarela de pagos del MVP | **IMPORTANTE** | checkout, webhooks, conciliación | **CERRADA** (2026-10-21) |
| D-03 | Facturación electrónica DIAN | **IMPORTANTE** | invoices, flujo post-pago, legal | **CERRADA (modelo)** (2026-10-21) |
| D-04 | Cuentas de cliente | **IMPORTANTE** | auth, RLS, checkout | **CERRADA** (2026-10-21) |
| D-05 | Alcance funcional del MVP | **IMPORTANTE** | port desde `multitiendas`, olas | **CERRADA** (2026-10-21) |
| D-06 | Moneda e impuestos | **IMPORTANTE** | precios, invoices, reportes | **CERRADA** (2026-10-21) |
| D-07 | Dominios y TLS | **IMPORTANTE** | tenancy, onboarding | **CERRADA** (2026-10-21) |
| D-08 | Primer tenant y fecha de lanzamiento | **IMPORTANTE** | contenido, QA, go-live | **CERRADA** (2026-10-21) |

## Protocolo para cerrar una decisión

1. Elegir una opción.
2. Escribir la respuesta en la sección **Decisión** de este documento, con fecha y responsable.
3. Si cambia la arquitectura, crear o actualizar un ADR en `docs/adr/`.
4. Actualizar `.kiro/steering/` si la decisión afecta reglas permanentes.
5. Cambiar el estado a **CERRADA**.

---

## D-01 — Modelo de cobro a comerciantes

**IMPORTANTE — CERRADA (2026-10-21)**

**Contexto:** el documento V2 describe un SaaS con builder, pero no define cómo paga el comerciante por la plataforma. Sin esto no existen `plans`, `subscriptions`, trials, suspensión por impago ni métricas de negocio.

**Opciones:**

- **A. Suscripción mensual por plan** (Starter / Pro), con trial de 14 días. Ingreso predecible; requiere definir límites por plan (productos, dominios, storage, usuarios).
- **B. Comisión por venta** (porcentaje del GMV). Alinea incentivos, pero exige conciliación con la pasarela y reportes por tenant.
- **C. Híbrido:** suscripción base + comisión por ventas altas o add-ons (dominio custom, storage extra).

**Recomendación:** A para el MVP (0% comisión), con la estructura de datos preparada para C.

**Impacto si no se decide:** no se puede diseñar el admin de facturación, el onboarding ni la suspensión de tenants.

**Bloquea:** `design.md`, `apps/admin`, tablas `plans` / `subscriptions` / `usage`.

**Criterio de cierre:** plan elegido, límites por plan y política de trial/impago.

**Decisión (2026-10-21):** **A.** Suscripción mensual con trial de 14 días y 0% de comisión durante el MVP. Los límites por plan y el precio se definen con costos reales de infraestructura. La estructura de datos queda preparada para el modelo híbrido (C).

**Pendiente derivado:** precios y límites por plan. No bloquea el diseño; se define antes del onboarding.

---

## D-02 — Pasarela de pagos del MVP

**IMPORTANTE — CERRADA (2026-10-21)**

**Contexto:** hay dos flujos de dinero distintos y el documento V2 los mezcla:

1. **Plataforma → comerciante:** cobro de la suscripción mensual (D-01).
2. **Comerciante → comprador:** cobro del checkout de cada tienda.

Elegir "Wompi vs MercadoPago vs Stripe" sin separar estos flujos produce una decisión incompleta.

### 2.1 Decisión oculta: ¿quién es el comerciante de registro?

| Modelo | Cómo funciona | Implicaciones |
|---|---|---|
| **Credenciales por tenant** | Cada comerciante conecta su cuenta de pasarela; la plataforma solo orquesta. | El comerciante es el *merchant of record*. Sin custodia de fondos. Onboarding más pesado. |
| **Marketplace / connected accounts** | La plataforma es facilitadora; la pasarela divide pagos y comisiones. | Mejor UX y fee automático. Requiere soporte de marketplace y revisión legal. |
| **Plataforma merchant of record** | La plataforma cobra y luego liquida al comerciante. | Custodia de fondos, riesgo regulatorio y contable alto. No recomendado para el MVP. |

**Recomendación:** credenciales por tenant en el MVP (sin custodia de fondos). Evaluar marketplace en fase 2 si la propuesta exige checkout único y split de comisiones.

### 2.2 Criterios para elegir la pasarela

| Criterio | Wompi | MercadoPago | Stripe |
|---|---|---|---|
| Cobertura Colombia | Alta | Alta | Media |
| COP, PSE, Nequi | Sí | Sí | Limitado |
| Tarjetas internacionales | Media | Alta | Alta |
| Suscripciones / cobro recurrente | Verificar | Preapproval | Billing maduro |
| Marketplace / split | Verificar | Marketplace | Connect |
| Webhooks firmados e idempotencia | Sí | Sí | Sí |
| Sandbox y documentación | Buena | Buena | Excelente |
| Tarifas | Verificar vigentes | Verificar vigentes | Verificar vigentes |
| Complejidad de integración | Media | Media | Media-alta |

> Las tarifas y la disponibilidad de suscripciones/marketplace deben confirmarse con cada proveedor antes de cerrar la decisión. No se asumen en este documento.

### 2.3 Opciones

- **A. Wompi para checkout + MercadoPago para suscripciones.** Dos integraciones, cobertura local fuerte.
- **B. Solo MercadoPago:** checkout y preapproval en un solo proveedor; menor cobertura PSE/Nequi que Wompi.
- **C. Stripe:** Billing y Connect muy maduros; menor penetración local para el checkout del comprador.
- **D. Wompi + Stripe:** Wompi para COP/PSE/Nequi; Stripe para suscripciones y ventas internacionales.

### 2.4 Decisión

**Decisión (2026-10-21):**

1. **Merchant of record:** el comerciante. Growup usa credenciales por tenant y no custodia fondos.
2. **Checkout del comprador:** Wompi como pasarela principal para COP (PSE, Nequi y tarjetas). Cada tenant conecta su propia cuenta de Wompi.
3. **Suscripción de la plataforma:** Stripe Billing. Si la entidad legal no puede operar con Stripe en Colombia, se usa MercadoPago preapproval como respaldo.
4. **Comisión por venta:** no se implementa en el MVP. Queda como decisión de fase 2; el diseño deja una abstracción de proveedor y campos de fee/ledger preparados, sin split.
5. **Refunds y chargebacks:** los asume el comerciante en el checkout. La plataforma gestiona solo disputas de la suscripción.
6. **Datos de tarjeta:** nunca tocan Growup; se usa hosted checkout/redirect del proveedor.

**Pendientes derivados (no bloquean el diseño):**

- Confirmar que la entidad legal de Growup puede abrir cuenta Stripe; si no, suscripción con MercadoPago preapproval.
- Definir si la suscripción acepta PSE/Nequi o solo tarjeta.
- Verificar tarifas y soporte de Wompi para el flujo elegido.
- Decidir en fase 2 si habrá comisión por venta y, por tanto, marketplace.

**Impacto:** habilita Wave 4; obliga al onboarding de cuentas Wompi por tenant y a dos integraciones (Wompi + Stripe).

**Bloquea:** Wave 4 (checkout/pagos), DDL de `payments`, `webhook_events`, `tenant_payment_accounts` y `platform_subscriptions`.

**Criterio de cierre:** cumplido el 2026-10-21.

**Decisión:** **CERRADA** (2026-10-21).

---

## D-03 — Facturación electrónica DIAN

**IMPORTANTE — CERRADA (modelo) — 2026-10-21**

**Contexto:** en Colombia la factura electrónica es obligatoria y requiere CUFE, QR y validación ante la DIAN. Construirlo desde cero es un proyecto en sí mismo.

**Opciones:**

- **A. Proveedor certificado** (Factus, Siigo, Alegra u otro): API de emisión, menor riesgo legal.
- **B. Integración directa con la DIAN:** control total, pero alto costo de mantenimiento y certificación.
- **C. Emisión manual fuera de la plataforma:** simple, pero rompe la promesa de "facturación incluida".

**Recomendación:** A. El backend guarda `electronic_ref` y el PDF, pero delega la emisión al proveedor.

**Impacto si no se decide:** no se puede cerrar el flujo de orden pagada → factura.

**Bloquea:** `invoices`, Wave 4, cumplimiento legal.

**Criterio de cierre:** proveedor elegido, contrato/API key y flujo de reintentos definido.

**Decisión (2026-10-21):** **A.** Se usa un proveedor certificado. El backend guarda `electronic_ref` y el PDF, y delega la emisión. El proveedor concreto (Factus, Siigo o Alegra) se elige antes de la Wave 4.

**Pendiente derivado:** selección del proveedor, contrato y API key.

---

## D-04 — Cuentas de cliente

**IMPORTANTE — CERRADA (2026-10-21)**

**Contexto:** el documento no define si el comprador final tiene cuenta, si compra como invitado o si usa magic link. Esto cambia auth, RLS, checkout y soporte.

**Opciones:**

- **A. Guest checkout solamente:** mínima fricción; el cliente recibe seguimiento por email/WhatsApp.
- **B. Guest + magic link opcional:** historial y direcciones sin contraseñas.
- **C. Cuentas completas con contraseña:** más control, más superficie de ataque y soporte.

**Recomendación:** B. El personal del comerciante usa Supabase Auth; el comprador compra como invitado y puede reclamar su historial con magic link.

**Impacto si no se decide:** no se puede diseñar el modelo de identidad ni el checkout.

**Bloquea:** ADR-0003, DDL de `customers`, Wave 1 y Wave 4.

**Criterio de cierre:** opción elegida y política de datos personales asociada.

**Decisión (2026-10-21):** **B.** Guest checkout con magic link opcional. El personal del comerciante usa Supabase Auth; el comprador no usa contraseña.

---

## D-05 — Alcance funcional del MVP

**IMPORTANTE — CERRADA (2026-10-21)**

**Contexto:** `multitiendas` ya tiene returns/RMA, bespoke, promociones, envío blindado e IA/WhatsApp. La V2 no los menciona. Portar todo multiplica el tiempo; no portar nada pierde capacidades valiosas.

**Opciones:**

- **A. MVP comercial:** catálogo, variantes, media, carrito, checkout, pagos, órdenes, factura, builder y publish.
- **B. MVP + verticales:** añadir returns, bespoke, promociones y envío blindado.
- **C. MVP + IA:** añadir WhatsApp y gobernanza cognitiva desde el inicio.

**Recomendación:** A. Diferir B y C a fases posteriores, dejando las tablas y feature flags preparados.

**Impacto si no se decide:** no se puede planificar el port ni las olas; el equipo puede intentar abarcar demasiado.

**Bloquea:** `tasks.md`, migración desde `multitiendas`, Wave 2-7.

**Criterio de cierre:** lista cerrada de funcionalidades MVP y lista explícita de diferidas.

**Decisión (2026-10-21):** **A.** MVP comercial. Se difieren returns/RMA, bespoke, promociones, envío blindado, IA/WhatsApp, L402, multi-moneda y dominios custom.

---

## D-06 — Moneda e impuestos

**IMPORTANTE — CERRADA (2026-10-21)**

**Contexto:** el documento asume COP, pero no define si los precios incluyen IVA, cómo se redondea ni cómo se manejan envíos y descuentos.

**Opciones:**

- **A. COP only, IVA 19% incluido en el precio mostrado**, envío plano por zona.
- **B. COP + multi-moneda desde el inicio**, con tabla de tasas y precios por moneda.
- **C. Precios sin impuestos y cálculo en checkout**, estilo B2B.

**Recomendación:** A para el MVP. Guardar siempre centavos y snapshot de precios en `order_items`.

**Impacto si no se decide:** los totales, invoices y reportes pueden ser inconsistentes.

**Bloquea:** DDL de `orders` / `invoices`, checkout y reportes.

**Criterio de cierre:** moneda, tratamiento de IVA, redondeo y política de envío.

**Decisión (2026-10-21):** **A.** COP únicamente. Los precios mostrados incluyen IVA 19%. Se guardan montos en centavos y un snapshot de `subtotal_cents`, `tax_cents`, `shipping_cents` y `total_cents` en la orden, con la tasa aplicada. Envío plano por zona. El total se muestra en pesos enteros, pero el cálculo interno es en centavos. Multi-moneda queda diferido (D-05). Descuentos y promociones quedan fuera del MVP.

**Pendiente derivado:** confirmar con contador el tratamiento de IVA sobre el envío, los redondeos de facturación y que todos los productos del piloto estén gravados al 19%; definir zonas y tarifas de envío.

---

## D-07 — Dominios y TLS

**IMPORTANTE — CERRADA (2026-10-21)**

**Contexto:** el storefront resuelve tenant por host. El MVP puede usar subdominios gestionados o permitir dominios propios desde el día 1.

**Opciones:**

- **A. Solo subdominios `*.growup.com`**, con wildcard TLS.
- **B. Subdominios + dominios custom** con verificación DNS y emisión automática de certificados.
- **C. Dominio único con path por tenant** (`/t/slug`), sin TLS por tenant.

**Recomendación:** A en el MVP; B en fase 3 con Cloudflare for SaaS o Vercel Domains.

**Impacto si no se decide:** no se puede diseñar `domains`, el onboarding ni el middleware.

**Bloquea:** ADR-0003, `domains`, Wave 1.

**Criterio de cierre:** estrategia de dominios y proveedor de TLS.

**Decisión (2026-10-21):** **A.** Subdominios `*.growup.com` con wildcard TLS. Los dominios custom se posponen a fase 3.

**Pendiente derivado:** confirmar proveedor de DNS/TLS (Cloudflare o Vercel) y dominio raíz.

---

## D-08 — Primer tenant y fecha de lanzamiento

**IMPORTANTE — CERRADA (2026-10-21)**

**Contexto:** sin un tenant real y una fecha, el catálogo, el contenido, el QA y el go-live quedan indefinidos.

**Opciones:**

- **A. Piloto con ropa + joyería** (los dos tenants de referencia), lanzamiento interno.
- **B. Solo un tenant** (ropa o joyería) para reducir alcance.
- **C. Tenant externo real** con onboarding asistido.

**Recomendación:** A para validar el motor multi-tenant, con fecha de lanzamiento a confirmar.

**Impacto si no se decide:** no se puede planificar contenido, migración de datos ni aceptación.

**Bloquea:** Wave 3 (contenido), Wave 8 (go-live).

**Criterio de cierre:** tenant(s) piloto, fecha objetivo y responsable de contenido.

**Decisión (2026-10-21):** **A.** Piloto con ropa + joyería. Fecha objetivo: **Q1 2027**.

**Pendiente derivado:** fecha exacta dentro de Q1 2027, responsable de contenido por tenant y criterios de aceptación del piloto.
