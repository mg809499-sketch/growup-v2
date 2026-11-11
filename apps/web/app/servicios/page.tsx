import Link from "next/link";
import type { Metadata } from "next";

import { services, coming_soon } from "@/content/services";

export const metadata: Metadata = {
  title: "Servicios — todo lo que tu tienda necesita",
  description:
    "Builder, catálogo e inventario, pagos Wompi, facturación DIAN, media y CDN, dominios, pedidos y auditoría — en un solo panel.",
};

const STATUS_LABEL: Record<string, string> = {
  disponible: "Disponible",
  "en-piloto": "En piloto",
  proximamente: "Próximamente",
};

export default function ServiciosPage() {
  return (
    <>
      <section className="hairline-b">
        <div className="mx-auto max-w-6xl px-6 py-16 md:px-10 md:py-20">
          <p className="label text-[var(--muted)]">[ servicios ]</p>
          <h1 className="display mt-3 text-5xl leading-[0.95] md:text-7xl">
            Todo lo que
            <br /> tu marca necesita.
          </h1>
          <p className="mt-6 max-w-md text-lg leading-relaxed text-[var(--muted)]">
            Ocho piezas que se encajan entre sí: publicas más rápido, operas
            menos al teléfono y vendes con lo que ya tienes.
          </p>
        </div>
      </section>

      <section aria-label="Listado de servicios" className="hairline-b">
        <div className="mx-auto max-w-6xl px-6 py-12 md:px-10">
          <ul className="grid gap-px overflow-hidden border border-[var(--hairline)] bg-[var(--hairline)] md:grid-cols-2">
            {services.map((service) => (
              <li key={service.slug} className="bg-[var(--surface-2)]">
                <Link
                  href={`/servicios/${service.slug}`}
                  className="group flex h-full flex-col gap-4 p-6 transition-colors hover:bg-[var(--ink)] hover:text-[var(--surface)] md:p-8"
                >
                  <div className="flex items-center justify-between gap-4">
                    <h2 className="text-2xl font-medium leading-tight">{service.title}</h2>
                    <span className="label shrink-0 border border-[var(--hairline)] px-2 py-1 text-[var(--muted)] group-hover:border-[var(--surface)] group-hover:text-[var(--surface)]">
                      {STATUS_LABEL[service.status]}
                    </span>
                  </div>
                  <p className="max-w-md text-[var(--muted)] group-hover:text-[var(--surface)]">
                    {service.short}
                  </p>
                  <span className="label mt-auto text-[var(--signal)] group-hover:text-[var(--surface)]">
                    Ver servicio →
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section aria-label="Próximamente" className="mx-auto max-w-6xl px-6 py-12 md:px-10">
        <p className="label text-[var(--muted)]">[ próximamente ]</p>
        <ul className="mt-4 grid gap-4 md:grid-cols-3">
          {coming_soon.map((item) => (
            <li key={item.title} className="border border-dashed border-[var(--hairline)] p-5">
              <p className="label text-[var(--muted)]">Próximamente</p>
              <h3 className="mt-2 font-medium">{item.title}</h3>
              <p className="mt-1 text-sm text-[var(--muted)]">{item.note}</p>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
