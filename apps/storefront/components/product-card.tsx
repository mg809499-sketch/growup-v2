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
    <article className="group glass-card overflow-hidden p-3">
      <Link
        href={`/products/${product.slug}`}
        className="block rounded-xl focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#0d0d0d]"
      >
        <div className="relative aspect-[4/5] w-full overflow-hidden rounded-xl bg-slate-100">
          {image ? (
            <Image
              src={image}
              alt={product.name}
              fill
              sizes="(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw"
              className="object-cover transition-transform duration-[450ms] ease-out group-hover:scale-[1.045] group-focus-within:scale-[1.045]"
            />
          ) : (
            <div className="flex h-full items-center justify-center">
              <span className="label text-[#525866]">[ sin imagen ]</span>
            </div>
          )}
        </div>

        <div className="mt-3 flex items-start justify-between gap-4 border-t border-black/10 pt-3">
          <div>
            {typeof index === "number" ? (
              <p className="label text-[#525866]">
                [{String(index + 1).padStart(2, "0")}]
              </p>
            ) : null}
            <h2 className="mt-1 text-base font-semibold leading-tight text-[#0d0d0d]">
              {product.name}
            </h2>
          </div>
          <Price cents={product.min_price_cents} className="shrink-0 text-sm font-bold text-[#0d0d0d]" />
        </div>
      </Link>
    </article>
  );
}
