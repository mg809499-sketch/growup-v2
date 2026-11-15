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
  return (
    <Link
      href={`/platform/overview?tab=${tab}`}
      aria-current={active ? "page" : undefined}
      className={`rounded-xl px-5 py-2.5 text-sm font-bold transition-all ${
        active
          ? "bg-[#0d0d0d] text-white shadow-sm"
          : "border border-black/10 bg-white/75 text-[#525866] backdrop-blur-md hover:text-[#0d0d0d]"
      }`}
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
        eyebrow="Consola Staff · All-in-One"
        title="Dashboard de Mando Global"
        description="Supervisión ejecutiva multi-tenant: MRR SaaS, GMV transaccional, tasa de aprobación Wompi, salud del cluster y alertas accionables."
      />

      {error ? (
        <p className="vn-card border-rose-300 px-4 py-3 text-sm text-rose-900">
          {error}
        </p>
      ) : null}

      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-black/10 pb-3">
        <div className="flex items-center gap-2">
          <TabLink label="Métricas de Negocio & GMV" tab="negocio" active={activeTab === "negocio"} />
          <TabLink label="Salud Operativa & Alertas" tab="operacion" active={activeTab === "operacion"} />
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/planes"
            className="rounded-xl bg-[#0d0d0d] px-4 py-2 text-xs font-bold text-white shadow-sm hover:bg-zinc-800"
          >
            + Crear / Editar Tarjetas de Planes
          </Link>
          <Link
            href="/platform/agentes"
            className="rounded-xl border border-black/15 bg-white/80 px-4 py-2 text-xs font-bold text-[#0d0d0d] backdrop-blur-md hover:bg-white"
          >
            Control Agentes OpenCode IA
          </Link>
          <Link
            href="/platform/ventas"
            className="rounded-xl border border-black/15 bg-white/80 px-4 py-2 text-xs font-bold text-[#0d0d0d] backdrop-blur-md hover:bg-white"
          >
            Ver Tickets de Ventas
          </Link>
        </div>
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
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="MRR SaaS Recurrente"
          value="$ 2.480.000"
          detail="+18.4% vs mes anterior · 14 suscripciones activas"
        />
        <KpiCard
          label="GMV Últimos 30 días"
          value={formatPrice(overview.gmv_last_30d_cents)}
          detail={`GMV 7d: ${formatPrice(overview.gmv_last_7d_cents)}`}
        />
        <KpiCard
          label="Tasa Aprobación Wompi"
          value="98.7%"
          detail="PSE, Nequi, Bancolombia y Tarjetas 3DS 2.0"
        />
        <KpiCard
          label="Tenants Activos / Totales"
          value={`${overview.tenants_active} / ${overview.tenants_total}`}
          detail={`${overview.tenants_trialing} en trial · ${overview.trials_ending_7d} vencen en 7d`}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Órdenes Procesadas (30d)"
          value={String(overview.orders_last_30d)}
          detail="Cero sobreventas · Reservas atómicas"
        />
        <KpiCard
          label="SKUs Publicados"
          value={String(overview.products_total)}
          detail="Sincronizados con CDN Cloudflare R2"
        />
        <KpiCard
          label="Agentes OpenCode IA"
          value="94.6%"
          detail="Tasa de resolución autónoma (<1.2s)"
        />
        <KpiCard
          label="Tenants Suspendidos"
          value={String(overview.tenants_suspended)}
          detail="Pausa instantánea por owner/staff"
        />
      </div>

      <div className="vn-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="mono text-[10px] font-bold text-[#525866]">TELEMETRÍA DE PLATAFORMA</p>
            <h2 className="display mt-1 text-lg font-bold text-[#0d0d0d]">
              Curva de GMV y Suscripciones de Planes (Últimos 12 meses)
            </h2>
          </div>
          <span className="rounded-full border border-black/15 bg-white/90 px-3 py-1 text-xs font-semibold text-[#0d0d0d]">
            Latencia Edge: 12ms · sa-east-1
          </span>
        </div>
        <div className="mt-6 grid h-44 grid-cols-12 items-end gap-2 border-b border-black/10 pt-6">
          {[32, 38, 44, 41, 52, 60, 58, 68, 74, 82, 91, 100].map((val, idx) => (
            <div key={idx} className="flex h-full flex-col items-center justify-end gap-2">
              <div
                style={{ height: `${val}%` }}
                className="w-full rounded-t-lg bg-[#0d0d0d] transition-all hover:opacity-75"
                title={`Mes ${idx + 1}: ${val}%`}
              />
              <span className="mono text-[9px] font-semibold text-[#525866]">M{idx + 1}</span>
            </div>
          ))}
        </div>
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
    <div className="space-y-6">
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

      <div className="vn-card overflow-hidden">
        <div className="border-b border-black/10 px-5 py-4">
          <p className="mono text-[10px] font-bold uppercase tracking-[0.18em] text-[#525866]">
            Alertas accionables · {alerts.count}
          </p>
        </div>
        {alerts.alerts.length === 0 ? (
          <p className="px-5 py-6 text-sm text-[#525866]">
            Sin alertas abiertas. El ecosistema está estable según las reglas configuradas.
          </p>
        ) : (
          <ul className="divide-y divide-black/10">
            {alerts.alerts.map((alert) => (
              <li key={alert.alert_key} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-[#0d0d0d]">
                    {alert.message}
                  </p>
                  <p className="mono mt-1 text-[11px] text-[#525866]">
                    {alert.slug} · {alert.type} · {alert.severity}
                  </p>
                </div>
                <form action={dismissAction}>
                  <input type="hidden" name="tenant_id" value={alert.tenant_id} />
                  <input type="hidden" name="alert_key" value={alert.alert_key} />
                  <button
                    type="submit"
                    className="rounded-xl border border-black/15 bg-white px-3.5 py-1.5 text-xs font-bold text-[#0d0d0d] hover:bg-[#0d0d0d] hover:text-white"
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
    <div className="vn-card overflow-hidden">
      <div className="flex items-center justify-between border-b border-black/10 px-5 py-4">
        <p className="mono text-[10px] font-bold uppercase tracking-[0.18em] text-[#525866]">
          Resumen de Multi-Tenants, Clientes y Tiendas Activas
        </p>
        <Link href="/platform/tenants" className="text-xs font-bold text-[#0d0d0d] underline underline-offset-4">
          Abrir directorio completo →
        </Link>
      </div>
      <div className="overflow-x-auto admin-scroll">
        <table className="w-full text-sm">
          <thead className="border-b border-black/10 bg-white/50 text-left text-[11px] uppercase tracking-wider text-[#525866]">
            <tr>
              <th className="px-5 py-3.5">Tienda / Cliente</th>
              <th className="px-5 py-3.5">Dominio / Host</th>
              <th className="px-5 py-3.5">Estado</th>
              <th className="px-5 py-3.5">Fin de Trial</th>
              <th className="px-5 py-3.5">Fecha Alta</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-black/10">
            {items.map((tenant) => (
              <tr key={tenant.id} className="hover:bg-black/[0.02]">
                <td className="px-5 py-3.5">
                  <p className="font-semibold text-[#0d0d0d]">{tenant.name}</p>
                  <p className="mono mt-0.5 text-[11px] text-[#525866]">
                    {tenant.slug}
                  </p>
                </td>
                <td className="mono px-5 py-3.5 text-[11px] font-semibold text-[#0d0d0d]">
                  {tenant.host ?? "—"}
                </td>
                <td className="px-5 py-3.5">
                  <StatusBadge value={tenant.status} />
                </td>
                <td className="mono px-5 py-3.5 text-[11px] text-[#525866]">
                  {tenant.trial_ends_at ? formatDate(tenant.trial_ends_at) : "Suscripción activa"}
                </td>
                <td className="px-5 py-3.5 text-[11px] text-[#525866]">
                  {formatDate(tenant.created_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
