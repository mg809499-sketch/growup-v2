# ADR-0006 — Stack satélite: búsqueda, colas, media y observabilidad

- **Estado:** Aceptada
- **Fecha:** 2026-10-21
- **Decisores:** equipo de ingeniería
- **Relacionado con:** ADR-0004, ADR-0005, ADR-0008, `.kiro/steering/tech-stack.md`

## Contexto

El MVP comercial necesita búsqueda de catálogo, trabajos en segundo plano (emails, facturas, media, webhooks, conciliación), almacenamiento de imágenes y documentos, contratos tipados y observabilidad. El documento V2 menciona varias alternativas (Celery/NATS, Meilisearch/Typesense, Cloudinary, LangFuse) sin elegir. La regla es no añadir infraestructura que el MVP no justifique.

## Decisión

### 1. Búsqueda: PostgreSQL FTS

- `tsvector` generado en `products` (nombre, descripción, tags, SKU y variantes) con configuración `spanish`.
- Índice GIN y `pg_trgm` para tolerancia a errores de tipeo.
- Filtros por categoría, precio, atributos y disponibilidad; facets calculadas en SQL.
- Paginación por cursor; límite máximo de resultados.
- Reindexación por trigger o job; un job de verificación compara conteos.
- **Meilisearch/Typesense** se adopta solo si se cumple alguno de estos umbrales: catálogo > 50.000 productos, p95 de búsqueda > 300 ms o necesidad de relevancia avanzada. La interfaz `SearchPort` permite el cambio.

### 2. Colas y jobs: Redis + ARQ

- **ARQ** sobre Redis para jobs asíncronos: emails transaccionales, emisión de facturas, procesamiento de media, reintentos de webhooks, purga de caché, conciliación y reindexación.
- Redis separado por uso: `cache`, `queue`, `rate-limit` (bases lógicas o instancias distintas).
- Jobs idempotentes con `job_id` estable; reintentos con backoff exponencial; dead-letter queue y alerta.
- Cron jobs: conciliación diaria, verificación de cadena de auditoría, limpieza de reservas expiradas, backups lógicos.
- **Celery/NATS** no se adoptan en el MVP: ARQ cubre el volumen esperado con menos piezas.

### 3. Media: Cloudflare R2

| Bucket | Acceso | Uso |
|---|---|---|
| `growup-catalog-{env}` | Público de solo lectura vía CDN | Imágenes de catálogo y contenido |
| `growup-private-{env}` | Privado, URL firmada | Facturas, documentos, exports |
| `growup-backups-{env}` | Privado | Dumps lógicos |

- Uploads vía URL prefirmada; el navegador nunca recibe credenciales de R2.
- Prefijo obligatorio `tenant/{tenant_id}/...`.
- Validación en el worker: MIME real, tamaño máximo (10 MB imágenes, 20 MB PDF), dimensiones máximas (6000×6000), protección contra decompression bombs.
- Imágenes: strip de EXIF, corrección de orientación, variantes AVIF/WebP en anchos 320/640/960/1280/1600, `blurhash`.
- PDFs: antivirus (ClamAV) y allowlist; nunca se sirven desde el bucket público.
- Nombres de archivo aleatorios (UUID); el nombre original se guarda como metadata, no en la clave.
- Cloudflare CDN con cache inmutable (`Cache-Control: public, max-age=31536000, immutable`) para variantes con hash.
- **Cloudinary** no se adopta: R2 ya es el almacenamiento elegido y evita otro vendor.
- Implementación: `boto3` para S3/R2 y URLs prefirmadas; `Pillow` para AVIF/WebP, orientación y strip de EXIF; `blurhash` para el placeholder; `arq` para el worker de procesamiento.

### 4. Observabilidad

- **Sentry** para errores en storefront, admin, API y workers, con `tenant_id`, `trace_id` y release.
- **OpenTelemetry** para trazas y métricas; exportador OTLP configurable (Sentry, Grafana Cloud o colector propio).
- Logs estructurados JSON a stdout con `timestamp`, `level`, `service`, `env`, `tenant_id`, `trace_id`, `request_id`, `route`, `status`, `latency_ms`.
- Prohibido loggear PII, tokens, secretos, payloads completos de pago o prompts completos.
- Correlación Next.js → FastAPI → worker mediante `traceparent`/`trace_id`.
- Alertas mínimas:
  - 5xx > 1% durante 5 min.
  - p95 API > 500 ms durante 10 min.
  - Profundidad de cola > 100 o dead-letter > 0.
  - Fallos de webhook > 5 en 15 min.
  - Verificación de cadena de auditoría fallida.
  - Conexiones a Postgres > 80% del límite.
- **LangFuse** se difiere hasta que exista IA conversacional (D-05).

### 5. Contratos

- FastAPI genera OpenAPI 3.1.
- `packages/contracts` genera tipos TypeScript con `openapi-typescript`.
- CI falla si el OpenAPI cambió y los tipos no se regeneraron.
- Los tipos de bloques se comparten entre admin y storefront desde `packages/contracts` (o `packages/ui`), no se duplican a mano.

### 6. Email transaccional

- Proveedor recomendado: **Resend** (DX y deliverability), con SMTP de respaldo.
- Remitentes por dominio verificado: `no-reply@growup.com` para plataforma; el comerciante puede usar su dominio en fase 2.
- Plantillas versionadas en código; texto plano alternativo.
- Magic links, confirmación de orden, factura y alertas operativas.
- Rebotes y quejas se procesan por webhook y se registran; no se reintenta indefinidamente.

### 7. Feature flags y rate limiting

- `tenant_features` en Postgres para capacidades por plan/tenant; sin servicio externo en el MVP.
- Rate limiting con token bucket en Redis por tenant, IP y ruta; límites más estrictos en auth, checkout y webhooks.
- En el borde, Cloudflare/Vercel aplica límites adicionales por IP.

### 8. Backups y secretos

- Supabase PITR + dump lógico diario a R2 + prueba de restauración trimestral.
- R2 con versioning y lifecycle policy.
- Secretos en `.env` local, GitHub Environments, Fly secrets y Vercel env; credenciales de pago de tenants en Supabase Vault/KMS.
- Rotación documentada de claves de pasarela, JWT y firmas de preview.

## Alternativas consideradas

| Alternativa | Pros | Contras | ¿Por qué no? |
|---|---|---|---|
| A. Meilisearch desde el día 1 | Relevancia y facets potentes | Otro servicio, sincronización y costo | Postgres FTS cubre el MVP |
| B. Postgres FTS + pg_trgm (elegida) | Cero infraestructura extra; transaccional | Menos relevancia avanzada | Suficiente para el catálogo piloto |
| C. Celery + Redis | Madurez y ecosistema | Más pesado y más configuración | ARQ es suficiente |
| D. Cloudinary | Transformaciones listas | Costo y dependencia | R2 + worker propio |
| E. Kafka/NATS | Altísimo throughput | Complejidad operativa | El volumen del MVP no lo justifica |
| F. LangFuse ahora | Trazas de IA | No hay IA en el MVP | Se difiere con D-05 |

## Consecuencias

### Positivas

- Menos servicios que operar y menor costo inicial.
- Búsqueda y datos transaccionales en la misma base, sin sincronización.
- Media validada y servida por CDN con cache inmutable.
- Trazas correlacionadas entre frontend, API y workers.

### Negativas / deuda asumida

- Postgres FTS tiene límites de relevancia y facets; habrá que migrar si el catálogo crece.
- ARQ es menos maduro que Celery; hay que cuidar reintentos y visibilidad.
- El procesamiento de imágenes consume CPU del worker.
- La observabilidad multi-proveedor requiere disciplina de configuración.

### Neutras

- `SearchPort`, `QueuePort` y `StoragePort` permiten cambiar de proveedor sin tocar los dominios.
- El email transaccional es un proveedor externo; se puede cambiar por SMTP.

## Cómo se verifica

- Búsqueda en español con tildes, sin tildes y con errores de tipeo; p95 < 300 ms con 10.000 productos.
- Job duplicado no envía dos emails ni emite dos facturas.
- Job fallido llega a dead-letter y genera alerta.
- Imagen con EXIF: se sirve sin metadatos y con variantes correctas.
- PDF infectado (EICAR) se rechaza.
- URL firmada expira y no se puede reutilizar.
- `trace_id` aparece en logs de Next, API y worker.
- CI falla si los contratos TypeScript están desactualizados.

## Pendientes

- Confirmar proveedor de email y dominio de envío.
- Definir región de R2 y del CDN.
- Definir el colector OTLP final (Sentry, Grafana Cloud o propio).
- Umbral exacto para migrar a Meilisearch.

## Enlaces

- [ADR-0004](0004-pagos-checkout-merchant-of-record.md)
- [ADR-0005](0005-contenido-y-publishing.md)
- [Tech stack steering](../../.kiro/steering/tech-stack.md)
