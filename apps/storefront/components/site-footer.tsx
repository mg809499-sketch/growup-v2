import type { components } from "@growup/contracts";

type TenantPublic = components["schemas"]["TenantPublic"];

export function SiteFooter({ tenant }: { tenant: TenantPublic }) {
  return (
    <footer className="mt-24 border-t border-[var(--hairline)]">
      <div className="mx-auto flex max-w-[1440px] flex-col gap-8 px-4 py-10 md:flex-row md:items-end md:justify-between md:px-10">
        <div>
          <p className="display text-[clamp(1.8rem,4vw,3.4rem)] leading-none">
            {tenant.name}
          </p>
          <p className="label mt-4 text-[var(--muted)]">Bogotá · Colombia</p>
        </div>
        <div className="flex flex-col gap-2 text-sm text-[var(--muted)] md:items-end">
          <p>Envíos nacionales · COP</p>
          <p>© {new Date().getFullYear()} {tenant.name}. Todos los derechos reservados.</p>
          <p className="label">Growup commerce engine</p>
        </div>
      </div>
    </footer>
  );
}
