import Link from "next/link";

import { EmptyState } from "@/components/empty-state";
import { ProductCard } from "@/components/product-card";
import { SectionLabel } from "@/components/section-label";
import { getBootstrap, getStorefrontHost, listProducts } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function CollectionPage({
  searchParams,
}: {
  searchParams: Promise<{ category?: string }>;
}) {
  const { category } = await searchParams;
  const host = await getStorefrontHost();
  const [bootstrap, products] = await Promise.all([
    getBootstrap(host),
    listProducts(host, 30, category),
  ]);

  return (
    <main className="mx-auto max-w-[1440px] px-4 pt-10 md:px-10 md:pt-14">
      <div className="border-b border-[var(--hairline)] pb-6">
        <SectionLabel>Catálogo</SectionLabel>
        <div className="mt-2 flex flex-wrap items-end justify-between gap-4">
          <h1 className="display text-[clamp(2.8rem,8vw,6rem)] leading-none">
            Colección
          </h1>
          <p className="label text-[var(--muted)]">
            {products.items.length} {products.items.length === 1 ? "pieza" : "piezas"}
          </p>
        </div>
        <p className="mt-4 max-w-xl text-sm leading-relaxed text-[var(--muted)]">
          Una selección editorial de {bootstrap.tenant.name}. Series cortas,
          producción local y disponibilidad limitada.
        </p>
        {category ? (
          <div className="mt-4 flex items-center gap-3">
            <span className="label border border-[var(--hairline)] px-2 py-1">
              {category}
            </span>
            <Link className="label underline underline-offset-4" href="/collection">
              Quitar filtro
            </Link>
          </div>
        ) : null}
      </div>

      {products.items.length > 0 ? (
        <div className="mt-8 grid grid-cols-1 gap-x-4 gap-y-12 sm:grid-cols-2 lg:grid-cols-3">
          {products.items.map((product, index) => (
            <ProductCard key={product.id} product={product} index={index} />
          ))}
        </div>
      ) : (
        <div className="mt-8">
          <EmptyState
            title="No hay piezas con este filtro"
            description="Prueba con otra categoría o vuelve a la colección completa."
          />
        </div>
      )}
    </main>
  );
}
