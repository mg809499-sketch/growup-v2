# Guías paso a paso — pendientes de Growup

> Fecha: 2026-11-10 · Complemento de `plan-maestro-growup.md` y `decisiones-proveedores-growup.md` · Cada guía indica objetivo, pasos, comandos y criterio de listo (DoD). Los datos de proveedores (cuentas, URLs, tokens) nunca se commitean; van a `.env` local, GitHub Environments o `fly secrets`/Vercel env.

**Índice**
1. [G-F0 Ratificación de decisiones (sesión F0-01)](#g-f0)
2. [G-F1-A Dockerfile y .dockerignore de API y worker](#g-f1-a)
3. [G-F1-B Proyecto Supabase prod en sa-east-1](#g-f1-b)
4. [G-F1-C Vercel: storefront y admin con wildcard](#g-f1-c)
5. [G-F1-D Cloudflare DNS + WAF + rate limiting](#g-f1-d)
6. [G-F1-E Fly.io: apps staging/prod + secrets](#g-f1-e)
7. [G-F1-F CI/CD completo (pip-audit, pnpm audit, Trivy, secret scanning, deploy)](#g-f1-f)
8. [G-F1-G Observabilidad: Sentry + OTel + Grafana Cloud + alertas](#g-f1-g)
9. [G-F2 Hardening: chequeos rápidos y fixes de DB/JWKS/rate-limit](#g-f2)
10. [G-F3 Builder y contenido (ADR-0005)](#g-f3)
11. [G-F4-A Wompi: cuenta sandbox y spike (B-06)](#g-f4-a)
12. [G-F4-B Checkout redirect + webhook + orden](#g-f4-b)
13. [G-F4-C DIAN con Factus (factura y nota crédito)](#g-f4-c)
14. [G-F4-D Stripe Billing + suspensión por impago](#g-f4-d)
15. [G-F4-E Resend + dominios por tenant + ARQ](#g-f4-e)
16. [G-F5-A DPA/clickwrap: legal_documents y legal_acceptances](#g-f5-a)
17. [G-F5-B Runbook DSR (documento ejecutable)](#g-f5-b)
18. [G-F5-C Protocolo de brecha y game day](#g-f5-c)
19. [G-F5-D Soporte, FAQ y acceso temporal auditado](#g-f5-d)
20. [G-F6 Seed demo (B-01) y Playwright E2E (B-02)](#g-f6)
21. [B-03 CI y seguridad (checklist)](#b-03)
22. [Guía de go-live (checklist 72h)](#go-live)
23. [Plantilla de PR y plantillas de auditoría (`tenant-isolation-check` / `block-review` / `payment-webhook-review`)](#plantillas)

---
<a id="g-f0"></a>
## G-F0 — Sesión de ratificación de decisiones (F0-01)

**Duración:** 2–3 h · **Asisten:** equipo (2) + abogado (1h final) + contador (30 min específicos).

**Agenda:**
1. Lectura del resumen ejecutivo de `decisiones-proveedores-growup.md` (15 min).
2. Contador: confirmar D-06 (IVA envío incluido o no, redondeo, productos joyería gravados) y D-01/D-02 (IVA de la suscripción, retenciones a Stripe/MP, régimen de la entidad Growup para cobrar suscripción; si la entidad puede operar Stripe).
3. Abogado: aprobar regla de D-11/SAQ A (redirect), DPA (D-09), matriz DSR (D-10), protocolo brecha (D-12), plantilla devoluciones (D-13), cláusula no-facilitador en ToS (D-17), anexos de sub-encargados y transferencias internacionales (US).
4. Equipo: precios de plan y límites (D-01 der.), fecha piloto 2027-02-15 y responsable contenido, elección Resend/Factus/Cloudflare como propuestas de eficiencia (se ratifican aquí).
5. **Registro:** editar `docs/decisiones-pendientes.md` in situ: cada decisión → CERRADA con fecha, responsable y referencia a este plan. Sin acta, no hay cambios.
6. Si algo queda sin acuerdo: se marca `DIFERIDA al <fecha>` con bloqueador explícito; ninguna tarea dependiente inicia.

**Entregable:** `docs/legal/acta-cierre-decisiones-2026-11.md` con acuerdos literales + este checklist firmado.

---
<a id="g-f1-a"></a>
## G-F1-A — Dockerfile de API y worker

**API (`services/api/Dockerfile`):**
```dockerfile
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_SYSTEM_PYTHON=1
WORKDIR /app
# Usuario no root
RUN groupadd -r app && useradd -r -g app app
# uv desde imagen oficial
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/
# Capa de dependencias (cacheable)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
# Código
COPY app ./app
RUN uv sync --frozen --no-dev && chown -R app:app /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=4)"
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```
Worker: mismo patrón, `CMD ["uv", "run", "arq", "app.workers.media.WorkerSettings"]`, **sin** `EXPOSE` ni ingress en Fly. `.dockerignore`: `.venv`, `__pycache__`, `.pytest_cache`, `.env`, `tests`, `.mypy_cache`, `.ruff_cache`, `*.md`.

**DoD:** `docker build` < 5 min; Trivy sin CRITICAL/HIGH; `docker run` local contra compose; `USER` ≠ root; tamaño < 200 MB (python slim + uv suele quedar ~180 MB).

---
<a id="g-f1-b"></a>
## G-F1-B — Supabase prod/staging en sa-east-1

1. Crear organización/proyectos: `growup-staging`, `growup-prod` (sa-east-1). Diferenciar claves desde el día 1.
2. Settings → Database: copiar **Connection string (Transaction, puerto 6543)** → `GROWUP_DATABASE_URL` (API) y **Direct** → `GROWUP_MIGRATION_URL` (CI/migraciones). **Nunca pwd del pooler superuser para la API.**
3. Crear roles y grants (una vez, SQL Editor):
```sql
create role app_rw nologin nobypassrls;
create role app_worker nologin nobypassrls;
create role app_api_login login nosuperuser nobypassrls password '<vault>';
create role app_worker_login login nosuperuser nobypassrls password '<vault>';
grant app_rw to app_api_login;
grant app_worker to app_worker_login;
grant usage on schema app to app_rw, app_worker;
```
4. `ALTER ROLE` statement_timeout/lock_timeout para app_api_login (p.ej. `statement_timeout='15s'`, `lock_timeout='5s'`).
5. PITR activado (7 días) + dump diario `pg_dump` a R2 vía job (GitHub Action diario, credencial R2 write-only). Probar restauración en proyecto `growup-restore-test` y documentar tiempo en `docs/operations/restore-test.md`.
6. JWT: **pasar a signing keys asimétricas ES256** (Auth → JWKS). Requisito del verificador. Desactivar HS256 como único método. `site_url=https://admin.growup.com`, signup off salvo onboarding vía platform admin, MFA (TOTP) obligatorio para owner/admins en prod.
7. Aplicar migraciones con direct connection en orden; `pnpm dlx supabase test db` contra staging.
8. Config `schemas = ["public"]` en API settings; el schema `app` no se expone; `service_role` jamás en la API.

**DoD:** conexión con `app_api_login` vía pooler OK; insert cruzado A→B falla con 42501; restore probado; JWKS verificado por el API; Auth con ES256.

---
<a id="g-f1-c"></a>
## G-F1-C — Vercel: dos proyectos + wildcard

1. Importar repo en Vercel dos veces: `growup-storefront` (root `apps/storefront`) y `growup-admin` (root `apps/admin`). Framework Next; **Node 22**; install `pnpm install --frozen-lockfile`; build `pnpm build` filtrado por app; output default.
2. Dominios: storefront — `growup.com`, `www.growup.com` (redirect), `*.growup.com` (**wildcard requiere Vercel Pro o plan con wildcard TLS** — verificar; si no cubre, usar un dominio por tenant seedeado o Cloudflare for SaaS fase 3; fallback: `{slug}.growup.com` vía CNAME wildcard + certificado wildcard manual cargado en Vercel — Vercel soporta upload de certs wildcard managed). Admin — `admin.growup.com`.
3. Env vars por ambiente (Production/Preview/Development): `GROWUP_API_URL=https://api.growup.com` (prod) / `https://api.staging.growup.com`; `NEXT_PUBLIC_MEDIA_BASE_URL=https://cdn.growup.com`; `GROWUP_STOREFRONT_HOST` NO se setea en prod (host real manda); admin: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_STOREFRONT_URL=https://{slug}.growup.com` no fijo — se pasa por tenant.
4. Preview deployments con **password protection** (Vercel Authentication) y sin indexar (`X-Robots-Tag: noindex`); staging real = `staging.growup.com` (proyecto de staging separado o `staging` branch en ambos proyectos).
5. Headers en `next.config.ts`: HSTS (`max-age=63072000; includeSubDomains; preload`) en prod, `X-Robots-Tag` por host admin, `Cache-Control` adecuados estáticos.

**DoD:** `https://ropa.growup.com` sirve staging con candado; `admin.growup.com` protegido y noindex; Lighthouse en preview sin errores de TLS.

---
<a id="g-f1-d"></a>
## G-F1-D — Cloudflare DNS + WAF + rate limiting

1. Crear zona `growup.com` (plan Free) y apuntar NS del registrador a Cloudflare.
2. Registros: `A/CNAME @ → vercel-dns` (proxied DNS-only→ editar según indicaciones Vercel), `* → CNAME cname.vercel-dns.com` (proxied naranja según compatibilidad Vercel/Cloudflare — Vercel soporta proxy naranja con Full strict), `admin → CNAME`, `api → CNAME <fly-app>.fly.dev` (proxied), `mail.* → CNAME <resend>` (DNS only gris), `_dmarc` TXT, MX para `soporte@` (Google Workspace).
3. SSL/TLS: **Full (strict)**; siempre HTTPS; TLS 1.2+.
4. WAF/rate limiting (Security → WAF): reglas —
   - `/v1/storefront/*` > 300 req/min/IP → block 1 min;
   - `/v1/admin/*` > 120 req/min/IP → block 1 min;
   - `/v1/platform/*` > 30 req/min/IP → managed challenge;
   - `/v1/admin/login`, magic-link endpoints: 10 req/min → block;
   - Bot Fight Mode ON (free); regla custom: bloquear países fuera de CO/MX/US/ES/CL/AR si el negocio lo permite (opcional; documentar).
5. Caching: bypass para `api.*` (API dinámica); cachear assets storefront `*.growup.com/_next/static/*` edge TTL 1y; **nunca** cachear `/api/*` ni respuestas admin.
6. Notificaciones: email+webhook (staging) y WhatsApp/PagerDuty para WAF blocks anómalos.

**DoD:** `curl -I https://api.growup.com/healthz` muestra headers Cloudflare; regla de rate limit dispara en prueba (script con 350 requests); origen Fly no accesible directamente (firewall restrict) — o al menos no documentado/aconsejado.

---
<a id="g-f1-e"></a>
## G-F1-E — Fly.io: apps y secrets

```bash
fly launch --name growup-api-staging --region gru --no-deploy   # o fly.toml en repo
fly secrets set -a growup-api-staging \
  GROWUP_DATABASE_URL='postgresql://app_api_login:XXX@...pooler.supabase.com:6543/postgres' \
  GROWUP_WORKER_DATABASE_URL='postgresql://app_worker_login:XXX@...:6543/postgres' \
  GROWUP_MIGRATION_URL='postgresql://postgres:XXX@...:5432/postgres' \
  GROWUP_REDIS_URL='rediss://default:XXX@upstash sa-east-1' \
  GROWUP_R2_ENDPOINT=... GROWUP_R2_ACCESS_KEY_ID=... GROWUP_R2_SECRET_ACCESS_KEY=... \
  GROWUP_R2_BUCKET=growup-media-staging GROWUP_MEDIA_PUBLIC_BASE_URL=https://cdn-staging.growup.com \
  GROWUP_SUPABASE_URL=https://xxxx.supabase.co GROWUP_SUPABASE_JWT_AUDIENCE=authenticated \
  GROWUP_SENTRY_DSN=... GROWUP_ENV=staging GROWUP_ROOT_DOMAIN=growup.com \
  GROWUP_CORS_ORIGINS='https://staging.growup.com,https://admin-staging.growup.com'
fly deploy -a growup-api-staging
fly apps create growup-api-production
```
Worker: app `growup-worker-staging`, misma imagen, override CMD; sin `services` (sin ingress); `[http_service]` ausente; secrets idénticos salvo `GROWUP_ENV=production`.
**Conexión directa al pooler de Supabase desde Fly está soportada (transaction mode)**; si hay problemas raros, usar session mode con `max_overflow` bajo y documentar.

**DoD:** `fly status` 2 máquinas prod; `readyz` 200; worker procesa job de prueba (`process_media` con asset dummy); certificado Let's Encrypt de `api.growup.com` emitido (o Origin CA si proxy naranja full strict).

---
<a id="g-f1-f"></a>
## G-F1-F — CI/CD completo

Añadir a `.github/workflows/ci.yml`:
```yaml
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd services/api && pip install pip-audit && uv run pip-audit --strict
      - run: pnpm install --frozen-lockfile && pnpm audit --prod --audit-level high
      - uses: aquasecurity/trivy-action@0.28.0
        with: { image-ref: 'ghcr.io/${{ github.repository }}/api:ci', severity: 'CRITICAL,HIGH', exit-code: '1' }
      - uses: gitleaks/gitleaks-action@v2   # secret scanning
  deploy-staging:
    needs: [api, db, contracts, frontend, security]
    if: github.ref == 'refs/heads/main'
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - run: echo "Vercel auto-deploy via Git integration"
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --remote-only -a growup-api-staging
        env: { FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN_STAGING }} }
  deploy-production:
    needs: [deploy-staging]
    if: github.ref == 'refs/heads/main'
    environment: production   # required reviewers
    ...
```
Más: branch protection en `main` (Settings → Branches): require PR + 5 checks + linear history + no force push; CODEOWNERS `* @personaA @personaB`; PR template con sección "Evidencia / migraciones expand-contract / secretos verificados".

**DoD:** secret ficticio en PR de prueba es detectado; deploy-staging actualiza `staging.growup.com` solo; deploy-production exige reviewer; audit findings triados y documentados.

---
<a id="g-f1-g"></a>
## G-F1-G — Sentry + OpenTelemetry + Grafana Cloud

**Sentry:** crear proyectos `growup-storefront`, `growup-admin`, `growup-api`, `growup-worker`; DSNs en env por ambiente; en FastAPI `sentry_sdk.init(dsn, environment, traces_sample_rate=0.1, send_default_pii=False)`; en Next `@sentry/nextjs` con `replaysSessionSampleRate: 0` (PII).
**OTel:** `pip install opentelemetry-distro opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-asyncpg opentelemetry-exporter-otlp`; `opentelemetry-bootstrap -a install`; `opentelemetry-instrument` o `instrument()` en `main.py`; atributo común `service.name=growup-api`, `deployment.environment`; propagación `traceparent` storefront→API (fetch con header) y API→worker (ARQ job kwargs).
**Grafana Cloud Free:** stack grafanacloud; recibir OTLP; dashboards: (1) API RED (rate/errors/duration p50/p95 por ruta), (2) DB pool y conexiones Supabase, (3) ARQ cola/jobs/failures, (4) frontend Web Vitals (RUM opcional), (5) negocio (órdenes/día, conversión) en fase 4.
**Alertas:** 5xx>2% (5 min), p95>1.5s 10 min, readyz fail, `decision_logs` tamper (job diario F2-13) → webhook/email on-call.

**DoD:** un request navegador→storefront→API aparece como traza única con `tenant_id`; alerta de prueba llega al canal; logs sin PII (revisión manual de 100 líneas sample).

---
<a id="g-f2"></a>
## G-F2 — Hardening backend/DB (quick wins y fixes)

**Verificación rápida de estado (correr y anotar resultados):**
```bash
cd services/api
uv run ruff check . && uv run mypy app && uv run pytest      # baseline
grep -rn "resolve_tenant" --include=*.sql ../../supabase | head
grep -rn "status" app/domains/tenants/service.py | head
```
**F2-01 suspensión (SQL):**
```sql
-- nueva versión filtra status; mantener índice domains(host)
create or replace function app.resolve_tenant(p_host text)
returns table(id uuid, slug text, name text, status text)
language sql security definer set search_path = pg_catalog, app as $$
  select t.id, t.slug, t.name, t.status
  from app.domains d join app.tenants t on t.id = d.tenant_id
  where d.host = lower(p_host) and t.status in ('active','trialing')
$$;
```
+ invalidación Redis: clave `tenant:{slug}:status` versionada; `TenantResolver` compara versión (GET con TTL 60s) — o pub/sub `tenant:suspend` que borra caches. Test: suspender → siguiente storefront request 404 en ≤2s (con 2 workers).
**F2-03 (grants por columna):**
```sql
revoke update on app.tenants from app_rw;
grant update (name, legal_name, updated_at) on app.tenants to app_rw;
-- plan_id/status/trial_ends_at solo vía funciones SECURITY DEFINER (create_tenant_with_owner, platform billing jobs)
```
**F2-04 JWKS singleflight:** en `JWKSCache`, `asyncio.Lock` por kid + `self._refresh_task` compartido; negative cache dict `kid→expiry(now+60)`; cooldown global `self._last_refresh` (300s). Tests con mock de `httpx`: 50 tasks concurrentes con kid nuevo → 1 llamada.
**F2-05 rate limit:** tabla Redis `rl:{scope}:{key}` INCR+EXPIRE; middleware antes de routing de rutas públicas; 429 envelope `{"error":{"code":"RATE_LIMITED",...,"details":{"retry_after":int}}}` + header `Retry-After`.
**F2-06:** header `X-Request-ID` regex `^[A-Za-z0-9-]{1,64}$` else reemplazar por uuid4; `Transfer-Encoding: chunked` sin content-length en prod → 411.
**F2-08:** media/identity routers: cambiar `get_admin_context`+chequeo manual por `get_tenant_context` directo (guardar casos sin tenant como plataforma); `request.state.tenant_id` siempre seteado para logging.
**F2-14:** índices nuevos + unique; pgTAP de balance `decision_logs` intacto.

**DoD por fix:** test que falla antes y pasa después; pgTAP/integración verde; sin regresiones en `pytest` completo.

---
<a id="g-f3"></a>
## G-F3 — Builder y contenido (ADR-0005) — orden de implementación

1. **Esquema**: `00000000000010_content.sql` — `pages(id, tenant_id, slug, title, status, published_version_id nullable, created_at, updated_at, unique(tenant_id,slug))`, `page_versions(id, tenant_id, page_id, version int, layout jsonb not null, created_by, created_at, unique(tenant_id, page_id, version))`, `themes(tenant_id pk, tokens jsonb, updated_at)`, `outbox_events(id, tenant_id, type, payload jsonb, created_at, processed_at)`. RLS + grants columna-only donde aplique (F2-03 patrón). Ver `pgTAP` patrón existente.
2. **Bloques Pydantic** (`app/domains/content/blocks.py`): `Annotated[BlockUnion, Field(discriminator='type')]`; 16 clases; `extra='forbid'`; validadores: `alt` requerido en image; `items` máx (columns ≤4, faq ≤12, gallery ≤12, product_grid ≤24 items); `rich_text.markdown` ≤ 10.000 chars, strip tags con `bleach` whitelist md→html mínimo; `video_embed.url` regex `^https://(www\.)?(youtube\.com|youtu\.be|player\.vimeo\.com)/`.
3. **API** (`/v1/storefront/pages/{slug}` pública cacheada por tag; admin CRUD+publish con outbox; preview token). Envelope de errores estándar. `contracts:check` obligatorio en PR.
4. **Storefront**: `BlockRenderer` server-side; ISR `export const revalidate = 3600` + `unstable_cache` con tag `page:{tenant}:{slug}`; publish → webhook → `revalidateTag`. Componentes en `components/blocks/` con props tipadas desde contracts. Fallback: bloque desconocido → `null` + log estructurado `block_unknown`.
5. **Admin**: `/(dashboard)/builder`; lista de páginas → editor; panel izquierdo árbol de bloques (dnd), panel derecho props (formularios por tipo, textarea para rich_text con contador, pickers de media conectados a `/v1/admin/media`), barra superior: Guardar (autosave 2s) / Vista previa (iframe con token) / Publicar (modal confirm + `If-Match: version`). Conflictos → banner "Alguien más editó esta página. Recarga para ver cambios."
   *(Implementado 2026-11-13 en `feat/builder-visual`: ver nota de estado en F3-07 del plan maestro. Los formularios de props se escriben a mano por tipo — no hay UI dinámica desde JSON-schema — y las imágenes usan `ImageInput` (URL pública o picker de media cuando `NEXT_PUBLIC_MEDIA_BASE_URL` está configurada).)*
6. **Seeder de páginas piloto** en seed.demo.sql (F6-01): home con hero+product_grid+editorial_split, colección con collection_grid, PDP fuera de bloques (ruta fija).
7. **Docs:** `docs/prompts/v0-storefront.md` se marca "implementado"; `block-review` skill sobre cada PR de bloque.

**DoD:** publicar un cambio en staging visible < 10s; rollback a versión anterior en 1 click; XSS payloads (`<script>`, `javascript:`, onerror) rechazados por schema y por renderer; Lighthouse móvil ≥ 80.

---
<a id="g-f4-a"></a>
## G-F4-A — Wompi: cuenta sandbox y spike (B-06)

1. Crear cuenta comercio en wompi.co (sandbox de prueba) con los datos de la entidad Growup (no del tenant; cada tenant conectará su cuenta propia — para el piloto los dos tenants = cuentas sandbox nuestras). Anotar `public_key` (test) y `events_secret` (test).
2. Documentación: https://docs.wompi.co — revisar "Checkout" (redirect), "Firma de integridad" (SHA256 de `reference+amount_in_cents+currency+integrity_key`), "Webhooks" (verificación por `events_secret` + `checksum`), estados `PENDING/APPROVED/DECLINED/VOIDED/ERROR`, 3DS.
3. **Spike checklist (entregar `docs/spikes/wompi.md`):**
   - Redirect vs widget: confirmar URL de checkout hosted (`https://checkout.wompi.co/p/` o web checkout actual) y parámetros requeridos; confirmar dominios exactos para CSP (`checkout.wompi.co`, `cdn.wompi.co` si widget).
   - Webhook firmado: ejemplo de payload; verificación HMAC; idempotencia; orden de llegada (APPROVED tras PENDING duplicado).
   - 3DS: comportamiento por franquicia; qué devuelve el webhook (`three_ds_auth_type` si aplica); PSE/Nequi sin 3DS.
   - Campos de riesgo expuestos (fraud score, bin, last_four, payment_method_type).
   - Tarifas vigentes (% + fijo COP) y tiempos de dispersión.
   - Expiración de transacción (revenue si no finaliza en N minutos).
4. Decidir y registrar: redirect hosted ratificado (ADR-0010 Aceptada); CSP final; D-11 y D-14 cerradas oficialmente.

**DoD:** `docs/spikes/wompi.md` con requests/responses reales (sanitizadas) + decisión; cuenta sandbox con al menos una transacción APPROVED de prueba.

---
<a id="g-f4-b"></a>
## G-F4-B — Checkout redirect + webhook + orden

1. Al confirmar checkout (`POST /v1/storefront/checkout`): transacción BD → crear `orders(status='pending')` + `payments(provider='wompi', status='pending')` con `reference='ord_{uuid}'`; descontar reserva de inventario (`reserve` 15 min); firmar `integrity`.
2. Redirigir 302 a Wompi con query params. Los dos tenants usan cuentas propias: leer credenciales desde `tenant_payment_accounts` (AES-GCM sobre `events_secret` con clave maestra en secret).
3. Webhook `POST /v1/webhooks/wompi` (público, sin auth, verificado por firma): verificar `X-Webhook-Signature`/checksum → buscar por `reference` → idempotencia en `webhook_events(provider,event_id)` → si duplicado, 200 silencioso → según status: `APPROVED` → `orders.status='paid'`, `confirm` reserva, encolar `emit_invoice`+`send_order_confirmation`; `DECLINED|VOIDED|ERROR` → `failed`, liberar reserva, email "pago no completado"; `PENDING` largado (> 30 min) → job de expiración.
4. Firma: nunca confiar en payload sin verificar; responder 200 rápido y procesar en ARQ (`process_wompi_webhook`) — Wompi reintenta si no hay 200.
5. Admin: vista órdenes; detalle; transiciones fulfillment; botón "Reenviar confirmación" (usa email existente).
6. Tests: fixtures de payload (APPROVED/DECLINED/duplicado/firma inválida); order de eventos; reserva confirmada/liberada exactamente-once.

**DoD:** compra E2E sandbox verde con Playwright; 100% de eventos de prueba procesados; 0 reservas huérfanas tras batería de pruebas.

---
<a id="g-f4-c"></a>
## G-F4-C — Factus (DIAN): factura y nota crédito

1. Cuenta Factus developer (sandbox): `client_id`, `client_secret`; OAuth2 token (cachear hasta expiración).
2. Adaptador `FactusClient` (retries 3×, timeout 30s, backoff 2/5/10s):
   - `create_invoice(order)`: payload cf/01 — emisor (datos DIAN del tenant: NIT, nombre, régimen, resolución de facturación, prefijo), receptor (cliente: tipo doc CC/NIT/CE, número, nombre, dirección, email), ítems (descripción, cantidad, precio unitario IVA incluido, tasa IVA 19%, subtotal), totales (subtotal, tax_total, total en centavos), forma de pago 1 (contado).
   - `create_credit_note(invoice, reason_code=3 (devolución parcial/total), items)`: nc/02 referenciando cf/01.
3. Tablas: `invoices(order_id, provider='factus', electronic_ref, cufe, pdf_url, status, issued_at, error)`, `invoice_events` (log sin PII: ids y estados).
4. Orden `paid` → ARQ `emit_invoice` → éxito: `invoices.status='emitted'`, email "factura disponible" con PDF link; fallo → reintento; 3 fallos → `approval_tasks(type='invoice_emission', payload)` + alerta a soporte (F5-07).
5. Refund (F4-05): si factura emitida → ARQ `emit_credit_note` automático con monto del refund (parcial permitido). Si no emitida aún → detener refund hasta resolver la factura (orden de consistencia fiscal).
6. Sandbox: emitir factura de prueba cf/01 y nc/02; guardar PDFs de evidencia en `docs/spikes/factus/` (sin datos reales).
7. Modo producción: credenciales prod en secrets; prefijos/resolución de facturación por tenant (onboarding captura NIT/resolución en admin → `tenant_fiscal_profiles`).

**DoD:** factura y nota crédito sandbox validadas; fallback manual probado; cero datos fiscales inventados — todo viene del perfil fiscal del tenant o queda en error explícito.

---
<a id="g-f4-d"></a>
## G-F4-D — Stripe Billing y suspensión por impago

1. Stripe (modo test a v1): productos `Starter`/`Pro` COP, precios mensuales y anuales según plan. `signing_secret` de webhook en secrets. Customer y Subscription gestionados desde el **platform admin** (alta manual asistida en MVP) o portal.
2. Onboarding del tenant facturado (plataforma→comerciante, flujo inverso al checkout): página admin `/billing` → "Activar prueba" crea `trialing` (14d) → Stripe Checkout (subscription mode) con datos del owner → webhook activa `active`.
3. Webhooks `POST /v1/webhooks/stripe` (verificado por `stripe.Webhook.construct_event`):
   - `invoice.paid` → `active`;
   - `invoice.payment_failed` → `past_due` + email dunning (D+0); ARQ programar recordatorios D+1/D+3/D+7;
   - `invoice.paid` desde `past_due` → `active` (limpiar cola);
   - `customer.subscription.deleted` o `past_due` + 8 días sin pago → `suspended` (+ invalidar caches, email owner "tienda suspendida");
   - `customer.subscription.updated` → límites de plan (`plans`-features gates en código: `require_entitlement('products', n)`).
4. Reactivación: pago → `active` + email + caches invalidadas.
5. Auditoría: cada transición en `decision_logs` (`policy_id='billing.suspend'`, payload redactado).
6. Test con Stripe CLI: `stripe listen --forward-to`; `stripe trigger invoice.payment_failed`; ciclo completo en staging.

**DoD:** ciclo completo ensayado; tienda suspendida no sirve storefront ni admin (F2-01); emails de dunning recibidos; sin duplicados de evento (idempotencia en `webhook_events`).

---
<a id="g-f4-e"></a>
## G-F4-E — Resend + dominio por tenant + ARQ

1. Resend: dominio `growup.com` verificado (DKIM, SPF con include Resend, DMARC p=quarantine rua=mailto:dmarc@growup.com).
2. Onboarding tenant: ARQ job `provision_tenant_email` → `resend.domains.create('mail.{slug}.growup.com')` → devolver registros DNS (CNAMEs) → (Cloudflare API: crear registros automáticamente si permiso, o mostrar al owner para pegarlos) → `resend.domains.verify()` polling hasta verified (timeout 24h, estado en `tenant_email_domains`).
3. Fallback: mientras `pending`/`failed`, envío por dominio compartido `mail.growup.com` con `Reply-To: pedidos@{slug}.growup.com`; banner admin "Verificando dominio…".
4. Worker `send_email(template, to, data, tenant_id, idempotency_key)`: render Jinja2/React-Email (HTML + text); llama Resend; escribe `email_events(provider_id, status)`; reintentos; rebotes vía webhook `/v1/webhooks/resend` → `email_suppressions(tenant_id, email)`.
5. Supabase Auth: SMTP = Resend (`smtp.resend.com:587`, user `resend`, pass API key), remitente `Growup <noresponder@auth.growup.com>`.
6. Plantillas (Jinja en `services/api/app/domains/notifications/templates/`): orden-confirmada, orden-enviada, factura-lista, dunning-1/3/7, bienvenida-owner, dsr-confirmado, suspensión. Variables escapadas; nunca PII en logs; idioma es-CO.

**DoD:** email desde `mail.joyeria.growup.com` con DKIM pass (verificado con mail-tester ≥ 9/10); rebote de prueba suprime la dirección; magic link llega; métricas en admin (enviados/fallidos/últimos 50).

---
<a id="g-f5-a"></a>
## G-F5-A — DPA/clickwrap: legal_documents + legal_acceptances

**Migración:**
```sql
create table app.legal_documents (
  id uuid primary key default gen_random_uuid(),
  type text not null check (type in ('dpa','tos','privacy','returns','subscription')),
  version text not null, title text not null, body_md text not null,
  sha256 text not null, published_at timestamptz not null default now(),
  unique (type, version)
);
create table app.legal_acceptances (
  tenant_id uuid not null references app.tenants(id),
  document_id uuid not null references app.legal_documents(id),
  actor_user_id uuid not null, accepted_at timestamptz not null default now(),
  method text not null default 'clickwrap', evidence jsonb,
  primary key (tenant_id, document_id)
);
alter table app.tenants add column legal_status text not null default 'active' check (legal_status in ('pending_legal','active'));
-- sin update/delete grants en legal_acceptances para app_rw; solo insert vía function app.accept_legal_document(...)
```
**Flujo owner:** primer login admin → `GET /v1/admin/legal/pending` → si versión no aceptada → pantalla bloqueante con DPA (scroll + checkbox + botón "Aceptar como responsable") → `POST /v1/admin/legal/accept` (transacción: insert acceptance + `legal_status='active'` si ya firmó todo + `decision_logs` `legal.document_accepted`) → redirect a resumen. Platform admin **no** ve el botón.

**Publish/billing gate:** middleware `require_legal_active` en rutas publish (admin) y checkout (storefront): `legal_status != 'active'` → 403 `LEGAL_NOT_ACCEPTED` (storefront: "Tienda en configuración").

**DoD:** pgTAP de inmutabilidad (update/delete rechazados); integración: tenant nuevo → publish 403 → owner acepta → publish 200; `verify_decision_chain` íntegro; abogado firma DPA y ToS finales.

---
<a id="g-f5-b"></a>
## G-F5-B — Runbook DSR ejecutable (`docs/operations/dsr-runbook.md`)

```markdown
# DSR runbook (Derechos del titular — Growup, CO Habeas Data / GDPR)
1. Recepción: webhook/email `dsr@growup.com` o solicitud en `soporte@growup.com` con asunto [DSR].
2. Registrar: `dsr_requests(id, tenant_id?, requester_email, type, status='received', received_at)` + asignar a `platform_dsr` (persona A).
3. Verificar identidad (≤ 2 días hábiles):
   - Email coincide con pedido/customer; pedir número de orden + últimos 4 del pago o correo de confirmación; para cuentas magic-link, reenviar enlace de verificación al correo.
   - Si datos de tenant: verificar rol (owner/manager) y ámbito (su tenant solamente).
4. Alcance: clasificar dato por categoría (pedido, factura, cuenta, marketing, logs).
5. Ejecutar según matriz de retención (decisiones-proveedores §D-10):
   - Anonimizar: nombre→'Titular', email→'anon-{sha256(email+salt)}@deleted.growup.com', phone/address→NULL, mantener ciudad/depto;
   - Conservar: facturas/órdenes (≥5 años) marcadas `anonymized_at`; decision_logs sin tocar;
   - Borrar: carritos, analytics sin agregar, auth_events expirados.
   - SQL de ejemplo (transacción con verificación previa y rollback): [snippet]
6. Verificación post-acción: queries de control; conteo antes/después; comparación con matriz.
7. Respuesta al titular (≤ 15 días hábiles): plantilla `docs/legal/dsr-response.md` — qué se hizo, qué se conserva y por qué (obligación fiscal), cómo apelar a la SIC.
8. Registrar evidencia: `dsr_requests.status='completed'`, `decision_logs` `dsr.executed` (payload sin PII: hashes/ids).
9. Si hay backups involucrados: nota estándar "los backups se renuevan en ≤ 7 días y la anonimización se reaplica al restaurar".
```
**DoD:** DSR simulado completo en staging ≤ 4 h de esfuerzo de operador; evidencia almacenada; `platform_dsr` es el único rol que puede ejecutar las escrituras (grants verificados por pgTAP).

---
<a id="g-f5-c"></a>
## G-F5-C — Protocolo de brecha y game day

**Runbook (`docs/operations/breach-runbook.md`):**
1. Detección (alertas G-F1-G) → quien detecta declara S1-S4 en canal `#incidentes` (WhatsApp/Telegram) + abre `decision_logs` `incident.declared`.
2. Contención: rotar credenciales afectadas (Supabase JWT keys si aplica, R2 keys, Wompi/Stripe secrets), revocar sesiones Auth (`admin.auth.admin.signOut(user_id)` por admin afectado), bloquear IP en WAF, congelar deploys.
3. Evaluación: qué datos, cuántos titulares, qué tenants, ¿exfiltración confirmada? (logs/WAF/Sentry/DB snapshots).
4. Notificaciones: tenant afectado ≤ 24h (plantilla, indicando qué pasó, datos afectados, medidas, contacto); SIC ≤ 72h si S1 (plantilla abogado); titulares si el riesgo es alto (plantilla abogado).
5. Remediación y evidencia: causa raíz, fix, test que reproduce antes/después; registrar `incident.resolved` en `decision_logs` y resumen en `docs/operations/incidents/`.
6. Game day (antes del go-live): escenario "leak de `app.customers` detectado por alarma de RLS bypass en staging" — ejecutar detección→contención→notificación ficticia→postmortem; medir tiempos; ajustar runbook.

**DoD:** game day completado con tiempos registrados; plantillas impresas en la carpeta `docs/legal/breach-templates/`; abogado valida lenguaje.

---
<a id="g-f5-d"></a>
## G-F5-D — Soporte, FAQ y acceso temporal auditado

1. `soporte@growup.com`: Google Workspace shared mailbox (delegación A+B) o `support@growup-soporte` alias; auto-reply con SLA (8h hábiles) y enlace a FAQ.
2. Repo privado `growup-soporte` con issue template "Ticket" (tenant, severidad, descripción, adjuntos sin PII real).
3. FAQ `help.growup.com` (GitHub Pages privada o página estática en el storefront principal, ruta `/ayuda`): artículos F5-07; publicar antes del piloto.
4. Acceso de soporte (W1-07): procedimiento — ticket con consentimiento del owner (respuesta escrita "autorizo acceso por 24h para [motivo]") → persona A abre sesión admin con su propio usuario + vista impersonation read-only (si existe feature) o logs de acceso; motivo y expiración registrados; cierre obligatorio con `decision_logs` `support.access_closed`; acceso de escritura prohibido salvo petición explícita y backup previo.
5. Nunca: compartir passwords; pedir datos de tarjeta; operar sobre datos de producción sin ticket; dejar sesiones abiertas.

**DoD:** FAQ pública con 10 artículos; acceso temporal ensayado y logueado; SLA configurado y comunicado en onboarding y factura/suscripción.

---
<a id="g-f6"></a>
## G-F6 — Seed demo (B-01) y Playwright E2E (B-02)

**Seed (`services/api/scripts/seed_demo.py`):** crear vía API/DB transacción única — tenants `ropa` (`ropa.growup.com`) y `joyeria` (`joyeria.growup.com`) `status=active`, settings default COP/es-CO, temas default, 3 categorías/tenant (`ropa: camisetas,pantalones,accesorios`; `joyeria: anillos,collares,aretes`), 6 productos/tenant con 2 variantes, precios COP centavos (`2999000` = $29.990), slugs únicos, `status='active'`, publish en página home seedeada. Idempotente: `on conflict do nothing` + verificación de conteos. **No** usar `seed.sql`; documentar comando en README. pgTAP sigue verde (no toca contadores globales).
**Playwright (`apps/storefront/e2e/`):** config con `baseURL=http://localhost:3000` y headers host por proyecto (`ropa.growup.com` mapeado a 127.0.0.1 via `webServer` o `host` header en `extraHTTPHeaders`). Tests: home muestra nombre tenant; colección lista productos; PDP variantes/precio/alt; producto inexistente → 404; host ajeno no ve datos; compra sandbox mockeando webhook (estado `paid`); axe sin críticos; LCP medido vía `page.metrics()` o Lighthouse CI aparte. Script `test:e2e`. Corre en job `e2e` en main contra staging.

**IMPORTANTE — transporte de SQL con texto no-ASCII (regla dura, 2026-11-10):** `Get-Content file.sql -Raw | docker exec -i psql -f -` en PowerShell 5.1 decodifica el archivo con la página de códigos de la consola (cp437/cp1252) y convierte los acentos a `?` (mojibake irreversible en la BD — ocurrió con el seed demo). Aplicar SQL con texto en español **siempre** con:
```powershell
docker cp supabase/seed.demo.sql growup-pg-audit:/tmp/seed.demo.sql
docker exec growup-pg-audit psql -U postgres -d growup -f /tmp/seed.demo.sql
```
(o `cmd /c type supabase/seed.demo.sql | docker exec -i growup-pg-audit psql -U postgres -d growup`, o `psql` instalado en el host). Verificar tras cualquier seed/carga de datos:
```sql
select 'tenants' t, name from app.tenants where name like '%?%'
union all select 'categories', name from app.categories where name like '%?%'
union all select 'products', name from app.products where name like '%?%'
union all select 'pages', title from app.pages where title like '%?%'
union all select 'page_versions', left(layout::text, 80) from app.page_versions where layout::text like '%?%';
```
Debe devolver 0 filas. Si detecta mojibake: sobrescribir las filas afectadas con el SQL correctivo equivalente vía `docker cp`. Nota: la caché ISR/fetch de Next (`revalidate=3600`) sirve respuestas previas hasta expirar; tras corregir datos, **reiniciar los servidores del storefront** o borrar `.next/cache`.

**DoD:** B-01 y B-02 criterios de `reparto-trabajo.md` cumplidos; evidencia en PR (7 test cases + `axe` output).

---
<a id="b-03"></a>
## B-03 — CI y seguridad (checklist definitiva)

- [ ] `pip-audit --strict` en job API (falla el build en HIGH/CRITICAL).
- [ ] `pnpm audit --prod --audit-level high` en frontend (misma política).
- [ ] Trivy sobre la imagen API/worker (F1-A).
- [ ] Gitleaks en CI + **secret scanning nativo de GitHub activado** (Settings → Code security) + push protection.
- [ ] Branch protection `main`: PR + checks + review + no force push; CODEOWNERS.
- [ ] Dependabot o Renovate semanal (grupos: python, npm, docker, gh-actions).
- [ ] `docs/compliance/vendor-review.md` con primera revisión fechada.
- [ ] MFA obligatorio en GitHub/Vercel/Fly/Supabase/Cloudflare/Stripe/Wompi/Resend/Google (evidencia: capturas archivadas sin datos, solo settings).
- [ ] Rotación de secretos documentada (cadencia 180 días; responsable; checklist post-rotación).

---
<a id="go-live"></a>
## Guía de go-live (piloto ropa+joyería)

**T-7 días:** restore de backup verificado; runbooks impresos; inventario de scripts checkout; DPA firmado por ambos comercios; FAQs publicadas; cuentas Stripe suscripción cobrando trial; monitoreo dashboards listos; on-call confirmado.
**T-24h:** freeze de migraciones (solo hotfix); freeze de contenido; último smoke test completo (Playwright) en prod; banner "envío listo"; comunicar a comercios con agenda y canal directo.
**T-0 (go):** DNS público final; verificar ropa/joyeria en navegador limpio (3 redes distintas); prueba de compra real con tarjeta propia (monto mínimo) en joyería; factura Factus llega al email; owner recibe magic link; logs en verde; postear en canal.
**T+24h / T+72h:** vigilancia activa (dashboards + Sentry + logs); revisión de métricas (errores, p95, órdenes); ajuste fino WAF si falsos positivos; comunicación proactiva a comercios.
**T+7 días:** postmortem-lite; lecciones; decisión formal go/no-go fase 2 (dominio custom, más tenants, features diferidas).

**Rollback:** Vercel Instant Rollback (1 click) → Fly `fly deploy --image <anterior>` → migración contract reversa **solo** con script probado; datos de órdenes nunca se pierden (webhook Wompi hace recon).

---
<a id="plantillas"></a>
## Plantillas de revisión y PR

**PR template** (`.github/pull_request_template.md`):
```markdown
## Qué cambia y por qué
## Evidencia (tests, capturas, logs)
- [ ] `ruff`, `mypy`, `pytest` verdes · [ ] `pnpm lint/typecheck/build` verdes · [ ] pgTAP verdes
## Base de datos
- [ ] Migración expand/contract incluida · [ ] pgTAP nuevos · [ ] Sin DROP destructivo en este deploy
## Multi-tenant y seguridad
- [ ] `tenant-isolation-check` ejecutada (si toca tenancy) · [ ] Sin secretos/PII en logs
## Contenido / bloques
- [ ] `block-review` ejecutada · [ ] Esquemas cerrados, sin HTML arbitrario
## Pagos / webhooks
- [ ] `payment-webhook-review` ejecutada · [ ] Idempotencia verificada · [ ] Firma validada
## Despliegue
- [ ] Orden: migraciones → API → frontend · [ ] Rollback documentado
```
**`tenant-isolation-check` (resumen operativo):** para cada endpoint nuevo/tocado: probar con tenant A y B (y con tenant suspendido); listado/insert/update/delete cruzados fallan o devuelven 403/404; `X-Tenant-ID` ignorado; `tenant_id` nunca del body; RLS con `app_rw`; skill `.kiro/skills/tenant-isolation-check` o equivalente manual documentado en PR.
**`block-review`:** cada bloque nuevo/tocado: schema cerrado probado con payloads maliciosos, `alt` obligatorio, límites de items, Markdown saneado, allowlist de video, fallback desconocido, snapshot del render, publish purge verificado.
**`payment-webhook-review`:** firma/HMAC, idempotencia `event_id`, orden de eventos, reintentos, no PAN en logs, montos en centavos re-leídos de BD (nunca del webhook), timeouts y DLQ, alertas.
