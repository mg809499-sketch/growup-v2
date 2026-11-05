---
id: converge
name: converge
description: Bucle que verifica que lo implementado cumple la spec, en lugar de marcar tareas a mano. Reemplaza la tabla de "Estado/Evidencia" manual por evidencia generada.
---

# converge — Verificación de implementación contra spec

## Propósito

Sustituir el marcado manual de tareas ("Estado/Evidencia") por un bucle de verificación que confirme que lo implementado cumple la spec. Una tarea no se considera completa hasta que hay evidencia generada (tests, lint, typecheck, build, pgTAP).

## Cuándo se dispara

- Al finalizar una tarea o un conjunto de tareas.
- Antes de marcar una tarea como "hecha" en `tasks.md`.
- Como gate de PR/merge ("Sin test no hay merge").

## Entradas

- `tasks.md` con tareas y estados.
- `requirements.md` / `design.md` (spec de referencia).
- Resultados de comandos: `uv run ruff check .`, `uv run mypy app`, `uv run pytest`, `pnpm lint`, `pnpm typecheck`, `pnpm build`, `pnpm dlx supabase test db`.

## Bucle de convergencia

Para cada tarea T:

1. **Identificar evidencias requeridas** según el tipo de cambio:
   - Tabla nueva → RLS A/B, `tenant_id`, USING/WITH CHECK, índice, pgTAP.
   - Endpoint de tenant → token válido, mismatch, rol insuficiente, recurso ajeno.
   - Checkout → idempotencia, stock, monto, webhook firmado, replay.
   - Publish → schema inválido, versión inmutable, rollback, purga.
   - Bloque → props inválidas, XSS, alt text, fallback, a11y.
   - Dinero → centavos, redondeo, snapshot de totales.
   - Migración → `supabase db reset` + pgTAP + expand/contract.

2. **Ejecutar los comandos de verificación** correspondientes y capturar salida.

3. **Comparar contra la spec:** ¿la implementación cubre el requisito de `requirements.md` asociado a T?

4. **Veredicto por tarea:**
   - `VERIFICADO`: tests pasan, lint/mypy/typecheck/build en verde, evidencia adjunta.
   - `FALLÓ`: algún comando falló o falta evidencia. La tarea NO se marca como hecha.
   - `BLOQUEADA`: depende de una ambigüedad sin resolver (ver `clarify`).

5. **Actualizar `tasks.md`** solo con el veredicto `VERIFICADO`, adjuntando comando ejecutado y resultado.

## Salida

- Informe por tarea: ID, estado, veredicto, comando ejecutado, resultado, brechas.
- Tabla de "Estado/Evidencia" generada (no manual): cada fila tiene comando + resultado + hash de evidencia cuando corresponda.
- Lista de tareas que no pueden cerrarse por falta de evidencia.

## Integración con growup

- Reemplaza la tabla manual de Definition of Done por evidencia ejecutable.
- Se ejecuta en CI: ruff, mypy, pytest con Postgres real; frontend: lint, typecheck, build.
- Si el cambio toca aislamiento de tenants → ejecutar `tenant-isolation-check`.
- Si toca bloques/contenido → ejecutar `block-review`.
- Si toca pagos/webhooks → ejecutar `payment-webhook-review`.
