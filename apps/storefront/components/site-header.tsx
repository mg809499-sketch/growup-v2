import Link from "next/link";

import type { components } from "@growup/contracts";

type TenantPublic = components["schemas"]["TenantPublic"];

export function SiteHeader({ tenant }: { tenant: TenantPublic }) {
  return (
    <header className="sticky top-0 z-40 border-b border-[var(--hairline)] bg-[var(--surface)]/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-[1440px] items-center justify-between gap-6 px-4 md:h-20 md:px-10">
        <Link
          href="/"
          className="display text-[clamp(1.1rem,1.8vw,1.6rem)] leading-none tracking-[-0.03em] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--signal)]"
        >
          {tenant.name}
        </Link>

        <nav aria-label="Navegación principal" className="hidden items-center gap-8 md:flex">
          <Link className="label transition-opacity hover:opacity-60" href="/">
            Inicio
          </Link>
          <Link className="label transition-opacity hover:opacity-60" href="/collection">
            Colección
          </Link>
        </nav>

        <div className="label hidden text-[var(--muted)] md:block">Bogotá · COP</div>
        <Link
          href="/collection"
          className="label border border-[var(--ink)] px-3 py-2 transition-colors hover:bg-[var(--ink)] hover:text-[var(--surface)] md:hidden"
        >
          Ver colección
        </Link>
      </div>
    </header>
  );
}
