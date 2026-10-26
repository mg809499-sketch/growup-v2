# apps/admin

Backoffice multi-tenant: catálogo, media, auditoría, tenants de plataforma y,
más adelante, builder y pedidos.

## Estado

- Login con Supabase Auth (staff) y sesión por cookies.
- Resumen con rol, tenant y permisos (`/v1/admin/me`).
- Catálogo de solo lectura: listado y detalle con variantes/media.
- Media de solo lectura.
- Auditoría con verificación de cadena.
- Tenants de plataforma con búsqueda, estado y paginación.
- Sin builder, pedidos ni edición todavía.

## Ejecutar

```bash
cp apps/admin/.env.example apps/admin/.env.local
# NEXT_PUBLIC_SUPABASE_URL y NEXT_PUBLIC_SUPABASE_ANON_KEY
# GROWUP_API_URL=http://127.0.0.1:8000
pnpm install
pnpm --filter @growup/admin dev
```

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
