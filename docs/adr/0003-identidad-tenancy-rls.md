# ADR-0003 — Identidad, tenancy y RLS

- **Estado:** Aceptada
- **Fecha:** 2026-10-21
- **Decisores:** equipo de ingeniería
- **Relacionado con:** D-04, D-07, ADR-0002, `.kiro/steering/security.md`

## Contexto

Growup sirve N tiendas desde un solo storefront y un solo admin. El tenant se resuelve por host y cada página se renderiza desde una versión publicada. Esa arquitectura solo es segura si la identidad, el tenant y el aislamiento de datos se resuelven de forma determinista en el backend y en la base de datos.

La V1 de `multitiendas` tiene tres defectos que no se deben repetir:

1. Decodifica el JWT sin verificar la firma.
2. Usa una política `tenants_isolated USING (true)`.
3. Usa `service_role` en la API y fija el tenant con `NEXT_PUBLIC_TENANT_ID`.

Las decisiones de negocio ya cerradas fijan el marco:

- **D-04:** el comprador final compra como invitado y puede reclamar su historial con magic link. El personal del comerciante usa Supabase Auth.
- **D-07:** los comerciantes publican en subdominios `*.growup.com` con wildcard TLS; los dominios custom se posponen a fase 3.

## Decisión

### 1. Proveedor de identidad

- **Supabase Auth** es el IdP.
- **Personal del comerciante:** email + contraseña (o magic link) con Supabase Auth. Roles en `app_metadata`: `owner`, `manager`, `treasurer`, `packer`, `support`.
- **Comprador final:** checkout como invitado. El magic link es opcional y sirve para reclamar historial y direcciones; no hay contraseñas de comprador.
- **Platform admin:** rol `platform_admin` con `tenant_id = null`. Solo accede a endpoints de plataforma auditados; no obtiene `BYPASSRLS`.

### 2. Verificación del JWT

La API verifica cada token con las claves públicas de Supabase (JWKS):

- Firma asimétrica (`RS256`/`ES256`), nunca `alg: none`.
- `iss`, `aud`, `exp` y `nbf`.
- Caché de JWKS con expiración y refresco ante `kid` desconocido.
- Prohibido `jwt.decode(..., verify_signature=False)` y prohibido leer claims de un token sin verificar.
- Tenant y rol se leen exclusivamente de `app_metadata.tenant_id` y `app_metadata.role`.
- Token válido sin `tenant_id` solo se acepta en rutas de plataforma.

### 3. Resolución del tenant

```text
Host (normalizado) → domains.host → tenant_id
```

- Normalización: minúsculas, sin puerto, sin punto final, IDN a punycode.
- Para `*.growup.com`, el slug del subdominio se resuelve contra `domains`; no se acepta cualquier subdominio.
- Host desconocido → `404 TENANT_NOT_FOUND`.
- `X-Tenant-ID` es solo un hint interno entre servicios. Si llega desde internet y no coincide con el host o con el claim del JWT → `403 TENANT_MISMATCH` + evento de seguridad.
- La resolución de `tenants` y `domains` se hace con una función `SECURITY DEFINER` acotada (`app.resolve_tenant(host)`), no con una política `USING (true)`.

### 4. Roles de base de datos

| Rol | Uso | RLS | DDL |
|---|---|---|---|
| `app_rw` | API | Sujeto a RLS | No |
| `app_worker` | Workers y jobs | Sujeto a RLS, con contexto explícito por tenant | No |
| `service_role` | Tareas administrativas auditadas | Bypass intencional y auditado | No |
| owner de migraciones | Migraciones | N/A | Sí |

- La API usa `app_rw`, sin `BYPASSRLS`.
- `service_role` no se usa en la API; solo en workers y tareas administrativas que lo justifiquen y queden auditadas.
- Las migraciones se ejecutan con un rol distinto al de la API.

### 5. RLS forzado

Toda tabla de negocio cumple:

```sql
tenant_id uuid not null references tenants(id),
-- índice por tenant_id
alter table <tabla> enable row level security;
alter table <tabla> force row level security;

create policy tenant_isolation on <tabla>
  using (tenant_id = app.current_tenant())
  with check (tenant_id = app.current_tenant());
```

- `app.current_tenant()` lee `current_setting('app.tenant_id', true)` y devuelve `uuid`. Si no hay contexto, la política deniega.
- El contexto se fija con `SET LOCAL app.tenant_id = '<uuid>'` dentro de una transacción. Nunca `SET` de sesión.
- El pool de conexiones debe preservar el contexto transaccional; si se usa PgBouncer en modo transacción, `SET LOCAL` es obligatorio y se documenta.
- `tenants` no tiene política `USING (true)`. El acceso público se limita a la función de resolución.
- Las tablas de plataforma (`plans`, `subscriptions` de plataforma, `platform_admins`) usan políticas propias y no se mezclan con tablas de tenant.

### 6. Flujos de autenticación

- **Admin:** Next.js con `@supabase/ssr`; la sesión vive en cookies `HttpOnly`, `Secure`, `SameSite=Lax`. Los Server Actions y Route Handlers llaman a FastAPI con `Authorization: Bearer <access_token>`.
- **Storefront:** rutas públicas sin JWT; el tenant se resuelve por host y solo se sirve contenido publicado. El magic link se gestiona con Supabase Auth OTP y se vincula a `customers.auth_user_id`.
- **Navegador:** puede hablar con los endpoints de Auth de Supabase, pero nunca con Postgres, Storage ni tablas directamente. Todo dato de negocio pasa por FastAPI.

### 7. Autorización

- La matriz de permisos por rol vive en el dominio (`app/domains/identity/policies.py`) y se prueba con pytest.
- Un token de un tenant no puede operar sobre otro, aunque el rol sea `owner`.
- Las rutas de plataforma exigen `platform_admin` y dejan auditoría.
- Los errores de autorización son estables: `TENANT_MISMATCH`, `FORBIDDEN`, `TOKEN_INVALID`, `TOKEN_EXPIRED`.

### 8. Auditoría de seguridad

Se registran en una tabla append-only:

- Mismatch de host/claim.
- Token inválido o firma fallida.
- Cambios de rol o de tenant.
- Accesos de `platform_admin`.
- Intentos de acceso cross-tenant.

Sin PII cruda en logs; se guarda `tenant_id`, actor, evento, resultado, IP y `trace_id`.

## Alternativas consideradas

| Alternativa | Pros | Contras | ¿Por qué no? |
|---|---|---|---|
| A. Auth propio con contraseñas | Control total | Superficie de ataque y mantenimiento altos | No es el core del producto |
| B. Supabase Auth + RLS (elegida) | IdP gestionado, JWT estándar, RLS en la misma base | Dependencia de Supabase; hay que cuidar el pool | Mejor relación riesgo/costo |
| C. Solo autorización en la API | Menos setup inicial | Un bug de código filtra todos los tenants | El aislamiento debe estar en la DB |
| D. `service_role` en la API | Menos fricción con RLS | Anula la defensa en profundidad | Prohibido por seguridad |

## Consecuencias

### Positivas

- El aislamiento queda enforced por PostgreSQL, no solo por código.
- Un solo modelo de identidad para admin, storefront y workers.
- Los dominios custom se añaden después sin cambiar el contrato (`domains.host`).
- Los defectos críticos de la V1 se corrigen antes de portar módulos.

### Negativas / deuda asumida

- Hay que implementar y testear la caché de JWKS y el manejo de cookies en Next.js.
- RLS exige tests de integración con Postgres real; no basta con mocks.
- El magic link depende de la deliverability del proveedor de email.
- El pool de conexiones debe configurarse con cuidado para no perder `SET LOCAL`.

### Neutras

- Supabase Auth es el IdP, pero la API no confía en el cliente: siempre verifica el token.
- El platform admin existe, pero no es un superusuario de base de datos.

## Cómo se verifica

- **JWT:** firma inválida, `alg: none`, token expirado, `aud` incorrecto, `iss` incorrecto, token sin `tenant_id` en ruta de tenant.
- **Host:** subdominio válido, desconocido, con puerto, con mayúsculas, con `X-Tenant-ID` spoofeado.
- **RLS:** SELECT/INSERT/UPDATE/DELETE cross-tenant devuelven 0 filas o error; `app_rw` no puede hacer `BYPASSRLS`; sin `SET LOCAL` no se ven filas.
- **Roles:** un `owner` del tenant A no puede mutar el tenant B; un `packer` no puede cambiar precios.
- **Auditoría:** cada mismatch genera un evento con `trace_id`.
- **Pen-test:** 12 vectores cross-tenant definidos en `docs/architecture/03-tenancy.md` (pendiente de escribir).

## Enlaces

- [D-04 y D-07](../decisiones-pendientes.md)
- [ADR-0002](0002-repositorio-y-reutilizacion.md)
- [Security steering](../../.kiro/steering/security.md)
