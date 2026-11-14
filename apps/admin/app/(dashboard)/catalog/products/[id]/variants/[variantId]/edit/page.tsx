import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import {
  deleteVariantAction,
  updateVariantAction,
} from "@/app/(dashboard)/catalog/products/actions";
import { ConfirmSubmit } from "@/components/confirm-submit";
import { PageHeader } from "@/components/page-header";
import { SectionError } from "@/components/section-error";
import { requireSession } from "@/lib/auth";
import { ApiError, apiGet } from "@/lib/api";
import type { ProductDetailResponse } from "@/lib/api";

const inputClass =
  "mt-1 w-full border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-slate-950";
const labelClass =
  "mono block text-[10px] uppercase tracking-[0.14em] text-slate-500";

export default async function EditVariantPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string; variantId: string }>;
  searchParams: Promise<{ error?: string }>;
}) {
  const { id, variantId } = await params;
  const { error } = await searchParams;
  const { token } = await requireSession();

  let product: ProductDetailResponse;
  try {
    product = await apiGet<ProductDetailResponse>(
      `/v1/admin/products/${encodeURIComponent(id)}`,
      token,
    );
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
          title="Variante no disponible"
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

  const variant = product.variants.find((item) => item.id === variantId);
  if (!variant) {
    notFound();
  }

  const options = Object.entries(variant.option_values);
  const [option1Name, option1Value] = options[0] ?? ["", ""];
  const [option2Name, option2Value] = options[1] ?? ["", ""];

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
        eyebrow="Variante"
        title={variant.sku}
        description="Edita precio, opciones y estado. El stock se gestiona por inventario; aquí solo se muestra."
      />

      {error ? (
        <p className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </p>
      ) : null}

      <form action={updateVariantAction} className="space-y-6">
        <input type="hidden" name="product_id" value={product.id} />
        <input type="hidden" name="variant_id" value={variant.id} />

        <section className="border border-slate-200 bg-white p-5">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <label>
              <span className={labelClass}>Nombre</span>
              <input
                className={inputClass}
                name="variant_name"
                required
                maxLength={200}
                defaultValue={variant.name}
              />
            </label>
            <label>
              <span className={labelClass}>Precio (COP)</span>
              <input
                className={inputClass}
                name="price_cop"
                type="number"
                min={1}
                step={1}
                required
                defaultValue={variant.price_cents / 100}
              />
            </label>
            <label>
              <span className={labelClass}>Precio anterior (COP)</span>
              <input
                className={inputClass}
                name="compare_at_cop"
                type="number"
                min={0}
                step={1}
                defaultValue={
                  variant.compare_at_price_cents
                    ? variant.compare_at_price_cents / 100
                    : ""
                }
              />
            </label>
            <label>
              <span className={labelClass}>Estado</span>
              <select
                className={inputClass}
                name="is_active"
                defaultValue={variant.is_active ? "true" : "false"}
              >
                <option value="true">Activa</option>
                <option value="false">Inactiva</option>
              </select>
            </label>
            <label>
              <span className={labelClass}>Opción 1 (nombre)</span>
              <input
                className={inputClass}
                name="option_name"
                defaultValue={option1Name}
                maxLength={50}
              />
            </label>
            <label>
              <span className={labelClass}>Opción 1 (valor)</span>
              <input
                className={inputClass}
                name="option_value"
                defaultValue={option1Value}
                maxLength={50}
              />
            </label>
            <label>
              <span className={labelClass}>Opción 2 (nombre)</span>
              <input
                className={inputClass}
                name="option_name_2"
                defaultValue={option2Name}
                maxLength={50}
              />
            </label>
            <label>
              <span className={labelClass}>Opción 2 (valor)</span>
              <input
                className={inputClass}
                name="option_value_2"
                defaultValue={option2Value}
                maxLength={50}
              />
            </label>
          </div>

          <p className="mono mt-4 text-[11px] text-slate-500">
            Stock actual: {variant.stock_available} · El ajuste de inventario se
            hará desde el módulo de inventario.
          </p>
        </section>

        <div className="flex flex-wrap items-center gap-4">
          <button
            className="bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
            type="submit"
          >
            Guardar variante
          </button>
          <Link
            className="mono text-[11px] text-slate-500 underline underline-offset-4"
            href={`/catalog/products/${product.id}`}
          >
            Cancelar
          </Link>
        </div>
      </form>

      <form action={deleteVariantAction}>
        <input type="hidden" name="product_id" value={product.id} />
        <input type="hidden" name="variant_id" value={variant.id} />
        <ConfirmSubmit
          className="mono border border-red-300 bg-white px-3 py-2 text-[11px] uppercase tracking-[0.12em] text-red-700 hover:border-red-700"
          message="¿Eliminar esta variante? La operación no se puede deshacer."
        >
          Eliminar variante
        </ConfirmSubmit>
      </form>
    </div>
  );
}
