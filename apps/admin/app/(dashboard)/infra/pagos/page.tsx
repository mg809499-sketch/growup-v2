"use client";

import { useState } from "react";

import { KpiCard } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";

const PAYOUT_HISTORY = [
  {
    id: "LIQ-2026-114",
    date: "14 Nov 2026 · 18:00",
    bank: "Bancolombia · Cuenta Corriente *8901",
    gross: "$ 12.400.000 COP",
    fee: "$ 364.800 COP (2.65% + $700)",
    net: "$ 12.035.200 COP",
    status: "paid",
  },
  {
    id: "LIQ-2026-113",
    date: "07 Nov 2026 · 18:00",
    bank: "Bancolombia · Cuenta Corriente *8901",
    gross: "$ 9.850.000 COP",
    fee: "$ 289.225 COP (2.65% + $700)",
    net: "$ 9.560.775 COP",
    status: "paid",
  },
];

export default function PagosWompiPage() {
  const [sandboxMode, setSandboxMode] = useState(false);
  const [amountCop, setAmountCop] = useState(189900);

  const wompiFee = Math.round(amountCop * 0.0265 + 700);
  const ivaOnFee = Math.round(wompiFee * 0.19);
  const netDispersed = Math.max(0, amountCop - wompiFee - ivaOnFee);

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="4. Módulo: Infraestructura & Finanzas · Pasarelas & Pagos (Wompi Gateway)"
        title="Pasarela Wompi Colombia & Liquidaciones Bancarias"
        description="Configuración de llaves públicas/privadas (Producción y Sandbox), switches por método de pago (PSE, Nequi, Daviplata, Tarjetas 3DS 2.0) y simulador transparente de comisiones."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Estado de Integración" value={sandboxMode ? "Modo Sandbox" : "Producción Live"} detail="Merchant of Record: Tu Tienda (Cero custodia)" />
        <KpiCard label="Tasa de Aprobación" value="98.7%" detail="Protocolo 3D Secure 2.0 activo" />
        <KpiCard label="Tarifa Procesamiento" value="2.65% + $700" detail="Dispersión T+1 a cuenta bancaria" />
        <KpiCard label="Cumplimiento PCI-DSS" value="SAQ A" detail="Cero PAN/CVV almacenado en Growup" />
      </div>

      <div className="grid gap-6 lg:grid-cols-12">
        {/* Credenciales API y Métodos de Pago */}
        <section className="vn-card space-y-4 p-6 lg:col-span-7">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-black/10 pb-3">
            <div>
              <p className="mono text-[10px] font-bold text-[#525866]">CREDENCIALES DEL COMERCIANTE</p>
              <h2 className="display mt-1 text-lg font-bold text-[#0d0d0d]">
                Llaves API Wompi &amp; Métodos Habilitados
              </h2>
            </div>
            <button
              type="button"
              onClick={() => setSandboxMode((v) => !v)}
              className="rounded-xl border border-black/15 bg-white px-3.5 py-1.5 text-xs font-bold text-[#0d0d0d] hover:bg-[#0d0d0d] hover:text-white"
            >
              Cambiar a {sandboxMode ? "Producción Live" : "Modo Pruebas (Sandbox)"}
            </button>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block text-xs font-medium text-[#525866]">
              Llave Pública ({sandboxMode ? "pub_test_*" : "pub_prod_*"})
              <input
                type="text"
                readOnly
                value={sandboxMode ? "pub_test_Q5yDA9xoKdePzhSGeVe9HAez7" : "pub_prod_98a7b6c5d4e3f2g1h0j9k8l7"}
                className="mt-1 w-full rounded-xl border border-black/15 bg-slate-50 px-3 py-2 font-mono text-xs text-[#0d0d0d]"
              />
            </label>
            <label className="block text-xs font-medium text-[#525866]">
              Secreto de Eventos (Webhook SHA-256)
              <input
                type="password"
                readOnly
                value="events_secret_cifrado_aes_gcm"
                className="mt-1 w-full rounded-xl border border-black/15 bg-slate-50 px-3 py-2 font-mono text-xs text-[#0d0d0d]"
              />
            </label>
          </div>

          <div className="space-y-2 pt-2">
            <p className="mono text-[10px] font-bold text-[#525866]">SWITCHES DE MÉTODOS DE PAGO EN CHECKOUT</p>
            <div className="grid gap-2.5 sm:grid-cols-2">
              {[
                { name: "PSE (Todos los bancos colombianos)", active: true },
                { name: "Botón Nequi Directo (Push 1-Click)", active: true },
                { name: "Daviplata Directo", active: true },
                { name: "Tarjetas Crédito/Débito (3D Secure 2.0)", active: true },
              ].map((m) => (
                <label
                  key={m.name}
                  className="flex items-center justify-between rounded-xl border border-black/10 bg-white/90 px-3.5 py-2.5 text-xs font-semibold text-[#0d0d0d]"
                >
                  <span>{m.name}</span>
                  <input type="checkbox" defaultChecked={m.active} className="h-4 w-4 accent-[#0d0d0d]" />
                </label>
              ))}
            </div>
          </div>
        </section>

        {/* Calculadora transparente de comisiones */}
        <section className="vn-card flex flex-col justify-between p-6 lg:col-span-5">
          <div>
            <p className="mono text-[10px] font-bold text-[#525866]">SIMULADOR DE COSTOS Y DISPERSIÓN</p>
            <h2 className="display mt-1 text-lg font-bold text-[#0d0d0d]">
              Calculadora de Comisiones (2.65% + $700 COP)
            </h2>

            <label className="mt-4 block text-xs font-medium text-[#525866]">
              Monto de la venta en COP
              <input
                type="number"
                value={amountCop}
                onChange={(e) => setAmountCop(Math.max(0, Number(e.target.value) || 0))}
                className="mt-1 w-full rounded-xl border border-black/15 bg-white px-3.5 py-2 font-mono text-base font-bold text-[#0d0d0d]"
              />
            </label>

            <dl className="mt-4 space-y-2.5 rounded-2xl border border-black/10 bg-white/90 p-4 text-xs">
              <div className="flex justify-between">
                <dt className="text-[#525866]">Comisión Wompi (2.65% + $700):</dt>
                <dd className="mono font-bold text-[#0d0d0d]">$ {wompiFee.toLocaleString("es-CO")} COP</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-[#525866]">IVA sobre comisión (19%):</dt>
                <dd className="mono font-bold text-[#0d0d0d]">$ {ivaOnFee.toLocaleString("es-CO")} COP</dd>
              </div>
              <div className="flex justify-between border-t border-black/10 pt-2.5 text-sm">
                <dt className="font-bold text-[#0d0d0d]">Neto a recibir en tu banco:</dt>
                <dd className="mono font-extrabold text-emerald-800">
                  $ {netDispersed.toLocaleString("es-CO")} COP
                </dd>
              </div>
            </dl>
          </div>

          <p className="mt-4 text-[11px] text-[#525866]">
            Tiempo de dispersión: 24 horas hábiles a cuenta corriente o de ahorros.
          </p>
        </section>
      </div>

      {/* Historial de liquidaciones bancarias */}
      <div className="vn-card overflow-x-auto admin-scroll">
        <div className="border-b border-black/10 px-5 py-4">
          <p className="mono text-[10px] font-bold text-[#525866]">
            HISTORIAL DE LIQUIDACIONES BANCARIAS AUTOMÁTICAS
          </p>
        </div>
        <table className="w-full text-left text-sm">
          <thead className="border-b border-black/10 bg-white/50 text-[11px] uppercase tracking-wider text-[#525866]">
            <tr>
              <th className="px-5 py-3.5">ID Liquidación</th>
              <th className="px-5 py-3.5">Fecha</th>
              <th className="px-5 py-3.5">Cuenta Destino</th>
              <th className="px-5 py-3.5">Bruto Procesado</th>
              <th className="px-5 py-3.5">Costo Pasarela</th>
              <th className="px-5 py-3.5">Neto Transferido</th>
              <th className="px-5 py-3.5">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-black/10">
            {PAYOUT_HISTORY.map((row) => (
              <tr key={row.id} className="hover:bg-black/[0.02]">
                <td className="mono px-5 py-4 text-xs font-bold text-[#0d0d0d]">{row.id}</td>
                <td className="px-5 py-4 text-xs text-[#525866]">{row.date}</td>
                <td className="px-5 py-4 text-xs font-semibold text-[#0d0d0d]">{row.bank}</td>
                <td className="mono px-5 py-4 text-xs text-[#0d0d0d]">{row.gross}</td>
                <td className="mono px-5 py-4 text-xs text-[#525866]">{row.fee}</td>
                <td className="mono px-5 py-4 text-xs font-bold text-emerald-800">{row.net}</td>
                <td className="px-5 py-4">
                  <StatusBadge value={row.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
