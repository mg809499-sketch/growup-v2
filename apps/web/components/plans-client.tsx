"use client";

import { useState } from "react";
import Link from "next/link";

import { Modal } from "@/components/modal";
import { annual_note, plans, show_pricing, trial_days } from "@/content/plans";
import type { Plan } from "@/content/plans";

export function PlansClient() {
  const [selected, setSelected] = useState<Plan | null>(null);

  return (
    <div>
      <div className="grid gap-6 md:grid-cols-2">
        {plans.map((plan) => (
          <article
            key={plan.id}
            id={plan.id}
            className="flex flex-col border border-[var(--hairline)] bg-[var(--surface-2)] p-6"
          >
            <p className="label text-[var(--muted)]">Plan</p>
            <h2 className="display mt-2 text-4xl">{plan.name}</h2>
            <p className="mt-2 text-sm text-[var(--muted)]">{plan.tagline}</p>
            <p className="label mt-4 text-[var(--signal)]">{plan.best_for}</p>

            <dl className="mt-6 grid grid-cols-2 gap-3">
              {plan.features.map((feature) => (
                <div key={feature.label} className="border border-[var(--hairline)] p-3">
                  <dt className="label text-[var(--muted)]">{feature.label}</dt>
                  <dd className="mt-1 text-sm font-medium">{feature.value}</dd>
                </div>
              ))}
            </dl>

            <ul className="mt-6 space-y-2 text-sm text-[var(--muted)]">
              {plan.limits.map((limit) => (
                <li key={limit} className="flex gap-2">
                  <span aria-hidden className="text-[var(--signal)]">■</span>
                  {limit}
                </li>
              ))}
            </ul>

            <button
              type="button"
              onClick={() => setSelected(plan)}
              className="label mt-6 inline-flex w-full items-center justify-center border border-[var(--ink)] bg-[var(--ink)] px-6 py-3 text-[var(--surface)] transition-colors hover:bg-[var(--signal)]"
            >
              {plan.cta}
            </button>
          </article>
        ))}
      </div>

      <p className="label mt-6 text-center text-[var(--muted)]">
        {trial_days} días de prueba · {annual_note}
        {show_pricing ? null : " · precios en revisión — nos escribimos"}
      </p>

      {selected ? (
        <Modal
          title={`${selected.name} — detalle y acceso`}
          onClose={() => setSelected(null)}
          describedBy={`plan-${selected.id}-detail`}
        >
          <div id={`plan-${selected.id}-detail`}>
            <p className="text-sm text-[var(--muted)]">{selected.best_for}</p>
            <dl className="mt-4 grid grid-cols-2 gap-3">
              {selected.features.map((feature) => (
                <div key={feature.label} className="border border-[var(--hairline)] p-3">
                  <dt className="label text-[var(--muted)]">{feature.label}</dt>
                  <dd className="mt-1 text-sm font-medium">{feature.value}</dd>
                </div>
              ))}
            </dl>
            <ul className="mt-4 space-y-2 text-sm text-[var(--muted)]">
              {selected.limits.map((limit) => (
                <li key={limit} className="flex gap-2">
                  <span aria-hidden className="text-[var(--signal)]">■</span>
                  {limit}
                </li>
              ))}
            </ul>
            <p className="mt-4 text-sm leading-relaxed">
              ¿Encaja con tu marca? Te abrimos la tienda con acceso asistido:
              catálogo inicial, tema, media y primer cobro de prueba incluidos.
            </p>
            <Link
              href="/solicitar-acceso"
              onClick={() => setSelected(null)}
              className="label mt-4 inline-flex w-full items-center justify-center border border-[var(--ink)] bg-[var(--ink)] px-6 py-3 text-[var(--surface)] transition-colors hover:bg-[var(--signal)]"
            >
              Solicitar acceso →
            </Link>
            <p className="label mt-3 text-center text-[var(--muted)]">
              Sin cobro hasta el día {trial_days + 1} · cancelas cuando quieras
            </p>
          </div>
        </Modal>
      ) : null}
    </div>
  );
}
