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
      <div className="flex flex-wrap items-end justify-between gap-4">
        <PageHeader
          eyebrow="Consola Staff · Multi-Tenants"
          title="Resumen de Multi-Tenants, Clientes y Tiendas"
          description="Control global de comercios activos, cuentas en trial, dominios asignados y congelamiento/activación instantánea con auditoría."
        />
        <a
          href="/platform/tenants/export"
          className="rounded-xl bg-[#0d0d0d] px-4 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-zinc-800"
        >
          Exportar Directorio CSV
        </a>
      </div>

      {forbidden ? (
        <div className="vn-card border-amber-300 px-5 py-4 text-sm text-[#0d0d0d]">
          Tu cuenta no tiene permiso `platform:tenants`. Esta vista solo está
          disponible para platform admins.
        </div>
      ) : (
        <>
          <form className="vn-card flex flex-wrap items-end gap-3 p-5">
            <label className="block min-w-[220px] flex-1">
              <span className="mono block text-[10px] font-semibold uppercase tracking-[0.14em] text-[#525866]">
                Buscar cliente, tienda o dominio
              </span>
              <input
                className="mt-1.5 w-full rounded-xl border border-black/15 bg-white/90 px-3.5 py-2 text-sm text-[#0d0d0d] placeholder:text-slate-400 focus:border-[#0d0d0d] focus:outline-none"
                type="search"
                name="q"
                defaultValue={params.q ?? ""}
                placeholder="Ej. sol-de-calle, joyeria, mitiendadeportiva..."
              />
            </label>
            <label className="block">
              <span className="mono block text-[10px] font-semibold uppercase tracking-[0.14em] text-[#525866]">
                Estado
              </span>
              <select
                className="mt-1.5 rounded-xl border border-black/15 bg-white/90 px-3.5 py-2 text-sm text-[#0d0d0d] focus:border-[#0d0d0d] focus:outline-none"
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
              className="rounded-xl bg-[#0d0d0d] px-5 py-2 text-sm font-bold text-white hover:bg-zinc-800"
              type="submit"
            >
              Filtrar
            </button>
            <Link
              className="mono px-3 py-2 text-[11px] font-semibold text-[#525866] underline underline-offset-4 hover:text-[#0d0d0d]"
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
              <div className="vn-card overflow-x-auto admin-scroll">
                <table className="w-full min-w-[900px] text-left text-sm">
                  <thead className="border-b border-black/10 bg-white/50">
                    <tr className="mono text-[10px] uppercase tracking-[0.12em] text-[#525866]">
                      <th className="px-5 py-3.5 font-semibold">Tienda / Cliente</th>
                      <th className="px-5 py-3.5 font-semibold">Estado</th>
                      <th className="px-5 py-3.5 font-semibold">Host Primario</th>
                      <th className="px-5 py-3.5 font-semibold">Plan</th>
                      <th className="px-5 py-3.5 font-semibold">Vencimiento Trial</th>
                      <th className="px-5 py-3.5 font-semibold">Creado</th>
                      <th className="px-5 py-3.5 text-right font-semibold">Acción Operativa</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-black/10">
                    {page.items.map((tenant) => (
                      <tr key={tenant.id} className="hover:bg-black/[0.02]">
                        <td className="px-5 py-4">
                          <p className="font-semibold text-[#0d0d0d]">{tenant.name}</p>
                          <p className="mono mt-0.5 text-[10px] text-[#525866]">
                            {tenant.slug}
                          </p>
                        </td>
                        <td className="px-5 py-4">
                          <StatusBadge value={tenant.status} />
                        </td>
                        <td className="mono px-5 py-4 text-[11px] font-semibold text-[#0d0d0d]">
                          {tenant.host ?? "—"}
                        </td>
                        <td className="mono px-5 py-4 text-[11px] font-bold text-[#0d0d0d]">
                          {tenant.plan_id ? "PRO / STARTER" : "TRIAL"}
                        </td>
                        <td className="px-5 py-4 text-[#525866]">
                          {formatDate(tenant.trial_ends_at)}
                        </td>
                        <td className="px-5 py-4 text-[#525866]">
                          {formatDate(tenant.created_at)}
                        </td>
                        <td className="px-5 py-4 text-right">
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
                              className="mono rounded-xl border border-black/15 bg-white px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.12em] text-[#0d0d0d] hover:bg-[#0d0d0d] hover:text-white"
                            >
                              {tenant.status === "suspended" ? "Activar Tienda" : "Pausar Tienda"}
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
