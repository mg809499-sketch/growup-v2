# Sincronización frontend, apps y Docker con el plan maestro — cambios pendientes

> Fecha: 2026-11-10 · Complementa `plan-maestro-growup.md` (F1, F3, F4, F6) · **Ninguno de estos cambios está aplicado aún.** Es la especificación ejecutable para cuando se salga del modo plan. Regla: cada bloque aquí indica archivo(s) exactos, qué cambia y por qué, alineado con las decisiones de `decisiones-proveedores-growup.md`.

## 0. Mapa de cambios por superficie

| Superficie | Objetivo de sincronización | Fase |
|---|---|---|
| `apps/storefront` | De hardcodeado a dirigido por datos: ISR + purga, bloques, tema desde API, checkout, páginas legales, SEO | F3, F4, F6 |
| `apps/admin` | Builder, pedidos, billing/suscripción, gate legal, soporte | F3, F4, F5 |
| `packages/contracts` | Regenerar desde OpenAPI (bloques, páginas, órdenes, errores 422 envelope) | F3, F4 |
| `packages/config` (nuevo) | Utilidades compartidas (formato precio/fecha/bytes, constantes) | F0-06 |
| `packages/brand` / `apps/frontend` / `frontend/` | Borrado/archivo (zombies de la auditoría) | F0-04 |
| `infra/` + Dockerfiles | API/worker containerizados, compose local completo y endurecido, fly.toml | F1 |
| `.github/workflows/ci.yml` | Docker build+Trivy, e2e job, deploy staging/prod | F1-07 |
| Env/examples | Variables coherentes y completas en ambos apps (.env.example) | F1 |

---

## 1. `apps/storefront` — cambios detallados

### 1.1 `app/layout.tsx`
- **Antes:** `data-theme={defaultTheme()}` desde `GROWUP_DEFAULT_THEME`; si `getBootstrap()` falla → header/footer desaparecen silenciosamente; 5 fuentes cargadas siempre.
- **Después:**
  - Tema dinámico: CSS vars inyectadas en `<html>`/`body` desde `bootstrap.theme.tokens` (o `data-theme` por `tenant.settings.theme` + stylesheet por tenant en R2/static). Fuente: `tenant.settings.font_display/font_body` vía `next/font` con subset `latin` — cargar solo la familia activa (`ropa`: Anton+Space Grotesk; `joyeria`: Playfair+Plus Jakarta Sans). Eliminar carga universal de las 5 familias.
  - Si bootstrap falla: renderizar página de **"Tienda en configuración"** (estado controlado, layout mínimo, contacto soporte@growup.com) en vez de contenido sin header/footer. Log estructurado `bootstrap_failed` con `host`.
  - Header/footer pasan a ser **bloques** (`components/blocks/header.tsx`, `footer.tsx`) renderizados desde el `page_version` publicado; durante F3 se mantiene el header actual como fallback hasta migrar el seed de páginas.
  - Metadata: `generateMetadata` desde `bootstrap.settings` (SEO por tenant) con `noindex` si `legal_status='pending_legal'`.

### 1.2 `lib/api.ts` (cliente storefront)
- Mantener `getStorefrontHost()` (host→tenant vía API, `X-Storefront-Host`) pero:
  - Añadir `fetch` con `next: { tags: [`tenant:{host}`], revalidate: 3600 }` en `getBootstrap`, `listProducts`, `getProduct`, `getPage`.
  - Eliminar `cache: 'no-store'` y `force-dynamic` en páginas una vez ISR esté activo (mantener `force-dynamic` solo en carrito).
  - Errores: mapear envelope `AppError` nuevo (`VALIDATION_ERROR` incluido por F2-07); `ApiError.details` expuesto para debug; 404 → `notFound()`; `LEGAL_NOT_ACCEPTED` → UI de configuración; sin filtrar internals.
  - Tipar `getPage(slug)` → `PageVersion` desde `@growup/contracts`.
- Añadir `lib/cart.ts`: `getCart/addToCart/updateItem/removeItem` contra `POST/GET /v1/storefront/cart*` (cookie httpOnly del server, `credentials: 'include'`). **Cero estado de carrito en cliente**; snapshot desde servidor en cada render.
- Añadir `lib/legal.ts`: carga `/legal/devoluciones` y `/legal/privacidad` como bloques `rich_text` (páginas legales publicadas), con fallback a rutas estáticas `app/legal/[slug]/page.tsx` que leen del seed.

### 1.3 Páginas
| Archivo | Cambio |
|---|---|
| `app/page.tsx` | Render desde bloques: `const page = await getPage('home')` → `<BlockRenderer blocks={page.layout.blocks}/>`. Fallback a home hardcodeada solo mientras F3 completa el seed (feature flag `page.render = 'blocks' \| 'legacy'` removido al final de F3-08). |
| `app/collection/page.tsx` | Igual: bloque `collection_grid`; filtros por categoría siguen vía query param. |
| `app/products/[slug]/page.tsx` | Bloques + botón **Añadir al carrito** real (form server action → `addToCart` → redirect a `/carrito`). Estructura de datos sin cambios (usa `getProduct`). |
| `app/cart/page.tsx` (nuevo) | Server component: lee carrito, lista items, envío por zona (calculado server-side), total en centavos/COP, CTA **Ir a pagar** → `POST /v1/storefront/checkout` → redirect 302 a Wompi. |
| `app/checkout/*` (nuevo mínimo) | `checkout/exito` (estado por `reference` vía API), `checkout/fallo`, `checkout/pendiente` — páginas post-redirect Wompi; sin scripts de terceros; CSP estricta. |
| `app/legal/devoluciones/page.tsx` + `privacidad/page.tsx` (nuevos) | Renderizan páginas legales seedeadas (bloque rich_text). Enlazadas en footer y PDP. |
| `app/sitemap.ts`, `app/robots.ts`, `app/manifest.ts` (nuevos) | Sitemap por tenant (home, colección, productos activos, legales), `robots` con allow/disallow `/checkout|/cart`, manifest básico con nombre del tenant. JSON-LD `Product` en PDP. |
| `app/error.tsx` | Mantener boundary; `console.error` solo con `NODE_ENV!=='production'`; mensaje genérico en prod. |
| `app/not-found.tsx` (nuevo) | 404 amigable con link a colección. |

### 1.4 Componentes nuevos (`components/blocks/`)
`header.tsx`, `footer.tsx`, `hero.tsx`, `editorial-split.tsx`, `product-grid.tsx`, `product-carousel.tsx` (carrusel con scroll-snap CSS, sin libs), `collection-grid.tsx`, `image-banner.tsx`, `rich-text.tsx` (recibe HTML saneado **del servidor**; el componente solo hace `dangerouslySetInnerHTML` sobre contenido ya saneado por la API — única excepción documentada, protegida por `block-review`), `quote.tsx`, `gallery.tsx`, `video-embed.tsx` (iframe `youtube.com|player.vimeo.com`, `loading="lazy"`, `sandbox` sin allow-top-navigation), `faq.tsx` (acordeón con `<details>`, cero JS), `newsletter.tsx` (form server action → tabla `newsletter_subscribers`, sin terceros), `spacer.tsx`, `columns.tsx`. Más `block-renderer.tsx` (switch por `type`, default `null` + log `block_unknown`) y `components/cart-button.tsx`.

### 1.5 Configuración
- `next.config.ts`: ISR habilitado (sin `dynamic = 'force-dynamic'` global); `images.remotePatterns` añadir `https://cdn.growup.com`, `https://*.r2.dev`, sandbox `cdn.staging.growup.com`; headers HSTS solo en prod; `X-Robots-Tag: noindex` si host preview.
- `app/globals.css`: tokens desde variables inyectadas (`--brand`, `--font-*`), mantener sistema actual `data-theme` como capa fallback; `prefers-reduced-motion` ya está.
- **Borrar** copy hardcodeado Bogotá/[DROP 01] al migrar home a bloques; tenant pasa a mandar (settings: tagline, announcement bar).
- `package.json` storefront: scripts `test`, `test:e2e` (playwright), `test:e2e:ui`; deps dev: `@playwright/test`, `@axe-core/playwright`, `lighthouse` (CI), **sin** librerías de UI.

### 1.6 Variables de entorno (`.env.example` storefront)
```
GROWUP_API_URL=http://localhost:8000        # coherente con admin (hoy inconsistente 8000 vs 127.0.0.1)
GROWUP_STOREFRONT_HOST=ropa.growup.com      # override local
NEXT_PUBLIC_MEDIA_BASE_URL=http://localhost:9000/growup-catalog-local   # MinIO local
# PROHIBIDO NEXT_PUBLIC_TENANT_ID
```

---

## 2. `apps/admin` — cambios detallados

### 2.1 Navegación y rutas nuevas
`Resumen · Builder · Pedidos · Catálogo · Media · Auditoría · Billing · Plataforma · Ajustes` (antes: sin builder/pedidos/billing).

| Ruta | Contenido |
|---|---|
| `builder/` | Lista páginas (estado, versión publicada, "hay cambios sin publicar"); editor `/builder/[pageId]` — árbol de bloques dnd (HTML5 o `@dnd-kit/core` — permitido: no es UI kit), panel de props por tipo (forms derivados de contracts), autosave debounce 2s, `If-Match: version` con 409 UI, preview iframe con token firmado, botones Guardar/Publicar/Descartar. |
| `pedidos/` | Lista (filtros estado/fecha/búsqueda), detalle (`/pedidos/[id]`): items con snapshot, dirección envío, estado fulfillment con transición controlada (`paid→preparing→shipped→delivered`), acciones: marcar enviado (tracking opcional), cancelar+reembolso (confirmación doble, alerta irreversible si refund manual en Wompi), historial de eventos, botones "Reenviar confirmación"/"Ver factura". |
| `billing/` | Estado de suscripción (Starter/Pro, trial N días restantes, próximo cobro), botón portal Stripe (`billing:manage`), banner `past_due` con dunning + contacto soporte; si `legal_status='pending_legal'` → banner DPA bloqueante con enlace a aceptación. |
| `ajustes/` | Perfil tenant: nombre/legal_name (editable), plan (solo lectura), zonas de envío planas (2 zonas, tarifas editables), datos fiscales DIAN (NIT, resolución, prefijo — alimenta Factus), política de devolución acotada (plazo/exclusiones/categorías retornables), DNS de email (estado verificación dominio Resend + "Verificar ahora"), robots de soporte (accesos activos/histórico). |
| `legal/aceptar/page.tsx` (nueva, gate) | Pantalla full-width sin sidebar: DPA renderizado, checkbox "Acepto como responsable del tratamiento", botón "Aceptar y activar"; si hay versión nueva pendiente se bloquea toda la app tras login (redirect desde `requireSession()` cuando `legal_status='pending_legal'`). |
| `soporte/accesos/` | Historial de accesos de soporte (quién, cuándo, motivo, expiración) — lectura auditada. |

### 2.2 Fixes de código admin
- `lib/auth.ts`: eliminar doble `getUser()`/`getSession()` redundante (una sola llamada); si `legal_status='pending_legal'` → redirect `/legal/aceptar`.
- `lib/api.ts`: errores desde envelope nuevo (`AppError.code/message/details`), sin `?error=` por query donde se pueda usar estado server-side; mantener patrón PRG pero centralizar helper `actionError(searchParams)`.
- **Reemplazar `ConfirmSubmit`** (`window.confirm`) por componente `confirm-dialog.tsx` propio (modal accesible, focus-trap simple, botón destructivo rojo, Escape/overlay para cancelar).
- `components/offset-pagination.tsx`: usar `<Link>` (client navigation) en vez de `<a>`; unificar con patrón manual de `media/page.tsx` (eliminar duplicado).
- Toda respuesta admin: `cache: 'no-store'` + header `Cache-Control: no-store` (API lo pone tras F2-10).
- `status-badge.tsx`: extender variantes para `past_due`, `suspended`, `shipped`, `delivered`, `refund_pending` (mantener mapa único).
- Tipos desde `@growup/contracts` (`Order`, `OrderDetail`, `PageSummary`, `LegalDocument`…) tras regenerar contratos.

### 2.3 Variables de entorno (`.env.example` admin)
```
GROWUP_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
NEXT_PUBLIC_STOREFRONT_URL=https://ropa.growup.com   # evitar hardcode; default seguro
NEXT_PUBLIC_STRIPE_PORTAL_RETURN_URL=http://localhost:3001/billing
```

---

## 3. Packages

### 3.1 `packages/contracts`
`pnpm contracts:export && pnpm contracts:generate && pnpm contracts:check` tras cada cambio de API (F3/F4). Nuevos tipos: `PageSummary`, `PageVersion`, `Block*` (discriminated union), `Order*`, `Cart*`, `LegalDocument`, `BillingStatus`, errores envelope unificado. CI ya bloquea drift (✅ se mantiene).

### 3.2 `packages/config` (nuevo, `@growup/config`)
`formatPrice(cents, currency='COP')`, `formatDate`, `formatBytes`, `COP` constante, `DEFAULT_ZONES`, `supportEmail`. Eliminar duplicados en storefront/admin (`lib/format.ts`). `package.json` + `tsconfig`; apps lo importan vía `transpilePackages`.

### 3.3 Zombies (F0-04)
Borrar `apps/frontend/`, `packages/brand/` (sin package.json, no en lockfile). `frontend/` raíz → `git mv docs/prototypes/legacy-html/` (conservar referencia visual v1) con `README` explicativo; `README.md` raíz deja de afirmar "Spec en `.kiro`"; `reparto-trabajo.md` se sincroniza con este plan (tareas A-02..B-07 mapeadas a F-IDs, B-03 = F1-F/B-03 checklist).

---

## 4. Docker e infra — sincronización

### 4.1 `services/api/Dockerfile` y `.dockerignore`
Según G-F1-A del archivo de guías (multi-stage uv, no-root, healthcheck). Worker: `fly.worker.toml`-ready, CMD `arq app.workers.media.WorkerSettings`, sin EXPOSE. `.dockerignore` completo.

### 4.2 `infra/docker-compose.yml` (local dev completo)
Reescribir (manteniendo Redis+MinIO, añAdiendo el resto, **solo local**):
```yaml
name: growup-local
services:
  redis:
    image: redis:7.2-alpine            # pineado, no :latest
    ports: ["6379:6379"]
    healthcheck: ["CMD","redis-cli","ping"]
    restart: unless-stopped
    volumes: [redis-data:/data]
  minio:
    image: minio/minio:RELEASE.2025-09-07T16-13-09Z   # pin por fecha
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:?set in .env}   # sin password hardcodeada
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:?}
    ports: ["9000:9000"]               # consola 9001 NO expuesta por defecto? mantener "9001:9001" pero documentar
    healthcheck: ["CMD","mc","ready","local"]           # o curl documentado
    volumes: [minio-data:/data]
  mc-init:
    image: minio/mc:latest
    depends_on: [minio]
    entrypoint: > "/bin/sh -c 'mc alias set local http://minio:9000 $$MINIO_ROOT_USER $$MINIO_ROOT_PASSWORD; mc mb -p local/growup-catalog-local || true; mc anonymous set download local/growup-catalog-local/public || true'"
    environment: { MINIO_ROOT_USER: ${MINIO_ROOT_USER}, MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD} }
  api:
    build: ../services/api
    profiles: ["app"]                  # opcional: por defecto se corre con uv en host
    env_file: [../services/api/.env]
    environment: { GROWUP_REDIS_URL: "redis://redis:6379/0", GROWUP_R2_ENDPOINT: "http://minio:9000" }
    ports: ["8000:8000"]
    depends_on: { redis: { condition: service_healthy } }
  worker:
    build: ../services/api
    command: ["uv","run","arq","app.workers.media.WorkerSettings"]
    profiles: ["app"]
    env_file: [../services/api/.env]
volumes: { redis-data: {}, minio-data: {} }
```
- `infra/.env.example` con `MINIO_ROOT_USER/PASSWORD` **reemplazar `growup123`**; nunca reutilizar en prod; el README local documenta `docker compose -f infra/docker-compose.yml up -d` y que `-p` no existe para esto.
- El compose **no representa producción**; prod = Fly/Vercel/Supabase/Upstash (ADR-0008/0012). Nota grande en el archivo.

### 4.3 `fly.toml` / `fly.production.toml` (raíz o `infra/fly/`)
Ver G-F1-E: `app=growup-api-staging|production`, `primary_region='gru'`, VM shared-cpu-1x 256MB→512MB según métricas, `http_service` con `force_https`, `internal_port=8000`, `checks` `/healthz`+`/readyz`, `auto_stop_machines='stop'` solo staging, `min_machines_running=2` prod, secrets vía `fly secrets`. Worker: sin `http_service`, `internal_port` none, `[processes]` separados si una sola imagen (web=uvicorn, worker=arq) — decisión: **dos apps Fly** (simple, deploy independiente).

### 4.4 `.dockerignore` global y raíz
Añadir `.dockerignore` en raíz (git, node_modules, .next, docs grandes, `.env*`) — Docker contexts pequeños y sin secretos.

### 4.5 CI (`.github/workflows/ci.yml`)
Jobs nuevos/ajustados (detalle en G-F1-F): `docker` (build API/worker + Trivy), `e2e` (Playwright vs staging, solo `main` + `workflow_dispatch`), `deploy-staging` (automático en main con `environment: staging`), `deploy-production` (`environment: production` con reviewers), `audit` job con `pip-audit` + `pnpm audit --prod` + `gitleaks`. Branch protection en main; CODEOWNERS; PR template (G plantillas).

### 4.6 Variables en repo
`apps/*/.env.example` completos y coherentes; `services/api/.env.example` añadir `GROWUP_ENV=local|staging|production`, `GROWUP_PREVIEW_SECRET`, `GROWUP_BILLING_PROVIDER`, `GROWUP_STRIPE_*`, `GROWUP_FACTUS_*` (placeholders) — sin valores reales.

---

## 5. Orden de aplicación al salir del modo plan (resumen ejecutable)

1. F0-04/F0-05/F0-06 limpieza + `packages/config` + zombies (sin tocar lógica) — verificar `pnpm install && pnpm build` verde.
2. G-F1-A…E Dockerfiles + compose + fly + Vercel/Cloudflare/Supabase staging — staging vivo con catálogo actual.
3. F2 hardening (backend) y regeneración `contracts` en cada paso.
4. F3 builder: contratos → blocks API → storefront renderer → admin builder → ISR/purga → seed páginas; F3-05 enciende `page.render='blocks'`; borrar ruta legacy.
5. F4 cart/checkout/pedidos/billing/DIAN/email con storefront (`/carrito`, post-pago) y admin (`pedidos`, `billing`, `ajustes`) en el mismo milestone.
6. F5 legal: `/legal/*`, gate `pending_legal`, FAQ; los textos placeholder del repo hasta que llegue el abogado — marcar con banner "texto en revisión legal" en staging, **prohibido en prod**.
7. F6 seed + Playwright + go-live checklist (§ guía go-live).

## 6. Criterio de "sincronizado" (verificación)

- `pnpm install --frozen-lockfile`, `pnpm lint`, `pnpm typecheck`, `pnpm build` verde en todo el monorepo.
- Storefront staging renderiza home **desde bloques publicados** con ISR + purge < 10 s; tema del tenant aplicado; error de bootstrap → página de configuración.
- Flujo compra sandbox completo en `ropa.growup.com` (staging): carrito → redirect Wompi → webhook → orden paid → email → factura Factus sandbox → pedido visible en `admin/pedidos`.
- `admin/billing` muestra suscripción trial; `pending_legal` bloquea publish y checkout y muestra DPA; aceptación → desbloqueo.
- Docker: `docker build` API/worker sin root; compose local levanta minio+redis+api+worker con `.env` propio; Trivy sin CRÍTICOS; staging en Fly/Vercel/Supabase con WAF Cloudflare y rate limiting verificado.
- Sin referencias rotas: `grep -r "polvora\|growup123\|\.kiro\|force-dynamic\|apps/frontend"` en código activo → 0 resultados.
