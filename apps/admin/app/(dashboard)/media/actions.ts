"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { requireSession } from "@/lib/auth";
import { ApiError, apiGet, apiSend } from "@/lib/api";

export type UploadUrlResult =
  | { ok: true; assetId: string; uploadUrl: string; expiresIn: number }
  | { ok: false; error: string };

export async function requestUploadUrlAction(input: {
  filename: string;
  contentType: string;
  sizeBytes: number;
}): Promise<UploadUrlResult> {
  const { token } = await requireSession();
  try {
    const result = await apiSend<{
      asset_id: string;
      upload_url: string;
      r2_key: string;
      expires_in: number;
    }>("POST", "/v1/admin/media/upload-url", token, {
      filename: input.filename,
      content_type: input.contentType,
      size_bytes: input.sizeBytes,
    });
    if (!result) {
      return { ok: false, error: "La API no devolvió la URL de subida" };
    }
    return {
      ok: true,
      assetId: result.asset_id,
      uploadUrl: result.upload_url,
      expiresIn: result.expires_in,
    };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof ApiError ? error.message : "No se pudo preparar la subida",
    };
  }
}

export type CompleteUploadResult = { ok: true } | { ok: false; error: string };

export async function completeUploadAction(
  assetId: string,
  alt: string,
): Promise<CompleteUploadResult> {
  const { token } = await requireSession();
  try {
    await apiSend("POST", `/v1/admin/media/${assetId}/complete`, token, { alt });
    return { ok: true };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof ApiError ? error.message : "No se pudo completar la subida",
    };
  }
}

export type MediaStatusResult =
  | { ok: true; status: string }
  | { ok: false; error: string };

export async function getMediaAssetStatusAction(
  assetId: string,
): Promise<MediaStatusResult> {
  const { token } = await requireSession();
  try {
    const asset = await apiGet<{ status: string }>(
      `/v1/admin/media/${assetId}`,
      token,
    );
    return { ok: true, status: asset.status };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof ApiError ? error.message : "No se pudo consultar el estado",
    };
  }
}

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
