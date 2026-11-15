import Link from "next/link";

import { Price } from "@/components/price";
import { fetchCart } from "@/lib/cart";
import { checkoutAction, updateCartItemAction } from "@/lib/cart-actions";
import { DEFAULT_SHIPPING_ZONES, formatPrice } from "@growup/config";

export const dynamic = "force-dynamic";
export const metadata = {
  title: "Carrito | Growup",
  robots: { index: false, follow: false },
};

export default async function CartPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { error } = await searchParams;
  const cart = await fetchCart();
  const items = cart?.items ?? [];

  return (
    <main className="mx-auto max-w-[1100px] px-4 pt-10 md:px-10">
      <nav className="label text-[var(--muted)]">
        <Link href="/collection" className="hover:text-[var(--ink)]">
          ← Seguir comprando
        </Link>
      </nav>

      <h1 className="display mt-4 text-5xl leading-[0.95]">Carrito</h1>

      {error ? (
        <p className="mt-4 border border-[var(--signal)] px-4 py-3 text-sm text-[var(--signal)]">
          {error}
        </p>
      ) : null}

      {items.length === 0 ? (
        <p className="mt-10 border border-[var(--hairline)] px-6 py-16 text-center text-[var(--muted)]">
          Tu carrito está vacío.{" "}
          <Link href="/collection" className="underline underline-offset-2">
            Ver la colección
          </Link>
        </p>
      ) : (
        <div className="mt-8 grid gap-10 lg:grid-cols-12">
          <section className="lg:col-span-7">
            <ul className="divide-y divide-[var(--hairline)] border-y border-[var(--hairline)]">
              {items.map((item) => (
                <li key={item.variant_id} className="flex items-center justify-between gap-4 py-4">
                  <div>
                    <p className="text-sm font-medium">{item.product_name}</p>
                    <p className="label mt-1 text-[var(--muted)]">
                      {item.variant_title ?? "Única"} · {item.variant_sku}
                    </p>
                    <Price cents={item.unit_price_cents} className="mt-1 text-sm" />
                  </div>
                  <form action={updateCartItemAction} className="flex items-center gap-2">
                    <input type="hidden" name="variant_id" value={item.variant_id} />
                    <label className="sr-only" htmlFor={`qty-${item.variant_id}`}>
                      Cantidad
                    </label>
                    <input
                      id={`qty-${item.variant_id}`}
                      name="quantity"
                      type="number"
                      min={0}
                      max={50}
                      defaultValue={item.quantity}
                      className="w-16 border border-[var(--hairline)] bg-[var(--surface-2)] px-2 py-2"
                    />
                    <button type="submit" className="label border border-[var(--hairline)] px-3 py-2">
                      Act.
                    </button>
                  </form>
                </li>
              ))}
            </ul>
            <div className="mt-4 flex items-center justify-between">
              <p className="label text-[var(--muted)]">Subtotal</p>
              <p className="text-lg font-medium">{formatPrice(cart?.subtotal_cents ?? 0)}</p>
            </div>
          </section>

          <form action={checkoutAction} className="space-y-4 lg:col-span-5">
            <fieldset className="border border-[var(--hairline)] p-5">
              <legend className="label px-2 text-[var(--muted)]">Datos de envío</legend>
              <label className="block text-sm">
                <span className="mb-1 block text-[var(--muted)]">Correo</span>
                <input
                  name="email"
                  type="email"
                  required
                  className="w-full border border-[var(--hairline)] bg-[var(--surface-2)] px-3 py-2"
                />
              </label>
              <label className="mt-3 block text-sm">
                <span className="mb-1 block text-[var(--muted)]">Nombre completo</span>
                <input
                  name="shipping_name"
                  required
                  minLength={2}
                  className="w-full border border-[var(--hairline)] bg-[var(--surface-2)] px-3 py-2"
                />
              </label>
              <label className="mt-3 block text-sm">
                <span className="mb-1 block text-[var(--muted)]">Dirección</span>
                <input
                  name="shipping_line1"
                  required
                  minLength={3}
                  className="w-full border border-[var(--hairline)] bg-[var(--surface-2)] px-3 py-2"
                />
              </label>
              <div className="mt-3 grid grid-cols-2 gap-3">
                <label className="block text-sm">
                  <span className="mb-1 block text-[var(--muted)]">Ciudad</span>
                  <input
                    name="shipping_city"
                    required
                    className="w-full border border-[var(--hairline)] bg-[var(--surface-2)] px-3 py-2"
                  />
                </label>
                <label className="block text-sm">
                  <span className="mb-1 block text-[var(--muted)]">Departamento</span>
                  <input
                    name="shipping_state"
                    required
                    className="w-full border border-[var(--hairline)] bg-[var(--surface-2)] px-3 py-2"
                  />
                </label>
              </div>
              <label className="mt-3 block text-sm">
                <span className="mb-1 block text-[var(--muted)]">Zona de envío</span>
                <select
                  name="shipping_zone"
                  defaultValue="bogota"
                  className="w-full border border-[var(--hairline)] bg-[var(--surface-2)] px-3 py-2"
                >
                  {DEFAULT_SHIPPING_ZONES.map((zone) => (
                    <option key={zone.code} value={zone.code}>
                      {zone.name} — {formatPrice(zone.price_cents)}
                    </option>
                  ))}
                </select>
              </label>
            </fieldset>

            <button
              type="submit"
              className="label w-full border border-[var(--ink)] bg-[var(--ink)] px-6 py-4 text-[var(--surface)] transition-colors hover:bg-[var(--signal)]"
            >
              Ir a pagar con Wompi
            </button>
            <p className="label text-center text-[var(--muted)]">
              Pago seguro · no almacenamos datos de tarjeta
            </p>
          </form>
        </div>
      )}
    </main>
  );
}
