import type { Metadata } from "next";

import { site } from "@/content/site";

export const metadata: Metadata = {
  title: "Consola — entra a tu tienda",
  description: "Administrador de tu tienda growup: catálogo, pedidos, media y auditoría.",
};

export default function ConsolaPage() {
  return (
    <section className="mx-auto max-w-3xl px-6 py-20 text-center md:px-10">
      <p className="label text-[var(--muted)]">[ consola ]</p>
      <h1 className="display mt-4 text-5xl leading-[0.95] md:text-7xl">
        Tu tienda
        <br /> te espera.
      </h1>
      <p className="mx-auto mt-6 max-w-md text-lg leading-relaxed text-[var(--muted)]">
        Entra al backoffice de tu tienda: catálogo, media, pedidos, facturación
        y auditoría — con tu cuenta de growup.
      </p>
      <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
        <a
          href={site.admin_login_url}
          className="label inline-flex border border-[var(--ink)] bg-[var(--ink)] px-8 py-4 text-[var(--surface)] transition-colors hover:bg-[var(--signal)]"
        >
          Entrar a mi tienda →
        </a>
        <a href={site.admin_login_url} className="label underline underline-offset-4 hover:opacity-60">
          ¿Aún no tienes tienda? Crea tu cuenta
        </a>
      </div>
      <p className="label mt-8 text-[var(--muted)]">{site.admin_url.replace(/^https?:\/\//, "")}</p>
    </section>
  );
}
