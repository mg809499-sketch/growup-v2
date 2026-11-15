import Image from "next/image";
import Link from "next/link";

import { mockTheme } from "@/content/mock-storefront";
import { site } from "@/content/site";
import { ProductCarousel } from "@/components/mock-product-carousel";

export default function HomePage() {
  const { tenant, categories, products, brands, credits } = mockTheme;

  return (
    <>
      {/* Hero: mock completo de storefront con glassmorphism y fondo blanco */}
      <section
        aria-labelledby="hero-title"
        className="border-b border-black/10 bg-transparent text-[#0d0d0d]"
      >
        <div className="mx-auto max-w-6xl px-6 py-8 md:px-10 md:py-10">
          <div className="glass-card mb-6 flex flex-col gap-3 px-5 py-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-[13px] font-medium text-[#525866]">
                Demo de storefront publicada · {tenant.host}
              </p>
              <p className="mt-0.5 text-[15px] font-semibold text-[#0d0d0d]">
                {tenant.name} — esta es la experiencia que un comerciante ve en growup.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <Link href="/servicios/builder" className="font-medium text-[#0d0d0d] underline underline-offset-4 hover:opacity-70">
                Ver cómo se construye
              </Link>
              <a
                href={site.admin_login_url}
                className="inline-flex min-h-11 items-center rounded-xl bg-[#0d0d0d] px-5 font-semibold text-white shadow-sm"
              >
                Entrar a la tienda
              </a>
            </div>
          </div>

          <div className="grid gap-6 py-4 md:grid-cols-12 md:gap-8 md:py-6">
            <div className="glass-card flex flex-col justify-between gap-6 p-6 md:col-span-5 md:p-8">
              <div>
                <span className="label inline-block rounded-full border border-black/10 bg-white/80 px-3 py-1 text-[#525866]">
                  Plataforma E-Commerce
                </span>
                <h1
                  id="hero-title"
                  className="display mt-4 text-[clamp(2.2rem,4.6vw,3.8rem)] leading-[1.02] text-[#0d0d0d]"
                >
                  La tienda online lista para publicar.
                </h1>
                <p className="mt-4 max-w-[36ch] text-[1.05rem] leading-relaxed text-[#525866]">
                  Catálogo, páginas con bloques, pagos hosted y facturación — sin rehacer
                  tu marca. Esto es un mock vivo del storefront.
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-4">
                <a
                  href={site.admin_login_url}
                  className="nova-cta inline-flex min-h-12 items-center rounded-xl bg-[#0d0d0d] px-6 text-sm font-semibold uppercase tracking-[0.08em] text-white"
                >
                  Solicitar cupo piloto
                </a>
                <Link href="/servicios" className="text-sm font-semibold text-[#0d0d0d] underline underline-offset-4 hover:opacity-70">
                  Qué incluye
                </Link>
              </div>
            </div>

            {/* Mosaico de tarjetas redondeadas con glassmorphism */}
            <div className="relative md:col-span-7">
              <div className="grid grid-cols-12 gap-4">
                <div className="group glass-card relative col-span-8 aspect-[4/5] overflow-hidden">
                  <Image
                    src="/assets-nova/drop-sol-de-calle.jpg"
                    alt="Calle streetwear en Tokio para la colección de Sol de Calle"
                    fill
                    priority
                    sizes="(max-width: 768px) 66vw, 560px"
                    className="object-cover transition-transform duration-[450ms] ease-out group-hover:scale-[1.045]"
                  />
                  <div className="absolute inset-x-3 bottom-3 flex items-end justify-between rounded-2xl border border-black/10 bg-white/80 p-4 backdrop-blur-xl">
                    <div className="text-[#0d0d0d]">
                      <p className="text-[11px] font-semibold uppercase tracking-wider text-[#525866]">
                        DROP 04 · EN VIVO
                      </p>
                      <p className="display mt-0.5 text-xl leading-none text-[#0d0d0d]">
                        Sol de Calle
                      </p>
                    </div>
                    <span className="rounded-xl bg-[#0d0d0d] px-3.5 py-1.5 text-[12px] font-semibold text-white">
                      Ver drop
                    </span>
                  </div>
                </div>
                <div className="col-span-4 flex flex-col gap-4">
                  <div className="group glass-card relative aspect-square overflow-hidden">
                    <Image
                      src="/assets-nova/aretes-kyanite.jpg"
                      alt="Aretes Arabesque de oro y kyanita"
                      fill
                      sizes="(max-width: 768px) 33vw, 220px"
                      className="object-cover transition-transform duration-[450ms] ease-out group-hover:scale-[1.045]"
                    />
                    <p className="absolute left-3 top-3 rounded-full border border-black/10 bg-white/85 px-3 py-1 text-[11px] font-semibold text-[#0d0d0d] backdrop-blur-md">
                      Aurélia
                    </p>
                  </div>
                  <div className="group glass-card relative aspect-[4/5] overflow-hidden">
                    <Image
                      src="/assets-nova/denim-jeans.jpg"
                      alt="Editorial de denim recto"
                      fill
                      sizes="(max-width: 768px) 33vw, 220px"
                      className="object-cover transition-transform duration-[450ms] ease-out group-hover:scale-[1.045]"
                    />
                    <p className="absolute left-3 bottom-3 rounded-full border border-black/10 bg-white/85 px-3 py-1 text-[11px] font-semibold text-[#0d0d0d] backdrop-blur-md">
                      Estudio 04
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Carril de categorías con bordes redondeados y etiqueta glass */}
          <div className="mt-4 flex gap-4 overflow-x-auto pb-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            {categories.map((category) => (
              <Link
                key={category.label}
                href={category.href}
                className="group glass-card relative h-36 w-[156px] shrink-0 overflow-hidden md:h-40"
              >
                <Image
                  src={category.image}
                  alt={category.label}
                  fill
                  sizes="156px"
                  className="object-cover transition-transform duration-[450ms] ease-out group-hover:scale-[1.045]"
                />
                <span className="absolute inset-x-2.5 bottom-2.5 flex items-center justify-between rounded-xl border border-black/10 bg-white/85 px-3 py-1.5 text-[13px] font-semibold text-[#0d0d0d] backdrop-blur-md">
                  <span>{category.label}</span>
                  <span>→</span>
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Carrusel de productos */}
      <ProductCarousel products={products} />

      {/* Marcas en tarjetas redondeadas glass */}
      <section aria-labelledby="marcas-plataforma" className="border-t border-black/10 px-6 py-16 md:px-10">
        <div className="mx-auto max-w-6xl">
          <h2 id="marcas-plataforma" className="display text-[clamp(1.5rem,2.8vw,2.25rem)] leading-tight text-[#0d0d0d]">
            Marcas que publican con growup
          </h2>
          <p className="mt-3 max-w-[52ch] text-[#525866]">
            Dos pilotos y el estudio que los cura: ropa y joyería premium con inventario
            propio, Wompi hosted y factura DIAN.
          </p>
          <div className="mt-8 grid gap-4 md:grid-cols-4">
            {brands.map((brand) => (
              <div key={brand.name} className="glass-card p-6">
                <p className="display text-xl text-[#0d0d0d]">{brand.name}</p>
                <p className="mt-2 text-sm text-[#525866]">{brand.line}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Cómo funciona */}
      <section aria-labelledby="como-funciona" className="border-t border-black/10 px-6 py-16 md:px-10">
        <div className="mx-auto grid max-w-6xl gap-10 md:grid-cols-12">
          <h2
            id="como-funciona"
            className="display max-w-[18ch] text-[clamp(1.6rem,2.6vw,2.4rem)] leading-[1.05] text-[#0d0d0d] md:col-span-4"
          >
            Del prototipo a la tienda publicada
          </h2>
          <ol className="grid gap-6 text-[1.05rem] leading-[1.55] md:col-span-7 md:col-start-6">
            <li className="glass-card p-5">
              <span className="font-bold text-[#0d0d0d]">Solicita acceso.</span>{" "}
              <span className="text-[#525866]">Te abrimos la tienda con acceso asistido; sin tarjeta al pedir cupo.</span>
            </li>
            <li className="glass-card p-5">
              <span className="font-bold text-[#0d0d0d]">Carga catálogo y páginas.</span>{" "}
              <span className="text-[#525866]">Variantes, media e inventario atómico. Builder de bloques con publish atómico.</span>
            </li>
            <li className="glass-card p-5">
              <span className="font-bold text-[#0d0d0d]">Publica y cobra.</span>{" "}
              <span className="text-[#525866]">Checkout Wompi hosted. Facturación DIAN por API (pendiente de proveedor sandbox en piloto).</span>
            </li>
          </ol>
        </div>
      </section>

      {/* Créditos */}
      <section aria-label="Créditos de las imágenes" className="border-t border-black/10 px-6 py-6 md:px-10">
        <details className="glass-card mx-auto max-w-6xl p-4 text-[13px] text-[#525866]">
          <summary className="cursor-pointer font-semibold text-[#0d0d0d]">
            Créditos de fotografía usada en este demo
          </summary>
          <ul className="mt-3 list-disc space-y-1 pl-5">
            {credits.map((credit) => (
              <li key={credit}>{credit}</li>
            ))}
          </ul>
        </details>
      </section>
    </>
  );
}
