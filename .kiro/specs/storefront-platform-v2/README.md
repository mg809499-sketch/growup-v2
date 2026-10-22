# Storefront Platform V2 — Spec

Spec del MVP comercial de Growup: dos tenants piloto (ropa y joyería), storefront con builder, checkout invitado, pagos Wompi, suscripción Stripe y facturación DIAN.

## Documentos

| Documento | Contenido |
|---|---|
| [`requirements.md`](requirements.md) | Personas, requisitos funcionales, NFRs, fuera de alcance y criterios de aceptación |
| [`design.md`](design.md) | Contenedores, API, dominios, flujos, caché, seguridad y testing |
| [`tasks.md`](tasks.md) | Olas 0-8, tareas, dependencias, estado actual y riesgos |

## Decisiones que la gobiernan

- D-01 a D-08 cerradas en [`docs/decisiones-pendientes.md`](../../../docs/decisiones-pendientes.md).
- ADRs 0001-0008 en [`docs/adr/`](../../../docs/adr/README.md).
- ADR-0005 (contenido/publishing) en **Propuesta** hasta revisión del modelo de bloques.

## Estado actual (2026-10-21)

| Área | Estado |
|---|---|
| Decisiones de negocio | Cerradas |
| ADRs | 0001-0004, 0006-0008 aceptadas; 0005 propuesta |
| Arquitectura | Overview, datos y tenancy documentados |
| Seguridad | JWT/JWKS, host, errores, transacción con `SET LOCAL ROLE app_rw`, memberships/roles, `/v1/admin/me` y 10 vectores cross-tenant automatizados |
| Base de datos | Tenancy + catálogo + gobernanza + inventario + media; 78 tests pgTAP |
| API | `/healthz`, `/readyz`, `/v1/storefront/bootstrap`, `/v1/admin/me`, catálogo admin/storefront, onboarding platform y media admin |
| Catálogo | API base, media upload/worker y asociación producto-media listos; faltan E2E R2, facetas y colecciones |
| Contratos | OpenAPI → TypeScript con check en CI |
| Frontend | Pendiente del export de v0 |
| Catálogo/contenido/comercio | Pendiente (olas 2-4) |

## Próximo hito

**M1:** dos tenants resuelven por host, login admin, onboarding y 12 vectores HTTP en verde.

## Cómo trabajar

1. Leer `requirements.md` y `design.md`.
2. Tomar una tarea de `tasks.md`.
3. Implementar con tests y evidencia.
4. Ejecutar la skill correspondiente si toca tenancy, bloques o pagos.
5. Actualizar `tasks.md` y el ADR/spec si cambió una decisión.
