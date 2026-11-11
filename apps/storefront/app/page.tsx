import Image from "next/image";
import Link from "next/link";

import { EmptyState } from "@/components/empty-state";
import { ProductCard } from "@/components/product-card";
import { SectionLabel } from "@/components/section-label";
import { BlockRenderer } from "@/components/blocks";
import { getBootstrap, getPublishedPage, getStorefrontHost, listProducts } from "@/lib/api";
import { mediaUrl } from "@/lib/format";
import type { Block } from "@/lib/blocks";

export const revalidate = 3600;

export default async function HomePage() {
  const host = await getStorefrontHost();
  const published = await getPublishedPage(host, "home");

  if (published && typeof published.layout === "object" && Array.isArray((published.layout as { blocks?: unknown }).blocks)) {
    const blocks = (published.layout as { blocks: Block[] }).blocks;
    return (
      <main>
        {blocks.map((block) => (
          <BlockRenderer key={block.id} block={block} />
        ))}
      </main>
    );
  }

  const [bootstrap, products] = await Promise.all([
    getBootstrap(host),
    listProducts(host, 6),
  ]);

  const hero = products.items[0];
  const heroImage = hero?.primary_image_key
    ? mediaUrl("", hero.primary_image_key)
    : "";

  return (
    <main>
      <section className="mx-auto max-w-[1440px] px-4 pt-8 md:px-10 md:pt-14">
        <div className="grid gap-8 border-b border-[var(--hairline)] pb-10 lg:grid-cols-12 lg:gap-10 lg:pb-14">
          <div className="flex flex-col justify-between lg:col-span-7">
            <div>
              <SectionLabel>[DROP 01]</SectionLabel>
              <h1 className="display mt-4 max-w-full text-[clamp(3.6rem,11vw,8.8rem)] leading-[0.84]">
                {bootstrap.tenant.name}
              </h1>
              <p className="mt-6 max-w-lg text-base leading-relaxed text-[var(--muted)] md:text-lg">
                Comercio editorial desde Bogotá. Piezas seleccionadas, series
                cortas y una tienda que se siente como un archivo.
              </p>
            </div>

            <div className="mt-10 flex flex-wrap items-center gap-4">
              <Link
                href="/collection"
                className="label inline-flex items-center border border-[var(--ink)] bg-[var(--ink)] px-5 py-3 text-[var(--surface)] transition-colors hover:bg-[var(--signal)] hover:text-[var(--surface)]"
              >
                [ Ver colección ]
              </Link>
              <p className="label text-[var(--muted)]">Envíos nacionales · COP</p>
            </div>
          </div>

          <div className="lg:col-span-5">
            <div className="relative aspect-[4/5] w-full overflow-hidden bg-[var(--surface-2)]">
              {heroImage ? (
                <Image
                  src={heroImage}
                  alt={hero?.name ?? bootstrap.tenant.name}
                  fill
                  priority
                  sizes="(min-width: 1024px) 40vw, 100vw"
                  className="object-cover"
                />
              ) : (
                <div className="flex h-full items-center justify-center">
                  <span className="label text-[var(--muted)]">[ imagen editorial ]</span>
                </div>
              )}
            </div>
            <div className="mt-3 flex items-center justify-between gap-4">
              <p className="label text-[var(--muted)]">Temporada 01</p>
              <p className="label text-[var(--muted)]">Bogotá / CO</p>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-[1440px] px-4 pt-10 md:px-10 md:pt-14">
        <div className="flex items-end justify-between gap-6 border-b border-[var(--hairline)] pb-4">
          <div>
            <SectionLabel>Selección</SectionLabel>
            <h2 className="display mt-2 text-[clamp(2rem,4vw,3.4rem)] leading-none">
              Últimas piezas
            </h2>
          </div>
          <Link className="label shrink-0 hover:opacity-60" href="/collection">
            Ver todo →
          </Link>
        </div>

        {products.items.length > 0 ? (
          <div className="mt-6 grid grid-cols-1 gap-x-4 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
            {products.items.map((product, index) => (
              <ProductCard key={product.id} product={product} index={index} />
            ))}
          </div>
        ) : (
          <div className="mt-6">
            <EmptyState
              title="Todavía no hay piezas publicadas"
              description="Cuando el catálogo del tenant tenga productos activos, aparecerán aquí automáticamente."
            />
          </div>
        )}
      </section>

      <section className="mx-auto mt-16 max-w-[1440px] px-4 md:mt-24 md:px-10">
        <div className="grid gap-6 border-y border-[var(--hairline)] py-8 md:grid-cols-3">
          <div>
            <SectionLabel>01 / Envío</SectionLabel>
            <p className="mt-2 text-sm leading-relaxed text-[var(--muted)]">
              Envíos nacionales coordinados con el comercio. Cobertura y tiempos
              se confirman al finalizar la compra.
            </p>
          </div>
          <div>
            <SectionLabel>02 / Cambios</SectionLabel>
            <p className="mt-2 text-sm leading-relaxed text-[var(--muted)]">
              Cada tienda publica su política de cambios y devoluciones conforme
              a la normativa colombiana.
            </p>
          </div>
          <div>
            <SectionLabel>03 / Pago</SectionLabel>
            <p className="mt-2 text-sm leading-relaxed text-[var(--muted)]">
              Pago seguro con la pasarela del comercio. Growup no almacena datos
              de tarjeta.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
