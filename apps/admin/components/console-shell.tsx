"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { NavLink } from "@/components/nav-link";

type NavGroup = {
  group: string;
  links: ReadonlyArray<{ href: string; label: string }>;
};

const STAFF_NAV: ReadonlyArray<NavGroup> = [
  {
    group: "Mando Global & Tenants",
    links: [
      { href: "/platform/overview", label: "Dashboard de Mando Global" },
      { href: "/platform/tenants", label: "Multi-tenants, Clientes y Tiendas" },
    ],
  },
  {
    group: "Monetización & Home Growup",
    links: [
      { href: "/planes", label: "Editor Tarjetas de Planes" },
      { href: "/platform/ventas", label: "Ventas · Tickets de Planes" },
      { href: "/platform/dominios", label: "Manejo de Dominios" },
    ],
  },
  {
    group: "Gobernanza & Ecosistema",
    links: [
      { href: "/platform/agentes", label: "Agentes OpenCode IA" },
      { href: "/platform/apis", label: "APIs & Webhooks" },
    ],
  },
];

const OWNER_NAV: ReadonlyArray<NavGroup> = [
  {
    group: "1. Portal Principal",
    links: [
      { href: "/builder", label: "Store & Web Builder v3.0" },
    ],
  },
  {
    group: "2. Operaciones Core",
    links: [
      { href: "/", label: "Dashboard Central" },
      { href: "/catalog/products", label: "Catálogo & Inventario" },
      { href: "/orders", label: "Órdenes & Pedidos" },
      { href: "/media", label: "Media & Activos CDN" },
    ],
  },
  {
    group: "3. Crecimiento & Canales",
    links: [
      { href: "/suggestions", label: "Agentes IA (OpenCode v2.5)" },
      { href: "/crecimiento/afiliados", label: "Red Aliada / Afiliados B2B" },
    ],
  },
  {
    group: "4. Infraestructura & Finanzas",
    links: [
      { href: "/infra/pagos", label: "Pasarelas & Pagos (Wompi)" },
      { href: "/infra/dominio", label: "Dominio & Marca (Cloudflare)" },
      { href: "/audit", label: "Ajustes & Configuración" },
    ],
  },
];

export function ConsoleShell({
  userEmail,
  preview,
  logoutAction,
  children,
}: {
  userEmail: string;
  preview: boolean;
  logoutAction: () => Promise<void>;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isStaffConsole =
    pathname.startsWith("/platform") || pathname.startsWith("/planes");

  const activeNav = isStaffConsole ? STAFF_NAV : OWNER_NAV;

  return (
    <div className="min-h-screen text-[#0d0d0d] lg:flex">
      {/* Sidebar glassmorphic blanca con bordes redondeados */}
      <aside className="flex w-full flex-col border-b border-black/10 bg-white/75 backdrop-blur-xl lg:min-h-screen lg:w-[296px] lg:shrink-0 lg:border-b-0 lg:border-r">
        <div className="border-b border-black/10 px-5 py-5">
          {/* Conmutador entre las 2 consolas separadas por rol */}
          <div className="mb-4 grid grid-cols-2 gap-1.5 rounded-2xl border border-black/10 bg-slate-100/80 p-1">
            <Link
              href="/"
              className={`rounded-xl px-2.5 py-2 text-center text-[11px] font-bold transition-all ${
                !isStaffConsole
                  ? "bg-[#0d0d0d] text-white shadow-sm"
                  : "text-[#525866] hover:text-[#0d0d0d]"
              }`}
            >
              Consola Cliente
            </Link>
            <Link
              href="/platform/overview"
              className={`rounded-xl px-2.5 py-2 text-center text-[11px] font-bold transition-all ${
                isStaffConsole
                  ? "bg-[#0d0d0d] text-white shadow-sm"
                  : "text-[#525866] hover:text-[#0d0d0d]"
              }`}
            >
              Consola Staff
            </Link>
          </div>

          <Link href={isStaffConsole ? "/platform/overview" : "/"} className="block">
            <span className="mono text-[10px] font-semibold tracking-[0.2em] text-[#525866]">
              {isStaffConsole ? "ROL: STAFF / ALL-IN-ONE" : "ROL: CLIENTE / OWNER TENANT"}
            </span>
            <span className="display mt-1 block text-xl font-extrabold tracking-tight text-[#0d0d0d]">
              {isStaffConsole ? "growup. staff" : "growup. store"}
            </span>
            <span className="mt-1 block text-xs text-[#525866]">
              {isStaffConsole
                ? "Mando global multi-tenant, planes y agentes"
                : "Portal Builder v3.0, operaciones, IA y Wompi"}
            </span>
          </Link>
        </div>

        <nav aria-label="Navegación de consola" className="admin-scroll flex-1 overflow-y-auto px-3 py-4">
          {activeNav.map((section) => (
            <div key={section.group} className="pb-4">
              <p className="mono px-3 py-1 text-[10px] font-semibold tracking-[0.16em] text-[#525866]">
                {section.group}
              </p>
              <div className="mt-1 space-y-1">
                {section.links.map((link) => (
                  <NavLink key={link.href} href={link.href} label={link.label} />
                ))}
              </div>
            </div>
          ))}
        </nav>

        <div className="border-t border-black/10 bg-white/60 px-5 py-4">
          <div className="flex items-center justify-between gap-2">
            <span className="mono truncate text-[11px] font-semibold text-[#0d0d0d]">
              {userEmail}
            </span>
            <span className="rounded-full border border-black/15 bg-white px-2.5 py-0.5 text-[10px] font-bold text-[#0d0d0d]">
              {isStaffConsole ? "STAFF" : "OWNER"}
            </span>
          </div>
          <p className="mono mt-1 text-[10px] text-[#525866]">
            PostgreSQL FORCE RLS · sa-east-1
          </p>
          <form action={logoutAction} className="mt-3">
            <button
              type="submit"
              className="w-full rounded-xl border border-black/15 bg-white/80 px-3 py-2 text-xs font-bold text-[#0d0d0d] hover:bg-[#0d0d0d] hover:text-white"
            >
              Salir de la consola
            </button>
          </form>
        </div>
      </aside>

      {/* Área principal blanca con tarjetas glassmorphic */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 border-b border-black/10 bg-white/75 px-4 py-3.5 backdrop-blur-xl lg:px-8">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="inline-flex items-center gap-2 rounded-full border border-black/10 bg-white/90 px-3 py-1 text-xs font-semibold text-[#0d0d0d] shadow-xs">
                <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
                {isStaffConsole
                  ? "Cluster Multi-Tenant Conectado"
                  : "Conectado a Edge & Wompi Live (12ms)"}
              </span>
              {preview ? (
                <span className="mono hidden rounded-full border border-black/10 bg-slate-100 px-2.5 py-1 text-[10px] font-semibold text-[#525866] sm:inline-block">
                  VISTA DE DISEÑO LOCAL
                </span>
              ) : null}
            </div>

            <div className="flex items-center gap-2.5">
              {!isStaffConsole ? (
                <Link
                  href="/builder"
                  className="rounded-xl bg-[#0d0d0d] px-4 py-2 text-xs font-bold text-white shadow-sm hover:bg-zinc-800"
                >
                  Abrir Store Builder v3.0
                </Link>
              ) : (
                <Link
                  href="/planes"
                  className="rounded-xl bg-[#0d0d0d] px-4 py-2 text-xs font-bold text-white shadow-sm hover:bg-zinc-800"
                >
                  Editar Tarjetas de Planes →
                </Link>
              )}
              <a
                href="http://localhost:3003"
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-xl border border-black/15 bg-white/80 px-3.5 py-2 text-xs font-bold text-[#0d0d0d] backdrop-blur-md hover:bg-white"
              >
                Ver Home Growup ↗
              </a>
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1440px] flex-1 px-4 py-6 lg:px-8 lg:py-8">
          {children}
        </main>
      </div>
    </div>
  );
}
