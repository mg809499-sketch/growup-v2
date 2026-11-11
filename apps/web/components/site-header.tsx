import Link from "next/link";

import { site } from "@/content/site";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-[var(--hairline)] bg-[var(--surface)]/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-6 py-4 md:px-10">
        <Link href="/" className="display text-xl leading-none">
          growup<span aria-hidden className="text-[var(--signal)]">.</span>
        </Link>
        <nav aria-label="Principal" className="hidden items-center gap-8 md:flex">
          <Link href="/servicios" className="label text-[var(--muted)] transition-colors hover:text-[var(--ink)]">
            Servicios
          </Link>
          <Link href="/planes" className="label text-[var(--muted)] transition-colors hover:text-[var(--ink)]">
            Planes
          </Link>
          <a
            href={site.admin_url}
            className="label text-[var(--muted)] transition-colors hover:text-[var(--ink)]"
            target="_blank"
            rel="noopener noreferrer"
          >
            Consola
          </a>
        </nav>
        <a
          href={site.admin_login_url}
          className="label inline-flex items-center border border-[var(--ink)] bg-[var(--ink)] px-5 py-2.5 text-[var(--surface)] transition-colors hover:bg-[var(--signal)]"
        >
          Iniciar sesión
        </a>
      </div>
    </header>
  );
}
