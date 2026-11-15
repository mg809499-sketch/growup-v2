import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Price } from "@/components/price";
import { SectionLabel } from "@/components/section-label";
import {
  ApiError,
  getBootstrap,
  getProduct,
  getStorefrontHost,
} from "@/lib/api";
import type { ProductDetailResponse } from "@/lib/api";
import { mediaUrl, productImage, formatPrice } from "@/lib/format";
import { addToCartAction } from "@/lib/cart-actions";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const host = await getStorefrontHost();
  let product: ProductDetailResponse;
  let tenantName: string;
  try {
    [product, { tenant: { name: tenantName } }] = await Promise.all([
      getProduct(host, slug),
      getBootstrap(host),
    ]);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      notFound();
    }
    throw error;
  }
  return {
    title: `${product.name} | ${tenantName}`,
    description:
      product.description ??
      `Conoce ${product.name} en la tienda ${tenantName}.`,
  };
}

function variantLabel(optionValues: Record<string, string>): string {
  const entries = Object.entries(optionValues);
  if (entries.length === 0) {
    return "Única";
  }
  return entries.map(([key, value]) => `${key}: ${value}`).join(" · ");
}

export default async function ProductPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const host = await getStorefrontHost();

  let product;
  try {
    product = await getProduct(host, slug);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      notFound();
    }
    throw error;
  }

  const primaryImage = productImage(product.media);
  const media = product.media
    .map((item) => ({
      ...item,
      absoluteUrl: mediaUrl(item.url, item.r2_key),
    }))
    .filter((item) => item.absoluteUrl);

  const main = primaryImage;
  const thumbnails = media
    .filter((item) => item.media_asset_id !== primaryImage?.mediaAssetId)
    .slice(0, 4);
  const hasActiveVariant = product.variants.some(
    (variant) => variant.is_active && variant.stock_available > 0,
  );
  const minimumPriceVariant = product.variants.find(
    (variant) =>
      variant.is_active && variant.price_cents === product.min_price_cents,
  );

  return (
    <main className="mx-auto max-w-[1440px] px-4 pt-8 md:px-10 md:pt-12">
      <nav className="label flex items-center gap-2 text-[var(--muted)]">
        <Link className="hover:text-[var(--ink)]" href="/">
          Inicio
        </Link>
        <span>/</span>
        <Link className="hover:text-[var(--ink)]" href="/collection">
          Colección
        </Link>
        <span>/</span>
        <span className="text-[var(--ink)]">{product.name}</span>
      </nav>

      <div className="mt-6 grid gap-8 border-t border-[var(--hairline)] pt-6 lg:grid-cols-12 lg:gap-10">
        <div className="lg:col-span-7">
          <div className="group relative aspect-[4/5] w-full overflow-hidden bg-[var(--surface-2)]">
            {main ? (
              <Image
                src={main.url}
                alt={main.alt || product.name}
                fill
                priority
                sizes="(min-width: 1024px) 55vw, 100vw"
                className="object-cover transition-transform duration-[450ms] ease-out group-hover:scale-[1.045] motion-reduce:transition-none motion-reduce:transform-none"
              />
            ) : (
              <div className="flex h-full items-center justify-center">
                <span className="label text-[var(--muted)]">[ sin imagen ]</span>
              </div>
            )}
          </div>

          {thumbnails.length > 0 ? (
            <div className="mt-3 grid grid-cols-4 gap-3">
              {thumbnails.map((item) => (
                <div
                  key={item.media_asset_id}
                  className="group relative aspect-square overflow-hidden bg-[var(--surface-2)]"
                >
                  <Image
                    src={item.absoluteUrl}
                    alt={item.alt ?? product.name}
                    fill
                    sizes="15vw"
                    className="object-cover transition-transform duration-[450ms] ease-out group-hover:scale-[1.055] motion-reduce:transition-none motion-reduce:transform-none"
                  />
                </div>
              ))}
            </div>
          ) : null}
        </div>

        <div className="lg:col-span-5 lg:pl-6">
          <SectionLabel>{product.brand ?? "Selección"}</SectionLabel>
          <h1 className="display mt-3 text-[clamp(2.6rem,6vw,4.8rem)] leading-[0.95]">
            {product.name}
          </h1>

          <div className="mt-4 flex items-center gap-4">
            <Price
              cents={product.min_price_cents}
              compareAtCents={minimumPriceVariant?.compare_at_price_cents}
              className="text-lg"
            />
            <span
              className={`label border px-2 py-1 ${
                hasActiveVariant
                  ? "border-[var(--hairline)] text-[var(--muted)]"
                  : "border-[var(--signal)] text-[var(--signal)]"
              }`}
            >
              {hasActiveVariant ? "Disponible" : "Agotado"}
            </span>
          </div>

          {product.description ? (
            <p className="mt-6 whitespace-pre-line text-sm leading-relaxed text-[var(--muted)]">
              {product.description}
            </p>
          ) : null}

          <div className="mt-8 border-t border-[var(--hairline)] pt-5">
            <SectionLabel>Variantes</SectionLabel>
            <ul className="mt-3 divide-y divide-[var(--hairline)] border-y border-[var(--hairline)]">
              {product.variants.map((variant) => (
                <li
                  key={variant.id}
                  className="flex items-center justify-between gap-4 py-3"
                >
                  <div>
                    <p className="text-sm">{variantLabel(variant.option_values)}</p>
                    <p className="label mt-1 text-[var(--muted)]">
                      {variant.sku}
                    </p>
                  </div>
                  <div className="text-right">
                    <Price cents={variant.price_cents} className="text-sm" />
                    <p className="label mt-1 text-[var(--muted)]">
                      {!variant.is_active
                        ? "No disponible"
                        : variant.stock_available > 0
                        ? `${variant.stock_available} disponibles`
                        : "Agotado"}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <form action={addToCartAction} className="mt-6 border border-[var(--hairline)] px-4 py-4">
            <p className="label text-[var(--muted)]">Compra</p>
            <label htmlFor="variant-select" className="sr-only">Variante</label>
            <select
              id="variant-select"
              name="variant_id"
              required
              defaultValue=""
              className="mt-2 w-full border border-[var(--hairline)] bg-[var(--surface-2)] px-3 py-3"
            >
              <option value="" disabled>
                Elige una variante…
              </option>
              {product.variants
                .filter((variant) => variant.is_active && variant.stock_available > 0)
                .map((variant) => (
                  <option key={variant.id} value={variant.id}>
                    {variantLabel(variant.option_values)} — {formatPrice(variant.price_cents)}
                  </option>
                ))}
            </select>
            <div className="mt-3 flex items-center gap-3">
              <label htmlFor="qty" className="label text-[var(--muted)]">Cantidad</label>
              <input
                id="qty"
                name="quantity"
                type="number"
                min={1}
                max={10}
                defaultValue={1}
                className="w-20 border border-[var(--hairline)] bg-[var(--surface-2)] px-3 py-2"
              />
            </div>
            <button
              type="submit"
              disabled={!hasActiveVariant}
              className="label mt-4 w-full border border-[var(--ink)] bg-[var(--ink)] px-6 py-3 text-[var(--surface)] transition-colors hover:bg-[var(--signal)] hover:text-[var(--surface)] disabled:cursor-not-allowed disabled:opacity-40"
            >
              {hasActiveVariant ? "Añadir al carrito" : "Agotado"}
            </button>
          </form>

          {product.tags.length > 0 ? (
            <div className="mt-6 flex flex-wrap gap-2">
              {product.tags.map((tag) => (
                <span
                  key={tag}
                  className="label border border-[var(--hairline)] px-2 py-1 text-[var(--muted)]"
                >
                  {tag}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </main>
  );
}
