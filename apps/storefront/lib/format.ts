import {
  formatPrice,
  resolveThemeCssVars,
  resolveThemePreset,
  type ThemePreset,
} from "@growup/config";
import type { BootstrapResponse, ProductMediaResponse } from "@/lib/api";

export type StorefrontTheme = ThemePreset;

export function defaultTheme(): StorefrontTheme {
  return "nova";
}

export function resolveStorefrontTheme(
  bootstrap?: Pick<BootstrapResponse, "tenant" | "theme"> | null,
): StorefrontTheme {
  if (!bootstrap) {
    return "nova";
  }
  return resolveThemePreset(bootstrap.theme ?? null, bootstrap.tenant?.slug ?? null);
}

export function resolveStorefrontStyle(
  bootstrap?: Pick<BootstrapResponse, "tenant" | "theme"> | null,
): Record<string, string> {
  if (!bootstrap) {
    return resolveThemeCssVars(null, null);
  }
  return resolveThemeCssVars(bootstrap.theme ?? null, bootstrap.tenant?.slug ?? null);
}

export { formatPrice };

export function mediaUrl(url: string, r2Key: string): string {
  if (url) {
    return url;
  }

  const base = process.env.NEXT_PUBLIC_MEDIA_BASE_URL?.replace(/\/$/, "");
  return base ? `${base}/${r2Key.replace(/^\//, "")}` : "";
}

export function productImage(
  media: ProductMediaResponse[] | undefined,
): { mediaAssetId: string; url: string; alt: string } | null {
  if (!media || media.length === 0) {
    return null;
  }

  const prioritized = [...media].sort(
    (left, right) => Number(right.is_primary) - Number(left.is_primary),
  );
  for (const item of prioritized) {
    const url = mediaUrl(item.url, item.r2_key);
    if (url) {
      return {
        mediaAssetId: item.media_asset_id,
        url,
        alt: item.alt ?? "",
      };
    }
  }
  return null;
}
