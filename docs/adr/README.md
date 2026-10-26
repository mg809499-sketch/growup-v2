# Architecture Decision Records

Registro de decisiones de arquitectura de Growup.

## Formato

Cada ADR vive en un archivo `NNNN-titulo-corto.md` y usa la plantilla [`0000-template.md`](0000-template.md).

Estados posibles:

- **Propuesta** — en discusión.
- **Aceptada** — vigente; guía la implementación.
- **Rechazada** — se conserva para memoria.
- **Reemplazada** — sustituida por otro ADR; se indica cuál.

## Índice

| ADR | Título | Estado | Fecha |
|---|---|---|---|
| [0001](0001-producto-saas-builder.md) | Producto: SaaS multi-tenant con builder | Aceptada | 2026-10-21 |
| [0002](0002-repositorio-y-reutilizacion.md) | Repositorio y reutilización de `multitiendas` | Aceptada | 2026-10-21 |
| [0003](0003-identidad-tenancy-rls.md) | Identidad, tenancy y RLS | Aceptada | 2026-10-21 |
| [0004](0004-pagos-checkout-merchant-of-record.md) | Pagos, checkout y merchant of record | Aceptada | 2026-10-21 |
| [0005](0005-contenido-y-publishing.md) | Modelo de contenido y publishing | Propuesta | 2026-10-21 |
| [0006](0006-stack-satelite.md) | Stack satélite (búsqueda, colas, media, observabilidad) | Aceptada | 2026-10-21 |
| [0007](0007-motor-reglas-auditoria.md) | Motor de reglas y auditoría | Aceptada | 2026-10-21 |
| [0008](0008-topologia-despliegue.md) | Topología de despliegue | Aceptada | 2026-10-21 |
| [0009](0009-privacidad-dpa-dsr.md) | Privacidad, DPA, aceptaciones legales y DSR | Propuesta | 2026-10-26 |
| [0010](0010-checkout-pci-scripts.md) | Checkout hosted, PCI SAQ A y gestión de scripts | Propuesta | 2026-10-26 |
| [0011](0011-email-transaccional.md) | Email transaccional multi-tenant | Propuesta | 2026-10-26 |

## Relación con las decisiones de negocio

Las decisiones [`D-01` a `D-08`](../decisiones-pendientes.md) están cerradas, y D-17/D-18 se cerraron el 2026-10-26. Los ADRs 0001-0008 registran las decisiones técnicas aceptadas. El ADR-0005 queda en **Propuesta** hasta la revisión del modelo de bloques. Los ADR-0009 a 0011 son **Propuesta** y acompañan las decisiones D-09 a D-16, que aún no se consideran cerradas.
