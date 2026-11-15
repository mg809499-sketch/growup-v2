/**
 * Modo de previsualización de diseño local (NOVA_DESIGN_PREVIEW=1).
 * Provee datos de demostración ricos para las 2 consolas (Staff All-in-One y
 * Cliente Owner) cuando aún no se han configurado llaves de Supabase o API local.
 * Nunca se activa en producción.
 */

export function isDesignPreview(): boolean {
  return (
    process.env.NOVA_DESIGN_PREVIEW === "1" ||
    process.env.NEXT_PUBLIC_NOVA_DESIGN_PREVIEW === "1"
  );
}

export const designPreviewUser = {
  id: "00000000-0000-4000-8000-000000000001",
  email: "operaciones@growup.co",
  aud: "authenticated",
  role: "authenticated",
} as const;

export const designPreviewToken = "design-preview";

export const mockMeResponse = {
  role: "owner",
  tenant_id: "00000000-0000-4000-8000-000000000002",
  permissions: [
    "catalog.read",
    "catalog.write",
    "orders.read",
    "orders.write",
    "content.read",
    "content.write",
    "content.publish",
    "media.write",
    "platform.admin",
    "audit.read",
  ],
  email: designPreviewUser.email,
} as const;

export const mockPlatformOverview = {
  tenants_total: 18,
  tenants_active: 14,
  tenants_trialing: 3,
  tenants_suspended: 1,
  tenants_canceled: 0,
  trials_ending_7d: 2,
  gmv_last_7d_cents: 4_890_000_000,
  gmv_last_30d_cents: 19_450_000_000,
  orders_last_30d: 1_284,
  products_total: 642,
  media_bytes_total: 1_845_493_760,
  media_failed: 0,
  outbox_stuck: 0,
  audit_decisions_last_7d: 318,
  audit_denied_last_7d: 2,
  subscriptions_active: 14,
  computed_at: new Date().toISOString(),
} as const;

export const mockPlatformAlerts = {
  alerts: [
    {
      type: "trial_expiring",
      alert_key: "trial-mitiendadeportiva",
      tenant_id: "00000000-0000-4000-8000-000000000012",
      slug: "mitiendadeportiva",
      name: "Mi Tienda Deportiva",
      message: "Trial vence en 48 horas · 48 SKUs sincronizados y checkout Wompi listo.",
      severity: "warning",
    },
    {
      type: "high_volume",
      alert_key: "spike-sol-de-calle",
      tenant_id: "00000000-0000-4000-8000-000000000010",
      slug: "ropa",
      name: "Sol de Calle",
      message: "Pico de tráfico en Drop 04 · 98.9% aprobación en Wompi PSE/Nequi.",
      severity: "info",
    },
  ],
  count: 2,
} as const;

export const mockPlatformTenants = {
  items: [
    {
      id: "00000000-0000-4000-8000-000000000010",
      slug: "ropa",
      name: "Sol de Calle",
      status: "active",
      host: "ropa.growup.com",
      plan_id: "00000000-0000-4000-8000-000000000102",
      trial_ends_at: null,
      created_at: "2026-10-21T14:00:00.000Z",
    },
    {
      id: "00000000-0000-4000-8000-000000000011",
      slug: "joyeria",
      name: "Aurélia Atelier",
      status: "active",
      host: "joyeria.growup.com",
      plan_id: "00000000-0000-4000-8000-000000000102",
      trial_ends_at: null,
      created_at: "2026-10-24T16:30:00.000Z",
    },
    {
      id: "00000000-0000-4000-8000-000000000012",
      slug: "mitiendadeportiva",
      name: "Mi Tienda Deportiva",
      status: "trialing",
      host: "mitiendadeportiva.growupstore.app",
      plan_id: "00000000-0000-4000-8000-000000000101",
      trial_ends_at: "2026-11-28T23:59:59.000Z",
      created_at: "2026-11-12T09:15:00.000Z",
    },
    {
      id: "00000000-0000-4000-8000-000000000013",
      slug: "estudio-04",
      name: "Estudio 04 · Denim & Archivo",
      status: "active",
      host: "estudio04.growup.com",
      plan_id: "00000000-0000-4000-8000-000000000102",
      trial_ends_at: null,
      created_at: "2026-11-01T11:00:00.000Z",
    },
  ],
  total: 4,
  limit: 20,
  offset: 0,
} as const;

export const mockPlans = [
  {
    id: "00000000-0000-4000-8000-000000000101",
    code: "starter",
    name: "Starter Editorial",
    price_cents: 4_900_000,
    currency: "COP",
    billing_interval: "month",
    trial_days: 14,
    features: [
      "Hasta 200 productos y variantes con stock atómico",
      "Store & Web Builder v3.0 (NOVA + 16 bloques cerrados)",
      "Checkout Express Wompi (PSE, Nequi, Bancolombia, Tarjetas)",
      "2 cuentas de staff y 2 GB en Cloudflare R2 CDN",
      "Subdominio *.growup.com con SSL TLS 1.3",
    ],
    active: true,
    badge: "PILOTO",
    description: "Para marcas emergentes de ropa, deporte y bienestar.",
    sort_order: 10,
    list_price_cop_cents: 4_900_000,
    list_price_usd_cents: 1_500,
  },
  {
    id: "00000000-0000-4000-8000-000000000102",
    code: "pro",
    name: "Pro Multi-Canal & IA",
    price_cents: 12_900_000,
    currency: "COP",
    billing_interval: "month",
    trial_days: 14,
    features: [
      "Hasta 3.000 SKUs, multi-bodega y alertas de reorden con IA",
      "Store Builder v3.0 + Mapeo WooCommerce / ACF + Snippets Tailwind",
      "Agente OpenCode IA 24/7 en WhatsApp Business con links Wompi",
      "Facturación electrónica DIAN automática + Red Aliada B2B",
      "10 cuentas de staff, 25 GB Media CDN y soporte prioritario",
    ],
    active: true,
    badge: "MÁS ELEGIDO",
    description: "Escala comercial con automatización OpenCode IA y alto tráfico.",
    sort_order: 20,
    list_price_cop_cents: 12_900_000,
    list_price_usd_cents: 3_500,
  },
  {
    id: "00000000-0000-4000-8000-000000000103",
    code: "enterprise",
    name: "Enterprise Pod Dedicado",
    price_cents: 49_000_000,
    currency: "COP",
    billing_interval: "month",
    trial_days: 30,
    features: [
      "SKUs y órdenes ilimitadas en celda dedicada sa-east-1",
      "Dominio custom en Cloudflare Enterprise (300+ PoPs)",
      "Agentes IA dedicados + Webhooks firmados de alta frecuencia",
      "Auditoría inmutable SOC 2-ready y gerente de cuenta",
    ],
    active: true,
    badge: "ALL-IN-ONE",
    description: "Infraestructura aislada para marcas de alto volumen y drops.",
    sort_order: 30,
    list_price_cop_cents: 49_000_000,
    list_price_usd_cents: 12_500,
  },
] as const;

export const mockBuilderPages = {
  items: [
    {
      id: "00000000-0000-4000-8000-000000000201",
      slug: "home",
      title: "Home · Colección Deportiva Alto Rendimiento",
      status: "published",
      published_version_id: "00000000-0000-4000-8000-000000000301",
      updated_at: "2026-11-15T09:30:00.000Z",
      latest_version: 4,
    },
    {
      id: "00000000-0000-4000-8000-000000000202",
      slug: "drop-04",
      title: "Landing Drop 04 · Sol de Calle",
      status: "draft",
      published_version_id: null,
      updated_at: "2026-11-15T10:00:00.000Z",
      latest_version: 2,
    },
  ],
  total: 2,
  limit: 100,
  offset: 0,
} as const;

export const mockBuilderDraft = {
  id: "00000000-0000-4000-8000-000000000301",
  version: 4,
  layout: {
    version: 1,
    blocks: [
      {
        id: "header-1",
        type: "header",
        brand: "MI TIENDA DEPORTIVA",
        nav: [
          { label: "Colección 2025", href: "/collection" },
          { label: "Alto Rendimiento", href: "/collection?cat=pro" },
          { label: "Ofertas", href: "/collection?cat=sale" },
        ],
        cta: { label: "Comprar con Wompi", href: "/carrito" },
      },
      {
        id: "hero-mascota-promo",
        type: "hero",
        eyebrow: "COLECCIÓN OFICIAL 2025 · ENVÍO GRATIS NACIONAL (CÓDIGO: GROWUP2025)",
        title: "COLECCIÓN DEPORTIVA DE ALTO RENDIMIENTO",
        subtitle: "$189.900 COP (Antes $249.900 COP · Ahorras 24%) · 14 unidades disponibles en tallas S, M, L, XL.",
        align: "left",
        cta: { label: "Comprar Ahora con Wompi", href: "/collection" },
      },
      {
        id: "grid-woo",
        type: "product_grid",
        title: "Vitrina Sincronizada WooCommerce (48 SKUs OK)",
        source: "latest",
        category_slug: "",
        limit: 8,
        show_price: true,
      },
      {
        id: "footer-1",
        type: "footer",
        columns: [
          {
            title: "Tienda",
            links: [
              { label: "Catálogo oficial", href: "/collection" },
              { label: "Rastreo de guías", href: "/orders" },
            ],
          },
        ],
        legal_line: "© 2026 Mi Tienda Deportiva · Facturación Electrónica DIAN Habilitada · SSL TLS 1.3",
      },
    ],
  },
} as const;

export const mockProducts = {
  items: [
    {
      id: "00000000-0000-4000-8000-000000000401",
      slug: "chaqueta-valkyrie-pro",
      name: "Chaqueta Deportiva Valkyrie Pro 450GSM",
      status: "active",
      brand: "Mi Tienda Deportiva",
      category_id: null,
      min_price_cents: 18_990_000,
      max_price_cents: 18_990_000,
      variant_count: 4,
      stock_total: 42,
      primary_image_key: null,
      updated_at: "2026-11-15T08:00:00.000Z",
    },
    {
      id: "00000000-0000-4000-8000-000000000402",
      slug: "jean-recto-archivo-04",
      name: "Jean Recto Archivo 04 · Raw Denim",
      status: "active",
      brand: "Sol de Calle",
      category_id: null,
      min_price_cents: 22_900_000,
      max_price_cents: 22_900_000,
      variant_count: 4,
      stock_total: 18,
      primary_image_key: null,
      updated_at: "2026-11-14T19:20:00.000Z",
    },
    {
      id: "00000000-0000-4000-8000-000000000403",
      slug: "aretes-arabesque-kyanite",
      name: "Aretes Arabesque Oro 18k & Kyanita",
      status: "active",
      brand: "Aurélia Atelier",
      category_id: null,
      min_price_cents: 49_000_000,
      max_price_cents: 49_000_000,
      variant_count: 1,
      stock_total: 3,
      primary_image_key: null,
      updated_at: "2026-11-14T15:10:00.000Z",
    },
    {
      id: "00000000-0000-4000-8000-000000000404",
      slug: "cortavientos-reflex-pro",
      name: "Cortavientos Ultraligero Reflex Pro",
      status: "active",
      brand: "Mi Tienda Deportiva",
      category_id: null,
      min_price_cents: 21_000_000,
      max_price_cents: 21_000_000,
      variant_count: 3,
      stock_total: 4,
      primary_image_key: null,
      updated_at: "2026-11-15T07:45:00.000Z",
    },
  ],
  total: 4,
  limit: 20,
  offset: 0,
} as const;

export const mockOrders = {
  items: [
    {
      id: "00000000-0000-4000-8000-000000000501",
      email: "camila.restrepo@gmail.com",
      status: "paid",
      subtotal_cents: 18_990_000,
      tax_cents: 3_032_000,
      shipping_cents: 800_000,
      total_cents: 19_790_000,
      shipping_zone: "bogota",
      created_at: "2026-11-15T09:42:00.000Z",
      updated_at: "2026-11-15T09:43:00.000Z",
    },
    {
      id: "00000000-0000-4000-8000-000000000502",
      email: "mateo.lopez@outlook.com",
      status: "preparing",
      subtotal_cents: 45_800_000,
      tax_cents: 7_312_000,
      shipping_cents: 1_500_000,
      total_cents: 47_300_000,
      shipping_zone: "resto",
      created_at: "2026-11-15T08:15:00.000Z",
      updated_at: "2026-11-15T08:30:00.000Z",
    },
    {
      id: "00000000-0000-4000-8000-000000000503",
      email: "valeria.gomez@empresa.co",
      status: "shipped",
      subtotal_cents: 49_000_000,
      tax_cents: 7_823_500,
      shipping_cents: 0,
      total_cents: 49_000_000,
      shipping_zone: "bogota",
      created_at: "2026-11-14T17:10:00.000Z",
      updated_at: "2026-11-14T19:00:00.000Z",
    },
    {
      id: "00000000-0000-4000-8000-000000000504",
      email: "andres.pardo@gmail.com",
      status: "delivered",
      subtotal_cents: 13_600_000,
      tax_cents: 2_171_400,
      shipping_cents: 800_000,
      total_cents: 14_400_000,
      shipping_zone: "bogota",
      created_at: "2026-11-13T12:05:00.000Z",
      updated_at: "2026-11-14T10:20:00.000Z",
    },
  ],
  total: 4,
  limit: 20,
  offset: 0,
} as const;
