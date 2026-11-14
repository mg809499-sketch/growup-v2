"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { requireSession } from "@/lib/auth";
import { apiSend, ApiError } from "@/lib/api";

export async function updatePlanAction(formData: FormData) {
  const { token } = await requireSession();
  const planId = String(formData.get("plan_id") ?? "").trim();
  if (!planId) {
    redirect("/planes?error=plan-no-encontrado");
  }

  const name = String(formData.get("name") ?? "").trim();
  const priceCents = Number(formData.get("price_cents") ?? 0);
  const currency = String(formData.get("currency") ?? "COP").trim().toUpperCase();
  const interval = String(formData.get("billing_interval") ?? "month");
  const trialDays = Number(formData.get("trial_days") ?? 14);
  const sortOrder = Number(formData.get("sort_order") ?? 100);
  const badge = String(formData.get("badge") ?? "").trim();
  const featuresRaw = String(formData.get("features") ?? "");
  const active = String(formData.get("active") ?? "") === "on";

  const features = featuresRaw
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .slice(0, 64);

  if (!/^[A-Z]{3}$/.test(currency) || interval !== "month" && interval !== "year") {
    redirect("/planes?error=datos-invalidos");
  }

  try {
    await apiSend("PUT", `/v1/platform/plans/${planId}`, token, {
      name,
      price_cents: Math.max(0, Math.trunc(priceCents)),
      currency,
      billing_interval: interval,
      trial_days: Math.max(0, Math.min(365, Math.trunc(trialDays))),
      features,
      active,
      badge,
      sort_order: Math.max(0, Math.min(10000, Math.trunc(sortOrder))),
    });
  } catch (error) {
    const message =
      error instanceof ApiError ? error.message : "No se pudo guardar el plan";
    redirect(`/planes?error=${encodeURIComponent(message)}`);
  }
  revalidatePath("/planes");
}

export async function pauseTenantAction(formData: FormData) {
  const { token } = await requireSession();
  const tenantId = String(formData.get("tenant_id") ?? "").trim();
  const status = String(formData.get("status") ?? "").trim();
  if (!tenantId || (status !== "active" && status !== "suspended")) {
    redirect("/platform/tenants?error=accion-invalida");
  }
  try {
    await apiSend("PATCH", `/v1/platform/tenants/${tenantId}`, token, { status });
  } catch (error) {
    const message =
      error instanceof ApiError ? error.message : "No se pudo actualizar el tenant";
    redirect(`/platform/tenants?error=${encodeURIComponent(message)}`);
  }
  revalidatePath("/platform/tenants");
}
