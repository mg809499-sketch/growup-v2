import { plans } from "@/content/plans";
import Link from "next/link";

export function PlanCarousel() {
  return (
    <div
      className="-mx-6 flex snap-x snap-mandatory gap-4 overflow-x-auto px-6 pb-4 md:mx-0 md:grid md:grid-cols-2 md:gap-6 md:overflow-visible md:px-0 md:pb-0"
      aria-label="Planes"
    >
      {plans.map((plan) => (
        <article
          key={plan.id}
          className="w-[300px] shrink-0 snap-center border border-[var(--hairline)] bg-[var(--surface-2)] p-6 md:w-auto"
        >
          <p className="label text-[var(--muted)]">Plan</p>
          <h3 className="display mt-2 text-4xl">{plan.name}</h3>
          <p className="mt-2 text-sm text-[var(--muted)]">{plan.tagline}</p>
          <dl className="mt-6 grid grid-cols-2 gap-3">
            {plan.features.slice(0, 6).map((feature) => (
              <div key={feature.label} className="border border-[var(--hairline)] p-3">
                <dt className="label text-[var(--muted)]">{feature.label}</dt>
                <dd className="mt-1 text-sm font-medium">{feature.value}</dd>
              </div>
            ))}
          </dl>
          <Link
            href={`/planes#${plan.id}`}
            className="label mt-6 inline-flex border border-[var(--ink)] px-4 py-2 transition-colors hover:bg-[var(--ink)] hover:text-[var(--surface)]"
          >
            Ver detalles →
          </Link>
        </article>
      ))}
    </div>
  );
}
