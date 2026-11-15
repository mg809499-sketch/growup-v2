import { KpiCard } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";

export const dynamic = "force-dynamic";

const SUPERVISED_CHATS = [
  {
    id: "chat-01",
    customer: "Laura Méndez (+57 314 220 9182)",
    query: "¿Tienen la Chaqueta Valkyrie Pro en talla M para envío hoy a Medellín?",
    agent_reply:
      "¡Hola Laura! Sí, tenemos 14 unidades disponibles en talla M. Te comparto tu link de pago directo Wompi (PSE/Nequi/Tarjetas): https://checkout.wompi.co/l/valkyrie-m",
    status: "ALLOW",
    time: "Hace 3 min · Resuelto en 0.8s",
  },
  {
    id: "chat-02",
    customer: "Carlos Ruiz (+57 301 558 1920)",
    query: "Necesito cambiar la talla de mi pedido #ORD-9038 por una L.",
    agent_reply:
      "He validado tu pedido #ORD-9038 dentro de los 30 días de cambio. Paso la conversación a un operador humano para generar tu guía de recogida sin costo.",
    status: "HANDOFF",
    time: "Hace 18 min · Escalado a humano",
  },
];

export default function SuggestionsPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="3. Módulo: Crecimiento & Canales · Agentes IA (OpenCode Engine v2.5)"
        title="Agentes IA & Automatización WhatsApp Business"
        description="Monitor del agente en vivo 24/7, consola de entrenamiento documental (PDF, FAQs, catálogo), simulador de chat WhatsApp con links de pago Wompi y supervisión humana."
      />

      {/* Monitor del agente */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Estado del Agente"
          value="Activo 24/7"
          detail="OpenCode Engine v2.5 en línea"
        />
        <KpiCard
          label="Tasa Resolución Autónoma"
          value="94.6%"
          detail="Consultas de stock, tallas y checkout cerradas sin humano"
        />
        <KpiCard
          label="Tiempo Medio Respuesta"
          value="0.9s"
          detail="Meta operativa < 1.2s cumplida"
        />
        <KpiCard
          label="Ventas Cerradas por IA (Mes)"
          value="$ 14.280.000"
          detail="Links Wompi disparados dentro de WhatsApp"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-12">
        {/* Consola de entrenamiento */}
        <section className="vn-card space-y-4 p-6 lg:col-span-6">
          <div className="border-b border-black/10 pb-3">
            <p className="mono text-[10px] font-bold text-[#525866]">BASE DE CONOCIMIENTO DEL LLM</p>
            <h2 className="display mt-1 text-lg font-bold text-[#0d0d0d]">
              Consola de Entrenamiento (PDF, Políticas, Catálogo y FAQs)
            </h2>
          </div>

          <div className="space-y-3">
            <label className="block text-xs font-medium text-[#525866]">
              URL del Catálogo / Sitemap Sincronizado
              <input
                type="url"
                defaultValue="https://mitiendadeportiva.growupstore.app/sitemap.xml"
                className="mt-1 w-full rounded-xl border border-black/15 bg-white px-3 py-2 font-mono text-xs text-[#0d0d0d]"
              />
            </label>
            <label className="block text-xs font-medium text-[#525866]">
              Políticas de Cambios, Garantías y FAQs
              <textarea
                rows={4}
                defaultValue={
                  "1. Envíos gratis nacionales con el cupón GROWUP2025.\n2. Cambios de talla sin costo dentro de los primeros 30 días.\n3. Pagos verificados únicamente por link oficial Wompi (PSE, Nequi, Bancolombia y Tarjetas)."
                }
                className="mt-1 w-full rounded-xl border border-black/15 bg-white p-3 text-xs leading-relaxed text-[#0d0d0d]"
              />
            </label>
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-dashed border-black/20 bg-white/70 p-4">
              <div>
                <p className="text-xs font-bold text-[#0d0d0d]">
                  📄 Manuales PDF y Fichas Técnicas Cargadas (3 archivos)
                </p>
                <p className="text-[11px] text-[#525866]">
                  guia-tallas-2025.pdf · politica-devoluciones-dian.pdf · catalogo-woo.pdf
                </p>
              </div>
              <button
                type="button"
                className="rounded-xl bg-[#0d0d0d] px-4 py-2 text-xs font-bold text-white hover:bg-zinc-800"
              >
                + Subir PDF / Re-entrenar
              </button>
            </div>
          </div>
        </section>

        {/* Integración WhatsApp Business + Simulador con disparador Wompi */}
        <section className="vn-card space-y-4 p-6 lg:col-span-6">
          <div className="flex items-center justify-between border-b border-black/10 pb-3">
            <div>
              <p className="mono text-[10px] font-bold text-[#525866]">CANAL CONVERSACIONAL EN VIVO</p>
              <h2 className="display mt-1 text-lg font-bold text-[#0d0d0d]">
                WhatsApp Business (QR + Simulador de Pago Wompi)
              </h2>
            </div>
            <span className="rounded-full border border-emerald-300 bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-900">
              QR Vinculado · Webhook OK
            </span>
          </div>

          <div className="grid gap-4 sm:grid-cols-12">
            <div className="flex flex-col items-center justify-center rounded-2xl border border-black/10 bg-white p-4 text-center sm:col-span-4">
              <div className="grid h-24 w-24 grid-cols-4 gap-1 rounded-xl border border-black/15 bg-slate-100 p-2">
                {Array.from({ length: 16 }).map((_, i) => (
                  <div
                    key={i}
                    className={`rounded-xs ${i % 3 === 0 ? "bg-[#0d0d0d]" : "bg-slate-300"}`}
                  />
                ))}
              </div>
              <p className="mono mt-2 text-[10px] font-bold text-[#0d0d0d]">WHATSAPP QR SYNC</p>
              <p className="text-[10px] text-[#525866]">+57 300 912 4400</p>
            </div>

            <div className="flex flex-col justify-between rounded-2xl border border-black/10 bg-slate-50/90 p-4 sm:col-span-8">
              <div className="space-y-2 text-xs">
                <div className="rounded-xl border border-black/10 bg-white p-2.5 text-[#0d0d0d]">
                  <strong>Cliente:</strong> Quiero comprar la Chaqueta Valkyrie en talla M con Nequi.
                </div>
                <div className="rounded-xl border border-emerald-300 bg-emerald-50/90 p-2.5 text-[#0d0d0d]">
                  <strong>OpenCode IA:</strong> ¡Separada tu unidad! Paga en 1-click aquí:{" "}
                  <span className="mono underline">wompi.co/l/valkyrie-m</span> ($189.900 COP).
                </div>
              </div>
              <div className="mt-3 flex gap-2">
                <button
                  type="button"
                  className="flex-1 rounded-xl bg-[#0d0d0d] px-3 py-2 text-xs font-bold text-white hover:bg-zinc-800"
                >
                  ⚡ Disparar Link de Pago Wompi en Chat
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Historial de conversaciones supervisadas */}
      <section className="vn-card overflow-hidden">
        <div className="flex items-center justify-between border-b border-black/10 px-5 py-4">
          <p className="mono text-[10px] font-bold text-[#525866]">
            HISTORIAL DE CONVERSACIONES SUPERVISADAS (INTERVENCIÓN HUMANA 1-CLICK)
          </p>
        </div>
        <div className="divide-y divide-black/10">
          {SUPERVISED_CHATS.map((chat) => (
            <div key={chat.id} className="flex flex-wrap items-start justify-between gap-4 p-5">
              <div className="max-w-3xl space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-[#0d0d0d]">{chat.customer}</span>
                  <span className="mono text-[10px] text-[#525866]">{chat.time}</span>
                  <StatusBadge value={chat.status} />
                </div>
                <p className="text-xs text-[#525866]">
                  <strong className="text-[#0d0d0d]">Cliente:</strong> “{chat.query}”
                </p>
                <p className="text-xs text-[#0d0d0d]">
                  <strong>Agente OpenCode:</strong> {chat.agent_reply}
                </p>
              </div>
              <button
                type="button"
                className="rounded-xl border border-black/15 bg-white px-3.5 py-2 text-xs font-bold text-[#0d0d0d] hover:bg-[#0d0d0d] hover:text-white"
              >
                Intervenir Manualmente
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
