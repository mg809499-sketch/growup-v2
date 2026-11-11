import { formatPrice } from "@growup/config";
import type { ProductMediaResponse } from "@/lib/api";

export type StorefrontTheme = "ropa" | "joyeria";

export function defaultTheme(): StorefrontTheme {
  return process.env.GROWUP_DEFAULT_THEME === "joyeria" ? "joyeria" : "ropa";
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
