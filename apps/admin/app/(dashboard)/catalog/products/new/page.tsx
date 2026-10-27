import Link from "next/link";

import { createProductAction } from "@/app/(dashboard)/catalog/products/actions";
import { PageHeader } from "@/components/page-header";
import { requireSession } from "@/lib/auth";

const inputClass =
  "mt-1 w-full border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-slate-950";
const labelClass =
  "mono block text-[10px] uppercase tracking-[0.14em] text-slate-500";

export default async function NewProductPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { error } = await searchParams;
  await requireSession();

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
        eyebrow="Catálogo"
        title="Nuevo producto"
        description="Crea el producto con su primera variante. Después puedes añadir más variantes y media."
      />

      {error ? (
        <p className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </p>
      ) : null}

      <form action={createProductAction} className="space-y-6">
        <section className="border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-medium">Producto</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <label>
              <span className={labelClass}>Nombre</span>
              <input className={inputClass} name="name" required maxLength={200} />
            </label>
            <label>
              <span className={labelClass}>Slug</span>
              <input
                className={inputClass}
                name="slug"
                required
                pattern="[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
                placeholder="camisa-oxido"
              />
            </label>
            <label>
              <span className={labelClass}>Estado</span>
              <select className={inputClass} name="status" defaultValue="draft">
                <option value="draft">Draft</option>
                <option value="active">Active</option>
              </select>
            </label>
            <label>
              <span className={labelClass}>Marca</span>
              <input className={inputClass} name="brand" maxLength={100} />
            </label>
            <label className="sm:col-span-2">
              <span className={labelClass}>Descripción</span>
              <textarea
                className={`${inputClass} min-h-28`}
                name="description"
                maxLength={20000}
              />
            </label>
            <label className="sm:col-span-2">
              <span className={labelClass}>Tags (separados por coma)</span>
              <input className={inputClass} name="tags" />
            </label>
          </div>
        </section>

        <section className="border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-medium">Primera variante</h2>
          <p className="mt-1 text-sm text-slate-500">
            El stock se carga en la ubicación principal del tenant.
          </p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <label>
              <span className={labelClass}>SKU</span>
              <input className={inputClass} name="sku" required maxLength={100} />
            </label>
            <label>
              <span className={labelClass}>Nombre de la variante</span>
              <input
                className={inputClass}
                name="variant_name"
                required
                maxLength={200}
                placeholder="M / Negro"
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
                placeholder="189000"
              />
            </label>
            <label>
              <span className={labelClass}>Stock inicial</span>
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
              <span className={labelClass}>Opción (nombre)</span>
              <input
                className={inputClass}
                name="option_name"
                placeholder="Talla"
                maxLength={50}
              />
            </label>
            <label>
              <span className={labelClass}>Opción (valor)</span>
              <input
                className={inputClass}
                name="option_value"
                placeholder="M"
                maxLength={50}
              />
            </label>
          </div>
        </section>

        <div className="flex items-center gap-3">
          <button
            className="bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
            type="submit"
          >
            Crear producto
          </button>
          <Link
            className="mono text-[11px] text-slate-500 underline underline-offset-4"
            href="/catalog/products"
          >
            Cancelar
          </Link>
        </div>
      </form>
    </div>
  );
}
