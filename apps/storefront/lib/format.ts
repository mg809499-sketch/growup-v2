import type { ProductMediaResponse } from "@/lib/api";

export type StorefrontTheme = "ropa" | "joyeria";

export function defaultTheme(): StorefrontTheme {
  return process.env.GROWUP_DEFAULT_THEME === "joyeria" ? "joyeria" : "ropa";
}

export function formatPrice(cents: number): string {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(cents / 100);
}

export function mediaUrl(url: string, r2Key: string): string {
  if (url) {
    return url;
  }

  const base = process.env.NEXT_PUBLIC_MEDIA_BASE_URL?.replace(/\/$/, "");
  return base ? `${base}/${r2Key.replace(/^\//, "")}` : "";
}

export function productImage(
  media: ProductMediaResponse[] | undefined,
): { url: string; alt: string } | null {
  if (!media || media.length === 0) {
    return null;
  }

  const primary = media.find((item) => item.is_primary) ?? media[0];
  const url = mediaUrl(primary.url, primary.r2_key);

  return url ? { url, alt: primary.alt ?? "" } : null;
}
