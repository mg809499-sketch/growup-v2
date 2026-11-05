# ADR-0009 — Privacidad, DPA, aceptaciones legales y DSR

- **Estado:** Propuesta
- **Fecha:** 2026-10-26
- **Decisores:** Producto, Ingeniería y Legal (revisión pendiente)
- **Relacionado con:** D-09, D-10, D-12, ADR-0003, ADR-0007, ADR-0008

## Contexto

El modelo operativo propuesto es que Growup actúe como **encargado del tratamiento** (*processor*) y el tenant como **responsable** (*controller*) de los datos de compradores. La calificación definitiva depende de los fines, medios, contratos y operación real; requiere revisión legal. El onboarding actual crea el tenant desde un platform admin (`POST /v1/platform/tenants`) y no exige aceptación de un DPA por parte del owner. Tampoco existe un flujo de derechos del titular (DSR), una matriz de retención ni una decisión formal de residencia de datos.

Restricciones existentes:

- `decision_logs` es append-only y sostiene una cadena de hashes; no se puede “limpiar” retroactivamente sin romperla.
- Las facturas electrónicas tienen obligaciones de conservación tributaria.
- El proyecto Supabase aún no se ha creado en producción; la región queda por fijar.
- La aprobación de textos legales requiere abogado; este ADR no sustituye esa revisión.

## Decisión

**Propuesta no aprobada; D-09 y D-10 continúan abiertas.** La opción A es una dirección de diseño, no una autorización para cambiar el onboarding ni procesar datos reales. No se implementan cambios funcionales hasta que se cumplan las compuertas indicadas al final y se registren las decisiones explícitas.

1. **DPA clickwrap por el owner (propuesta).** El tenant permanece sin habilitar publicación/datos reales mientras falte una aceptación vigente requerida. La compuerta de publicación también valida por separado el entitlement de billing; la transición exacta (`pending_legal`, `active`, entitlement) y la regla de gracia de `past_due` deben definirse con billing y probarse en integración.
2. **Documentos y aceptaciones versionados (propuesta).** `legal_documents` conservaría tipo, versión, hash, contenido aprobado y vigencia; `legal_acceptances` vincularía tenant, documento, actor autenticado, instante y método. Esquema, inmutabilidad, evidencia de IP/User-Agent y retención requieren revisión de Legal y minimización. Un hash simple de IP no se considera anonimización.
3. **DSR manual asistido (propuesta).** Recepción, verificación, alcance, análisis por dato, ejecución selectiva, verificación y respuesta segura. El rol `platform:dsr` se limitaría a la tarea autorizada; el mecanismo de ejecución y cualquier `SECURITY DEFINER` requieren revisión de permisos, actor, tenant, transacción e idempotencia antes de implementarse.
4. **Supresión selectiva (propuesta).** No borrar indiscriminadamente filas fiscales ni alterar `decision_logs`. Una matriz aprobada definirá qué campo se suprime, anonimiza, conserva o restringe, por qué, durante cuánto tiempo y qué ocurre en backups y subencargados.
5. **Residencia (pendiente).** La preferencia de una región Supabase y su alineación con cómputo, colas, storage y observabilidad no cierra la decisión: falta confirmar región, proveedores, latencia, transferencias y revisión contractual.
6. **Minimización de auditoría.** `decision_logs` no debe incluir nombres, emails, teléfonos, direcciones ni contenido libre con PII. Usar identificadores seudónimos y `context_summary` allowlist/redactado según ADR-0007.

La plantilla de DPA, roles contractuales, plazos de atención/retención, evidencia, transferencias y región definitiva quedan **pendientes de revisión** antes de cerrar D-09/D-10.

### Flujo propuesto y fail-closed

```text
DPA: legal aprueba texto → publica versión/hash → owner autenticado revisa
  → registra aceptación explícita → verifica evidencia → habilita solo tras compuerta aprobada
  └─ rechazo/fallo/versión vencida → permanece bloqueado y no publica

DSR: recibe → verifica identidad y autoridad → localiza tenant/datos
  → clasifica solicitud por campo + obligación validada
  → suprime/anonimiza/restringe o documenta excepción
  → verifica resultado → responde en plazo aprobado → conserva evidencia mínima
```

Un cambio legal no se resuelve con un despliegue de código: la nueva versión y su transición contractual deben aprobarse primero. Una operación DSR no puede saltarse RLS o usar `service_role` de forma general para facilitar el borrado.

## Alternativas consideradas

| Alternativa | Pros | Contras | ¿Por qué no? |
|---|---|---|---|
| DPA negociable por tenant | Flexibilidad enterprise | Costo legal y operativo alto | Sobredimensionado para el MVP |
| Sin DPA, solo cláusula en ToS | Menor esfuerzo | Suficiencia contractual y legal por validar | No se asume mientras D-09 esté abierta |
| DSR self-service | Escala y menos carga manual | Más superficie y desarrollo | Se prepara para fase 2 |
| Borrado físico total | Simple de explicar | Rompe facturas y cadena de auditoría | Incumple obligaciones tributarias/auditoría |

## Consecuencias

### Positivas

- Evidencia contractual y trazabilidad de aceptación, si el flujo es aprobado e implementado.
- DSR repetible y auditable, compatible con obligaciones confirmadas en la matriz legal.
- Menos PII en logs y auditoría desde el diseño.
- Posible alineación de región tras confirmar infraestructura, transferencias y contratos.

### Negativas / deuda asumida

- El onboarding agrega un paso y un estado nuevo.
- La anonimización requiere diseño por campo y pruebas con datos reales.
- La retención en backups y proveedores externos no es inmediata.
- La revisión legal es un bloqueo real, no un checkbox.

### Neutras

- `legal_acceptances` crece de forma append-only; necesita política de retención propia.

## Cómo se verifica

- Antes de aprobar la propuesta: pruebas pgTAP de RLS A/B, `FORCE RLS`, no bypass, inmutabilidad y falta de contexto; ningún tenant ve aceptaciones ajenas.
- Pruebas de integración: tenant no publica antes de cumplir la compuerta legal y funcional; aceptación duplicada no crea evidencia inconsistente; actor y versión coinciden.
- DSR con datos sintéticos: solicitudes duplicadas, identidad no verificada, cada categoría de retención, anonimización, acceso restringido, fallos parciales y restauración de backup.
- Auditoría: `verify_decision_chain` se mantiene íntegra y no contiene PII; no hay credenciales ni datos de pago en logs.
- Hasta que D-09/D-10 se cierren y estas verificaciones pasen, los flujos se consideran diseño, no control operativo.

## Compuertas para pasar a Aceptada

1. Abogado colombiano aprueba el DPA, roles contractuales, textos, evidencia de aceptación, subencargados y transferencias.
2. Abogado/contador aprueba la matriz por categoría de dato, incluido el requisito provisional de al menos cinco años para órdenes, facturas y `decision_logs`, y confirma fundamento, alcance, inicio del cómputo, anonimización, backups y plazos de atención.
3. Producto registra explícitamente las opciones elegidas para D-09 y D-10, responsable y fecha en el registro de decisiones; la región y proveedores quedan confirmados.
4. Ingeniería implementa los controles y pruebas de esta ADR; la revisión de seguridad valida RLS, privilegios y auditoría.
5. Solo entonces se actualiza estado, migraciones y flujo de publicación. La aprobación de una ADR no sustituye el bloqueo de producción mientras falte evidencia.

## Enlaces

- `docs/decisiones-pendientes (1).md` — D-09, D-10, D-12
- `docs/architecture/03-tenancy.md`
- `supabase/migrations/20261021000200_governance.sql`
- [Flujo de onboarding legal](../legal/flujo-onboarding-legal.svg)
- [Flujo DSR, anonimización y retención](../legal/flujo-dsr.svg)
- [Flujos legales operativos](../legal/flujos.md)
- [Flujos de seguridad](../architecture/04-flujos-seguridad.md)
