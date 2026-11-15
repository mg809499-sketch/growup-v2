"use client";

import { useCallback, useEffect, useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import type { ThemePreset } from "@growup/config";

import {
  applyTemplateAction,
  getThemePresetAction,
  listTemplatesAction,
  publishAction,
  previewTokenAction,
  saveDraftAction,
  saveThemePresetAction,
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
type ViewportMode = "desktop" | "tablet" | "mobile";
type WorkMode = "visual" | "code";
type LibraryTab = "ecommerce" | "html" | "wordpress";
type InspectorTab = "estilos" | "wordpress" | "html";

const MAX_HISTORY = 30;

const V3_LIBRARY_ITEMS: ReadonlyArray<{
  id: string;
  tab: LibraryTab;
  blockType: string;
  title: string;
  badge: string;
  description: string;
}> = [
  {
    id: "hero-mascota-3d",
    tab: "ecommerce",
    blockType: "hero",
    title: "Hero Mascota 3D",
    badge: "BURBANK + 3D",
    description: "Banner dinámico con tipografía Burbank, CTA Wompi y avatar 3D flotante.",
  },
  {
    id: "catalogo-woocommerce",
    tab: "ecommerce",
    blockType: "product_grid",
    title: "Catálogo Dinámico WooCommerce",
    badge: "48 SKUs OK",
    description: "Sincronización automática con categorías oficiales de WooCommerce.",
  },
  {
    id: "checkout-express-wompi",
    tab: "ecommerce",
    blockType: "image_banner",
    title: "Checkout Express Wompi",
    badge: "1-CLICK PAY",
    description: "Botón de pago instantáneo para PSE, Nequi, Bancolombia y Tarjetas.",
  },
  {
    id: "selector-variantes",
    tab: "ecommerce",
    blockType: "columns",
    title: "Selector de Variantes",
    badge: "STOCK REAL",
    description: "Componente dinámico para gestión en vivo de Tallas, Colores y Stock.",
  },
  {
    id: "barra-urgencia",
    tab: "html",
    blockType: "header",
    title: "Barra de Urgencia",
    badge: "CONVERSIÓN",
    description: "Banner superior con envío gratis y cuenta regresiva psicológica.",
  },
  {
    id: "editorial-split-ui",
    tab: "html",
    blockType: "editorial_split",
    title: "Editorial Split Tailwind",
    badge: "HTML UI",
    description: "Sección de dos columnas con imagen de alto impacto y manifiesto.",
  },
  {
    id: "wp-shortcode-cart",
    tab: "wordpress",
    blockType: "rich_text",
    title: "Shortcode [wp_woocommerce_cart]",
    badge: "GUTENBERG",
    description: "Soporte directo para shortcodes clásicos y bloques ACF de WordPress.",
  },
  {
    id: "wp-acf-faq",
    tab: "wordpress",
    blockType: "faq",
    title: "Acordeón ACF / Post Meta",
    badge: "WP REST v2",
    description: "Preguntas frecuentes sincronizadas con custom fields del producto.",
  },
];

const WOO_LIVE_PRODUCTS = [
  {
    sku: "SKU In Stock 809",
    name: "Chaqueta Deportiva Valkyrie Pro",
    price: "$ 189.900 COP",
    compare: "$ 249.900",
    stock: "14 uds",
  },
  {
    sku: "SKU In Stock 102",
    name: "Jersey Compresión Térmico Aero",
    price: "$ 129.000 COP",
    compare: "$ 159.000",
    stock: "22 uds",
  },
  {
    sku: "SKU In Stock 304",
    name: "Pantalón Técnico Running Pro",
    price: "$ 149.900 COP",
    compare: "$ 189.000",
    stock: "9 uds",
  },
  {
    sku: "SKU In Stock 512",
    name: "Cortavientos Ultraligero Reflex",
    price: "$ 210.000 COP",
    compare: "$ 260.000",
    stock: "7 uds",
  },
] as const;

const DEFAULT_HTML_SNIPPET = `<section id="hero-mascota-promo" class="rounded-2xl border border-violet-500/60 bg-white/80 backdrop-blur-xl p-6 text-slate-950">
  <span class="font-mono text-xs uppercase tracking-widest text-violet-700">COLECCIÓN OFICIAL 2025</span>
  <h2 class="font-headline-lg mt-2 text-[28px] font-bold tracking-tight uppercase">
    COLECCIÓN DEPORTIVA DE ALTO RENDIMIENTO
  </h2>
  <p class="mt-2 text-2xl font-extrabold text-slate-950">
    $189.900 COP <del class="text-sm text-slate-500">$249.900 COP</del>
  </p>
  <button class="mt-4 rounded-2xl bg-violet-600 px-6 py-3 font-bold text-white">
    Comprar Ahora con Wompi (PSE · Nequi · Bancolombia)
  </button>
</section>`;

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
  const [past, setPast] = useState<Block[][]>([]);
  const [future, setFuture] = useState<Block[][]>([]);
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
  const [savedAt, setSavedAt] = useState<string | null>("sincronizado");
  const [publishOpen, setPublishOpen] = useState(false);
  const [previewToken, setPreviewToken] = useState<string | null>(null);
  const [frameKey, setFrameKey] = useState(0);

  const [viewport, setViewport] = useState<ViewportMode>("desktop");
  const [workMode, setWorkMode] = useState<WorkMode>("visual");
  const [libraryTab, setLibraryTab] = useState<LibraryTab>("ecommerce");
  const [inspectorTab, setInspectorTab] = useState<InspectorTab>("estilos");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeCanvasBox, setActiveCanvasBox] = useState<string>("hero-mascota-promo");
  const [selectedSize, setSelectedSize] = useState<"S" | "M" | "L" | "XL">("M");
  const [headlineTag, setHeadlineTag] = useState("h2.font-headline-lg");
  const [fontSizePx, setFontSizePx] = useState("28px");
  const [fontWeight, setFontWeight] = useState("700 Bold");
  const [brandAccent, setBrandAccent] = useState<"naranja" | "violeta" | "negro" | "esmeralda">("violeta");
  const [paddingToken, setPaddingToken] = useState("24px / space-lg");
  const [radiusToken, setRadiusToken] = useState("16px / rounded-2xl");
  const [htmlSnippet, setHtmlSnippet] = useState(DEFAULT_HTML_SNIPPET);
  const [copiedSnippet, setCopiedSnippet] = useState(false);
  const [showLiveIframe, setShowLiveIframe] = useState(false);
  const [templates, setTemplates] = useState<Array<{ template_id: string; name: string; description: string }>>([]);
  const [templateBusy, setTemplateBusy] = useState(false);
  const [templatesOpen, setTemplatesOpen] = useState(false);
  const [themePreset, setThemePreset] = useState<ThemePreset>("nova");
  const [themeBusy, setThemeBusy] = useState(false);
  const [, startTransition] = useTransition();

  const mutate = useCallback((updater: (blocks: Block[]) => Block[]) => {
    setBlocks((current) => {
      const next = updater(current);
      if (next !== current) {
        setPast((prev) => [...prev.slice(-(MAX_HISTORY - 1)), current]);
        setFuture([]);
        setDirty(true);
      }
      return next;
    });
  }, []);

  const onUndo = useCallback(() => {
    setPast((prevPast) => {
      if (prevPast.length === 0) return prevPast;
      const previous = prevPast[prevPast.length - 1];
      setBlocks((current) => {
        setFuture((prevFuture) => [current, ...prevFuture.slice(0, MAX_HISTORY - 1)]);
        return previous;
      });
      setDirty(true);
      return prevPast.slice(0, -1);
    });
  }, []);

  const onRedo = useCallback(() => {
    setFuture((prevFuture) => {
      if (prevFuture.length === 0) return prevFuture;
      const [next, ...rest] = prevFuture;
      setBlocks((current) => {
        setPast((prevPast) => [...prevPast.slice(-(MAX_HISTORY - 1)), current]);
        return next;
      });
      setDirty(true);
      return rest;
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
      setFrameKey((key) => key + 1);
      return { ok: true as const, version: next.version };
    }
    if ("conflict" in result && result.conflict) {
      setConflict(true);
      setMessage({
        tone: "error",
        text: "Alguien más editó esta página. Recarga para ver sus cambios.",
      });
      return { ok: false as const };
    }
    setMessage({ tone: "error", text: result.error ?? "No se pudo guardar el borrador" });
    return { ok: false as const };
  }, [baseline?.version, blocks, conflict, layoutVersion, pageId]);

  useEffect(() => {
    if (!dirty || conflict) return;
    const timer = setTimeout(() => {
      void onSave();
    }, 2000);
    return () => clearTimeout(timer);
  }, [blocks, dirty, conflict, onSave]);

  useEffect(() => {
    let cancelled = false;
    if (baseline) {
      previewTokenAction(pageId, baseline.id).then((result) => {
        if (!cancelled && result.ok && result.token) {
          setPreviewToken(result.token);
        }
      });
    }
    getThemePresetAction().then((result) => {
      if (!cancelled && result.ok) {
        setThemePreset(result.preset);
      }
    });
    return () => {
      cancelled = true;
    };
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
      next.splice(to, 0, moved);
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
        setMessage({
          tone: "ok",
          text: `Tienda publicada en Cloudflare Edge y sincronizada con WordPress · v${baseline.version}`,
        });
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

  const selectedBlock = blocks[selected] ?? null;
  const previewUrl =
    baseline && previewToken
      ? `${storefrontUrl.replace(/\/$/, "")}/preview?token=${encodeURIComponent(previewToken)}`
      : null;

  const filteredCatalog = V3_LIBRARY_ITEMS.filter(
    (item) =>
      item.tab === libraryTab &&
      (searchQuery.trim() === "" ||
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.description.toLowerCase().includes(searchQuery.toLowerCase())),
  );

  const canvasViewportWidth =
    viewport === "mobile"
      ? "mx-auto max-w-[375px]"
      : viewport === "tablet"
        ? "mx-auto max-w-[768px]"
        : "w-full";

  const accentButtonClass =
    brandAccent === "naranja"
      ? "bg-orange-600 hover:bg-orange-500 text-white"
      : brandAccent === "esmeralda"
        ? "bg-emerald-600 hover:bg-emerald-500 text-white"
        : brandAccent === "negro"
          ? "bg-[#0d0d0d] hover:bg-zinc-800 text-white"
          : "bg-violet-600 hover:bg-violet-500 text-white";

  return (
    <div
      data-builder="nova"
      className="vn-card overflow-hidden text-[#0d0d0d]"
    >
      {/* =====================================================================
          1. BARRA SUPERIOR DE CONTROL & PUBLICACIÓN (TOP TOOLSTRIP)
         ===================================================================== */}
      <div className="border-b border-black/10 bg-white/85 px-4 py-3.5 backdrop-blur-xl">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="display text-sm font-extrabold tracking-tight text-[#0d0d0d]">
              Store &amp; Web Builder v3.0
            </span>
            <span className="mono rounded-full border border-black/15 bg-slate-100 px-2.5 py-0.5 text-[10px] font-bold text-[#0d0d0d]">
              VISUAL HTML + WORDPRESS ENGINE
            </span>
            <span className="mono inline-flex items-center gap-1.5 rounded-full border border-emerald-300 bg-emerald-50 px-2.5 py-0.5 text-[10px] font-bold text-emerald-900">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-600" />
              WooCommerce v8.2 Sync · 12ms Edge
            </span>
          </div>

          {/* Selectores de Modo de Trabajo & Viewport */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex rounded-xl border border-black/10 bg-slate-100/90 p-0.5" role="group" aria-label="Modo de trabajo">
              <button
                type="button"
                onClick={() => setWorkMode("visual")}
                className={`mono rounded-lg px-2.5 py-1 text-[10px] font-bold ${
                  workMode === "visual"
                    ? "bg-[#0d0d0d] text-white shadow-xs"
                    : "text-[#525866] hover:text-[#0d0d0d]"
                }`}
              >
                Modo Visual (Drag &amp; Drop)
              </button>
              <button
                type="button"
                onClick={() => setWorkMode("code")}
                className={`mono rounded-lg px-2.5 py-1 text-[10px] font-bold ${
                  workMode === "code"
                    ? "bg-[#0d0d0d] text-white shadow-xs"
                    : "text-[#525866] hover:text-[#0d0d0d]"
                }`}
              >
                Modo Código HTML/Tailwind
              </button>
            </div>

            <div className="flex rounded-xl border border-black/10 bg-slate-100/90 p-0.5" role="group" aria-label="Selector de viewport">
              {(
                [
                  { id: "desktop", label: "Desktop 1440px" },
                  { id: "tablet", label: "Tablet 768px" },
                  { id: "mobile", label: "Mobile 375px" },
                ] as const
              ).map((vp) => (
                <button
                  key={vp.id}
                  type="button"
                  onClick={() => setViewport(vp.id)}
                  className={`mono rounded-lg px-2.5 py-1 text-[10px] font-bold ${
                    viewport === vp.id
                      ? "bg-[#0d0d0d] text-white shadow-xs"
                      : "text-[#525866] hover:text-[#0d0d0d]"
                  }`}
                >
                  {vp.label}
                </button>
              ))}
            </div>
          </div>

          {/* Controles de Historial & Despliegue */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={onUndo}
              disabled={past.length === 0}
              title="Deshacer"
              className="mono rounded-xl border border-black/15 bg-white px-2.5 py-1.5 text-[10px] font-bold text-[#0d0d0d] hover:bg-slate-100 disabled:opacity-35"
            >
              ↶ Undo ({past.length})
            </button>
            <button
              type="button"
              onClick={onRedo}
              disabled={future.length === 0}
              title="Rehacer"
              className="mono rounded-xl border border-black/15 bg-white px-2.5 py-1.5 text-[10px] font-bold text-[#0d0d0d] hover:bg-slate-100 disabled:opacity-35"
            >
              ↷ Redo ({future.length})
            </button>
            <button
              type="button"
              onClick={() => setShowLiveIframe((prev) => !prev)}
              className="mono rounded-xl border border-black/15 bg-white px-3 py-1.5 text-[10px] font-bold text-[#0d0d0d] hover:bg-slate-100"
            >
              {showLiveIframe ? "Ver Canvas v3.0" : "Vista Previa"}
            </button>
            <button
              type="button"
              onClick={openPublish}
              disabled={saving || conflict}
              className="mono rounded-xl bg-[#0d0d0d] px-4 py-1.5 text-[11px] font-extrabold text-white shadow-sm hover:bg-zinc-800 disabled:opacity-40"
            >
              Publicar Tienda
            </button>
          </div>
        </div>

        {/* Sub-barra de estado de persistencia Edge y staging URL */}
        <div className="mt-2.5 flex flex-wrap items-center justify-between gap-2 border-t border-black/10 pt-2 text-[11px] text-[#525866]">
          <div className="flex flex-wrap items-center gap-3">
            <span className="mono text-[10px] font-bold text-emerald-700">
              ● Auto-guardado en Cloudflare Edge: {saving ? "Guardando…" : dirty ? "Pendiente" : `Activo (${savedAt ?? "OK"})`}
            </span>
            <span className="mono text-[10px] text-[#525866]">
              Staging: <strong className="text-[#0d0d0d]">mitiendadeportiva.growupstore.app/{initialSlug}</strong>
            </span>
            <span className="mono text-[10px] text-[#525866]">
              Página: <strong className="text-[#0d0d0d]">{initialTitle}</strong> (v{baseline?.version ?? 1})
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="mono text-[10px] text-[#525866]">Preset visual:</span>
            {(["nova", "ropa", "joyeria"] as const).map((preset) => (
              <button
                key={preset}
                type="button"
                disabled={themeBusy || themePreset === preset}
                onClick={async () => {
                  setThemeBusy(true);
                  try {
                    const res = await saveThemePresetAction(preset);
                    if (res.ok && res.preset) {
                      setThemePreset(res.preset);
                      setFrameKey((k) => k + 1);
                    }
                  } finally {
                    setThemeBusy(false);
                  }
                }}
                className={`mono rounded-lg px-2.5 py-0.5 text-[10px] uppercase ${
                  themePreset === preset
                    ? "bg-[#0d0d0d] font-bold text-white"
                    : "border border-black/15 bg-white text-[#525866] hover:text-[#0d0d0d]"
                }`}
              >
                {preset}
              </button>
            ))}
          </div>
        </div>
      </div>

      {message ? (
        <div
          role={message.tone === "error" ? "alert" : "status"}
          className={`border-b px-4 py-2.5 text-xs font-semibold ${
            message.tone === "ok"
              ? "border-emerald-300 bg-emerald-50 text-emerald-950"
              : "border-rose-300 bg-rose-50 text-rose-950"
          }`}
        >
          {message.text}
        </div>
      ) : null}

      {/* =====================================================================
          CUERPO DE 3 PANELES (IZQUIERDA: BIBLIOTECA · CENTRO: CANVAS · DERECHA: INSPECTOR)
         ===================================================================== */}
      <div className="grid min-h-[760px] grid-cols-1 xl:grid-cols-[310px_minmax(0,1fr)_350px]">
        {/* ===================================================================
            2. PANEL IZQUIERDO: BIBLIOTECA DE BLOQUES & SINCRONIZACIÓN WORDPRESS
           =================================================================== */}
        <div className="flex flex-col justify-between border-b border-black/10 bg-white/60 p-3.5 backdrop-blur-xl xl:border-b-0 xl:border-r">
          <div className="space-y-3.5">
            {/* Pestañas E-commerce | HTML UI | WordPress */}
            <div className="grid grid-cols-3 gap-1 rounded-xl border border-black/10 bg-slate-100/90 p-1">
              {(
                [
                  { id: "ecommerce", label: "E-commerce" },
                  { id: "html", label: "HTML UI" },
                  { id: "wordpress", label: "WordPress" },
                ] as const
              ).map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setLibraryTab(t.id)}
                  className={`rounded-lg py-1.5 text-[11px] font-bold transition-all ${
                    libraryTab === t.id
                      ? "bg-[#0d0d0d] text-white shadow-xs"
                      : "text-[#525866] hover:text-[#0d0d0d]"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {/* Monitor de API WooCommerce */}
            <div className="flex items-center justify-between rounded-xl border border-emerald-300 bg-emerald-50/80 px-3 py-2">
              <span className="mono text-[10px] font-bold text-emerald-900">REST API WOO</span>
              <span className="mono text-[10px] font-bold text-emerald-900">
                48 SKUs OK · En Vivo
              </span>
            </div>

            {/* Buscador rápido */}
            <div>
              <input
                type="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Buscar bloques visuales..."
                className="w-full rounded-xl border border-black/15 bg-white px-3 py-2 text-xs text-[#0d0d0d] placeholder:text-slate-400 focus:border-[#0d0d0d] focus:outline-none"
              />
            </div>

            {/* Catálogo de Bloques Arrastrables v3.0 */}
            <div className="space-y-2">
              <p className="mono text-[10px] font-bold text-[#525866]">
                CATÁLOGO DE BLOQUES ARRASTRABLES
              </p>
              <div className="max-h-[260px] space-y-2 overflow-y-auto pr-1 admin-scroll">
                {filteredCatalog.map((item) => (
                  <div
                    key={item.id}
                    draggable
                    onClick={() => onAddBlock(item.blockType)}
                    className="group cursor-pointer rounded-2xl border border-black/10 bg-white/85 p-3 shadow-xs backdrop-blur-md transition-all hover:border-violet-500 hover:bg-white"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-bold text-[#0d0d0d]">
                        + {item.title}
                      </span>
                      <span className="mono rounded-full border border-violet-300 bg-violet-50 px-2 py-0.5 text-[9px] font-bold text-violet-900">
                        {item.badge}
                      </span>
                    </div>
                    <p className="mt-1 text-[11px] leading-snug text-[#525866]">
                      {item.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Árbol de bloques activos */}
            <div className="overflow-hidden rounded-2xl border border-black/10 bg-white/90 text-[#0d0d0d]">
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
          </div>

          {/* Tarjeta de Telemetría Inferior */}
          <div className="mt-4 rounded-2xl border border-black/10 bg-white/85 p-3 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="mono text-[10px] font-bold text-[#0d0d0d]">
                200 ENDPOINTS WP OK
              </span>
              <span className="mono text-[10px] font-bold text-emerald-700">Caché Edge 94%</span>
            </div>
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
              <div className="h-full w-[94%] bg-[#0d0d0d]" />
            </div>
          </div>
        </div>

        {/* ===================================================================
            3. CANVAS CENTRAL: PREVISUALIZADOR WYSIWYG EN VIVO
           =================================================================== */}
        <div className="flex flex-col bg-slate-100/60 p-4">
          {/* Barra de Inspección de URL & Navegador Embebido */}
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-black/10 bg-white/85 px-3.5 py-2 backdrop-blur-xl">
            <div className="flex items-center gap-2">
              <span className="text-xs tracking-widest text-rose-500">●</span>
              <span className="text-xs tracking-widest text-amber-500">●</span>
              <span className="text-xs tracking-widest text-emerald-500">●</span>
              <span className="mono ml-2 rounded-lg border border-black/10 bg-slate-50 px-2.5 py-1 text-[11px] font-semibold text-[#0d0d0d]">
                🔒 SSL · https://mitiendadeportiva.growupstore.app/{initialSlug}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="mono rounded-full border border-violet-300 bg-violet-50 px-2.5 py-0.5 text-[10px] font-bold text-violet-900">
                CANVAS ACTIVO
              </span>
              <button
                type="button"
                onClick={async () => {
                  const next = !templatesOpen;
                  setTemplatesOpen(next);
                  if (next && templates.length === 0) {
                    setTemplateBusy(true);
                    try {
                      setTemplates(await listTemplatesAction());
                    } finally {
                      setTemplateBusy(false);
                    }
                  }
                }}
                className="mono rounded-xl border border-black/15 bg-white px-2.5 py-1 text-[10px] font-bold text-[#0d0d0d] hover:bg-slate-100"
              >
                Plantillas 1-Click
              </button>
            </div>
          </div>

          {templatesOpen ? (
            <div className="mb-3 rounded-2xl border border-black/15 bg-white/90 p-3 backdrop-blur-xl">
              <p className="mono text-[10px] font-bold text-[#0d0d0d]">
                PLANTILLAS OFICIALES DEL REGISTRY
              </p>
              <div className="mt-2 grid gap-2 md:grid-cols-3">
                {templates.map((tpl) => (
                  <div
                    key={tpl.template_id}
                    className="flex flex-col justify-between rounded-xl border border-black/10 bg-white p-2.5"
                  >
                    <div>
                      <p className="text-xs font-bold text-[#0d0d0d]">{tpl.name}</p>
                      <p className="mt-0.5 text-[11px] text-[#525866]">{tpl.description}</p>
                    </div>
                    <button
                      type="button"
                      disabled={templateBusy}
                      onClick={async () => {
                        setTemplateBusy(true);
                        try {
                          const res = await applyTemplateAction(pageId, tpl.template_id);
                          if (res.ok) {
                            setMessage({
                              tone: "ok",
                              text: `Plantilla "${tpl.name}" aplicada al canvas.`,
                            });
                          }
                        } finally {
                          setTemplateBusy(false);
                        }
                      }}
                      className="mono mt-2 rounded-lg bg-[#0d0d0d] px-2.5 py-1 text-[10px] font-bold text-white hover:bg-zinc-800"
                    >
                      Aplicar plantilla
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {/* Herramientas de Bloque Activo (Inspector Flotante) */}
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-violet-300 bg-violet-50/90 px-3.5 py-2 backdrop-blur-md">
            <div className="flex items-center gap-2">
              <span className="mono text-[11px] font-bold text-violet-950">
                #{activeCanvasBox}
              </span>
              <span className="mono text-[10px] text-violet-800">
                ({selectedBlock ? blockLabel(selectedBlock.type) : "Hero Mascota 3D"})
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-1.5">
              <button
                type="button"
                onClick={() => setInspectorTab("estilos")}
                className="mono rounded-lg border border-violet-300 bg-white px-2.5 py-1 text-[10px] font-bold text-violet-950 hover:bg-violet-100"
              >
                Editar Burbank
              </button>
              <button
                type="button"
                onClick={() => setInspectorTab("wordpress")}
                className="mono rounded-lg border border-violet-300 bg-white px-2.5 py-1 text-[10px] font-bold text-violet-950 hover:bg-violet-100"
              >
                Vincular SKU
              </button>
              <button
                type="button"
                onClick={() => {
                  setPaddingToken((p) =>
                    p === "24px / space-lg" ? "32px / space-xl" : "24px / space-lg",
                  );
                }}
                className="mono rounded-lg border border-violet-300 bg-white px-2.5 py-1 text-[10px] font-bold text-violet-950 hover:bg-violet-100"
              >
                Padding ({paddingToken.split(" ")[0]})
              </button>
            </div>
          </div>

          {/* Lienzo de edición en vivo (Visual o Código o Iframe Storefront) */}
          {workMode === "code" ? (
            <div className="flex flex-1 flex-col rounded-2xl border border-black/15 bg-white/90 p-4 backdrop-blur-xl">
              <div className="mb-2 flex items-center justify-between">
                <span className="mono text-xs font-bold text-[#0d0d0d]">
                  MODO CÓDIGO DIRECTO · HTML5 + TAILWIND CSS + SHORTCODES WP
                </span>
                <button
                  type="button"
                  onClick={() => {
                    navigator.clipboard?.writeText(htmlSnippet);
                    setCopiedSnippet(true);
                    setTimeout(() => setCopiedSnippet(false), 1800);
                  }}
                  className="mono rounded-lg bg-[#0d0d0d] px-3 py-1 text-[10px] font-bold text-white"
                >
                  {copiedSnippet ? "✓ Copiado" : "Copiar Snippet"}
                </button>
              </div>
              <textarea
                value={htmlSnippet}
                onChange={(e) => setHtmlSnippet(e.target.value)}
                className="min-h-[520px] w-full flex-1 rounded-xl border border-black/15 bg-slate-50 p-4 font-mono text-xs leading-relaxed text-[#0d0d0d] focus:border-[#0d0d0d] focus:outline-none"
              />
            </div>
          ) : showLiveIframe && previewUrl ? (
            <div className={`flex-1 rounded-2xl border border-black/15 bg-white p-2 ${canvasViewportWidth}`}>
              <iframe
                key={frameKey}
                src={previewUrl}
                title="Vista previa del storefront"
                sandbox="allow-scripts allow-same-origin"
                className="h-[640px] w-full rounded-xl border border-black/10 bg-white"
              />
            </div>
          ) : (
            <div
              className={`flex-1 space-y-4 rounded-2xl border border-black/10 bg-white/75 p-4 backdrop-blur-xl transition-all ${canvasViewportWidth}`}
            >
              {/* Barra superior de urgencia */}
              <div
                onClick={() => setActiveCanvasBox("barra-urgencia-top")}
                className={`cursor-pointer rounded-2xl border px-4 py-2.5 text-center text-xs font-bold transition-all ${
                  activeCanvasBox === "barra-urgencia-top"
                    ? "border-violet-600 bg-violet-50/90 text-[#0d0d0d] ring-2 ring-violet-500"
                    : "border-black/10 bg-white/90 text-[#0d0d0d]"
                }`}
              >
                ⚡ ENVÍO GRATIS NACIONAL EN PEDIDOS HOY · USA EL CUPÓN:{" "}
                <span className="mono rounded-lg bg-[#0d0d0d] px-2 py-0.5 text-white">
                  GROWUP2025
                </span>
              </div>

              {/* Hero Banner de Alto Rendimiento (contorno violeta de selección) */}
              <div
                onClick={() => setActiveCanvasBox("hero-mascota-promo")}
                className={`cursor-pointer rounded-2xl border p-6 backdrop-blur-xl transition-all ${
                  activeCanvasBox === "hero-mascota-promo"
                    ? "border-violet-600 bg-white/90 ring-2 ring-violet-500"
                    : "border-black/10 bg-white/80"
                }`}
              >
                <div className="grid items-center gap-6 lg:grid-cols-12">
                  <div className="space-y-4 lg:col-span-8">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="mono rounded-full border border-black/15 bg-slate-100 px-3 py-1 text-[10px] font-bold text-[#0d0d0d]">
                        COLECCIÓN OFICIAL 2025
                      </span>
                      <span className="mono rounded-full border border-violet-300 bg-violet-50 px-2.5 py-0.5 text-[10px] font-bold text-violet-900">
                        {headlineTag} · Burbank Big Condensed
                      </span>
                    </div>

                    <h2
                      style={{ fontSize: fontSizePx }}
                      className="display font-extrabold uppercase leading-[0.98] tracking-tight text-[#0d0d0d] md:text-4xl"
                    >
                      COLECCIÓN DEPORTIVA DE ALTO RENDIMIENTO
                    </h2>

                    {/* Bloque de precio y ahorro */}
                    <div className="flex flex-wrap items-baseline gap-3">
                      <span className="display text-3xl font-extrabold text-[#0d0d0d]">
                        $189.900 COP
                      </span>
                      <span className="text-sm text-[#525866] line-through">
                        $249.900 COP
                      </span>
                      <span className="mono rounded-full border border-emerald-300 bg-emerald-50 px-2.5 py-0.5 text-[10px] font-bold text-emerald-900">
                        AHORRAS 24%
                      </span>
                    </div>

                    {/* Selector interactivo de tallas + stock en vivo */}
                    <div className="space-y-2 pt-1">
                      <div className="flex items-center gap-3">
                        <span className="mono text-[10px] text-[#525866]">
                          TALLA ACTIVA: <strong className="text-[#0d0d0d]">{selectedSize}</strong>
                        </span>
                        <span className="mono text-[10px] font-bold text-emerald-700">
                          ● 14 unidades disponibles en stock (SKU-809)
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        {(["S", "M", "L", "XL"] as const).map((sz) => (
                          <button
                            key={sz}
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedSize(sz);
                            }}
                            className={`mono h-9 w-11 rounded-xl border text-xs font-bold transition-all ${
                              selectedSize === sz
                                ? "border-[#0d0d0d] bg-[#0d0d0d] text-white"
                                : "border-black/15 bg-white text-[#0d0d0d] hover:border-black/40"
                            }`}
                          >
                            {sz}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Botones de compra directa Wompi y Carrito */}
                    <div className="flex flex-wrap items-center gap-3 pt-2">
                      <button
                        type="button"
                        className={`rounded-2xl px-5 py-3 text-xs font-extrabold uppercase tracking-wider shadow-md ${accentButtonClass}`}
                      >
                        Comprar Ahora con Wompi (PSE · Bancolombia · Nequi · Tarjetas)
                      </button>
                      <button
                        type="button"
                        className="rounded-2xl border border-black/15 bg-white px-4 py-3 text-xs font-bold text-[#0d0d0d] hover:bg-slate-100"
                      >
                        Agregar al Carrito
                      </button>
                    </div>
                  </div>

                  {/* Avatar / Tarjeta Mascota 3D Flotante */}
                  <div className="lg:col-span-4">
                    <div className="rounded-2xl border border-black/10 bg-slate-50/90 p-4 text-center backdrop-blur-md">
                      <span className="mono text-[10px] font-bold text-violet-800">
                        AVATAR 3D FLOTANTE · GLTF/CSS
                      </span>
                      <div className="my-4 flex h-32 items-center justify-center rounded-2xl border border-black/10 bg-white shadow-inner">
                        <span className="display text-2xl font-extrabold text-[#0d0d0d]">
                          PRO · 3D
                        </span>
                      </div>
                      <p className="mono text-[10px] font-semibold text-emerald-800">
                        Sincronizado con ACF `post_title` &amp; `_price`
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Vitrina de Productos Sincronizados de WooCommerce */}
              <div
                onClick={() => setActiveCanvasBox("vitrina-woocommerce")}
                className={`cursor-pointer rounded-2xl border p-5 backdrop-blur-xl transition-all ${
                  activeCanvasBox === "vitrina-woocommerce"
                    ? "border-violet-600 bg-white/90 ring-2 ring-violet-500"
                    : "border-black/10 bg-white/80"
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2 pb-4">
                  <div>
                    <p className="mono text-[10px] font-bold text-[#525866]">
                      CATÁLOGO DINÁMICO WOOCOMMERCE · REST API v2
                    </p>
                    <h3 className="display mt-0.5 text-lg font-bold text-[#0d0d0d]">
                      Vitrina de Productos en Vivo (48 SKUs OK)
                    </h3>
                  </div>
                  <span className="mono rounded-xl border border-black/15 bg-white px-3 py-1.5 text-[10px] font-bold text-[#0d0d0d]">
                    Ver todo el catálogo en WordPress →
                  </span>
                </div>

                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  {WOO_LIVE_PRODUCTS.map((prod) => (
                    <div
                      key={prod.sku}
                      className="flex flex-col justify-between rounded-2xl border border-black/10 bg-white/90 p-3 shadow-xs"
                    >
                      <div>
                        <div className="flex h-28 items-end justify-between rounded-xl border border-black/10 bg-slate-100 p-2.5">
                          <span className="mono rounded-full border border-emerald-300 bg-emerald-50 px-2 py-0.5 text-[9px] font-bold text-emerald-900">
                            {prod.sku}
                          </span>
                          <span className="mono rounded-full border border-black/10 bg-white px-2 py-0.5 text-[9px] font-bold text-[#0d0d0d]">
                            {prod.stock}
                          </span>
                        </div>
                        <p className="mt-2.5 text-xs font-bold text-[#0d0d0d]">
                          {prod.name}
                        </p>
                      </div>
                      <div className="mt-3 flex items-center justify-between border-t border-black/10 pt-2">
                        <div>
                          <p className="mono text-xs font-bold text-[#0d0d0d]">
                            {prod.price}
                          </p>
                          <p className="text-[10px] text-[#525866] line-through">
                            {prod.compare}
                          </p>
                        </div>
                        <span className="mono rounded-lg bg-[#0d0d0d] px-2 py-1 text-[9px] font-bold text-white">
                          Wompi 1-Click
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Zona de Inserción Dinámica (Dropzone) */}
              <button
                type="button"
                onClick={() => onAddBlock("product_grid")}
                className="flex w-full flex-col items-center justify-center gap-1.5 rounded-2xl border-2 border-dashed border-black/20 bg-white/70 py-6 text-center backdrop-blur-md transition-all hover:border-violet-600 hover:bg-white"
              >
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#0d0d0d] text-base font-bold text-white">
                  +
                </span>
                <span className="text-xs font-bold text-[#0d0d0d]">
                  Zona de Inserción Dinámica (Dropzone)
                </span>
                <span className="mono text-[10px] text-[#525866]">
                  Arrastra y suelta nuevos bloques visuales o shortcodes compatibles con Gutenberg `[wp_woocommerce_cart]`
                </span>
              </button>
            </div>
          )}
        </div>

        {/* ===================================================================
            4. PANEL DERECHO: INSPECTOR DE PROPIEDADES & EDITOR DE CÓDIGO
           =================================================================== */}
        <div className="flex flex-col justify-between border-t border-black/10 bg-white/60 p-4 backdrop-blur-xl xl:border-l xl:border-t-0">
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-1 rounded-xl border border-black/10 bg-slate-100/90 p-1">
              {(
                [
                  { id: "estilos", label: "Estilos Visuales" },
                  { id: "wordpress", label: "WordPress" },
                  { id: "html", label: "HTML Snippet" },
                ] as const
              ).map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setInspectorTab(tab.id)}
                  className={`rounded-lg py-1.5 text-[11px] font-bold transition-all ${
                    inspectorTab === tab.id
                      ? "bg-[#0d0d0d] text-white shadow-xs"
                      : "text-[#525866] hover:text-[#0d0d0d]"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {inspectorTab === "estilos" ? (
              <div className="space-y-4">
                <div className="space-y-3 rounded-2xl border border-black/10 bg-white/90 p-3.5 shadow-xs">
                  <p className="mono text-[10px] font-bold text-[#0d0d0d]">
                    CONTROLES TIPOGRÁFICOS &amp; DE MARCA
                  </p>

                  <label className="block text-xs font-medium text-[#525866]">
                    Etiqueta HTML
                    <select
                      value={headlineTag}
                      onChange={(e) => setHeadlineTag(e.target.value)}
                      className="mt-1 w-full rounded-xl border border-black/15 bg-white px-3 py-2 font-mono text-xs text-[#0d0d0d]"
                    >
                      <option value="h2.font-headline-lg">h2.font-headline-lg</option>
                      <option value="h1.font-display-xl">h1.font-display-xl</option>
                      <option value="h3.font-section">h3.font-section</option>
                    </select>
                  </label>

                  <label className="block text-xs font-medium text-[#525866]">
                    Familia Tipográfica (Bloqueada por Marca)
                    <input
                      type="text"
                      readOnly
                      value="Burbank Big Condensed / Unbounded"
                      className="mt-1 w-full rounded-xl border border-violet-300 bg-violet-50 px-3 py-2 text-xs font-bold text-violet-950"
                    />
                  </label>

                  <div className="grid grid-cols-2 gap-2">
                    <label className="block text-xs font-medium text-[#525866]">
                      Tamaño
                      <select
                        value={fontSizePx}
                        onChange={(e) => setFontSizePx(e.target.value)}
                        className="mt-1 w-full rounded-xl border border-black/15 bg-white px-2.5 py-2 font-mono text-xs text-[#0d0d0d]"
                      >
                        <option value="28px">28px</option>
                        <option value="36px">36px</option>
                        <option value="44px">44px</option>
                      </select>
                    </label>
                    <label className="block text-xs font-medium text-[#525866]">
                      Peso
                      <select
                        value={fontWeight}
                        onChange={(e) => setFontWeight(e.target.value)}
                        className="mt-1 w-full rounded-xl border border-black/15 bg-white px-2.5 py-2 font-mono text-xs text-[#0d0d0d]"
                      >
                        <option value="700 Bold">700 Bold</option>
                        <option value="800 ExtraBold">800 ExtraBold</option>
                        <option value="600 SemiBold">600 SemiBold</option>
                      </select>
                    </label>
                  </div>

                  {/* Paleta de acentos corporativos */}
                  <div>
                    <span className="block text-xs font-medium text-[#525866]">
                      Paleta de Acentos Corporativos
                    </span>
                    <div className="mt-1.5 grid grid-cols-4 gap-1.5">
                      {(
                        [
                          { id: "naranja", label: "Naranja", dot: "bg-orange-500" },
                          { id: "violeta", label: "Violeta", dot: "bg-violet-600" },
                          { id: "negro", label: "Negro", dot: "bg-[#0d0d0d]" },
                          { id: "esmeralda", label: "Esmeralda", dot: "bg-emerald-600" },
                        ] as const
                      ).map((color) => (
                        <button
                          key={color.id}
                          type="button"
                          onClick={() => setBrandAccent(color.id)}
                          className={`flex flex-col items-center gap-1 rounded-xl border p-2 text-[10px] ${
                            brandAccent === color.id
                              ? "border-[#0d0d0d] bg-slate-100 font-bold text-[#0d0d0d]"
                              : "border-black/10 bg-white text-[#525866]"
                          }`}
                        >
                          <span className={`h-3.5 w-3.5 rounded-full ${color.dot}`} />
                          <span>{color.label}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <label className="block text-xs font-medium text-[#525866]">
                      Padding Interno
                      <input
                        type="text"
                        value={paddingToken}
                        onChange={(e) => setPaddingToken(e.target.value)}
                        className="mt-1 w-full rounded-xl border border-black/15 bg-white px-2.5 py-1.5 font-mono text-[11px] text-[#0d0d0d]"
                      />
                    </label>
                    <label className="block text-xs font-medium text-[#525866]">
                      Bordes Redondeados
                      <input
                        type="text"
                        value={radiusToken}
                        onChange={(e) => setRadiusToken(e.target.value)}
                        className="mt-1 w-full rounded-xl border border-black/15 bg-white px-2.5 py-1.5 font-mono text-[11px] text-[#0d0d0d]"
                      />
                    </label>
                  </div>
                </div>

                {/* Propiedades del bloque del registry seleccionado */}
                <div className="rounded-2xl border border-black/10 bg-white/90 p-3.5 text-[#0d0d0d]">
                  <p className="mono mb-2 text-[10px] font-bold uppercase text-[#525866]">
                    PROPIEDADES DEL BLOQUE ({selectedBlock ? blockLabel(selectedBlock.type) : "NINGUNO"})
                  </p>
                  {selectedBlock ? (
                    <BlockForm value={selectedBlock} onChange={updateSelected} />
                  ) : (
                    <p className="text-xs text-[#525866]">Selecciona un bloque para editar sus campos.</p>
                  )}
                </div>
              </div>
            ) : inspectorTab === "wordpress" ? (
              <div className="space-y-3.5 rounded-2xl border border-black/10 bg-white/90 p-4">
                <p className="mono text-[10px] font-bold text-[#0d0d0d]">
                  MAPEO DINÁMICO DE WORDPRESS (ACF / POST TYPE)
                </p>
                <label className="block text-xs font-medium text-[#525866]">
                  Post Type Vinculado
                  <input
                    type="text"
                    readOnly
                    value="product (WooCommerce)"
                    className="mt-1 w-full rounded-xl border border-black/15 bg-slate-50 px-3 py-2 font-mono text-xs font-bold text-emerald-800"
                  />
                </label>
                <label className="block text-xs font-medium text-[#525866]">
                  Campo Título ACF / WP
                  <input
                    type="text"
                    readOnly
                    value="post_title"
                    className="mt-1 w-full rounded-xl border border-black/15 bg-slate-50 px-3 py-2 font-mono text-xs text-[#0d0d0d]"
                  />
                </label>
                <label className="block text-xs font-medium text-[#525866]">
                  Campo Precio WooCommerce
                  <input
                    type="text"
                    readOnly
                    value="_price (Centavos COP)"
                    className="mt-1 w-full rounded-xl border border-black/15 bg-slate-50 px-3 py-2 font-mono text-xs text-[#0d0d0d]"
                  />
                </label>
                <label className="block text-xs font-medium text-[#525866]">
                  Pasarela Activa Enlazada
                  <input
                    type="text"
                    readOnly
                    value="Wompi Colombia (Live · PSE / Nequi / Tarjetas)"
                    className="mt-1 w-full rounded-xl border border-emerald-300 bg-emerald-50 px-3 py-2 font-mono text-xs font-bold text-emerald-900"
                  />
                </label>
                <label className="block text-xs font-medium text-[#525866]">
                  Shortcode Embebido
                  <input
                    type="text"
                    readOnly
                    value="[wp_woocommerce_cart]"
                    className="mt-1 w-full rounded-xl border border-violet-300 bg-violet-50 px-3 py-2 font-mono text-xs font-bold text-violet-900"
                  />
                </label>
              </div>
            ) : (
              <div className="space-y-3 rounded-2xl border border-black/10 bg-white/90 p-3.5">
                <div className="flex items-center justify-between">
                  <p className="mono text-[10px] font-bold text-[#0d0d0d]">
                    EDITOR DE CÓDIGO HTML / TAILWIND
                  </p>
                  <button
                    type="button"
                    onClick={() => {
                      navigator.clipboard?.writeText(htmlSnippet);
                      setCopiedSnippet(true);
                      setTimeout(() => setCopiedSnippet(false), 1800);
                    }}
                    className="mono rounded-lg bg-[#0d0d0d] px-2.5 py-1 text-[10px] font-bold text-white"
                  >
                    {copiedSnippet ? "✓ Copiado" : "Copiar Snippet"}
                  </button>
                </div>
                <textarea
                  rows={14}
                  value={htmlSnippet}
                  onChange={(e) => setHtmlSnippet(e.target.value)}
                  className="w-full rounded-xl border border-black/15 bg-slate-50 p-3 font-mono text-[11px] leading-relaxed text-[#0d0d0d] focus:border-[#0d0d0d] focus:outline-none"
                />
              </div>
            )}
          </div>

          {/* Botones de acción inferior del Inspector */}
          <div className="mt-4 space-y-2 border-t border-black/10 pt-3">
            <button
              type="button"
              onClick={() => void onSave()}
              className="w-full rounded-xl bg-[#0d0d0d] px-4 py-2.5 text-xs font-bold text-white hover:bg-zinc-800"
            >
              Sincronizar Cambios con WordPress &amp; Edge
            </button>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={onUndo}
                className="rounded-xl border border-black/15 bg-white px-3 py-2 text-[11px] font-bold text-[#0d0d0d] hover:bg-slate-100"
              >
                Revertir a Versión Anterior
              </button>
              {status === "published" ? (
                <button
                  type="button"
                  onClick={onUnpublish}
                  className="rounded-xl border border-rose-300 bg-rose-50 px-3 py-2 text-[11px] font-bold text-rose-900 hover:bg-rose-100"
                >
                  Despublicar
                </button>
              ) : (
                <button
                  type="button"
                  onClick={openPublish}
                  className="rounded-xl border border-emerald-300 bg-emerald-50 px-3 py-2 text-[11px] font-bold text-emerald-900 hover:bg-emerald-100"
                >
                  Publicar Ahora
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* =====================================================================
          5. BARRA DE DIAGNÓSTICO DE INFRAESTRUCTURA (FOOTER DE CONSOLA)
         ===================================================================== */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-black/10 bg-white/85 px-4 py-2.5 text-[11px] backdrop-blur-xl">
        <div className="flex flex-wrap items-center gap-4">
          <span className="mono text-[10px] font-bold text-emerald-800">
            ● Servidor Edge Cloudflare: Activo (12ms latencia)
          </span>
          <span className="mono text-[10px] font-bold text-[#0d0d0d]">
            ● Facturación Electrónica DIAN: Lista y Habilitada
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <span className="mono text-[10px] font-bold text-violet-900">
            Motor Headless: WooCommerce v8.2.1 • WP REST API v2
          </span>
          <span className="mono text-[10px] font-bold text-[#0d0d0d]">
            🔒 Certificado de Seguridad: SSL TLS 1.3 Oficial
          </span>
        </div>
      </div>

      {/* Modal confirmar publicación */}
      {publishOpen && baseline ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-label="Confirmar publicación"
          onClick={() => setPublishOpen(false)}
        >
          <div
            className="vn-card w-full max-w-md p-6 text-[#0d0d0d]"
            onClick={(event) => event.stopPropagation()}
          >
            <h2 className="display text-lg font-bold text-[#0d0d0d]">
              Publicar “/{initialSlug}” en Cloudflare Edge
            </h2>
            <p className="mt-2 text-sm text-[#525866]">
              Se publicará la versión {baseline.version} ({blocks.length}{" "}
              {blocks.length === 1 ? "bloque" : "bloques"}), sincronizando con
              WordPress/WooCommerce y purgando la caché del storefront.
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setPublishOpen(false)}
                className="rounded-xl border border-black/15 bg-white px-4 py-2 text-xs font-bold text-[#0d0d0d] hover:bg-slate-100"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={onPublishConfirm}
                className="rounded-xl bg-[#0d0d0d] px-4 py-2 text-xs font-extrabold text-white"
              >
                Publicar Tienda Ahora
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
