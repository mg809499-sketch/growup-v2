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
| 0003 | Identidad y tenancy | Pendiente (D-04, D-07) | — |
| 0004 | Modelo de contenido y publishing | Pendiente | — |
| 0005 | Stack satélite (búsqueda, colas, media, observabilidad) | Pendiente | — |
| 0006 | Motor de reglas y auditoría | Pendiente | — |
| 0007 | Topología de despliegue | Pendiente | — |

## Relación con las decisiones de negocio

Los ADRs técnicos 0003-0007 dependen de las decisiones de negocio [`D-01` a `D-08`](../decisiones-pendientes.md). No se escriben hasta que esas decisiones estén cerradas.
