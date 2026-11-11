import Link from "next/link";

import { apiGet } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import { PageHeader } from "@/components/page-header";
import type { PageListResponse } from "@/lib/pages";
import { createPageAction } from "./actions";

export const dynamic = "force-dynamic";

const STATUS_LABEL: Record<string, string> = {
  draft: "Borrador",
  published: "Publicada",
  archived: "Archivada",
};

export default async function BuilderPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { token } = await requireSession();
  const params = await searchParams;
  const pages = await apiGet<PageListResponse>(
    "/v1/admin/pages?limit=100",
    token,
  );

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Contenido"
        title="Builder de páginas"
        description="Crea páginas por tenant, edita el layout en JSON con el block registry y publica con purga de caché. La versión publicada es la que ve el storefront."
      />

      {params.error ? (
        <p className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {params.error}
        </p>
      ) : null}

      <form
        action={createPageAction}
        className="flex flex-col gap-3 border border-slate-200 bg-white p-5 sm:flex-row sm:items-end"
      >
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">Slug</span>
          <input
            name="slug"
            required
            placeholder="home"
            pattern="[a-z0-9](?:[a-z0-9/-]{0,126}[a-z0-9])?"
            className="w-48 border border-slate-200 px-3 py-2 outline-none focus:border-slate-400"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">Título</span>
          <input
            name="title"
            required
            placeholder="Inicio"
            className="w-64 border border-slate-200 px-3 py-2 outline-none focus:border-slate-400"
          />
        </label>
        <button
          type="submit"
          className="border border-slate-900 bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
        >
          Crear página
        </button>
      </form>

      <div className="border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Slug</th>
              <th className="px-4 py-3">Título</th>
              <th className="px-4 py-3">Estado</th>
              <th className="px-4 py-3">Actualizada</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {pages.items.map((page) => (
              <tr key={page.id} className="border-b border-slate-100 last:border-0">
                <td className="px-4 py-3 font-mono text-xs">{page.slug}</td>
                <td className="px-4 py-3">{page.title}</td>
                <td className="px-4 py-3">
                  <span className="inline-flex border border-slate-200 px-2 py-0.5 text-xs">
                    {STATUS_LABEL[page.status] ?? page.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-500">
                  {new Date(page.updated_at).toLocaleString("es-CO")}
                </td>
                <td className="px-4 py-3 text-right">
                  <Link
                    href={`/builder/${page.id}`}
                    className="text-xs underline underline-offset-2 hover:text-slate-900"
                  >
                    Editar →
                  </Link>
                </td>
              </tr>
            ))}
            {pages.items.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                  Sin páginas todavía. Crea la primera (p. ej. «home»).
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
