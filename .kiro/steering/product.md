# Producto

## Qué es

Growup es una plataforma SaaS multi-tenant de comercio electrónico. Un comerciante crea su tienda, elige un tema, edita páginas con un builder de bloques y publica en su dominio. El motor es uno solo: el tenant se resuelve por host y la página se renderiza desde una versión publicada.

## Para quién

- Comerciantes de moda y joyería en Colombia (piloto: ropa y joyería).
- Compradores finales que esperan una experiencia editorial, rápida y móvil.

## Alcance del MVP

Catálogo, variantes, media, carrito, checkout, pagos, órdenes, facturación, builder, publish y subdominios.

## Fuera del MVP (diferido)

Returns/RMA, bespoke, promociones, envío blindado, IA/WhatsApp, L402, multi-moneda y dominios custom. Ver `D-05`.

## Principios

1. **La IA recomienda, las reglas deciden.** Ninguna mutación sensible se aprueba por un modelo.
2. **El tenant es sagrado.** Aislamiento por RLS y validación de host + JWT.
3. **El diseño es el producto.** Dos marcas radicalmente distintas sobre el mismo motor.
4. **Publicar es atómico.** Una versión publicada no se muta; se reemplaza con rollback.
5. **Sin decisiones silenciosas.** Lo que falte se pregunta y se documenta.

## Métricas de éxito del MVP

- Un tenant nuevo publica su home sin redeploy.
- Checkout sin overselling.
- Storefront con LCP móvil < 2.5 s.
- Cero incidentes de fuga entre tenants.
