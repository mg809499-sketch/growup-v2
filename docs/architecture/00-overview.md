# Arquitectura — Overview

> Documento vivo. Las decisiones cerradas viven en [`docs/adr/`](../adr/README.md); este documento describe cómo encajan.

## 1. Contexto

Growup es un SaaS multi-tenant de comercio para moda y joyería en Colombia. Un comerciante crea su tienda, carga catálogo, elige un tema, edita páginas con un builder de bloques y publica en `{slug}.growup.com`. El comprador navega el storefront, compra como invitado y paga con Wompi. Growup cobra una suscripción mensual por la plataforma.

```text
Comprador ──► Storefront (Next.js) ──► API FastAPI ──► PostgreSQL (Supabase)
Comerciante ─► Admin (Next.js) ──────► API FastAPI ──► Redis / R2 / Wompi / Stripe
Worker ARQ ──────────────────────────► API/DB ───────► Email / DIAN / Conciliación
```

## 2. Actores

| Actor | Dónde entra | Qué hace |
|---|---|---|
| Comprador | `{slug}.growup.com` | Navega, compra como invitado, reclama historial con magic link |
| Personal del comerciante | `admin.growup.com` | Catálogo, media, builder, pedidos, pagos, equipo |
| Platform admin | `admin.growup.com/platform` | Tenants, planes, soporte, auditoría |
| Worker | Sin ingress | Media, facturas, webhooks, emails, conciliación |
| Pasarelas | Webhooks | Wompi (checkout), Stripe (suscripción) |

## 3. Contenedores

| Contenedor | Tecnología | Despliegue | ADR |
|---|---|---|---|
| Storefront | Next.js 16 App Router, RSC, Tailwind 4 | Vercel | 0005, 0008 |
| Admin | Next.js 16 App Router | Vercel | 0008 |
| API | FastAPI, Pydantic v2, asyncpg | Fly.io | 0003, 0004, 0008 |
| Workers | ARQ sobre Redis | Fly.io | 0006 |
| Base de datos | PostgreSQL (Supabase) + RLS | Supabase | 0003 |
| Caché / colas | Redis (Upstash) | Upstash | 0006 |
| Media | Cloudflare R2 + CDN | Cloudflare | 0006 |
| Búsqueda | PostgreSQL FTS + pg_trgm | Supabase | 0006 |
| Observabilidad | Sentry + OpenTelemetry | SaaS | 0006 |
| Contratos | OpenAPI → TypeScript | CI | 0006 |

## 4. Mapa de dominios del backend

```text
services/api/app/
├─ core/                 # config, db, auth, tenant, cache, queue, observability
├─ domains/
│  ├─ identity/          # staff, customers, roles, magic links
│  ├─ tenants/           # tenants, domains, settings, features, onboarding
│  ├─ catalog/           # products, variants, categories, collections, inventory
│  ├─ content/           # pages, versions, blocks, themes, publish, preview
│  ├─ commerce/          # carts, checkout, orders, shipping
│  ├─ payments/          # tenant accounts, payments, webhooks, refunds
│  ├─ billing/           # plans, subscriptions, platform invoices
│  ├─ invoices/          # DIAN provider adapter, invoices
│  ├─ governance/        # policies, decisions, approvals
│  ├─ media/             # uploads, variants, R2
│  ├─ search/            # queries, facets
│  └─ notifications/     # email templates, outbox
├─ platform/             # endpoints de platform admin
└─ workers/              # ARQ jobs
```

Regla: cada dominio expone `router.py`, `schemas.py`, `service.py`, `repository.py` y `policies.py` cuando aplica. Los dominios no se importan entre sí por dentro; se comunican por servicios de aplicación o eventos.

## 5. Flujos clave

### 5.1 Render de una página

```text
Browser → {slug}.growup.com
  → Next resuelve host y pide bootstrap a la API
  → API: host → domains → tenant (cacheado)
  → API devuelve tenant, tema y settings
  → Next pide la página publicada por slug
  → BlockRenderer renderiza la versión publicada
  → CDN/Next cachea por tenant + página; publish purga el tag
```

### 5.2 Checkout

```text
Carrito (cliente) → POST /v1/checkout
  → valida stock y precios en servidor
  → reserva stock con TTL
  → crea payment + redirect a Wompi Web Checkout
  → comprador paga
  → webhook firmado de Wompi
  → verifica monto, marca orden pagada, confirma stock
  → encola email + factura DIAN
  → confirma al comprador
```

### 5.3 Publicar una página

```text
Admin builder → autosave draft (control optimista)
  → POST /v1/content/pages/{id}/publish
  → valida schema, permisos y render
  → crea page_version inmutable y actualiza published_version_id
  → outbox → worker purga caché
  → storefront sirve la nueva versión
```

### 5.4 Suscripción de la plataforma

```text
Admin → Stripe Checkout (trial 14 días)
  → webhook Stripe firmado
  → actualiza platform_subscription
  → recalcula entitlements (tenant_features)
  → past_due → gracia → suspensión de publish
```

## 6. Decisiones que gobiernan el sistema

| Tema | Decisión | ADR |
|---|---|---|
| Producto | SaaS multi-tenant con builder | 0001 |
| Repositorio | Port selectivo desde `multitiendas` | 0002 |
| Identidad | Supabase Auth + JWKS + RLS | 0003 |
| Pagos | Merchant of record = comerciante; Wompi + Stripe | 0004 |
| Contenido | JSONB versionado, publish atómico, bloques cerrados | 0005 |
| Satélites | Postgres FTS, ARQ, R2, Sentry/OTel | 0006 |
| Gobernanza | `decide()` + auditoría hash chain | 0007 |
| Despliegue | Vercel + Fly + Supabase + Upstash + R2 | 0008 |

## 7. Fuera de alcance del MVP

Returns/RMA, bespoke, promociones, envío blindado, IA/WhatsApp, L402, multi-moneda, dominios custom, comisión por venta/marketplace. Ver D-05.

## 8. Documentos relacionados

- [Modelo de datos](02-datos.md)
- [Tenancy y threat model](03-tenancy.md)
- [Flujos de seguridad de extremo a extremo](04-flujos-seguridad.md)
- [Flujos legales propuestos](../legal/flujos.md)
- [ADRs](../adr/README.md)
- [Decisiones de negocio](../decisiones-pendientes.md)
- [Spec del MVP](../../.kiro/specs/storefront-platform-v2/requirements.md)
