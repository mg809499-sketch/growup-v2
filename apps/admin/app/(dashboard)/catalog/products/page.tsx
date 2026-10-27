import Link from "next/link";

import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { requireSession } from "@/lib/auth";
import { apiGet, queryString } from "@/lib/api";
import type { ProductListResponse } from "@/lib/api";
import { formatPrice } from "@/lib/format";

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
  const page = await apiGet<ProductListResponse>(
    `/v1/admin/products${queryString({
      status: params.status,
      q: params.q,
      limit,
      cursor: params.cursor,
    })}`,
    token,
  );

  const nextParams = new URLSearchParams();
  if (params.status) nextParams.set("status", params.status);
  if (params.q) nextParams.set("q", params.q);
  nextParams.set("limit", String(limit));
  if (page.next_cursor) {
    nextParams.set("cursor", page.next_cursor);
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <Link
          className="mono border border-slate-950 bg-slate-950 px-3 py-2 text-[11px] uppercase tracking-[0.12em] text-white hover:bg-white hover:text-slate-950"
          href="/catalog/products/new"
        >
          Nuevo producto
        </Link>
      </div>

      <PageHeader
        eyebrow="Catálogo"
        title="Productos"
        description="Listado y edición de productos, variantes y media del tenant."
      />

      <form className="flex flex-wrap items-end gap-3 border border-slate-200 bg-white p-4">
        <label className="block">
          <span className="mono block text-[10px] uppercase tracking-[0.14em] text-slate-500">
            Buscar
          </span>
          <input
            className="mt-1 w-64 border border-slate-300 px-3 py-2 text-sm"
            type="search"
            name="q"
            defaultValue={params.q ?? ""}
            placeholder="Nombre o descripción"
          />
        </label>
        <label className="block">
          <span className="mono block text-[10px] uppercase tracking-[0.14em] text-slate-500">
            Estado
          </span>
          <select
            className="mt-1 border border-slate-300 px-3 py-2 text-sm"
            name="status"
            defaultValue={params.status ?? ""}
          >
            <option value="">Todos</option>
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="archived">Archived</option>
          </select>
        </label>
        <button
          className="bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          type="submit"
        >
          Filtrar
        </button>
        <Link
          className="mono px-2 py-2 text-[11px] text-slate-500 underline underline-offset-4"
          href="/catalog/products"
        >
          Limpiar
        </Link>
      </form>

      {page.items.length === 0 ? (
        <EmptyState
          title="No hay productos con este filtro"
          description="Cambia el estado o la búsqueda para ver otros resultados."
        />
      ) : (
        <div className="overflow-x-auto border border-slate-200 bg-white">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50">
              <tr className="mono text-[10px] uppercase tracking-[0.12em] text-slate-500">
                <th className="px-4 py-3 font-medium">Producto</th>
                <th className="px-4 py-3 font-medium">Estado</th>
                <th className="px-4 py-3 font-medium">Precio</th>
                <th className="px-4 py-3 font-medium">Slug</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {page.items.map((product) => (
                <tr key={product.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <p className="font-medium text-slate-950">{product.name}</p>
                    <p className="mono mt-0.5 text-[10px] text-slate-400">
                      {product.id}
                    </p>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge value={product.status} />
                  </td>
                  <td className="px-4 py-3 text-slate-700">
                    {product.min_price_cents === product.max_price_cents
                      ? formatPrice(product.min_price_cents)
                      : `${formatPrice(product.min_price_cents)} – ${formatPrice(
                          product.max_price_cents,
                        )}`}
                  </td>
                  <td className="mono px-4 py-3 text-[11px] text-slate-500">
                    {product.slug}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      className="mono text-[11px] underline underline-offset-4 hover:text-slate-950"
                      href={`/catalog/products/${product.id}`}
                    >
                      Ver
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {page.next_cursor ? (
        <div className="flex justify-end">
          <Link
            className="border border-slate-300 bg-white px-3 py-1.5 text-sm hover:border-slate-950"
            href={`/catalog/products?${nextParams.toString()}`}
          >
            Siguiente
          </Link>
        </div>
      ) : null}
    </div>
  );
}
