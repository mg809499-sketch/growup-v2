# @growup/web — growup.com (marketing del SaaS)

Suite pública del producto Growup: welcome, planes con carrusel + modales, servicios, consola (link al admin) y solicitud de acceso. **No** es el storefront de los tenants ni el admin; es el sitio de marketing del SaaS.

## Identidad

Dirección v0 (editorial, igual al storefront): Anton (display) · Space Grotesk (cuerpo) · Space Mono (etiquetas), superficies papel `#f4f3ee` / tinta `#0d0d0d`, acento señal solo en CTAs, hairlines. Sin librerías de UI.

## Rutas

| Ruta | Qué es |
|---|---|
| `/` | Welcome: hero Anton, diferenciadores, cómo funciona, planes destacados, servicios, pilotos (placeholders con permiso pendiente), CTA |
| `/planes` | Starter/Pro **sin precios** (hasta ratificar D-01), carrusel + modal accesible (focus trap, Escape, overlay, aria-modal) |
| `/servicios` | Índice de 8 servicios MVP (estado real: disponible / en piloto) |
| `/servicios/[slug]` | 8 sub-páginas SSG con includes, estado, CTA a solicitar-acceso |
| `/consola` | Portal «ya tengo cuenta» → `https://admin.growup.com` |
| `/solicitar-acceso` | Formulario (abre `mailto:` prellenado; sin backend aún) |
| `/solicitar-acceso`, `/sitemap.xml`, `/robots.txt`, `/manifest.webmanifest`, `/opengraph-image` | SEO/OG generados |

## Reglas duras de contenido

- **Cero precios en público** hasta ratificar D-01 derivado (`show_pricing = false` en `content/plans.ts`).
- Servicios diferidos (agentes IA, marketplace apps, dominio propio) aparecen como «Próximamente» **sin CTA** y sin promesa de fecha.
- Testimonios de pilotos: texto genérico hasta tener permiso por escrito de ambos tenants.
- Super consola nunca pública.

## Desarrollo

```bash
pnpm install
pnpm --filter @growup/web dev        # http://localhost:3003
pnpm --filter @growup/web build      # estático, 19 rutas
pnpm --filter @growup/web lint
pnpm --filter @growup/web typecheck
```

## Pendientes antes de publicar

- `show_pricing = true` cuando el equipo ratifique D-01 derivado y contador valide IVA.
- Testimonios reales con permiso por escrito de ropa y joyería.
- Sustituir placeholder `site.contact_email` (`hola@growup.com`) y añadir WhatsApp si el owner define el número.
- Desplegar en proyecto Vercel `growup-web` (apex growup.com) — requiere decisión de dominio (D-07/fase 3 para dominio propio en la tienda; la marketing web vive en apex desde ya).
