import type { components } from "@growup/contracts";

import {
  isDesignPreview,
  mockBuilderDraft,
  mockBuilderPages,
  mockMeResponse,
  mockOrders,
  mockPlans,
  mockPlatformAlerts,
  mockPlatformOverview,
  mockPlatformTenants,
  mockProducts,
} from "@/lib/design-preview";

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
  if (isDesignPreview()) {
    const mocks = mockGetForDesignPreview(path);
    if (mocks !== null) {
      return mocks as T;
    }
  }

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
  if (isDesignPreview()) {
    return "id,slug,name,status,host\n00000000-0000-4000-8000-000000000010,ropa,Sol de Calle,active,ropa.growup.com\n";
  }

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

export async function apiGetSafe<T>(
  path: string,
  token: string,
): Promise<SafeGetResult<T>> {
  if (isDesignPreview()) {
    const mocks = mockGetForDesignPreview(path);
    if (mocks !== null) {
      return { data: mocks as T, error: null, redirectToLogin: false };
    }
  }

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

function mockGetForDesignPreview(path: string): unknown | null {
  const clean = path.split("?")[0].replace(/\/$/, "");
  switch (clean) {
    case "/v1/admin/me":
      return mockMeResponse;
    case "/v1/platform/overview":
      return mockPlatformOverview;
    case "/v1/platform/alerts":
      return mockPlatformAlerts;
    case "/v1/platform/tenants":
      return mockPlatformTenants;
    case "/v1/platform/plans":
      return mockPlans;
    case "/v1/admin/pages":
      return mockBuilderPages;
    case "/v1/admin/products":
      return mockProducts;
    case "/v1/admin/orders":
      return mockOrders;
    case "/v1/admin/theme":
      return { tokens: { schema_version: 1, preset: "nova" } };
    case "/v1/admin/templates":
      return [
        {
          template_id: "ropa-starter",
          name: "Colección Deportiva & Streetwear (v3.0)",
          description: "Hero Mascota 3D + Catálogo WooCommerce + Checkout Express Wompi.",
        },
        {
          template_id: "joyeria-starter",
          name: "Alta Joyería · Aurélia Atelier",
          description: "Editorial macro en obsidiana, piezas 1 de 1 y certificación.",
        },
        {
          template_id: "drop-flash",
          name: "Drop Flash · Barra de Urgencia",
          description: "Lanzamiento con contador regresivo, stock en vivo y pago 1-click.",
        },
      ];
    default:
      if (/^\/v1\/admin\/pages\/[^/]+\/draft$/.test(clean)) {
        return mockBuilderDraft;
      }
      if (/^\/v1\/admin\/pages\/[^/]+$/.test(clean)) {
        const pageId = clean.split("/").pop();
        return (
          mockBuilderPages.items.find((p) => p.id === pageId) ??
          mockBuilderPages.items[0]
        );
      }
      if (clean.startsWith("/v1/admin/audit/verify")) {
        return { valid: true, checked_entries: 42, broken_at_id: null };
      }
      if (clean.startsWith("/v1/admin/audit")) {
        return {
          items: [
            {
              id: "00000000-0000-4000-8000-000000000901",
              action: "content.publish",
              decision: "ALLOW",
              policy_version: "v1.4",
              actor_id: mockMeResponse.tenant_id,
              reason: "Publicación atómica Store Builder v3.0 en Cloudflare Edge",
              entry_hash: "8f9d2a1c4b7e60319a8d2c4f1e0b7a6c",
              prev_hash: "00000000000000000000000000000000",
              created_at: "2026-11-15T09:30:00.000Z",
            },
            {
              id: "00000000-0000-4000-8000-000000000902",
              action: "inventory.reorder_suggestion",
              decision: "HANDOFF",
              policy_version: "v1.4",
              actor_id: mockMeResponse.tenant_id,
              reason: "Stock bajo detectado en SKU Citrato de Magnesio (4 uds)",
              entry_hash: "3c7b91e04a2d8f615e3a9c0d1b4e7f2a",
              prev_hash: "8f9d2a1c4b7e60319a8d2c4f1e0b7a6c",
              created_at: "2026-11-15T09:45:00.000Z",
            },
          ],
          total: 2,
          limit: 20,
          offset: 0,
        };
      }
      if (clean.startsWith("/v1/admin/suggestions")) {
        return {
          items: [
            {
              id: "00000000-0000-4000-8000-000000000801",
              kind: "reorder",
              status: "pending",
              title: "Reabastecer SKU-809 · Chaqueta Deportiva Valkyrie (Talla M)",
              summary: "Velocidad de venta +38% en las últimas 48h. Stock actual: 4 unidades.",
              payload: { sku: "SKU-809", suggested_qty: 24, current_stock: 4 },
              created_at: "2026-11-15T08:00:00.000Z",
            },
          ],
          total: 1,
        };
      }
      if (
        clean.startsWith("/v1/admin/") ||
        clean.startsWith("/v1/platform")
      ) {
        return { items: [], total: 0, limit: 20, offset: 0 };
      }
      return null;
  }
}

export async function apiSend<T>(
  method: "POST" | "PUT" | "PATCH" | "DELETE",
  path: string,
  token: string,
  body?: unknown,
): Promise<T | null> {
  if (isDesignPreview()) {
    return {
      id: "00000000-0000-4000-8000-000000000301",
      version: 5,
      token: "preview-demo-token",
      status: "ok",
    } as unknown as T;
  }

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
