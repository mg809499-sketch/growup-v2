import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { SuggestionActionForm } from "@/components/suggestion-action-form";
import { requireSession } from "@/lib/auth";
import { apiGetSafe } from "@/lib/api";

export const dynamic = "force-dynamic";

type Suggestion = {
  id: string;
  type: string;
  status: string;
  payload: Record<string, unknown>;
  proposed_at: string;
};

export default async function SuggestionsPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string; error?: string }>;
}) {
  const { token } = await requireSession();
  const { status, error } = await searchParams;
  const validStatus = ["pending", "accepted", "applied", "dismissed", "all"] as const;
  const filter = validStatus.includes((status as never) ?? "pending")
    ? ((status as (typeof validStatus)[number]) ?? "pending")
    : "pending";

  const result = await apiGetSafe<{ items: Suggestion[]; total: number }>(
    `/v1/admin/inventory/suggestions?status=${filter}&limit=50`,
    token,
  );
  const items = (result.data as { items: Suggestion[] }).items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Inventario"
        title="Sugerencias de reorden"
        description="Recomendaciones rule-based para mantener stock; nadie ejecuta cambios sin aprobación humana."
      />

      {error ? (
        <p className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </p>
      ) : null}

      <div className="flex gap-2 text-xs">
        {validStatus.map((s) => (
          <Link
            key={s}
            href={`/suggestions?status=${s}`}
            className={`border px-3 py-1.5 font-medium ${
              s === filter
                ? "border-slate-900 bg-slate-900 text-white"
                : "border-slate-200 text-slate-600 hover:border-slate-400"
            }`}
          >
            {s}
          </Link>
        ))}
      </div>

      <div className="space-y-3">
        {items.map((item) => {
          const sku = String(item.payload?.sku ?? "—");
          const stock = String(item.payload?.stock ?? "—");
          const threshold = String(item.payload?.threshold ?? "—");
          return (
            <div key={item.id} className="border border-slate-200 bg-white p-4">
              <p className="mono text-[10px] uppercase tracking-[0.14em] text-slate-500">
                {item.type} · {item.status}
              </p>
              <p className="mt-1 font-medium text-slate-900">
                Reordenar <span className="font-mono">{sku}</span>
              </p>
              <p className="mt-1 text-xs text-slate-600">
                Stock {stock} · mínimo {threshold} · propuesto{" "}
                {new Date(item.proposed_at).toLocaleString("es-CO")}
              </p>
              {item.status === "pending" ? <SuggestionActionForm id={item.id} /> : null}
            </div>
          );
        })}
        {items.length === 0 ? (
          <p className="text-sm text-slate-500">No hay sugerencias con este estado.</p>
        ) : null}
      </div>
    </div>
  );
}
