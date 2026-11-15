import { KpiCard } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";

export const dynamic = "force-dynamic";

const WEBHOOK_ENDPOINTS = [
  {
    id: "wh-wompi",
    event: "payment.wompi.transaction_updated",
    target: "https://api.growup.com/v1/webhooks/wompi",
    security: "SHA-256 Checksum + Timestamp + Inbox Idempotente",
    latency: "18ms",
    status: "active",
  },
  {
    id: "wh-stripe",
    event: "billing.stripe.invoice_paid",
    target: "https://api.growup.com/v1/webhooks/stripe",
    security: "Stripe-Signature HMAC-SHA256",
    latency: "22ms",
    status: "active",
  },
  {
    id: "wh-order-created",
    event: "order.created / order.paid / order.cancelled",
    target: "https://mitiendadeportiva.growupstore.app/wp-json/wc/v3/webhooks",
    security: "HMAC-SHA256 por Tenant + Outbox ARQ",
    latency: "12ms",
    status: "active",
  },
  {
    id: "wh-dian",
    event: "invoice.factus.cufe_validated",
    target: "https://api.growup.com/v1/webhooks/dian",
    security: "Bearer Token + Firma Proveedor DIAN",
    latency: "45ms",
    status: "trialing",
  },
];

export default function StaffApisPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Consola Staff · Conectividad & Contratos"
        title="APIs, Webhooks y Eventos de Plataforma"
        description="Supervisión del gateway FastAPI (/v1/*), contratos OpenAPI 3.1 tipados, cola de despacho Outbox ARQ y recepción firmada de pasarelas."
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Endpoints REST / OpenAPI" value="200 OK" detail="Contratos sincronizados con @growup/contracts" />
        <KpiCard label="Caché Edge Cloudflare" value="94.2%" detail="Hit ratio global en rutas públicas" />
        <KpiCard label="Latencia P95 API" value="38ms" detail="Pool asyncpg con SET LOCAL app.tenant_id" />
        <KpiCard label="Entregas Webhook 24h" value="99.98%" detail="Reintentos con backoff exponencial en ARQ" />
      </div>

      <div className="vn-card overflow-x-auto admin-scroll">
        <div className="flex items-center justify-between border-b border-black/10 px-5 py-4">
          <p className="mono text-[10px] font-bold text-[#525866]">REGISTRO DE WEBHOOKS Y ADAPTADORES EXTERNOS</p>
          <span className="mono text-xs font-bold text-[#0d0d0d]">Swagger / OpenAPI v3.1 Activo</span>
        </div>
        <table className="w-full text-left text-sm">
          <thead className="border-b border-black/10 bg-white/50 text-[11px] uppercase tracking-wider text-[#525866]">
            <tr>
              <th className="px-5 py-3.5">Evento / Canal</th>
              <th className="px-5 py-3.5">Endpoint Destino</th>
              <th className="px-5 py-3.5">Seguridad / Firma</th>
              <th className="px-5 py-3.5">Latencia</th>
              <th className="px-5 py-3.5">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-black/10">
            {WEBHOOK_ENDPOINTS.map((wh) => (
              <tr key={wh.id} className="hover:bg-black/[0.02]">
                <td className="mono px-5 py-4 text-xs font-semibold text-[#0d0d0d]">{wh.event}</td>
                <td className="mono px-5 py-4 text-xs text-[#525866]">{wh.target}</td>
                <td className="px-5 py-4 text-xs text-[#525866]">{wh.security}</td>
                <td className="mono px-5 py-4 text-xs font-bold text-[#0d0d0d]">{wh.latency}</td>
                <td className="px-5 py-4">
                  <StatusBadge value={wh.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
