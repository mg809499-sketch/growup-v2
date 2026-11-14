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
    "w-full border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-slate-500";

  return (
    <div className="border border-slate-200 bg-white">
      <div className="flex flex-wrap items-center justify-between gap-4 px-5 py-4">
        <div>
          <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">
            {plan.code}
          </p>
          <p className="mt-1 font-semibold text-slate-900">{plan.name}</p>
          <p className="mt-0.5 text-xs text-slate-500">
            {formatPrice(plan.price_cents)} · {plan.billing_interval === "year" ? "anual" : "mensual"} · prueba {plan.trial_days}d
            {plan.active ? "" : " · inactivo"}
          </p>
          {plan.badge ? (
            <span className="mono mt-1 inline-block border border-orange-200 bg-orange-50 px-2 py-0.5 text-[10px] uppercase text-orange-700">
              {plan.badge}
            </span>
          ) : null}
        </div>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="border border-slate-200 px-3 py-1.5 text-xs font-medium hover:border-slate-400"
        >
          {open ? "Cerrar" : "Editar"}
        </button>
      </div>

      {open ? (
        <form action={updatePlanAction} className="border-t border-slate-200 p-5">
          <input type="hidden" name="plan_id" value={plan.id} />
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block text-xs">
              Nombre
              <input className={`${fieldClass} mt-1`} name="name" defaultValue={plan.name} maxLength={200} required />
            </label>
            <label className="block text-xs">
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
            <label className="block text-xs">
              Moneda
              <input className={`${fieldClass} mt-1 font-mono text-xs`} name="currency" defaultValue={plan.currency} maxLength={3} required />
            </label>
            <label className="block text-xs">
              Intervalo
              <select className={`${fieldClass} mt-1`} name="billing_interval" defaultValue={plan.billing_interval}>
                <option value="month">Mensual</option>
                <option value="year">Anual</option>
              </select>
            </label>
            <label className="block text-xs">
              Días de prueba
              <input className={`${fieldClass} mt-1`} name="trial_days" type="number" min={0} max={365} defaultValue={plan.trial_days} required />
            </label>
            <label className="block text-xs">
              Sort order
              <input className={`${fieldClass} mt-1`} name="sort_order" type="number" min={0} max={10000} defaultValue={plan.sort_order} required />
            </label>
            <label className="block text-xs sm:col-span-2">
              Badge
              <input className={`${fieldClass} mt-1`} name="badge" defaultValue={plan.badge} maxLength={80} />
            </label>
            <label className="flex items-center gap-2 text-xs sm:col-span-2">
              <input type="checkbox" name="active" defaultChecked={plan.active} className="accent-slate-900" />
              Activo
            </label>
          </div>

          <label className="mt-3 block text-xs">
            Características (una por línea)
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
            className="mt-4 border border-slate-900 bg-slate-900 px-4 py-2 text-xs font-medium text-white hover:bg-slate-700"
          >
            Guardar plan
          </button>
        </form>
      ) : null}
    </div>
  );
}
