---
name: payment-webhook-review
description: Revisa webhooks de pago (Wompi, Stripe, DIAN) para firma, replay, idempotencia, resolución de tenant, monto/moneda, máquina de estados y conciliación. Úsala al crear o modificar webhooks, checkout, refunds o billing.
---

# Payment Webhook Review

## Objetivo

Garantizar que un pago solo se confirma por un webhook firmado, que un replay no duplica efectos y que un evento del tenant A no puede mutar datos del tenant B.

## Cuándo usarla

- Nuevo webhook o cambio de firma.
- Cambio en checkout, payment intent, refund o suscripción.
- Cambio en la máquina de estados de pago/orden.
- Cambio en conciliación o reintentos.

## Checklist

### Firma y autenticidad

- [ ] Se verifica la firma del proveedor con el secreto correcto.
- [ ] Se valida el timestamp (tolerancia corta) cuando el proveedor lo soporta.
- [ ] Se rechaza firma inválida, ausente o algoritmo inesperado.
- [ ] No se confía en el redirect del navegador para confirmar el pago.

### Tenant y aislamiento

- [ ] Wompi: el tenant se resuelve por `webhook_key` no adivinable, no por el payload.
- [ ] Stripe: el tenant se resuelve por `metadata.tenant_id` y se valida contra `stripe_customer_id`.
- [ ] La transacción ejecuta `SET LOCAL ROLE app_rw` + `app.tenant_id`.
- [ ] Un `webhook_key` de B no puede actualizar una orden de A.
- [ ] El evento se registra con `tenant_id` correcto.

### Idempotencia y replay

- [ ] `provider_event_id` es único por tenant/proveedor.
- [ ] Un evento duplicado devuelve 200 sin duplicar pago, factura ni email.
- [ ] El procesamiento es transaccional o usa outbox.
- [ ] Los reintentos son seguros.

### Monto y estado

- [ ] Se compara monto y moneda con la orden; mismatch → `PAYMENT_MISMATCH` y no fulfillment.
- [ ] La orden solo pasa a `paid` con el webhook confirmado.
- [ ] La reserva de stock se confirma una sola vez.
- [ ] Refund es idempotente y registra `provider_refund_id`.
- [ ] `HANDOFF` para refunds sobre umbral.

### Secretos y observabilidad

- [ ] Credenciales por tenant cifradas; nunca en logs ni respuestas.
- [ ] No se loguea PAN, CVV, tokens ni payload completo.
- [ ] `trace_id` y `tenant_id` en el evento.
- [ ] Alerta si fallan webhooks o si la conciliación detecta diferencias.

### Tests

- [ ] Firma válida, inválida y replay.
- [ ] Evento de A con key de B → rechazado.
- [ ] Monto distinto → no fulfillment.
- [ ] Pago duplicado no duplica factura/email.
- [ ] Refund duplicado no duplica reembolso.
- [ ] Suscripción `trialing → active → past_due → canceled`.

## Comandos

```bash
cd services/api
uv run pytest tests/domains/payments tests/domains/billing tests/integration
uv run ruff check .
uv run mypy app
```

## Salida esperada

```text
PAYMENT WEBHOOK REVIEW: PASS | FAIL
- Proveedor: <wompi | stripe | dian>
- Firma: <evidencia>
- Tenant: <resolución + test>
- Idempotencia: <test>
- Monto/estado: <test>
- Secretos: <revisión>
- Conciliación: <job/alerta>
```

Sin firma, sin idempotencia o con tenant resuelto por payload: FAIL.
