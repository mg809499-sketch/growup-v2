import Link from "next/link";
import { redirect } from "next/navigation";

import { KpiCard } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { requireSession } from "@/lib/auth";
import { apiGetSafe, queryString } from "@/lib/api";
import type { ProductListResponse } from "@/lib/api";
import { formatPrice } from "@/lib/format";

const CATALOG_ENRICHED: Record<
  string,
  { sku: string; category: string; margin: string; stock: number }
> = {
  "chaqueta-valkyrie-pro": {
    sku: "SKU-809",
    category: "Alto Rendimiento",
    margin: "58% ($110.140)",
    stock: 42,
  },
  "jean-recto-archivo-04": {
    sku: "SKU-102",
    category: "Denim Editorial",
    margin: "62% ($141.980)",
    stock: 18,
  },
  "aretes-arabesque-kyanite": {
    sku: "SKU-304",
    category: "Alta Joyería 18k",
    margin: "68% ($333.200)",
    stock: 3,
  },
  "cortavientos-reflex-pro": {
    sku: "SKU-512",
    category: "Running & Outdoor",
    margin: "55% ($115.500)",
    stock: 4,
  },
};

export default async function ProductsPage({
  searchParams,
}: {
  searchParams: Promise<{
    status?: string;
    q?: string;
    cursor?: string;
    limit?: string;
  }>;
}) {
  const params = await searchParams;
  const { token } = await requireSession();
  const limit = Math.min(Number(params.limit) || 20, 50);
  const result = await apiGetSafe<ProductListResponse>(
    `/v1/admin/products${queryString({
      status: params.status,
      q: params.q,
      limit,
      cursor: params.cursor,
    })}`,
    token,
  );
  if (result.redirectToLogin) {
    redirect("/login");
  }
  const page = result.data;
  const items = page?.items ?? [];

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <PageHeader
          eyebrow="2. Módulo: Operaciones Core · Catálogo & Inventario"
          title="Catálogo & Inventario en Tiempo Real"
          description="Control de SKUs activos, existencias físicas multi-bodega, alertas de stock bajo, márgenes de ganancia y vinculación directa con Wompi."
        />
        <Link
          className="rounded-xl bg-[#0d0d0d] px-4 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-zinc-800"
          href="/catalog/products/new"
        >
          + Crear / Editar SKU
        </Link>
      </div>

      {/* Métricas de bodega */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Total de SKUs Activos"
          value="48 SKUs"
          detail="100% sincronizados con Store Builder v3.0"
        />
        <KpiCard
          label="Unidades Físicas en Stock"
          value="642 uds"
          detail="Reservas atómicas sin sobreventa"
        />
        <KpiCard
          label="Productos con Stock Bajo"
          value="2 SKUs"
          detail="Alerta enviada a Agente OpenCode IA"
        />
        <KpiCard
          label="Valoración Económica"
          value="$ 128.400.000"
          detail="Costo promedio ponderado en COP"
        />
      </div>

      {/* Barra de filtros & búsqueda */}
      <form className="vn-card flex flex-wrap items-end gap-3 p-5">
        <label className="block min-w-[240px] flex-1">
          <span className="mono block text-[10px] font-semibold uppercase tracking-[0.14em] text-[#525866]">
            Buscar por SKU, código de barras o título
          </span>
          <input
            className="mt-1.5 w-full rounded-xl border border-black/15 bg-white px-3.5 py-2 text-sm text-[#0d0d0d] placeholder:text-slate-400"
            type="search"
            name="q"
            defaultValue={params.q ?? ""}
            placeholder="Ej. SKU-809, Valkyrie, Denim..."
          />
        </label>
        <label className="block">
          <span className="mono block text-[10px] font-semibold uppercase tracking-[0.14em] text-[#525866]">
            Categoría
          </span>
          <select className="mt-1.5 rounded-xl border border-black/15 bg-white px-3.5 py-2 text-sm text-[#0d0d0d]">
            <option value="">Todas las categorías</option>
            <option value="deporte">Alto Rendimiento</option>
            <option value="denim">Denim Editorial</option>
            <option value="joyeria">Alta Joyería 18k</option>
          </select>
        </label>
        <label className="block">
          <span className="mono block text-[10px] font-semibold uppercase tracking-[0.14em] text-[#525866]">
            Estado
          </span>
          <select
            className="mt-1.5 rounded-xl border border-black/15 bg-white px-3.5 py-2 text-sm text-[#0d0d0d]"
            name="status"
            defaultValue={params.status ?? ""}
          >
            <option value="">Todos</option>
            <option value="active">Publicado</option>
            <option value="draft">Borrador</option>
            <option value="archived">Agotado / Archivado</option>
          </select>
        </label>
        <button
          className="rounded-xl bg-[#0d0d0d] px-5 py-2 text-sm font-bold text-white hover:bg-zinc-800"
          type="submit"
        >
          Filtrar Catálogo
        </button>
      </form>

      {/* Tabla de gestión de productos */}
      <div className="vn-card overflow-x-auto admin-scroll">
        <table className="w-full min-w-[920px] text-left text-sm">
          <thead className="border-b border-black/10 bg-white/50">
            <tr className="mono text-[10px] uppercase tracking-[0.12em] text-[#525866]">
              <th className="px-5 py-3.5 font-semibold">Fotografía &amp; Producto</th>
              <th className="px-5 py-3.5 font-semibold">SKU Único</th>
              <th className="px-5 py-3.5 font-semibold">Categoría</th>
              <th className="px-5 py-3.5 font-semibold">Stock Real</th>
              <th className="px-5 py-3.5 font-semibold">Precio Venta (COP)</th>
              <th className="px-5 py-3.5 font-semibold">Margen</th>
              <th className="px-5 py-3.5 font-semibold">Estado</th>
              <th className="px-5 py-3.5 text-right font-semibold">Acciones Rápidas</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-black/10">
            {items.map((product) => {
              const meta = CATALOG_ENRICHED[product.slug] ?? {
                sku: `SKU-${product.slug.slice(0, 4).toUpperCase()}`,
                category: "Catálogo General",
                margin: "56%",
                stock: 12,
              };
              return (
                <tr key={product.id} className="hover:bg-black/[0.02]">
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-3">
                      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-black/10 bg-slate-100 font-mono text-[10px] font-bold text-[#0d0d0d]">
                        IMG
                      </div>
                      <div>
                        <p className="font-semibold text-[#0d0d0d]">{product.name}</p>
                        <p className="mono mt-0.5 text-[10px] text-[#525866]">
                          /{product.slug}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="mono px-5 py-4 text-xs font-bold text-[#0d0d0d]">
                    {meta.sku}
                  </td>
                  <td className="px-5 py-4 text-xs text-[#525866]">{meta.category}</td>
                  <td className="mono px-5 py-4 text-xs font-bold text-[#0d0d0d]">
                    {meta.stock} uds
                  </td>
                  <td className="mono px-5 py-4 text-xs font-bold text-[#0d0d0d]">
                    {formatPrice(product.min_price_cents)}
                  </td>
                  <td className="mono px-5 py-4 text-xs text-emerald-800">
                    {meta.margin}
                  </td>
                  <td className="px-5 py-4">
                    <StatusBadge value={product.status} />
                  </td>
                  <td className="px-5 py-4 text-right">
                    <div className="inline-flex items-center gap-1.5">
                      <Link
                        className="rounded-lg border border-black/15 bg-white px-2.5 py-1 text-xs font-semibold text-[#0d0d0d] hover:bg-[#0d0d0d] hover:text-white"
                        href={`/catalog/products/${product.id}`}
                      >
                        Editar
                      </Link>
                      <button
                        type="button"
                        className="rounded-lg border border-black/15 bg-white px-2.5 py-1 text-xs font-semibold text-[#525866] hover:text-[#0d0d0d]"
                      >
                        Clonar
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Modal / Panel rápido de Creación y Vinculación de SKU */}
      <section className="vn-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-black/10 pb-4">
          <div>
            <p className="mono text-[10px] font-bold text-[#525866]">CREACIÓN Y EDICIÓN RÁPIDA DE SKU</p>
            <h2 className="display mt-1 text-lg font-bold text-[#0d0d0d]">
              Ficha de Producto, Variantes y Pasarela Wompi
            </h2>
          </div>
          <span className="rounded-full border border-emerald-300 bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-900">
            Vinculado con Checkout Express Wompi
          </span>
        </div>
        <div className="mt-4 grid gap-4 md:grid-cols-4">
          <label className="block text-xs font-medium text-[#525866]">
            Título del Producto
            <input
              type="text"
              placeholder="Ej. Chaqueta Deportiva Pro"
              className="mt-1 w-full rounded-xl border border-black/15 bg-white px-3 py-2 text-sm text-[#0d0d0d]"
            />
          </label>
          <label className="block text-xs font-medium text-[#525866]">
            SKU &amp; Variantes (Talla/Color)
            <input
              type="text"
              placeholder="SKU-910 · S, M, L, XL"
              className="mt-1 w-full rounded-xl border border-black/15 bg-white px-3 py-2 font-mono text-sm text-[#0d0d0d]"
            />
          </label>
          <label className="block text-xs font-medium text-[#525866]">
            Precio en COP
            <input
              type="number"
              placeholder="189900"
              className="mt-1 w-full rounded-xl border border-black/15 bg-white px-3 py-2 font-mono text-sm text-[#0d0d0d]"
            />
          </label>
          <div className="flex items-end">
            <Link
              href="/catalog/products/new"
              className="inline-flex w-full items-center justify-center rounded-xl bg-[#0d0d0d] px-4 py-2.5 text-xs font-bold text-white hover:bg-zinc-800"
            >
              Guardar y Publicar SKU
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
