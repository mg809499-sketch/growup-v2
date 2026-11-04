# ADR-0009 — Privacidad, DPA, aceptaciones legales y DSR

- **Estado:** Propuesta
- **Fecha:** 2026-10-26
- **Decisores:** Producto, Ingeniería y Legal (revisión pendiente)
- **Relacionado con:** D-09, D-10, D-12, ADR-0003, ADR-0007, ADR-0008

## Contexto

Growup es **encargado del tratamiento** (*processor*) de los datos de compradores y el tenant es **responsable** (*controller*). El onboarding actual crea el tenant desde un platform admin (`POST /v1/platform/tenants`) y no exige aceptación de un DPA por parte del owner. Tampoco existe un flujo de derechos del titular (DSR), una matriz de retención ni una decisión formal de residencia de datos.

Restricciones existentes:

- `decision_logs` es append-only y sostiene una cadena de hashes; no se puede “limpiar” retroactivamente sin romperla.
- Las facturas electrónicas tienen obligaciones de conservación tributaria.
- El proyecto Supabase aún no se ha creado en producción; la región queda por fijar.
- La aprobación de textos legales requiere abogado; este ADR no sustituye esa revisión.

## Decisión

Se propone adoptar la opción A de D-09 y D-10, con estos ajustes:

1. **DPA clickwrap por el owner.** El platform admin crea el tenant en estado `pending_legal`. El owner recibe un magic link, inicia sesión y acepta el DPA y los términos de la plataforma. Hasta entonces el tenant no se activa ni publica storefront.
2. **Documentos y aceptaciones versionados.** `legal_documents` guarda tipo, versión, hash, contenido inmutable y vigencia. `legal_acceptances` guarda tenant, documento, actor, fecha, método e IP **hasheada**; es append-only y tiene RLS por tenant.
3. **DSR manual asistido.** Un platform admin con permiso `platform:dsr` ejecuta la solicitud con motivo y auditoría. La operación se implementa como función `SECURITY DEFINER` con actor check, idempotente y transaccional.
4. **Anonimización/pseudonimización, no borrado indiscriminado.** Se eliminan o pseudonimizan datos de cliente y direcciones; se conserva la información fiscal mínima de órdenes/facturas con acceso restringido. No se promete borrado inmediato en backups ni en logs históricos.
5. **Residencia única.** La región del proyecto Supabase es la región de referencia; cómputo, colas, storage y observabilidad se alinean a ella. Se mide latencia desde Colombia antes de crear producción.
6. **Sin PII en auditoría.** `decision_logs` no debe contener nombres, emails, teléfonos ni direcciones; `actor_id` se mantiene pseudónimo y `context_summary` pasa por `redact()`.

La plantilla de DPA, los plazos de retención y la región definitiva quedan **pendientes de revisión legal** antes de cerrar D-09/D-10.

## Alternativas consideradas

| Alternativa | Pros | Contras | ¿Por qué no? |
|---|---|---|---|
| DPA negociable por tenant | Flexibilidad enterprise | Costo legal y operativo alto | Sobredimensionado para el MVP |
| Sin DPA, solo cláusula en ToS | Menor esfuerzo | No cumple contrato específico de encargado | Riesgo regulatorio |
| DSR self-service | Escala y menos carga manual | Más superficie y desarrollo | Se prepara para fase 2 |
| Borrado físico total | Simple de explicar | Rompe facturas y cadena de auditoría | Incumple obligaciones tributarias/auditoría |

## Consecuencias

### Positivas

- Evidencia contractual y trazabilidad de aceptación.
- DSR repetible, auditado y compatible con obligaciones fiscales.
- Menos PII en logs y auditoría desde el diseño.
- Región coherente con el resto de la infraestructura.

### Negativas / deuda asumida

- El onboarding agrega un paso y un estado nuevo.
- La anonimización requiere diseño por campo y pruebas con datos reales.
- La retención en backups y proveedores externos no es inmediata.
- La revisión legal es un bloqueo real, no un checkbox.

### Neutras

- `legal_acceptances` crece de forma append-only; necesita política de retención propia.

## Cómo se verifica

- pgTAP: RLS A/B en `legal_acceptances`; append-only; ningún tenant ve aceptaciones ajenas.
- Integración: tenant no activo hasta aceptación; aceptación idempotente; auditoría con actor correcto.
- DSR: prueba con un cliente de prueba, verificación de anonimización y conservación de factura.
- Auditoría: `verify_decision_chain` sigue en verde y `decision_logs` no contiene PII.

## Enlaces

- `docs/decisiones-pendientes (1).md` — D-09, D-10, D-12
- `docs/architecture/03-tenancy.md`
- `supabase/migrations/20261021000200_governance.sql`
- [Flujo de onboarding legal](../legal/flujo-onboarding-legal.svg)
- [Flujo DSR, anonimización y retención](../legal/flujo-dsr.svg)
