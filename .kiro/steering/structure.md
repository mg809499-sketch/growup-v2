---
inclusion: always
---

# Estructura y fronteras del repositorio

## Mapa

```text
growup/
├─ apps/
│  ├─ storefront/        # Next.js público: host→tenant, páginas publicadas, carrito
│  └─ admin/             # Next.js privado: builder, catálogo, pedidos, billing
├─ services/api/         # FastAPI + workers ARQ
│  ├─ app/core/          # config, db, auth, tenancy, cache, observabilidad
│  ├─ app/domains/       # identity, tenants, catalog, content, commerce, payments...
│  ├─ app/api/           # dependencias HTTP compartidas
│  ├─ app/schemas/       # schemas de ops/plataforma
│  └─ tests/             # unitarios, integración, contratos
├─ packages/contracts/   # OpenAPI → TypeScript (generado)
├─ supabase/             # migraciones, seed, tests pgTAP
├─ docs/                 # ADRs, arquitectura, decisiones
└─ .kiro/                # steering, specs, skills, hooks
```

## Reglas de dependencia

- `apps/storefront` y `apps/admin` no comparten estado de React ni lógica de negocio; comparten `packages/contracts` y tokens.
- El navegador no llama a FastAPI para mutaciones del storefront: usa el BFF de Next (`apps/storefront`), que firma el host.
- `apps/*` no importa código Python. `services/api` no importa código TypeScript.
- `services/api/app/core/` no importa `domains/`. Los dominios pueden importar `core/`.
- Los dominios no se importan entre sí por sus internals; exponen servicios de aplicación o eventos.
- `workers/` puede importar dominios; nunca al revés.
- `packages/contracts/src/schema.d.ts` es generado. No se edita a mano: se regenera con `pnpm contracts:generate`.

## Dónde va cada cambio

| Cambio | Ubicación |
|---|---|
| Regla de negocio | `services/api/app/domains/<dominio>/service.py` |
| Acceso a datos | `services/api/app/domains/<dominio>/repository.py` |
| Endpoint | `services/api/app/domains/<dominio>/router.py` |
| Schema HTTP | `services/api/app/domains/<dominio>/schemas.py` |
| Migración/RLS | `supabase/migrations/` + test pgTAP |
| Contrato compartido | `packages/contracts` (generado) |
| Componente visual | `apps/storefront` o `apps/admin` |
| Decisión de arquitectura | `docs/adr/` |
| Decisión de negocio | `docs/decisiones-pendientes.md` |
| Regla permanente para agentes | `.kiro/steering/` |
| Check reutilizable | `.kiro/skills/<nombre>/SKILL.md` |
| Automatización | `.kiro/hooks/<nombre>.json` |

## Naming

- Python: `snake_case`; clases `PascalCase`; módulos por dominio.
- TypeScript: `camelCase`; componentes `PascalCase`; archivos `kebab-case`.
- SQL: tablas en plural, columnas en singular, `snake_case`.
- Dinero: `*_cents` como `bigint`; nunca `float`.
- Errores: códigos estables en `SCREAMING_SNAKE_CASE` (`TENANT_MISMATCH`, `INSUFFICIENT_STOCK`).

## Prohibiciones

- Lógica de negocio en componentes de UI.
- Node/Express/Nest en el backend.
- DDL manual en Supabase.
- `service_role` en la API.
- `BYPASSRLS` en el rol de la API.
- Secretos o PII en el repositorio o en logs.
- HTML arbitrario en bloques del builder.
