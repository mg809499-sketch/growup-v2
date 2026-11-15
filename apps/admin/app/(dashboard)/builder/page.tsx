import Link from "next/link";
import { redirect } from "next/navigation";

import { apiGetSafe } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import { PageHeader } from "@/components/page-header";
import type { PageListResponse } from "@/lib/pages";

type DraftResponse = {
  id: string | null;
  version: number | null;
  layout: Record<string, unknown> | null;
};
import { createPageAction } from "./actions";
import { BuilderEditor } from "./[id]/builder-editor";

export const dynamic = "force-dynamic";

const STATUS_LABEL: Record<string, string> = {
  draft: "Borrador",
  published: "Publicada en Edge",
  archived: "Archivada",
};

export default async function BuilderPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { token } = await requireSession();
  const params = await searchParams;
  const result = await apiGetSafe<PageListResponse>(
    "/v1/admin/pages?limit=100",
    token,
  );
  if (result.redirectToLogin) {
    redirect("/login");
  }
  const pages = result.data?.items ?? [];
  const primaryPage = pages[0] ?? {
    id: "00000000-0000-4000-8000-000000000201",
    slug: "home",
    title: "Home · Colección Deportiva Alto Rendimiento",
    status: "published",
  };

  // Carga el borrador real de la página primaria (sin mocks).
  let primaryDraft: { id: string; version: number; layout: Record<string, unknown> } | null = null;
  if (pages.length > 0) {
    const draftResult = await apiGetSafe<DraftResponse>(
      `/v1/admin/pages/${primaryPage.id}/draft`,
      token,
    );
    const draft = draftResult.data;
    if (draft && draft.id && draft.version && draft.layout) {
      primaryDraft = { id: draft.id, version: draft.version, layout: draft.layout };
    }
  }

  const storefrontUrl =
    process.env.NEXT_PUBLIC_STOREFRONT_URL ?? "http://localhost:3000";

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <PageHeader
          eyebrow="1. Módulo: Portal Principal · Store Builder v3.0"
          title="Store & Web Builder v3.0 (Visual HTML & WordPress)"
          description="Acceso directo a la creación y despliegue del canal de venta en mitiendadeportiva.growupstore.app con sincronización WooCommerce v8.2.1 y Checkout Express Wompi."
        />

        <form
          action={createPageAction}
          className="vn-card flex flex-wrap items-end gap-2.5 p-3.5"
        >
          <label className="block text-xs font-medium text-[#525866]">
            <span className="mono block text-[10px]">Nuevo Slug</span>
            <input
              name="slug"
              required
              placeholder="ej. promo-wompi"
              pattern="[a-z0-9](?:[a-z0-9/-]{0,126}[a-z0-9])?"
              className="mt-1 w-36 rounded-xl border border-black/15 bg-white px-2.5 py-1.5 text-xs text-[#0d0d0d]"
            />
          </label>
          <label className="block text-xs font-medium text-[#525866]">
            <span className="mono block text-[10px]">Título de Página</span>
            <input
              name="title"
              required
              placeholder="Landing Promo"
              className="mt-1 w-44 rounded-xl border border-black/15 bg-white px-2.5 py-1.5 text-xs text-[#0d0d0d]"
            />
          </label>
          <button
            type="submit"
            className="rounded-xl bg-[#0d0d0d] px-3.5 py-1.5 text-xs font-bold text-white hover:bg-zinc-800"
          >
            + Nueva Página
          </button>
        </form>
      </div>

      {params.error ? (
        <p className="vn-card border-rose-300 px-4 py-3 text-sm text-rose-900">
          {params.error}
        </p>
      ) : null}

      {pages.length > 0 ? (
        <div className="vn-card flex flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="mono text-[10px] font-bold text-[#525866]">PÁGINAS DEL CANAL:</span>
            {pages.map((p) => (
              <Link
                key={p.id}
                href={`/builder/${p.id}`}
                className="inline-flex items-center gap-2 rounded-xl border border-black/15 bg-white/90 px-3 py-1.5 text-xs font-semibold text-[#0d0d0d] hover:border-black/40"
              >
                <span className="mono text-[11px] font-bold text-[#0d0d0d]">/{p.slug}</span>
                <span>{p.title}</span>
                <span className="mono rounded-full border border-emerald-300 bg-emerald-50 px-2 py-0.5 text-[9px] font-bold text-emerald-900">
                  {STATUS_LABEL[p.status] ?? p.status}
                </span>
              </Link>
            ))}
          </div>
          <span className="mono text-[10px] font-semibold text-[#525866]">
            Tipografía: Unbounded + Geist + Geist Mono
          </span>
        </div>
      ) : null}

      <BuilderEditor
        pageId={primaryPage.id}
        initialSlug={primaryPage.slug}
        initialTitle={primaryPage.title}
        status={primaryPage.status}
        latestDraft={primaryDraft}
        storefrontUrl={storefrontUrl}
      />
    </div>
  );
}
