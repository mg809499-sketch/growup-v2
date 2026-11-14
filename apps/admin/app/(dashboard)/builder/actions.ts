"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { requireSession } from "@/lib/auth";
import { apiGet, apiSend, ApiError } from "@/lib/api";
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
  expectedVersion?: number | null,
): Promise<ActionResult & { version?: number; id?: string; conflict?: boolean; latest?: number }> {
  const { token } = await requireSession();
  let layout: unknown;
  try {
    layout = JSON.parse(layoutJson);
  } catch {
    return { ok: false, error: "El layout no es JSON válido" };
  }
  try {
    const body =
      expectedVersion === undefined ? { layout } : { layout, expected_version: expectedVersion };
    const draft = await apiSend<DraftResponse>(
      "POST",
      `/v1/admin/pages/${pageId}/draft`,
      token,
      body,
    );
    revalidatePath(`/builder/${pageId}`);
    return {
      ok: true,
      version: draft?.version ?? undefined,
      id: draft?.id ?? undefined,
    };
  } catch (error) {
    if (error instanceof ApiError && error.code === "VERSION_CONFLICT") {
      return { ok: false, conflict: true, error: "Alguien más editó esta página. Recarga para ver los cambios." };
    }
    return { ok: false, error: messageFor(error) };
  }
}

export async function applyTemplateAction(
  pageId: string,
  templateId: string,
): Promise<{ ok: true } | { ok: false; error: string }> {
  const { token } = await requireSession();
  if (!/^[a-z0-9-]+$/.test(templateId)) {
    return { ok: false, error: "Plantilla inválida" };
  }
  try {
    await apiSend(
      "POST",
      `/v1/admin/pages/${pageId}/apply-template`,
      token,
      { template_id: templateId },
    );
    revalidatePath(`/builder/${pageId}`);
    return { ok: true };
  } catch (error) {
    return { ok: false, error: messageFor(error) };
  }
}

export async function listTemplatesAction(): Promise<Array<{ template_id: string; name: string; description: string }>> {
  const { token } = await requireSession();
  try {
    return (await apiGet(
      "/v1/admin/templates",
      token,
    )) as unknown as Array<{ template_id: string; name: string; description: string }>;
  } catch {
    return [];
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

export type MediaItem = {
  id: string;
  url: string;
  alt: string;
  filename: string;
  mime: string;
  width: number | null;
};

export async function listMediaAction(
  offset = 0,
  limit = 24,
): Promise<{ ok: true; items: MediaItem[] } | { ok: false; error: string }> {
  const { token } = await requireSession();
  const mediaBase = process.env.NEXT_PUBLIC_MEDIA_BASE_URL?.replace(/\/$/, "") ?? "";
  try {
    const result = await apiGet<{
      items: Array<{
        id: string;
        r2_key: string;
        alt: string | null;
        original_filename: string | null;
        mime: string;
        width: number | null;
      }>;
    }>(
      `/v1/admin/media?status=ready&limit=${limit}&offset=${offset}`,
      token,
    );
    const items: MediaItem[] = result.items.map((asset) => ({
      id: asset.id,
      url: mediaBase ? `${mediaBase}/${asset.r2_key.replace(/^\//, "")}` : "",
      alt: asset.alt ?? "",
      filename: asset.original_filename ?? asset.r2_key,
      mime: asset.mime,
      width: asset.width,
    }));
    return { ok: true, items };
  } catch (error) {
    return { ok: false, error: messageFor(error) };
  }
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
