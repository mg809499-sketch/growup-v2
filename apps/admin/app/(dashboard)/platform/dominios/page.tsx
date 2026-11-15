import { KpiCard } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";

export const dynamic = "force-dynamic";

const GLOBAL_DOMAINS = [
  {
    host: "ropa.growup.com",
    tenant: "Sol de Calle",
    type: "Subdominio Wildcard (*.growup.com)",
    tls: "TLS 1.3 Activo (Cloudflare Edge)",
    cwv: "99 / 100",
    status: "active",
  },
  {
    host: "joyeria.growup.com",
    tenant: "Aurélia Atelier",
    type: "Subdominio Wildcard (*.growup.com)",
    tls: "TLS 1.3 Activo (Cloudflare Edge)",
    cwv: "99 / 100",
    status: "active",
  },
  {
    host: "mitiendadeportiva.growupstore.app",
    tenant: "Mi Tienda Deportiva",
    type: "Subdominio Staging & Edge",
    tls: "TLS 1.3 Activo (Cloudflare Edge)",
    cwv: "99 / 100",
    status: "active",
  },
  {
    host: "estudio04.growup.com",
    tenant: "Estudio 04 · Denim & Archivo",
    type: "Subdominio Wildcard (*.growup.com)",
    tls: "TLS 1.3 Activo (Cloudflare Edge)",
    cwv: "98 / 100",
    status: "active",
  },
];

export default function StaffDominiosPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Consola Staff · Enrutamiento Edge"
        title="Manejo Global de Dominios y Certificados TLS"
        description="Resolución determinista Host → Tenant (app.resolve_tenant), estado de certificados Wildcard TLS 1.3 en Cloudflare Edge y propagación DNS global."
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Dominios Verificados" value="18 / 18" detail="100% con SSL TLS 1.3 estricto" />
        <KpiCard label="Puntos de Presencia" value="300+ PoPs" detail="Red Anycast Cloudflare Global" />
        <KpiCard label="Latencia Resolución Host" value="12ms" detail="Caché en memoria + función SECURITY DEFINER" />
        <KpiCard label="Protección Anti-DDoS" value="Ilimitada" detail="WAF activo y bloqueo de X-Tenant-ID falso" />
      </div>

      <div className="vn-card overflow-x-auto admin-scroll">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-black/10 bg-white/50 text-[11px] uppercase tracking-wider text-[#525866]">
            <tr>
              <th className="px-5 py-3.5">Host / Dominio</th>
              <th className="px-5 py-3.5">Tenant Asignado</th>
              <th className="px-5 py-3.5">Tipo de Enrutamiento</th>
              <th className="px-5 py-3.5">Certificado SSL</th>
              <th className="px-5 py-3.5">Core Web Vitals</th>
              <th className="px-5 py-3.5">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-black/10">
            {GLOBAL_DOMAINS.map((dom) => (
              <tr key={dom.host} className="hover:bg-black/[0.02]">
                <td className="mono px-5 py-4 text-xs font-bold text-[#0d0d0d]">{dom.host}</td>
                <td className="px-5 py-4 font-semibold text-[#0d0d0d]">{dom.tenant}</td>
                <td className="px-5 py-4 text-xs text-[#525866]">{dom.type}</td>
                <td className="px-5 py-4 text-xs font-semibold text-emerald-700">{dom.tls}</td>
                <td className="mono px-5 py-4 text-xs font-bold text-[#0d0d0d]">{dom.cwv}</td>
                <td className="px-5 py-4">
                  <StatusBadge value={dom.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
