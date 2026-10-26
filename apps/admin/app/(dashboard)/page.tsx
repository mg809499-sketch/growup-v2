import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { requireSession } from "@/lib/auth";
import { apiGet } from "@/lib/api";
import type { MeResponse } from "@/lib/api";

export default async function DashboardPage() {
  const { token } = await requireSession();
  const me = await apiGet<MeResponse>("/v1/admin/me", token);

  const cards = [
    { label: "Rol", value: me.role },
    {
      label: "Tenant",
      value: me.tenant_id ?? "plataforma",
    },
    { label: "Permisos", value: String(me.permissions.length) },
    { label: "Correo", value: me.email ?? "—" },
  ];

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Resumen"
        title="Estado de la cuenta"
        description="Sesión verificada con Supabase Auth y contexto resuelto desde la API multi-tenant."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <div key={card.label} className="border border-slate-200 bg-white p-5">
            <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">
              {card.label}
            </p>
            <p className="mono mt-3 break-all text-sm text-slate-950">
              {card.value}
            </p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Link
          href="/catalog/products"
          className="border border-slate-200 bg-white p-5 transition-colors hover:border-slate-950"
        >
          <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">
            Catálogo
          </p>
          <p className="mt-2 text-lg font-medium">Productos y variantes</p>
          <p className="mt-1 text-sm text-slate-500">
            Listado, precios, stock y media del tenant.
          </p>
        </Link>
        <Link
          href="/media"
          className="border border-slate-200 bg-white p-5 transition-colors hover:border-slate-950"
        >
          <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">
            Media
          </p>
          <p className="mt-2 text-lg font-medium">Biblioteca del tenant</p>
          <p className="mt-1 text-sm text-slate-500">
            Estado de procesamiento, alt text y variantes.
          </p>
        </Link>
        <Link
          href="/audit"
          className="border border-slate-200 bg-white p-5 transition-colors hover:border-slate-950"
        >
          <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">
            Auditoría
          </p>
          <p className="mt-2 text-lg font-medium">Decisiones y cadena</p>
          <p className="mt-1 text-sm text-slate-500">
            Historial de `decision_logs` y verificación de integridad.
          </p>
        </Link>
      </div>

      <div className="border border-slate-200 bg-white p-5">
        <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">
          Permisos activos
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {me.permissions.map((permission) => (
            <span
              key={permission}
              className="mono border border-slate-200 bg-slate-50 px-2 py-1 text-[10px] text-slate-600"
            >
              {permission}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
