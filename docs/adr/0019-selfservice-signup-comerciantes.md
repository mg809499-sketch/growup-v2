# ADR-0019 — Signup self-service de comerciantes en el admin

- **Estado:** Aceptada
- **Fecha:** 2026-11-11
- **Decisores:** equipo (implementado por agentes; valida el owner)
- **Relacionado con:** ADR-0003 (identidad y tenancy), D-01 (modelo de cobro, derivado pendiente), D-19 (venta de subdominios, abierta)

## Contexto

El acceso de comerciantes a la plataforma era 100% asistido: un comerciante no podía
crear su cuenta sin que alguien le creara el usuario en Supabase Auth y su
membresía manualmente. No hay credenciales por defecto y no deben existir.

El sitio marketing (`apps/web`, 3003) enviaba todos los CTAs "Solicitar acceso" a
`/solicitar-acceso` (formulario `mailto:` sin backend). Se quiere **automatizar
el alta**: que un comerciante cree su cuenta y su tienda sin intervención manual,
cumpliendo además la regla dura del proyecto (**los clientes nunca tocan Studio
ni el SQL**: nada de altas vía consola).

## Decisión

El admin (`apps/admin`, 3001) `/login` pasa a ser **dos paneles**:

- **Crear cuenta** — Google OAuth (Supabase Auth) y, tras autenticarse, un
  formulario con: nombre completo, celular, tipo y número de identificación
  legal, nombre y tipo de tienda (ropa/joyería/otro), plan (Starter/Pro), slug,
  y dominio (subdominio `slug.growup.com` o dominio propio con DNS posterior).
- **Iniciar sesión** — Google OAuth y email+contraseña (sin cambios de
  comportamiento para cuentas existentes).

Al enviar el formulario, la API (`POST /v1/onboarding/complete`) crea de forma
**atómica**, en una transacción vía función `SECURITY DEFINER`
(`app.complete_client_signup`): tenant (`trialing`, trial 14 días) → membership
`owner/active` → fila en `app.clients` (CRM de comerciantes; rol constante
`owner`) → actualización de `auth.users.raw_app_meta_data`
(`tenant_id`, `role='owner'`). El admin refresca la sesión y redirige al panel.

En `apps/web`, **todos** los CTAs "Solicitar acceso" se reemplazan por
**"Iniciar sesión"** → `admin_login_url` (`NEXT_PUBLIC_ADMIN_URL`), y
`/solicitar-acceso` queda como redirect permanente a esa URL.

`app.clients` es tabla de **plataforma** (CRM de comerciantes, como
`app.plans`): sin `tenant_id`, RLS forzado, **sin grants** para `app_rw`; solo
accede la función `SECURITY DEFINER`. `app_metadata` se toca desde esa función,
propiedad de la migración, no desde la API ni con `service_role`.

## Alternativas consideradas

| Alternativa | Pros | Contras | ¿Por qué no? |
|---|---|---|---|
| Mantener alta manual asistida | Cero superficie pública | No escala; requiere Studio para cada alta | Contradice el objetivo de automatizar |
| Onboarding vía platform admin (UI en 3001) | Sin endpoint público | Sigue siendo manual; no es self-service | No resuelve el caso "comerciante llega solo" |
| Alta vía `service_role` en la API | Directo | Viola la regla: service_role solo en workers | Rechazada por regla dura del repo |
| FK `clients.user_id → auth.users` | Integridad referencial | `auth` es esquema de GoTrue; FK cross-schema frágil; `memberships` ya omite FK por el mismo motivo | Rechazada por paridad con `memberships` |
| Tabla de alta temporal + trigger en `auth.users` | Un solo camino de escritura | El alta ocurre después del login OAuth (formulario posterior); el trigger no puede capturar los datos de la tienda | Rechazada: la opción actual (función atómica) es más simple y testeable |

## Consecuencias

### Positivas

- Alta self-service end-to-end sin intervención manual ni Studio.
- Atomicidad: cualquier fallo (slug tomado, plan inválido, dominio duplicado)
  revierte tenant + membresía + CRM; no quedan estados a medias.
- Idempotencia: un segundo intento del mismo usuario falla con
  `SIGNUP_ALREADY_COMPLETED` y el admin lo entra directo al panel.
- `service_role` no se usa fuera de workers; la API sigue con rol sujeto a RLS.

### Negativas / deuda asumida

- El endpoint `/v1/onboarding/complete` es **público con JWT Google** (cualquier
  cuenta de Google válida puede crear tenants). Falta rate-limiting por IP/usuario
  (Redis) o captcha; registrado como riesgo, no implementado en este ADR.
- **Cobro del subdominio**: `slug.growup.com` se venderá, pero en este ADR solo
  se registra la intención (`wants_subdomain`); el cobro queda en D-19 (abierta).
- **Precios de planes**: el selector muestra Starter/Pro sin precios hasta
  ratificar el derivado de D-01; `plans.price_cents` sigue en placeholder.
- **Dominio propio**: se registra como `domains(type='custom', verified_at=null)`;
  la verificación DNS queda para un paso posterior (manual o futura automatización).
- Google OAuth requiere client ID/secret propios del proyecto (no en el repo);
  en local se activa en `supabase/config.toml` con `enabled=true` + credenciales.

### Neutras

- `/solicitar-acceso` queda como redirect permanente (308) a `admin/login`:
  conserva enlaces históricos y sitemap externo.

## Cómo se verifica

- `supabase/tests/signup.sql` (pgTAP, 11 casos: alta feliz, dominio propio,
  idempotencia, slug tomado, plan inválido, acceso denegado para `app_rw`).
- `services/api/tests/integration/test_onboarding.py` (5 casos con DB real).
- Manual: http://localhost:3001/login → "Continuar con Google" → completar
  formulario → entrar al panel; http://localhost:3003 → "Iniciar sesión" →
  `http://localhost:3001/login`.

## Enlaces

- `supabase/migrations/20261111000000_client_signup.sql`
- `services/api/app/domains/onboarding/`
- `apps/admin/app/login/`, `apps/admin/app/auth/callback/`
- `apps/web/content/site.ts` (`admin_login_url`)
- ADR-0003 (identidad, tenancy y RLS) · D-01 (modelo de cobro) · D-19 (subdominios)
