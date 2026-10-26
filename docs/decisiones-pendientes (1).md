# Decisiones de negocio pendientes

> **Estado:** 10 cerradas (D-03 con proveedor por definir; D-17 y D-18 cerradas el 2026-10-26) · 8 en propuesta (D-09 a D-16, no cerradas) · **Última actualización:** 2026-10-26
> **Regla:** ninguna de estas decisiones se asume en silencio. Cada una se cierra con una respuesta explícita y, cuando aplique, un ADR.
> **Origen de D-09 a D-18 (2026-10-24):** brechas detectadas al comparar la arquitectura con los procesos y la normativa de una plataforma de comercio de referencia (Shopify + PCI-DSS v4.0.1, GDPR Art. 28, CCPA, marketplace facilitator USA, SOC 2). Cubren cumplimiento legal, riesgo de pagos y operación, ejes que las 8 decisiones originales no abordan.
> **Nota (2026-10-26):** D-09 a D-16 se mantienen como propuesta, sujetas a revisión legal, verificación de proveedores y aprobación explícita. D-17 y D-18 se cerraron el 2026-10-26: no hay custodio de fondos ni split en el MVP, y se adopta una postura alineada con SOC 2 sin certificación. Ver “Resolución propuesta y secuencia” al final.

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
| D-09 | DPA processor/controller | **CRÍTICA** | Wave 1 (onboarding), go-live legal | **PROPUESTA** (2026-10-26) |
| D-10 | Derechos del titular y retención de datos | **CRÍTICA** | RLS, auditoría, legal, residencia de datos | **PROPUESTA** (2026-10-26) |
| D-11 | Alcance PCI-DSS v4.0.1 y página de pago | **CRÍTICA** | checkout, seguridad, storefront | **PROPUESTA** (2026-10-26) |
| D-12 | Notificación de brechas (72 h) | **CRÍTICA** | gobernanza, go-live legal | **PROPUESTA** (2026-10-26) |
| D-13 | Política de devolución, reembolso y garantía | **IMPORTANTE** | legal, storefront, checkout | **PROPUESTA** (2026-10-26) |
| D-14 | Fraude y chargebacks: responsabilidad y flujo | **IMPORTANTE** | checkout, pagos, órdenes | **PROPUESTA** (2026-10-26) |
| D-15 | Proveedor de email transaccional y región | **IMPORTANTE** | Wave 4/8, emails de orden | **PROPUESTA** (2026-10-26) |
| D-16 | Soporte al comerciante y SLA | **IMPORTANTE** | operación, producto | **PROPUESTA** (2026-10-26) |
| D-17 | Marketplace facilitator / responsabilidad fiscal | **A CONSIDERAR** | fase 2, impuestos, comisión | **CERRADA** (2026-10-26) |
| D-18 | Vendor risk y objetivo SOC 2 | **A CONSIDERAR** | change management, proveedores | **CERRADA** (2026-10-26) |

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

**Pendiente derivado (2026-10-24):** definir el flujo de **nota crédito** cuando hay refund después de factura emitida. Hoy figura como INV-03 (*Should*) en `requirements.md` pero sin decisión: hay que decidir si el proveedor certificado emite la nota crédito automáticamente o si se resuelve por `HANDOFF` manual (ADR-0007). Se relaciona con D-13 (devoluciones) y D-14 (chargebacks).

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

**Nota de riesgo (2026-10-24):** mientras el pendiente derivado siga abierto, los totales de `orders` e `invoices` pueden quedar inconsistentes (IVA del envío y redondeos sin regla fija). Debe cerrarse antes de la Wave 4 (checkout) para no snapshotear totales con una regla provisional. Para mercados fuera de Colombia, el cálculo multi-jurisdicción queda cubierto por D-17 (marketplace facilitator), no por esta decisión.

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

**Pendiente derivado (2026-10-24):** la elección de proveedor de DNS/TLS y la región de borde se conecta con la **residencia de datos** de D-10. Decidir ambos de forma coherente: dónde terminan el TLS, dónde residen los datos personales y qué implica eso para GDPR/Habeas Data.

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
---

## D-09 — DPA (acuerdo de tratamiento de datos) processor/controller

**CRÍTICA — PROPUESTA (2026-10-26)**

**Contexto:** GDPR Art. 28 y CCPA exigen un contrato escrito entre el encargado del tratamiento (*processor*) y el responsable (*controller*). En Growup, la plataforma es el *processor* y cada tenant es el *controller* de los datos de sus compradores (ya reconocido en el marco legal del documento V2). Hoy no existe decisión sobre si habrá un DPA plantilla, quién lo firma durante el onboarding, cómo se acepta (clickwrap versionado) ni dónde se versiona y audita. Sin DPA, la exposición legal es alta (multas GDPR hasta 4% del *turnover* global o €20M; CCPA hasta USD 7.500 por violación intencional).

**Opciones:**

- **A. DPA plantilla único, aceptado en el onboarding (clickwrap versionado).** El comerciante acepta un DPA estándar al crear el tenant; se guarda versión, timestamp y aceptante. Escala sin fricción.
- **B. DPA negociable por tenant.** Flexible para clientes enterprise, pero caro de operar y versionar.
- **C. Sin DPA explícito, solo cláusula en los ToS.** Mínimo esfuerzo, pero no cumple el requisito de contrato específico de GDPR Art. 28.

**Recomendación:** **A** para el MVP. DPA plantilla aceptado como clickwrap en el onboarding, con registro de versión/fecha/aceptante en una tabla auditable. Reservar B para fase enterprise.

**Impacto si no se decide:** el onboarding de tenants puede quedar sin base legal y el go-live queda bloqueado por riesgo regulatorio.

**Bloquea:** Wave 1 (onboarding), go-live legal, `tenant_settings`/tabla de aceptaciones legales.

**Criterio de cierre:** plantilla de DPA aprobada por legal, mecanismo de aceptación y almacenamiento versionado definido, responsable asignado.

**Nota de propuesta (2026-10-26):** la aceptación debe hacerla el **owner del tenant** en su primer acceso, no el platform admin que crea el tenant. Se requiere estado `pending_legal`, documento versionado con hash y registro append-only; la plantilla y el flujo deben validarse con abogado antes de cerrar.

---

## D-10 — Derechos del titular de datos y retención

**CRÍTICA — PROPUESTA (2026-10-26)**

**Contexto:** CCPA y GDPR otorgan al titular derechos de acceso, borrado (*right to erasure*) y opt-out. Las plataformas de referencia exponen incluso webhooks obligatorios de cumplimiento (p. ej. redacción de datos de cliente y de tienda). Hoy en Growup no hay decisión sobre el flujo de *data-subject request* (DSR), el plazo de borrado, la política de retención ni la **residencia de datos** (la región Supabase/Fly está solo como W0-09, no como decisión formal). Esto toca RLS, la auditoría inmutable (que es *append-only* y no puede simplemente borrarse) y el marco legal.

**Opciones:**

- **A. Flujo DSR manual operado por platform admin + política de retención definida + región única.** El comprador o el tenant solicita; platform admin ejecuta borrado/anonimización con auditoría. Simple para el MVP.
- **B. Flujo DSR self-service** (endpoint/portal) con anonimización automática y webhooks de redacción. Más maduro, más trabajo.
- **C. Posponer** y cubrir solo con política escrita sin implementación. No cumple plazos legales.

**Recomendación:** **A** para el MVP, con diseño preparado para B. Definir: (1) anonimización en lugar de borrado físico donde la auditoría/contabilidad lo exijan; (2) plazos de retención por tipo de dato (orden, factura, logs); (3) una sola región de datos, coherente con D-07.

**Impacto si no se decide:** imposible responder solicitudes legales en plazo; conflicto entre "borrado" y la cadena de auditoría inmutable sin resolver.

**Bloquea:** RLS, auditoría, legal, residencia de datos, W0-09.

**Criterio de cierre:** flujo DSR definido, política de retención por tipo de dato, estrategia de anonimización vs borrado frente a la cadena de auditoría, y región de datos elegida.

**Preferencia registrada (2026-10-26):** una sola región, **la del proyecto Supabase**; cómputo, colas, storage y observabilidad se alinean a esa región. Pendiente crear el proyecto, medir latencia desde Colombia y confirmar disponibilidad de todos los proveedores. La anonimización se diseñará por campo, con retención fiscal separada y sin prometer borrado irreversible en backups.

---

## D-11 — Alcance PCI-DSS v4.0.1 y protección de la página de pago

**CRÍTICA — PROPUESTA (2026-10-26)**

**Contexto:** D-02 establece que los datos de tarjeta nunca tocan Growup (hosted checkout de Wompi), lo que apunta a **SAQ A**. Sin embargo, desde PCI-DSS v4.0.1 (controles obligatorios desde el 31-mar-2025) incluso el checkout delegado exige proteger la página de pago: inventario y gestión de los scripts que corren en el navegador, detección de manipulación (*e-skimming*), MFA en accesos privilegiados y escaneo ASV cuando aplica. Hoy no hay decisión sobre quién es responsable del SAQ, cómo se gestionan los scripts del storefront ni si se corre ASV.

**Opciones:**

- **A. SAQ A estricto con página de pago minimalista.** El storefront no carga scripts de terceros en el flujo de pago; redirect limpio a Wompi. Minimiza superficie y mantiene elegibilidad a SAQ A.
- **B. SAQ A-EP** si el storefront entrega/ejecuta scripts que podrían afectar el pago. Más controles (incluido ASV scan).
- **C. No formalizar el SAQ** y confiar en la pasarela. Incumple el requisito contractual con las marcas.

**Recomendación:** **A.** Mantener el flujo de pago libre de scripts de terceros para preservar SAQ A; establecer un inventario de scripts del storefront con política de aprobación, CSP estricta en el flujo de checkout (ya hay CSP en `/v1`) y un responsable del SAQ anual. Correr ASV si la elegibilidad lo exige.

**Impacto si no se decide:** riesgo de e-skimming en checkout y de incumplimiento del acuerdo con las marcas/pasarela; posible pérdida de elegibilidad a SAQ A.

**Bloquea:** checkout (Wave 4), seguridad, render del storefront (gestión de scripts).

**Criterio de cierre:** nivel de SAQ definido, responsable asignado, política de gestión de scripts de la página de pago y decisión sobre ASV scan.

**Nota de propuesta (2026-10-26):** Wompi todavía no tiene cuenta ni spike técnico. La decisión final se toma **al final de la secuencia**, después de confirmar redirect vs widget, dominios, 3DS y campos de riesgo. Mientras tanto se diseña el checkout sin scripts de terceros y con redirect hosted como opción preferida.

---

## D-12 — Notificación de brechas (72 h)

**CRÍTICA — PROPUESTA (2026-10-26)**

**Contexto:** GDPR y las buenas prácticas de e-commerce exigen notificar una brecha de datos a la autoridad (y, según severidad, a los afectados) dentro de 72 horas. En el modelo processor/controller, Growup (*processor*) debe además notificar a los tenants (*controllers*) para que estos cumplan su propio deber. Hoy no hay decisión formal sobre el protocolo, los plazos internos ni el responsable. Es una decisión de **gobernanza**, no solo un runbook técnico.

**Opciones:**

- **A. Protocolo formal con responsable (DPO/seguridad), SLA interno de detección→notificación y plantillas.** Define cadena de mando, criterios de severidad y canal a tenants y autoridad.
- **B. Solo runbook técnico** sin responsable ni SLA. Insuficiente frente al plazo legal.
- **C. Posponer a fase 2.** Deja el go-live expuesto.

**Recomendación:** **A.** Nombrar responsable, definir SLA interno (p. ej. notificar al tenant dentro de X horas de confirmada la brecha, y a la autoridad dentro de 72 h), y preparar plantillas de notificación. Enlazar con la observabilidad (alertas de 5xx/cadena rota) como disparador de detección.

**Impacto si no se decide:** incumplimiento del plazo legal de 72 h y de la obligación de informar a los tenants.

**Bloquea:** gobernanza, go-live legal, runbooks de Wave 7 (OPS-05).

**Criterio de cierre:** responsable nombrado, SLA de detección→notificación, plantillas y canal a autoridad/tenants definidos.

**Nota de propuesta (2026-10-26):** el plazo de 24 h a tenants es un **objetivo contractual**, no una obligación legal; el plazo ante la SIC y la aplicación de GDPR deben validarse con abogado. El protocolo requiere on-call y detección real (auth, WAF, DB, cadena de auditoría), no solo Sentry.

---

## D-13 — Política de devolución, reembolso y garantía al consumidor

**IMPORTANTE — PROPUESTA (2026-10-26)**

**Contexto:** D-05 difiere returns/RMA como **software** (flujo técnico), pero la **política legal** de reembolso, retracto y garantía es de publicación obligatoria (Estatuto del Consumidor en Colombia; derecho de desistimiento en UE/UK). Es independiente de construir el flujo técnico: la tienda debe exhibir una política clara aunque el proceso se opere manualmente. Hoy no está decidida.

**Opciones:**

- **A. Política plantilla de plataforma + campos editables por tenant**, publicada en el storefront, con valores por defecto conformes a la ley colombiana. Operación manual del reembolso vía pasarela en el MVP.
- **B. Cada tenant redacta su política libremente.** Riesgo de políticas no conformes.
- **C. Sin política publicada.** Incumple la normativa de consumidor.

**Recomendación:** **A.** Plantilla conforme al Estatuto del Consumidor (derecho de retracto, plazos, garantía legal) con campos ajustables por tenant, visible en el storefront y versionada. El flujo técnico de returns sigue diferido (D-05), pero la política y el reembolso manual existen desde el go-live.

**Impacto si no se decide:** tiendas publicadas sin política de devolución conforme; incumplimiento de protección al consumidor.

**Bloquea:** legal, storefront (página de política), checkout (enlace a términos).

**Criterio de cierre:** plantilla aprobada por legal, campos editables definidos, ubicación en el storefront y proceso de reembolso manual del MVP acordado.

**Nota de propuesta (2026-10-26):** la política y la plantilla se pueden cerrar antes que la automatización. Los campos del tenant deben ser acotados (plazos, exclusiones, productos retornables) y la nota crédito queda condicionada al proveedor DIAN de D-03.

---

## D-14 — Fraude y chargebacks: responsabilidad y flujo

**IMPORTANTE — PROPUESTA (2026-10-26)**

**Contexto:** D-02 establece que *refunds* y *chargebacks* los asume el comerciante (merchant of record = tenant), pero no decide si Growup provee herramientas de **screening de fraude** (cola de revisión, señales AVS/CVV, IP/proxy, distancia billing-shipping, velocity), si exige **3DS**, ni cómo se arma la **evidencia de disputa**. Las plataformas de referencia tratan la prevención de fraude y la gestión de disputas como un proceso central de tres capas (pre-compra, reglas en checkout, análisis post-orden). Hoy el tema no aparece en la spec.

**Opciones:**

- **A. Delegar 100% a la pasarela (Wompi) en el MVP.** Growup no implementa scoring propio; se apoya en el 3DS/antifraude de la pasarela y documenta que la disputa la gestiona el comerciante. Mínimo esfuerzo; menor control.
- **B. Capa ligera propia de señales + cola de revisión.** Growup marca órdenes de alto riesgo para revisión del tenant antes de fulfillment, apoyándose en señales básicas. Equilibrio.
- **C. Motor de fraude completo propio.** Máximo control; fuera de alcance razonable para el MVP.

**Recomendación:** **A** para el MVP (apoyarse en el antifraude y 3DS de Wompi; dejar claro en ToS/onboarding que la disputa y el chargeback son del comerciante), con el diseño preparado para añadir B (cola de revisión + señales) en fase 2. Dejar campos para registrar el resultado de la disputa y enlazar con D-03 (nota crédito) y PAY-03 (refunds con `HANDOFF`).

**Impacto si no se decide:** órdenes fraudulentas sin proceso de revisión y disputas sin flujo de evidencia; fricción en el primer chargeback real.

**Bloquea:** checkout (Wave 4), pagos, órdenes, conciliación (PAY-04).

**Criterio de cierre:** nivel de antifraude del MVP elegido, responsabilidad de la disputa documentada, exigencia o no de 3DS, y campos de disputa/evidencia definidos.

**Nota de propuesta (2026-10-26):** 3DS solo aplica a tarjetas y no a PSE/Nequi; los campos de riesgo se guardan solo si Wompi los expone. La cuenta Wompi aún no existe, así que la decisión final se difiere al final de la secuencia.

---

## D-15 — Proveedor de email transaccional y región

**IMPORTANTE — PROPUESTA (2026-10-26)**

**Contexto:** `requirements.md` §7 lista "Proveedor de email y región — por definir" pero sin ID ni sección propia. Los emails transaccionales (confirmación de orden, envío, magic link, dunning, factura) son parte del flujo crítico de Wave 4/8. Sin proveedor no hay ORD-05, CHK-05, AUTH-04 ni BILL-05.

**Opciones:**

- **A. Proveedor transaccional dedicado** (p. ej. Resend, Postmark, SES). Entregabilidad y reputación gestionadas; webhooks de rebote/entrega.
- **B. SMTP propio.** Máximo control; alta carga de reputación/entregabilidad; no recomendado.
- **C. El proveedor del stack** (p. ej. Supabase Auth para magic link) + otro para marketing. Mezcla; definir límites.

**Recomendación:** **A.** Elegir un proveedor transaccional con webhooks de rebote y DKIM/SPF/DMARC configurados, con remitente por tenant o por plataforma según branding. Confirmar región de envío coherente con la residencia de datos (D-10). Separar transaccional de cualquier email de marketing futuro.

**Impacto si no se decide:** no se pueden cerrar los emails de orden/confirmación/magic link ni el dunning; bloquea Wave 4/8.

**Bloquea:** Wave 4/8, ORD-05, CHK-05, AUTH-04, BILL-05.

**Criterio de cierre:** proveedor elegido, configuración DKIM/SPF/DMARC, manejo de rebotes y región definida.

**Dirección registrada (2026-10-26):** se quiere **identidad de envío por tenant**. El diseño debe soportar dominio/subdominio verificado por tenant con DKIM/SPF/DMARC y automatización del onboarding; si el proveedor no permite verificarlo por API, se usa un dominio compartido como fallback temporal. La elección Resend/Postmark queda pendiente de spike. Usar **ARQ**, no Celery.

---

## D-16 — Soporte al comerciante y SLA

**IMPORTANTE — PROPUESTA (2026-10-26)**

**Contexto:** no hay decisión sobre canal de soporte al comerciante, niveles de servicio (SLA) ni base de conocimiento. Las plataformas de referencia consideran el soporte parte del producto, no un extra. En el MVP con dos tenants piloto el soporte puede ser liviano, pero debe existir un canal y expectativas claras antes del go-live.

**Opciones:**

- **A. Canal único de soporte (email/ticket) + SLA básico + FAQ mínima**, operado por el equipo. Suficiente para el piloto.
- **B. Plataforma de ticketing dedicada + SLA por plan.** Escala mejor; sobredimensionado para el MVP.
- **C. Sin canal formal.** Riesgo de abandono del comerciante.

**Recomendación:** **A** para el MVP: un canal de soporte (email o ticket), SLA básico de primera respuesta, y una FAQ/base de conocimiento mínima. Escalar a B cuando crezca el número de tenants. Enlazar con el rol `support` ya existente en AUTH-03.

**Impacto si no se decide:** comerciantes sin ruta de ayuda en el piloto; riesgo reputacional y de churn.

**Bloquea:** operación, producto, go-live del piloto (Wave 8).

**Criterio de cierre:** canal de soporte definido, SLA básico acordado y base de conocimiento mínima publicada.

**Nota de propuesta (2026-10-26):** calibrar el SLA a la capacidad real (horas hábiles y on-call financiado para S1); comprometer respuesta y workaround, no resolución de dependencias externas. El acceso de soporte debe ser temporal, con motivo, consentimiento del tenant y auditoría (W1-07).

---

## D-17 — Marketplace facilitator / responsabilidad fiscal

**A CONSIDERAR — CERRADA (2026-10-26)**

**Contexto:** D-01 y D-02 anticipan que en fase 2 Growup podría cobrar comisión o hacer *split* de pagos (modelo marketplace). En USA, las leyes de *marketplace facilitator* trasladan la obligación de recaudar y remitir impuestos de venta al facilitador cuando este procesa los pagos, y el nexus económico (umbral típico USD 100k / 200 transacciones por estado) determina dónde aplica. Esto cambia **quién remite impuestos**. Aunque no aplica al MVP (merchant of record = comerciante, COP, Colombia), conviene registrar la postura para no decidirlo en silencio en fase 2.

**Opciones:**

- **A. "No aplica en el MVP": el comerciante es responsable fiscal; Growup no es facilitador.** Documentar que, si en fase 2 se adopta comisión/split, se reabre esta decisión con asesoría fiscal USA/CO.
- **B. Diseñar ya para facilitador** (motor de impuestos multi-jurisdicción, nexus, remisión). Sobredimensionado para el MVP.
- **C. No registrar la postura.** Riesgo de asumir el rol de facilitador sin saberlo al introducir el split.

**Recomendación:** **A.** Dejar constancia de que en el MVP Growup no actúa como marketplace facilitator y el comerciante es el responsable fiscal. Marcar explícitamente que la introducción de comisión/split en fase 2 obliga a reabrir esta decisión (motor de impuestos, nexus, remisión) con asesoría fiscal. Se relaciona con D-06 (IVA/impuestos CO).

**Impacto si no se decide:** riesgo de asumir obligaciones de recaudo/remisión al activar el modelo marketplace sin análisis fiscal.

**Bloquea:** fase 2 (comisión/marketplace), impuestos, conciliación.

**Criterio de cierre:** postura del MVP registrada y gatillo de reapertura para fase 2 definido con asesoría fiscal.

**Nota de propuesta (2026-10-26):** se puede registrar la postura del MVP ahora. Cualquier custodia de fondos, split o comisión obliga a reabrir con asesoría fiscal colombiana y, si aplica, análisis de marketplace facilitator en USA.

**Decisión (2026-10-26):** **A.** Growup no actúa como marketplace facilitator ni intermediario fiscal en el MVP. El comerciante es merchant of record y responsable de IVA, facturación y retenciones. Se registra la postura en los ToS y se prohíbe custodia de fondos o split hasta reabrir con asesoría fiscal. **Responsable:** Equipo Growup (producto e ingeniería). **Gatillo de reapertura:** comisión, split o custodia de fondos.

---

## D-18 — Vendor risk y objetivo SOC 2

**A CONSIDERAR — CERRADA (2026-10-26)**

**Contexto:** SOC 2 Type II es hoy un requisito de facto para vender SaaS a clientes enterprise. Decidir si Growup apunta a SOC 2 (y cuándo) define desde ya prácticas que son baratas si se adoptan temprano y caras de retrofittear: gestión de cambios en producción (*change management*), revisión periódica de proveedores (*vendor risk* sobre Wompi, Stripe, Cloudflare R2, Supabase), inventario de activos, respuesta a incidentes y entrenamiento. Los hallazgos típicos de auditoría se concentran justo en acceso, change management y vendor risk.

**Opciones:**

- **A. "SOC 2-ready" desde el MVP sin certificar aún.** Adoptar las prácticas (políticas de cambio, revisión anual de proveedores, inventario, IR) pero diferir la auditoría formal hasta tener demanda enterprise. Bajo costo incremental.
- **B. Perseguir SOC 2 Type II formal ya.** 6-14 meses y costo alto; prematuro para dos tenants piloto.
- **C. No adoptar prácticas.** Retrofit caro y bloqueo comercial futuro.

**Recomendación:** **A.** Operar "SOC 2-ready": política de change management sobre producción, revisión anual de los proveedores críticos (Wompi/Stripe/R2/Supabase) con registro, inventario de activos y proceso de respuesta a incidentes (enlaza con D-12). Diferir la certificación formal hasta que un cliente enterprise la exija. Enlaza con la observabilidad y auditoría ya implementadas.

**Impacto si no se decide:** retrofit costoso de controles y posible bloqueo en procurement enterprise más adelante.

**Bloquea:** change management, gestión de proveedores, madurez para ventas enterprise.

**Criterio de cierre:** decisión sobre objetivo SOC 2 (ready vs certificar vs no), set mínimo de políticas adoptadas y cadencia de revisión de proveedores definida.

**Nota de propuesta (2026-10-26):** adoptar “alineado con SOC 2”, no “certificado”. La matriz de controles y la evidencia deben existir antes de afirmar la postura; OTel aún no está implementado y `decision_logs` es el ledger real (no `ai_audit_logs`).

**Decisión (2026-10-26):** **A.** Adoptar una postura alineada con SOC 2, sin certificación formal. Controles mínimos: change management (PR + CI + revisión + migraciones), acceso con MFA y mínimo privilegio, revisión trimestral de accesos, vendor risk anual (Supabase, Wompi, Stripe, Cloudflare, Fly, R2, Resend), inventario de activos, respuesta a incidentes (D-12), backups con prueba de restauración y evidencia en el repositorio. No se afirmará certificación SOC 2. **Responsable:** Ingeniería/Operaciones. **Gatillo de reapertura:** cliente enterprise que exija auditoría formal.

---

## Resolución propuesta y secuencia (2026-10-26)

D-09 a D-16 **no se cierran** en esta fecha. La opción A se mantiene como dirección recomendada, con estas condiciones:

| ID | Estado propuesto | Condición para cerrar |
|---|---|---|
| D-09 | Propuesta | Abogado + DPA plantilla + aceptación del owner + `legal_acceptances` |
| D-10 | Propuesta | Abogado + matriz de retención + región Supabase + anonimización por campo |
| D-11 | Condicionada | Spike Wompi (redirect/widget, dominios, 3DS); se decide al final |
| D-12 | Propuesta | Abogado/DPO + on-call + detección + plantillas |
| D-13 | Condicionada | Plantilla legal + campos acotados; automatización depende de D-03 |
| D-14 | Condicionada | Verificar 3DS/campos Wompi; retención de PII; cuenta pendiente |
| D-15 | Condicionada | Spike Resend/Postmark + dominio por tenant + DKIM/SPF/DMARC con ARQ |
| D-16 | Condicionada | SLA realista + on-call + acceso de soporte auditado |
| D-17 | **CERRADA** (2026-10-26) | Postura “no facilitador” registrada; reabrir si hay comisión/split/custodia |
| D-18 | **CERRADA** (2026-10-26) | Postura “alineado con SOC 2”; matriz de controles y evidencia en curso |

### Secuencia

**Ahora**
- D-17 (postura) y D-18 (alineación, sin certificar): **cerradas el 2026-10-26**.
- D-16: definir canal y SLA realista; email/shared inbox primero.
- D-15: dirección por tenant y spike de proveedor; ARQ.
- D-11: diseñar checkout sin terceros y con redirect; **no** comprar/integrar Wompi aún.

**Antes de Wave 1 (onboarding)**
- D-09 y D-10 con abogado/DPO.
- W1-07: acceso de soporte temporal y auditado.

**Antes de Wave 4 (checkout)**
- Cerrar el derivado de D-06 (IVA del envío, redondeos y zonas).
- D-11 final, D-13, D-14, D-15 final y D-03 (proveedor DIAN para nota crédito).
- **Wompi al final**: cuenta, spike, webhooks y 3DS.

**Antes de go-live**
- D-12, D-16 final, D-18 evidencia y D-08 (fecha/responsable de contenido).
- ADR-0005 sigue pendiente para contenido/publishing; sin eso no hay storefront ni política publicada.
