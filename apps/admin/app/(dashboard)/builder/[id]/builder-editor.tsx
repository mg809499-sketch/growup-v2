"use client";

import { useState, useTransition } from "react";

import {
  publishAction,
  previewTokenAction,
  saveDraftAction,
  unpublishAction,
} from "../actions";

const TEMPLATE = `{
  "version": 1,
  "blocks": [
    {
      "id": "hero-1",
      "type": "hero",
      "title": "Temporada 01",
      "subtitle": "Series cortas, piezas seleccionadas.",
      "eyebrow": "Nuevo",
      "align": "left",
      "cta": { "label": "Ver colección", "href": "/collection" }
    },
    { "id": "grid-1", "type": "product_grid", "title": "Últimas piezas", "source": "latest", "limit": 8, "show_price": true }
  ]
}`;

type Props = {
  pageId: string;
  initialSlug: string;
  initialTitle: string;
  status: string;
  latestDraft: { id: string; version: number; layout: Record<string, unknown> } | null;
  storefrontUrl: string;
};

export function BuilderEditor({
  pageId,
  initialSlug,
  initialTitle,
  status,
  latestDraft,
  storefrontUrl,
}: Props) {
  const [layout, setLayout] = useState(() =>
    JSON.stringify(latestDraft?.layout ?? JSON.parse(TEMPLATE), null, 2),
  );
  const [draftId, setDraftId] = useState(latestDraft?.id ?? null);
  const [draftVersion, setDraftVersion] = useState(latestDraft?.version ?? null);
  const [message, setMessage] = useState<{ tone: "ok" | "error"; text: string } | null>(null);
  const [pending, startTransition] = useTransition();

  const onSave = () =>
    startTransition(async () => {
      const result = await saveDraftAction(pageId, layout);
      if (!result.ok) {
        setMessage({ tone: "error", text: result.error });
        return;
      }
      setDraftId(result.id ?? null);
      setDraftVersion(result.version ?? null);
      setMessage({
        tone: "ok",
        text: `Borrador guardado · versión ${result.version}`,
      });
    });

  const onPublish = () =>
    startTransition(async () => {
      if (!draftId || draftVersion === null) {
        setMessage({ tone: "error", text: "Guarda un borrador primero." });
        return;
      }
      const result = await publishAction(pageId, draftId, draftVersion);
      setMessage(
        result.ok
          ? { tone: "ok", text: "Página publicada. El storefront purga su caché." }
          : { tone: "error", text: result.error },
      );
    });

  const onUnpublish = () =>
    startTransition(async () => {
      const result = await unpublishAction(pageId);
      setMessage(
        result.ok
          ? { tone: "ok", text: "Página despublicada." }
          : { tone: "error", text: result.error },
      );
    });

  const onPreview = () =>
    startTransition(async () => {
      if (!draftId) {
        setMessage({ tone: "error", text: "Guarda un borrador primero." });
        return;
      }
      const result = await previewTokenAction(pageId, draftId);
      if (!result.ok || !result.token) {
        setMessage({ tone: "error", text: result.ok ? "Sin token" : result.error });
        return;
      }
      const base = storefrontUrl.replace(/\/$/, "");
      window.open(`${base}/preview?token=${encodeURIComponent(result.token)}`, "_blank", "noopener");
    });

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
      <div className="border border-slate-200 bg-white">
        <div className="flex items-center justify-between border-b border-slate-200 px-4 py-2">
          <p className="mono text-[10px] uppercase tracking-[0.18em] text-slate-500">
            layout.json · block registry
          </p>
          <button
            type="button"
            onClick={() => setLayout(JSON.stringify(JSON.parse(TEMPLATE), null, 2))}
            className="text-xs underline underline-offset-2 hover:text-slate-900"
          >
            Insertar plantilla
          </button>
        </div>
        <textarea
          value={layout}
          onChange={(event) => setLayout(event.target.value)}
          spellCheck={false}
          className="h-[560px] w-full resize-y p-4 font-mono text-xs leading-relaxed outline-none"
        />
      </div>

      <aside className="space-y-4">
        <div className="border border-slate-200 bg-white p-4 text-sm">
          <p className="mono text-[10px] uppercase tracking-[0.18em] text-slate-500">Estado</p>
          <p className="mt-1 font-medium text-slate-900">{status}</p>
          <p className="mono mt-2 text-[11px] text-slate-500">
            /{initialSlug} · {initialTitle}
          </p>
          {draftVersion !== null ? (
            <p className="mono mt-1 text-[11px] text-slate-500">borrador v{draftVersion}</p>
          ) : null}
        </div>

        {message ? (
          <p
            className={`border px-4 py-3 text-sm ${
              message.tone === "ok"
                ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                : "border-red-200 bg-red-50 text-red-700"
            }`}
          >
            {message.text}
          </p>
        ) : null}

        <div className="space-y-2 border border-slate-200 bg-white p-4">
          <button
            type="button"
            onClick={onSave}
            disabled={pending}
            className="w-full border border-slate-900 bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            Guardar borrador
          </button>
          <button
            type="button"
            onClick={onPreview}
            disabled={pending}
            className="w-full border border-slate-200 px-4 py-2 text-sm hover:border-slate-400 disabled:opacity-50"
          >
            Vista previa
          </button>
          <button
            type="button"
            onClick={onPublish}
            disabled={pending}
            className="w-full border border-emerald-700 bg-emerald-700 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-600 disabled:opacity-50"
          >
            Publicar
          </button>
          <button
            type="button"
            onClick={onUnpublish}
            disabled={pending}
            className="w-full border border-red-200 px-4 py-2 text-sm text-red-700 hover:border-red-400 disabled:opacity-50"
          >
            Despublicar
          </button>
        </div>

        <p className="text-xs leading-relaxed text-slate-500">
          Bloques válidos: header, footer, hero, editorial_split, product_grid,
          product_carousel, collection_grid, image_banner, rich_text, quote,
          gallery, video_embed, faq, newsletter, spacer, columns. Los esquemas
          se validan en el servidor al guardar y al publicar.
        </p>
      </aside>
    </div>
  );
}
