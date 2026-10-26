function buildHref(
  basePath: string,
  params: Record<string, string | number | null | undefined>,
  offset: number,
  limit: number,
): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  }
  search.set("offset", String(offset));
  search.set("limit", String(limit));
  return `${basePath}?${search.toString()}`;
}

export function OffsetPagination({
  basePath,
  params,
  offset,
  limit,
  total,
}: {
  basePath: string;
  params: Record<string, string | number | null | undefined>;
  offset: number;
  limit: number;
  total: number;
}) {
  const hasPrevious = offset > 0;
  const hasNext = offset + limit < total;

  if (!hasPrevious && !hasNext) {
    return null;
  }

  return (
    <div className="flex items-center justify-between border-t border-slate-200 pt-4 text-sm">
      <p className="mono text-[11px] text-slate-500">
        {total === 0 ? 0 : offset + 1}–{Math.min(offset + limit, total)} de {total}
      </p>
      <div className="flex gap-2">
        {hasPrevious ? (
          <a
            className="border border-slate-300 bg-white px-3 py-1.5 hover:border-slate-950"
            href={buildHref(basePath, params, Math.max(0, offset - limit), limit)}
          >
            Anterior
          </a>
        ) : null}
        {hasNext ? (
          <a
            className="border border-slate-300 bg-white px-3 py-1.5 hover:border-slate-950"
            href={buildHref(basePath, params, offset + limit, limit)}
          >
            Siguiente
          </a>
        ) : null}
      </div>
    </div>
  );
}
