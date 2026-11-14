"use server";

import { revalidatePath } from "next/cache";

import { requireSession } from "@/lib/auth";
import { apiSend, ApiError } from "@/lib/api";

export async function resolveSuggestionAction(
  id: string,
  action: "accept" | "dismiss",
): Promise<{ ok: boolean; error?: string }> {
  const { token } = await requireSession();
  if (!id || !["accept", "dismiss"].includes(action)) {
    return { ok: false, error: "Acción inválida" };
  }
  try {
    await apiSend("POST", `/v1/admin/inventory/suggestions/${id}/resolve`, token, {
      action,
    });
    revalidatePath("/suggestions");
    return { ok: true };
  } catch (error) {
    const message = error instanceof ApiError ? error.message : "No se pudo actualizar";
    return { ok: false, error: message };
  }
}
