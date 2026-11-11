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
