"use client";

import { useState } from "react";

import { site } from "@/content/site";

const inputClass =
  "w-full border border-[var(--hairline)] bg-[var(--surface-2)] px-4 py-3 outline-none focus-visible:border-[var(--ink)]";

export default function SolicitarAccesoPage() {
  const [sent, setSent] = useState(false);

  function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);

    const name = String(data.get("nombre") ?? "").trim();
    const email = String(data.get("email") ?? "").trim();
    const store = String(data.get("tienda") ?? "").trim();
    const kind = String(data.get("tipo") ?? "ropa");
    const message = String(data.get("mensaje") ?? "").trim();

    const subject = `Solicitud de acceso growup — ${store || name}`;
    const body = [
      `Nombre: ${name}`,
      `Correo: ${email}`,
      `Tienda: ${store}`,
      `Tipo: ${kind}`,
      "",
      message,
    ].join("\n");

    window.location.href = `mailto:${site.contact_email}?subject=${encodeURIComponent(
      subject,
    )}&body=${encodeURIComponent(body)}`;
    setSent(true);
  }

  return (
    <section className="mx-auto max-w-2xl px-6 py-16 md:px-10 md:py-20">
      <p className="label text-[var(--muted)]">[ solicitar acceso ]</p>
      <h1 className="display mt-3 text-5xl leading-[0.95] md:text-6xl">
        Cupos de piloto.
        <br /> Te escribimos.
      </h1>
      <p className="mt-6 text-lg leading-relaxed text-[var(--muted)]">
        Déjanos tus datos y el equipo growup te contacta en menos de 24 h
        hábiles con propuesta, cupos y una llamada de 20 minutos. Sin tarjeta al
        pedir cupo.
      </p>

      {sent ? (
        <div role="status" className="mt-8 border border-[var(--hairline)] bg-[var(--surface-2)] p-6">
          <p className="display text-2xl">Correo en camino</p>
          <p className="mt-2 text-[var(--muted)]">
            Se abrió tu cliente de correo con la solicitud prellenada. Si no se
            abre, escríbenos directo a{" "}
            <a className="underline underline-offset-4" href={`mailto:${site.contact_email}`}>
              {site.contact_email}
            </a>
            .
          </p>
        </div>
      ) : (
        <form onSubmit={onSubmit} className="mt-8 space-y-4">
          <label className="block text-sm">
            <span className="mb-1 block label text-[var(--muted)]">Nombre</span>
            <input name="nombre" required autoComplete="name" className={inputClass} />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block label text-[var(--muted)]">Correo</span>
            <input name="email" type="email" required autoComplete="email" className={inputClass} />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block label text-[var(--muted)]">Nombre de la tienda</span>
            <input name="tienda" required className={inputClass} />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block label text-[var(--muted)]">Tipo de producto</span>
            <select name="tipo" defaultValue="ropa" className={inputClass}>
              <option value="ropa">Ropa</option>
              <option value="joyería">Joyería</option>
              <option value="otro">Otro</option>
            </select>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block label text-[var(--muted)]">Mensaje (opcional)</span>
            <textarea name="mensaje" rows={4} className={inputClass} />
          </label>
          {/* Honeypot anti-spam: los humanos no lo ven ni lo llenan. */}
          <div aria-hidden className="hidden">
            <label>
              No llenar
              <input name="website" tabIndex={-1} autoComplete="off" />
            </label>
          </div>
          <button
            type="submit"
            className="label inline-flex w-full items-center justify-center border border-[var(--ink)] bg-[var(--ink)] px-6 py-4 text-[var(--surface)] transition-colors hover:bg-[var(--signal)]"
          >
            Solicitar acceso →
          </button>
          <p className="label text-center text-[var(--muted)]">
            Sin tarjeta · respuesta &lt; 24 h hábiles · cupos limitados
          </p>
        </form>
      )}
    </section>
  );
}
