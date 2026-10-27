"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { requireSession } from "@/lib/auth";
import { ApiError, apiSend } from "@/lib/api";

function fail(error: unknown): never {
  const message =
    error instanceof ApiError || error instanceof Error
      ? error.message
      : "Error inesperado";
  redirect(`/media?error=${encodeURIComponent(message)}`);
}

export async function updateMediaAltAction(formData: FormData) {
  const { token } = await requireSession();
  const assetId = String(formData.get("media_asset_id") ?? "").trim();
  const alt = String(formData.get("alt") ?? "").trim();

  if (!assetId) {
    fail(new Error("La imagen es obligatoria"));
  }
  if (!alt) {
    fail(new Error("El alt text es obligatorio"));
  }

  try {
    await apiSend("PATCH", `/v1/admin/media/${assetId}`, token, { alt });
  } catch (error) {
    fail(error);
  }

  revalidatePath("/media");
  redirect("/media");
}
