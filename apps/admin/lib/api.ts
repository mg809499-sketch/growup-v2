import type { components } from "@growup/contracts";

export type MeResponse = components["schemas"]["MeResponse"];
export type PlanOut = components["schemas"]["PlanOut"];
export type PlanUpdateRequest = components["schemas"]["PlanUpdateRequest"];
export type ProductListResponse = components["schemas"]["ProductListResponse"];
export type ProductDetailResponse = components["schemas"]["ProductDetailResponse"];
export type PlatformTenantListResponse =
  components["schemas"]["PlatformTenantListResponse"];
export type MediaAssetListResponse = components["schemas"]["MediaAssetListResponse"];
export type AuditLogListResponse = components["schemas"]["AuditLogListResponse"];
export type AuditVerifyResponse = components["schemas"]["AuditVerifyResponse"];

const API_URL = (process.env.GROWUP_API_URL ?? "http://localhost:8000").replace(
  /\/$/,
  "",
);

export class ApiError extends Error {
  readonly status: number;
  readonly code: string | null;

  constructor(status: number, message: string, code: string | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
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
    throw await toApiError(response);
  }

  return (await response.json()) as T;
}

/** Solo para endpoints de texto (CSV, etc.): devuelve el cuerpo en crudo. */
export async function apiGetText(path: string, token: string): Promise<string> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      Accept: "text/csv,text/plain,*/*",
      Authorization: `Bearer ${token}`,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw await toApiError(response);
  }

  return response.text();
}

export type SafeGetError = {
  status: number;
  code: string | null;
  message: string;
};

/** Resultado discriminado de una lectura contra la API. Nunca lanza. */
export type SafeGetResult<T> =
  | { data: T; error: null; redirectToLogin: false }
  | { data: null; error: SafeGetError; redirectToLogin: false }
  | { data: null; error: null; redirectToLogin: true };

/**
 * apiGet tolerante a fallos para Server Components:
 *  - 401 → redirectToLogin (el llamador hace redirect("/login")).
 *  - cualquier otro fallo (4xx/5xx/red) → { error } con status/code para
 *    renderizar una tarjeta controlada en lugar de tumbar la página (React #441).
 */
export async function apiGetSafe<T>(
  path: string,
  token: string,
): Promise<SafeGetResult<T>> {
  try {
    return { data: await apiGet<T>(path, token), error: null, redirectToLogin: false };
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return { data: null, error: null, redirectToLogin: true };
    }
    return {
      data: null,
      error: {
        status: error instanceof ApiError ? error.status : 0,
        code: error instanceof ApiError ? error.code : null,
        message: error instanceof Error ? error.message : "Error inesperado",
      },
      redirectToLogin: false,
    };
  }
}

export async function apiSend<T>(
  method: "POST" | "PUT" | "PATCH" | "DELETE",
  path: string,
  token: string,
  body?: unknown,
): Promise<T | null> {
  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${token}`,
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });

  if (!response.ok) {
    throw await toApiError(response);
  }

  if (response.status === 204) {
    return null;
  }

  return (await response.json()) as T;
}

async function toApiError(response: Response): Promise<ApiError> {
  let message = `Error ${response.status}`;
  let code: string | null = null;
  try {
    const payload = (await response.json()) as {
      error?: { message?: string; code?: string };
    };
    message = payload.error?.message ?? payload.error?.code ?? message;
    code = payload.error?.code ?? null;
  } catch {
    // La API puede devolver HTML en errores de infraestructura.
  }
  return new ApiError(response.status, message, code);
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
