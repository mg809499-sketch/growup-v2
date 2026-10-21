# apps/storefront

Storefront único del SaaS. Renderiza la versión publicada de cada página según el tenant resuelto por host.

## Estado

Pendiente: aquí se integrará el export de v0 descrito en [`docs/prompts/v0-storefront.md`](../../docs/prompts/v0-storefront.md).

## Criterios de integración

- Next.js 16 App Router + TypeScript estricto + Tailwind CSS 4.
- Tokens de tema en CSS variables; dos presets (`ropa`, `joyeria`).
- `BlockRenderer` con discriminated unions y schema cerrado.
- Sin llamadas directas a Supabase; todo pasa por FastAPI.
- Sin `NEXT_PUBLIC_TENANT_ID`: el tenant se resuelve por host.
- `next/image` con `sizes` y `priority` solo en el hero.
- WCAG 2.2 AA y `npm run build` en verde.
