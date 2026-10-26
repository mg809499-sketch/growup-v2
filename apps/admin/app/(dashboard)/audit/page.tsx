import Link from "next/link";

import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { requireSession } from "@/lib/auth";
import { apiGet, queryString } from "@/lib/api";
import type { AuditLogListResponse, AuditVerifyResponse } from "@/lib/api";
import { formatDate } from "@/lib/format";

export default async function AuditPage({
  searchParams,
}: {
  searchParams: Promise<{
    action?: string;
    decision?: string;
    limit?: string;
    before_seq?: string;
  }>;
}) {
  const params = await searchParams;
  const { token } = await requireSession();
  const limit = Math.min(Number(params.limit) || 50, 100);

  const [page, verify] = await Promise.all([
    apiGet<AuditLogListResponse>(
      `/v1/admin/audit${queryString({
        action: params.action,
        decision: params.decision,
        limit,
        before_seq: params.before_seq,
      })}`,
      token,
    ),
    apiGet<AuditVerifyResponse>("/v1/admin/audit/verify", token),
  ]);

  const nextParams = new URLSearchParams();
  if (params.action) nextParams.set("action", params.action);
  if (params.decision) nextParams.set("decision", params.decision);
  nextParams.set("limit", String(limit));
  if (page.next_cursor) {
    nextParams.set("before_seq", String(page.next_cursor));
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Auditoría"
        title="Decisiones y cadena de integridad"
        description="Registro append-only de las decisiones de gobernanza del tenant."
      />

      <div
        className={`border px-4 py-3 text-sm ${
          verify.valid
            ? "border-emerald-200 bg-emerald-50 text-emerald-800"
            : "border-red-200 bg-red-50 text-red-800"
        }`}
      >
        <p className="font-medium">
          {verify.valid ? "Cadena válida" : "Cadena alterada"}
        </p>
        <p className="mono mt-1 text-[11px] opacity-80">
          chain_key: {verify.chain_key}
        </p>
      </div>

      <form className="flex flex-wrap items-end gap-3 border border-slate-200 bg-white p-4">
        <label className="block">
          <span className="mono block text-[10px] uppercase tracking-[0.14em] text-slate-500">
            Acción
          </span>
          <input
            className="mt-1 w-64 border border-slate-300 px-3 py-2 text-sm"
            type="search"
            name="action"
            defaultValue={params.action ?? ""}
            placeholder="catalog.update_product"
          />
        </label>
        <label className="block">
          <span className="mono block text-[10px] uppercase tracking-[0.14em] text-slate-500">
            Decisión
          </span>
          <select
            className="mt-1 border border-slate-300 px-3 py-2 text-sm"
            name="decision"
            defaultValue={params.decision ?? ""}
          >
            <option value="">Todas</option>
            <option value="ALLOW">ALLOW</option>
            <option value="DENY">DENY</option>
            <option value="HANDOFF">HANDOFF</option>
          </select>
        </label>
        <button
          className="bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          type="submit"
        >
          Filtrar
        </button>
        <Link
          className="mono px-2 py-2 text-[11px] text-slate-500 underline underline-offset-4"
          href="/audit"
        >
          Limpiar
        </Link>
      </form>

      {page.items.length === 0 ? (
        <EmptyState
          title="No hay decisiones con este filtro"
          description="El registro se llena a medida que se ejecutan acciones auditadas."
        />
      ) : (
        <div className="overflow-x-auto border border-slate-200 bg-white">
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50">
              <tr className="mono text-[10px] uppercase tracking-[0.12em] text-slate-500">
                <th className="px-4 py-3 font-medium">Seq</th>
                <th className="px-4 py-3 font-medium">Acción</th>
                <th className="px-4 py-3 font-medium">Decisión</th>
                <th className="px-4 py-3 font-medium">Razón</th>
                <th className="px-4 py-3 font-medium">Actor</th>
                <th className="px-4 py-3 font-medium">Fecha</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {page.items.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50">
                  <td className="mono px-4 py-3 text-[11px] text-slate-500">
                    {log.seq}
                  </td>
                  <td className="px-4 py-3">
                    <p className="font-medium">{log.action}</p>
                    <p className="mono mt-0.5 text-[10px] text-slate-400">
                      {log.policy_id} · {log.policy_version}
                    </p>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge value={log.decision} />
                  </td>
                  <td className="mono px-4 py-3 text-[11px] text-slate-600">
                    {log.reason_code}
                  </td>
                  <td className="mono px-4 py-3 text-[11px] text-slate-500">
                    {log.actor_type}:{log.actor_id ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {formatDate(log.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {page.next_cursor ? (
        <div className="flex justify-end">
          <Link
            className="border border-slate-300 bg-white px-3 py-1.5 text-sm hover:border-slate-950"
            href={`/audit?${nextParams.toString()}`}
          >
            Siguiente
          </Link>
        </div>
      ) : null}
    </div>
  );
}
