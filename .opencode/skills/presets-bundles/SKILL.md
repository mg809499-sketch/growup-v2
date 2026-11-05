---
id: presets-bundles
name: presets-bundles
description: Empaquetar estándares regulatorios de forma reutilizable (SOC 2, PCI SAQ-A). Relevante si se va por SOC 2 / PCI SAQ-A (ADR-0010, ADR-0018).
---

# presets-bundles — Estándares regulatorios reutilizables

## Propósito

Definir bundles de controles, evidencias y tests para estándares regulatorios, de modo que un tenant o una ola de cumplimiento pueda adoptarlos como paquete reutilizable en lugar de reconstruirlos desde cero.

## Cuándo se dispara

- Al preparar una ola de cumplimiento (SOC 2, PCI SAQ-A, ISO 27001, etc.).
- Al añadir un nuevo estándar regulatorio al alcance de un tenant.
- Como insumo para `analyze` y `converge` (los controles del bundle se convierten en tareas verificables).

## Bundles definidos

### PCI SAQ-A (basado en ADR-0010)

Controles:
- Checkout redirect hosted (datos de tarjeta fuera del origen de Growup).
- Cero scripts de terceros en `/checkout` (inventario versionado + test que falle si aparece uno).
- CSP estricta en checkout (allowlist origen propio + dominios Wompi confirmados, sin `unsafe-inline`).
- SRI en assets propios y monitoreo de integridad en el borde.
- MFA en accesos administrativos que tocan checkout.
- Ningún dato de tarjeta en logs, Sentry, analytics ni base de datos.
- Webhooks de pago firmados + idempotencia por `webhook_id`.

Evidencia/tests:
- Test de headers: CSP, `X-Frame-Options`, `Referrer-Policy` en `/checkout`.
- Test E2E en sandbox: redirect, pago aprobado, webhook firmado, orden creada.
- Revisión anual de SAQ y evidencia de MFA.

ADR de referencia: `docs/adr/0010-checkout-pci-scripts.md` (Propuesta, 2026-10-26).

### SOC 2 (pendiente / ADR-0018)

Controles (borrador, pendiente de ADR-0018):
- Gestión de cambios y revisión de acceso.
- Monitoreo y respuesta a incidentes.
- Cifrado en tránsito y en reposo.
- Backups con PITR y prueba de restauración.
- Logs de auditoría append-only (`ai_audit_logs`, cadena de integridad `prev_hash` + `hash`).

Evidencia:
- Informe de acceso y cambios.
- Prueba de restauración de backup.
- Verificación de cadena de integridad de auditoría.

ADR de referencia: pendiente (ADR-0018, mencionada en `docs/decisiones-pendientes.md` D-18).

## Estructura de un bundle

Cada bundle vive en `docs/compliance/<estándar>/` y contiene:

- `controles.md` — lista de controles con ID, descripción, severidad, responsable.
- `evidencias.md` — qué pruebas generan cada control (comandos, capturas, logs).
- `tasks.md` — tareas derivadas para implementar/verificar cada control.
- `test/` — tests automatizados que validan el control (si aplica).

## Flujo de adopción

1. Elegir el estándar y el bundle correspondiente.
2. Copiar el bundle como punto de partida para la ola/tenant.
3. `analyze` verifica que las tareas del bundle estén en `tasks.md` y mapeadas a la spec.
4. `converge` ejecuta las evidencias y genera el informe de cumplimiento.
5. `clarify` resuelve ambigüedades de interpretación del estándar antes de implementar.

## Integración con growup

- Se activa solo si se va por SOC 2 / PCI SAQ-A (ADR-0010, ADR-0018); de lo contrario queda como referencia.
- Los webhooks de pago ya requieren firma e idempotencia (regla de gobernanza), lo cual se superpone con el bundle PCI.
- `ai_audit_logs` append-only (gobernanza) alimenta el bundle SOC 2.
