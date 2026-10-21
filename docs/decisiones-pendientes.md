# Decisiones de negocio pendientes

> **Estado:** abierto · **Última actualización:** 2026-10-21
> **Regla:** ninguna de estas decisiones se asume en silencio. Cada una se cierra con una respuesta explícita y, cuando aplique, un ADR.

## Resumen

| ID | Decisión | Prioridad | Bloquea | Estado |
|---|---|---|---|---|
| D-01 | Modelo de cobro a comerciantes | **IMPORTANTE** | `design.md`, admin, onboarding | Pendiente |
| D-02 | Pasarela de pagos del MVP | **IMPORTANTE** | checkout, webhooks, conciliación | Pendiente |
| D-03 | Facturación electrónica DIAN | **IMPORTANTE** | invoices, flujo post-pago, legal | Pendiente |
| D-04 | Cuentas de cliente | **IMPORTANTE** | auth, RLS, checkout | Pendiente |
| D-05 | Alcance funcional del MVP | **IMPORTANTE** | port desde `multitiendas`, olas | Pendiente |
| D-06 | Moneda e impuestos | **IMPORTANTE** | precios, invoices, reportes | Pendiente |
| D-07 | Dominios y TLS | **IMPORTANTE** | tenancy, onboarding | Pendiente |
| D-08 | Primer tenant y fecha de lanzamiento | **IMPORTANTE** | contenido, QA, go-live | Pendiente |

## Protocolo para cerrar una decisión

1. Elegir una opción.
2. Escribir la respuesta en la sección **Decisión** de este documento, con fecha y responsable.
3. Si cambia la arquitectura, crear o actualizar un ADR en `docs/adr/`.
4. Actualizar `.kiro/steering/` si la decisión afecta reglas permanentes.
5. Cambiar el estado a **CERRADA**.

---

## D-01 — Modelo de cobro a comerciantes

**IMPORTANTE — PENDIENTE**

**Contexto:** el documento V2 describe un SaaS con builder, pero no define cómo paga el comerciante por la plataforma. Sin esto no existen `plans`, `subscriptions`, trials, suspensión por impago ni métricas de negocio.

**Opciones:**

- **A. Suscripción mensual por plan** (Starter / Pro), con trial de 14 días. Ingreso predecible; requiere definir límites por plan (productos, dominios, storage, usuarios).
- **B. Comisión por venta** (porcentaje del GMV). Alinea incentivos, pero exige conciliación con la pasarela y reportes por tenant.
- **C. Híbrido:** suscripción base + comisión por ventas altas o add-ons (dominio custom, storage extra).

**Recomendación:** A para el MVP (0% comisión), con la estructura de datos preparada para C. El precio se define después con costos reales de infraestructura.

**Impacto si no se decide:** no se puede diseñar el admin de facturación, el onboarding ni la suspensión de tenants.

**Bloquea:** `design.md`, `apps/admin`, tablas `plans` / `subscriptions` / `usage`.

**Criterio de cierre:** plan elegido, límites por plan y política de trial/impago.

**Decisión:** _(pendiente)_

---

## D-02 — Pasarela de pagos del MVP

**IMPORTANTE — PENDIENTE**

**Contexto:** el checkout necesita una pasarela con webhooks firmados, tokenización y conciliación. El documento menciona Wompi, MercadoPago y Stripe sin elegir.

**Opciones:**

- **A. Wompi** (Colombia): fuerte en COP, PSE y Nequi; integración directa.
- **B. MercadoPago** (LatAm): cobertura regional, checkout y suscripciones.
- **C. Stripe** (internacional): mejor DX, pero menor penetración local y otro contrato.

**Recomendación:** Wompi para el MVP en Colombia y MercadoPago como segunda opción. Stripe solo si hay ventas internacionales.

**Impacto si no se decide:** no se puede implementar `payments`, webhooks ni conciliación.

**Bloquea:** Wave 4 (checkout/pagos), DDL de `payments` y `webhook_events`.

**Criterio de cierre:** pasarela principal, pasarela de respaldo y proveedor de suscripciones (si aplica).

**Decisión:** _(pendiente)_

---

## D-03 — Facturación electrónica DIAN

**IMPORTANTE — PENDIENTE**

**Contexto:** en Colombia la factura electrónica es obligatoria y requiere CUFE, QR y validación ante la DIAN. Construirlo desde cero es un proyecto en sí mismo.

**Opciones:**

- **A. Proveedor certificado** (Factus, Siigo, Alegra u otro): API de emisión, menor riesgo legal.
- **B. Integración directa con la DIAN:** control total, pero alto costo de mantenimiento y certificación.
- **C. Emisión manual fuera de la plataforma:** simple, pero rompe la promesa de "facturación incluida".

**Recomendación:** A. El backend guarda `electronic_ref` y el PDF, pero delega la emisión al proveedor.

**Impacto si no se decide:** no se puede cerrar el flujo de orden pagada → factura.

**Bloquea:** `invoices`, Wave 4, cumplimiento legal.

**Criterio de cierre:** proveedor elegido, contrato/API key y flujo de reintentos definido.

**Decisión:** _(pendiente)_

---

## D-04 — Cuentas de cliente

**IMPORTANTE — PENDIENTE**

**Contexto:** el documento no define si el comprador final tiene cuenta, si compra como invitado o si usa magic link. Esto cambia auth, RLS, checkout y soporte.

**Opciones:**

- **A. Guest checkout solamente:** mínima fricción; el cliente recibe seguimiento por email/WhatsApp.
- **B. Guest + magic link opcional:** historial y direcciones sin contraseñas.
- **C. Cuentas completas con contraseña:** más control, más superficie de ataque y soporte.

**Recomendación:** B. El personal del comerciante usa Supabase Auth; el comprador compra como invitado y puede reclamar su historial con magic link.

**Impacto si no se decide:** no se puede diseñar el modelo de identidad ni el checkout.

**Bloquea:** ADR-0003, DDL de `customers`, Wave 1 y Wave 4.

**Criterio de cierre:** opción elegida y política de datos personales asociada.

**Decisión:** _(pendiente)_

---

## D-05 — Alcance funcional del MVP

**IMPORTANTE — PENDIENTE**

**Contexto:** `multitiendas` ya tiene returns/RMA, bespoke, promociones, envío blindado e IA/WhatsApp. La V2 no los menciona. Portar todo multiplica el tiempo; no portar nada pierde capacidades valiosas.

**Opciones:**

- **A. MVP comercial:** catálogo, variantes, media, carrito, checkout, pagos, órdenes, factura, builder y publish.
- **B. MVP + verticales:** añadir returns, bespoke, promociones y envío blindado.
- **C. MVP + IA:** añadir WhatsApp y gobernanza cognitiva desde el inicio.

**Recomendación:** A. Diferir B y C a fases posteriores, dejando las tablas y feature flags preparados.

**Impacto si no se decide:** no se puede planificar el port ni las olas; el equipo puede intentar abarcar demasiado.

**Bloquea:** `tasks.md`, migración desde `multitiendas`, Wave 2-7.

**Criterio de cierre:** lista cerrada de funcionalidades MVP y lista explícita de diferidas.

**Decisión:** _(pendiente)_

---

## D-06 — Moneda e impuestos

**IMPORTANTE — PENDIENTE**

**Contexto:** el documento asume COP, pero no define si los precios incluyen IVA, cómo se redondea ni cómo se manejan envíos y descuentos.

**Opciones:**

- **A. COP only, IVA 19% incluido en el precio mostrado**, envío plano por zona.
- **B. COP + multi-moneda desde el inicio**, con tabla de tasas y precios por moneda.
- **C. Precios sin impuestos y cálculo en checkout**, estilo B2B.

**Recomendación:** A para el MVP. Guardar siempre centavos y snapshot de precios en `order_items`.

**Impacto si no se decide:** los totales, invoices y reportes pueden ser inconsistentes.

**Bloquea:** DDL de `orders` / `invoices`, checkout y reportes.

**Criterio de cierre:** moneda, tratamiento de IVA, redondeo y política de envío.

**Decisión:** _(pendiente)_

---

## D-07 — Dominios y TLS

**IMPORTANTE — PENDIENTE**

**Contexto:** el storefront resuelve tenant por host. El MVP puede usar subdominios gestionados o permitir dominios propios desde el día 1.

**Opciones:**

- **A. Solo subdominios `*.cordiasolve.com`**, con wildcard TLS.
- **B. Subdominios + dominios custom** con verificación DNS y emisión automática de certificados.
- **C. Dominio único con path por tenant** (`/t/slug`), sin TLS por tenant.

**Recomendación:** A en el MVP; B en fase 3 con Cloudflare for SaaS o Vercel Domains.

**Impacto si no se decide:** no se puede diseñar `domains`, el onboarding ni el middleware.

**Bloquea:** ADR-0003, `domains`, Wave 1.

**Criterio de cierre:** estrategia de dominios y proveedor de TLS.

**Decisión:** _(pendiente)_

---

## D-08 — Primer tenant y fecha de lanzamiento

**IMPORTANTE — PENDIENTE**

**Contexto:** sin un tenant real y una fecha, el catálogo, el contenido, el QA y el go-live quedan indefinidos.

**Opciones:**

- **A. Piloto con ropa + joyería** (los dos tenants de referencia), lanzamiento interno.
- **B. Solo un tenant** (ropa o joyería) para reducir alcance.
- **C. Tenant externo real** con onboarding asistido.

**Recomendación:** A para validar el motor multi-tenant, con fecha de lanzamiento a confirmar.

**Impacto si no se decide:** no se puede planificar contenido, migración de datos ni aceptación.

**Bloquea:** Wave 3 (contenido), Wave 8 (go-live).

**Criterio de cierre:** tenant(s) piloto, fecha objetivo y responsable de contenido.

**Decisión:** _(pendiente)_
