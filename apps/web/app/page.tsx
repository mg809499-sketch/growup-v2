import Link from "next/link";

import { PlanCarousel } from "@/components/plan-carousel";
import { services, coming_soon } from "@/content/services";
import { site } from "@/content/site";

const steps = [
  {
    number: "01",
    title: "Solicita acceso",
    body: "Nos escribes o dejas tus datos. Te abrimos la tienda con acceso asistido.",
  },
  {
    number: "02",
    title: "Publicas tu catálogo",
    body: "Productos, variantes, media y páginas con el builder. En minutos.",
  },
  {
    number: "03",
    title: "Vendes y cobras",
    body: "Checkout Wompi hosted, factura DIAN y stock que no se oversell.",
  },
];

const differentiators = [
  {
    number: "01",
    title: "Builder de páginas",
    body: "16 bloques cerrados, versionado, preview con token y publish atómico con purga de caché.",
  },
  {
    number: "02",
    title: "Catálogo sin oversell",
    body: "Variantes, SKU, FTS en español e inventario atómico multi-ubicación.",
  },
  {
    number: "03",
    title: "Pagos hosted",
    body: "Wompi de tu cuenta cobra al comprador; Stripe de growup cobra tu suscripción. Cero PAN en nuestros servidores.",
  },
  {
    number: "04",
    title: "Facturación DIAN",
    body: "Cada pago emite factura electrónica por API; devoluciones generan nota crédito.",
  },
];

export default function HomePage() {
  return (
    <>
      {/* Hero */}
      <section className="border-b border-[var(--hairline)]">
        <div className="mx-auto grid max-w-6xl gap-10 px-6 pb-16 pt-14 md:grid-cols-12 md:px-10 md:pb-24 md:pt-20">
          <div className="flex flex-col justify-center md:col-span-7">
            <p className="label text-[var(--muted)]">[ comercio × acento ]</p>
            <h1 className="display mt-4 text-[clamp(3.2rem,12vw,7.5rem)] leading-[0.9]">
              La tiendita completa para marcas de ropa y joyería
            </h1>
            <p className="mt-6 max-w-md text-lg leading-relaxed text-[var(--muted)]">
              Tienda, builder, catálogo, inventario, pagos Wompi y factura
              DIAN — en una sola plataforma para marcas colombianas.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Link
                href="/solicitar-acceso"
                className="label inline-flex border border-[var(--ink)] bg-[var(--ink)] px-6 py-4 text-[var(--surface)] transition-colors hover:bg-[var(--signal)]"
              >
                Solicitar acceso
              </Link>
              <Link href="/planes" className="label underline underline-offset-4 hover:opacity-60">
                Ver planes →
              </Link>
            </div>
            <p className="label mt-8 text-[var(--muted)]">
              Piloto ropa + joyería · Q1 2027 · Sin tarjeta al pedir cupo
            </p>
          </div>

          <div
            aria-hidden
            className="relative flex min-h-[320px] flex-col justify-end overflow-hidden border border-[var(--hairline)] bg-[var(--ink)] p-6 text-[var(--surface)] md:col-span-5"
          >
            <p className="label text-[var(--muted)]">[ 01 / señal ]</p>
            <p className="display mt-auto text-6xl leading-[0.9] text-[var(--surface)]">
              Archivo
              <br />
              <span className="text-[var(--signal)]">ropa</span>
            </p>
            <p className="mt-3 text-sm text-[var(--muted)]">
              Ropa artesanal · Bogotá — storefront con bloques publicados
            </p>
          </div>
        </div>
      </section>

      {/* Diferenciadores */}
      <section aria-label="Diferenciadores" className="hairline-b">
        <div className="mx-auto max-w-6xl px-6 py-14 md:px-10">
          <p className="label text-[var(--muted)]">[ 01 / qué resuelve ]</p>
          <div className="mt-6 grid gap-px overflow-hidden border border-[var(--hairline)] bg-[var(--hairline)] md:grid-cols-2 lg:grid-cols-4">
            {differentiators.map((item) => (
              <div key={item.number} className="bg-[var(--surface-2)] p-6">
                <p className="label text-[var(--muted)]">[{item.number}]</p>
                <h2 className="mt-3 text-lg font-medium leading-tight">{item.title}</h2>
                <p className="mt-2 text-sm leading-relaxed text-[var(--muted)]">{item.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Cómo funciona */}
      <section aria-label="Cómo funciona" className="hairline-b">
        <div className="mx-auto max-w-6xl px-6 py-14 md:px-10">
          <p className="label text-[var(--muted)]">[ 02 / cómo funciona ]</p>
          <ol className="mt-6 grid gap-8 md:grid-cols-3">
            {steps.map((step) => (
              <li key={step.number} className="border-l-2 border-[var(--ink)] pl-5">
                <p className="label text-[var(--muted)]">{step.number}</p>
                <h3 className="mt-2 text-xl font-medium">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[var(--muted)]">{step.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Planes */}
      <section aria-label="Planes" className="hairline-b">
        <div className="mx-auto max-w-6xl px-6 py-14 md:px-10">
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div>
              <p className="label text-[var(--muted)]">[ 03 / planes ]</p>
              <h2 className="display mt-2 text-4xl md:text-5xl">Escoge tu ritmo</h2>
            </div>
            <Link href="/planes" className="label underline underline-offset-4 hover:opacity-60">
              Ver plan completo →
            </Link>
          </div>
          <div className="mt-8">
            <PlanCarousel />
          </div>
        </div>
      </section>

      {/* Servicios */}
      <section aria-label="Servicios" className="hairline-b">
        <div className="mx-auto max-w-6xl px-6 py-14 md:px-10">
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div>
              <p className="label text-[var(--muted)]">[ 04 / servicios ]</p>
              <h2 className="display mt-2 text-4xl md:text-5xl">Todo en un solo panel</h2>
            </div>
            <Link href="/servicios" className="label underline underline-offset-4 hover:opacity-60">
              Todos los servicios →
            </Link>
          </div>
          <ul className="mt-8 grid grid-cols-2 gap-px overflow-hidden border border-[var(--hairline)] bg-[var(--hairline)] md:grid-cols-4">
            {services.slice(0, 8).map((service) => (
              <li key={service.slug} className="bg-[var(--surface-2)]">
                <Link
                  href={`/servicios/${service.slug}`}
                  className="flex h-full flex-col justify-between gap-4 p-5 transition-colors hover:bg-[var(--ink)] hover:text-[var(--surface)]"
                >
                  <h3 className="text-sm font-medium leading-snug">{service.title}</h3>
                  <p className="label text-[var(--muted)]">{service.status === "en-piloto" ? "en piloto" : service.status}</p>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Prueba social honesta */}
      <section aria-label="Pilotos" className="hairline-b">
        <div className="mx-auto max-w-6xl px-6 py-14 md:px-10">
          <p className="label text-[var(--muted)]">[ 05 / pilotos ]</p>
          <h2 className="display mt-2 text-3xl md:text-4xl">
            Dos marcas que están construyendo con growup
          </h2>
          <div className="mt-8 grid gap-6 md:grid-cols-2">
            <figure className="border border-[var(--hairline)] p-6">
              <blockquote className="text-lg leading-relaxed">
                «Queremos un archivo editorial, no otra tienda genérica. growup
                nos deja diseñar la boutique como se ve y pagar cobrando de
                inmediato.»
              </blockquote>
              <figcaption className="label mt-4 text-[var(--muted)]">
                Piloto ropa · Bogotá · En preparación (pendiente de permiso de nombre)
              </figcaption>
            </figure>
            <figure className="border border-[var(--hairline)] p-6">
              <blockquote className="text-lg leading-relaxed">
                «Facturar cada venta por API sin tocar la DIAN a mano es la
                diferencia entre vender y operar en serio.»
              </blockquote>
              <figcaption className="label mt-4 text-[var(--muted)]">
                Piloto joyería · Bogotá · En preparación (pendiente de permiso de nombre)
              </figcaption>
            </figure>
          </div>
        </div>
      </section>

      {/* Próximamente */}
      <section aria-label="Próximamente" className="hairline-b">
        <div className="mx-auto max-w-6xl px-6 py-10 md:px-10">
          <p className="label text-[var(--muted)]">[ próximamente ]</p>
          <ul className="mt-3 flex flex-wrap gap-3 text-sm text-[var(--muted)]">
            {coming_soon.map((item) => (
              <li key={item.title} className="label border border-[var(--hairline)] px-3 py-2">
                {item.title}
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* CTA final */}
      <section aria-label="Solicitar acceso">
        <div className="mx-auto max-w-6xl px-6 py-20 text-center md:px-10">
          <p className="label text-[var(--muted)]">[ 06 / cupos ]</p>
          <h2 className="display mx-auto mt-4 max-w-4xl text-5xl leading-[0.95] md:text-7xl">
            ¿Vendemos tú y yo en marzo?
          </h2>
          <p className="mx-auto mt-6 max-w-md text-lg text-[var(--muted)]">
            Cupos de piloto limitados. Sin tarjeta al pedir cupo; recibes una
            propuesta y una llamada de 20 minutos.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/solicitar-acceso"
              className="label inline-flex border border-[var(--ink)] bg-[var(--ink)] px-8 py-4 text-[var(--surface)] transition-colors hover:bg-[var(--signal)]"
            >
              Solicitar acceso
            </Link>
            <a href={`mailto:${site.contact_email}`} className="label underline underline-offset-4 hover:opacity-60">
              {site.contact_email}
            </a>
          </div>
        </div>
      </section>
    </>
  );
}
