// @growup/config — utilidades y constantes compartidas del monorepo.
// Dinero SIEMPRE en centavos enteros COP.

export const COP_CURRENCY = "COP";
export const SUPPORT_EMAIL = "soporte@growup.com";
export const LEGAL_REVIEW_BANNER = "El texto legal está en revisión.";

export const DEFAULT_SHIPPING_ZONES = [
  { code: "bogota", name: "Bogotá D.C.", price_cents: 800_000 },
  { code: "resto", name: "Resto del país", price_cents: 1_500_000 },
] as const;

export function formatPrice(cents: number): string {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: COP_CURRENCY,
    maximumFractionDigits: 0,
  }).format(cents / 100);
}

export function formatDate(value: string | null): string {
  if (!value) {
    return "—";
  }
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
