import { KpiCard } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";

export const dynamic = "force-dynamic";

const DNS_RECORDS = [
  {
    type: "CNAME",
    name: "www.mitiendadeportiva.com",
    content: "edge.growupstore.app",
    ttl: "Auto (Proxied Cloudflare)",
    status: "active",
  },
  {
    type: "A",
    name: "@ (mitiendadeportiva.com)",
    content: "104.21.48.201 (Anycast Edge)",
    ttl: "Auto (Proxied Cloudflare)",
    status: "active",
  },
  {
    type: "TXT",
    name: "_growup-verification",
    content: "growup-tenant-verify=mitiendadeportiva-2026-ok",
    ttl: "3600s",
    status: "active",
  },
  {
    type: "TXT",
    name: "_dmarc / SPF / DKIM",
    content: "v=DMARC1; p=quarantine; rua=mailto:dmarc@growup.com",
    ttl: "3600s",
    status: "active",
  },
];

export default function DominioEdgePage() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="4. Módulo: Infraestructura & Finanzas · Dominio & Marca"
        title="Administrador de Dominios, Registros DNS y SSL TLS 1.3"
        description="Configuración de dominio principal (tutienda.com), subdominios (*.growup.com), propagación DNS en vivo en Edge y métricas Core Web Vitals."
      />

      {/* Métricas Core Web Vitals y Edge */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Velocidad Móvil (CWV)" value="99 / 100" detail="LCP 1.4s · CLS 0.01 · INP 48ms" />
        <KpiCard label="Latencia Global Edge" value="12ms" detail="Promedio global < 480ms en 300+ PoPs" />
        <KpiCard label="Certificado SSL" value="TLS 1.3 Estricto" detail="Renovación automática Zero-Downtime" />
        <KpiCard label="Protección Anti-DDoS" value="Activa 24/7" detail="Mitigación L3/L4/L7 ilimitada en borde" />
      </div>

      {/* Configurador de dominio principal y subdominio */}
      <section className="vn-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-black/10 pb-4">
          <div>
            <p className="mono text-[10px] font-bold text-[#525866]">CONFIGURADOR DE DOMINIOS DEL TENANT</p>
            <h2 className="display mt-1 text-lg font-bold text-[#0d0d0d]">
              Dominio Principal, Subdominio Oficial y Redirección 301
            </h2>
          </div>
          <span className="rounded-full border border-emerald-300 bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-900">
            Propagación Global Verificada
          </span>
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <label className="block text-xs font-medium text-[#525866]">
            Dominio Personalizado Principal
            <input
              type="text"
              defaultValue="mitiendadeportiva.com"
              className="mt-1 w-full rounded-xl border border-black/15 bg-white px-3 py-2 font-mono text-sm font-bold text-[#0d0d0d]"
            />
          </label>
          <label className="block text-xs font-medium text-[#525866]">
            Subdominio Edge Gestionado
            <input
              type="text"
              readOnly
              value="mitiendadeportiva.growupstore.app"
              className="mt-1 w-full rounded-xl border border-black/15 bg-slate-50 px-3 py-2 font-mono text-sm text-[#0d0d0d]"
            />
          </label>
          <div className="flex items-end">
            <button
              type="button"
              className="w-full rounded-xl bg-[#0d0d0d] px-4 py-2.5 text-xs font-bold text-white hover:bg-zinc-800"
            >
              Verificar Propagación DNS &amp; Purgar Edge
            </button>
          </div>
        </div>
      </section>

      {/* Tabla de registros DNS en vivo */}
      <div className="vn-card overflow-x-auto admin-scroll">
        <div className="border-b border-black/10 px-5 py-4">
          <p className="mono text-[10px] font-bold text-[#525866]">
            REGISTROS DNS EN VIVO (CNAME, A, TXT — CLOUDFLARE EDGE)
          </p>
        </div>
        <table className="w-full text-left text-sm">
          <thead className="border-b border-black/10 bg-white/50 text-[11px] uppercase tracking-wider text-[#525866]">
            <tr>
              <th className="px-5 py-3.5">Tipo</th>
              <th className="px-5 py-3.5">Nombre / Host</th>
              <th className="px-5 py-3.5">Contenido / Valor</th>
              <th className="px-5 py-3.5">TTL / Proxy</th>
              <th className="px-5 py-3.5">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-black/10">
            {DNS_RECORDS.map((rec) => (
              <tr key={rec.name} className="hover:bg-black/[0.02]">
                <td className="mono px-5 py-4 text-xs font-bold text-[#0d0d0d]">{rec.type}</td>
                <td className="mono px-5 py-4 text-xs font-semibold text-[#0d0d0d]">{rec.name}</td>
                <td className="mono px-5 py-4 text-xs text-[#525866]">{rec.content}</td>
                <td className="px-5 py-4 text-xs text-[#525866]">{rec.ttl}</td>
                <td className="px-5 py-4">
                  <StatusBadge value={rec.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
