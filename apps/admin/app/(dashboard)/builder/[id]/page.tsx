import { notFound } from "next/navigation";

import { apiGet } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import { PageHeader } from "@/components/page-header";
import type { PageDetail } from "@/lib/pages";
import { updatePageAction } from "../actions";
import { BuilderEditor } from "./builder-editor";

export const dynamic = "force-dynamic";

type DraftResponse = {
  id: string | null;
  version: number | null;
  layout: Record<string, unknown> | null;
};

export default async function BuilderEditorPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ error?: string }>;
}) {
  const { id } = await params;
  const query = await searchParams;
  const { token } = await requireSession();

  let page: PageDetail | null = null;
  try {
    page = await apiGet<PageDetail>(`/v1/admin/pages/${id}`, token);
  } catch {
    notFound();
  }
  if (!page) {
    notFound();
  }

  const draft = await apiGet<DraftResponse>(`/v1/admin/pages/${id}/draft`, token);
  const latestDraft =
    draft.id && draft.version && draft.layout
      ? { id: draft.id, version: draft.version, layout: draft.layout }
      : null;

  const storefrontUrl =
    process.env.NEXT_PUBLIC_STOREFRONT_URL ?? "http://localhost:3000";

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Builder"
        title={page.title}
        description="Edita el layout y publícalo. El storefront renderiza la versión publicada y purga su caché automáticamente."
      />

      {query.error ? (
        <p className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {query.error}
        </p>
      ) : null}

      <form
        action={updatePageAction.bind(null, id)}
        className="flex flex-col gap-3 border border-slate-200 bg-white p-5 sm:flex-row sm:items-end"
      >
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">Slug</span>
          <input
            name="slug"
            defaultValue={page.slug}
            pattern="[a-z0-9](?:[a-z0-9/-]{0,126}[a-z0-9])?"
            className="w-48 border border-slate-200 px-3 py-2 font-mono text-xs outline-none focus:border-slate-400"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">Título</span>
          <input
            name="title"
            defaultValue={page.title}
            className="w-64 border border-slate-200 px-3 py-2 outline-none focus:border-slate-400"
          />
        </label>
        <button
          type="submit"
          className="border border-slate-200 px-4 py-2 text-sm hover:border-slate-400"
        >
          Guardar datos
        </button>
      </form>

      <BuilderEditor
        pageId={id}
        initialSlug={page.slug}
        initialTitle={page.title}
        status={page.status}
        latestDraft={latestDraft}
        storefrontUrl={storefrontUrl}
      />
    </div>
  );
}
