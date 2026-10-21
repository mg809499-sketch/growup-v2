# ADR-0005 — Modelo de contenido y publishing

- **Estado:** Propuesta (requiere revisión)
- **Fecha:** 2026-10-21
- **Decisores:** equipo de producto e ingeniería
- **Relacionado con:** ADR-0001, D-05, D-07

## Contexto

El storefront no renderiza código por tenant: renderiza una **versión publicada** de una página compuesta por bloques. El admin tiene un builder drag-and-drop. Publicar debe ser atómico, con preview y rollback, y el mismo motor debe producir dos marcas visualmente distintas (ropa y joyería) sin forks.

Restricciones:

- Nada de HTML arbitrario: los bloques tienen schemas cerrados.
- Una versión publicada no se muta; se reemplaza.
- El tenant se resuelve por host (ADR-0003).
- El storefront debe cachear y invalidar por tenant/página.
- El builder debe tolerar autosave y edición concurrente sin pisar cambios.

## Decisión

### 1. Modelo de datos

| Tabla | Campos principales | Notas |
|---|---|---|
| `pages` | `id`, `tenant_id`, `slug`, `title`, `status`, `draft_version_id`, `published_version_id`, timestamps | Único `(tenant_id, slug)` |
| `page_versions` | `id`, `tenant_id`, `page_id`, `version`, `layout jsonb`, `schema_version`, `created_by`, `created_at`, `published_at`, `notes` | Inmutable al publicar |
| `themes` | `id`, `tenant_id`, `name`, `preset`, `tokens jsonb`, `is_active`, timestamps | Presets `ropa`, `joyeria` |
| `media_assets` | `id`, `tenant_id`, `r2_key`, `mime`, `width`, `height`, `alt`, `blurhash`, `variants jsonb`, timestamps | Prefijo `tenant/{tenant_id}/` |
| `tenant_settings` | `tenant_id`, `navigation jsonb`, `seo_defaults jsonb`, `shipping_zones jsonb`, timestamps | Schemas cerrados |

- `page_versions.layout` es un documento JSONB con un array de bloques. Cada bloque tiene `id` estable, `type`, `props` y opcionalmente `children`.
- La validación se hace con Pydantic v2 (discriminated unions) al guardar y al renderizar.
- `schema_version` permite migrar layouts antiguos sin romper el storefront.
- No se guardan referencias cross-tenant: un bloque de producto solo puede referenciar productos del mismo `tenant_id`.

### 2. Draft, autosave y concurrencia

- El borrador es mutable y se guarda con control optimista por `version` (`If-Match` / `expected_version`).
- Autosave crea una revisión de borrador, no una versión publicada.
- Si dos editores guardan, el segundo recibe `409 VERSION_CONFLICT` y debe recargar o fusionar.
- El editor puede bloquear la página por sesión (`editing_by`, `editing_since`) con TTL, pero el bloqueo es una ayuda, no la fuente de verdad.
- El historial de borradores se conserva con retención configurable.

### 3. Publish atómico

1. Validar el layout contra el schema y el registry.
2. Validar permisos (`content.publish`) y reglas de gobernanza.
3. Renderizar un preview server-side para detectar errores.
4. En una transacción: crear `page_version` inmutable, actualizar `pages.published_version_id`, escribir un evento en el outbox.
5. Un worker consume el outbox y purga la caché del storefront (`tenant:{tenant_id}:page:{slug}`).

- Si falla la validación o el render, no se publica nada.
- Rollback = apuntar `published_version_id` a una versión anterior y emitir el mismo evento de purga. No se borra la versión nueva.
- Publicar es idempotente por `page_version_id` y `publish_request_id`.

### 4. Block registry cerrado

Tipos iniciales del MVP:

- `header`, `footer`
- `hero`
- `editorial_split`
- `product_grid`
- `product_carousel`
- `collection_grid`
- `image_banner`
- `rich_text`
- `quote`
- `gallery`
- `video_embed` (solo proveedores allowlist: YouTube/Vimeo)
- `faq`
- `newsletter`
- `spacer`
- `columns`

Reglas:

- Cada bloque tiene schema Pydantic/Zod, límites de items, textos alternativos obligatorios en imágenes y validación de links.
- `rich_text` acepta un subconjunto de Markdown (negrita, cursiva, listas, links); se sanea en el servidor. No se acepta HTML.
- No hay bloques de código, scripts, iframes libres ni CSS arbitrario.
- Un bloque desconocido se renderiza con un fallback seguro y se registra; nunca rompe la página.
- El registry se versiona en código; añadir un bloque requiere tests y revisión de diseño.

### 5. Temas y tokens

- Los tokens viven en `themes.tokens` con un schema cerrado: color, tipografía, espaciado, radios, sombras y ancho máximo.
- El storefront genera CSS variables a partir de los tokens; no se inyecta CSS del admin.
- Presets iniciales:
  - `ropa`: Sol de Calle (editorial, streetwear, alto contraste).
  - `joyeria`: Aurélia Atelier (quiet luxury, serif, mucho aire).
- Un tenant puede tener varios temas, pero solo uno activo en el MVP.
- Cambiar tokens no requiere republicar páginas; se invalida la caché del tema.

### 6. Renderizado y caché

- El storefront resuelve tenant y página, pide `GET /v1/storefront/pages/{slug}` y recibe la versión publicada + tema + settings.
- `BlockRenderer` mapea `type` → componente. Server Components por defecto; Client Components solo para carruseles, menú móvil, galería y compra.
- Imágenes con `next/image`, `sizes` correctos y `priority` solo en el hero.
- Caché:
  - CDN/Next con `revalidate` corto (60 s) y stale-while-revalidate.
  - Purga por tag en publish/rollback.
  - La página de preview no se cachea y lleva `noindex`.
- Si la API no responde, el storefront sirve la última versión cacheada si existe; si no, un fallback 503 controlado.

### 7. Preview

- Token firmado de corta duración con `tenant_id`, `page_id`, `version_id`, `exp` y `scope=preview`.
- URL `https://{slug}.growup.com/preview/{page_id}?token=...`.
- El preview renderiza el borrador o una versión específica; no es indexable y no se comparte fuera del admin.
- El token se valida en el servidor; nunca se confía en un query param sin firma.

### 8. SEO y accesibilidad

- Metadatos por página: title, description, canonical, OG image.
- Sitemap y robots por tenant.
- JSON-LD de producto generado desde el catálogo, no desde bloques.
- Los bloques validan jerarquía de headings, alt text y contraste de tokens.
- Tests de accesibilidad con axe en las páginas de ejemplo.

## Alternativas consideradas

| Alternativa | Pros | Contras | ¿Por qué no? |
|---|---|---|---|
| A. HTML libre por tenant | Máxima flexibilidad | XSS, imposible de mantener y de estilizar | Prohibido por producto |
| B. JSONB versionado + registry (elegida) | Publish atómico, rollback, schemas seguros | Requiere validación y migraciones de schema | Mejor equilibrio |
| C. Tabla normalizada de bloques | Consultas y edición granular | Versionar un árbol normalizado es complejo | El documento versionado es más simple |
| D. Mutar la versión publicada | Menos tablas | Sin rollback ni cache consistente | Viola el principio de publish atómico |

## Consecuencias

### Positivas

- Publicar y revertir son operaciones atómicas y auditables.
- El builder no puede inyectar HTML ni romper el diseño.
- Dos marcas distintas comparten el mismo motor y registry.
- El caché se invalida por tenant/página sin purgas globales.

### Negativas / deuda asumida

- Hay que mantener schemas y migraciones de bloques.
- El autosave y el control de concurrencia añaden complejidad al admin.
- La purga de caché depende de un outbox y de un worker saludable.
- El preview firmado requiere gestión de claves.

### Neutras

- Los temas son datos, no código; un diseño nuevo se añade como preset.
- El registry puede crecer, pero cada bloque nuevo tiene costo de diseño y tests.

## Cómo se verifica

- Publicar una página inválida devuelve `400` y no cambia `published_version_id`.
- Publicar dos veces la misma versión es idempotente.
- Rollback sirve la versión anterior y purga la caché.
- Dos editores concurrentes: el segundo recibe `409`.
- Un bloque desconocido no rompe el render.
- Un token de preview expirado devuelve `401`.
- Un slug de otro tenant devuelve `404`.
- Tests de accesibilidad y de contrato de bloques en CI.

## Pendientes

- Lista final de bloques del MVP y sus props exactas.
- Schema de tokens y presets visuales (se alinea con el export de v0).
- Política de retención de borradores y versiones.
- Scheduled publish (fuera del MVP).

## Enlaces

- [ADR-0001](0001-producto-saas-builder.md)
- [Prompt v0](../prompts/v0-storefront.md)
- [D-05 y D-07](../decisiones-pendientes.md)
