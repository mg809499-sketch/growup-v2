# Steering

Reglas permanentes que Kiro carga en cada sesión. Todas usan `inclusion: always`.

| Archivo | Qué gobierna |
|---|---|
| [`product.md`](product.md) | Qué es Growup, alcance del MVP, principios y métricas |
| [`tech-stack.md`](tech-stack.md) | Stack, convenciones y prohibiciones técnicas |
| [`security.md`](security.md) | Identidad, tenancy, RLS, media, secretos y threat model |
| [`governance.md`](governance.md) | `decide()`, auditoría, pagos y marco de IA |
| [`structure.md`](structure.md) | Mapa del repo, fronteras, naming y dónde va cada cambio |
| [`testing.md`](testing.md) | Pirámide de tests, comandos, evidencia y CI |

## Regla de conflicto

Si dos steering se contradicen, gana el más específico y se documenta la decisión en `docs/adr/`. Si el conflicto es de negocio, se detiene la implementación y se consulta.

## Mantenimiento

- Cambiar una regla permanente requiere PR y justificación.
- No duplicar reglas: si vive en un ADR, el steering solo la referencia.
- Las reglas de seguridad y aislamiento no se relajan para cumplir fechas.
