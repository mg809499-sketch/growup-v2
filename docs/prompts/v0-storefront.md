# Prompt v0 — Storefront multi-tenant (prototipo visual)

> **Versión:** 1.0 · Octubre 2026
> **Destino:** v0 (Vercel) → luego se integra en `apps/storefront` del monorepo `growup`.
> **Stack del prototipo:** Next.js 16 App Router + TypeScript + Tailwind CSS + `next/font` + `next/image`.
> **Marcas de referencia:** Sol de Calle / Estudio 04 (ropa) y Aurélia Atelier (joyería).
> **Importante:** este prototipo usa mocks. No consume FastAPI, no tiene auth ni pagos reales. Su objetivo es fijar la dirección visual y producir componentes reutilizables para el block registry.

---

## Cómo usarlo

1. Abre un proyecto nuevo en [v0](https://v0.dev) y pega **todo el bloque de abajo** (desde `Actúa como...` hasta el final).
2. Si v0 trunca la respuesta, pide las iteraciones en este orden:
   - Iteración 1: shell, tokens de los dos temas y home de ambas marcas.
   - Iteración 2: `/coleccion`, `/pdp/[slug]`, carrito y checkout.
   - Iteración 3: README, accesibilidad y pulido responsive.
3. Al terminar, exporta el proyecto y guárdalo como base de `apps/storefront`.

---

```text
Actúa como un equipo senior de diseño e ingeniería frontend especializado en e-commerce editorial de lujo y streetwear.

OBJETIVO
Construye un prototipo frontend completo en Next.js 16 (App Router) + TypeScript + Tailwind CSS de un "storefront engine" multi-tenant para una plataforma SaaS. En este prototipo NO hay backend: todos los datos vienen de mocks tipados. El mismo motor debe renderizar dos marcas con identidades visuales radicalmente distintas, seleccionables con un switcher de tenant.

MARCAS
- Tenant "ropa": Sol de Calle / Estudio 04. Streetwear editorial latinoamericano, brutalismo impreso, off-white, negro y rojo bermellón.
- Tenant "joyeria": Aurélia Atelier. Alta joyería, quiet luxury, obsidiana, oro champán, serif editorial.

STACK OBLIGATORIO
- Next.js 16 App Router, React 19, TypeScript estricto.
- Tailwind CSS v4. Define los tokens como CSS variables en app/globals.css y úsalos en las clases.
- next/font/google: Anton, Space Grotesk, Space Mono, Playfair Display, Plus Jakarta Sans.
- next/image para todas las imágenes.
- Sin librerías de UI: prohibido shadcn, MUI, Chakra, Radix Themes o similares. Componentes propios.
- Iconos: lucide-react solo si es imprescindible, trazo 1.5px.
- Sin backend, sin fetch real, sin auth. Datos en lib/mock.ts.
- Prohibido `any`.

ESTRUCTURA DE ARCHIVOS
app/
  layout.tsx
  page.tsx                  # home; lee ?tenant=ropa|joyeria (searchParams es Promise en Next 15/16)
  coleccion/page.tsx
  pdp/[slug]/page.tsx
  carrito/page.tsx
  checkout/page.tsx
  globals.css
components/
  layout/Header.tsx
  layout/Footer.tsx
  layout/TenantSwitcher.tsx
  layout/MobileMenu.tsx
  blocks/BlockRenderer.tsx
  blocks/Hero.tsx
  blocks/Marquee.tsx
  blocks/ProductGrid.tsx
  blocks/CategoryGrid.tsx
  blocks/EditorialSplit.tsx
  blocks/Spotlight.tsx
  blocks/SpecsBand.tsx
  blocks/Provenance.tsx
  blocks/TrustStrip.tsx
  blocks/Faq.tsx
  blocks/CtaBand.tsx
  commerce/ProductCard.tsx
  commerce/VariantSelector.tsx
  commerce/AddToCart.tsx
  commerce/QuantityStepper.tsx
  commerce/CartLine.tsx
  commerce/CartSummary.tsx
  commerce/CheckoutForm.tsx
  ui/Button.tsx
  ui/Tag.tsx
  ui/Field.tsx
  ui/SectionLabel.tsx
  ui/Price.tsx
lib/
  themes.ts
  mock.ts
  blocks.ts
  format.ts
  cart.tsx
public/products/
README.md

MODELO DE DATOS (tipos en lib/blocks.ts y lib/mock.ts)
- ThemeTokens { id: 'ropa' | 'joyeria'; name: string; colors: Record<string,string>; fonts: {...}; radius: 0; motion: {...} }
- Block = HeroBlock | MarqueeBlock | ProductGridBlock | CategoryGridBlock | EditorialBlock | SpotlightBlock | SpecsBlock | ProvenanceBlock | TrustBlock | FaqBlock | CtaBlock. Cada uno con `type` literal y props.
- PageLayout { tenantId: 'ropa' | 'joyeria'; slug: string; blocks: Block[] }
- Product { id, slug, name, subtitle, priceCents, compareAtCents?, currency: 'COP', images: string[], category, variants: Variant[], specs: {label,value}[], badge?, isOneOfOne? }
- Variant { id, size?, color?, sku, stock }
- JewelrySpec { karat, weightGrams, gem, serial, certificate }
BlockRenderer recibe blocks[] y renderiza cada tipo con el tema activo. Los dos tenants comparten los mismos tipos de bloque; solo cambia el estilo y el contenido.

TEMA 1 — ROPA (data-theme="ropa")
Paleta:
--surface: #F4F3EE; --surface-2: #FAF9F4; --ink: #0D0D0D; --signal: #FF3B1D; --cement: #8C887B; --hairline: #E5E3DC.
Tipografía:
- Display: Anton, siempre UPPERCASE, tracking -0.03em, line-height 0.86. H1 112px desktop / 56px mobile.
- Body: Space Grotesk 15-18px, line-height 1.45.
- Labels: Space Mono 10-12px, uppercase, tracking 0.08-0.12em.
Reglas:
- border-radius: 0 en TODO.
- box-shadow: none. Única excepción: hover del CTA primario con `4px 4px 0 0 #0D0D0D`.
- Bordes de 1px #0D0D0D o #E5E3DC como estructura, nunca cards flotantes.
- Grid asimétrico de 12 columnas; márgenes 40px desktop / 16px mobile; gutters 24px.
- Titulares que sangran el viewport y palabras gigantes recortadas.
- Cero gradientes, cero glassmorphism, cero emojis.
- Etiquetas técnicas: `[01/04]`, `LOTE_24`, `450 GSM`, `CDMX / BOG / SP`.
Componentes:
- Botón primario negro con texto off-white, uppercase, tracking 0.05em, sin radius; hover rojo.
- Botón ghost con borde 1px.
- Chips rectangulares con borde 1px y Space Mono.
- Cards sin sombra: imagen 4:5 edge-to-edge + metadata strip con índice, nombre y precio.
- Marquee infinito alternando negro/rojo; pausa en hover y con prefers-reduced-motion.
Home, en este orden:
1. Header fijo: logo "SOL DE CALLE", nav (DROP, COLECCIÓN, ARCHIVO, TALLAS), carrito con contador, menú mobile full-screen.
2. Hero asimétrico: 7 columnas imagen editorial, 5 columnas titular gigante "SOL DE CALLE" + subtítulo "EDITORIAL STREETWEAR / BOGOTÁ" + CTA "[ VER DROP 04 ]" + telemetría técnica.
3. Marquee: "ESTUDIO 04 /// HECHO EN LATINOAMÉRICA /// CDMX · BOGOTÁ · SÃO PAULO".
4. ProductGrid "DROP 04" con 6 productos; scroll horizontal en desktop y grid 2-col en mobile. Cada card con índice, nombre, precio COP y badge AGOTADO si stock 0.
5. CategoryGrid de 3 celdas: DENIM / TEES / ABRIGOS, con imagen y hover de inversión.
6. EditorialSplit: imagen full-bleed + manifiesto "NO HACEMOS ROPA. HACEMOS UNIFORMES PARA LA CALLE." + 3 specs (450 GSM, 100% algodón, tinte reactivo).
7. SpecsBand con barcode SVG, tabla de tallas y cuidados.
8. Faq acordeón: envíos, cambios 30 días, guía de tallas.
9. CtaBand "ÚNETE AL ARCHIVO" con input de email.
10. Footer con columnas, coordenadas, barcode y copyright.

TEMA 2 — JOYERÍA (data-theme="joyeria")
Paleta:
--surface: #0B0B0C; --surface-1: #141416; --surface-2: #1E1E22; --ivory: #F5F4F0; --gold: #D4AF37; --gold-soft: #E5C378; --taupe: #9E9B93; --hairline: #26262B.
Tipografía:
- Display: Playfair Display, nunca uppercase, tracking -0.02em, 48-64px desktop / 28-36px mobile.
- Body: Plus Jakarta Sans 300, 14-16px, line-height 1.6.
- Labels: Plus Jakarta Sans 9-12px, uppercase, tracking 0.18-0.25em, color taupe.
Reglas:
- border-radius: 0.
- Sin cards: la imagen vive directo sobre el fondo; separación por espacio vertical y hairlines de 1px #26262B.
- Mucho aire: 5-7rem de padding vertical entre secciones.
- Sin sombras; profundidad por capas tonales y hairlines. Modal con rgba(11,11,12,.88) + backdrop blur 16px.
- Sin badges comerciales agresivos; el lujo se comunica en microtipografía.
- Imágenes macro, chiaroscuro, fondo negro.
Componentes:
- CTA primario marfil con texto obsidiana; hover dorado.
- CTA secundario transparente con borde hairline; hover borde dorado.
- Chips rectangulares con borde hairline; seleccionado con borde dorado.
- Especificaciones en dos columnas: descriptor taupe a la izquierda, valor marfil a la derecha, separadas por hairline.
- Acordeón de proveniencia con + / — de 1px.
Home, en este orden:
1. Header transparente sobre hero: logo "AURÉLIA" en serif, nav (COLECCIÓN, ATELIER, CERTIFICADOS, CONTACTO), carrito, menú mobile.
2. Hero full-bleed: macro de anillo o diamante, overlay mínimo, titular "Aurélia" + "Alta joyería · Piezas únicas" + CTA "Descubrir la colección" + link "Agendar una cita privada".
3. Spotlight de una pieza 1 de 1: imagen 3:4, nombre serif, ficha (Oro 18k, 4.2 g, Diamante talla brillante, Serie AU-001), CTA "Reservar pieza" + "Solicitar dossier".
4. CraftsmanshipBand: 3 pasos (selección de gemas, engaste a mano, certificación GIA) con números romanos y hairlines.
5. TrustStrip: GIA / Envío blindado asegurado / Pedidos a medida / Devolución 30 días.
6. Provenance accordion: certificado, trazabilidad, cuidados.
7. Colección editorial: 4 piezas en grid asimétrico, sin cards, con nombre serif y precio discreto.
8. CtaBand "Una pieza. Una historia." + botón "Agendar cita en el atelier".
9. Footer con dirección Bogotá/París, horarios, newsletter y legal.

PÁGINAS INTERNAS (ambas marcas)
- /coleccion: grid filtrable por categoría/talla/material (chips rectangulares), contador de resultados y orden por precio. En joyería, filtros por metal, gema y talla.
- /pdp/[slug]: galería (1 imagen grande + thumbnails), título, precio COP, selector de variante (talla/color en ropa; metal/talla en joyería), stock, CTA agregar, ficha técnica, acordeón de envío/cambios y piezas relacionadas.
- /carrito: líneas con imagen, variante, cantidad, subtotal, resumen, CTA a checkout y estado vacío editorial.
- /checkout: formulario de 1 paso (contacto, envío, pago simulado), resumen fijo, validación básica y botón "Confirmar pedido" que muestra estado de éxito. Sin integración real.
- Carrito persistente en localStorage con Context. Contador en header. AddToCart con feedback visual.

INTERACCIONES
- TenantSwitcher fijo abajo a la derecha, visible solo en desarrollo, con "ROPA / JOYERÍA". Cambia tema, copy y productos vía ?tenant=.
- Header sticky; menú mobile full-screen.
- Marquee pausa en hover y respeta prefers-reduced-motion.
- Focus visible: outline 2px solid (rojo en ropa, dorado en joyería), offset 2px.
- Transiciones de 100-150ms; sin animaciones decorativas largas.
- Hover states claros en links, botones y cards.

ACCESIBILIDAD Y RENDIMIENTO
- HTML semántico, landmarks, alt descriptivo y labels asociados.
- Contraste AA en ambos temas.
- Navegación completa por teclado; menú y carrito cierran con Escape.
- Imágenes con width/height o fill + sizes; hero con priority.
- Sin layout shift; fuentes con display swap.
- `npm run build` debe pasar sin errores de TypeScript.

CONTENIDO
- Todo el copy en español de Colombia, real y específico, sin lorem ipsum.
- Precios en COP con Intl.NumberFormat('es-CO').
- Ropa: 6 productos (jean recto, oversize tee, hoodie 450gsm, chaqueta cargo, cargo pant, cap) con nombres como "JEAN RECTO 04", "TEE BLANK 02", "HOODIE 450".
- Joyería: 4 piezas (anillo solitario, cadena veneciana, aretes ópera, brazalete) con nombres como "Solitario Aurélia", "Cadena Venezia", "Aretes Ópera", "Brazalete Lune" y fichas técnicas realistas.
- Imágenes: usa imágenes editoriales de Unsplash con URLs directas y estables. Si alguna falla, muestra un bloque de superficie con la etiqueta técnica; nunca un placeholder gris genérico.

PROHIBIDO
- border-radius distinto de 0.
- box-shadow suave, gradientes, glassmorphism, neumorfismo.
- Cards flotantes con sombra.
- Estilo "SaaS dashboard" (azul/morado, pills, sombras).
- Emojis.
- Lorem ipsum.
- Dependencias de UI externas.
- Animaciones que no aporten.

ENTREGABLE
1. Proyecto Next.js completo y ejecutable.
2. README con estructura, cómo cambiar de tenant y dónde reemplazar los mocks por la API real (endpoints futuros: /storefront/resolve, /catalog, /cart, /checkout).
3. lib/blocks.ts como base del block registry que luego replicará el backend.
4. La misma data, dos marcas completamente distintas.
```

---

## Checklist al recibir el prototipo

- [ ] La home de ropa y la de joyería comparten tipos de bloque pero se ven como marcas distintas.
- [ ] `border-radius: 0` y ausencia de sombras suaves en ambas.
- [ ] El switcher `?tenant=` cambia tema, copy y productos.
- [ ] `/pdp/[slug]` funciona en las dos marcas, con variantes y stock.
- [ ] El carrito persiste al recargar y el contador del header se actualiza.
- [ ] `/checkout` valida y muestra estado de éxito simulado.
- [ ] Responsive correcto a 390 px y 1440 px.
- [ ] Navegación por teclado y foco visible.
- [ ] `npm run build` pasa sin errores de TypeScript.
- [ ] `lib/blocks.ts` es reusable como contrato del block registry del backend.

## Notas de integración

- v0 puede devolver Next 15 + Tailwind 3. Al portar a `growup` se alinea a Next 16 + Tailwind 4; no se reescribe el diseño.
- Los mocks deben mapear 1:1 a los futuros endpoints de FastAPI:
  - `GET /api/v1/storefront/resolve?host=` → tenant + theme + página publicada.
  - `GET /api/v1/catalog/products` → productos y variantes.
  - `POST /api/v1/cart/items` → carrito.
  - `POST /api/v1/checkout` → orden.
- Las imágenes definitivas vivirán en R2 con URLs firmadas; las de Unsplash son solo para el prototipo.
