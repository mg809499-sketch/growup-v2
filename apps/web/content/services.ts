// Servicios MVP de growup.com (solo lo comprometido). Los diferidos viven en /servicios#proximamente.
export type Service = {
  slug: string;
  title: string;
  short: string;
  hero: string;
  description: string;
  includes: string[];
  status: "disponible" | "en-piloto" | "proximamente";
  cta_label: string;
};

export const services: Service[] = [
  {
    slug: "builder",
    title: "Builder de páginas",
    short: "Publica páginas con bloques — sin tocar código.",
    hero: "Diseña tu propia boutique, bloque a bloque.",
    description:
      "El builder de growup te deja componer home, colección y cualquier página con bloques cerrados y validados. Cambia el contenido, previsualiza con token firmado y publica; el storefront purga su caché al instante.",
    includes: [
      "16 bloques MVP (hero, producto, colección, editoriales, FAQ, galería, videos, newsletter…)",
      "Versionado de páginas con rollback en un clic",
      "Previsualización con token firmado antes de publicar",
      "Publish atómico con purga de caché (ISR)",
    ],
    status: "en-piloto",
    cta_label: "Ver builder en el demo",
  },
  {
    slug: "catalogo-inventario",
    title: "Catálogo e inventario",
    short: "Productos, variantes y stock sin overselling.",
    hero: "Tu catálogo, tu stock, tu control.",
    description:
      "Productos con variantes sin límite de opciones, SKU por variante, búsqueda con FTS en español y reserva de inventario atómica para que nunca vendas lo que no tienes.",
    includes: [
      "Variantes ilimitadas, price_cents en enteros y compare-at",
      "Multi-ubicación con reservas confirmadas al pago",
      "Búsqueda full-text en español (nombre + descripción)",
      "Importación lista para cuando lo necesites",
    ],
    status: "disponible",
    cta_label: "Quiero saber más",
  },
  {
    slug: "pagos-wompi",
    title: "Pagos y Wompi",
    short: "Tu cuenta, tus cobros. Nosotros nunca tocamos tarjetas.",
    hero: "Cobras con tu cuenta Wompi. Nosotros solo fluimos.",
    description:
      "El comercio (tú) es el comerciante de registro: conectas tu propia cuenta Wompi y recibes el dinero directo. growup solo orquesta el checkout hosted (cero PAN en nuestros servidores) y la suscripción de la plataforma se cobra aparte por Stripe.",
    includes: [
      "Checkout hosted PCI SAQ A: cero datos de tarjeta en growup",
      "Tu cuenta Wompi cifrada y aislada por tenant",
      "Webhooks firmados e idempotencia de eventos",
      "Confirmación de orden, email y factura automáticos",
    ],
    status: "en-piloto",
    cta_label: "Quiero conectar Wompi",
  },
  {
    slug: "facturacion-dian",
    title: "Facturación DIAN",
    short: "Factura electrónica y nota crédito incluidas.",
    hero: "Vendes; la factura electrónica sale sola.",
    description:
      "Cada venta que pasa a «pagada» emite su factura electrónica por API con un proveedor certificado (Factus). Devoluciones y ajustes generan nota crédito automática contra la factura original.",
    includes: [
      "Factura electrónica cf/01 por orden pagada",
      "Nota crédito nc/02 en refunds completos o parciales",
      "Reintentos con backoff y fallback manual supervisado",
      "CUFE y PDF disponibles en el pedido",
    ],
    status: "en-piloto",
    cta_label: "Quiero saber más",
  },
  {
    slug: "media-cdn",
    title: "Media y CDN",
    short: "Imágenes AVIF/WebP que vuelan, con CDN incluido.",
    hero: "Tus fotos cargan rápido. Siempre.",
    description:
      "Subes la foto original y growup genera las variantes (320–1600px) en AVIF/WebP, elimina EXIF, entrega blurhash y las sirve desde CDN. Tú no optimizas nada.",
    includes: [
      "Pipeline de optimización automática (EXIF, AVIF, WebP)",
      "CDN incluido: carga rápida en todo el país",
      "Alt obligatorio e inventario por producto",
      "Blurhash placeholders",
    ],
    status: "disponible",
    cta_label: "Quiero ver el pipeline",
  },
  {
    slug: "dominios",
    title: "Dominios y TLS",
    short: "tu-tienda.growup.com con HTTPS incluido.",
    hero: "Tu tienda, tu subdominio, tu candado.",
    description:
      "Cada tienda publica en {slug}.growup.com con wildcard TLS automático. Dominios propios (tu-marca.com) llegan en fase 3; ya están en el roadmap con verificación DNS y certificados gestionados.",
    includes: [
      "Subdominio {slug}.growup.com con wildcard TLS",
      "Certificados y renovación automáticos",
      "Dominio propio en fase 3 (Cloudflare for SaaS)",
      "DNS gestionado por growup — cero configuración de tu lado",
    ],
    status: "disponible",
    cta_label: "Quiero mi subdominio",
  },
  {
    slug: "pedidos",
    title: "Pedidos y fulfillment",
    short: "De «pagado» a «entregado» sin papel.",
    hero: "Cada pedido, un flujo claro de la compra a la entrega.",
    description:
      "Panel de pedidos con máquina de estados (preparando, enviada, entregada), evidencia para disputas, reembolso manual asistido y export de pedidos cuando lo necesites.",
    includes: [
      "Máquina de estados con transiciones válidas",
      "Reembolso manual desde Wompi con tracking interno",
      "Plantilla de evidencia para chargebacks",
      "Export CSV para tu contador",
    ],
    status: "disponible",
    cta_label: "Quiero saber más",
  },
  {
    slug: "auditoria-gobernanza",
    title: "Auditoría y gobernanza",
    short: "Cada acción, registrada con cadena de hashes.",
    hero: "Todo lo que pasa en tu cuenta, firmado.",
    description:
      "growup audita sus propias decisiones con decision_logs append-only y cadena SHA-256 por tenant. Tú puedes verificar la integridad de la cadena; nosotros respondemos por ella.",
    includes: [
      "Decision logs append-only con verify_chain",
      "Auditoría consultable desde el admin",
      "Accesos de soporte temporal y consentidos",
      "Registro de aceptaciones (DPA, ToS) por tenant",
    ],
    status: "disponible",
    cta_label: "Quiero ver el ledger",
  },
];

// Diferidos — solo visibilidad honesta, sin CTA.
export const coming_soon: { title: string; note: string }[] = [
  { title: "Marketplace de apps", note: "Decisión D-17 pendiente (no facilitador en MVP)." },
  { title: "Dominios propios", note: "Fase 3 · Cloudflare for SaaS verificación DNS + wildcard gestionado." },
  { title: "Agentes IA en tu tienda", note: "Fuera de alcance del MVP (D-05)." },
];

export function getService(slug: string): Service | undefined {
  return services.find((service) => service.slug === slug);
}
