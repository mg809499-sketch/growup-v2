import Image from "next/image";

export function ProductCarousel({
  products,
}: {
  products: ReadonlyArray<{ id: string; name: string; price_cents: number; badge: string; image: string; alt: string }>;
}) {
  return (
    <section aria-labelledby="productos-drop" className="px-6 pb-20 pt-6 md:px-10">
      <div className="mx-auto max-w-6xl">
        <div className="flex items-end justify-between gap-6 border-b border-black/10 pb-4">
          <div>
            <p className="text-[15px] text-[#525866]">Sol de Calle · Drop 04</p>
            <h2 id="productos-drop" className="display mt-1 text-[clamp(1.75rem,3.2vw,2.75rem)] leading-[1] text-[#0d0d0d]">
              Últimas piezas del lote 24
            </h2>
          </div>
          <p className="hidden text-sm text-[#525866] md:block">Desliza →</p>
        </div>

        <div className="mt-6 flex gap-5 overflow-x-auto pb-4 [scrollbar-width:none] scroll-smooth snap-x snap-mandatory [&::-webkit-scrollbar]:hidden">
          {products.map((product) => (
            <article
              key={product.id}
              className="group glass-card w-[72vw] max-w-[280px] shrink-0 snap-start overflow-hidden"
            >
              <div className="relative aspect-[4/5] overflow-hidden rounded-t-2xl bg-slate-100">
                <Image
                  src={product.image}
                  alt={product.alt}
                  fill
                  sizes="(max-width: 768px) 72vw, 280px"
                  className="object-cover transition-transform duration-[450ms] ease-out group-hover:scale-[1.045]"
                  priority={product.id === "jeans-archivo-04"}
                />
                <span className="absolute left-3 top-3 rounded-full border border-black/10 bg-white/85 px-3 py-1 text-[11px] font-semibold tracking-[0.08em] text-[#0d0d0d] backdrop-blur-md">
                  {product.badge}
                </span>
              </div>
              <div className="grid gap-2 border-t border-black/10 p-4">
                <h3 className="text-[14px] font-semibold leading-snug text-[#0d0d0d]">{product.name}</h3>
                <p className="font-[family-name:var(--font-geist-mono)] text-[17px] font-bold tabular-nums text-[#0d0d0d]">
                  {new Intl.NumberFormat("es-CO", {
                    style: "currency",
                    currency: "COP",
                    maximumFractionDigits: 0,
                  }).format(product.price_cents / 100)}
                </p>
                <a
                  href="#carrito-demo"
                  className="mt-1 inline-flex min-h-11 items-center justify-center rounded-xl border border-[#0d0d0d] bg-white/80 px-4 text-sm font-semibold text-[#0d0d0d] backdrop-blur-md transition-colors hover:bg-[#0d0d0d] hover:text-white"
                >
                  Añadir al carrito
                </a>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
