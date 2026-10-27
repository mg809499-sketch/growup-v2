import Link from "next/link";
import { notFound } from "next/navigation";

import { updateProductAction } from "@/app/(dashboard)/catalog/products/actions";
import { PageHeader } from "@/components/page-header";
import { requireSession } from "@/lib/auth";
import { ApiError, apiGet } from "@/lib/api";
import type { ProductDetailResponse } from "@/lib/api";

const inputClass =
  "mt-1 w-full border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-slate-950";
const labelClass =
  "mono block text-[10px] uppercase tracking-[0.14em] text-slate-500";

export default async function EditProductPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ error?: string }>;
}) {
  const { id } = await params;
  const { error } = await searchParams;
  const { token } = await requireSession();

  let product: ProductDetailResponse;
  try {
    product = await apiGet<ProductDetailResponse>(
      `/v1/admin/products/${encodeURIComponent(id)}`,
      token,
    );
  } catch (apiError) {
    if (apiError instanceof ApiError && apiError.status === 404) {
      notFound();
    }
    throw apiError;
  }

  return (
    <div className="space-y-6">
      <div>
        <Link
          className="mono text-[11px] text-slate-500 underline underline-offset-4"
          href={`/catalog/products/${product.id}`}
        >
          ← Volver al producto
        </Link>
      </div>

      <PageHeader
        eyebrow="Catálogo"
        title="Editar producto"
        description="Los cambios se guardan en la API admin y quedan auditados."
      />

      {error ? (
        <p className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </p>
      ) : null}

      <form action={updateProductAction} className="space-y-6">
        <input type="hidden" name="product_id" value={product.id} />

        <section className="border border-slate-200 bg-white p-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <label>
              <span className={labelClass}>Nombre</span>
              <input
                className={inputClass}
                name="name"
                required
                maxLength={200}
                defaultValue={product.name}
              />
            </label>
            <label>
              <span className={labelClass}>Estado</span>
              <select
                className={inputClass}
                name="status"
                defaultValue={product.status}
              >
                <option value="draft">Draft</option>
                <option value="active">Active</option>
                <option value="archived">Archived</option>
              </select>
            </label>
            <label>
              <span className={labelClass}>Marca</span>
              <input
                className={inputClass}
                name="brand"
                maxLength={100}
                defaultValue={product.brand ?? ""}
              />
            </label>
            <label>
              <span className={labelClass}>Tags (separados por coma)</span>
              <input
                className={inputClass}
                name="tags"
                defaultValue={product.tags.join(", ")}
              />
            </label>
            <label className="sm:col-span-2">
              <span className={labelClass}>Descripción</span>
              <textarea
                className={`${inputClass} min-h-32`}
                name="description"
                maxLength={20000}
                defaultValue={product.description ?? ""}
              />
            </label>
          </div>
        </section>

        <div className="flex items-center gap-3">
          <button
            className="bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
            type="submit"
          >
            Guardar cambios
          </button>
          <Link
            className="mono text-[11px] text-slate-500 underline underline-offset-4"
            href={`/catalog/products/${product.id}`}
          >
            Cancelar
          </Link>
        </div>
      </form>
    </div>
  );
}
