# Skills

Checks reutilizables para tareas de alto riesgo. Cada skill vive en su carpeta y se carga desde `SKILL.md`.

| Skill | Cuándo usarla | Evidencia que exige |
|---|---|---|
| [`tenant-isolation-check`](tenant-isolation-check/SKILL.md) | Cambios de RLS, tenancy, JWT, webhooks, caché o media | pgTAP + integración + 12 vectores |
| [`block-review`](block-review/SKILL.md) | Bloques, temas, builder, publish o preview | Schema cerrado + XSS + a11y + LCP |
| [`payment-webhook-review`](payment-webhook-review/SKILL.md) | Wompi, Stripe, DIAN, checkout, refunds, billing | Firma + replay + tenant + monto |

## Regla

Una skill no reemplaza los tests: los orquesta y exige evidencia. Si el check falla, no se mergea.
