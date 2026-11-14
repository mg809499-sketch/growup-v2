import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import {
  addVariantAction,
  attachMediaAction,
  detachMediaAction,
} from "@/app/(dashboard)/catalog/products/actions";
import { ConfirmSubmit } from "@/components/confirm-submit";
import { PageHeader } from "@/components/page-header";
import { SectionError } from "@/components/section-error";
import { StatusBadge } from "@/components/status-badge";
import { requireSession } from "@/lib/auth";
import { ApiError, apiGet } from "@/lib/api";
import type {
  MediaAssetListResponse,
  ProductDetailResponse,
} from "@/lib/api";
import { formatPrice } from "@/lib/format";

const inputClass =
  "mt-1 w-full border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-slate-950";
const labelClass =
  "mono block text-[10px] uppercase tracking-[0.14em] text-slate-500";

export default async function ProductDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ error?: string; media_offset?: string }>;
}) {
  const { id } = await params;
  const { error, media_offset } = await searchParams;
  const { token } = await requireSession();
  const requestedMediaOffset = Number(media_offset);
  const mediaOffset =
    Number.isSafeInteger(requestedMediaOffset) &&
    requestedMediaOffset >= 0 &&
    requestedMediaOffset <= 1_000_000
      ? requestedMediaOffset
      : 0;

  let product: ProductDetailResponse;
  let mediaLibrary: MediaAssetListResponse;
  try {
    [product, mediaLibrary] = await Promise.all([
      apiGet<ProductDetailResponse>(
        `/v1/admin/products/${encodeURIComponent(id)}`,
        token,
      ),
      apiGet<MediaAssetListResponse>(
        `/v1/admin/media?status=ready&limit=100&offset=${mediaOffset}`,
        token,
      ),
    ]);
  } catch (apiError) {
    if (apiError instanceof ApiError && apiError.status === 401) {
      redirect("/login");
    }
    if (apiError instanceof ApiError && apiError.status === 404) {
      notFound();
    }
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Catálogo"
          title="Producto no disponible"
          description="No se pudo resolver el producto desde la API."
        />
        <SectionError
          title="No se pudo cargar el producto"
          error={{
            status: apiError instanceof ApiError ? apiError.status : 0,
            code: apiError instanceof ApiError ? apiError.code : null,
            message: apiError instanceof Error ? apiError.message : "Error inesperado",
          }}
        />
      </div>
    );
  }

  const attachedIds = new Set(
    product.media.map((item) => item.media_asset_id),
  );
  const availableMedia = mediaLibrary.items.filter(
    (item) => !attachedIds.has(item.id),
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link
          className="mono text-[11px] text-slate-500 underline underline-offset-4"
          href="/catalog/products"
        >
          ← Volver al catálogo
        </Link>
        <Link
          className="mono border border-slate-950 bg-white px-3 py-2 text-[11px] uppercase tracking-[0.12em] hover:bg-slate-950 hover:text-white"
          href={`/catalog/products/${product.id}/edit`}
        >
          Editar producto
        </Link>
      </div>

      <PageHeader
        eyebrow="Producto"
        title={product.name}
        description={product.description ?? "Sin descripción."}
      />

      {error ? (
        <p className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </p>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="border border-slate-200 bg-white p-4">
          <p className={labelClass}>Estado</p>
          <div className="mt-2">
            <StatusBadge value={product.status} />
          </div>
        </div>
        <div className="border border-slate-200 bg-white p-4">
          <p className={labelClass}>Precio</p>
          <p className="mt-2 text-sm">
            {formatPrice(product.min_price_cents)} –{" "}
            {formatPrice(product.max_price_cents)}
          </p>
        </div>
        <div className="border border-slate-200 bg-white p-4">
          <p className={labelClass}>Variantes</p>
          <p className="mt-2 text-sm">{product.variants.length}</p>
        </div>
        <div className="border border-slate-200 bg-white p-4">
          <p className={labelClass}>Media</p>
          <p className="mt-2 text-sm">{product.media.length}</p>
        </div>
      </div>

      <div className="border border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-4 py-3">
          <h2 className="text-sm font-medium">Variantes</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="bg-slate-50">
              <tr className="mono text-[10px] uppercase tracking-[0.12em] text-slate-500">
                <th className="px-4 py-2 font-medium">SKU</th>
                <th className="px-4 py-2 font-medium">Opciones</th>
                <th className="px-4 py-2 font-medium">Precio</th>
                <th className="px-4 py-2 font-medium">Stock</th>
                <th className="px-4 py-2 font-medium">Activa</th>
                <th className="px-4 py-2" />
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
                  <td className="px-4 py-2 text-right">
                    <Link
                      className="mono text-[11px] underline underline-offset-4"
                      href={`/catalog/products/${product.id}/variants/${variant.id}/edit`}
                    >
                      Editar
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <form
          action={addVariantAction}
          className="grid gap-3 border-t border-slate-200 bg-slate-50 p-4 sm:grid-cols-2 lg:grid-cols-6"
        >
          <input type="hidden" name="product_id" value={product.id} />
          <label>
            <span className={labelClass}>SKU</span>
            <input className={inputClass} name="sku" required maxLength={100} />
          </label>
          <label>
            <span className={labelClass}>Nombre</span>
            <input
              className={inputClass}
              name="variant_name"
              required
              maxLength={200}
            />
          </label>
          <label>
            <span className={labelClass}>Precio COP</span>
            <input
              className={inputClass}
              name="price_cop"
              type="number"
              min={1}
              step={1}
              required
            />
          </label>
          <label>
            <span className={labelClass}>Stock</span>
            <input
              className={inputClass}
              name="stock"
              type="number"
              min={0}
              step={1}
              defaultValue={0}
            />
          </label>
          <label>
            <span className={labelClass}>Opción</span>
            <input
              className={inputClass}
              name="option_name"
              placeholder="Talla"
              maxLength={50}
            />
          </label>
          <label>
            <span className={labelClass}>Valor</span>
            <input
              className={inputClass}
              name="option_value"
              placeholder="L"
              maxLength={50}
            />
          </label>
          <div className="sm:col-span-2 lg:col-span-6">
            <button
              className="bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
              type="submit"
            >
              Añadir variante
            </button>
          </div>
        </form>
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
                  <form action={detachMediaAction}>
                    <input type="hidden" name="product_id" value={product.id} />
                    <input
                      type="hidden"
                      name="media_asset_id"
                      value={item.media_asset_id}
                    />
                    <ConfirmSubmit
                      className="mono border border-red-200 px-2 py-1 text-[10px] uppercase tracking-[0.08em] text-red-700 hover:border-red-600"
                      message="¿Desasociar esta imagen del producto?"
                    >
                      Quitar
                    </ConfirmSubmit>
                  </form>
                </div>
              </div>
            ))}
          </div>
        )}

        {availableMedia.length > 0 ? (
          <form
            action={attachMediaAction}
            className="grid gap-3 border-t border-slate-200 bg-slate-50 p-4 sm:grid-cols-4"
          >
            <input type="hidden" name="product_id" value={product.id} />
            <label className="sm:col-span-2">
              <span className={labelClass}>Imagen disponible</span>
              <select className={inputClass} name="media_asset_id" required>
                <option value="">Selecciona una imagen</option>
                {availableMedia.map((asset) => (
                  <option key={asset.id} value={asset.id}>
                    {asset.alt ?? asset.original_filename ?? asset.id}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span className={labelClass}>Principal</span>
              <select className={inputClass} name="is_primary" defaultValue="false">
                <option value="false">No</option>
                <option value="true">Sí</option>
              </select>
            </label>
            <div className="flex items-end">
              <button
                className="bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
                type="submit"
              >
                Asociar imagen
              </button>
            </div>
          </form>
        ) : (
          <p className="border-t border-slate-200 px-4 py-4 text-sm text-slate-500">
            No hay imágenes listas para asociar. Sube media desde la API y
            vuelve a esta pantalla.
          </p>
        )}
        {mediaLibrary.total > mediaLibrary.limit ? (
          <nav
            aria-label="Paginación de biblioteca de imágenes"
            className="flex items-center justify-between border-t border-slate-200 px-4 py-3 text-sm"
          >
            <span className="text-slate-500">
              {mediaOffset + 1}–
              {mediaOffset + mediaLibrary.items.length} de {mediaLibrary.total}
            </span>
            <div className="flex gap-3">
              {mediaOffset > 0 ? (
                <Link
                  className="underline underline-offset-4"
                  href={`/catalog/products/${product.id}?media_offset=${Math.max(
                    0,
                    mediaOffset - mediaLibrary.limit,
                  )}`}
                >
                  Anterior
                </Link>
              ) : null}
              {mediaOffset + mediaLibrary.items.length < mediaLibrary.total ? (
                <Link
                  className="underline underline-offset-4"
                  href={`/catalog/products/${product.id}?media_offset=${
                    mediaOffset + mediaLibrary.items.length
                  }`}
                >
                  Siguiente
                </Link>
              ) : null}
            </div>
          </nav>
        ) : null}
      </div>

      <div className="border border-slate-200 bg-white p-4">
        <p className={labelClass}>Tags</p>
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
