import Link from "next/link";
import { notFound } from "next/navigation";
import { revalidatePath } from "next/cache";

import { apiGet, apiSend, ApiError } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import { PageHeader } from "@/components/page-header";
import type { OrderDetail } from "@/lib/orders";
import { formatPrice } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function OrderDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ error?: string }>;
}) {
  const { id } = await params;
  const query = await searchParams;
  const { token } = await requireSession();

  let order: OrderDetail | null = null;
  try {
    order = await apiGet<OrderDetail>(`/v1/admin/orders/${id}`, token);
  } catch {
    notFound();
  }
  if (!order) {
    notFound();
  }

  async function transition(formData: FormData) {
    "use server";
    const { token: sessionToken } = await requireSession();
    const target = String(formData.get("status") ?? "");
    try {
      await apiSend("POST", `/v1/admin/orders/${id}/status`, sessionToken, {
        status: target,
      });
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "No se pudo actualizar el estado";
      const { redirect } = await import("next/navigation");
      redirect(`/orders/${id}?error=${encodeURIComponent(message)}`);
    }
    revalidatePath(`/orders/${id}`);
    const { redirect } = await import("next/navigation");
    redirect(`/orders/${id}`);
  }

  const nextActions: Record<string, string[]> = {
    paid: ["preparing", "cancelled"],
    preparing: ["shipped", "cancelled"],
    shipped: ["delivered"],
    refund_pending: ["refunded"],
  };
  const actions = nextActions[order.status] ?? [];

  return (
    <div className="space-y-6">
      <Link href="/orders" className="text-xs text-slate-500 underline underline-offset-2">
        ← Pedidos
      </Link>
      <PageHeader
        eyebrow={order.email}
        title={`Pedido ${order.id.slice(0, 8)}`}
        description={`Creado el ${new Date(order.created_at).toLocaleString("es-CO")} · zona ${order.shipping_zone ?? "—"}`}
      />

      {query.error ? (
        <p className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {query.error}
        </p>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="border border-slate-200 bg-white lg:col-span-2">
          <table className="w-full text-sm">
            <thead className="border-b text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-2">Producto</th>
                <th className="px-4 py-2">Cantidad</th>
                <th className="px-4 py-2 text-right">Unitario</th>
              </tr>
            </thead>
            <tbody>
              {order.items.map((item, index) => (
                <tr key={index} className="border-b border-slate-100 last:border-0">
                  <td className="px-4 py-3">
                    <p>{item.product_name}</p>
                    <p className="font-mono text-xs text-slate-500">
                      {item.variant_sku} {item.variant_title ? `· ${item.variant_title}` : ""}
                    </p>
                  </td>
                  <td className="px-4 py-3">{item.quantity}</td>
                  <td className="px-4 py-3 text-right">{formatPrice(item.unit_price_cents)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="space-y-1 border-t border-slate-200 px-4 py-3 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">Subtotal</span>
              <span>{formatPrice(order.subtotal_cents)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">IVA (19% incluido)</span>
              <span>{formatPrice(order.tax_cents)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Envío</span>
              <span>{formatPrice(order.shipping_cents)}</span>
            </div>
            <div className="flex justify-between border-t border-slate-100 pt-2 text-base font-semibold">
              <span>Total</span>
              <span>{formatPrice(order.total_cents)}</span>
            </div>
          </div>
        </div>

        <aside className="space-y-4">
          <div className="border border-slate-200 bg-white p-4">
            <p className="text-xs uppercase tracking-wide text-slate-500">Estado</p>
            <p className="mt-1 font-medium text-slate-900">{order.status}</p>
            {actions.length > 0 ? (
              <div className="mt-3 space-y-2">
                {actions.map((next) => (
                  <form key={next} action={transition}>
                    <input type="hidden" name="status" value={next} />
                    <button
                      type="submit"
                      className="w-full border border-slate-900 bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-700"
                    >
                      Marcar como «{next}»
                    </button>
                  </form>
                ))}
              </div>
            ) : (
              <p className="mt-2 text-xs text-slate-500">Sin acciones disponibles.</p>
            )}
          </div>

          <div className="border border-slate-200 bg-white p-4 text-xs leading-relaxed text-slate-500">
            El cobro lo procesa la cuenta Wompi del comerciante. Growup no
            almacena datos de tarjeta. Los reembolsos se gestionan desde el
            panel de Wompi; el estado aquí es solo contable/operativo.
          </div>
        </aside>
      </div>
    </div>
  );
}
