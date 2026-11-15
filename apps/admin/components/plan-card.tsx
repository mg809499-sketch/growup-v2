"use client";

import { useState } from "react";

import { updatePlanAction } from "@/app/(dashboard)/planes/actions";
import type { PlanOut } from "@/lib/api";
import { formatPrice } from "@/lib/format";

export function PlanCard({ plan }: { plan: PlanOut }) {
  const [open, setOpen] = useState(false);
  const [featuresText, setFeaturesText] = useState(
    (plan.features ?? []).join("\n"),
  );
  const fieldClass =
    "w-full rounded-xl border border-black/15 bg-white/90 px-3 py-2 text-sm text-[#0d0d0d] outline-none focus:border-[#0d0d0d]";

  return (
    <div className="vn-card flex flex-col justify-between overflow-hidden transition-all hover:border-black/25">
      <div className="p-6">
        <div className="flex items-start justify-between gap-3">
          <div>
            <span className="mono text-[10px] font-bold uppercase tracking-[0.18em] text-[#525866]">
              CÓDIGO: {plan.code} · ORDEN #{plan.sort_order}
            </span>
            <h3 className="display mt-1 text-xl font-extrabold text-[#0d0d0d]">
              {plan.name}
            </h3>
          </div>
          {plan.badge ? (
            <span className="mono rounded-full border border-black/15 bg-slate-100 px-3 py-1 text-[10px] font-bold uppercase text-[#0d0d0d]">
              {plan.badge}
            </span>
          ) : null}
        </div>

        <div className="mt-4 flex items-baseline gap-2">
          <span className="display text-3xl font-extrabold text-[#0d0d0d]">
            {formatPrice(plan.price_cents)}
          </span>
          <span className="text-xs text-[#525866]">
            / {plan.billing_interval === "year" ? "año" : "mes"} · Trial {plan.trial_days} días
          </span>
        </div>

        {plan.description ? (
          <p className="mt-2 text-xs text-[#525866]">{plan.description}</p>
        ) : null}

        <ul className="mt-4 space-y-2 border-t border-black/10 pt-4 text-xs text-[#0d0d0d]">
          {(plan.features ?? []).map((feature, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <span className="font-bold text-emerald-700">✓</span>
              <span>{feature}</span>
            </li>
          ))}
        </ul>

        <div className="mt-5 flex items-center justify-between border-t border-black/10 pt-4">
          <span
            className={`mono text-[10px] font-bold uppercase ${
              plan.active ? "text-emerald-700" : "text-rose-700"
            }`}
          >
            {plan.active ? "● Visible en Home Growup" : "○ Oculto en Home"}
          </span>
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            className="rounded-xl border border-black/15 bg-white/80 px-3.5 py-1.5 text-xs font-bold text-[#0d0d0d] hover:bg-[#0d0d0d] hover:text-white"
          >
            {open ? "Cerrar editor" : "Editar tarjeta"}
          </button>
        </div>
      </div>

      {open ? (
        <form action={updatePlanAction} className="border-t border-black/10 bg-slate-50/80 p-5">
          <input type="hidden" name="plan_id" value={plan.id} />
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block text-xs font-medium text-[#525866]">
              Nombre en la tarjeta
              <input className={`${fieldClass} mt-1`} name="name" defaultValue={plan.name} maxLength={200} required />
            </label>
            <label className="block text-xs font-medium text-[#525866]">
              Precio (centavos COP)
              <input
                className={`${fieldClass} mt-1 font-mono text-xs`}
                name="price_cents"
                type="number"
                min={0}
                step={100}
                defaultValue={plan.price_cents}
                required
              />
            </label>
            <label className="block text-xs font-medium text-[#525866]">
              Moneda
              <input className={`${fieldClass} mt-1 font-mono text-xs`} name="currency" defaultValue={plan.currency} maxLength={3} required />
            </label>
            <label className="block text-xs font-medium text-[#525866]">
              Intervalo de cobro
              <select className={`${fieldClass} mt-1`} name="billing_interval" defaultValue={plan.billing_interval}>
                <option value="month">Mensual</option>
                <option value="year">Anual</option>
              </select>
            </label>
            <label className="block text-xs font-medium text-[#525866]">
              Días de prueba (Trial)
              <input className={`${fieldClass} mt-1`} name="trial_days" type="number" min={0} max={365} defaultValue={plan.trial_days} required />
            </label>
            <label className="block text-xs font-medium text-[#525866]">
              Orden en carrusel Home
              <input className={`${fieldClass} mt-1`} name="sort_order" type="number" min={0} max={10000} defaultValue={plan.sort_order} required />
            </label>
            <label className="block text-xs font-medium text-[#525866] sm:col-span-2">
              Badge destacado (ej. MÁS ELEGIDO, PILOTO, ALL-IN-ONE)
              <input className={`${fieldClass} mt-1`} name="badge" defaultValue={plan.badge} maxLength={80} />
            </label>
            <label className="flex items-center gap-2 text-xs font-semibold text-[#0d0d0d] sm:col-span-2">
              <input type="checkbox" name="active" defaultChecked={plan.active} className="accent-[#0d0d0d]" />
              Publicar esta tarjeta en el Home de growup.com
            </label>
          </div>

          <label className="mt-3 block text-xs font-medium text-[#525866]">
            Beneficios que aparecen en la tarjeta (uno por línea)
            <textarea
              name="features"
              rows={4}
              className={`${fieldClass} mt-1 resize-y text-xs leading-relaxed`}
              value={featuresText}
              onChange={(event) => setFeaturesText(event.target.value)}
            />
          </label>

          <button
            type="submit"
            className="mt-4 w-full rounded-xl bg-[#0d0d0d] px-4 py-2.5 text-xs font-bold text-white hover:bg-zinc-800"
          >
            Guardar y sincronizar con Home Growup
          </button>
        </form>
      ) : null}
    </div>
  );
}
