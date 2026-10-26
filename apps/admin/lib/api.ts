import type { components } from "@growup/contracts";

export type MeResponse = components["schemas"]["MeResponse"];
export type ProductListResponse = components["schemas"]["ProductListResponse"];
export type ProductDetailResponse = components["schemas"]["ProductDetailResponse"];
export type PlatformTenantListResponse =
  components["schemas"]["PlatformTenantListResponse"];
export type MediaAssetListResponse = components["schemas"]["MediaAssetListResponse"];
export type AuditLogListResponse = components["schemas"]["AuditLogListResponse"];
export type AuditVerifyResponse = components["schemas"]["AuditVerifyResponse"];

const API_URL = (process.env.GROWUP_API_URL ?? "http://127.0.0.1:8000").replace(
  /\/$/,
  "",
);

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function apiGet<T>(path: string, token: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${token}`,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let message = `Error ${response.status}`;
    try {
      const payload = (await response.json()) as {
        error?: { message?: string; code?: string };
      };
      message = payload.error?.message ?? payload.error?.code ?? message;
    } catch {
      // La API puede devolver HTML en errores de infraestructura.
    }
    throw new ApiError(response.status, message);
  }

  return (await response.json()) as T;
}

export function queryString(
  params: Record<string, string | number | null | undefined>,
): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  }
  const result = search.toString();
  return result ? `?${result}` : "";
}
