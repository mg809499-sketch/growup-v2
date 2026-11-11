import "server-only";

import { cookies } from "next/headers";

import type { components } from "@growup/contracts";

import { getStorefrontHost } from "@/lib/api";

export type CartResponse = components["schemas"]["CartResponse"];

export const CART_COOKIE = "growup_cart";

const API_URL = (process.env.GROWUP_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export function cartCookieOptions() {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 24 * 30,
  };
}

export async function getCartId(): Promise<string | undefined> {
  const jar = await cookies();
  return jar.get(CART_COOKIE)?.value;
}

export async function fetchCart(): Promise<CartResponse | null> {
  const jar = await cookies();
  const host = await getStorefrontHost();
  const cartId = jar.get(CART_COOKIE)?.value;

  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Storefront-Host": host,
  };
  if (cartId) {
    headers["X-Cart-ID"] = cartId;
  }

  const response = await fetch(`${API_URL}/v1/storefront/cart`, {
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    return null;
  }

  const cart = (await response.json()) as CartResponse;
  const newCartId = response.headers.get("X-Cart-ID") ?? cart.cart_id;
  if (newCartId && newCartId !== cartId) {
    jar.set(CART_COOKIE, newCartId, cartCookieOptions());
  }
  return cart;
}
