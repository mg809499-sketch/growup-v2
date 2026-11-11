// Contacto comercial y autoridad del sitio.
// TODO(owner): reemplazar con el canal real de ventas (email/WhatsApp destino).
const adminUrl = process.env.NEXT_PUBLIC_ADMIN_URL ?? "http://localhost:3001";

export const site = {
  name: "growup",
  legal_name: "growup · Cordiasolve V2",
  url: "https://growup.com",
  // En produccion (Vercel), definir NEXT_PUBLIC_ADMIN_URL=https://admin.growup.com en build.
  admin_url: adminUrl,
  admin_login_url: `${adminUrl}/login`,
  storefront_example: "https://ropa.growup.com",
  contact_email: "hola@growup.com",
  // Sin WhatsApp público hasta que el owner defina el número destino.
  contact_hours: "Lun–Vie · 8:00–18:00 (Bogotá)",
} as const;
