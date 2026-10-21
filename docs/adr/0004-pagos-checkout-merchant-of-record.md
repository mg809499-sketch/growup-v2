# ADR-0004 — Pagos, checkout y merchant of record

- **Estado:** Aceptada
- **Fecha:** 2026-10-21
- **Decisores:** equipo de ingeniería y producto
- **Relacionado con:** D-01, D-02, D-06 (pendiente), ADR-0003

## Contexto

Growup tiene dos flujos de dinero que no se pueden mezclar:

1. **Plataforma → comerciante:** cobro de la suscripción mensual (D-01).
2. **Comerciante → comprador:** cobro del checkout de cada tienda (D-02).

La decisión D-02 cerró el modelo: **el comerciante es el merchant of record**. Growup usa credenciales por tenant, no custodia fondos y no implementa split de pagos en el MVP. El checkout usa **Wompi** y la suscripción de la plataforma usa **Stripe Billing**.

La decisión D-06 (moneda e impuestos) sigue abierta. Este ADR no fija la política de IVA: los importes se guardan en centavos y se congelan en el snapshot de la orden; el cálculo de impuestos se define en el ADR de datos/comercio cuando D-06 se cierre.

## Decisión

### 1. Separación de dominios

- `commerce/payments`: pagos del comprador al comerciante (Wompi, credenciales por tenant).
- `billing`: suscripción del comerciante a la plataforma (Stripe Billing).
- Tablas, servicios, webhooks y permisos separados. Un fallo en billing no bloquea el checkout de una tienda, y viceversa.

### 2. Merchant of record

- Cada tenant conecta su propia cuenta de Wompi desde el admin (`settings/payments`).
- Growup nunca recibe, retiene ni liquida fondos de las ventas del comerciante.
- El onboarding valida las credenciales con una llamada de prueba y guarda el estado (`pending`, `connected`, `error`).
- Los términos de servicio deben declarar que el comerciante es el vendedor y responsable de la transacción.

### 3. Checkout

- **Wompi Web Checkout** (hosted) en el MVP para minimizar el alcance PCI. El comprador sale a la pasarela y vuelve a la confirmación de la orden.
- La API crea la transacción con un `checkout_idempotency_key` único por intento; reintentos devuelven el mismo pago.
- Importes en centavos (`int`), moneda COP. Prohibido `float`.
- La orden guarda un snapshot inmutable de precios, impuestos y envío.
- Estados de pago: `pending → authorized → paid → refunded / partially_refunded / failed / expired`.
- Estados de orden: `pending_payment → paid → fulfilled → cancelled / refunded`.
- **La única fuente de verdad de "pagado" es el webhook firmado.** El redirect del navegador nunca confirma un pago.
- La reserva de inventario se hace al iniciar el checkout con TTL y se confirma al recibir el webhook `paid`; se libera por expiración o fallo. Esto evita overselling sin confiar en el cliente.

### 4. Webhooks

**Wompi (por tenant):**

- `POST /webhooks/wompi/{webhook_key}` con `webhook_key` no adivinable por tenant.
- Verificar firma con el `events_secret` del tenant, tolerancia de timestamp y `provider_event_id` único.
- Resolver el tenant por `webhook_key` con una función `SECURITY DEFINER` acotada; después `SET LOCAL app.tenant_id`. Nunca confiar solo en el payload.
- Si el monto o la moneda no coinciden con la orden → `PAYMENT_MISMATCH`, revisión manual y **no** se marca como pagada.

**Stripe (plataforma):**

- `POST /webhooks/stripe` con verificación `Stripe-Signature` y el secreto de la cuenta de plataforma.
- El tenant se resuelve desde `metadata.tenant_id` y se valida contra el `stripe_customer_id`.
- Idempotencia por `event.id`.

**Reglas comunes:**

- Guardar `provider_event_id`, tipo, hash del payload y resultado; no guardar PII cruda.
- Replay de un evento no duplica pagos, facturas ni entitlements.
- Eventos desconocidos se registran y se ignoran; no rompen el endpoint.

### 5. Credenciales por tenant

Tabla `tenant_payment_accounts`:

| Campo | Tipo | Nota |
|---|---|---|
| `tenant_id` | uuid | FK, RLS |
| `provider` | text | `wompi` |
| `status` | text | `pending`, `connected`, `error` |
| `provider_account_id` | text | ID público de la cuenta |
| `credentials_encrypted` | bytea | envelope encryption (KMS o Supabase Vault) |
| `webhook_key` | uuid | único, no adivinable |
| `created_at`, `updated_at` | timestamptz | |

- Los secretos nunca se devuelven al cliente ni se escriben en logs.
- Solo el servicio de pagos descifra; el acceso queda auditado.
- Rotación de credenciales soportada sin downtime.

### 6. Suscripción de la plataforma

- Stripe Billing: un `customer` por tenant, suscripción con trial de 14 días, Checkout Session y Customer Portal.
- Tablas: `platform_subscriptions`, `platform_invoices`, `billing_events`.
- Entitlements derivados del estado: `trialing`, `active`, `past_due` (gracia), `canceled` (suspensión de publish tras la gracia).
- Si la entidad legal de Growup no puede operar con Stripe en Colombia, se cambia el adaptador a MercadoPago preapproval sin cambiar el dominio. La decisión de negocio ya autorizó ese respaldo.
- La suscripción se cobra con tarjeta en el MVP. PSE/Nequi para la suscripción queda como pendiente derivado.

### 7. Abstracción de proveedor

```python
class PaymentProvider(Protocol):
    async def create_checkout(...) -> CheckoutResult: ...
    async def verify_webhook(...) -> ProviderEvent: ...
    async def refund(...) -> RefundResult: ...
    async def get_payment(...) -> ProviderPayment: ...
```

- `WompiProvider` y `StripeBillingProvider` implementan el puerto.
- Los payloads específicos viven en los adaptadores; el dominio usa tipos canónicos.
- `Money(amount_cents: int, currency: str)`; nunca `float`.
- Un futuro `MercadoPagoProvider` o un modelo marketplace se añade sin reescribir el checkout.

### 8. Refunds y chargebacks

- En el checkout, el comerciante asume refunds y chargebacks desde su cuenta de Wompi. Growup ofrece la trazabilidad y los enlaces, pero no arbitra ni custodia fondos.
- La plataforma gestiona solo disputas de la suscripción.
- `refunds` guarda `provider_refund_id`, monto, motivo y estado; es idempotente.

### 9. Conciliación

- Job diario por tenant: órdenes pagadas vs transacciones de Wompi; reporte de diferencias.
- Job diario de suscripciones: estado local vs Stripe.
- Las diferencias generan alerta operativa; no se corrigen automáticamente sin regla.

### 10. Cumplimiento

- **PCI DSS:** checkout hosted; Growup no ve PAN/CVV; alcance SAQ A/A-EP según el flujo final.
- **Habeas Data:** minimización de datos de pago, consentimiento y retención documentada.
- **DIAN:** el pago confirmado dispara la solicitud de factura (D-03), pero el estado de la factura es independiente del estado del pago.
- **Términos:** el comerciante es el vendedor; Growup es el proveedor tecnológico.

## Modelo de datos canónico

| Tabla | Propósito | RLS |
|---|---|---|
| `tenant_payment_accounts` | Credenciales y estado por tenant/proveedor | Sí |
| `payments` | Pago del comprador, montos y estado | Sí |
| `payment_events` | Webhooks y eventos del proveedor | Sí |
| `refunds` | Reembolsos del checkout | Sí |
| `platform_subscriptions` | Suscripción del tenant a Growup | Sí |
| `platform_invoices` | Facturas de la suscripción | Sí |
| `billing_events` | Webhooks de Stripe | Sí |

Todas llevan `tenant_id`, `ENABLE` + `FORCE ROW LEVEL SECURITY` y la política `tenant_id = app.current_tenant()`.

## Alternativas consideradas

| Alternativa | Pros | Contras | ¿Por qué no? |
|---|---|---|---|
| A. Credenciales por tenant + Wompi/Stripe (elegida) | Sin custodia, bajo PCI, cobertura local | Dos integraciones y onboarding | Mejor relación riesgo/valor para el MVP |
| B. Marketplace / connected accounts | Split automático y mejor UX | Requiere soporte del proveedor y revisión legal | Se evalúa en fase 2 |
| C. Plataforma merchant of record | Control total del flujo | Custodia de fondos y riesgo regulatorio | No apto para el MVP |
| D. Solo MercadoPago | Una integración | Menor cobertura PSE/Nequi | El usuario prefirió Wompi + Stripe |
| E. Formulario de tarjeta propio | Control de UI | PCI completo y riesgo alto | Prohibido |

## Consecuencias

### Positivas

- Growup no custodia fondos ni asume el riesgo de chargebacks del checkout.
- El alcance PCI se mantiene bajo con checkout hosted.
- La suscripción tiene un proveedor maduro (Stripe Billing) y un respaldo claro.
- La abstracción de proveedor permite añadir marketplace o comisión sin reescribir el dominio.

### Negativas / deuda asumida

- Cada comerciante debe tener cuenta de Wompi y completar el onboarding.
- No hay split automático de comisiones; si se aprueba en fase 2, habrá que migrar a marketplace.
- Dos integraciones y dos conciliaciones.
- Dependencia de la disponibilidad de Stripe para la entidad legal colombiana.
- La conciliación manual es inevitable en el MVP.

### Neutras

- El fee del proveedor se guarda si está disponible, pero no se usa para el precio del MVP.
- La factura DIAN se dispara por pago confirmado, no por el redirect.

## Cómo se verifica

- Firma de webhook válida, inválida y replay; tolerancia de timestamp.
- Un webhook del tenant A no puede actualizar una orden del tenant B.
- Un evento duplicado no duplica pago, factura ni entitlement.
- Un monto distinto al de la orden bloquea el fulfillment y genera alerta.
- Un refund duplicado es idempotente.
- Ciclo de suscripción: `trialing → active → past_due → canceled`.
- Los secretos no aparecen en logs ni en respuestas de la API.
- Tests con proveedores falsos (Wompi y Stripe) y fixtures de Web Checkout.

## Pendientes derivados

- **D-06:** tratamiento de IVA y moneda; afecta el cálculo del monto, no la arquitectura de pagos.
- **D-02-b:** comisión por venta y marketplace; se decide en fase 2.
- Confirmar disponibilidad de Stripe para la entidad legal de Growup.
- Confirmar tarifas y flujo exacto de Wompi Web Checkout.
- Definir si la suscripción acepta PSE/Nequi además de tarjeta.

## Enlaces

- [D-01 y D-02](../decisiones-pendientes.md)
- [ADR-0003](0003-identidad-tenancy-rls.md)
- [Security steering](../../.kiro/steering/security.md)
