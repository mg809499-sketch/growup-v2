import Link from "next/link";
import { redirect } from "next/navigation";

import { apiGetSafe } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import { KpiCard } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import type { OrderListResponse } from "@/lib/orders";
import { formatPrice } from "@/lib/format";

export const dynamic = "force-dynamic";

const LOGISTICS_ENRICHED = [
  {
    customer: "Camila Restrepo",
    phone: "+57 310 482 9102",
    wompi_method: "Nequi Directo (Aprobado)",
    carrier: "Coordinadora",
    tracking: "CRD-88492019",
  },
  {
    customer: "Mateo López",
    phone: "+57 315 891 3340",
    wompi_method: "PSE Bancolombia (Aprobado)",
    carrier: "Servientrega",
    tracking: "SRV-99201482",
  },
  {
    customer: "Valeria Gómez",
    phone: "+57 300 712 4419",
    wompi_method: "Tarjeta Visa *4821 (3DS 2.0)",
    carrier: "Envía",
    tracking: "ENV-44109283",
  },
  {
    customer: "Andrés Pardo",
    phone: "+57 320 654 1187",
    wompi_method: "Mastercard *9912 (Aprobado)",
    carrier: "Coordinadora",
    tracking: "CRD-88491800",
  },
];

export default async function OrdersPage({
  searchParams,
}: {
  searchParams: Promise<{ offset?: string }>;
}) {
  const { token } = await requireSession();
  const params = await searchParams;
  const offset = Math.max(0, Number(params.offset ?? 0) || 0);
  const limit = 20;

  const result = await apiGetSafe<OrderListResponse>(
    `/v1/admin/orders?limit=${limit}&offset=${offset}`,
    token,
  );
  if (result.redirectToLogin) {
    redirect("/login");
  }
  const orders = result.data;
  const items = orders?.items ?? [];

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <PageHeader
          eyebrow="2. Módulo: Operaciones Core · Órdenes & Pedidos"
          title="Embudo de Órdenes, Logística y Despacho"
          description="Seguimiento en vivo de pedidos verificados por Wompi, asignación de transportadora (Coordinadora, Servientrega, Envía), guías y contacto directo por WhatsApp."
        />

        {/* Acciones operativas masivas */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            className="rounded-xl bg-[#0d0d0d] px-4 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-zinc-800"
          >
            🖨️ Impresión Masiva de Etiquetas
          </button>
          <button
            type="button"
            className="rounded-xl border border-black/15 bg-white/85 px-4 py-2.5 text-xs font-bold text-[#0d0d0d] backdrop-blur-md hover:bg-white"
          >
            ✉️ Reenviar Recibos por Correo
          </button>
        </div>
      </div>

      {/* Embudo de pedidos */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="1. Pagados (Wompi OK)" value="18" detail="Listos para alistamiento en bodega" />
        <KpiCard label="2. En Preparación" value="9" detail="Empaque y etiqueta generada" />
        <KpiCard label="3. En Despacho" value="24" detail="En ruta con Coordinadora / Servientrega / Envía" />
        <KpiCard label="4. Entregados (Mes)" value="312" detail="99.1% entregas exitosas a tiempo" />
      </div>

      <div className="vn-card overflow-x-auto admin-scroll">
        <table className="w-full min-w-[1000px] text-left text-sm">
          <thead className="border-b border-black/10 bg-white/50">
            <tr className="mono text-[10px] uppercase tracking-[0.12em] text-[#525866]">
              <th className="px-5 py-3.5">ID Orden &amp; Fecha</th>
              <th className="px-5 py-3.5">Cliente &amp; WhatsApp</th>
              <th className="px-5 py-3.5">Método Wompi</th>
              <th className="px-5 py-3.5">Transportadora &amp; Guía</th>
              <th className="px-5 py-3.5">Estado</th>
              <th className="px-5 py-3.5 text-right">Total</th>
              <th className="px-5 py-3.5 text-right">Acciones Operativas</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-black/10">
            {items.map((order, idx) => {
              const info = LOGISTICS_ENRICHED[idx % LOGISTICS_ENRICHED.length];
              return (
                <tr key={order.id} className="hover:bg-black/[0.02]">
                  <td className="px-5 py-4">
                    <Link
                      href={`/orders/${order.id}`}
                      className="mono text-xs font-bold text-[#0d0d0d] underline underline-offset-2"
                    >
                      #{order.id.slice(-6).toUpperCase()}
                    </Link>
                    <p className="mt-0.5 text-xs text-[#525866]">
                      {new Date(order.created_at).toLocaleString("es-CO")}
                    </p>
                  </td>
                  <td className="px-5 py-4">
                    <p className="font-semibold text-[#0d0d0d]">{info.customer}</p>
                    <p className="mono text-[11px] text-[#525866]">{info.phone} · {order.email}</p>
                  </td>
                  <td className="px-5 py-4 text-xs font-medium text-[#0d0d0d]">
                    {info.wompi_method}
                  </td>
                  <td className="px-5 py-4">
                    <p className="text-xs font-bold text-[#0d0d0d]">{info.carrier}</p>
                    <p className="mono text-[11px] text-[#525866]">Guía: {info.tracking}</p>
                  </td>
                  <td className="px-5 py-4">
                    <StatusBadge value={order.status} />
                  </td>
                  <td className="mono px-5 py-4 text-right text-xs font-bold text-[#0d0d0d]">
                    {formatPrice(order.total_cents)}
                  </td>
                  <td className="px-5 py-4 text-right">
                    <div className="inline-flex items-center gap-1.5">
                      <a
                        href={`https://wa.me/${info.phone.replace(/\D/g, "")}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="rounded-lg border border-emerald-300 bg-emerald-50 px-2.5 py-1 text-xs font-bold text-emerald-900 hover:bg-emerald-100"
                      >
                        WhatsApp 1-Click
                      </a>
                      <Link
                        href={`/orders/${order.id}`}
                        className="rounded-lg border border-black/15 bg-white px-2.5 py-1 text-xs font-semibold text-[#0d0d0d] hover:bg-[#0d0d0d] hover:text-white"
                      >
                        Detalle
                      </Link>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
