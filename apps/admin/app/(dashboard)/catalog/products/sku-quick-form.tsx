"use client";

import { useMemo, useState } from "react";
import Link from "next/link";

type Props = {
  categories: string[];
  brands: string[];
};

function formatCOP(value: number): string {
  if (!Number.isFinite(value)) return "—";
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(value);
}

export function SkuQuickForm({ categories, brands }: Props) {
  const [salePrice, setSalePrice] = useState("");
  const [purchasePrice, setPurchasePrice] = useState("");
  const [imageUrl, setImageUrl] = useState("");

  const margin = useMemo(() => {
    const sale = Number(salePrice);
    const purchase = Number(purchasePrice);
    if (!Number.isFinite(sale) || !Number.isFinite(purchase) || sale <= 0) {
      return null;
    }
    const profit = sale - purchase;
    const percent = (profit / sale) * 100;
    return { profit, percent };
  }, [salePrice, purchasePrice]);

  return (
    <section className="vn-card p-6">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-black/10 pb-4">
        <div>
          <p className="mono text-[10px] font-bold text-[#525866]">
            CREACIÓN Y EDICIÓN RÁPIDA DE SKU
          </p>
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
          Categoría
          <select className="mt-1 w-full rounded-xl border border-black/15 bg-white px-3 py-2 text-sm text-[#0d0d0d]">
            <option value="">Seleccionar categoría</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
            <option value="__new__">+ Crear categoría</option>
          </select>
        </label>

        <label className="block text-xs font-medium text-[#525866]">
          Marca
          <select className="mt-1 w-full rounded-xl border border-black/15 bg-white px-3 py-2 text-sm text-[#0d0d0d]">
            <option value="">Seleccionar marca</option>
            {brands.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
            <option value="__new__">+ Crear marca</option>
          </select>
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
          Precio de compra (COP)
          <input
            type="number"
            value={purchasePrice}
            onChange={(e) => setPurchasePrice(e.target.value)}
            placeholder="120000"
            className="mt-1 w-full rounded-xl border border-black/15 bg-white px-3 py-2 font-mono text-sm text-[#0d0d0d]"
          />
        </label>

        <label className="block text-xs font-medium text-[#525866]">
          Precio de venta (COP)
          <input
            type="number"
            value={salePrice}
            onChange={(e) => setSalePrice(e.target.value)}
            placeholder="189900"
            className="mt-1 w-full rounded-xl border border-black/15 bg-white px-3 py-2 font-mono text-sm text-[#0d0d0d]"
          />
        </label>

        <label className="block text-xs font-medium text-[#525866]">
          Margen de ganancia
          <div className="mt-1 flex h-[38px] items-center rounded-xl border border-emerald-300 bg-emerald-50 px-3 font-mono text-sm font-bold text-emerald-900">
            {margin
              ? `${margin.percent.toFixed(1)}% · ${formatCOP(margin.profit)}`
              : "—"}
          </div>
        </label>

        <label className="block text-xs font-medium text-[#525866]">
          Imagen (URL)
          <input
            type="url"
            value={imageUrl}
            onChange={(e) => setImageUrl(e.target.value)}
            placeholder="https://.../producto.webp"
            className="mt-1 w-full rounded-xl border border-black/15 bg-white px-3 py-2 font-mono text-sm text-[#0d0d0d]"
          />
        </label>
      </div>

      {imageUrl ? (
        <div className="mt-4 flex items-center gap-3">
          {/* URL arbitraria del comerciante: next/image exigiría remotePatterns comodín. */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={imageUrl}
            alt="Vista previa"
            className="h-16 w-16 rounded-xl border border-black/10 object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
          <span className="text-xs text-[#525866]">Vista previa de la imagen (URL)</span>
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap items-end justify-between gap-3">
        <p className="text-xs text-[#525866]">
          También puedes subir imágenes desde la biblioteca de Media y asignarlas al producto.
        </p>
        <Link
          href="/catalog/products/new"
          className="inline-flex items-center justify-center rounded-xl bg-[#0d0d0d] px-4 py-2.5 text-xs font-bold text-white hover:bg-zinc-800"
        >
          Guardar y Publicar SKU
        </Link>
      </div>
    </section>
  );
}