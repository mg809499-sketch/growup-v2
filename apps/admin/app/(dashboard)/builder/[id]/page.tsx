import { notFound, redirect } from "next/navigation";

import { ApiError, apiGet, apiGetSafe } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import { PageHeader } from "@/components/page-header";
import { SectionError } from "@/components/section-error";
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
  } catch (apiError) {
    if (apiError instanceof ApiError && apiError.status === 401) {
      redirect("/login");
    }
    notFound();
  }
  if (!page) {
    notFound();
  }

  const draftResult = await apiGetSafe<DraftResponse>(
    `/v1/admin/pages/${id}/draft`,
    token,
  );
  if (draftResult.redirectToLogin) {
    redirect("/login");
  }
  const draft = draftResult.data;
  const latestDraft =
    draft && draft.id && draft.version && draft.layout
      ? { id: draft.id, version: draft.version, layout: draft.layout }
      : null;

  const storefrontUrl =
    process.env.NEXT_PUBLIC_STOREFRONT_URL ?? "http://localhost:3000";

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <PageHeader
          eyebrow="Store & Web Builder v3.0"
          title={page.title}
          description="Edición visual Drag & Drop, mapeo dinámico WooCommerce/ACF y publicación directa en Cloudflare Edge."
        />

        <form
          action={updatePageAction.bind(null, id)}
          className="vn-card flex flex-wrap items-end gap-3 p-3.5"
        >
          <label className="block text-xs font-medium text-[#525866]">
            <span className="mono block text-[10px]">Slug</span>
            <input
              name="slug"
              defaultValue={page.slug}
              pattern="[a-z0-9](?:[a-z0-9/-]{0,126}[a-z0-9])?"
              className="mt-1 w-36 rounded-xl border border-black/15 bg-white px-2.5 py-1.5 font-mono text-xs text-[#0d0d0d]"
            />
          </label>
          <label className="block text-xs font-medium text-[#525866]">
            <span className="mono block text-[10px]">Título</span>
            <input
              name="title"
              defaultValue={page.title}
              className="mt-1 w-52 rounded-xl border border-black/15 bg-white px-2.5 py-1.5 text-xs text-[#0d0d0d]"
            />
          </label>
          <button
            type="submit"
            className="rounded-xl bg-[#0d0d0d] px-3.5 py-1.5 text-xs font-bold text-white hover:bg-zinc-800"
          >
            Guardar Metadatos
          </button>
        </form>
      </div>

      {query.error ? (
        <p className="vn-card border-rose-300 px-4 py-3 text-sm text-rose-900">
          {query.error}
        </p>
      ) : null}

      {draftResult.error || !draft ? (
        <SectionError
          title="No se pudo cargar el borrador de la página"
          error={draftResult.error ?? { status: 0, code: null, message: "Respuesta inválida" }}
        />
      ) : (
        <BuilderEditor
          pageId={id}
          initialSlug={page.slug}
          initialTitle={page.title}
          status={page.status}
          latestDraft={latestDraft}
          storefrontUrl={storefrontUrl}
        />
      )}
    </div>
  );
}
