import Link from "next/link";

import { logout } from "@/app/login/actions";
import { NavLink } from "@/components/nav-link";
import { requireSession } from "@/lib/auth";

export const dynamic = "force-dynamic";

export default async function DashboardLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const { user } = await requireSession();

  return (
    <div className="min-h-screen bg-[#f6f6f4] lg:flex">
      <aside className="flex w-full flex-col bg-slate-950 lg:min-h-screen lg:w-64 lg:shrink-0">
        <div className="border-b border-white/10 px-5 py-5">
          <Link href="/" className="block">
            <span className="mono text-[10px] uppercase tracking-[0.24em] text-slate-500">
              Growup
            </span>
            <span className="mt-1 block text-lg font-semibold tracking-tight text-white">
              Backoffice
            </span>
          </Link>
        </div>

        <nav aria-label="Navegación principal" className="flex-1 py-4">
          <NavLink href="/" label="Resumen" />
          <NavLink href="/catalog/products" label="Catálogo" />
          <NavLink href="/media" label="Media" />
          <NavLink href="/audit" label="Auditoría" />
          <NavLink href="/platform/tenants" label="Plataforma · Tenants" />
        </nav>

        <div className="border-t border-white/10 px-5 py-4">
          <p className="mono truncate text-[11px] text-slate-400">
            {user.email ?? user.id}
          </p>
          <form action={logout} className="mt-3">
            <button
              type="submit"
              className="mono text-[11px] uppercase tracking-[0.14em] text-slate-500 underline underline-offset-4 hover:text-white"
            >
              Cerrar sesión
            </button>
          </form>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="border-b border-slate-200 bg-white px-4 py-4 lg:px-8">
          <div className="flex items-center justify-between gap-4">
            <p className="mono text-[11px] uppercase tracking-[0.18em] text-slate-500">
              Panel de operación
            </p>
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
