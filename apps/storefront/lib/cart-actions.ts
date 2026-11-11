"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { getStorefrontHost } from "@/lib/api";
import { CART_COOKIE, cartCookieOptions } from "@/lib/cart";

const API_URL = (process.env.GROWUP_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

async function callCart(path: string, method: string, body?: unknown) {
  const host = await getStorefrontHost();
  const jar = await cookies();
  const cartId = jar.get(CART_COOKIE)?.value;

  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Storefront-Host": host,
  };
  if (cartId) headers["X-Cart-ID"] = cartId;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });

  const newCartId = response.headers.get("X-Cart-ID");
  if (newCartId && newCartId !== "converted" && newCartId !== cartId) {
    jar.set(CART_COOKIE, newCartId, cartCookieOptions());
  }

  return response;
}

export async function addToCartAction(formData: FormData) {
  const variantId = String(formData.get("variant_id") ?? "");
  const quantity = Number(formData.get("quantity") ?? 1);
  if (!variantId) {
    redirect("/collection");
  }
  await callCart("/v1/storefront/cart/items", "POST", {
    variant_id: variantId,
    quantity: Number.isFinite(quantity) && quantity > 0 ? Math.floor(quantity) : 1,
  });
  redirect("/carrito");
}

export async function updateCartItemAction(formData: FormData) {
  const variantId = String(formData.get("variant_id") ?? "");
  const quantity = Number(formData.get("quantity") ?? 0);
  await callCart("/v1/storefront/cart/items", "PATCH", {
    variant_id: variantId,
    quantity: Number.isFinite(quantity) ? Math.max(0, Math.floor(quantity)) : 0,
  });
  redirect("/carrito");
}

export async function checkoutAction(formData: FormData) {
  const email = String(formData.get("email") ?? "");
  const shippingZone = String(formData.get("shipping_zone") ?? "resto");
  const name = String(formData.get("shipping_name") ?? "");
  const line1 = String(formData.get("shipping_line1") ?? "");
  const city = String(formData.get("shipping_city") ?? "");
  const state = String(formData.get("shipping_state") ?? "");

  const host = await getStorefrontHost();
  const origin = `https://${host}`;
  const response = await callCart("/v1/storefront/checkout", "POST", {
    email,
    shipping_zone: shippingZone,
    shipping: {
      name,
      line1,
      city,
      state,
      line2: String(formData.get("shipping_line2") ?? "") || undefined,
    },
    redirect_base_url: origin,
  });

  if (!response.ok) {
    redirect("/carrito?error=No+se+pudo+iniciar+el+pago");
  }
  const payload = (await response.json()) as { wompi_url: string };
  if (!payload.wompi_url.startsWith("https://")) {
    redirect("/carrito?error=Respuesta+inválida+de+la+pasarela");
  }
  redirect(payload.wompi_url);
}
