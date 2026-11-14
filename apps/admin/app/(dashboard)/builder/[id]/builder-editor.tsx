"use client";

import { useCallback, useEffect, useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import {
  publishAction,
  previewTokenAction,
  saveDraftAction,
  unpublishAction,
} from "../actions";
import { BlockTree } from "@/components/blocks/block-tree";
import { BlockForm } from "@/components/blocks/block-forms";
import {
  blockLabel,
  createBlock,
  list,
  obj,
  str,
  type Block,
} from "@/lib/builder-blocks";

type Props = {
  pageId: string;
  initialSlug: string;
  initialTitle: string;
  status: string;
  latestDraft: { id: string; version: number; layout: Record<string, unknown> } | null;
  storefrontUrl: string;
};

type Baseline = { id: string; version: number };

/** Sanea el layout del servidor de forma defensiva (nunca lanza). */
function sanitizeBlocks(layout: Record<string, unknown> | undefined): Block[] {
  const raw = list(obj(layout).blocks);
  const blocks: Block[] = [];
  for (const item of raw) {
    const record = obj(item);
    const type = str(record.type);
    if (!type) continue;
    const id = str(record.id).trim() || `${type}-${blocks.length}`;
    blocks.push({ ...record, id, type } as Block);
  }
  return blocks;
}

export function BuilderEditor({
  pageId,
  initialSlug,
  initialTitle,
  status,
  latestDraft,
  storefrontUrl,
}: Props) {
  const router = useRouter();
  const [blocks, setBlocks] = useState<Block[]>(() =>
    sanitizeBlocks(latestDraft?.layout as Record<string, unknown> | undefined),
  );
  const [layoutVersion] = useState<number>(() => {
    const version = Number(obj(latestDraft?.layout as Record<string, unknown> | undefined).version);
    return Number.isInteger(version) && version >= 1 ? version : 1;
  });
  const [baseline, setBaseline] = useState<Baseline | null>(
    latestDraft ? { id: latestDraft.id, version: latestDraft.version } : null,
  );
  const [selected, setSelected] = useState(0);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [conflict, setConflict] = useState(false);
  const [message, setMessage] = useState<{ tone: "ok" | "error"; text: string } | null>(null);
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [publishOpen, setPublishOpen] = useState(false);
  const [previewToken, setPreviewToken] = useState<string | null>(null);
  const [frameKey, setFrameKey] = useState(0);
  const [, startTransition] = useTransition();

  const mutate = useCallback((updater: (blocks: Block[]) => Block[]) => {
    setBlocks((current) => {
      const next = updater(current);
      if (next !== current) {
        setDirty(true);
      }
      return next;
    });
  }, []);

  const onSave = useCallback(async () => {
    if (conflict) return undefined;
    setSaving(true);
    setMessage(null);
    const layoutJson = JSON.stringify({ version: layoutVersion, blocks });
    const result = await saveDraftAction(pageId, layoutJson, baseline?.version ?? 0);
    setSaving(false);
    if (result.ok) {
      const next = { id: result.id ?? "", version: result.version ?? 0 };
      setBaseline(next);
      setDirty(false);
      setConflict(false);
      setSavedAt(new Date().toLocaleTimeString("es-CO", { hour12: false }));
      setFrameKey((key) => key + 1); // recarga la vista previa con la versión guardada
      return { ok: true as const, version: next.version };
    }
    if ("conflict" in result && result.conflict) {
      setConflict(true);
      setMessage({
        tone: "error",
        text: "Alguien más editó esta página. Recarga para ver sus cambios; tus ediciones se descartarán.",
      });
      return { ok: false as const };
    }
    setMessage({ tone: "error", text: result.error ?? "No se pudo guardar el borrador" });
    return { ok: false as const };
  }, [baseline?.version, blocks, conflict, layoutVersion, pageId]);

  // Autosave con debounce de 2s (G-F3 §5).
  useEffect(() => {
    if (!dirty || conflict) return;
    const timer = setTimeout(() => {
      void onSave();
    }, 2000);
    return () => clearTimeout(timer);
  }, [blocks, dirty, conflict, onSave]);

  // Token de preview al montar (solo si hay borrador).
  useEffect(() => {
    if (!baseline) return;
    let cancelled = false;
    previewTokenAction(pageId, baseline.id).then((result) => {
      if (!cancelled && result.ok && result.token) {
        setPreviewToken(result.token);
      }
    });
    return () => {
      cancelled = true;
    };
    // Solo al montar: el token dura 15 min; "Actualizar vista" lo renueva.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onAddBlock = useCallback(
    (type: string) => {
      const index = blocks.length;
      mutate((current) =>
        current.length >= 256 ? current : [...current, createBlock(type)],
      );
      setSelected(index);
    },
    [mutate, blocks.length],
  );

  const onRemove = useCallback((index: number) => {
    mutate((current) => (current.length <= 1 ? current : current.filter((_, i) => i !== index)));
    setSelected((current) => {
      if (index < current) return current - 1;
      if (index === current) return Math.max(0, current - 1);
      return current;
    });
  }, [mutate]);

  const onDuplicate = useCallback((index: number) => {
    mutate((current) => {
      if (current.length >= 256) return current;
      const source = current[index];
      const copy: Block = {
        ...structuredClone(source),
        id: `${source.type}-${Math.random().toString(36).slice(2, 10)}`,
      };
      return [...current.slice(0, index + 1), copy, ...current.slice(index + 1)];
    });
    setSelected(index + 1);
  }, [mutate]);

  const onReorder = useCallback((from: number, to: number) => {
    mutate((current) => {
      const next = [...current];
      const [moved] = next.splice(from, 1);
      if (!moved) return current;
      const target = to > from ? to : to;
      next.splice(target, 0, moved);
      return next;
    });
    setSelected(to);
  }, [mutate]);

  const onMove = useCallback((index: number, direction: -1 | 1) => {
    mutate((current) => {
      const target = index + direction;
      if (target < 0 || target >= current.length) return current;
      const next = [...current];
      const [moved] = next.splice(index, 1);
      next.splice(target, 0, moved);
      return next;
    });
    setSelected((current) => Math.max(0, Math.min(blocks.length - 1, current + direction)));
  }, [mutate, blocks.length]);

  const updateSelected = useCallback((patch: Record<string, unknown>) => {
    mutate((current) =>
      current.map((block, i) => (i === selected ? { ...block, ...patch } : block)),
    );
  }, [mutate, selected]);

  const onRefreshPreview = useCallback(() => {
    if (!baseline) return;
    startTransition(async () => {
      const result = await previewTokenAction(pageId, baseline.id);
      if (result.ok && result.token) {
        setPreviewToken(result.token);
        setFrameKey((key) => key + 1);
      }
    });
  }, [baseline, pageId]);

  const openPublish = useCallback(() => {
    if (dirty) {
      void onSave().then((result) => {
        if (result?.ok) setPublishOpen(true);
      });
    } else {
      setPublishOpen(true);
    }
  }, [dirty, onSave]);

  const onPublishConfirm = useCallback(() => {
    if (!baseline) return;
    startTransition(async () => {
      const result = await publishAction(pageId, baseline.id, baseline.version);
      if (result.ok) {
        setPublishOpen(false);
        setMessage({ tone: "ok", text: `Página publicada · versión ${baseline.version}` });
        router.refresh();
      } else {
        setMessage({ tone: "error", text: result.error });
      }
    });
  }, [baseline, pageId, router]);

  const onUnpublish = useCallback(() => {
    startTransition(async () => {
      const result = await unpublishAction(pageId);
      setMessage(
        result.ok
          ? { tone: "ok", text: "Página despublicada." }
          : { tone: "error", text: result.error },
      );
      router.refresh();
    });
  }, [pageId, router]);

  const onDiscard = useCallback(() => {
    if (!dirty || window.confirm("¿Descartar los cambios sin guardar?")) {
      router.refresh();
    }
  }, [dirty, router]);

  const selectedBlock = blocks[selected] ?? null;
  const previewUrl =
    baseline && previewToken
      ? `${storefrontUrl.replace(/\/$/, "")}/preview?token=${encodeURIComponent(previewToken)}`
      : null;
  const stateLabel = conflict
    ? "conflicto"
    : saving
      ? "guardando…"
      : dirty
        ? "cambios sin guardar"
        : baseline
          ? "sincronizado"
          : "sin borrador";

  return (
    <div className="grid gap-4 xl:grid-cols-[280px_minmax(0,1fr)_minmax(320px,440px)]">
      {/* Columna 1 — árbol */}
      <div className="border border-slate-200 bg-white">
        <BlockTree
          blocks={blocks}
          selectedIndex={selected}
          onSelect={setSelected}
          onAdd={onAddBlock}
          onDuplicate={onDuplicate}
          onRemove={onRemove}
          onReorder={onReorder}
          onMove={onMove}
          canRemove={blocks.length > 1}
        />
      </div>

      {/* Columna 2 — propiedades del bloque seleccionado */}
      <div className="flex min-h-[420px] flex-col border border-slate-200 bg-white">
        <div className="flex items-center justify-between border-b border-slate-200 px-4 py-2">
          <p className="mono text-[10px] uppercase tracking-[0.18em] text-slate-500">
            {selectedBlock ? blockLabel(selectedBlock.type) : "Ningún bloque seleccionado"}
          </p>
          <span className="mono text-[10px] text-slate-400">
            {blocks.length} {blocks.length === 1 ? "bloque" : "bloques"}
          </span>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          {selectedBlock ? (
            <BlockForm value={selectedBlock} onChange={updateSelected} />
          ) : (
            <p className="text-sm text-slate-500">Selecciona o añade un bloque para editarlo.</p>
          )}
        </div>
      </div>

      {/* Columna 3 — vista previa en iframe + acciones */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between border border-slate-200 bg-white px-4 py-2">
          <div>
            <p className="mono text-[10px] uppercase tracking-[0.18em] text-slate-500">
              Vista previa
            </p>
            <p className="text-[11px] text-slate-500">
              /{initialSlug} · {initialTitle} · v{baseline?.version ?? "—"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`mono px-2 py-1 text-[9px] uppercase tracking-[0.14em] ${
                conflict
                  ? "bg-red-100 text-red-700"
                  : dirty
                    ? "bg-amber-100 text-amber-800"
                    : "bg-emerald-100 text-emerald-800"
              }`}
            >
              {stateLabel}
              {savedAt && !dirty && !conflict ? ` · ${savedAt}` : ""}
            </span>
            <button
              type="button"
              onClick={onRefreshPreview}
              disabled={!baseline}
              className="border border-slate-200 px-2 py-1 text-[11px] text-slate-600 hover:border-slate-400 disabled:opacity-40"
            >
              Actualizar
            </button>
          </div>
        </div>

        {conflict ? (
          <div className="border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800">
            <p className="font-medium">Conflicto de edición</p>
            <p className="mt-1">
              Otra sesión guardó la página primero. Tus cambios sin guardar se descartarán.
            </p>
            <div className="mt-3 flex gap-2">
              <button
                type="button"
                onClick={() => window.location.reload()}
                className="border border-red-400 bg-white px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-100"
              >
                Recargar con la versión del servidor
              </button>
            </div>
          </div>
        ) : null}

        <div className="min-h-[380px] flex-1 border border-slate-200 bg-slate-100">
          {previewUrl ? (
            <iframe
              key={frameKey}
              src={previewUrl}
              title="Vista previa de la página"
              sandbox="allow-scripts allow-same-origin"
              className="h-full min-h-[380px] w-full"
            />
          ) : (
            <div className="flex h-full min-h-[380px] flex-col items-center justify-center gap-2 p-6 text-center">
              <p className="text-sm text-slate-500">Aún no hay borrador guardado.</p>
              <p className="text-xs text-slate-400">
                Añade un bloque o espera el autoguardado para previsualizar.
              </p>
            </div>
          )}
        </div>

        {message ? (
          <p
            role={message.tone === "error" ? "alert" : "status"}
            className={`border px-4 py-2 text-sm ${
              message.tone === "ok"
                ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                : "border-red-200 bg-red-50 text-red-700"
            }`}
          >
            {message.text}
          </p>
        ) : null}

        <div className="space-y-2 border border-slate-200 bg-white p-3">
          <div className="flex items-center justify-between gap-2">
            <button
              type="button"
              onClick={onDiscard}
              className="text-xs text-slate-500 underline underline-offset-2 hover:text-slate-800"
            >
              Descartar cambios
            </button>
            <div className="flex items-center gap-2">
              {status === "published" ? (
                <button
                  type="button"
                  onClick={onUnpublish}
                  className="border border-red-200 px-3 py-2 text-xs text-red-700 hover:border-red-400"
                >
                  Despublicar
                </button>
              ) : null}
              <button
                type="button"
                onClick={openPublish}
                disabled={!baseline || saving || conflict}
                className="border border-emerald-700 bg-emerald-700 px-5 py-2 text-sm font-medium text-white hover:bg-emerald-600 disabled:opacity-40"
              >
                Publicar
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Modal publicar */}
      {publishOpen && baseline ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4"
          role="dialog"
          aria-modal="true"
          aria-label="Confirmar publicación"
          onClick={() => setPublishOpen(false)}
        >
          <div
            className="w-full max-w-md border border-slate-200 bg-white p-6 shadow-xl"
            onClick={(event) => event.stopPropagation()}
          >
            <h2 className="text-lg font-semibold text-slate-900">Publicar “/{initialSlug}”</h2>
            <p className="mt-2 text-sm text-slate-600">
              Se publicará la versión {baseline.version} ({blocks.length}{" "}
              {blocks.length === 1 ? "bloque" : "bloques"}) y se purgará la caché del storefront.
              La publicación anterior queda disponible para rollback.
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setPublishOpen(false)}
                className="border border-slate-200 px-4 py-2 text-sm text-slate-600 hover:border-slate-400"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={onPublishConfirm}
                className="border border-emerald-700 bg-emerald-700 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-600"
              >
                Publicar ahora
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
