import type { components } from "@growup/contracts";

export type PageSummary = components["schemas"]["PageSummary"];
export type PageDetail = components["schemas"]["PageDetail"];
export type PageListResponse = components["schemas"]["PageListResponse"];

// Respuesta sin tipar estrictamente: el draft devuelve version/layout dinámicos.
export type DraftResponse = {
  id: string | null;
  version: number | null;
  layout: Record<string, unknown> | null;
};
