import Image from "next/image";
import Link from "next/link";

import type { ProductSummaryResponse } from "@/lib/api";
import { mediaUrl } from "@/lib/format";
import { Price } from "@/components/price";

export function ProductCard({
  product,
  index,
}: {
  product: ProductSummaryResponse;
  index?: number;
}) {
  const image = product.primary_image_key
    ? mediaUrl("", product.primary_image_key)
    : "";

  return (
    <article className="group">
      <Link
        href={`/products/${product.slug}`}
        className="block focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--signal)]"
      >
        <div className="relative aspect-[4/5] w-full overflow-hidden bg-[var(--surface-2)]">
          {image ? (
            <Image
              src={image}
              alt={product.name}
              fill
              sizes="(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw"
              className="object-cover transition-transform duration-500 group-hover:scale-[1.02]"
            />
          ) : (
            <div className="flex h-full items-center justify-center">
              <span className="label text-[var(--muted)]">[ sin imagen ]</span>
            </div>
          )}
        </div>

        <div className="flex items-start justify-between gap-4 border-t border-[var(--hairline)] pt-3">
          <div>
            {typeof index === "number" ? (
              <p className="label text-[var(--muted)]">
                [{String(index + 1).padStart(2, "0")}]
              </p>
            ) : null}
            <h2 className="mt-1 text-base font-medium leading-tight">{product.name}</h2>
          </div>
          <Price cents={product.min_price_cents} className="shrink-0 text-sm" />
        </div>
      </Link>
    </article>
  );
}
