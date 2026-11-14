import Link from "next/link";
import { redirect } from "next/navigation";

import { apiGetSafe } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import { PageHeader } from "@/components/page-header";
import { SectionError } from "@/components/section-error";
import type { OrderListResponse } from "@/lib/orders";
import { formatPrice } from "@/lib/format";

export const dynamic = "force-dynamic";

const STATUS_LABEL: Record<string, string> = {
  pending: "Pendiente",
  paid: "Pagada",
  failed: "Fallida",
  expired: "Expirada",
  cancelled: "Cancelada",
  preparing: "Preparando",
  shipped: "Enviada",
  delivered: "Entregada",
  refund_pending: "Reembolso pendiente",
  refunded: "Reembolsada",
};

export default async function OrdersPage({
  searchParams,
}: {
  searchParams: Promise<{ offset?: string }>;
}) {
  const { token } = await requireSession();
  const params = await searchParams;
  const offset = Math.max(0, Number(params.offset ?? 0) || 0);
  const limit = 20;

  const result = await apiGetSafe<OrderListResponse>(
    `/v1/admin/orders?limit=${limit}&offset=${offset}`,
    token,
  );
  if (result.redirectToLogin) {
    redirect("/login");
  }
  const orders = result.data;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Comercio"
        title="Pedidos"
        description="Órdenes recibidas por la tienda. El cobro lo procesa la pasarela del comerciante (Wompi); Growup no custodia fondos."
      />

      {orders === null ? (
        <SectionError
          title="No se pudo cargar el listado de pedidos"
          error={result.error ?? { status: 0, code: null, message: "Respuesta inválida" }}
        />
      ) : (
      <div className="border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Fecha</th>
              <th className="px-4 py-3">Correo</th>
              <th className="px-4 py-3">Estado</th>
              <th className="px-4 py-3 text-right">Total</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {orders.items.map((order) => (
              <tr key={order.id} className="border-b border-slate-100 last:border-0">
                <td className="px-4 py-3 text-slate-500">
                  {new Date(order.created_at).toLocaleString("es-CO")}
                </td>
                <td className="px-4 py-3">{order.email}</td>
                <td className="px-4 py-3">
                  <span className="inline-flex border border-slate-200 px-2 py-0.5 text-xs">
                    {STATUS_LABEL[order.status] ?? order.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-right font-mono text-xs">
                  {formatPrice(order.total_cents)}
                </td>
                <td className="px-4 py-3 text-right">
                  <Link
                    href={`/orders/${order.id}`}
                    className="text-xs underline underline-offset-2 hover:text-slate-900"
                  >
                    Ver →
                  </Link>
                </td>
              </tr>
            ))}
            {orders.items.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-10 text-center text-slate-500">
                  Sin pedidos todavía.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
      )}

      {orders ? (
        <div className="flex items-center justify-between text-sm">
          <p className="text-slate-500">
            {orders.total} pedido{orders.total === 1 ? "" : "s"}
          </p>
          <div className="flex gap-2">
            {offset > 0 ? (
              <Link
                href={`/orders?offset=${Math.max(0, offset - limit)}`}
                className="border border-slate-200 px-3 py-1.5 hover:border-slate-400"
              >
                ← Anterior
              </Link>
            ) : null}
            {offset + limit < orders.total ? (
              <Link
                href={`/orders?offset=${offset + limit}`}
                className="border border-slate-200 px-3 py-1.5 hover:border-slate-400"
              >
                Siguiente →
              </Link>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
