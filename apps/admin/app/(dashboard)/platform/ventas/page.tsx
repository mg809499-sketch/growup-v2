import { KpiCard } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { formatPrice } from "@/lib/format";

export const dynamic = "force-dynamic";

const PLAN_TICKETS = [
  {
    ticket_id: "TCK-2026-0891",
    tenant: "Sol de Calle",
    slug: "ropa.growup.com",
    plan: "Pro Multi-Canal & IA",
    amount_cents: 12_900_000,
    gateway: "Stripe Billing · Visa *4242",
    dian_ref: "FE-90142",
    status: "paid",
    date: "15 Nov 2026 · 09:12",
  },
  {
    ticket_id: "TCK-2026-0890",
    tenant: "Aurélia Atelier",
    slug: "joyeria.growup.com",
    plan: "Pro Multi-Canal & IA",
    amount_cents: 12_900_000,
    gateway: "Stripe Billing · Mastercard *8810",
    dian_ref: "FE-90141",
    status: "paid",
    date: "14 Nov 2026 · 16:40",
  },
  {
    ticket_id: "TCK-2026-0889",
    tenant: "Estudio 04 · Denim & Archivo",
    slug: "estudio04.growup.com",
    plan: "Pro Multi-Canal & IA",
    amount_cents: 12_900_000,
    gateway: "PSE Bancolombia · Wompi",
    dian_ref: "FE-90140",
    status: "paid",
    date: "12 Nov 2026 · 11:05",
  },
  {
    ticket_id: "TCK-2026-0888",
    tenant: "Mi Tienda Deportiva",
    slug: "mitiendadeportiva.growupstore.app",
    plan: "Starter Editorial (Trial 14d)",
    amount_cents: 4_900_000,
    gateway: "Trial Activo · Nequi Pre-aprobado",
    dian_ref: "PENDIENTE-TRIAL",
    status: "trialing",
    date: "12 Nov 2026 · 09:15",
  },
];

export default function StaffVentasPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Consola Staff · Facturación SaaS"
        title="Ventas · Tickets de Ventas de los Planes"
        description="Registro en vivo de los tickets de suscripción a los planes de Growup contratados por los comercios, método de cobro y comprobante electrónico."
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Tickets Emitidos (Mes)" value="18" detail="14 pagados · 3 en trial · 1 pendiente" />
        <KpiCard label="Recaudo Planes COP" value="$ 2.480.000" detail="Cobro recurrente automatizado" />
        <KpiCard label="Conversión de Trial" value="88.5%" detail="Trial de 14 días a plan activo" />
        <KpiCard label="Disputas / Contracargos" value="0" detail="0.0% en los últimos 90 días" />
      </div>

      <div className="vn-card overflow-x-auto admin-scroll">
        <div className="flex items-center justify-between border-b border-black/10 px-5 py-4">
          <p className="mono text-[10px] font-bold text-[#525866]">HISTORIAL DE TICKETS DE SUSCRIPCIÓN A PLANES GROWUP</p>
        </div>
        <table className="w-full text-left text-sm">
          <thead className="border-b border-black/10 bg-white/50 text-[11px] uppercase tracking-wider text-[#525866]">
            <tr>
              <th className="px-5 py-3.5">Ticket ID</th>
              <th className="px-5 py-3.5">Comerciante / Tienda</th>
              <th className="px-5 py-3.5">Plan Contratado</th>
              <th className="px-5 py-3.5">Monto</th>
              <th className="px-5 py-3.5">Pasarela / Método</th>
              <th className="px-5 py-3.5">Factura DIAN</th>
              <th className="px-5 py-3.5">Fecha</th>
              <th className="px-5 py-3.5">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-black/10">
            {PLAN_TICKETS.map((ticket) => (
              <tr key={ticket.ticket_id} className="hover:bg-black/[0.02]">
                <td className="mono px-5 py-4 text-xs font-bold text-[#0d0d0d]">{ticket.ticket_id}</td>
                <td className="px-5 py-4">
                  <p className="font-semibold text-[#0d0d0d]">{ticket.tenant}</p>
                  <p className="mono text-[10px] text-[#525866]">{ticket.slug}</p>
                </td>
                <td className="px-5 py-4 font-semibold text-[#0d0d0d]">{ticket.plan}</td>
                <td className="mono px-5 py-4 font-bold text-[#0d0d0d]">{formatPrice(ticket.amount_cents)}</td>
                <td className="px-5 py-4 text-xs text-[#525866]">{ticket.gateway}</td>
                <td className="mono px-5 py-4 text-xs text-[#0d0d0d]">{ticket.dian_ref}</td>
                <td className="px-5 py-4 text-xs text-[#525866]">{ticket.date}</td>
                <td className="px-5 py-4">
                  <StatusBadge value={ticket.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
