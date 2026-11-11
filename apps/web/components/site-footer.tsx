import Link from "next/link";

import { site } from "@/content/site";

const services = [
  { href: "/servicios/builder", label: "Builder" },
  { href: "/servicios/catalogo-inventario", label: "Catálogo e inventario" },
  { href: "/servicios/pagos-wompi", label: "Pagos y Wompi" },
  { href: "/servicios/facturacion-dian", label: "Facturación DIAN" },
] as const;

export function SiteFooter() {
  return (
    <footer className="hairline-t">
      <div className="mx-auto max-w-6xl px-6 py-12 md:px-10">
        <div className="flex flex-col justify-between gap-10 md:flex-row">
          <div className="max-w-sm">
            <Link href="/" className="display text-2xl leading-none">
              growup<span aria-hidden className="text-[var(--signal)]">.</span>
            </Link>
            <p className="mt-4 text-sm leading-relaxed text-[var(--muted)]">
              La tiendita completa para marcas de ropa y joyería en Colombia:
              storefront, builder, catálogo, inventario, pagos y facturación
              electrónica. {site.contact_hours}.
            </p>
          </div>

          <nav aria-label="Servicios" className="grid grid-cols-2 gap-x-10 gap-y-6 sm:grid-cols-3">
            <div>
              <p className="label text-[var(--muted)]">Producto</p>
              <ul className="mt-3 space-y-2 text-sm">
                {services.map((item) => (
                  <li key={item.href}>
                    <Link href={item.href} className="text-[var(--muted)] hover:text-[var(--ink)]">
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="label text-[var(--muted)]">Acceso</p>
              <ul className="mt-3 space-y-2 text-sm">
                <li><Link href="/planes" className="text-[var(--muted)] hover:text-[var(--ink)]">Planes</Link></li>
                <li><Link href="/solicitar-acceso" className="text-[var(--muted)] hover:text-[var(--ink)]">Solicitar acceso</Link></li>
                <li>
                  <a href={site.admin_url} className="text-[var(--muted)] hover:text-[var(--ink)]" target="_blank" rel="noopener noreferrer">
                    Consola de comercio
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <p className="label text-[var(--muted)]">Contacto</p>
              <ul className="mt-3 space-y-2 text-sm">
                <li>
                  <a href={`mailto:${site.contact_email}`} className="text-[var(--muted)] hover:text-[var(--ink)]">
                    {site.contact_email}
                  </a>
                </li>
                <li>Piloto ropa + joyería · Q1 2027</li>
              </ul>
            </div>
          </nav>
        </div>

        <div className="hairline-t mt-10 flex flex-wrap items-center justify-between gap-4 pt-6">
          <p className="label text-[var(--muted)]">© {new Date().getFullYear()} growup</p>
          <p className="label text-[var(--muted)]">ropa &amp; joyería · Colombia</p>
        </div>
      </div>
    </footer>
  );
}
