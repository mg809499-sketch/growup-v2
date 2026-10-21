# apps/admin

Backoffice multi-tenant: builder de páginas, catálogo, pedidos, ajustes y auditoría.

## Estado

Placeholder. Se scaffolding en la Wave 5, después de cerrar D-01 (modelo de cobro) y D-05 (alcance del MVP).

## Criterios

- Next.js 16 + TypeScript estricto.
- Autenticación con Supabase Auth y roles por tenant.
- Builder con autosave, bloqueo optimista por `version`, preview y publish.
- Sin acceso directo a Postgres; consume FastAPI.
- Nunca muestra datos de otro tenant, ni siquiera a un administrador de plataforma sin auditoría.
