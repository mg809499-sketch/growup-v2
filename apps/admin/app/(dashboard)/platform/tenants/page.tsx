import Link from "next/link";

import { EmptyState } from "@/components/empty-state";
import { OffsetPagination } from "@/components/offset-pagination";
import { pauseTenantAction } from "@/app/(dashboard)/planes/actions";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { requireSession } from "@/lib/auth";
import { ApiError, apiGet, queryString } from "@/lib/api";
import type { PlatformTenantListResponse } from "@/lib/api";
import { formatDate } from "@/lib/format";

export default async function TenantsPage({
  searchParams,
}: {
  searchParams: Promise<{
    status?: string;
    q?: string;
    limit?: string;
    offset?: string;
  }>;
}) {
  const params = await searchParams;
  const { token } = await requireSession();
  const limit = Math.min(Number(params.limit) || 20, 100);
  const offset = Math.max(Number(params.offset) || 0, 0);

  let page: PlatformTenantListResponse | null = null;
  let forbidden = false;

  try {
    page = await apiGet<PlatformTenantListResponse>(
      `/v1/platform/tenants${queryString({
        status: params.status,
        q: params.q,
        limit,
        offset,
      })}`,
      token,
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 403) {
      forbidden = true;
    } else {
      throw error;
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Plataforma"
        title="Tenants"
        description="Listado cross-tenant para platform admins. Cada fila incluye host primario, plan, trial y estado."
      />
      <div className="flex justify-end">
        <a
          href="/platform/tenants/export"
          className="mono border border-slate-200 px-3 py-2 text-[11px] uppercase tracking-[0.14em] text-slate-600 hover:border-slate-400"
        >
          Exportar CSV
        </a>
      </div>

      {forbidden ? (
        <div className="border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          Tu cuenta no tiene permiso `platform:tenants`. Esta vista solo está
          disponible para platform admins.
        </div>
      ) : (
        <>
          <form className="flex flex-wrap items-end gap-3 border border-slate-200 bg-white p-4">
            <label className="block">
              <span className="mono block text-[10px] uppercase tracking-[0.14em] text-slate-500">
                Buscar
              </span>
              <input
                className="mt-1 w-64 border border-slate-300 px-3 py-2 text-sm"
                type="search"
                name="q"
                defaultValue={params.q ?? ""}
                placeholder="Slug o nombre"
              />
            </label>
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
                <option value="trialing">Trialing</option>
                <option value="active">Active</option>
                <option value="past_due">Past due</option>
                <option value="suspended">Suspended</option>
                <option value="canceled">Canceled</option>
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
              href="/platform/tenants"
            >
              Limpiar
            </Link>
          </form>

          {page && page.items.length === 0 ? (
            <EmptyState
              title="No hay tenants con este filtro"
              description="Prueba otro estado o una búsqueda distinta."
            />
          ) : null}

          {page && page.items.length > 0 ? (
            <>
              <div className="overflow-x-auto border border-slate-200 bg-white">
                <table className="w-full min-w-[900px] text-left text-sm">
                  <thead className="border-b border-slate-200 bg-slate-50">
                    <tr className="mono text-[10px] uppercase tracking-[0.12em] text-slate-500">
                      <th className="px-4 py-3 font-medium">Tenant</th>
                      <th className="px-4 py-3 font-medium">Estado</th>
                      <th className="px-4 py-3 font-medium">Host</th>
                      <th className="px-4 py-3 font-medium">Plan</th>
                      <th className="px-4 py-3 font-medium">Trial</th>
                      <th className="px-4 py-3 font-medium">Creado</th>
                      <th className="px-4 py-3 text-right font-medium">Pausa</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {page.items.map((tenant) => (
                      <tr key={tenant.id} className="hover:bg-slate-50">
                        <td className="px-4 py-3">
                          <p className="font-medium">{tenant.name}</p>
                          <p className="mono mt-0.5 text-[10px] text-slate-400">
                            {tenant.slug}
                          </p>
                        </td>
                        <td className="px-4 py-3">
                          <StatusBadge value={tenant.status} />
                        </td>
                        <td className="mono px-4 py-3 text-[11px] text-slate-600">
                          {tenant.host ?? "—"}
                        </td>
                        <td className="mono px-4 py-3 text-[11px] text-slate-500">
                          {tenant.plan_id ?? "—"}
                        </td>
                        <td className="px-4 py-3 text-slate-600">
                          {formatDate(tenant.trial_ends_at)}
                        </td>
                        <td className="px-4 py-3 text-slate-600">
                          {formatDate(tenant.created_at)}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <form
                            action={pauseTenantAction}
                            className="inline-flex items-center gap-2"
                          >
                            <input type="hidden" name="tenant_id" value={tenant.id} />
                            <input
                              type="hidden"
                              name="status"
                              value={tenant.status === "suspended" ? "active" : "suspended"}
                            />
                            <button
                              type="submit"
                              className={`mono border px-3 py-1.5 text-[10px] uppercase tracking-[0.12em] transition-colors ${
                                tenant.status === "suspended"
                                  ? "border-emerald-300 bg-emerald-50 text-emerald-700 hover:border-emerald-500"
                                  : "border-slate-200 text-slate-600 hover:border-slate-400"
                              }`}
                            >
                              {tenant.status === "suspended" ? "Activar" : "Pausar"}
                            </button>
                          </form>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <OffsetPagination
                basePath="/platform/tenants"
                params={{ status: params.status, q: params.q }}
                offset={page.offset}
                limit={page.limit}
                total={page.total}
              />
            </>
          ) : null}
        </>
      )}
    </div>
  );
}
