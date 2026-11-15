import Link from "next/link";
import { redirect } from "next/navigation";

import { KpiCard } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { requireSession } from "@/lib/auth";
import { apiGetSafe } from "@/lib/api";
import type { MeResponse } from "@/lib/api";

const LIVE_FEED_ORDERS = [
  {
    id: "ORD-9041",
    customer: "Camila Restrepo",
    method: "Wompi · Nequi Directo",
    amount: "$ 189.900 COP",
    settlement: "Liquidación inmediata",
    status: "paid",
    time: "Hace 2 min",
  },
  {
    id: "ORD-9040",
    customer: "Mateo López",
    method: "Wompi · PSE Bancolombia",
    amount: "$ 473.000 COP",
    settlement: "Liquidación T+1",
    status: "preparing",
    time: "Hace 14 min",
  },
  {
    id: "ORD-9039",
    customer: "Valeria Gómez",
    method: "Wompi · Visa *4821 (3DS 2.0)",
    amount: "$ 490.000 COP",
    settlement: "Liquidación inmediata",
    status: "shipped",
    time: "Hace 38 min",
  },
  {
    id: "ORD-9038",
    customer: "Andrés Pardo",
    method: "Wompi · Mastercard *9912",
    amount: "$ 144.000 COP",
    settlement: "Liquidado en cuenta",
    status: "delivered",
    time: "Hace 1 hora",
  },
];

export default async function DashboardPage() {
  const { token } = await requireSession();
  const result = await apiGetSafe<MeResponse>("/v1/admin/me", token);
  if (result.redirectToLogin) {
    redirect("/login");
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <PageHeader
          eyebrow="2. Módulo: Operaciones Core · Dashboard Central"
          title="Dashboard Central del Comercio"
          description="Gestión diaria, transaccional y analítica del negocio en tiempo real: ingresos recurrentes, GMV en COP y USD, conversión de checkout y aprobación Wompi."
        />

        {/* Accesos rápidos */}
        <div className="flex flex-wrap items-center gap-2.5">
          <Link
            href="/catalog/products/new"
            className="rounded-xl bg-[#0d0d0d] px-4 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-zinc-800"
          >
            + Crear Nuevo Producto
          </Link>
          <Link
            href="/audit"
            className="rounded-xl border border-black/15 bg-white/80 px-4 py-2.5 text-xs font-bold text-[#0d0d0d] backdrop-blur-md hover:bg-white"
          >
            Exportar Reporte Fiscal DIAN
          </Link>
          <Link
            href="/audit#webhooks"
            className="rounded-xl border border-black/15 bg-white/80 px-4 py-2.5 text-xs font-bold text-[#0d0d0d] backdrop-blur-md hover:bg-white"
          >
            Conectar Nuevo Webhook
          </Link>
        </div>
      </div>

      {/* Tarjetas KPI en tiempo real */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="MRR SaaS / Ingresos Recurrentes"
          value="$ 18.450.000"
          detail="+24.2% vs. mes anterior · Suscripciones y recompras"
        />
        <KpiCard
          label="GMV Transaccional (COP / USD)"
          value="$ 64.890.000"
          detail="Equivalente: $ 15.820 USD procesados este mes"
        />
        <KpiCard
          label="Pedidos Hoy & Conversión"
          value="34 órdenes"
          detail="4.8% carritos completados (+0.9% con Wompi 1-Click)"
        />
        <KpiCard
          label="Tasa de Aprobación Wompi"
          value="98.7%"
          detail="Monitoreo sin rechazos bancarios en PSE / Nequi / 3DS"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-12">
        {/* Gráfica interactiva de rendimiento temporal */}
        <section className="vn-card flex flex-col justify-between p-6 lg:col-span-7">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="mono text-[10px] font-bold text-[#525866]">
                CURVA DE VENTAS ACUMULADAS (DÍA · SEMANA · MES)
              </p>
              <h2 className="display mt-1 text-lg font-bold text-[#0d0d0d]">
                Rendimiento Temporal y Picos de Tráfico
              </h2>
            </div>
            <div className="flex gap-1.5 rounded-xl border border-black/10 bg-slate-100/80 p-1 text-xs font-bold">
              <span className="rounded-lg bg-[#0d0d0d] px-2.5 py-1 text-white">Mes</span>
              <span className="px-2.5 py-1 text-[#525866]">Semana</span>
              <span className="px-2.5 py-1 text-[#525866]">Día</span>
            </div>
          </div>

          <div className="mt-6 grid h-52 grid-cols-12 items-end gap-2.5 border-b border-black/10 pt-6">
            {[28, 35, 42, 39, 54, 62, 71, 66, 79, 85, 92, 100].map((v, i) => (
              <div key={i} className="flex h-full flex-col items-center justify-end gap-2">
                <div
                  style={{ height: `${v}%` }}
                  className="w-full rounded-t-xl bg-[#0d0d0d] transition-all hover:opacity-75"
                  title={`Semana ${i + 1}: ${v}%`}
                />
                <span className="mono text-[9px] font-semibold text-[#525866]">S{i + 1}</span>
              </div>
            ))}
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-2 text-xs text-[#525866]">
            <span>Pico máximo: Drop 04 (viernes 20:00 COT · 142 req/s)</span>
            <span className="mono font-bold text-[#0d0d0d]">Ticket promedio: $ 214.500 COP</span>
          </div>
        </section>

        {/* Feed de órdenes en tiempo real */}
        <section className="vn-card flex flex-col justify-between p-6 lg:col-span-5">
          <div className="flex items-center justify-between border-b border-black/10 pb-3">
            <div>
              <p className="mono text-[10px] font-bold text-[#525866]">TRANSACCIONES ENTRANTES</p>
              <h2 className="display mt-1 text-lg font-bold text-[#0d0d0d]">
                Feed de Órdenes en Tiempo Real
              </h2>
            </div>
            <Link href="/orders" className="text-xs font-bold text-[#0d0d0d] underline underline-offset-4">
              Ver todas →
            </Link>
          </div>

          <ul className="my-4 divide-y divide-black/10">
            {LIVE_FEED_ORDERS.map((ord) => (
              <li key={ord.id} className="flex items-center justify-between gap-3 py-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="mono text-xs font-bold text-[#0d0d0d]">{ord.id}</span>
                    <span className="text-sm font-semibold text-[#0d0d0d]">{ord.customer}</span>
                  </div>
                  <p className="mt-0.5 text-xs text-[#525866]">
                    {ord.method} · {ord.settlement}
                  </p>
                </div>
                <div className="text-right">
                  <p className="mono text-xs font-bold text-[#0d0d0d]">{ord.amount}</p>
                  <div className="mt-1 flex items-center justify-end gap-1.5">
                    <StatusBadge value={ord.status} />
                  </div>
                </div>
              </li>
            ))}
          </ul>

          <div className="rounded-xl border border-black/10 bg-slate-50/90 px-3.5 py-2.5 text-xs text-[#525866]">
            Liquidación automática activa en cuenta bancaria verificada.
          </div>
        </section>
      </div>
    </div>
  );
}
