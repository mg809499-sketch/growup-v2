import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";

import { getService, services } from "@/content/services";

export function generateStaticParams() {
  return services.map((service) => ({ slug: service.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const service = getService(slug);
  if (!service) {
    return { title: "Servicio" };
  }
  return {
    title: service.title,
    description: service.short,
  };
}

const STATUS_LABEL = {
  disponible: "Disponible",
  "en-piloto": "En piloto",
  proximamente: "Próximamente",
} as const;

export default async function ServicePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const service = getService(slug);
  if (!service) {
    notFound();
  }

  return (
    <>
      <section className="hairline-b">
        <div className="mx-auto max-w-6xl px-6 py-16 md:px-10 md:py-20">
          <p className="label text-[var(--muted)]">
            [ servicio · {STATUS_LABEL[service.status]} ]
          </p>
          <h1 className="display mt-3 max-w-4xl text-5xl leading-[0.95] md:text-7xl">
            {service.hero}
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-[var(--muted)]">
            {service.description}
          </p>
          <Link
            href="/solicitar-acceso"
            className="label mt-8 inline-flex border border-[var(--ink)] bg-[var(--ink)] px-6 py-3 text-[var(--surface)] transition-colors hover:bg-[var(--signal)]"
          >
            {service.cta_label}
          </Link>
        </div>
      </section>

      <section aria-label="Qué incluye" className="hairline-b">
        <div className="mx-auto max-w-6xl px-6 py-12 md:px-10">
          <p className="label text-[var(--muted)]">[ qué incluye ]</p>
          <ul className="mt-6 grid gap-4 md:grid-cols-2">
            {service.includes.map((item) => (
              <li
                key={item}
                className="flex gap-3 border border-[var(--hairline)] bg-[var(--surface-2)] p-5"
              >
                <span aria-hidden className="label text-[var(--signal)]">■</span>
                <span className="leading-relaxed">{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-12 md:px-10">
        <Link href="/servicios" className="label text-[var(--muted)] hover:text-[var(--ink)]">
          ← Todos los servicios
        </Link>
      </section>
    </>
  );
}
