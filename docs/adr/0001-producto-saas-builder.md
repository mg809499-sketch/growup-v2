# ADR-0001 — Producto: SaaS multi-tenant con builder

- **Estado:** Aceptada
- **Fecha:** 2026-10-21
- **Decisores:** equipo de producto
- **Relacionado con:** D-05, D-07, ADR-0002

## Contexto

La V1 de `multitiendas` implementó dos tiendas con aplicaciones Next.js separadas (`store-clothing` y `store-jewelry`), cada una con su tenant fijado por variable de entorno. El documento de arquitectura V2 describe un producto distinto: un motor de storefront que renderiza layouts JSONB por tenant, con un builder drag-and-drop para comerciantes y capacidad de servir N tiendas.

Mantener dos aplicaciones no escala a N comerciantes y duplica el mantenimiento del storefront, el diseño y el checkout.

## Decisión

Construir un SaaS multi-tenant con:

- **Un solo storefront** (`apps/storefront`) que resuelve el tenant por host y renderiza la versión publicada de cada página.
- **Un admin** (`apps/admin`) con builder, catálogo, pedidos y ajustes.
- **Ropa y joyería como tenants piloto**, no como aplicaciones separadas. Sus identidades visuales se implementan como theme presets y bloques, no como forks de código.

## Alternativas consideradas

| Alternativa | Pros | Contras | ¿Por qué no? |
|---|---|---|---|
| A. Dos apps por vertical (V1) | Aislamiento simple, despliegues independientes | Duplica código, no escala a N tenants | El objetivo es un SaaS, no dos tiendas |
| B. Una app por tenant generada en build | Aislamiento máximo | Costo operativo y de onboarding altísimo | Inviable para N comerciantes |
| C. Storefront único + builder (elegida) | Escala, consistencia, onboarding repetible | Mayor complejidad inicial (versiones, publish, caché) | Es el producto que describe la V2 |

## Consecuencias

### Positivas

- Un solo código de storefront y un solo pipeline de diseño.
- Onboarding de un comerciante nuevo sin despliegue de código.
- El builder y el block registry se convierten en la ventaja competitiva.

### Negativas / deuda asumida

- Hay que construir versionado de páginas, preview, publish atómico, invalidación de caché y dominios.
- El alcance del MVP es mayor que el de la V1.
- Los dos storefronts existentes se fusionan; parte de su CSS por tenant se convierte en tokens.

### Neutras

- El admin deja de ser un backoffice mínimo y pasa a ser una pieza central del producto.

## Cómo se verifica

- Un tenant nuevo se crea y publica su home sin tocar código ni redeploy.
- La misma data de bloques produce dos marcas visualmente distintas.
- El rollback de una página publicada funciona sin pérdida de datos.

## Enlaces

- [Documento de arquitectura V2](../arquitectura-plataforma-inteligente-cordiasolve-v2.md)
- [Decisiones D-05 y D-07](../decisiones-pendientes.md)
