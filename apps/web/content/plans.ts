// Fuente única de planes para /planes y la portada.
// REGLA: mientras D-01 derivado (precios) no esté ratificado, precios nunca se muestran
// (show_pricing = false). El modal explica la conversación comercial.

export const show_pricing = false;

export type Plan = {
  id: "starter" | "pro";
  name: string;
  tagline: string;
  best_for: string;
  features: { label: string; value: string }[];
  limits: string[];
  cta: string;
};

export const plans: Plan[] = [
  {
    id: "starter",
    name: "Starter",
    tagline: "Para empezar a vender en serio",
    best_for: "Marcas de ropa y joyería con catálogo acotado.",
    features: [
      { label: "Productos", value: "Hasta 200" },
      { label: "Administradores", value: "2" },
      { label: "Storage de media", value: "2 GB" },
      { label: "Órdenes por mes", value: "500" },
      { label: "Soporte", value: "Email · 8 h hábiles" },
    ],
    limits: [
      "Builder de páginas y publicación incluidos",
      "Catálogo, inventario y checkout Wompi incluidos",
      "Facturación DIAN incluida (proveedor certificado)",
    ],
    cta: "Solicitar acceso",
  },
  {
    id: "pro",
    name: "Pro",
    tagline: "Para marcas que ya factura todo el año",
    best_for: "Catálogos grandes, equipos pequeños y operación continua.",
    features: [
      { label: "Productos", value: "Hasta 3.000" },
      { label: "Administradores", value: "10" },
      { label: "Storage de media", value: "25 GB" },
      { label: "Órdenes por mes", value: "Ilimitadas" },
      { label: "Soporte", value: "Prioritario · 4 h hábiles" },
    ],
    limits: [
      "Todo lo de Starter",
      "Soporte prioritario y onboarding asistido",
      "Facturación DIAN incluida (proveedor certificado)",
    ],
    cta: "Solicitar acceso",
  },
];

export const trial_days = 14;
export const annual_note = "Paga anual y te llevas 2 meses gratis.";
