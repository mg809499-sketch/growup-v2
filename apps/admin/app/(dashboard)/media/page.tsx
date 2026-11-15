import Link from "next/link";
import { redirect } from "next/navigation";

import { updateMediaAltAction } from "@/app/(dashboard)/media/actions";
import { MediaUploader } from "@/components/media-uploader";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { SectionError } from "@/components/section-error";
import { StatusBadge } from "@/components/status-badge";
import { requireSession } from "@/lib/auth";
import { apiGetSafe, queryString } from "@/lib/api";
import type { MediaAssetListResponse } from "@/lib/api";
import { formatBytes } from "@/lib/format";

export default async function MediaPage({
  searchParams,
}: {
  searchParams: Promise<{
    status?: string;
    limit?: string;
    offset?: string;
    error?: string;
  }>;
}) {
  const params = await searchParams;
  const { token } = await requireSession();
  const requestedLimit = Number(params.limit);
  const limit =
    Number.isInteger(requestedLimit) && requestedLimit >= 1 && requestedLimit <= 100
      ? requestedLimit
      : 50;
  const requestedOffset = Number(params.offset);
  const offset =
    Number.isSafeInteger(requestedOffset) &&
    requestedOffset >= 0 &&
    requestedOffset <= 1_000_000
      ? requestedOffset
      : 0;
  const result = await apiGetSafe<MediaAssetListResponse>(
    `/v1/admin/media${queryString({ status: params.status, limit, offset })}`,
    token,
  );
  if (result.redirectToLogin) {
    redirect("/login");
  }
  const page = result.data;
  const previousOffset = Math.max(0, offset - limit);
  const nextOffset = offset + (page?.items.length ?? 0);
  const pageHref = (targetOffset: number) => {
    const query = new URLSearchParams({
      limit: String(limit),
      offset: String(targetOffset),
    });
    if (params.status) {
      query.set("status", params.status);
    }
    return `/media?${query.toString()}`;
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Media"
        title="Biblioteca del tenant"
        description="Assets subidos a R2, estado de procesamiento, alt text y dimensiones."
      />

      {params.error ? (
        <p className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {params.error}
        </p>
      ) : null}

      <section className="border border-slate-200 bg-white p-4 text-sm text-slate-700">
        <p className="mono text-[10px] uppercase tracking-[0.14em] text-slate-500">
          Uso en landing y formatos recomendados
        </p>
        <ul className="mt-2 grid gap-1.5 sm:grid-cols-2">
          <li><strong>Logo:</strong> 512×512 px · PNG/WebP/SVG · fondo transparente</li>
          <li><strong>Banner hero:</strong> 1920×600 px · WebP/JPG · &lt; 400 KB</li>
          <li><strong>Hero full:</strong> 2560×1440 px · WebP/JPG</li>
          <li><strong>Producto:</strong> 1200×1200 px · WebP/JPG · cuadrado</li>
          <li><strong>Miniatura:</strong> 400×400 px · WebP/JPG</li>
        </ul>
        <p className="mt-2 text-xs text-slate-500">
          Al subir, indica el uso (logo/banner/producto) en el campo Alt para que el builder lo asigne automáticamente.
        </p>
      </section>

      <MediaUploader />

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

      {page === null ? (
        <SectionError
          title="No se pudo cargar la biblioteca de media"
          error={result.error ?? { status: 0, code: null, message: "Respuesta inválida" }}
        />
      ) : page.items.length === 0 ? (
        <EmptyState
          title="No hay media con este filtro"
          description="Sube imágenes arriba o cambia el filtro de estado."
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
                <th className="px-4 py-3 font-medium">Alt (editable)</th>
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
                  <td className="px-4 py-3">
                    <form
                      action={updateMediaAltAction}
                      className="flex min-w-[240px] items-center gap-2"
                    >
                      <input
                        type="hidden"
                        name="media_asset_id"
                        value={asset.id}
                      />
                      <input
                        className="w-full border border-slate-300 px-2 py-1 text-xs"
                        name="alt"
                        defaultValue={asset.alt ?? ""}
                        maxLength={300}
                        required
                        aria-label="Alt text"
                      />
                      <button
                        className="mono shrink-0 border border-slate-300 px-2 py-1 text-[10px] uppercase tracking-[0.08em] hover:border-slate-950"
                        type="submit"
                      >
                        Guardar
                      </button>
                    </form>
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
      {page ? (
        <nav
          aria-label="Paginación de media"
          className="flex items-center justify-between gap-4 text-sm"
        >
          <p className="text-slate-500">
            {page.total === 0
              ? "0 assets"
              : `${offset + 1}–${offset + page.items.length} de ${page.total}`}
          </p>
          <div className="flex gap-2">
            <Link
              aria-disabled={offset === 0}
              className={`border px-3 py-2 ${
                offset === 0
                  ? "pointer-events-none border-slate-200 text-slate-300"
                  : "border-slate-300 hover:border-slate-950"
              }`}
              href={pageHref(previousOffset)}
            >
              Anterior
            </Link>
            <Link
              aria-disabled={nextOffset >= page.total}
              className={`border px-3 py-2 ${
                nextOffset >= page.total
                  ? "pointer-events-none border-slate-200 text-slate-300"
                  : "border-slate-300 hover:border-slate-950"
              }`}
              href={pageHref(nextOffset)}
            >
              Siguiente
            </Link>
          </div>
        </nav>
      ) : null}
    </div>
  );
}
