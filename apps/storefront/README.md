# apps/storefront

Storefront único del SaaS. Resuelve el tenant por host y renderiza catálogo
desde la API FastAPI. El builder/publishing y el diseño final llegan con el
export de v0; esta primera base usa la dirección visual de
[`docs/prompts/v0-storefront.md`](../../docs/prompts/v0-storefront.md).

## Estado

- Home, colección, detalle de producto, carrito y retorno de checkout con datos reales de la API.
- Temas dinámicos por tenant resueltos desde `bootstrap.theme` (`nova` sistema técnico total por defecto en ADR-0020; presets `ropa` y `joyeria` disponibles para reversión inmediata).
- Sin login (el storefront es público).

## Ejecutar

```bash
cp apps/storefront/.env.example apps/storefront/.env.local
pnpm install
pnpm --filter @growup/storefront dev
```

La API debe estar en `GROWUP_API_URL` y el host configurado en
`GROWUP_STOREFRONT_HOST` debe existir en `app.domains`.

## Criterios

- Next.js 16 App Router + TypeScript estricto + Tailwind CSS 4.
- `next/image` y `next/font`; sin librerías de UI.
- El tenant se resuelve por host; no se usa `NEXT_PUBLIC_TENANT_ID`.
- WCAG 2.2 AA y `pnpm build` en verde.
