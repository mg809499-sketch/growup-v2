import { KpiCard } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";

export const dynamic = "force-dynamic";

const STAFF_AGENTS = [
  {
    id: "ag-constructor-nova",
    name: "Constructor · Gemini 4 Argon",
    model: "opencode-go/gemini-4-argon#high",
    role: "Generación de código, bloques cerrados y migraciones",
    status: "active",
    resolution: "97.4%",
    latency: "0.9s",
    policy: "ALLOW con validación de contrato",
  },
  {
    id: "ag-arquitecto-kimi",
    name: "Arquitecto · Kimi K3.1 Pro",
    model: "opencode-go/kimi-k3.1-pro#high",
    role: "Diseño de contratos por dominio y fronteras modulares",
    status: "active",
    resolution: "99.1%",
    latency: "1.1s",
    policy: "ALLOW solo lectura / diseño",
  },
  {
    id: "ag-auditor-luna",
    name: "Auditor · GPT-6 Luna",
    model: "opencode-go/gpt-6-luna#high",
    role: "Auditoría de aislamiento RLS, PCI SAQ A y regresiones",
    status: "active",
    resolution: "98.8%",
    latency: "0.7s",
    policy: "DENY automático ante fuga cross-tenant",
  },
  {
    id: "ag-whatsapp-comercio",
    name: "Agente Comercial WhatsApp Business v2.5",
    model: "opencode-go/deepseek-v4.1-flash#high",
    role: "Atención 24/7 por tenant, consulta de stock y disparo de links Wompi",
    status: "active",
    resolution: "94.6%",
    latency: "0.8s",
    policy: "HANDOFF a humano en reembolsos o quejas",
  },
];

export default function StaffAgentesPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Consola Staff · OpenCode IA"
        title="Creación y Control Global de Agentes IA"
        description="Orquestación central de agentes OpenCode para los tenants: asignación de modelos LLM, límites de presupuesto (FinOps), políticas ALLOW / DENY / HANDOFF y supervisión en vivo."
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Estado del Motor IA" value="Activo 24/7" detail="4 clústeres de agentes en línea" />
        <KpiCard label="Resolución Autónoma" value="94.6%" detail="Sin intervención humana requerida" />
        <KpiCard label="Tiempo de Respuesta" value="0.9s" detail="Meta SLA < 1.2s cumplida" />
        <KpiCard label="Cadena de Auditoría" value="100% Válida" detail="Hash chain en decision_logs" />
      </div>

      <section className="vn-card p-6">
        <p className="mono text-[10px] font-bold text-[#525866]">NUEVO AGENTE EN EL CLUSTER</p>
        <h2 className="display mt-1 text-lg font-bold text-[#0d0d0d]">
          Desplegar Nuevo Agente OpenCode IA
        </h2>
        <form className="mt-4 grid gap-4 md:grid-cols-4">
          <label className="block text-xs font-medium text-[#525866]">
            Nombre del Agente
            <input
              type="text"
              placeholder="ej. Asesor Joyería VIP"
              className="mt-1 w-full rounded-xl border border-black/15 bg-white/90 px-3 py-2 text-sm text-[#0d0d0d]"
            />
          </label>
          <label className="block text-xs font-medium text-[#525866]">
            Modelo LLM Asignado
            <select className="mt-1 w-full rounded-xl border border-black/15 bg-white/90 px-3 py-2 text-sm text-[#0d0d0d]">
              <option value="opencode-go/gemini-4-argon#high">Gemini 4 Argon (High)</option>
              <option value="opencode-go/kimi-k3.1-pro#high">Kimi K3.1 Pro (High)</option>
              <option value="opencode-go/gpt-6-luna#high">GPT-6 Luna (Auditor)</option>
              <option value="opencode-go/deepseek-v4.1-flash#high">DeepSeek V4.1 Flash</option>
            </select>
          </label>
          <label className="block text-xs font-medium text-[#525866]">
            Política de Gobernanza
            <select className="mt-1 w-full rounded-xl border border-black/15 bg-white/90 px-3 py-2 text-sm text-[#0d0d0d]">
              <option value="HANDOFF">HANDOFF (Requiere aprobación humana)</option>
              <option value="ALLOW">ALLOW (Ejecución dentro de reglas)</option>
              <option value="DENY">DENY (Solo lectura y diagnóstico)</option>
            </select>
          </label>
          <div className="flex items-end">
            <button
              type="button"
              className="w-full rounded-xl bg-[#0d0d0d] px-4 py-2.5 text-xs font-bold text-white hover:bg-zinc-800"
            >
              + Crear y Activar Agente
            </button>
          </div>
        </form>
      </section>

      <div className="vn-card overflow-x-auto admin-scroll">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-black/10 bg-white/50 text-[11px] uppercase tracking-wider text-[#525866]">
            <tr>
              <th className="px-5 py-3.5">Agente</th>
              <th className="px-5 py-3.5">Modelo</th>
              <th className="px-5 py-3.5">Rol / Alcance</th>
              <th className="px-5 py-3.5">Resolución</th>
              <th className="px-5 py-3.5">Latencia</th>
              <th className="px-5 py-3.5">Política</th>
              <th className="px-5 py-3.5">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-black/10">
            {STAFF_AGENTS.map((agent) => (
              <tr key={agent.id} className="hover:bg-black/[0.02]">
                <td className="px-5 py-4 font-semibold text-[#0d0d0d]">{agent.name}</td>
                <td className="mono px-5 py-4 text-xs font-semibold text-[#0d0d0d]">{agent.model}</td>
                <td className="px-5 py-4 text-xs text-[#525866]">{agent.role}</td>
                <td className="mono px-5 py-4 text-xs font-bold text-[#0d0d0d]">{agent.resolution}</td>
                <td className="mono px-5 py-4 text-xs text-[#0d0d0d]">{agent.latency}</td>
                <td className="px-5 py-4 text-xs font-medium text-[#525866]">{agent.policy}</td>
                <td className="px-5 py-4">
                  <StatusBadge value={agent.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
