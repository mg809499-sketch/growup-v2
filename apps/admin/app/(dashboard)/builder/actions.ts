"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { requireSession } from "@/lib/auth";
import { apiSend, ApiError } from "@/lib/api";
import type { DraftResponse } from "@/lib/pages";

export type ActionResult =
  | { ok: true }
  | { ok: false; error: string };

function messageFor(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  return "Ocurrió un error inesperado";
}

export async function createPageAction(formData: FormData) {
  const { token } = await requireSession();
  const slug = String(formData.get("slug") ?? "").trim();
  const title = String(formData.get("title") ?? "").trim();
  if (!slug || !title) {
    redirect("/builder?error=slug-y-titulo-requeridos");
  }
  try {
    await apiSend("POST", "/v1/admin/pages", token, { slug, title });
  } catch (error) {
    redirect(`/builder?error=${encodeURIComponent(messageFor(error))}`);
  }
  revalidatePath("/builder");
  redirect("/builder");
}

export async function updatePageAction(
  pageId: string,
  formData: FormData,
): Promise<void> {
  const { token } = await requireSession();
  const title = String(formData.get("title") ?? "").trim();
  const slug = String(formData.get("slug") ?? "").trim();
  try {
    await apiSend("PATCH", `/v1/admin/pages/${pageId}`, token, {
      title: title || undefined,
      slug: slug || undefined,
    });
  } catch (error) {
    redirect(
      `/builder/${pageId}?error=${encodeURIComponent(messageFor(error))}`,
    );
  }
  revalidatePath(`/builder/${pageId}`);
  redirect(`/builder/${pageId}`);
}

export async function saveDraftAction(
  pageId: string,
  layoutJson: string,
): Promise<ActionResult & { version?: number; id?: string }> {
  const { token } = await requireSession();
  let layout: unknown;
  try {
    layout = JSON.parse(layoutJson);
  } catch {
    return { ok: false, error: "El layout no es JSON válido" };
  }
  try {
    const draft = await apiSend<DraftResponse>(
      "POST",
      `/v1/admin/pages/${pageId}/draft`,
      token,
      { layout },
    );
    revalidatePath(`/builder/${pageId}`);
    return {
      ok: true,
      version: draft?.version ?? undefined,
      id: draft?.id ?? undefined,
    };
  } catch (error) {
    return { ok: false, error: messageFor(error) };
  }
}

export async function publishAction(
  pageId: string,
  versionId: string,
  expectedVersion: number,
): Promise<ActionResult> {
  const { token } = await requireSession();
  try {
    await apiSend("POST", `/v1/admin/pages/${pageId}/publish`, token, {
      version_id: versionId,
      expected_version: expectedVersion,
    });
  } catch (error) {
    return { ok: false, error: messageFor(error) };
  }
  revalidatePath(`/builder/${pageId}`);
  revalidatePath("/builder");
  return { ok: true };
}

export async function unpublishAction(pageId: string): Promise<ActionResult> {
  const { token } = await requireSession();
  try {
    await apiSend("POST", `/v1/admin/pages/${pageId}/unpublish`, token);
  } catch (error) {
    return { ok: false, error: messageFor(error) };
  }
  revalidatePath(`/builder/${pageId}`);
  revalidatePath("/builder");
  return { ok: true };
}

export async function previewTokenAction(
  pageId: string,
  versionId: string,
): Promise<ActionResult & { token?: string }> {
  const { token: sessionToken } = await requireSession();
  try {
    const params = new URLSearchParams({ version_id: versionId });
    const result = await apiSend<{ token: string }>(
      "POST",
      `/v1/admin/pages/${pageId}/preview-token?${params.toString()}`,
      sessionToken,
    );
    return { ok: true, token: result?.token };
  } catch (error) {
    return { ok: false, error: messageFor(error) };
  }
}
