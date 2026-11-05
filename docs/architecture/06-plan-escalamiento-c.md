# Growup Store — Plan C de Escalamiento por Celdas, Pagos y Datos

> **Estado:** propuesta de evolución; requiere aprobación de Producto/Ingeniería y revisión legal antes de operar producción.
> **Fecha de revisión:** 2026-11-05.
> **Relación:** complementa el [Plan B](05-plan-escalamiento-post-piloto.md); no modifica ADRs ni cierra D-09 a D-16.
> **Decisión propuesta:** preservar el stack vigente a corto plazo y evolucionar hacia celdas regionales con una frontera de pagos explícita, datos minimizados y outbox/inbox durable. Migrar a AWS solo si mediciones/costos justifican la consolidación.

## 1. Resultado ejecutivo

El Plan B es una buena dirección de bajo costo operativo, pero debe tratarse como diseño, no como control implementado. La revisión de seguridad delegada no encontró una vulnerabilidad explotable confirmada en el alcance revisado. Sí encontró que quedan pruebas de host/JWT, webhook, preview y caché por completar; el checkout de pagos y su outbox/inbox/idempotencia no están demostrados como implementación. Las pruebas de backend tampoco se pudieron ejecutar en este entorno: `uv` no está disponible y `python -m pytest` no pudo importar `fastapi`; no se ejecutaron pruebas con Postgres/pgTAP.

**No habilitar pagos reales hasta que la verificación criptográfica, el inbox durable, las transiciones idempotentes, la conciliación y las pruebas de fallo pasen en staging.** Separar las dos relaciones de pago ya aceptadas: Wompi del tenant para el comprador y Stripe de Growup para la suscripción. Nunca convertir Growup en custodio ni en merchant of record sin una nueva decisión y revisión legal.

El plan B debe corregir/explicitar cinco cosas antes de ejecutarse:

1. **RPO no es pérdida cero.** ADR-0008 fija un RPO objetivo de 15 minutos. Ese objetivo permite pérdida de commits recientes en un desastre. Outbox evita perder eventos entre el commit y el encolado, pero no evita pérdida si se pierde el propio primario. Definir recuperación de pagos mediante conciliación y aprobar RPO realista; no prometer “cero pérdida”.
2. **El receptor de webhooks no puede depender de reintentos largos.** La documentación de Wompi describe hasta tres reintentos en 24 horas. Debe validar y persistir un inbox antes de responder HTTP 200; luego se procesa en segundo plano y se reconcilia con el proveedor.
3. **La tabla outbox necesita un modelo de permisos ejecutable.** `tenant_id` + RLS no resuelven por sí solos el despacho global entre tenants. No otorgar `service_role` general al worker; usar un rol y función de claim mínimos, auditados, con pruebas, o procesar por tenant con contexto RLS.
4. **RLS en una réplica no es una frontera contra el operador/proceso privilegiado.** Réplicas se limitan a datos públicos y lecturas tolerantes a staleness; el endpoint público se protege además en la API. Checkout, secretos, PII, estado de pago e inventario permanecen en el primario.
5. **Residencia/costos no están seleccionados.** Supabase documenta una región de São Paulo (`sa-east-1`); la ubicación real del proyecto debe inspeccionarse. R2 no debe tratarse como almacenamiento regional garantizado solo por configurar un location hint: Cloudflare indica que el hint es best effort.
6. **La documentación del pooler necesita reconciliación.** ADR-0008 fija modo transacción para una API persistente en Fly.io, mientras que la guía actual de Supabase distingue conexión directa para backend persistente, pool compartido transaccional para serverless/edge y pool dedicado para alta carga. No cambiar el pooler sin spike: verificar `SET LOCAL`, prepared statements, query pipelining, IPv4/IPv6 y configuración exacta de asyncpg.
7. **“Firma Wompi” debe ser técnicamente precisa.** La documentación consultada describe checksum SHA-256 de campos `signature.properties` en orden + timestamp + secreto; no es una firma asimétrica de clave pública. Una ventana de antigüedad es una política del receptor y debe definirse/probarse además de la unicidad del evento.

## 2. Auditoría del Plan B y estado de verificación

| Tema | Evaluación | Acción/gate |
|---|---|---|
| RLS y aislamiento | ADR-0003 y `03-tenancy.md` describen `app_rw`, `SET LOCAL`, RLS forzado y tests. La revisión no confirmó una fuga explotable, pero la propia documentación deja vectores host/JWT, webhook, preview y caché sin cobertura completa. | Ejecutar la suite contra Postgres real y cerrar los vectores pendientes. No habilitar preview/cache/CDN en rutas de tenant hasta probar dos tenants y dos hosts. |
| Pago Wompi | ADR-0004 fija credenciales por tenant y webhook firmado; no se encontró evidencia suficiente de un checkout/webhook productivo ni de inbox durable. La muestra pública de Wompi no exhibe un `provider_event_id` independiente; no asumir que existe en todos los eventos. | Firma de Wompi con propiedades ordenadas + timestamp + secreto; comparar también el hash esperado en tiempo constante. Confirmar el esquema vigente del evento. Si no tiene ID estable, deduplicar por huella del evento firmado y transición idempotente (no por `transaction.id` solamente); reconciliar eventos no entregados. |
| Semántica de autenticación Wompi | ADR-0004 usa el término “firma”; la documentación consultada describe SHA-256 sobre la concatenación de campos configurados, timestamp y secreto compartido. Llamarlo asimétrico o implementar HMAC/public-key sería incompatible con el protocolo. | Seguir exactamente la especificación vigente; no normalizar/reordenar campos; comparar checksum en tiempo constante; política local de antigüedad y deduplicación complementan la validación. Actualizar terminología ADR al implementar. |
| URL de webhook Wompi | ADR-0004 propone una ruta que contiene `webhook_key`. Si esa clave se trata como secreto, puede quedar en logs de proxy/APM, errores o trazas. No se encontró una ruta productiva confirmada. | Usar la ruta solo como identificador opaco de enrutamiento, no como autenticación; la firma/checksum y el mapeo de cuenta son obligatorios. Redactar path/query de logs y traces, limitar tasa y permitir rotación. |
| Billing Stripe | Stripe Billing es para Growup, no para el cobro de productos. `metadata.tenant_id` no debe ser la única autoridad para resolver tenant. | Verificar firma sobre cuerpo crudo; mapear `customer`/`subscription` desde registros propios y comprobar estado/plan/precio esperados. Persistir evento único antes de responder 2xx. |
| Idempotencia | El modelo de datos plantea claves únicas, pero el esquema y el flujo no están implementados/ejecutados según la evidencia revisada. | Clave por tenant + operación, hash canónico de solicitud y resultado; mismo hash devuelve el mismo resultado, distinto hash produce conflicto. Restricción DB, no solo Redis. |
| Outbox/ARQ | ARQ está aceptado para jobs; no sustituye la atomicidad commit→evento. La muestra del Plan B no especifica permisos de claim, retención ni reconciliación de mensajes. | Outbox en la transacción de dominio; relay reintentable; inbox por consumidor; métricas de antigüedad, backlog, lease vencido, DLQ y replay seguro. |
| Caché | CDN/cache isolation parcial por documentación; el tenant y versión deben formar la clave. | Cachear solo contenido público publicado. No cachear admin, respuestas con PII, preview, inventario autoritativo, checkout ni respuestas webhook. Invalidar al publicar. |
| Media/R2 | ADR-0006 ya define validación, límites y buckets; despliegue/configuración no se verificó en este review. | Revisar ACL, lifecycle, cuentas por ambiente, URL prefirmada, límite de bytes/píxeles/tiempo, escaneo PDF y cumplimiento de borrado de huérfanos. |
| Región y continuidad | ADR-0008 establece RPO≤15 min y RTOs objetivo; no hay evidencia de región/cuentas ni simulacro disponible en este entorno. | Medir Colombia→región, restaurar backup en entorno aislado y comprobar pagos/eventos tras recuperación. Declarar límites del RPO al negocio. |
| Pool PostgreSQL | ADR-0008 elige Supavisor en modo transacción para Fly; la documentación vigente distingue conexión directa para backends persistentes y pool transaccional compartido para serverless. No es prueba de defecto, pero deja abierta una incompatibilidad posible de prepared statements/pipeline asyncpg. | Spike con carga y driver real; verificar límites, modo, prepared statements, pipelining, IPv4/IPv6 y el comportamiento de `SET LOCAL`. Registrar conexión elegida en ADR. |
| Legal y roles | D-09 a D-16 siguen abiertas/propuestas. No se demuestra aceptación DPA, política DSR/retención ni protocolo de breach aprobado. | Mantener gates legales abiertos y hacer revisión colombiana/contable. No automatizar purgas ni comunicar plazos normativos no confirmados. |
| Consistencia documental | D-06 aparece cerrada en `decisiones-pendientes.md`, pero ADR-0004 la llama pendiente; IVA de envío/redondeo siguen como pendientes derivados. | Corregir la referencia de ADR-0004 o separar “decisión base cerrada” de “reglas contables derivadas pendientes”; no cambiar la decisión sin responsable. |
| Verificación ejecutada | Revisión documental/código acotada; sin tests funcionales en este entorno por herramientas/dependencias ausentes. | Ejecutar CI/pgTAP al preparar el merge; no marcar los controles como verificados por esta auditoría. |

### Pruebas que deben bloquear el release de pagos

- Firma válida, firma inválida, timestamp fuera de tolerancia, ambiente sandbox/prod cruzado y cuerpo modificado.
- Repetición del mismo webhook, eventos concurrentes fuera de orden y replay manual; efectos exactamente una vez **por idempotencia**, no por suposición de entrega única.
- Evento válido con cuenta/orden/tenant/monto/moneda incorrectos: ningún pago confirmado, inventario vendido ni factura emitida.
- DB caída antes del commit: respuesta que provoca retry; DB commit exitoso y Redis caído: inbox/outbox queda durable y el worker recupera después.
- Caída de proveedor o respuesta de creación de pago perdida: recuperar estado por referencia/idempotency del proveedor y conciliación; no iniciar cobro duplicado a ciegas.
- Duplicado de `Idempotency-Key` con el mismo request hash; misma clave con monto, tenant, orden o cuerpo diferente.
- Dos pagos/concurrencia sobre la última unidad; pago posterior a expiración de reserva; refund total/parcial repetido.
- Tenant A intenta consultar, enlazar o actualizar pagos, clientes, direcciones, eventos o reembolsos de tenant B.
- Backup restore/PITR: recuperar orden, payment attempt, inbox, outbox y movimiento de inventario; comparar contra extracto del proveedor.

## 3. Plan C: topología regional por celdas

Una **celda** es un conjunto de cómputo y datos con un único escritor de PostgreSQL que atiende a un grupo explícito de tenants. El control plane resuelve `host → tenant_id → cell_id`; el plano de datos nunca acepta `cell_id` del cliente. El piloto comienza con una sola celda. No se recomienda active-active writes ni sharding antes de métricas, procedimientos de movimiento de tenant y pruebas de restore.

```text
Comprador / comerciante
       │ HTTPS
       ▼
Cloudflare: WAF + límites por IP/ruta + CDN de contenido público
       │ Host normalizado; sin confiar en X-Tenant-ID
       ▼
Vercel / Next.js: storefront SSR/ISR y admin
       │ API autenticada; resolver tenant/versión; sin cache de PII
       ▼
API FastAPI modular, sin estado (Fly GRU en la fase vigente)
       │ control-plane: host → tenant → cell_id
       │ DB: SET LOCAL ROLE app_rw + SET LOCAL app.tenant_id
       ▼
Celda inicial: Supabase Postgres (un primario)
       ├─ customers / orders / payments / payment inbox
       ├─ inventory / reservations
       ├─ idempotency + tenant outbox
       └─ Stripe billing (tenant mapping; secretos de plataforma fuera de DB)
                 │
                 ├─ Relay outbox → ARQ/Redis (tareas reintentables)
                 │                 ├─ prioridad operativa
                 │                 └─ baja: DIAN/email/media/archivo
                 ├─ Wompi (cuenta del tenant; checkout hosted)
                 └─ Stripe Billing (cuenta de Growup; suscripción SaaS)

R2: media pública versionada; documentos privados solo con región/contrato aprobados.
AWS S3 sa-east-1: candidato para archivo/backups privados si se elige ruta AWS.

Al alcanzar umbrales:
Control plane de tenants → celda 2 (separación por grupo de tenants)
Cada celda: su propio primario/RLS/backup/outbox; no hay joins entre celdas.
```

### Contratos de la celda

1. **Control plane mínimo:** mapa host/dominio verificado, `tenant_id`, `cell_id`, estado y versión de esquema. No almacenar PII de compradores allí. Cambios del mapa requieren autorización y auditoría.
2. **Resolución:** la API valida host canónico y credencial; consulta asignación confiable; establece contexto tenant en la transacción. RLS continúa siendo defensa obligatoria. No enrutar por `tenant_id` enviado por cliente.
3. **Consistencia:** una celda tiene un escritor. Lecturas autoritativas de checkout/pago/inventario van al primario. Una réplica puede servir catálogo publicado; después de una escritura, la lectura que requiera read-your-write vuelve al primario.
4. **Colas:** cada job tiene `tenant_id`, `event_id`, `aggregate_id` y versión de schema; el consumidor comprueba pertenencia del recurso. Los trabajos de pago/inventario no comparten límites de concurrencia con media/email.
5. **Migración de tenant:** snapshot consistente + pausa/dual-write controlado + verificación de conteos/hashes + cambio atómico de mapa + reconciliación. No usar dual-write ad hoc ni aceptar escrituras en dos primarios.
6. **Failover:** respaldos/PITR y restauración en región/cuenta objetivo. La recuperación de eventos de pasarela se apoya en inbox y conciliación, no en asumir que el proveedor reenvía indefinidamente.

## 4. Filtro de proveedores — nube, Postgres y objetos

La comparación es de ajuste técnico; no es una cotización ni certificación de cumplimiento. Se deben validar contrato, DPA/subencargados, soporte, región de datos efectiva, egreso, soporte de RLS/roles y restore antes de comprar.

| Servicio | Opción | Evaluación para Growup | Decisión propuesta |
|---|---|---|---|
| Postgres administrado | **Supabase Postgres** | Mantiene Auth, políticas RLS y operación actual. La documentación publica `sa-east-1` (São Paulo); la región real del proyecto y las funciones asociadas deben confirmarse en consola. La guía actual diferencia los modos de conexión por runtime. | **Preferir en Plan C inicial.** Probar carga, pool, RLS, PITR y latencia. Resolver la diferencia ADR-0008/pooler con un spike; no migrar solo por anticipar escala. |
| Postgres administrado | **AWS RDS for PostgreSQL** | Opción de consolidación en AWS y control de red/IAM; requiere asumir Auth, pooling, auditoría, jobs y operación que Supabase integra. Coste incluye cómputo, storage, I/O/IOPS, backups y transferencia. | **Candidato de fase avanzada**, solo si se justifica consolidación/controles o límites medidos de Supabase. |
| Compute API | **Fly.io** | ADR-0008 y stack actual; docs de Fly incluyen `gru` (São Paulo), aunque disponibilidad regional/servicio y red privada deben verificarse al desplegar. | Mantener para piloto y primera escala, medir conexión a la DB. |
| Compute API | **AWS ECS/Fargate en sa-east-1** | Consolidación de compute, red y RDS; mayor trabajo de plataforma/IAM/observabilidad y potencial costo base. Verificar soporte del servicio y límites por región. | Alternativa de migración, no destino automático. Benchmark completo antes de ADR. |
| Edge/frontend | **Vercel + Cloudflare** | Sigue la topología aceptada. Edge acelera contenido público, pero el cache key/invalidation por tenant debe probarse; no ejecutar escrituras transaccionales en Edge. | Mantener; CDN solo para objetos/contenido público y cache explícito. |
| Media pública | **Cloudflare R2** | Precio publicado consultado: Standard USD $0.015/GB-mes; egress a Internet sin cargo; cargos por operaciones. Location hints son best-effort, no residencia garantizada. | **Preferido para imágenes/variantes públicas** con hash y metadata no sensible. |
| Documentos privados/backups | **Amazon S3 regional** | Bucket en región concreta; control de acceso/IAM/KMS y opciones de lifecycle/archivo. Costes variables por storage, requests, retrieval/restore y transferencia. | Preferir si el destino/region AWS queda aprobado y el costo de operación compensa. Cifrado, bloqueo público, versiones y restore testado. |
| Documentos privados/backups | **R2 privado** | Puede tener acceso privado y restricciones de jurisdicción soportadas, pero su location hint no garantiza región; la lista de jurisdicciones y contrato deben revisarse para el uso previsto. | No usar para archivo legal/fiscal sensible hasta confirmar región/contrato, retención, recuperación y D-10. |
| Cache/colas | **Upstash Redis + ARQ** | Ya aceptado en ADR-0006/0008. Redis es efímero para efectos de negocio; la DB/outbox debe permitir reconstruir trabajo. | Mantener con TLS, separación de usos/credenciales, límites, región cercana y simulacro de pérdida. |
| Cola durable alternativa | **SQS (solo si se consolida en AWS)** | Reduce dependencia de Redis para backlog, pero añade integración y no crea exactly-once end-to-end. Standard queue es al menos una vez; deduplicación sigue siendo responsabilidad de DB/consumidor. | Considerar únicamente al mover compute/datos a AWS y con comparación operativa/costo. No introducir junto a ARQ sin necesidad demostrada. |

### Modelo de costo para decidir

No comparar únicamente precio por GB. Calcular para el mismo perfil de acceso:

```text
Costo mensual =
  Postgres compute + storage provisionado + IOPS + backups/PITR
  + réplica(s) + egreso/transferencia + pooler
  + objetos GB-mes + PUT/GET/LIST + retrieval + restauración
  + Redis/colas + observabilidad + soporte/plan + horas de operación
```

Medir GB por tabla/índice/TOAST/WAL/backup, operaciones de storage, egreso, tamaño medio de objeto y distribución GET/PUT, retención y frecuencia de restore. R2 puede ser ventajoso para imágenes de alto egreso; S3 puede reducir saltos y facilitar control regional/operativo si API/DB ya corren en AWS. No almacenar archivos duplicados indefinidamente: lifecycle solo después de comprobar integridad, legal hold y restauración.

## 5. Datos de compradores, órdenes y pagos por pasarela

### Principios no negociables

- No almacenar PAN completo, CVV/CVC, banda magnética, PIN ni credenciales de tarjeta. Hosted checkout/tokenización de Wompi; Growup conserva solo referencias necesarias.
- No confundir datos del pago del comprador (Wompi por tenant) con datos de suscripción SaaS (Stripe de Growup).
- Dinero en `bigint` de centavos + moneda; validar sumas y congelar snapshot de orden. El proveedor es fuente externa del estado, pero el estado interno se actualiza solo tras evento verificado/conciliación.
- Cada tabla tenant-scoped tiene `tenant_id NOT NULL`, `ENABLE` + `FORCE ROW LEVEL SECURITY`, políticas `USING`/`WITH CHECK` y claves/foreign keys compuestas con `tenant_id`. Excepciones de plataforma llevan un límite de seguridad explícito y nunca política genérica `USING (true)`.
- Minimizar datos en webhooks/logs/traces. El proveedor puede incluir correo y campos de transacción; persistir hash + subset requerido, no el JSON íntegro por defecto.

### Modelo lógico sugerido

```text
tenant (tienda)
 ├─ customers                 identidad/contacto del comprador en esta tienda
 ├─ customer_addresses        direcciones; acceso restringido
 ├─ orders                    snapshot operativo/fiscal del pedido
 │   ├─ order_items           snapshot de nombre/SKU/precio/impuesto
 │   └─ inventory_reservations
 ├─ tenant_payment_accounts   conexión a cuenta Wompi (referencia, estado, versión de secreto)
 ├─ payment_attempts          orden + proveedor/cuenta + monto + estado + referencia
 ├─ payment_webhook_inbox     evento verificado, único por cuenta y provider_event_id
 ├─ payment_events            cambios append-only, hash, tipo y resultado
 ├─ refunds                   reembolso y referencia externa
 └─ tenant_outbox_events      evento interno durable para worker

Growup (plataforma, separado)
 ├─ platform_subscriptions    tenant_id + Stripe customer/subscription IDs + estado
 ├─ billing_events            tenant_id, stripe event ID único, hash/status
 ├─ platform_webhook_inbox    tenant_id nullable durante resolución; RLS FORCE;
 │                            acceso solo a endpoint/función de ingreso acotada
 └─ secretos Stripe de plataforma fuera de Postgres (secret manager)
```

La columna `tenant_id` por sí sola no evita una FK cruzada. Definir `UNIQUE (tenant_id, id)` en padres y FKs `(tenant_id, order_id)` / `(tenant_id, payment_id)` en hijos, además de RLS. Esto impide asociar una fila de tenant A con una orden de tenant B incluso ante un bug de aplicación.

| Tabla | Campos permitidos/propuestos | Evitar/controles |
|---|---|---|
| `customers` | `id`, `tenant_id`, `auth_user_id` nullable, email normalizado, nombre mínimo, timestamps y fuente/consentimiento si aplica. | No centralizar perfil entre tenants sin decisión; acceso limitado a roles; búsqueda por email no debe permitir enumeración. |
| `customer_addresses` | `tenant_id`, `customer_id`, nombre de recepción, dirección, municipio, código postal, país, teléfono si el envío lo exige. | Aislar de logs/analytics; cifrar backups; no indexar PII innecesariamente; acceso de fulfillment auditado. |
| `orders` | `tenant_id`, contacto/dirección snapshot necesarios para despacho y comprobación, totales COP, estado y fechas. | Snapshot de PII tiene retención aprobada; no duplicar JSON arbitrario; limitar acceso y export. |
| `tenant_payment_accounts` | `tenant_id`, provider=`wompi`, `provider_account_id` público, estado, `webhook_key` aleatorio, `secret_version`, timestamps. | No exponer ni loggear secretos. Secretos cifrados envelope en Vault/KMS/secret manager; solo servicio pagos descifra; rotación y auditoría. No devolver ciphertext por API. |
| `payment_attempts` | `tenant_id`, `order_id`, proveedor, cuenta de proveedor, ID externo, `amount_cents`, `currency`, estado canónico, key/hash idempotencia, timestamps. | No guardar PAN/CVV. Mantener `checkout_url` en memoria/response efímera; si proveedor exige persistir, cifrar, expirar y no loggear porque puede actuar como bearer URL. |
| `payment_webhook_inbox` | tenant resuelto por cuenta, `provider`, `provider_event_id`, tipo allowlisted, `payload_hash`, estado, `received_at`, `processed_at`, intento/error code. | Único `(tenant_id, provider, provider_event_id)`; raw body no persistente por defecto; si una auditoría lo exige, cifrado, acceso restringido y retención limitada/aprobada. |
| `refunds` | `tenant_id`, `payment_id`, ID de refund proveedor, monto, motivo codificado, estado, idempotency key. | Constraint monto acumulado ≤ monto capturado; evitar notas libres con PII; no ejecutar refund solo por request del cliente. |
| `platform_subscriptions` | `tenant_id`, Stripe `customer_id`/`subscription_id`, plan interno, estado y periodos. | No guardar secret key; resolver tenant desde mapeo propio del customer/subscription verificado; metadata entrante es una señal, no autorización. |
| `billing_events` | `tenant_id`, `provider_event_id`, tipo allowlisted, hash, estado, timestamps. | Unique event ID y efecto idempotente; acceso platform/billing según rol; evitar payload completo de Stripe. |

### Flujo Wompi: comprador → merchant tenant

```text
Storefront → API calcula orden/monto en primario
           → crea payment_attempt + idempotency + reserva + outbox en transacción
           → Wompi Web Checkout hosted con cuenta del tenant
Wompi → webhook HTTPS
      → resolver webhook_key → tenant/account; buscar secreto versionado
      → verificar checksum según propiedades ordenadas + timestamp + secreto
      → validar ambiente, cuenta, referencia, orden, COP/monto y transición
      → insertar webhook inbox + actualizar pago + outbox en una transacción
      → HTTP 200 solo después del commit durable
Worker → factura/notificación/fulfillment idempotentes
Conciliación → comparar estado local con consulta/API/export del proveedor
```

El handler usa el algoritmo y formato exactos de la versión vigente de Wompi (no un HMAC inventado ni una validación sobre JSON reserializado). Comparar timestamp contra una ventana configurada y evitar replay mediante la constraint única del evento o una huella canónica si no existe ID estable. No usar `transaction.id` solo como clave de evento porque un pago puede tener más de una actualización legítima. Si no puede guardar durablemente, no responder 200. La documentación del proveedor describe reintentos limitados, por lo que reconciliación operativa es obligatoria. Eventos desconocidos se registran con subset seguro y alerta/rate limit; no se permite que un evento desconocido confirme orden.

### Flujo Stripe: merchant tenant → suscripción Growup

```text
Owner tenant → billing Growup → Stripe Checkout/Billing de plataforma
Stripe → webhook global firmado sobre cuerpo crudo
       → validar Stripe-Signature con secreto del endpoint/ambiente
       → mapear customer/subscription a tenant desde DB propia
       → verificar producto/plan/moneda/periodo permitidos
       → guardar billing event + actualizar entitlement + outbox de auditoría
```

La cuenta y el secret key pertenecen a Growup; credenciales de Stripe no son por tenant. No aceptar `tenant_id` de metadata sin corroborar la relación con los IDs de Stripe ya almacenados. Mantener billing independiente de checkout Wompi: caída o `past_due` no debe falsear el estado de pago del comprador. Las reglas de gracia/suspensión siguen la decisión de billing aprobada.

### Cifrado, acceso y separación

- Cifrado en tránsito TLS y cifrado administrado en reposo son mínimos, no sustituyen autorización por fila.
- Separar secretos de pasarela de la DB de negocio; usar KMS/Vault/secret manager, envelope encryption, `key_version`, rotación documentada, permisos por servicio y registro de descifrado sin secreto/PII.
- Restringir acceso de soporte con consentimiento del tenant, ticket/motivo, ventana temporal y auditoría; MFA y revisión por cuatro ojos para cambios de cuenta/pagos.
- No incluir token de sesión, URL privada firmada, webhook secret, email, dirección o payload completo en Sentry, OTel tags, request body logs o errores.
- Backups y exports contienen PII y referencias de pagos: cifrado, IAM mínimo, bucket privado, claves separadas por ambiente y pruebas de restore; retención final depende de D-10/revisión contable.

## 6. Outbox/inbox y tolerancia a pérdida

### Transacción del dominio

```sql
-- Fragmento conceptual; falta migración y pruebas de proyecto.
CREATE TABLE tenant_outbox_events (
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  id uuid NOT NULL,
  aggregate_type text NOT NULL,
  aggregate_id uuid NOT NULL,
  event_type text NOT NULL,
  payload jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  available_at timestamptz NOT NULL DEFAULT now(),
  attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  lease_until timestamptz,
  delivered_at timestamptz,
  last_error_code text,
  PRIMARY KEY (tenant_id, id)
);

ALTER TABLE tenant_outbox_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_outbox_events FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_outbox_isolation ON tenant_outbox_events
  USING (tenant_id = app.current_tenant())
  WITH CHECK (tenant_id = app.current_tenant());
```

La tabla real necesita además índice parcial de pendientes, política de actualización, validación de tipos/eventos y migración expand/contract. `payload` solo lleva datos necesarios y evita secretos/PII. Un dispatcher que reclama eventos de todos los tenants no debe recibir `BYPASSRLS` de uso general. Elegir y probar uno de estos diseños:

- **Opción preferida inicial:** workers por tenant/job con transacción `SET LOCAL app.tenant_id`; el mapa de tenants pendientes se obtiene por función de plataforma estrecha y auditada.
- **Opción especializada:** función `SECURITY DEFINER` de claim que fija `search_path`, limita columnas/eventos/lease, usa SQL estático, restringe EXECUTE al rol de relay y tiene tests negativos. No exponerla a API.

El relay marca `delivered_at` solo luego de confirmar en el broker; si cae tras publicar y antes de marcar, publica de nuevo y el consumidor deduplica por `event_id`. El broker no hace que el side effect sea exactly-once. Mantener inbox de consumidor y conciliación para pagos/facturas.

**RPO:** ADR-0008 tiene objetivo ≤15 minutos. Aceptarlo implica riesgo residual de perder commits recientes en pérdida regional del primario. Aprobar con negocio/operación si ese RPO es aceptable para pagos, o evaluar replicación síncrona/servicio con RPO menor y su latencia/costo. Independientemente, guardar eventos de proveedor durables en DB y ejecutar conciliación tras restore para descubrir transacciones cobradas sin commit local.

## 7. Arquitectura de datos y retención

| Categoría | Fuente de verdad | Archivo | Regla de borrado |
|---|---|---|---|
| Perfil/contacto comprador | Postgres tenant-scoped | No exportar por defecto | DSR y retención por finalidad; borrar/anonimizar campos según dictamen aprobado. |
| Orden y snapshot de venta | Postgres primario tenant-scoped | Export cifrado si volumen lo justifica | Retención fiscal/consumidor se valida con legal/contador; la tabla de 5 años sigue provisional. |
| Pago y referencia provider | Postgres: monto, moneda, IDs externos y estados | No raw webhook permanente | No PAN/CVV; retención y evidencia de disputa según política aprobada. |
| Eventos webhook | Inbox mínima, hashes, ID/type/status | R2 solo si Legal aprueba export | No conservar payload crudo sin base/TTL/ACL. |
| Factura electrónica | Proveedor DIAN + referencia interna | Bucket privado regional aprobado si se guarda PDF/XML | Retención por obligación fiscal confirmada; no purgar por los 90 días del plan inicial. |
| Media de catálogo | R2/S3 según clase y región | Media pública puede tener CDN/versionado | Purgar huérfanos después de verificar referencias y ventana de recuperación. |
| Logs operativos/auditoría | OTel/Sentry + `decision_logs` | Export cifrado y con manifiesto | Minimizar PII; retención de D-10 pendiente; archivo no equivale a supresión. |

No activar particionamiento ni purga por calendario como primer paso de ahorro. Medir índices, TOAST, churn, WAL/backups y tabla por tenant; reducir payload, revisar índices y archivar solo después de prueba de retorno/restauración. Al particionar, diseñar las restricciones únicas/FKs con la clave temporal; probar RLS en cada partición y que las consultas incluyan el rango que habilita pruning.

## 8. Plan de ejecución por fases

| Fase | Entregables | Criterio de avance |
|---|---|---|
| **0 — Antes de pagos reales** | Completar suite de tenant; implementar inbox/outbox/idempotencia; validar Wompi sandbox; restringir secretos; documentar estado y conciliación; cerrar DPA/PCI/brechas según decisión legal; restaurar backup y probar replay. | Todos los tests de pago/aislamiento de §2 pasan en CI y staging; rollback/replay operables; aprobación legal y de pasarela. |
| **1 — Calibrar celda piloto (0–3 meses)** | Confirmar regiones reales; medir p50/p95/p99 Colombia→Edge/API/DB/proveedor; dashboards por tenant sin PII; pool y límites; análisis de queries; rates y upload limits; datos clasificados. | SLO definido con tráfico medido; cero críticos abiertos; costo mensual por GB/tenant y costo por orden estimados. |
| **2 — Durabilidad y escala de lectura (3–6 meses)** | Relay/inbox recuperable; separar workers/colas; réplica solo ante cuello de lecturas; CDN cache key validada; R2 para media pública; decisión de S3 privado/backups con región/contrato; simulacro de restauración. | RPO/RTO verificados; lag y restore visibles; caché dos-host sin fuga; réplica nunca sirve checkout. |
| **3 — Celdas (6–12+ meses)** | Definir mapa control-plane, límites por celda, automatizar onboarding/movimiento de tenant, backup por celda, despliegue y migración expand/contract; evaluar AWS consolidado si el modelo de costo/operación gana. | Umbral de capacidad superado sostenidamente, rehearsals completos, dueño de plataforma y presupuesto; ADR aprobada. |
| **4 — Alta disponibilidad regional (solo si exigida)** | Standby/DR multi-región, failover controlado, DNS/Edge, pruebas de claves, failback y conciliación de pasarela. | SLO y RPO/RTO aprobados por negocio/legal; restore/failover medidos; no usar multi-primary salvo decisión separada. |

**No usar hitos de calendario como autorización automática.** Una réplica, región secundaria, sharding, outbox privilegiado, retención o cambio de proveedor requiere evidencia, prueba de recuperación, análisis de costo y owner nombrado.

## 9. ADRs y decisiones que deben mantenerse abiertas

| Elemento | Estado/tratamiento |
|---|---|
| ADR-0003 — tenancy/RLS | Mantener aceptada; ampliar tests y políticas al implementar nuevas tablas. |
| ADR-0004 — Wompi/Stripe/MoR | Mantener aceptada; implementar/verificar flujos antes de production. Cambiar proveedor o hacer marketplace exige ADR + revisión legal. |
| ADR-0006 — ARQ/R2/FTS/observabilidad | Mantener aceptada; R2 se recomienda para media pública, no se presume apto para archivo regulado. |
| ADR-0008 — Vercel/Fly/Supabase y RPO/RTO | Mantener hasta tener mediciones. La región Sao Paulo está publicada para Supabase; verificar cuenta y ajustar el texto de región si procede mediante ADR/registro formal. |
| D-06 — moneda/IVA | Decisión base aparece cerrada; confirmar con contador envío/redondeos/productos. Corregir ADR-0004 que aún la llama pendiente. |
| D-09 a D-16 | Permanecen propuestas/pendientes: DPA, DSR/retención, PCI, brechas, devoluciones, fraude, email, soporte. No se cierran con este plan. |
| ADR nueva candidata | Definir criterios y modelo para celdas, outbox/inbox global/tenant y almacenamiento/archivo por clasificación. Crear solo tras decidir sponsor, alcance, rollback, región y métricas. |

## 10. Checklist de release y operación

- [ ] Región Supabase real y región de Redis/API/storage verificadas desde consolas y contratos; latencia medida desde Colombia.
- [ ] AWS/Supabase/R2 evaluados con calculadora, cargas y restore; no seleccionar por precio de almacenamiento aislado.
- [ ] Todas las tablas de negocio tenant-scoped llevan `tenant_id`, RLS `ENABLE` + `FORCE`, `USING`/`WITH CHECK`, índices y tests A/B.
- [ ] `webhook_key`/account mapping resuelve cuenta antes de usar datos del payload; firma Wompi/Stripe validada según documentación vigente.
- [ ] Inbox duradero commit antes de HTTP 200; retención segura; reintentos y conciliación están monitorizados.
- [ ] Clave idempotente única en DB, request hash, conflictos y expiración probados; ninguna garantía depende solo de Redis.
- [ ] Pago y facturación están separados; secrets fuera de DB/logs; PAN/CVV nunca pasan por Growup.
- [ ] `checkout_url` es efímera o cifrada y expirable; no aparece en logs, analytics o errores.
- [ ] Billing Stripe tenant se resuelve por IDs propios verificados y no por metadata sin corroborar.
- [ ] RPO/RTO aprobados, medidos y explicados; restore incluye órdenes/pagos/inbox/outbox y reconciliación.
- [ ] Retención DSR, legal hold, export R2/S3 y borrado aprobados por Legal/Contabilidad; no hay purga automática de 90 días no aprobada.
- [ ] Runbooks para firma inválida, duplicado, mismatch, outage de proveedor, backlog, restore, rotación y acceso de soporte.

## Fuentes de proveedores consultadas

Consultadas el 2026-11-05; precios y disponibilidad pueden cambiar.

- [Regiones de Supabase](https://supabase.com/docs/guides/platform/regions) — incluye South America (São Paulo), `sa-east-1`; la región determina dónde se almacena el primario.
- [Pooling de Supabase](https://supabase.com/docs/guides/database/connecting-to-postgres) — recomienda método según runtime; conexiones persistentes, serverless y migraciones tienen rutas distintas; no asumir que todo backend debe usar pool compartido transaccional.
- [Precios R2](https://developers.cloudflare.com/r2/pricing/) — storage, operaciones, retrieval y egress.
- [Ubicación de datos R2](https://developers.cloudflare.com/r2/reference/data-location/) — location hints best-effort y restricciones jurisdiccionales con alcance específico.
- [Precios Amazon RDS PostgreSQL](https://aws.amazon.com/rds/postgresql/pricing/) — compute, storage, I/O/IOPS, backups y transferencias.
- [RDS Multi-AZ](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.html) — el standby de un deployment Multi-AZ de instancia no sirve lecturas; el cluster Multi-AZ con readers es un modo distinto.
- [Precios Amazon S3](https://aws.amazon.com/s3/pricing/) — clases, requests, retrieval, lifecycle y periodos mínimos de archivo.
- [Regiones/endpoints de AWS](https://docs.aws.amazon.com/general/latest/gr/rande.html) — incluye `sa-east-1`; disponibilidad debe comprobarse por servicio.
- [Eventos y firma Wompi Colombia](https://docs.wompi.co/docs/colombia/eventos/) — estructura, checksum/timestamp, ambientes y política de reintentos.
- [Gestión de eventos webhook de Stripe](https://docs.stripe.com/events/manage-webhook-endpoints) — validar firma con cuerpo original, recuperaciones, reintentos y deduplicación.

## Referencias internas

- [Plan B y matriz de alternativas](05-plan-escalamiento-post-piloto.md)
- [ADR-0003 — identidad, tenancy y RLS](../adr/0003-identidad-tenancy-rls.md)
- [ADR-0004 — pagos y merchant of record](../adr/0004-pagos-checkout-merchant-of-record.md)
- [ADR-0006 — stack satélite](../adr/0006-stack-satelite.md)
- [ADR-0008 — topología de despliegue](../adr/0008-topologia-despliegue.md)
- [Modelo de datos](02-datos.md)
- [Tenancy y threat model](03-tenancy.md)
- [Flujos de seguridad](04-flujos-seguridad.md)
- [Decisiones pendientes](../decisiones-pendientes.md)
- [Flujos legales](../legal/flujos.md)
