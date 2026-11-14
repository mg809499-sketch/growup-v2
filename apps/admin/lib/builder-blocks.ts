// Definiciones client-side de los 16 bloques del registry cerrado (ADR-0005).
// Los defaults y límites replican blocks.py del backend; la autoridad de
// validación es el servidor al guardar — aquí se previenen errores obvios.

export type Block = Record<string, unknown> & { id: string; type: string };

// ---------- helpers de lectura (toleran datos crudos del borrador) ----------
export function str(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

export function num(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

export function bool(value: unknown, fallback = false): boolean {
  return typeof value === "boolean" ? value : fallback;
}

export function list(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

export function obj(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

export type LinkValue = { label: string; href: string } | null;
export function readLink(value: unknown): LinkValue {
  const record = obj(value);
  const label = str(record.label);
  const href = str(record.href);
  return label || href ? { label, href } : null;
}

export type ImageValue = { url: string; alt: string } | null;
export function readImage(value: unknown): ImageValue {
  const record = obj(value);
  const url = str(record.url);
  const alt = str(record.alt);
  return url || alt ? { url, alt } : null;
}

// ---------- definiciones ----------
export type BlockKind =
  | "header"
  | "footer"
  | "hero"
  | "editorial_split"
  | "product_grid"
  | "product_carousel"
  | "collection_grid"
  | "image_banner"
  | "rich_text"
  | "quote"
  | "gallery"
  | "video_embed"
  | "faq"
  | "newsletter"
  | "spacer"
  | "columns";

export type BlockDef = {
  type: BlockKind;
  label: string;
  hint: string;
  defaults: () => Record<string, unknown>;
};

export const BLOCK_DEFS: BlockDef[] = [
  { type: "header", label: "Encabezado", hint: "Barra superior con navegación y CTA", defaults: () => ({ brand: "growup", nav: [], cta: null }) },
  { type: "footer", label: "Pie de página", hint: "Columnas de enlaces y línea legal", defaults: () => ({ columns: [], legal_line: "" }) },
  { type: "hero", label: "Hero", hint: "Portada principal con título e imagen", defaults: () => ({ eyebrow: "", title: "Temporada 01", subtitle: "", image: null, cta: null, align: "left" }) },
  { type: "editorial_split", label: "Editorial", hint: "Texto + imagen a dos columnas", defaults: () => ({ kicker: "", title: "Editorial", body: "", image: null, image_side: "left", cta: null }) },
  { type: "product_grid", label: "Grilla de productos", hint: "Productos publicados del catálogo", defaults: () => ({ title: "Últimas piezas", source: "latest", category_slug: "", limit: 8, show_price: true }) },
  { type: "product_carousel", label: "Carrusel de productos", hint: "Productos en carrusel horizontal", defaults: () => ({ title: "", source: "latest", category_slug: "", limit: 8 }) },
  { type: "collection_grid", label: "Grilla de categorías", hint: "Accesos a colecciones con imagen", defaults: () => ({ title: "", items: [{ title: "Nueva", href: "/collection", image: null }] }) },
  { type: "image_banner", label: "Banner con imagen", hint: "Imagen grande con título y botón", defaults: () => ({ image: null, href: "", title: "", button_label: "", ratio: "21:9" }) },
  { type: "rich_text", label: "Texto enriquecido", hint: "Markdown sin HTML (negrita, listas, links)", defaults: () => ({ markdown: "Escribe aquí…", width: "narrow" }) },
  { type: "quote", label: "Cita", hint: "Cita destacada con autor", defaults: () => ({ text: "", author: "" }) },
  { type: "gallery", label: "Galería", hint: "Hasta 12 imágenes en grilla", defaults: () => ({ images: [], columns: 3 }) },
  { type: "video_embed", label: "Video", hint: "YouTube o Vimeo (allowlist)", defaults: () => ({ url: "", title: "" }) },
  { type: "faq", label: "Preguntas frecuentes", hint: "Acordeón de hasta 12 preguntas", defaults: () => ({ title: "", items: [{ question: "", answer: "" }] }) },
  { type: "newsletter", label: "Boletín", hint: "Captura de correo (disponible pronto)", defaults: () => ({ title: "Boletín", subtitle: "", cta_label: "Quiero recibir novedades" }) },
  { type: "spacer", label: "Separador", hint: "Espacio vertical entre bloques", defaults: () => ({ height: "md" }) },
  { type: "columns", label: "Columnas", hint: "Hasta 4 columnas con sub-bloques", defaults: () => ({ columns: [{ width: 6, blocks: [] }, { width: 6, blocks: [] }] }) },
];

export const BLOCK_DEF_MAP: Record<string, BlockDef> = Object.fromEntries(
  BLOCK_DEFS.map((def) => [def.type, def]),
);

export function blockLabel(type: string): string {
  return BLOCK_DEF_MAP[type]?.label ?? type;
}

let counter = 0;
export function createBlock(type: string): Block {
  const def = BLOCK_DEF_MAP[type];
  if (!def) {
    throw new Error(`Bloque desconocido: ${type}`);
  }
  counter += 1;
  const suffix =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID().slice(0, 8)
      : `${Date.now()}-${counter}`;
  return { id: `${type}-${suffix}`, type, ...def.defaults() };
}

const URL_PATTERN = /^https?:\/\/[^\s<>"']{1,2047}$/;
export function isValidUrl(value: string): boolean {
  return URL_PATTERN.test(value);
}

const RELATIVE_OR_HTTP = /^(https?:\/\/|\/)[^\s<>"']*$/;
export function isValidHref(value: string): boolean {
  return value === "" || RELATIVE_OR_HTTP.test(value);
}

const VIDEO_PATTERN =
  /^https:\/\/(www\.)?(youtube\.com|youtu\.be|player\.vimeo\.com)\/[\w\-./?=&%]{1,300}$/i;
export function isValidVideoUrl(value: string): boolean {
  return VIDEO_PATTERN.test(value);
}

export function mediaPublicUrl(r2Key: string): string {
  const base = process.env.NEXT_PUBLIC_MEDIA_BASE_URL?.replace(/\/$/, "");
  return base && r2Key ? `${base}/${r2Key.replace(/^\//, "")}` : "";
}
