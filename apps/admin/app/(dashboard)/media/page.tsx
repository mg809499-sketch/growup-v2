import Link from "next/link";

import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { requireSession } from "@/lib/auth";
import { apiGet, queryString } from "@/lib/api";
import type { MediaAssetListResponse } from "@/lib/api";
import { formatBytes } from "@/lib/format";

export default async function MediaPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string; limit?: string }>;
}) {
  const params = await searchParams;
  const { token } = await requireSession();
  const limit = Math.min(Number(params.limit) || 50, 100);
  const page = await apiGet<MediaAssetListResponse>(
    `/v1/admin/media${queryString({ status: params.status, limit })}`,
    token,
  );

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Media"
        title="Biblioteca del tenant"
        description="Assets subidos a R2, estado de procesamiento, alt text y dimensiones."
      />

      <form className="flex flex-wrap items-end gap-3 border border-slate-200 bg-white p-4">
        <label className="block">
          <span className="mono block text-[10px] uppercase tracking-[0.14em] text-slate-500">
            Estado
          </span>
          <select
            className="mt-1 border border-slate-300 px-3 py-2 text-sm"
            name="status"
            defaultValue={params.status ?? ""}
          >
            <option value="">Todos</option>
            <option value="uploading">Uploading</option>
            <option value="ready">Ready</option>
            <option value="failed">Failed</option>
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
          href="/media"
        >
          Limpiar
        </Link>
      </form>

      {page.items.length === 0 ? (
        <EmptyState
          title="No hay media con este filtro"
          description="Sube imágenes desde el endpoint admin de media o cambia el estado."
        />
      ) : (
        <div className="overflow-x-auto border border-slate-200 bg-white">
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50">
              <tr className="mono text-[10px] uppercase tracking-[0.12em] text-slate-500">
                <th className="px-4 py-3 font-medium">Archivo</th>
                <th className="px-4 py-3 font-medium">Estado</th>
                <th className="px-4 py-3 font-medium">Tipo</th>
                <th className="px-4 py-3 font-medium">Tamaño</th>
                <th className="px-4 py-3 font-medium">Dimensiones</th>
                <th className="px-4 py-3 font-medium">Alt</th>
                <th className="px-4 py-3 font-medium">Clave R2</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {page.items.map((asset) => (
                <tr key={asset.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <p className="font-medium">
                      {asset.original_filename ?? "Sin nombre"}
                    </p>
                    <p className="mono mt-0.5 text-[10px] text-slate-400">
                      {asset.id}
                    </p>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge value={asset.status} />
                  </td>
                  <td className="mono px-4 py-3 text-[11px] text-slate-600">
                    {asset.mime}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {formatBytes(asset.size_bytes)}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {asset.width && asset.height
                      ? `${asset.width}×${asset.height}`
                      : "—"}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {asset.alt ?? "—"}
                  </td>
                  <td className="mono max-w-[280px] truncate px-4 py-3 text-[10px] text-slate-400">
                    {asset.r2_key}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
