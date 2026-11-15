# Plan FINAL — Suite pública Growup (growup.com) con dirección v0

Fecha: 2026-11-10 · Basado en el paquete de ejecución y decisiones de marca/contenido ratificadas en sesión con el usuario (2026-11-10). Reemplaza `suite-publica-growup.md` como especificación de ejecución para la fase "Suite pública".

**Decisiones cerradas (acta de esta sesión):**

| ID | Decisión | Valor ratificado |
|---|---|---|
| DEC-1 | Nombre | **Growup** (nunca "GrowUp Space" en materiales nuevos) |
| DEC-2 | Identidad visual | **Reabierta y actualizada (2026-11-15, DU-01 / DU-06, ADR-0020):** se adopta la dirección **Nova (Sistema Técnico Total)** en toda la plataforma (`apps/web`, `apps/admin` y preset `nova` en `apps/storefront`): tipografía `Unbounded` (display), `Geist` (cuerpo) y `Geist Mono` (datos/telemetría), superficies oscuras en `oklch()` con soporte `light-dark()` y acento volt `#b8ff3b` / `oklch(0.88 0.19 128)`. Los presets editoriales v0 (`ropa` y `joyeria`) se conservan en el motor de temas como reversión inmediata por tenant. |
| DEC-3 | Precios de planes en público | **Ocultos hasta ratificar D-01 derivado.** Solo "Solicitar acceso" / "Hablemos"; nada de números en público |
| DEC-4 | CTA de conversión | **Solicitar acceso manual**: formulario + email + WhatsApp; alta asistida por el equipo (sin self-service hasta onboarding público) |
| DEC-5 | Consolas | **Consola de clientes sí** (`/consola` → link a `admin.growup.com`); **super consola NO pública** (nunca en web pública; vive en `admin.growup.com/platform` con rol interno) |
| DEC-6 | Contenido inicial | Solicitar acceso manual · Testimonios de los dos pilotos (con permiso) · Servicios MVP únicamente · diferidos marcados **«Próximamente»** (agentes IA, dominios propios, marketplace) |
| DEC-7 | Prototipos legados | **Referencia de IA/flujos únicamente.** No se porta código, no se porta identidad visual, no se prometen features diferidas |

## 1. Qué se construye: `apps/web` — growup.com (marketing SaaS)

Nuevo app en el monorepo (Next.js 16 App Router, RSC, Tailwind 4, componentes propios, **sin librerías de UI**):

```text
app/
├─ layout.tsx                # Shell: header público + footer propios (dirección v0)
├─ page.tsx                  # Welcome growup.com
├─ planes/
│  └─ page.tsx               # 2 planes (Starter/Pro) SIN precios + carrusel + modales
├─ servicios/
│  ├─ page.tsx               # Índice de servicios MVP
│  └─ [slug]/page.tsx        # 8 páginas de servicio (SSG)
├─ consola/page.tsx          # "Ya tengo cuenta → admin.growup.com"
├─ solicitar-acceso/page.tsx # Formulario (nombre, email, tienda, tipo de producto, mensaje) + email + WhatsApp
├─ sitemap.ts, robots.ts, manifest.ts, opengraph-image.tsx
└─ not-found.tsx
components/
├─ site-header.tsx, site-footer.tsx
├─ plan-carousel.tsx         # scroll-snap/suave, 3D tilt leve; sin librerías
├─ plan-card.tsx             # tarjeta Starter/Pro: límites + features; sin precio; CTA
├─ modal.tsx                 # primitivo: overlay + Escape + focus trap + retorno de foco + aria-modal
├─ plan-modal.tsx            # detalle de plan seleccionado (límites, capacidades, CTA solicitar acceso)
├─ service-card.tsx, service-hero.tsx, service-faq.tsx
└─ stat-strip.tsx, review-card.tsx
content/
├─ plans.ts                  # definición de planes sin precios públicos (límites reales de D-01 propuesto)
├─ services.ts               # 8 servicios MVP + estados (disponible/próximamente)
└─ testimonials.ts           # 2 pilotos (ropa, joyería) — requiere permiso por escrito de ambos (DEC-6)
```

**Fuente única de planes:** `content/plans.ts` (precios nunca hardcodeados en markup; cuando se ratifiquen, se muestran desde aquí con un flag `show_pricing`).

## 2. Dirección v0 para el marketing (tokens)

- Superficies: `#f4f3ee` (papel) / `#0d0d0d` (tinta) / superficies elevadas `#faf9f4`; acento señal `#ff3b1d` reservado **solo para CTAs**; hairline `#e5e3dc`.
- Tipografía: Anton (display, ALL CAPS), Space Grotesk (cuerpo), Space Mono (labels `[ LABEL ]`), identica al tema `ropa` del storefront → coherencia Web ↔ Producto con **un solo sistema editorial**.
- Ritmo: secciones full-width con hairlines, numeración `[01] [02]…`, textura de papel sutil (CSS puro, sin assets), fotografía de producto de los pilotos con `next/image`.
- Dark mode: no en MVP (el storefront tampoco lo tiene salvo joyería).
- Iconografía: SVG inline propios (sin Material Symbols ni icon-fonts).

## 3. Home (`/`) — contenido sección por sección

1. **Header**: marca growup®, nav: Servicios · Planes · Consola · [Solicitar acceso].
2. **Hero**: eyebrow `[ COMERCIO × EDITORIAL ]`, titular Anton: «La tiendita completa para marcas de ropa y joyería», subtítulo, doble CTA: [Solicitar acceso] (señal) y [Ver planes ↓], imagen editorial (ropa real o joyería), badge de confianza «Piloto ropa + joyería · Q1 2027».
3. **Proof strip**: 2 pilotos con captura real de sus tiendas (curl de producción cuando estén públicas; si no, staging). Logos con permiso (DEC-6).
4. **Diferenciadores [01–04]**: Builder de bloques publicado · Pagos Wompi hosted + suscripción Stripe · Facturación DIAN incluida · Inventario sin oversell.
5. **Cómo funciona** 3 pasos: Solicita → Te creamos la tienda → Publicas y vendes.
6. **Planes destacados** (sin precios): 2 cards compactas + enlace a `/planes`.
7. **Servicios MVP** (8): grid de cards → sub-páginas.
8. **Testimonios** de los pilotos (con permiso, DEC-6).
9. **FAQ** (4–5): precio («Te llamamos con propuesta»), pasarela (Wompi del comerciante; Stripe suscripción de plataforma), factulación DIAN incluida, dominio (subdominio incluido; propio = fase 3), cero custodia de datos de tarjeta.
10. **CTA final** «Solicitar acceso» + contacto directo (email + WhatsApp).
11. **Footer**: marca, © growup, links privacidad/devoluciones (a páginas legales del store o propias), contacto, estado (futuro).

## 4. `/planes` — carrusel + modales (sin precios)

- Toggle **Mensual / Anual** (beneficio anual visible como «2 meses gratis» sin números).
- Dos `plan-card`: **Starter** (hasta 200 productos, 2 admins, 2 GB media, 500 órdenes/mes) · **Pro** (3.000 productos, 10 admins, 25 GB, órdenes ilimitadas, soporte prioritario).
- Click/Enter en card → **`plan-modal`**: detalle completo (límites, qué incluye, para quién es, qué no incluye, roadmap), CTA «Solicitar acceso → /solicitar-acceso».
- Modal accesible: `role="dialog"`, `aria-modal`, focus trap, Escape cierra, click en overlay cierra, retorno de foco al trigger, `prefers-reduced-motion` respeta sin animaciones.
- Sección «¿Necesitas algo distinto? → Hablemos» para planes futuros/enterprise.
- **Nunca** se muestran números; cuando se ratifiquen (D-01), `content/plans.ts` activa `show_pricing=true`.

## 5. Sub-páginas de servicio (`/servicios/[slug]`) — solo MVP

Estáticas (SSG), cada una con: eyebrow `[ SERVICIO ]`, titular Anton, qué es, para quién, qué incluye (lista), captura/mock del producto, estado (Disponible / En piloto / Próximamente), FAQ corta, CTA a `/solicitar-acceso`. Ocho páginas:

| Slug | Servicio | Fuente legada (IA solamente) | Estado honesto |
|---|---|---|---|
| `builder` | Builder de páginas + publish | `store-web-builder.html` | Disponible en piloto |
| `catalogo-inventario` | Catálogo, variantes, stock multi-ubicación | `catalogo-inventario.html` | Disponible |
| `pagos-wompi` | Checkout Wompi hosted (el comercio cobra; cero PAN en Growup) + suscripción Stripe | `pasarelas-pagos-wompi.html`, `...informacion-checkout.html` | En piloto (sandbox) |
| `facturacion-dian` | Factura + nota crédito vía proveedor certificado (Factus) | (sin legado; decisión D-03) | En piloto |
| `media-cdn` | Imágenes optimizadas AVIF/WebP + CDN | (nuevo) | Disponible |
| `dominios` | `{slug}.growup.com` incluido; dominio propio = fase 3 | `dominio-marca-infraestructura.html`, `dominios-cloudflare-edge.html` | Disponible / Próximamente |
| `pedidos` | Órdenes, fulfillment, reembolso manual | `ordenes-bold-gateway.html` | Disponible |
| `auditoria-gobernanza` | Auditoría con hash chain para tu cuenta | (nuevo) | Disponible |

- Índice `/servicios` lista las 8; diferidos (agentes IA, dominios propios, marketplace de apps) como sección **«Próximamente»** sin páginas (una sola tarjeta gris, sin CTA).

## 6. `/consola`

Dos tarjetas grandes:

1. **«Soy comerciante — Entrar a mi tienda»** → botón principal → `https://admin.growup.com` (target `_blank`). Microcopy: «Tu backoffice: catálogo, pedidos, media y auditoría».
2. **«¿Aún no tienes tienda?»** → link a `/solicitar-acceso`.

Nada de super consola; nada de enlaces de platform admin (DEC-5).

## 7. `/solicitar-acceso`

Formulario accesible (nombre, email, nombre de la tienda, tipo [ropa/joyería/otro], ciudad, mensaje) → envía a un endpoint simple (a decidir: mailto + WhatsApp deep-link en MVP; o tabla `leads` vía API más adelante). Éxito: página «Te escribimos pronto» con fallback email/WhatsApp visibles. Honeypot anti-spam (sin captcha de terceros). Validación server-side mínima si se hace vía API; si es mailto, validación cliente + aria-describedby.

## 8. Técnico y calidad

- Monorepo: nuevo `apps/web` en `pnpm-workspace.yaml`, scripts `dev/build/lint/typecheck`; `turbo` incluye `web`.
- **Sin librerías de UI**, sin tracking de terceros, `force-static`, `next/font` self-hosted, imágenes `next/image`, tamaños reales.
- SEO: metadata por ruta (title/description), OG `opengraph-image.tsx` por plantilla v0, `sitemap.ts`, `robots.ts` (allow todo salvo `/solicitar-acceso`? no — allow todo), JSON-LD `SoftwareApplication`.
- A11y: AA en header/nav/modales; focus-visible señales; skip-link.
- Lighthouse (staging): Performance ≥ 90, SEO ≥ 90, A11y ≥ 90, Best Practices ≥ 90.
- Verificación: `pnpm build` verde; `axe` sin críticos; navegación teclado del modal; `grep` de precios hardcodeados en el output público → debe devolver 0 hasta ratificar D-01.
- Deploy: proyecto Vercel `growup-web`, dominio `growup.com` apex (ADR-0008); staging en `staging.growup.com` o preview protegido (revisar/decidir con DNS de Cloudflare, D-07).

## 9. Lo que NO se construye (alcance congelado)

- Super consola pública; KPIs internos; directorio de tenants.
- Precios numéricos en público.
- Self-service signup; trial automático sin aprobación. ~~(Revertido parcialmente el 2026-11-11: el alta self-service de comerciantes vive en el admin, ver ADR-0019. El marketing web ya no envía CTAs a /solicitar-acceso sino a /login del admin.)~~
- Agentes IA, marketplace, dominios propios (badges «Próximamente» en el máximo de honestidad: sin CTA).
- Copiar el HTML legado ni su identidad violeta/naranja.

## 10. Entregables y Definition of Done

1. `apps/web` compila, lint/typecheck verdes; `pnpm build` con rutas: `/`, `/planes`, `/servicios`, `/servicios/[8]`, `/consola`, `/solicitar-acceso`, `/sitemap.xml`, `/robots.txt`, `/manifest.webmanifest`.
2. Modal de planes accesible y probado (teclado + lectores de pantalla + móvil).
3. Zero precios en público; cero promesas de diferidos como disponibles (honestidad DEC-6).
4. Lighthouse ≥ 90 en staging; axe sin críticos.
5. `docs/web-app.md` o README del app; `docs/reparto-trabajo.md` actualizado; `docs/plan/` registrado.
6. PR(s) con evidencia (capturas, Lighthouse JSON, axe output).

## 11. Orden de ejecución (para modo implementación)

1. Scaffolding `apps/web` + header/footer/tokens v0 + home skeleton.
2. `/planes` con `plans.ts` + carousel + modal.
3. 8 servicios + índice + «Próximamente».
4. `/consola`, `/solicitar-acceso`, SEO (sitemap/robots/OG/JSON-LD).
5. Pulido: Lighthouse/axe, screenshot review, README, deploy staging.

**Prerequisitos**: que el usuario entregue aprobación escrita de testimonios de los pilotos (DEC-6) o se publica con placeholders de marca cliente ("Tu marca aquí"). Precios: sin números hasta D-01.
