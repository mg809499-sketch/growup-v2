import Link from "next/link";
import { redirect } from "next/navigation";

import type { components } from "@growup/contracts";

import { KpiCard, RiskCard } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { SectionError } from "@/components/section-error";
import { StatusBadge } from "@/components/status-badge";
import { requireSession } from "@/lib/auth";
import { apiGetSafe } from "@/lib/api";
import { formatPrice, formatDate } from "@/lib/format";
import { dismissAlertAction } from "./actions";

export const dynamic = "force-dynamic";

type PlatformOverviewResponse = components["schemas"]["PlatformOverviewResponse"];
type PlatformAlertListResponse = components["schemas"]["PlatformAlertListResponse"];
type PlatformTenantListResponse = components["schemas"]["PlatformTenantListResponse"];

const TABS = ["negocio", "operacion"] as const;

function TabLink({
  label,
  tab,
  active,
}: {
  label: string;
  tab: (typeof TABS)[number];
  active: boolean;
}) {
  const className = `px-3 py-2 text-sm font-medium transition-colors ${
    active
      ? "border-b-2 border-slate-900 text-slate-900"
      : "text-slate-500 hover:text-slate-900"
  }`;
  return (
    <Link
      href={`/platform/overview?tab=${tab}`}
      aria-current={active ? "page" : undefined}
      className={className}
    >
      {label}
    </Link>
  );
}

export default async function PlatformOverviewPage({
  searchParams,
}: {
  searchParams: Promise<{ tab?: string; error?: string }>;
}) {
  const { tab, error } = await searchParams;
  const activeTab = TABS.includes(tab as never) ? (tab as (typeof TABS)[number]) : "negocio";

  const { token } = await requireSession();
  const [overviewResult, alertsResult, tenantsResult] = await Promise.all([
    apiGetSafe<PlatformOverviewResponse>("/v1/platform/overview", token),
    apiGetSafe<PlatformAlertListResponse>("/v1/platform/alerts", token),
    apiGetSafe<PlatformTenantListResponse>(
      "/v1/platform/tenants?limit=20",
      token,
    ),
  ]);

  if (overviewResult.redirectToLogin || alertsResult.redirectToLogin || tenantsResult.redirectToLogin) {
    redirect("/login");
  }
  const overview = overviewResult.data;
  const alerts = alertsResult.data;
  const tenants = tenantsResult.data;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Plataforma"
        title="Super consola"
        description="Panel ejecutivo del staff: KPIs agregados, salud multi-tenant y alertas accionables."
      />

      {error ? (
        <p className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </p>
      ) : null}

      <div className="flex items-center gap-4 border-b border-slate-200">
        <TabLink label="Negocio" tab="negocio" active={activeTab === "negocio"} />
        <TabLink label="Operación" tab="operacion" active={activeTab === "operacion"} />
      </div>

      {activeTab === "negocio" ? (
        <NegocioTab overview={overview} />
      ) : (
        <OperacionTab overview={overview} alerts={alerts} dismissAction={dismissAlertAction} />
      )}

      <TenantWatchlist items={tenants?.items ?? []} />
    </div>
  );
}

function NegocioTab({
  overview,
}: {
  overview: PlatformOverviewResponse | null;
}) {
  if (overview === null) {
    return (
      <SectionError
        title="No se pudo cargar el resumen ejecutivo"
        error={{ status: 0, code: null, message: "Respuesta inválida" }}
      />
    );
  }
  return (
    <div className="space-y-8">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Tenants totales" value={String(overview.tenants_total)} />
        <KpiCard label="Activos" value={String(overview.tenants_active)} />
        <KpiCard label="En trial" value={String(overview.tenants_trialing)} />
        <KpiCard
          label="Trials x 7d"
          value={String(overview.trials_ending_7d)}
          detail="Riesgo de conversión junior"
        />
        <KpiCard
          label="GMV últimos 7d"
          value={formatPrice(overview.gmv_last_7d_cents)}
        />
        <KpiCard
          label="GMV últimos 30d"
          value={formatPrice(overview.gmv_last_30d_cents)}
        />
        <KpiCard
          label="Órdenes últimos 30d"
          value={String(overview.orders_last_30d)}
        />
        <KpiCard
          label="Productos activos"
          value={String(overview.products_total)}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Suscripciones activas"
          value={String(overview.subscriptions_active)}
          detail="Placeholder: precio $0 hasta cerrar D-01"
        />
        <KpiCard label="Tenants suspendidos" value={String(overview.tenants_suspended)} />
        <KpiCard
          label="MRR real"
          value="$0"
          detail="La plataforma aún no cobra; precio pendiente de ratificación"
        />
        <KpiCard label="Suscripciones en riesgo" value="—" detail="Past due no implementado" />
      </div>
    </div>
  );
}

function OperacionTab({
  overview,
  alerts,
  dismissAction,
}: {
  overview: PlatformOverviewResponse | null;
  alerts: PlatformAlertListResponse | null;
  dismissAction: (formData: FormData) => Promise<void>;
}) {
  if (overview === null || alerts === null) {
    return (
      <SectionError
        title="No se pudo cargar el panel operativo"
        error={{ status: 0, code: null, message: "Respuesta inválida" }}
      />
    );
  }
  return (
    <div className="space-y-8">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <RiskCard
          label="Outbox atascado"
          value={String(overview.outbox_stuck)}
          severity={overview.outbox_stuck > 0 ? "critical" : "ok"}
          detail="Eventos sin publicar en >5 min"
        />
        <RiskCard
          label="Auditoría · Decisiones 7d"
          value={String(overview.audit_decisions_last_7d)}
          severity="ok"
          detail="Volumen de decisiones registradas"
        />
        <RiskCard
          label="Auditoría · Denegadas 7d"
          value={String(overview.audit_denied_last_7d)}
          severity={overview.audit_denied_last_7d > 0 ? "warn" : "ok"}
          detail="Acciones bloqueadas por gobernanza"
        />
        <RiskCard
          label="Media fallida"
          value={String(overview.media_failed)}
          severity={overview.media_failed > 0 ? "warn" : "ok"}
          detail="Assets con status=failed"
        />
      </div>

      <div className="border border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-4 py-3">
          <p className="mono text-[10px] uppercase tracking-[0.18em] text-slate-500">
            Alertas accionables · {alerts.count}
          </p>
        </div>
        {alerts.alerts.length === 0 ? (
          <p className="px-4 py-6 text-sm text-slate-500">
            Sin alertas abiertas. El ecosistema está estable según las reglas configuradas.
          </p>
        ) : (
          <ul className="divide-y divide-slate-200">
            {alerts.alerts.map((alert) => (
              <li key={alert.alert_key} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-900">
                    {alert.message}
                  </p>
                  <p className="mono mt-1 text-[11px] text-slate-500">
                    {alert.slug} · {alert.type} · {alert.severity}
                  </p>
                </div>
                <form action={dismissAction}>
                  <input type="hidden" name="tenant_id" value={alert.tenant_id} />
                  <input type="hidden" name="alert_key" value={alert.alert_key} />
                  <button
                    type="submit"
                    className="border border-slate-300 px-3 py-1 text-xs hover:border-slate-500"
                  >
                    Descartar
                  </button>
                </form>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function TenantWatchlist({
  items,
}: {
  items: Array<{
    id: string;
    slug: string;
    name: string;
    status: string;
    host: string | null;
    trial_ends_at: string | null;
    created_at: string;
  }>;
}) {
  return (
    <div className="border border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-4 py-3">
        <p className="mono text-[10px] uppercase tracking-[0.18em] text-slate-500">
          Tenants
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b text-left text-[10px] uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Tenant</th>
              <th className="px-4 py-3">Host</th>
              <th className="px-4 py-3">Estado</th>
              <th className="px-4 py-3">Trial ends</th>
              <th className="px-4 py-3">Creado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((tenant) => (
              <tr key={tenant.id} className="hover:bg-slate-50">
                <td className="px-4 py-3">
                  <p className="font-medium">{tenant.name}</p>
                  <p className="mono mt-0.5 text-[11px] text-slate-400">
                    {tenant.slug}
                  </p>
                </td>
                <td className="mono px-4 py-3 text-[11px] text-slate-600">
                  {tenant.host ?? "—"}
                </td>
                <td className="px-4 py-3">
                  <StatusBadge value={tenant.status} />
                </td>
                <td className="mono px-4 py-3 text-[11px] text-slate-500">
                  {tenant.trial_ends_at ? formatDate(tenant.trial_ends_at) : "—"}
                </td>
                <td className="px-4 py-3 text-[11px] text-slate-500">
                  {formatDate(tenant.created_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="border-t border-slate-200 px-4 py-2 text-right">
        <Link href="/platform/tenants" className="text-xs underline underline-offset-2 hover:text-slate-900">
          Ver todos los tenants →
        </Link>
      </div>
    </div>
  );
}
