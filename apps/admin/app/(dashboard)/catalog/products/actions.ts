"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { requireSession } from "@/lib/auth";
import { ApiError, apiSend } from "@/lib/api";
import type { ProductDetailResponse } from "@/lib/api";

function text(formData: FormData, key: string): string {
  return String(formData.get(key) ?? "").trim();
}

function required(formData: FormData, key: string, label: string): string {
  const value = text(formData, key);
  if (!value) {
    throw new Error(`${label} es obligatorio`);
  }
  return value;
}

function priceToCents(formData: FormData, key: string, label: string): number {
  const cents = parsePrice(text(formData, key), label);
  if (cents === null || cents <= 0) {
    throw new Error(`${label} debe ser mayor que cero`);
  }
  return cents;
}

function parsePrice(raw: string, label: string): number | null {
  if (!raw) {
    return null;
  }
  const pesos = Number(raw);
  if (!Number.isSafeInteger(pesos) || pesos < 0) {
    throw new Error(`${label} debe ser un entero en pesos`);
  }
  const cents = pesos * 100;
  if (!Number.isSafeInteger(cents)) {
    throw new Error(`${label} está fuera del rango permitido`);
  }
  return cents;
}

function integer(formData: FormData, key: string, label: string): number {
  const raw = text(formData, key);
  const value = Number(raw || "0");
  if (!Number.isInteger(value) || value < 0) {
    throw new Error(`${label} debe ser un entero no negativo`);
  }
  return value;
}

function tags(formData: FormData) {
  return text(formData, "tags")
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

function optionValues(formData: FormData) {
  const values: Record<string, string> = {};
  for (const suffix of ["", "_2"]) {
    const name = text(formData, `option_name${suffix}`);
    const value = text(formData, `option_value${suffix}`);
    if (name && value) {
      values[name] = value;
    }
  }
  return values;
}

function fail(path: string, error: unknown): never {
  const message =
    error instanceof ApiError || error instanceof Error
      ? error.message
      : "Error inesperado";
  redirect(`${path}?error=${encodeURIComponent(message)}`);
}

export async function createProductAction(formData: FormData) {
  const { token } = await requireSession();
  const path = "/catalog/products/new";

  let product: ProductDetailResponse | null = null;
  try {
    const body = {
      slug: required(formData, "slug", "El slug"),
      name: required(formData, "name", "El nombre"),
      description: text(formData, "description") || null,
      status: text(formData, "status") || "draft",
      brand: text(formData, "brand") || null,
      tags: tags(formData),
      variants: [
        {
          sku: required(formData, "sku", "El SKU"),
          name: required(formData, "variant_name", "El nombre de la variante"),
          price_cents: priceToCents(formData, "price_cop", "El precio"),
          stock: integer(formData, "stock", "El stock"),
          option_values: optionValues(formData),
          is_active: true,
        },
      ],
    };
    product = await apiSend<ProductDetailResponse>(
      "POST",
      "/v1/admin/products",
      token,
      body,
    );
  } catch (error) {
    fail(path, error);
  }

  if (!product) {
    fail(path, new Error("La API no devolvió el producto creado"));
  }

  revalidatePath("/catalog/products");
  redirect(`/catalog/products/${product.id}`);
}

export async function updateProductAction(formData: FormData) {
  const { token } = await requireSession();
  const productId = required(formData, "product_id", "El producto");
  const path = `/catalog/products/${productId}/edit`;

  try {
    await apiSend<ProductDetailResponse>(
      "PATCH",
      `/v1/admin/products/${productId}`,
      token,
      {
        name: required(formData, "name", "El nombre"),
        description: text(formData, "description") || null,
        status: text(formData, "status") || "draft",
        brand: text(formData, "brand") || null,
        tags: tags(formData),
      },
    );
  } catch (error) {
    fail(path, error);
  }

  revalidatePath("/catalog/products");
  revalidatePath(`/catalog/products/${productId}`);
  redirect(`/catalog/products/${productId}`);
}

export async function addVariantAction(formData: FormData) {
  const { token } = await requireSession();
  const productId = required(formData, "product_id", "El producto");
  const path = `/catalog/products/${productId}`;

  try {
    await apiSend<ProductDetailResponse>(
      "POST",
      `/v1/admin/products/${productId}/variants`,
      token,
      {
        sku: required(formData, "sku", "El SKU"),
        name: required(formData, "variant_name", "El nombre de la variante"),
        price_cents: priceToCents(formData, "price_cop", "El precio"),
        compare_at_price_cents: parsePrice(
          text(formData, "compare_at_cop"),
          "El precio anterior",
        ),
        stock: integer(formData, "stock", "El stock"),
        option_values: optionValues(formData),
        is_active: true,
      },
    );
  } catch (error) {
    fail(path, error);
  }

  revalidatePath(`/catalog/products/${productId}`);
  redirect(`/catalog/products/${productId}`);
}

export async function updateVariantAction(formData: FormData) {
  const { token } = await requireSession();
  const productId = required(formData, "product_id", "El producto");
  const variantId = required(formData, "variant_id", "La variante");
  const path = `/catalog/products/${productId}/variants/${variantId}/edit`;

  try {
    await apiSend<ProductDetailResponse>(
      "PATCH",
      `/v1/admin/products/${productId}/variants/${variantId}`,
      token,
      {
        name: required(formData, "variant_name", "El nombre de la variante"),
        price_cents: priceToCents(formData, "price_cop", "El precio"),
        compare_at_price_cents: parsePrice(
          text(formData, "compare_at_cop"),
          "El precio anterior",
        ),
        option_values: optionValues(formData),
        is_active: text(formData, "is_active") === "true",
      },
    );
  } catch (error) {
    fail(path, error);
  }

  revalidatePath(`/catalog/products/${productId}`);
  redirect(`/catalog/products/${productId}`);
}

export async function deleteVariantAction(formData: FormData) {
  const { token } = await requireSession();
  const productId = required(formData, "product_id", "El producto");
  const variantId = required(formData, "variant_id", "La variante");
  const path = `/catalog/products/${productId}`;

  try {
    await apiSend<null>(
      "DELETE",
      `/v1/admin/products/${productId}/variants/${variantId}`,
      token,
    );
  } catch (error) {
    fail(path, error);
  }

  revalidatePath(`/catalog/products/${productId}`);
  redirect(`/catalog/products/${productId}`);
}

export async function attachMediaAction(formData: FormData) {
  const { token } = await requireSession();
  const productId = required(formData, "product_id", "El producto");
  const path = `/catalog/products/${productId}`;

  try {
    await apiSend<ProductDetailResponse>(
      "POST",
      `/v1/admin/products/${productId}/media`,
      token,
      {
        media_asset_id: required(formData, "media_asset_id", "La imagen"),
        position: formData.get("position")
          ? integer(formData, "position", "La posición")
          : null,
        is_primary: text(formData, "is_primary") === "true",
      },
    );
  } catch (error) {
    fail(path, error);
  }

  revalidatePath(`/catalog/products/${productId}`);
  redirect(`/catalog/products/${productId}`);
}

export async function detachMediaAction(formData: FormData) {
  const { token } = await requireSession();
  const productId = required(formData, "product_id", "El producto");
  const mediaAssetId = required(formData, "media_asset_id", "La imagen");
  const path = `/catalog/products/${productId}`;

  try {
    await apiSend<null>(
      "DELETE",
      `/v1/admin/products/${productId}/media/${mediaAssetId}`,
      token,
    );
  } catch (error) {
    fail(path, error);
  }

  revalidatePath(`/catalog/products/${productId}`);
  redirect(`/catalog/products/${productId}`);
}
