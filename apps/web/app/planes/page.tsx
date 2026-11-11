import type { Metadata } from "next";

import { PlansClient } from "@/components/plans-client";
import { annual_note, show_pricing, trial_days } from "@/content/plans";

export const metadata: Metadata = {
  title: "Planes — Starter y Pro",
  description:
    "Dos planes, una sola suscripción: Starter para empezar y Pro para operar en serio. Trial de 14 días, sin tarjeta al pedir cupo.",
};

const faqs = [
  {
    question: "¿Cuánto cuesta growup?",
    answer:
      "Estamos cerrando los precios públicos con nuestro equipo y contador. Hoy es trial de 14 días y una propuesta con precios según tu catálogo. Nos escribes y te la enviamos en menos de 24 h hábiles.",
  },
  {
    question: "¿Quién cobra las ventas?",
    answer:
      "Tu propia cuenta Wompi (la del comercio) cobra al comprador; growup nunca custodia fondos ni ve tus datos de pago. La suscripción de la plataforma (Starter/Pro) se cobra aparte con Stripe Billing.",
  },
  {
    question: "¿Y la factura electrónica?",
    answer:
      "Incluida: cada pago emite factura electrónica DIAN por API y las devoluciones generan nota crédito contra la factura original.",
  },
  {
    question: "¿El dominio?",
    answer:
      "Cada marca publica en {slug}.growup.com con TLS wildcard. Dominio propio (tu-marca.com) en fase 3 — ya está en el roadmap.",
  },
];

export default function PlanesPage() {
  return (
    <>
      <section className="hairline-b">
        <div className="mx-auto max-w-6xl px-6 py-16 md:px-10 md:py-20">
          <p className="label text-[var(--muted)]">[ planes ]</p>
          <h1 className="display mt-3 text-5xl leading-[0.95] md:text-7xl">
            Dos planes.
            <br />
            Cero letra chica.
          </h1>
          <p className="mt-6 max-w-md text-lg leading-relaxed text-[var(--muted)]">
            {trial_days} días de trial sin tarjeta. {annual_note}{" "}
            {show_pricing ? null : "Precios públicos en revisión — te los llevamos en la llamada de 20 minutos."}
          </p>
        </div>
      </section>

      <section aria-label="Comparativo" className="hairline-b">
        <div className="mx-auto max-w-6xl px-6 py-12 md:px-10">
          <PlansClient />
        </div>
      </section>

      <section aria-label="Preguntas frecuentes" className="mx-auto max-w-4xl px-6 py-14 md:px-10">
        <p className="label text-[var(--muted)]">[ preguntas frecuentes ]</p>
        <div className="mt-6 divide-y divide-[var(--hairline)] border border-[var(--hairline)]">
          {faqs.map((faq) => (
            <details key={faq.question} className="group p-5">
              <summary className="flex cursor-pointer items-center justify-between gap-4 font-medium">
                {faq.question}
                <span aria-hidden className="text-[var(--muted)] transition-transform group-open:rotate-45">+</span>
              </summary>
              <p className="mt-3 leading-relaxed text-[var(--muted)]">{faq.answer}</p>
            </details>
          ))}
        </div>
      </section>
    </>
  );
}
