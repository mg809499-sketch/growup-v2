// Block registry del storefront (ADR-0005). Espejo de los esquemas Pydantic del backend.
// El backend valida todo; aquí se renderiza con fallback seguro para tipos desconocidos.

export type ImageRef = { url: string; alt: string };
export type LinkRef = { label: string; href: string };

export type Block = {
  id: string;
  type: string;
  [key: string]: unknown;
};

export type PageLayout = {
  version: number;
  blocks: Block[];
};

/**
 * Extrae bloques del layout crudo de la API (fail-safe, espejo del registry
 * cerrado del backend): descarta entradas que no sean objetos, sanea id/type y
 * nunca lanza. Cualquier bloque desconocido llega igualmente a `BlockRenderer`,
 * que lo ignora (fallback seguro).
 */
export function parseLayoutBlocks(value: unknown): Block[] {
  if (typeof value !== "object" || value === null) return [];
  const blocks = (value as { blocks?: unknown }).blocks;
  if (!Array.isArray(blocks)) return [];
  const parsed: Block[] = [];
  for (const item of blocks) {
    if (typeof item !== "object" || item === null) continue;
    const record = item as Record<string, unknown>;
    const type = typeof record.type === "string" ? record.type : "";
    if (!type) continue;
    const id =
      typeof record.id === "string" && record.id.trim()
        ? record.id
        : `block-${parsed.length}`;
    parsed.push({ ...record, id, type });
  }
  return parsed;
}

export function asImage(value: unknown): ImageRef | null {
  if (typeof value !== "object" || value === null) return null;
  const candidate = value as Record<string, unknown>;
  if (typeof candidate.url === "string" && typeof candidate.alt === "string" && candidate.alt) {
    return { url: candidate.url, alt: candidate.alt };
  }
  return null;
}

export function asLink(value: unknown): LinkRef | null {
  if (typeof value !== "object" || value === null) return null;
  const candidate = value as Record<string, unknown>;
  if (typeof candidate.label === "string" && typeof candidate.href === "string") {
    return { label: candidate.label, href: candidate.href };
  }
  return null;
}

export function str(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}
