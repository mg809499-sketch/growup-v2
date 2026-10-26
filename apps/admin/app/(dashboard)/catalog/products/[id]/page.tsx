import Link from "next/link";
import { notFound } from "next/navigation";

import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { requireSession } from "@/lib/auth";
import { ApiError, apiGet } from "@/lib/api";
import type { ProductDetailResponse } from "@/lib/api";
import { formatPrice } from "@/lib/format";

export default async function ProductDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const { token } = await requireSession();

  let product: ProductDetailResponse;
  try {
    product = await apiGet<ProductDetailResponse>(
      `/v1/admin/products/${encodeURIComponent(id)}`,
      token,
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      notFound();
    }
    throw error;
  }

  return (
    <div className="space-y-6">
      <div>
        <Link
          className="mono text-[11px] text-slate-500 underline underline-offset-4"
          href="/catalog/products"
        >
          ← Volver al catálogo
        </Link>
      </div>

      <PageHeader
        eyebrow="Producto"
        title={product.name}
        description={product.description ?? "Sin descripción."}
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="border border-slate-200 bg-white p-4">
          <p className="mono text-[10px] uppercase tracking-[0.14em] text-slate-500">
            Estado
          </p>
          <div className="mt-2">
            <StatusBadge value={product.status} />
          </div>
        </div>
        <div className="border border-slate-200 bg-white p-4">
          <p className="mono text-[10px] uppercase tracking-[0.14em] text-slate-500">
            Precio
          </p>
          <p className="mt-2 text-sm">
            {formatPrice(product.min_price_cents)} –{" "}
            {formatPrice(product.max_price_cents)}
          </p>
        </div>
        <div className="border border-slate-200 bg-white p-4">
          <p className="mono text-[10px] uppercase tracking-[0.14em] text-slate-500">
            Variantes
          </p>
          <p className="mt-2 text-sm">{product.variants.length}</p>
        </div>
        <div className="border border-slate-200 bg-white p-4">
          <p className="mono text-[10px] uppercase tracking-[0.14em] text-slate-500">
            Media
          </p>
          <p className="mt-2 text-sm">{product.media.length}</p>
        </div>
      </div>

      <div className="border border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-4 py-3">
          <h2 className="text-sm font-medium">Variantes</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="bg-slate-50">
              <tr className="mono text-[10px] uppercase tracking-[0.12em] text-slate-500">
                <th className="px-4 py-2 font-medium">SKU</th>
                <th className="px-4 py-2 font-medium">Opciones</th>
                <th className="px-4 py-2 font-medium">Precio</th>
                <th className="px-4 py-2 font-medium">Stock</th>
                <th className="px-4 py-2 font-medium">Activa</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {product.variants.map((variant) => (
                <tr key={variant.id}>
                  <td className="mono px-4 py-2 text-[11px] text-slate-600">
                    {variant.sku}
                  </td>
                  <td className="px-4 py-2 text-slate-600">
                    {Object.entries(variant.option_values)
                      .map(([key, value]) => `${key}: ${value}`)
                      .join(" · ") || "—"}
                  </td>
                  <td className="px-4 py-2">{formatPrice(variant.price_cents)}</td>
                  <td className="px-4 py-2">{variant.stock_available}</td>
                  <td className="px-4 py-2">
                    {variant.is_active ? "Sí" : "No"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="border border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-4 py-3">
          <h2 className="text-sm font-medium">Media asociada</h2>
        </div>
        {product.media.length === 0 ? (
          <p className="px-4 py-6 text-sm text-slate-500">
            Este producto no tiene media asociada.
          </p>
        ) : (
          <div className="divide-y divide-slate-100">
            {product.media.map((item) => (
              <div
                key={item.media_asset_id}
                className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 text-sm"
              >
                <div className="min-w-0">
                  <p className="truncate font-medium">
                    {item.alt ?? "Sin alt text"}
                  </p>
                  <p className="mono mt-0.5 break-all text-[10px] text-slate-400">
                    {item.r2_key}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <StatusBadge value={item.status} />
                  <span className="mono text-[10px] text-slate-500">
                    {item.width && item.height
                      ? `${item.width}×${item.height}`
                      : "—"}
                  </span>
                  {item.is_primary ? (
                    <span className="mono border border-slate-950 px-2 py-0.5 text-[10px]">
                      Principal
                    </span>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="border border-slate-200 bg-white p-4">
        <p className="mono text-[10px] uppercase tracking-[0.14em] text-slate-500">
          Tags
        </p>
        <div className="mt-2 flex flex-wrap gap-2">
          {product.tags.length === 0 ? (
            <span className="text-sm text-slate-500">Sin tags</span>
          ) : (
            product.tags.map((tag) => (
              <span
                key={tag}
                className="mono border border-slate-200 bg-slate-50 px-2 py-1 text-[10px] text-slate-600"
              >
                {tag}
              </span>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
