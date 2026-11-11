# apps/admin

Backoffice multi-tenant: catálogo, media, auditoría, tenants de plataforma y,
más adelante, builder y pedidos.

## Estado

- Login con Supabase Auth (staff) y sesión por cookies.
- **Signup self-service de comerciantes** (`/login` → panel «Crear cuenta»):
  continuán con Google → formulario (nombre completo, correo, celular, tipo y
  número de identificación, nombre/tipo de tienda, plan, slug y dominio) →
  `POST /v1/onboarding/complete` crea tenant (trialing, 14 días) + membership
  `owner/active` + fila en `app.clients` + `app_metadata` (`tenant_id`, `role=owner`),
  en una sola transacción (`app.complete_client_signup`, ADR-0019).
- Resumen con rol, tenant y permisos (`/v1/admin/me`).
- Catálogo editable: crear/editar producto, añadir/editar/eliminar variantes.
- Media: asociar/quitar imágenes del producto y editar `alt`.
- Auditoría con verificación de cadena.
- Tenants de plataforma con búsqueda, estado y paginación.
- Sin builder, pedidos, upload directo de media ni ajuste de inventario todavía.

## Ejecutar

```bash
cp apps/admin/.env.example apps/admin/.env.local
# NEXT_PUBLIC_SUPABASE_URL y NEXT_PUBLIC_SUPABASE_ANON_KEY
# GROWUP_API_URL=http://127.0.0.1:8000
pnpm install
pnpm --filter @growup/admin dev    # http://localhost:3001
```

## Alta self-service: activar Google OAuth en local

El botón «Continuar con Google» requiere un OAuth client (tipo Web) del
proyecto:

1. Google Cloud Console → APIs & Services → Credentials → Create OAuth client →
   **Web application**.
2. Authorized redirect URI: `http://127.0.0.1:54321/auth/v1/callback`
   (en producción: `https://<project-ref>.supabase.co/auth/v1/callback`).
3. En `supabase/config.toml`, sección `[auth.external.google]`: pegar
   `client_id`, descomentar `secret = "env(SUPABASE_AUTH_EXTERNAL_GOOGLE_SECRET)"`
   exportando esa variable (o pegar el secret solo en local, nunca commitear).
4. `enabled = true` y reiniciar Supabase (`pnpm dlx supabase stop && pnpm dlx supabase start`).
5. Reiniciar el admin si hace falta y probar en http://localhost:3001/login.

Sin credenciales, el botón muestra «No se pudo continuar con Google» (error
`oauth`) y el resto del login sigue funcionando con email+contraseña. En
producción se configura el provider en la dashboard de Supabase, nunca en el repo.

## Notas del flujo de alta

- Los campos del formulario (correo readonly desde el JWT de Google) llegan a
  la API en `POST /v1/onboarding/complete`; la API verifica el JWT vía JWKS y
  crea todo en una transacción. Idempotente: reintentos con el mismo usuario
  responden `SIGNUP_ALREADY_COMPLETED` y el admin entra directo al panel.
- `slug.growup.com` se vende (D-19, abierta): el checkbox «Quiero comprarlo»
  solo registra la intención (`app.clients.wants_subdomain`); no hay cobro aún.
- Dominio propio: se registra sin verificar (DNS posterior, `domains.type='custom'`).
- Plan: Starter/Pro sin precios hasta ratificar el derivado de D-01.


La API debe aceptar el JWT de Supabase vía JWKS. En local, Supabase Auth usa
HS256 por defecto y el verificador de la API rechaza ese algoritmo. Para el
flujo real:

1. Genera una signing key ES256 con `pnpm dlx supabase gen signing-key --algorithm ES256`.
2. Guarda el JWK en `supabase/signing_keys.json` dentro de un array (`[{...}]`).
   El archivo está en `.gitignore`; nunca se commitea.
3. Descomenta `signing_keys_path = "./signing_keys.json"` en `supabase/config.toml`.
4. Reinicia Supabase (`pnpm dlx supabase stop && pnpm dlx supabase start`).
5. Arranca la API con `GROWUP_SUPABASE_URL=http://127.0.0.1:54321`.

Sin esos pasos el login redirige correctamente pero la API rechaza el token
HS256. El storefront público no depende de esto.

## Criterios

- Next.js 16 App Router + TypeScript estricto + Tailwind CSS 4.
- Sin librerías de UI; componentes propios.
- El navegador no llama a FastAPI para mutaciones; las páginas server-side
  envían el Bearer token y la API valida firma/tenant.
- Ningún dato de otro tenant sin autorización de plataforma.
