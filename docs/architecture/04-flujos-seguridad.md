# Flujos de seguridad de extremo a extremo

> **Estado:** diseño objetivo; no acredita que los controles estén desplegados.
> Complementa [tenancy y threat model](03-tenancy.md), ADR-0003, ADR-0004 y ADR-0009.
> Toda ruta que no pueda demostrar su contexto o autorización falla cerrada.

## 1. Petición de tenant y contexto RLS

```mermaid
sequenceDiagram
    autonumber
    actor C as Cliente o staff
    participant E as Borde confiable
    participant A as API
    participant I as IdP/JWKS
    participant D as PostgreSQL
    C->>E: HTTPS + Host
    E->>A: Host normalizado; elimina headers internos entrantes
    A->>A: Host → domains → tenant_id
    opt Ruta autenticada
        A->>I: Verificar firma JWKS, iss, aud, exp, nbf
        I-->>A: Claims verificados
        A->>A: Confirmar membership activa y tenant del actor
        A->>A: Host/tenant/claim deben ser compatibles
    end
    A->>D: BEGIN + SET LOCAL ROLE app_rw
    A->>D: SET LOCAL app.tenant_id al tenant resuelto
    D->>D: FORCE RLS + USING/WITH CHECK
    D-->>A: Solo filas autorizadas; sin contexto, cero acceso
    A-->>C: Respuesta sin datos de otro tenant
```

### Contrato de confianza

1. El `Host` se normaliza y se resuelve contra un dominio registrado. Los headers de tenant enviados por el cliente nunca determinan el tenant. Si un proxy añade un header interno, debe eliminar cualquier valor entrante y el backend debe aceptar ese valor solo desde el proxy autenticado.
2. En rutas privadas se verifica el JWT con JWKS y se valida la membresía vigente desde la fuente de autorización definida por ADR-0003. Un JWT válido por sí solo no autoriza el tenant.
3. La aplicación establece el rol y `app.tenant_id` dentro de la misma transacción; no usa `SET` de sesión. Cada tabla de negocio aplica `ENABLE` y `FORCE ROW LEVEL SECURITY`, `USING` y `WITH CHECK`.
4. `app_rw` no tiene `BYPASSRLS`. `service_role` queda fuera de las peticiones normales de API; toda excepción administrativa debe ser acotada, auditada, justificada y probada.
5. IDs aportados por el cliente se consultan dentro del tenant ya establecido. Una fila ajena responde como inexistente (`404`) cuando sea apropiado, sin revelar su existencia.
6. La respuesta pública solo puede contener datos expresamente publicados. Errores de host, JWT, membresía, contexto o DB no degradan a un tenant predeterminado.

## 2. Caché, media y trabajos asíncronos

```text
Render público ─► resolver Host ─► tenant + versión publicada
                └► cache key = tenant_id + host canónico + recurso + versión

Upload ─► autorización tenant ─► clave generada tenant/{id}/... ─► URL breve
       ─► verificación posterior de bytes/MIME/tamaño/dimensiones
       ─► procesamiento aislado ─► estado ready solo al completar controles

Outbox/job ─► tenant_id persistido ─► validar pertenencia del recurso
           ─► transacción RLS con SET LOCAL ─► ejecutar y auditar resultado
```

- Nunca formar una clave de caché solo con URL/path si la respuesta depende del tenant. No cachear PII ni respuestas autenticadas en una caché pública compartida. Invalidar por tenant y versión al publicar.
- Las claves de R2 se generan en servidor; el nombre original no define el path. La URL prefirmada tiene TTL corto, permiso mínimo y límites de método, tipo y tamaño. El worker vuelve a verificar el objeto: el `Content-Type` del navegador no es evidencia.
- Limitar bytes, dimensiones, píxeles descomprimidos, tiempo de decodificación y concurrencia. Rechazar formatos no permitidos, escanear documentos permitidos contra malware y fallar con estado no publicable; no exponer archivos hasta completar el procesamiento.
- Los jobs contienen un `tenant_id` explícito, pero no se confía en él sin validar que el recurso pertenece a ese tenant. No reutilizar contexto de conexión o worker entre tenants.

## 3. Checkout, inventario y webhooks

```mermaid
sequenceDiagram
    autonumber
    actor B as Comprador
    participant A as API
    participant D as PostgreSQL
    participant P as Pasarela
    participant W as Worker/outbox
    B->>A: Checkout + clave de idempotencia
    A->>D: Resolver tenant; recalcular precios y stock
    A->>D: Reservar stock atómicamente con TTL
    A->>P: Crear checkout hosted con monto/moneda del servidor
    P-->>B: Redirección a checkout hosted
    P->>A: Webhook firmado
    A->>A: Resolver cuenta/tenant y verificar firma + ventana temporal
    A->>D: Reclamar provider_event_id una sola vez
    A->>D: Verificar tenant, orden, monto, moneda y estado
    A->>D: Confirmar pago + reserva en una transacción
    A->>W: Outbox para factura/email/conciliación
```

- El redirect del navegador nunca confirma pago. Los secretos de webhook y las credenciales se obtienen del almacén seguro por cuenta; no se aceptan identidad de tenant o estado de pago basados solo en el payload.
- Usar checkout hosted; Growup no recibe ni almacena PAN/CVV. Mantener el dominio de billing de la plataforma separado del pago comprador→comerciante.
- La firma se verifica sobre el cuerpo exacto requerido por el proveedor y su esquema vigente; validar timestamp/ventana cuando el proveedor lo soporte. La unicidad de `provider_event_id` y la transición de estado se aplican transaccionalmente.
- Si tenant, orden, monto, moneda o estado no coinciden, no se marca pagado, no se confirma inventario y se genera alerta/revisión. No registrar secretos ni payloads con PII completa.
- La reserva utiliza una actualización condicional atómica y una clave de idempotencia asociada a tenant e intento. Confirmación, liberación y expiración son transiciones mutuamente excluyentes; el job de expiración debe poder reintentarse sin duplicar movimientos.
- La generación de factura y notificaciones se publica vía outbox después del commit. Un fallo externo no revierte un pago confirmado ni produce una segunda factura al reintentar.
- Este es el flujo objetivo descrito por ADR-0004; pagos y webhooks no deben considerarse habilitados hasta que endpoints, secretos, pruebas y despliegue existan.

## 4. Búsqueda y límites contra abuso

- Toda búsqueda usa tenant ya resuelto; los parámetros `tenant_id` del cliente se ignoran o rechazan. SQL parametrizado, límite de longitud, filtros allowlist, paginación acotada y timeout de consulta.
- Rate limit por IP y tenant con límites separados para storefront, autenticación, uploads, búsqueda y checkout. Aplicar límites de concurrencia y presupuesto de consultas; los límites exactos se miden y configuran antes de producción.
- Las claves de búsqueda/caché incluyen tenant. Evitar filtros que induzcan scans sin límite y revisar planes de consulta al cambiar índices o ranking.
- Ante saturación, responder con error controlado; no quitar el tenant scope, ampliar límites ni recurrir a consultas no acotadas como fallback.

## 5. Señales, respuesta y evidencia

1. Alertar por `TENANT_MISMATCH`, errores de firma, replay, aumento de denegaciones, cadena de auditoría inválida, uso no esperado de roles privilegiados, límites de upload y fallos de expiración.
2. Correlacionar API, DB y workers con `trace_id`, tenant y actor seudónimo. Los logs no contienen credenciales, tokens, PAN/CVV, payloads completos ni PII innecesaria.
3. Ante indicio de exposición, declarar incidente, preservar evidencia con acceso restringido, detener la ruta o credencial afectada y determinar tenants/datos implicados antes de comunicar.
4. El runbook técnico se complementa con el flujo legal de `docs/legal/flujos.md`. Plazos, destinatarios legales y responsabilidades de notificación son compuertas pendientes de D-12 y revisión de asesoría colombiana; no se infieren de una referencia GDPR.

## 6. Verificación requerida

Los 12 vectores core de `03-tenancy.md` deben ejecutarse en CI con tenants A/B y base real; los vectores 13–16 son controles adicionales. Añadir integración para:

- Host no registrado, header de tenant falsificado y host/claim no compatibles.
- Falta de contexto RLS, reuso de conexión, `app_rw` sin bypass y escritura con `tenant_id` ajeno.
- Caché con dos hosts, URL R2 vencida o prefijo ajeno, objeto con MIME real discordante y dimensiones excesivas.
- Firma webhook inválida, evento repetido, mismatch de tenant/monto/moneda y eventos concurrentes.
- Checkout repetido, dos compradores compitiendo por la última unidad, expiración concurrente con pago y reintento de worker.
- Búsqueda con filtro de tenant falsificado, query excesiva y timeout/rate limit.

Una prueba pendiente o una configuración externa no observada se reporta como “no verificada”, nunca como control implementado.

## 7. Compuerta de publicación

```text
Solicitud de publish
  → autenticar actor + tenant; validar versión y schema cerrado
  → comprobar permiso de rol y decisión determinista
  → verificar aceptaciones legales vigentes requeridas (cuando D-09 esté aprobado)
  → verificar entitlement de billing según ADR-0004
  → publicar versión atómica y emitir evento/outbox
```

- Si el actor, schema, aceptación requerida o entitlement no es válido, no publicar y no purgar cachés como si hubiera éxito.
- La aceptación legal y el entitlement son condiciones separadas. Un tenant `past_due` solo puede seguir publicando si la regla de gracia aprobada por billing lo permite; el flujo no fija duración ni sustituye esa decisión.
- El control de aceptación no se considera activo hasta cerrar D-09, implementar la persistencia/versionado y probar que la API de publicación falla cerrada.
