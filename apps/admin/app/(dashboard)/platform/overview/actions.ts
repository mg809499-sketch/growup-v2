"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { ApiError, apiSend } from "@/lib/api";
import { requireSession } from "@/lib/auth";

export async function dismissAlertAction(formData: FormData): Promise<void> {
  const { token } = await requireSession();
  const tenantId = String(formData.get("tenant_id") ?? "").trim();
  const alertKey = String(formData.get("alert_key") ?? "").trim();
  if (!tenantId || !alertKey) {
    redirect("/platform/overview?error=parametros-faltantes&tab=operacion");
  }
  try {
    await apiSend("POST", "/v1/platform/alerts/dismiss", token, {
      tenant_id: tenantId,
      alert_key: alertKey,
    });
  } catch (error) {
    const message =
      error instanceof ApiError
        ? error.message
        : "No se pudo descartar la alerta";
    redirect(`/platform/overview?error=${encodeURIComponent(message)}&tab=operacion`);
  }
  revalidatePath("/platform/overview");
}
