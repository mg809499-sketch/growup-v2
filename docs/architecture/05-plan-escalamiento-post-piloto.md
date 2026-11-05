# Growup Store — Plan Master de Escalamiento, Arquitecturas Alternativas y Auditoría Post-Piloto

> **Estado:** propuesta técnica para revisión; no equivale a aprobación de ADR ni a evidencia de infraestructura desplegada.
> **Alcance de evidencia:** revisión del repositorio y de sus decisiones documentadas. No se verificaron cuentas, configuración ni métricas de producción.
> **Decisión recomendada:** evolucionar primero con la **Versión B, monolito modular**, conservando la topología aceptada por ADR-0008. Introducir réplicas, particiones, archivo frío y sharding solo al cumplir criterios medibles.
> **Google Docs:** no se creó un documento externo; este es el entregable local en Markdown.

## 1. Resumen ejecutivo

**Riesgo actual para habilitar comercio transaccional: alto hasta cerrar las compuertas de pagos, privacidad y operación.** El repositorio documenta una base sólida para aislamiento (RLS forzado, transacciones con contexto local, pruebas cross-tenant), catálogo, inventario concurrente, media y auditoría. Sin embargo, la documentación también indica que pagos/webhooks, la caché CDN completa y varios vectores de aislamiento aún no tienen cobertura demostrada; las decisiones legales D-09 a D-16 siguen abiertas. El estado de código no demuestra que proveedores o controles estén desplegados.

La ruta de menor riesgo y costo es **B con límites explícitos**: mantener FastAPI modular, PostgreSQL/Supabase y el pooler aceptado, añadir outbox + idempotencia antes de pagos reales, separar colas por prioridad en ARQ y cachear solo lecturas públicas no transaccionales. El checkout debe leer/escribir en el primario. Las réplicas se habilitan cuando métricas prueben presión de lectura; particionamiento, archivo y sharding requieren pruebas de restauración, retención aprobada y un caso de capacidad. Esto evita introducir consistencia eventual, complejidad operativa y costos antes de necesitarlos.

**“Cero pérdida” y “exactly once” no son garantías realistas entre sistemas distribuidos.** El objetivo implementable es persistencia transaccional local, entrega al menos una vez, consumidores idempotentes, conciliación y alertas. Una llamada externa puede fallar o su respuesta perderse; el sistema debe poder recuperarse sin duplicar órdenes, cobros o facturas.

## 2. Evidencia y límites de la auditoría

El README del repositorio declara como implementados el núcleo tenancy/RLS, el pool asyncpg con `SET LOCAL`, resolución host→tenant, auth de staff, catálogo, inventario con reservas concurrentes, gobernanza, worker ARQ de media, pruebas de aislamiento, hardening HTTP y observabilidad básica. La misma fuente indica que el storefront sigue incompleto y que aún faltan partes del MVP. `docs/architecture/03-tenancy.md` reporta 10 pruebas automatizadas cross-tenant: varios vectores están cubiertos, el vector de caché es parcial, y binding host+JWT, webhooks, preview y caché completa quedan pendientes según sus propios criterios.

Esta revisión **no** confirma despliegues, regiones, SLO, cuentas de pago, versiones activas de infraestructura, costes ni cumplimiento legal. Los elementos no demostrables desde el repositorio se marcan como pendientes de verificación, no como defectos confirmados ni como controles efectivos. `.kiro/steering/` no está disponible en este checkout; sus archivos figuran eliminados en el worktree y no se restauraron.

## 3. Topología recomendada — Versión B con guardrails

```text
Comprador / comerciante
        │ HTTPS
        ▼
Cloudflare: DNS + WAF + rate limits + CDN (solo respuestas públicas elegibles)
        │ host canónico; sin confiar en X-Tenant-ID del cliente
        ├──────────────► Vercel / Next.js: storefront SSR/ISR y admin
        │                    │ API privada; cache key por tenant + versión
        ▼                    ▼
Fly.io: FastAPI modular, horizontal y sin estado
        │ host → tenant + JWT/JWKS + membership
        │ transacción: SET LOCAL ROLE app_rw + SET LOCAL app.tenant_id
        ├──────────► Supavisor (modo transacción, ADR-0008) ──► PostgreSQL primario
        │                                                         ├─ checkout / pagos
        │                                                         ├─ inventario / órdenes
        │                                                         └─ outbox + idempotencia
        ├──────────► Redis + ARQ (colas separadas por prioridad)
        │                 ├─ alta: tareas críticas reintentables
        │                 └─ baja: email, DIAN, media, housekeeping
        └──────────► R2: objetos multimedia y archivos de auditoría aprobados

Cuando las métricas lo justifiquen:
PostgreSQL primario ──► réplica de lectura ──► catálogo/búsqueda tolerante a staleness
```

### Contratos de diseño

| Capa | Decisión propuesta | Invariante |
|---|---|---|
| Edge/CDN | Cloudflare delante del storefront; SSR/ISR de Next.js con invalidación por tenant y versión publicada. | No cachear PII, respuestas autenticadas, precio/stock de checkout ni contenido cuyo tenant no esté en la clave. |
| Resolución tenant | Resolver `Host` canónico contra dominios registrados; ignorar/rechazar `X-Tenant-ID` entrante. | El backend valida claims JWKS y membership; host, tenant y actor deben ser compatibles. |
| API | FastAPI modular en Fly.io, escalado horizontal con réplicas sin estado. | Cada operación de negocio lleva contexto tenant dentro de una transacción. No fallback a tenant por defecto. |
| Pool de DB | Mantener Supavisor en modo transacción y `SET LOCAL`, según ADR-0008. | No cambiar a PgBouncer sin ADR que compare pruebas, límites y efectos de pooler. No usar `SET` de sesión. |
| Primario | Toda escritura y toda decisión de inventario, checkout, pago, idempotencia y conciliación. | Una caché o réplica nunca autoriza la compra ni determina el precio final. |
| Réplica | Lecturas públicas de catálogo/búsqueda tras medir presión del primario y probar RLS/credenciales. | Admitir staleness solo en superficies no transaccionales; lectura posterior a escritura puede volver al primario. |
| Redis/ARQ | Colas con workers aislados por prioridad y límites de concurrencia. Redis es transporte/caché, no fuente de verdad. | Recuperación y deduplicación se basan en DB, no solo en el estado efímero de Redis. |
| R2 | Media con claves generadas por servidor; archivo de datos solo con controles y retención aprobados. | Verificar bytes y permisos en backend/worker; no confiar en MIME enviado por navegador. |

### Presupuesto de latencia y saturación

No se fijan valores numéricos de P99 sin una línea base. Medir P50/P95/P99 por ruta y tenant, separar tiempo de Edge/API/DB/proveedor, e instrumentar saturación de pool, conexiones, CPU, locks, cola y errores. Definir SLOs y límites de concurrencia a partir de tráfico real y pruebas de carga representativas. Al exceder un presupuesto: limitar tasa/concurrencia, aplicar backpressure y degradar funciones no críticas; nunca omitir RLS ni ampliar consultas sin límite.

## 4. Alternativas de arquitectura

### Versión A — Edge-first y servicios event-driven

```text
Cliente → Cloudflare Enterprise / Workers → Vercel Edge SSR + SWR
                                     │
                      API gateway / servicios en Fly.io o ECS
                          ├─ servicio de checkout/pagos
                          ├─ catálogo/búsqueda
                          └─ workers de eventos
                                     │
         Outbox → broker/colas → réplicas PostgreSQL + primario
                                     └──────────► R2 cold storage
```

**Ventajas:** menor latencia para contenido público cacheable; separación de cargas; opción de escalar servicios/consumidores independientemente; potencial aislamiento operativo por grupos de tenants en una etapa madura.

**Costes y riesgos:** más componentes, políticas de invalidación y observabilidad; caché de Edge aumenta impacto de errores de keying; SWR no sirve para inventario o pagos autoritativos; distribución de datos y sharding elevan el costo de operación, migración y respuesta a incidentes. La combinación de Vercel Edge, Workers, servicios, réplicas y cold storage no está demostrada como necesaria por las métricas del piloto.

**Condición para adoptarla:** P99 de SSR/API o saturación de lecturas permanece fuera del SLO después de optimizar índices/consultas y aprovechar caché segura; existe ownership de plataforma, despliegues, claves, observabilidad, runbooks y restauración probada.

### Versión B — Monolito modular y colas dedicadas

```text
Cliente → Cloudflare CDN/WAF → Next.js SSR/ISR
                                │
                     FastAPI modular, horizontal
                       ├─ transacción → PostgreSQL primario
                       │                 └─ outbox
                       ├─ Redis/ARQ prioridad alta: tareas operativas críticas
                       └─ Redis/ARQ prioridad baja: DIAN/email/media/archivo
                                      │
                     consumidores idempotentes + conciliación

Escala posterior, según evidencia:
réplica de lectura → particiones temporales → archivo R2 → sharding
```

**Ventajas:** conserva el stack y los límites de dominio actuales; menor complejidad de despliegue; una fuente transaccional clara; ARQ/Redis ya constan como dirección en ADR-0006 y hay worker de media en el README.

**Costes y riesgos:** el primario sigue concentrando escrituras; límites de módulos y concurrencia deben mantenerse; una cola compartida sin prioridades puede retrasar checkout; las lecturas no cacheables podrían consumir DB. Se mitiga con límites de workers, colas, índices, backpressure y separación de lecturas cuando se mida la necesidad.

**Recomendación:** usar B como ruta de evolución, **sin aprobar aquí cambios a ADRs**. “Write-through agresivo” de Redis no se recomienda para inventario/precios/estados de pago: PostgreSQL continúa siendo autoridad; usar cache-aside con TTL e invalidación/versionado para vistas públicas.

### Trade-offs

| Criterio | Versión A | Versión B recomendada | Motivo |
|---|---|---|---|
| Latencia de contenido público | Potencialmente mejor con Edge/Workers y SWR. | Buena con CDN + SSR/ISR; optimizar por métricas. | A solo gana si el cache hit y la invalidación están controlados por tenant. |
| Checkout y consistencia | Requiere más coordinación entre servicios. | Menos saltos y una fuente transaccional. | Los flujos de dinero/inventario deben priorizar consistencia sobre staleness. |
| Coste inicial | Alto: más servicios y capas gestionadas. | Menor: reutiliza stack/decisiones existentes. | Evita pagar por capacidad no demostrada. |
| Complejidad operativa | Alta; múltiples runtimes, eventos y fallbacks. | Moderada; exige límites y ownership de módulos. | Mejor para el equipo actual, declarado como dos personas en README. |
| Aislamiento multi-tenant | Potente pero con más límites de confianza y caché. | Menos piezas; RLS y contexto por transacción continúan esenciales. | Ninguna topología sustituye RLS, autorización o pruebas A/B. |
| Escalamiento de lecturas | Alto, con replicas y/o motores dedicados. | Incremental: CDN, optimización, réplica bajo umbral. | Posponer hasta que `EXPLAIN (ANALYZE, BUFFERS)` y telemetría lo justifiquen. |
| Riesgo de migración | Alto si se adopta sharding temprano. | Bajo/moderado; permite extraer servicios después. | Mantener IDs, contratos y outbox facilita una evolución futura. |

## 5. Resiliencia: persistencia, entrega e idempotencia

### Transactional Outbox

La orden, la reserva y el evento de salida se escriben en **la misma transacción**. El dispatcher reclama lotes con lease/`FOR UPDATE SKIP LOCKED`, publica y marca entrega solo tras el acuse del destino. Los fallos usan reintentos con backoff+jitter, máximo de intentos, cola de revisión y alertas; nunca se elimina el evento fallido silenciosamente.

Esquema conceptual para eventos de tenant (tipos, índices, RLS y permisos deben implementarse en migración):

```sql
CREATE TABLE outbox_events (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  aggregate_type text NOT NULL,
  aggregate_id uuid NOT NULL,
  event_type text NOT NULL,
  payload jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  available_at timestamptz NOT NULL DEFAULT now(),
  attempts integer NOT NULL DEFAULT 0,
  lease_until timestamptz,
  delivered_at timestamptz,
  last_error_code text,
  UNIQUE (tenant_id, id)
);
-- Índice de despacho parcial sugerido: (available_at, created_at)
-- WHERE delivered_at IS NULL; RLS ENABLE + FORCE y políticas USING/WITH CHECK.
```

La creación de `outbox_events` debe seguir la regla de aislamiento del proyecto: tabla tenant-scoped con `tenant_id`, RLS forzado y tests de acceso cruzado. Eventos globales de plataforma deben tener un límite de seguridad separado, no una política permisiva sobre la tabla tenant. El worker procesa con permisos mínimos; no dar `service_role` general a todos los workers. Una función de despacho privilegiada, si fuese necesaria, debe ser estrecha, auditada y probada.

Una fila de outbox puede entregarse más de una vez: cada consumidor mantiene una inbox/deduplicación persistente con clave única del evento. Para webhooks, persistir `provider_event_id` y resultado de verificación antes de responder éxito; si el evento no puede confirmarse durablemente, responder de forma que el proveedor pueda reintentar. Conciliar periódicamente los pagos con el estado del proveedor. ARQ transporta ejecuciones, no reemplaza outbox/inbox.

### Idempotencia de checkout y webhooks

| Operación | Clave y restricción | Resultado de repetición |
|---|---|---|
| Crear orden/checkout | `tenant_id + idempotency_key`, hash de solicitud, índice `UNIQUE`. | Mismo hash: devolver resultado registrado; hash diferente: conflicto, no crear otra orden. |
| Evento de proveedor | Cuenta/proveedor + `provider_event_id`, único persistente. | No volver a aplicar transición ni emitir segundo evento de dominio. |
| Efecto del worker | `event_id + consumer`, único en inbox o tabla de efecto. | Reanudar/confirmar resultado previo; no duplicar factura, correo o movimiento. |

Guardar clave, hash, estado y respuesta mínima durante el periodo operacional aprobado; no guardar datos de tarjeta ni duplicar PII. La transición de pago valida firma sobre el cuerpo exacto requerido por proveedor, timestamp/ventana si soportado, cuenta, orden, tenant, monto, moneda y estado. El redirect del navegador nunca confirma pago. Reintentar una operación externa requiere conocer su idempotencia; si el proveedor no la soporta, conciliar antes de repetir efectos.

**No prometer pérdida cero:** Outbox asegura que los eventos confirmados junto con el commit sobreviven a fallas del dispatcher, sujeto a durabilidad y backups de DB. No hace atómica la transacción con una pasarela, DIAN, email o Redis. El objetivo real es entrega al menos una vez, efectos idempotentes, reintento durable, conciliación y operación manual de excepciones.

## 6. Datos, rendimiento y coste por GB

| Medida | Aplicación | Criterio/guardrail |
|---|---|---|
| Índices y consultas | Medir queries lentas; revisar `EXPLAIN (ANALYZE, BUFFERS)` en entorno representativo; índices compuestos con `tenant_id` donde aplique; GIN/FTS solo para predicados reales. | Registrar plan, cardinalidad y costo antes/después. Evitar índice redundante o GIN sin presupuesto de escritura. |
| Catálogo y búsquedas | Mantener FTS/`pg_trgm` según ADR-0006 y validar límites/paginación/timeout. | Réplica o motor externo solo si el primario queda limitado tras optimización. |
| Réplica de lectura | Aislar lecturas públicas no críticas con consultas compatibles con RLS. | Activar con cuello de lectura probado; medir lag y costo. Nunca checkout, stock, permiso o lectura tras escritura que requiera consistencia inmediata. |
| Particionamiento temporal | Evaluar `order_events`, `inventory_movements`, `decision_logs` por rango de fecha si el volumen, retención y mantenimiento lo ameritan. | Diseñar clave primaria/únicos incluyendo clave de partición, índices, RLS, migración, consultas y pruning. Probar con datos reales antes de adopción. |
| Partición por tenant | No introducir particionado hash/lista por tenant ni sharding en el piloto. | Solo con cardinalidad/volumen y límites de capacidad medidos; el diseño debe preservar integridad global y procedimientos cross-shard. |
| Archivo frío | Exportar lotes elegibles a R2 cifrado, comprimido y con manifiesto (rango, cantidad, checksums/hash, versión de schema, fecha). Validar restauración y acceso auditado. | Exportar no autoriza borrar. Retención y borrado en DB requieren política aprobada por Legal/Contabilidad y pruebas de recuperación. |
| TTL | Limpiar carritos abandonados según política de producto; purgar media huérfana solo después de comprobar ausencia de referencias y ventana de recuperación. | Retención de PII, evidencia legal y datos fiscales prevalecen sobre TTL técnico. Borrado idempotente y auditable. |

La propuesta de archivar automáticamente a los 90 días **no se adopta como regla de borrado**. D-10 mantiene pendiente la retención por categoría; el plazo de cinco años es provisional en documentación y debe validarse por asesoría legal/contable. Separar logs operacionales, gobernanza, órdenes y documentos fiscales; aplicar retención por base jurídica y categoría, no por una cifra única. R2 reduce presión de DB solo si se verifica costo total, recuperación, cifrado, control de acceso y obligaciones de retención.

## 7. Auditoría multi-dominio y matriz de riesgos

Severidades expresan prioridad para salida a producción, condicionadas por la existencia de las rutas/proveedores. Ninguna fila es afirmación de incidente ocurrido.

| ID | Dominio / severidad | Riesgo o brecha y evidencia | Mitigación accionable |
|---|---|---|---|
| SEC-01 | Seguridad — Alta | `03-tenancy.md` documenta 10 pruebas de aislamiento; quedan pendientes binding host+JWT, webhook, preview y caché completa (el vector de caché solo tiene cobertura parcial). Rutas aún no construidas no están protegidas por cobertura futura. | Completar vectores faltantes con tenants A/B, JWT/JWKS realista, proveedor simulado y CDN/cache key tenant+versión. Exigir RLS `ENABLE` + `FORCE`, `USING`/`WITH CHECK`; `app_rw` sin `BYPASSRLS`; fallar cerrado. |
| SEC-02 | Seguridad/pagos — Alta | README/ADRs describen pagos como dirección, pero no demuestran despliegue de checkout/webhooks ni outbox/inbox. Reintentos sin unicidad pueden duplicar estados o efectos. | No habilitar pagos reales hasta firma verificada, replay controlado, idempotencia DB, reserva atómica, conciliación y pruebas de concurrencia/fallo. Aplicar el flujo de la sección 5. |
| SEC-03 | Seguridad/media — Media | README declara URL prefirmada, procesamiento AVIF/WebP y limpieza huérfana. El repositorio por sí solo no prueba límites operativos contra payloads extremos ni configuración de bucket/CDN. | Verificar límites de bytes/píxeles/tiempo/concurrencia; comprobar MIME por bytes, formatos admitidos, aislamiento del worker, ACL, TTL de URL y estado no publicable en fallo. Añadir casos de upload bomb y MIME discordante. |
| SEC-04 | Seguridad/caché — Alta | La documentación registra cobertura incompleta de cache isolation. Cachear respuesta por URL sin tenant/versión puede exponer tienda o contenido no publicado. | Mantener caché CDN deshabilitada para respuestas no verificadas; clave canónica incluye tenant+recurso+versión; invalidación en publish y pruebas de dos hosts, preview, stale y bypass de cache. |
| LEG-01 | Legal/privacidad — Alta | D-09 y ADR-0009 son propuestas; no se demuestra aceptación versionada del DPA ni gate de publicación. | Obtener aprobación jurídica del DPA y definir aceptante/versión/hash/evidencia; implementar gate fail-closed y pruebas antes de publicación. No presentar el control como desplegado mientras no exista. |
| LEG-02 | Legal/retención — Alta | D-10 mantiene abiertas DSR, retención y región; cinco años es provisional y no habilita purga automática de órdenes/logs. | Asesoría colombiana y contable aprueba matriz dato→base→retención→anonimización/borrado. Separar archivo de supresión; mantener suspensión por litigio/retención y reconstrucción desde backup. |
| LEG-03 | Legal/incidentes — Alta | D-12 está abierta. La referencia de 72 horas no debe presentarse como plazo general confirmado para toda brecha bajo ley colombiana; el objetivo de notificación interna de 24 h es contractual/propuesto. | Aprobar responsables, criterios, canal y tiempos por jurisdicción/rol con asesoría colombiana. Runbook técnico preserva evidencia y permite avisar pronto al tenant sin sustituir sus deberes. |
| LEG-04 | Legal/comercio — Media | D-13 pendiente; el storefront debe distinguir comerciante/merchant of record de Growup. El rol de responsable/encargado depende de cada finalidad, no solo de una cláusula. | Tenant gestiona oferta, producto, garantías, devoluciones y fondos conforme al modelo; Growup documenta finalidades propias (billing, seguridad, soporte) y de encargo en contratos/avisos revisados. Publicar políticas solo con aprobación. |
| LEG-05 | Legal/PCI — Alta | D-11 y ADR-0010 pendientes; hosted checkout reduce alcance, pero no basta para declarar SAQ A ni que PCI esté resuelto. | Confirmar redirect/widget, alcance con adquirente/pasarela y responsable PCI; proteger scripts, CSP, MFA y escaneo según elegibilidad. Mantener PAN/CVV fuera de Growup. |
| ARC-01 | Arquitectura — Media | Activar de inicio réplicas, particiones mensuales, archivo a 90 días y sharding añade complejidad antes de que haya métricas. | Aprobar B como recomendación; fijar umbrales de adopción con telemetría, `EXPLAIN`, crecimiento/GB, lag, costo y capacidad de recuperación. |
| ARC-02 | Arquitectura — Media | PgBouncer y caches write-through de la propuesta inicial podrían divergir de ADR-0008 (Supavisor transaccional + `SET LOCAL`) y comprometer consistencia de stock/pago. | Mantener pooler aceptado; cualquier reemplazo pasa por ADR y pruebas. Redis solo acelera vistas tolerantes a staleness, nunca fuente de verdad transaccional. |
| OPS-01 | Resiliencia — Alta | Redis/ARQ y worker de media constan en README, pero una cola sin outbox durable puede perder trabajo entre commit y enqueue. | Outbox antes de pagos/DIAN; publisher reanudable, retry/backoff, DLQ/revisión, métricas de edad y backlog, alertas, replay seguro y conciliación. |
| OPS-02 | Resiliencia — Media | El documento base V2 menciona Celery/NATS, Meilisearch y otras piezas que difieren de decisiones vigentes; usarlo literalmente puede expandir stack y romper consistencia arquitectónica. | Priorizar ADR-0006/0008 y decisiones vigentes. Tratar el documento base como legado; no introducir Celery, NATS o buscador dedicado sin ADR/medición. |
| OPS-03 | Datos/operación — Media | Réplica, archivo y particionado pueden provocar staleness, RLS inconsistente, errores de restauración o aumento de costo si se lanzan sin runbooks. | Probar failover/restauración, RPO/RTO, lag y export/import; añadir ownership, dashboards, límites de conexión y simulacro antes de habilitar. |

### STRIDE resumido

| Amenaza | Superficie | Control requerido |
|---|---|---|
| Spoofing | Host, JWT, webhook, tenant | Resolver host registrado; JWKS + `iss/aud/exp/nbf`; validar cuenta/proveedor/firma; no confiar en header ni body. |
| Tampering | Precio, inventario, estado de orden | Recalcular en servidor; constraints y transición atómica; firma y hash de solicitud; auditoría. |
| Repudiation | Aceptaciones legales, publicación, pago | Registros versionados/append-only, `trace_id`, actor seudónimo, evidencia íntegra y retención aprobada. |
| Information disclosure | RLS, cache, logs, R2, backup | FORCE RLS; claves tenant-aware; no PII/secretos en logs; ACL y cifrado; pruebas cross-tenant. |
| Denial of service | Upload, búsqueda, checkout, cola | Límites de payload y consultas; rate limit Edge/API; cuotas de concurrencia; backpressure y límites de worker. |
| Elevation of privilege | `service_role`, plataforma, soporte | Mínimo privilegio, MFA, acceso temporal con motivo/consentimiento, auditoría y revisión de cuatro ojos. |

## 8. Roles, privacidad y cumplimiento

- **Merchant of Record:** la dirección aceptada en ADR-0004 es que el tenant vende al comprador y recibe fondos; Growup presta tecnología y factura su propia suscripción. Wompi checkout del comprador y Stripe Billing de Growup son flujos separados. No crear split ni custodia de fondos en el MVP.
- **Protección de datos:** modelar responsable/encargado por finalidad, categorías, subencargados, soporte, billing y seguridad. La asignación contractual no borra responsabilidades que surjan de la operación real. Revisar Ley 1581, reglamentación aplicable, transferencias y deberes ante SIC con asesoría local.
- **DPA/onboarding:** aceptación debe pertenecer al owner autorizado del tenant, con versión/hash/fecha y evidencia definida por D-09; alta puede quedar `pending_legal`. Publicación bloqueada hasta aceptación vigente una vez aprobada e implementada la política.
- **DSR:** recibir, verificar identidad, clasificar, asignar al tenant o a Growup según finalidad, responder y auditar. Preferir anonimización selectiva cuando haya base legal de conservación; no borrar registros fiscales/auditoría por una solicitud sin dictamen. No prometer borrado de backups sin política documentada.
- **Brechas:** el encargado prepara evidencia y avisa al responsable dentro del SLA contractual; el responsable determina notificaciones a titulares/autoridad según los hechos y normativa. El protocolo, plazo y criterio aplicables son D-12 pendiente; no fijar 72 h como regla colombiana universal.
- **Consumidor y facturación:** la política de retracto/devolución/garantía y responsabilidades del comerciante siguen D-13; proveedor/factura/notas crédito siguen decisiones fiscales pertinentes. No afirmar cumplimiento DIAN por tener un worker o integración futura.

Esto es guía de arquitectura, no asesoría legal. D-09 a D-16 permanecen abiertas; este documento no las convierte en decisiones aceptadas ni reemplaza revisión jurídica, contable o de la pasarela.

## 9. Alineación de ADR y decisiones siguientes

| Referencia | Estado observado en documentación previa | Tratamiento en este plan |
|---|---|---|
| ADR-0003 — identidad, tenancy y RLS | Aceptada | Mantener fuente host→tenant, JWT/membership, transacción `SET LOCAL`, RLS forzado y pruebas. |
| ADR-0004 — pagos y merchant of record | Aceptada | Mantener tenant como comerciante, checkout alojado, sin custodia/split; completar idempotencia, webhooks y conciliación antes de live. |
| ADR-0006 — stack satélite | Aceptada | Reusar ARQ/Redis, R2, PostgreSQL FTS/GIN y Sentry/OpenTelemetry; no introducir Celery/NATS/buscador externo sin evidencia/ADR. |
| ADR-0007 — gobernanza | Aceptada | Mantener evidencia append-only con acceso y retención gobernados; archivo no equivale a borrar. |
| ADR-0008 — topología | Aceptada | Mantener Vercel + Fly.io + Supabase, pooler de transacción acordado y `SET LOCAL`. Este plan recomienda no supersederla. |
| ADR-0009 — privacidad/DPA/DSR | Propuesta | No aceptar ni cambiar estado. Requiere revisión legal y cierre de criterios D-09/D-10. |
| ADR-0010 — PCI | Propuesta | Completar después de spike con pasarela y validación de alcance. |
| ADR-0011 — email | Propuesta | Seleccionar proveedor, región, identidad por tenant y fallback tras spike; entrega via outbox. |
| Próximos ADR candidatos | No creados | ADR sobre criterios de réplica/particionamiento/archivo; ADR sobre contrato outbox/inbox e idempotencia si ADR existentes no los cubren. Confirmar numeración y ownership en `docs/adr/README.md` antes de crear. |

**Cierre en este documento:** la Versión B queda seleccionada únicamente como **recomendación de arquitectura**. No se cambia el estado de ADR-0008 ni se declara un decisor/aprobación inexistente. El cierre formal requiere owner de Producto/Ingeniería, revisión de impacto y actualización conforme al proceso de ADR.

## 10. Hoja de ruta post-piloto

| Fase | Trabajo | Salida verificable |
|---|---|---|
| Meses 1–3 — Estabilización | Sentry + OpenTelemetry; dashboards por ruta/tenant sin PII; baseline P50/P95/P99 y pool; límites de tasa Edge/API; revisión de índices GIN/FTS y `EXPLAIN`; completar tests cross-tenant; implementar outbox/idempotencia antes de pagos reales; runbooks de Redis/DB/proveedor. | SLO y budgets acordados; pruebas de carga y tenant A/B en CI; reintentos/replay probados; revisión legal de gates antes de habilitar comercio. |
| Meses 4–8 — Escala medida | Activar réplica solo ante cuello de lecturas; enrutar catálogo público tolerante a lag; diseñar particiones mensuales solo para tablas que lo necesiten; export a R2 en modo archivo verificable; autoescalado de API/workers con límites; políticas de cleanup aprobadas. | Dashboard de lag, conexiones y GB; restore/export testado; particionado con plan de migración y rollback; reporte de costo comparativo. |
| Mes 9+ — Alta disponibilidad | Evaluar grupos de tenants/sharding; capacidad multi-región de Edge y recuperación regional; migraciones expand/contract sin downtime; failover/restore y estrategia de claves/secrets. | ADR aprobada con umbrales; simulacro de RPO/RTO; migración ensayada con datos representativos; plan operativo y de costos. |

**Gates que no esperan al calendario:** no procesar pagos reales sin validación de webhook e idempotencia; no publicar tiendas con DPA requerido sin aceptación cuando D-09 esté aprobado; no activar purgas por antigüedad sin matriz de retención aprobada; no enrutar checkout/inventario a réplica o caché.

## 11. Estructura documental y trazabilidad

Conservar rutas y referencias existentes; **no mover ni renombrar** documentación del piloto en esta tarea. Adoptar la siguiente organización de forma incremental:

```text
docs/
  architecture/     decisiones de topología, datos, escala y diagramas
  adr/              decisiones técnicas versionadas y estado de aprobación
  security/         threat model, controles, pruebas, incidentes
  legal/            DPA, DSR, consumidores, brechas y revisión jurídica
  operations/       SLO, runbooks, backup/restore, despliegues
  regulatory/       matrices de obligaciones y fuentes revisadas
  decisions-pending.md  decisiones de negocio pendientes (ruta actual se preserva)
apps/
  storefront/
  admin/
services/
  api/
packages/
  contracts/
supabase/
  migrations/
  tests/
infra/
```

Cada documento de dominio enlaza los ADR que implementa; cada ADR enlaza la spec, migración, pruebas y runbook; cada control declara **propuesto / implementado / verificado** con evidencia. No mover `docs/architecture/04-flujos-seguridad.md`, `docs/legal/flujos.md` ni los diagramas existentes sin una migración de enlaces independiente.

## 12. Criterios de aceptación para ejecutar la propuesta

- [ ] ADR-0008 permanece intacta hasta revisión y aceptación formal.
- [ ] Cobertura de los vectores cross-tenant documentados completa en CI, incluidos host/JWT, webhook, preview y caché.
- [ ] Outbox/inbox/idempotency y conciliación probados ante reintentos, concurrencia, caída de Redis y caída de proveedor.
- [ ] Pagos usan primario; ningún redirect, caché o lectura de réplica confirma un cobro.
- [ ] Plan de prueba de carga registra P99, utilización y errores por ruta; sin umbrales inventados.
- [ ] RLS habilitado y forzado en nuevas tablas tenant-scoped; tests SELECT/INSERT/UPDATE/DELETE con tenants A/B.
- [ ] DPA, retención, DSR, incidentes, PCI, correo y políticas de consumidor se mantienen como gates legales abiertos hasta aprobación pertinente.
- [ ] Archivo a R2 tiene manifiesto, checksums, control de acceso, prueba de restauración y política de borrado aprobada.
- [ ] Runbooks cubren backpressure, DLQ, reintento, conciliación, restauración y acceso privilegiado.

## Referencias del repositorio

- [ADR-0003 — identidad, tenancy y RLS](../adr/0003-identidad-tenancy-rls.md)
- [ADR-0004 — pagos y merchant of record](../adr/0004-pagos-checkout-merchant-of-record.md)
- [ADR-0006 — stack satélite](../adr/0006-stack-satelite.md)
- [ADR-0008 — topología de despliegue](../adr/0008-topologia-despliegue.md)
- [ADR-0009 — privacidad, DPA y DSR](../adr/0009-privacidad-dpa-dsr.md)
- [ADR-0010 — PCI](../adr/0010-checkout-pci-scripts.md)
- [ADR-0011 — email transaccional](../adr/0011-email-transaccional.md)
- [Tenancy y threat model](03-tenancy.md)
- [Flujos de seguridad](04-flujos-seguridad.md)
- [Flujos legales](../legal/flujos.md)
- [Decisiones pendientes](../decisiones-pendientes.md)
- [Documento base V2 (legado)](../arquitectura-plataforma-inteligente-cordiasolve-v2.md)
