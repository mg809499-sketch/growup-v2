import { cache } from "react";
import { headers } from "next/headers";

import type { components } from "@growup/contracts";

export type BootstrapResponse = components["schemas"]["BootstrapResponse"];
export type ProductListResponse = components["schemas"]["ProductListResponse"];
export type ProductSummaryResponse = components["schemas"]["ProductSummaryResponse"];
export type ProductDetailResponse = components["schemas"]["ProductDetailResponse"];
export type ProductMediaResponse = components["schemas"]["ProductMediaResponse"];
export type ProductVariantResponse = components["schemas"]["VariantResponse"];

const API_URL = (process.env.GROWUP_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function getStorefrontHost(): Promise<string> {
  const requestHeaders = await headers();
  return (
    requestHeaders.get("x-storefront-host") ??
    process.env.GROWUP_STOREFRONT_HOST ??
    requestHeaders.get("host") ??
    ""
  );
}

async function apiGet<T>(path: string, host: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      Accept: "application/json",
      "X-Storefront-Host": host,
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
      // La API no siempre devuelve JSON en errores de infraestructura.
    }
    throw new ApiError(response.status, message);
  }

  return (await response.json()) as T;
}

export const getBootstrap = cache(async (host: string): Promise<BootstrapResponse> => {
  return apiGet<BootstrapResponse>("/v1/storefront/bootstrap", host);
});

export const listProducts = cache(
  async (host: string, limit = 12, category?: string): Promise<ProductListResponse> => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (category) {
      params.set("category", category);
    }
    return apiGet<ProductListResponse>(
      `/v1/storefront/products?${params.toString()}`,
      host,
    );
  },
);

export const getProduct = cache(
  async (host: string, slug: string): Promise<ProductDetailResponse> => {
    return apiGet<ProductDetailResponse>(
      `/v1/storefront/products/${encodeURIComponent(slug)}`,
      host,
    );
  },
);
