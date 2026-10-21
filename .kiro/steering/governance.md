---
inclusion: always
---

# Gobernanza e IA

## Axioma

**La IA recomienda, las reglas deciden.** Un modelo puede interpretar lenguaje natural, proponer una acción o redactar una respuesta; nunca aprueba una mutación sensible.

## Compuerta determinista

- Toda mutación sensible pasa por `decide(policy_id, input) -> Decision`.
- La decisión es binaria y auditable: `ALLOW`, `DENY` o `HANDOFF`.
- Las políticas viven versionadas en el repositorio y se prueban con pytest.
- Si se adopta OPA/Cedar en el futuro, se hace detrás de la misma interfaz.

## Pagos

- Prohibida la aprobación automática por capturas, OCR o texto manual.
- Todo pago se confirma por webhook firmado de la pasarela.
- Replay de un webhook no duplica la factura (idempotencia por `webhook_id`).

## Auditoría

- `ai_audit_logs` es append-only.
- Cada fila guarda `tenant_id`, actor, intent, decisión, razón, latencia y hash del prompt.
- La cadena de integridad usa `prev_hash` + `hash`; un job verifica la cadena.
- Sin PII cruda en los logs.

## IA conversacional

- Solo intents de una allowlist.
- Confianza baja → `HANDOFF` a humano.
- Límites de presupuesto por tenant y por agente antes de producción.
- Circuit breaker con fallback a plantillas estáticas.

## Regla de oro

Si una decisión no se puede explicar sin el modelo, no se puede ejecutar.
