import Link from "next/link";

import { logout } from "@/app/login/actions";
import { NavLink } from "@/components/nav-link";
import { requireSession } from "@/lib/auth";

export const dynamic = "force-dynamic";

const NAV_SECTIONS: ReadonlyArray<{ group: string; links: ReadonlyArray<{ href: string; label: string }> }> = [
  {
    group: "Operaciones Core",
    links: [
      { href: "/", label: "Resumen" },
      { href: "/orders", label: "Pedidos" },
      { href: "/catalog/products", label: "Catálogo" },
      { href: "/media", label: "Media" },
    ],
  },
  {
    group: "Crecimiento & Canales",
    links: [
      { href: "/builder", label: "Builder" },
      { href: "/planes", label: "Planes" },
    ],
  },
  {
    group: "Infraestructura",
    links: [
      { href: "/audit", label: "Auditoría" },
      { href: "/platform/overview", label: "Panel" },
      { href: "/platform/tenants", label: "Plataforma · Tenants" },
      { href: "/ajustes", label: "Ajustes" },
    ],
  },
];

export default async function DashboardLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const { user } = await requireSession();

  return (
    <div className="min-h-screen bg-[#f5f5f3] lg:flex">
      <aside className="flex w-full flex-col border-r border-slate-200 bg-white lg:min-h-screen lg:w-64 lg:shrink-0">
        <div className="border-b border-slate-200 px-5 py-5">
          <Link href="/" className="block">
            <span className="mono text-[10px] uppercase tracking-[0.24em] text-orange-600">
              GrowUp Space
            </span>
            <span className="mt-1 block text-lg font-semibold tracking-tight text-slate-900">
              Backoffice
            </span>
          </Link>
        </div>

        <nav aria-label="Navegación principal" className="flex-1 py-4">
          {NAV_SECTIONS.map((section) => (
            <div key={section.group} className="pb-3">
              <p className="mono px-5 text-[10px] uppercase tracking-[0.2em] text-slate-400">
                {section.group}
              </p>
              <div className="mt-1 space-y-0.5">
                {section.links.map((link) => (
                  <NavLink key={link.href} href={link.href} label={link.label} />
                ))}
              </div>
            </div>
          ))}
        </nav>

        <div className="border-t border-slate-200 px-5 py-4">
          <p className="mono truncate text-[11px] text-slate-600">
            {user.email ?? user.id}
          </p>
          <form action={logout} className="mt-3">
            <button
              type="submit"
              className="mono text-[11px] uppercase tracking-[0.14em] text-slate-500 underline underline-offset-4 hover:text-slate-900"
            >
              Cerrar sesión
            </button>
          </form>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="border-b border-slate-200 bg-white px-4 py-3 lg:px-8">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="relative inline-flex h-2.5 w-2.5 items-center justify-center rounded-full">
                <span className="absolute h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              <p className="mono text-[11px] uppercase tracking-[0.18em] text-slate-500">
                Live
              </p>
            </div>
            <p className="mono text-[11px] text-slate-400">COP · Bogotá</p>
          </div>
        </header>

        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 lg:px-8 lg:py-8">
          {children}
        </main>
      </div>
    </div>
  );
}
