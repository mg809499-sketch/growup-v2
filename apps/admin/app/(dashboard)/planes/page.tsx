import { PageHeader } from "@/components/page-header";
import { PlanCard } from "@/components/plan-card";
import { requireSession } from "@/lib/auth";
import { apiGetSafe } from "@/lib/api";
import type { PlanOut } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function PlanesPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { token } = await requireSession();
  const { error } = await searchParams;
  const result = await apiGetSafe<PlanOut[]>("/v1/platform/plans", token);
  const plans = result.redirectToLogin ? [] : (result.data ?? []);

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Consola Staff · Monetización & Home Growup"
        title="Editor de Tarjetas de Planes (Home de Growup)"
        description="Crea y edita las tarjetas de planes que aparecen en el carrusel principal de growup.com. Controla badges, límites de SKUs, trial de 14 días, precios COP/USD y visibilidad."
      />

      {error ? (
        <p className="vn-card border-rose-300 px-4 py-3 text-sm text-rose-900">
          {error}
        </p>
      ) : null}

      <section className="vn-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-black/10 pb-4">
          <div>
            <p className="mono text-[10px] font-bold text-[#525866]">NUEVA TARJETA PARA EL CARRUSEL DE GROWUP.COM</p>
            <h2 className="display mt-1 text-lg font-bold text-[#0d0d0d]">
              Crear Nueva Tarjeta de Plan SaaS
            </h2>
          </div>
          <span className="rounded-full border border-black/15 bg-white px-3 py-1 text-xs font-semibold text-[#0d0d0d]">
            Sincronización directa con /planes en growup.com
          </span>
        </div>

        <form className="mt-5 grid gap-4 md:grid-cols-4">
          <label className="block text-xs font-medium text-[#525866]">
            Código único (slug)
            <input
              type="text"
              placeholder="ej. scale-ai"
              className="mt-1 w-full rounded-xl border border-black/15 bg-white/90 px-3 py-2 text-sm text-[#0d0d0d] placeholder:text-slate-400"
            />
          </label>
          <label className="block text-xs font-medium text-[#525866]">
            Título de la tarjeta
            <input
              type="text"
              placeholder="ej. Scale IA & Omnicanal"
              className="mt-1 w-full rounded-xl border border-black/15 bg-white/90 px-3 py-2 text-sm text-[#0d0d0d] placeholder:text-slate-400"
            />
          </label>
          <label className="block text-xs font-medium text-[#525866]">
            Precio mensual (COP)
            <input
              type="number"
              placeholder="249000"
              className="mt-1 w-full rounded-xl border border-black/15 bg-white/90 px-3 py-2 font-mono text-sm text-[#0d0d0d] placeholder:text-slate-400"
            />
          </label>
          <label className="block text-xs font-medium text-[#525866]">
            Badge superior
            <input
              type="text"
              placeholder="ej. NUEVO · IA 24/7"
              className="mt-1 w-full rounded-xl border border-black/15 bg-white/90 px-3 py-2 text-sm text-[#0d0d0d] placeholder:text-slate-400"
            />
          </label>
          <label className="block text-xs font-medium text-[#525866] md:col-span-3">
            Lista de beneficios (separados por coma)
            <input
              type="text"
              placeholder="Builder v3.0, Agente WhatsApp 24/7, Checkout Wompi 1-Click, Facturación DIAN..."
              className="mt-1 w-full rounded-xl border border-black/15 bg-white/90 px-3 py-2 text-sm text-[#0d0d0d] placeholder:text-slate-400"
            />
          </label>
          <div className="flex items-end">
            <button
              type="button"
              className="w-full rounded-xl bg-[#0d0d0d] px-4 py-2.5 text-xs font-bold text-white hover:bg-zinc-800"
            >
              + Publicar Tarjeta en Home
            </button>
          </div>
        </form>
      </section>

      {result.error ? (
        <p className="vn-card border-rose-300 px-4 py-3 text-sm text-rose-900">
          No se pudo cargar el catálogo de planes.
        </p>
      ) : (
        <div className="grid gap-6 lg:grid-cols-3">
          {plans.map((plan) => (
            <PlanCard key={plan.id} plan={plan} />
          ))}
        </div>
      )}
    </div>
  );
}
