import { KpiCard } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";

export const dynamic = "force-dynamic";

const ALLIED_BRANDS = [
  {
    name: "Sol de Calle · Estudio 04",
    category: "Streetwear & Denim Pesado (450 GSM)",
    commission: "25% por venta cruzada",
    catalog_skus: "32 SKUs verificados",
    settlement: "Transferencia automática Wompi Split",
    status: "active",
  },
  {
    name: "Aurélia Atelier · Bogotá",
    category: "Alta Joyería & Piezas de Autor",
    commission: "18% por venta cruzada",
    catalog_skus: "19 SKUs verificados",
    settlement: "Liquidación semanal ACH",
    status: "active",
  },
  {
    name: "Kinetix Performance Lab",
    category: "Accesorios e Hidratación Deportiva",
    commission: "35% por venta cruzada",
    catalog_skus: "54 SKUs verificados",
    settlement: "Transferencia automática",
    status: "active",
  },
  {
    name: "Andes Outdoor Gear",
    category: "Impermeables & Trail Running",
    commission: "22% por venta cruzada",
    catalog_skus: "41 SKUs verificados",
    settlement: "Transferencia automática",
    status: "active",
  },
];

export default function AfiliadosPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="3. Módulo: Crecimiento & Canales · Red Aliada / Afiliados B2B"
        title="Red Aliada & Cross-Selling Post-Compra B2B"
        description="Directorio mayorista de +140 marcas aliadas verificadas con comisión pactada (15% a 35%). Sugiere productos complementarios en el checkout sin requerir inventario propio."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Marcas Aliadas Conectadas" value="146 Marcas" detail="Catálogo mayorista verificado en Colombia" />
        <KpiCard label="Margen Comisión Pactado" value="15% a 35%" detail="Sin costo de inventario ni bodegaje" />
        <KpiCard label="Ingresos Cross-Selling" value="$ 4.820.000" detail="Comisiones ganadas en el último mes" />
        <KpiCard label="Próxima Liquidación ACH" value="$ 1.290.000" detail="Programada a cuenta corriente Bancolombia" />
      </div>

      {/* Gestor de Cross-Selling en Checkout Post-Compra */}
      <section className="vn-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-black/10 pb-4">
          <div>
            <p className="mono text-[10px] font-bold text-[#525866]">REGLA DE UPSELL &amp; CROSS-SELLING POST-COMPRA</p>
            <h2 className="display mt-1 text-lg font-bold text-[#0d0d0d]">
              Gestor de Sugerencias Automáticas en Checkout
            </h2>
          </div>
          <span className="rounded-full border border-emerald-300 bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-900">
            Activo en Checkout Express Wompi
          </span>
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-black/10 bg-white/90 p-4">
            <p className="mono text-[10px] font-bold text-[#525866]">CUANDO EL CLIENTE COMPRA</p>
            <p className="mt-1 font-bold text-[#0d0d0d]">Chaqueta Deportiva Valkyrie Pro</p>
            <p className="mt-1 text-xs text-[#525866]">Categoría: Alto Rendimiento</p>
          </div>
          <div className="rounded-2xl border border-black/10 bg-white/90 p-4">
            <p className="mono text-[10px] font-bold text-[#525866]">SUGERIR EN 1-CLICK (SIN INVENTARIO PROPIO)</p>
            <p className="mt-1 font-bold text-[#0d0d0d]">Termo Isotérmico Kinetix + Gorra Trail</p>
            <p className="mt-1 text-xs font-semibold text-emerald-800">Tu comisión neta: 30% ($ 38.700 COP)</p>
          </div>
          <div className="rounded-2xl border border-black/10 bg-white/90 p-4">
            <p className="mono text-[10px] font-bold text-[#525866]">DESPACHO &amp; LIQUIDACIÓN</p>
            <p className="mt-1 font-bold text-[#0d0d0d]">Fulfillment directo por la marca aliada</p>
            <p className="mt-1 text-xs text-[#525866]">Guía generada automáticamente al aprobar pago</p>
          </div>
        </div>
      </section>

      {/* Directorio de marcas conectadas */}
      <div className="vn-card overflow-x-auto admin-scroll">
        <div className="border-b border-black/10 px-5 py-4">
          <p className="mono text-[10px] font-bold text-[#525866]">
            DIRECTORIO DE MARCAS ALIADAS VERIFICADAS (+140 COMERCIOS B2B)
          </p>
        </div>
        <table className="w-full text-left text-sm">
          <thead className="border-b border-black/10 bg-white/50 text-[11px] uppercase tracking-wider text-[#525866]">
            <tr>
              <th className="px-5 py-3.5">Marca Aliada</th>
              <th className="px-5 py-3.5">Vertical / Categoría</th>
              <th className="px-5 py-3.5">Comisión Pactada</th>
              <th className="px-5 py-3.5">Catálogo Disponible</th>
              <th className="px-5 py-3.5">Liquidación</th>
              <th className="px-5 py-3.5">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-black/10">
            {ALLIED_BRANDS.map((b) => (
              <tr key={b.name} className="hover:bg-black/[0.02]">
                <td className="px-5 py-4 font-bold text-[#0d0d0d]">{b.name}</td>
                <td className="px-5 py-4 text-xs text-[#525866]">{b.category}</td>
                <td className="mono px-5 py-4 text-xs font-bold text-emerald-800">{b.commission}</td>
                <td className="mono px-5 py-4 text-xs text-[#0d0d0d]">{b.catalog_skus}</td>
                <td className="px-5 py-4 text-xs text-[#525866]">{b.settlement}</td>
                <td className="px-5 py-4">
                  <StatusBadge value={b.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
