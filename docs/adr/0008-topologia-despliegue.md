# ADR-0008 — Topología de despliegue

- **Estado:** Aceptada
- **Fecha:** 2026-10-21
- **Decisores:** equipo de ingeniería
- **Relacionado con:** ADR-0003, ADR-0004, ADR-0006, D-07, D-08

## Contexto

Growup tiene cuatro cargas distintas: storefront público, admin autenticado, API y workers. El storefront debe servir `*.growup.com` con wildcard TLS y baja latencia móvil; el admin y la API manejan datos sensibles; los workers ejecutan jobs de media, facturas, webhooks y conciliación. El equipo es pequeño y el objetivo es operar con pocos servicios gestionados.

## Decisión

### 1. Ambientes

| Ambiente | Frontend | API / workers | Datos |
|---|---|---|---|
| Local | `pnpm dev` (Next) | `uv run uvicorn` + `arq` | Supabase CLI o proyecto dev, Redis local, R2 dev |
| Staging | Vercel Preview/Staging | Fly.io staging | Supabase staging, Upstash staging, R2 staging |
| Producción | Vercel Production | Fly.io production | Supabase prod, Upstash prod, R2 prod |

- Proyectos, buckets, claves y bases separados. Prohibido usar datos de producción en staging.
- Pasarelas en modo sandbox en local/staging; llaves de producción solo en prod.
- Variables por ambiente; nunca se comparten secretos entre staging y prod.

### 2. Frontend en Vercel

- `apps/storefront` y `apps/admin` son proyectos separados de Vercel, mismo monorepo.
- Dominios:
  - Storefront: `*.growup.com` (wildcard) + apex `growup.com`.
  - Admin: `admin.growup.com`.
  - API: `api.growup.com`.
- TLS: Vercel emite y renueva el certificado wildcard; DNS en Cloudflare con los registros que indique Vercel.
- El storefront resuelve el tenant en el servidor a partir del `Host`; no usa `NEXT_PUBLIC_TENANT_ID`.
- `middleware.ts` solo normaliza host y aplica headers de seguridad; la resolución de tenant se cachea en el servidor.
- Preview deployments de Vercel usan una protección de acceso; no indexables.

### 3. API y workers en Fly.io

- API: contenedor Docker, `uv` con `uv.lock`, usuario no root, health checks `/healthz` (liveness) y `/readyz` (DB/Redis).
- Workers: misma imagen, comando `arq app.worker.WorkerSettings`, sin ingress público, escala independiente.
- Región: la más cercana al proyecto Supabase y a Colombia. Preferencia `sa-east-1` (São Paulo) si Supabase y Fly la ofrecen; si no, `us-east-1`. Se decide al crear la infraestructura.
- Réplicas mínimas: 1 API en staging; 2 en producción detrás del balanceador de Fly. Workers: 1-2 según cola.
- `auto_stop_machines` para staging; producción siempre encendida.
- **Render** queda como alternativa operativa si Fly no cumple latencia o soporte; la arquitectura no cambia.

### 4. Base de datos y pooling

- Supabase Postgres; migraciones con Supabase CLI desde CI.
- La API se conecta por **Supavisor en modo transacción**; cada request abre transacción y usa `SET LOCAL app.tenant_id`.
- Migraciones y jobs administrativos usan conexión directa, no el pooler transaccional.
- Si el modo transacción rompe alguna extensión o contexto, se documenta y se usa sesión dedicada; prohibido cambiar a `SET` de sesión.
- Límite de conexiones por instancia; monitoreo de saturación.
- Migraciones **expand/contract**: primero añadir, desplegar, migrar datos, luego eliminar. Nunca un `DROP` destructivo en el mismo deploy que el código que lo usa.

### 5. Redis, media y email

- Upstash Redis con TLS; bases separadas para cache, colas y rate limiting.
- R2 con buckets por ambiente; CDN de Cloudflare para catálogo; URLs firmadas para privados.
- Email transaccional con proveedor externo (Resend recomendado); SMTP de respaldo.

### 6. CI/CD

Pipeline en GitHub Actions:

1. **API:** `ruff`, `mypy`, `pytest`, `pip-audit`.
2. **Frontend:** `pnpm lint`, `pnpm typecheck`, `pnpm build`, `pnpm audit`.
3. **Contratos:** verificar que `packages/contracts` está regenerado.
4. **Migraciones:** `supabase db diff --check` en staging; sin drift.
5. **Seguridad:** Trivy en la imagen; secret scanning.
6. **Deploy staging:** automático en `main` (Vercel + Fly).
7. **Smoke tests:** health, home de los dos tenants, login admin, checkout sandbox.
8. **Deploy producción:** manual con aprobación; migraciones primero, API después, frontend al final.
9. **Rollback:** Vercel instantáneo; Fly con release anterior; migraciones compatibles hacia atrás.

### 7. Seguridad de borde

- Cloudflare delante de `growup.com` y `api.growup.com`: WAF, rate limiting por IP, bot protection.
- CORS allowlist exacta (`admin.growup.com`, `*.growup.com` en desarrollo).
- HSTS, CSP estricta, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`.
- Cookies de admin `HttpOnly`, `Secure`, `SameSite=Lax`.
- Admin no indexable; `robots.txt` y `X-Robots-Tag`.
- Secretos en GitHub Environments, Fly secrets y Vercel env; rotación documentada.

### 8. Observabilidad y respuesta

- Sentry por servicio con releases y `trace_id`.
- OTel exportado a colector/Sentry/Grafana; logs JSON a stdout.
- Dashboards: latencia, 5xx, cola, webhooks, conexiones, costo.
- Alertas al canal de operaciones; runbooks en `docs/operations/`.
- On-call: una persona; escalado a ingeniería.

### 9. Recuperación

- **RPO:** ≤ 15 minutos (PITR de Supabase + dumps diarios a R2).
- **RTO:** ≤ 2 horas para API/storefront; ≤ 4 horas para workers.
- Restauración probada trimestralmente en staging.
- Runbook de incidente: declarar, mitigar, comunicar, postmortem sin culpables.

### 10. Costos

- Alertas de presupuesto en Vercel, Fly, Supabase, Upstash y Cloudflare.
- Etiquetado por ambiente; revisión mensual.
- Staging con scale-to-zero y datos pequeños.

## Alternativas consideradas

| Alternativa | Pros | Contras | ¿Por qué no? |
|---|---|---|---|
| A. Todo en Vercel (API serverless) | Un solo proveedor | Cold starts, conexiones, workers | La API y los workers necesitan proceso persistente |
| B. Vercel + Fly + Supabase (elegida) | Gestión mínima, región flexible, wildcard TLS | Varios proveedores | Mejor equilibrio para el equipo |
| C. AWS ECS/RDS | Control y escala | Mucha operación | No justificado para el MVP |
| D. Render para todo | Simple | Menos regiones y control | Alternativa, no primera opción |
| E. Self-hosted Postgres | Control total | Backups, RLS, Auth, PITR a cargo del equipo | Supabase ya resuelve eso |

## Consecuencias

### Positivas

- Wildcard TLS y despliegues de frontend sin gestionar certificados.
- API y workers escalan y despliegan por separado.
- Supabase cubre Postgres, Auth, RLS y PITR.
- El pipeline bloquea contratos desactualizados y migraciones destructivas.

### Negativas / deuda asumida

- Cuatro proveedores que monitorear y pagar.
- La latencia Colombia → región elegida debe medirse; si es alta, se ajusta la región.
- El pooler transaccional exige disciplina con `SET LOCAL`.
- La restauración y los runbooks requieren práctica, no solo documentación.

### Neutras

- Fly vs Render es una decisión operativa reversible.
- La región puede cambiar antes del lanzamiento; después implica migración.

## Cómo se verifica

- `https://{slug}.growup.com` responde con TLS válido y HSTS.
- Un subdominio inexistente devuelve 404, no el tenant por defecto.
- `api.growup.com/healthz` y `/readyz` responden 200.
- Un deploy de staging desde `main` pasa smoke tests de los dos tenants.
- Una migración incompatible falla el check y no llega a producción.
- Restauración de un dump en staging dentro del RTO.
- `trace_id` cruza Vercel → Fly → worker en Sentry/OTel.
- Los headers CSP/HSTS están presentes en storefront y admin.

## Pendientes

- Confirmar región Supabase/Fly y medir latencia desde Colombia.
- Confirmar Fly vs Render.
- Definir proveedor de email y dominio de envío.
- Crear `docs/operations/` con runbooks antes del go-live.

## Enlaces

- [ADR-0003](0003-identidad-tenancy-rls.md)
- [ADR-0004](0004-pagos-checkout-merchant-of-record.md)
- [ADR-0006](0006-stack-satelite.md)
- [Tech stack steering](../../.kiro/steering/tech-stack.md)
