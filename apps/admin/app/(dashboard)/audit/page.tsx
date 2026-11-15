import { redirect } from "next/navigation";

import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { requireSession } from "@/lib/auth";
import { apiGetSafe, queryString } from "@/lib/api";
import type { AuditLogListResponse, AuditVerifyResponse } from "@/lib/api";
import { formatDate } from "@/lib/format";

const TEAM_MEMBERS = [
  {
    name: "Andrés Morales",
    email: "owner@mitiendadeportiva.co",
    role: "Administrador (Owner)",
    scope: "Acceso total, facturación DIAN, Wompi y publicación Edge",
    status: "active",
  },
  {
    name: "Laura Quintero",
    email: "bodega@mitiendadeportiva.co",
    role: "Gestor de Inventario",
    scope: "Catálogo, SKUs, stock multi-bodega y guías Coordinadora/Servientrega",
    status: "active",
  },
  {
    name: "Camilo Vega",
    email: "soporte@mitiendadeportiva.co",
    role: "Agente de Soporte",
    scope: "Supervisión de chat WhatsApp IA, pedidos y cambios",
    status: "active",
  },
];

export default async function AuditAndSettingsPage({
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

  const [pageResult, verifyResult] = await Promise.all([
    apiGetSafe<AuditLogListResponse>(
      `/v1/admin/audit${queryString({
        action: params.action,
        decision: params.decision,
        limit,
        before_seq: params.before_seq,
      })}`,
      token,
    ),
    apiGetSafe<AuditVerifyResponse>("/v1/admin/audit/verify", token),
  ]);

  if (pageResult.redirectToLogin || verifyResult.redirectToLogin) {
    redirect("/login");
  }

  const page = pageResult.data;
  const verify = verifyResult.data;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="4. Módulo: Infraestructura & Finanzas · Ajustes, Desarrolladores & Auditoría"
        title="Ajustes de Empresa, Facturación DIAN, Roles y Webhooks"
        description="Perfil fiscal y tributario (NIT/DIAN), identidad visual de checkout, control de accesos por rol, webhooks para desarrolladores y cadena inmutable de auditoría."
      />

      <div className="grid gap-6 lg:grid-cols-12">
        {/* Perfil de la empresa y DIAN */}
        <section className="vn-card space-y-4 p-6 lg:col-span-6">
          <div className="border-b border-black/10 pb-3">
            <p className="mono text-[10px] font-bold text-[#525866]">DATOS FISCALES &amp; FACTURACIÓN ELECTRÓNICA DIAN</p>
            <h2 className="display mt-1 text-lg font-bold text-[#0d0d0d]">
              Perfil de la Empresa
            </h2>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block text-xs font-medium text-[#525866]">
              Razón Social
              <input
                type="text"
                defaultValue="Mi Tienda Deportiva S.A.S."
                className="mt-1 w-full rounded-xl border border-black/15 bg-white px-3 py-2 text-sm text-[#0d0d0d]"
              />
            </label>
            <label className="block text-xs font-medium text-[#525866]">
              NIT &amp; Dígito de Verificación
              <input
                type="text"
                defaultValue="901.482.109-4"
                className="mt-1 w-full rounded-xl border border-black/15 bg-white px-3 py-2 font-mono text-sm text-[#0d0d0d]"
              />
            </label>
            <label className="block text-xs font-medium text-[#525866]">
              Régimen Tributario
              <input
                type="text"
                defaultValue="Responsable de IVA (19%)"
                className="mt-1 w-full rounded-xl border border-black/15 bg-white px-3 py-2 text-sm text-[#0d0d0d]"
              />
            </label>
            <label className="block text-xs font-medium text-[#525866]">
              Resolución Facturación DIAN
              <input
                type="text"
                defaultValue="18764000001982 · Prefijo FE"
                className="mt-1 w-full rounded-xl border border-black/15 bg-white px-3 py-2 font-mono text-sm text-[#0d0d0d]"
              />
            </label>
          </div>
          <button
            type="button"
            className="rounded-xl bg-[#0d0d0d] px-4 py-2 text-xs font-bold text-white hover:bg-zinc-800"
          >
            Guardar Perfil Fiscal y DIAN
          </button>
        </section>

        {/* Identidad visual y Desarrolladores / Webhooks */}
        <section id="webhooks" className="vn-card space-y-4 p-6 lg:col-span-6">
          <div className="border-b border-black/10 pb-3">
            <p className="mono text-[10px] font-bold text-[#525866]">IDENTIDAD VISUAL &amp; DESARROLLADORES API</p>
            <h2 className="display mt-1 text-lg font-bold text-[#0d0d0d]">
              Marca del Checkout y Webhooks (`order.*`)
            </h2>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block text-xs font-medium text-[#525866]">
              Tipografía Oficial
              <input
                type="text"
                readOnly
                value="Unbounded + Geist + Geist Mono"
                className="mt-1 w-full rounded-xl border border-black/15 bg-slate-50 px-3 py-2 text-xs font-bold text-[#0d0d0d]"
              />
            </label>
            <label className="block text-xs font-medium text-[#525866]">
              Eventos Webhook Suscritos
              <input
                type="text"
                readOnly
                value="order.created, order.paid, order.cancelled"
                className="mt-1 w-full rounded-xl border border-black/15 bg-slate-50 px-3 py-2 font-mono text-xs text-[#0d0d0d]"
              />
            </label>
          </div>

          <label className="block text-xs font-medium text-[#525866]">
            Endpoint Receptor de Webhooks (Firmado con HMAC-SHA256)
            <input
              type="url"
              defaultValue="https://mitiendadeportiva.growupstore.app/wp-json/growup/v1/orders-webhook"
              className="mt-1 w-full rounded-xl border border-black/15 bg-white px-3 py-2 font-mono text-xs text-[#0d0d0d]"
            />
          </label>

          <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
            <span className="mono text-[11px] font-semibold text-[#525866]">
              Documentación Swagger / OpenAPI v3.1 habilitada
            </span>
            <button
              type="button"
              className="rounded-xl bg-[#0d0d0d] px-4 py-2 text-xs font-bold text-white hover:bg-zinc-800"
            >
              Registrar Webhook
            </button>
          </div>
        </section>
      </div>

      {/* Control de accesos y roles */}
      <section className="vn-card overflow-x-auto admin-scroll">
        <div className="flex items-center justify-between border-b border-black/10 px-5 py-4">
          <p className="mono text-[10px] font-bold text-[#525866]">
            CONTROL DE ACCESOS Y ROLES DEL EQUIPO (ADMINISTRADOR · INVENTARIO · SOPORTE)
          </p>
          <button
            type="button"
            className="rounded-xl bg-[#0d0d0d] px-3.5 py-1.5 text-xs font-bold text-white"
          >
            + Invitar Miembro
          </button>
        </div>
        <table className="w-full text-left text-sm">
          <thead className="border-b border-black/10 bg-white/50 text-[11px] uppercase tracking-wider text-[#525866]">
            <tr>
              <th className="px-5 py-3.5">Nombre</th>
              <th className="px-5 py-3.5">Correo</th>
              <th className="px-5 py-3.5">Rol Asignado</th>
              <th className="px-5 py-3.5">Permisos Efectivos</th>
              <th className="px-5 py-3.5">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-black/10">
            {TEAM_MEMBERS.map((m) => (
              <tr key={m.email} className="hover:bg-black/[0.02]">
                <td className="px-5 py-3.5 font-semibold text-[#0d0d0d]">{m.name}</td>
                <td className="mono px-5 py-3.5 text-xs text-[#525866]">{m.email}</td>
                <td className="px-5 py-3.5 text-xs font-bold text-[#0d0d0d]">{m.role}</td>
                <td className="px-5 py-3.5 text-xs text-[#525866]">{m.scope}</td>
                <td className="px-5 py-3.5">
                  <StatusBadge value={m.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* Cadena de auditoría append-only */}
      <section className="vn-card overflow-x-auto admin-scroll">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-black/10 px-5 py-4">
          <p className="mono text-[10px] font-bold text-[#525866]">
            CADENA DE AUDITORÍA INMUTABLE (`decision_logs` · SHA-256)
          </p>
          {verify ? (
            <span className="rounded-full border border-emerald-300 bg-emerald-50 px-3 py-0.5 text-xs font-bold text-emerald-900">
              {verify.valid ? "✓ Cadena de Integridad Válida" : "Cadena Alterada"}
            </span>
          ) : null}
        </div>
        <table className="w-full text-left text-sm">
          <thead className="border-b border-black/10 bg-white/50 text-[11px] uppercase tracking-wider text-[#525866]">
            <tr>
              <th className="px-5 py-3.5">Acción</th>
              <th className="px-5 py-3.5">Decisión</th>
              <th className="px-5 py-3.5">Política</th>
              <th className="px-5 py-3.5">Fecha</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-black/10">
            {(page?.items ?? []).map((log) => (
              <tr key={log.id} className="hover:bg-black/[0.02]">
                <td className="mono px-5 py-3.5 text-xs font-bold text-[#0d0d0d]">{log.action}</td>
                <td className="px-5 py-3.5">
                  <StatusBadge value={log.decision} />
                </td>
                <td className="mono px-5 py-3.5 text-xs text-[#525866]">{log.policy_version}</td>
                <td className="px-5 py-3.5 text-xs text-[#525866]">{formatDate(log.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
