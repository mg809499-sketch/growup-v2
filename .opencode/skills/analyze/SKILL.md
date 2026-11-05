---
id: analyze
name: analyze
description: Chequeo de consistencia cruzada spec ↔ plan ↔ tasks. Detecta desincronizaciones entre requirements.md, design.md, plan y tasks.md que nada detecta hoy.
---

# analyze — Consistencia cruzada spec ↔ plan ↔ tasks

## Propósito

Detectar que `tasks.md` (o el plan de trabajo) no se desincronicen de `requirements.md` (spec) y `design.md`. Hoy nada lo verifica; esta skill lo hace explícito.

## Cuándo se dispara

- Antes de cerrar un sprint o un conjunto de tareas.
- Al añadir, modificar o eliminar una tarea en `tasks.md`.
- Cuando `requirements.md` o `design.md` cambian.
- Como paso de CI/revisión de PR.

## Entradas

- `docs/decisiones-pendientes.md` (criterios de cierre y qué bloquea cada decisión).
- Los archivos de spec de la feature: `requirements.md`, `design.md`, `tasks.md`, `plan.md` (según existan bajo `.kiro/specs/<feature>/` o equivalente).
- ADRs relacionados en `docs/adr/`.

## Reglas de consistencia

| Relación | Qué verificar |
|---|---|
| spec → tasks | Cada requisito funcional de `requirements.md` debe tener al menos una tarea en `tasks.md` que lo cubra. |
| tasks → spec | Cada tarea en `tasks.md` debe mapearse a un requisito de `requirements.md` o a un criterio de cierre de una decisión. No hay tareas huérfanas. |
| design → tasks | Cada decisión de diseño en `design.md` que implique código debe tener una tarea de implementación o de test. |
| decisiones → tasks | Cada decisión de negocio "CERRADA" con campo "Bloquea" debe tener las tareas correspondientes creadas o planificadas. |
| tests → tasks | Cada tabla nueva, endpoint, bloque o flujo de checkout debe tener su test obligatorio (ver testing.md). |

## Pasos

1. Cargar `requirements.md` y extrair requisitos funcionales (IDs R-xx o bullets).
2. Cargar `tasks.md` y extrair tareas con IDs y estado.
3. Construir matriz de trazabilidad requisito ↔ tarea.
4. Reportar:
   - **Requisitos sin tarea:** funcionalidad especificada pero no planificada.
   - **Tareas sin requisito:** trabajo sin cobertura en spec (posible scope creep).
   - **Diseño sin tarea:** decisiones de `design.md` no traducidas a código/test.
   - **Decisiones bloqueando sin tarea:** D-xx con "Bloquea" sin tareas asociadas.
5. Evidencia: salida en formato tabla (ID requisito, título, tarea(s), estado, brecha).

## Salida

- Informe de consistencia con las cuatro categorías de brecha.
- Recomendación: crear tareas, actualizar spec, o cerrar tareas sobrantes.
- Si hay bloqueos críticos (requisito del MVP sin tarea), marcar la feature como "no lista para implementar".

## Integración con growup

- Se ejecuta antes de `uv run ruff check .`, `uv run mypy app`, `uv run pytest`, `pnpm lint`, `pnpm typecheck`, `pnpm build` como gate de planificación.
- Alinea con el Definition of Done: la evidencia deja de ser manual porque se deriva del trazado spec↔tasks.
