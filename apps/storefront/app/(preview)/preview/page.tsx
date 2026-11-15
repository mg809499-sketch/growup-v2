import type { Metadata } from "next";

import { BlockRenderer } from "@/components/blocks";
import { parseLayoutBlocks } from "@/lib/blocks";
import { setPreviewHost } from "@/lib/preview-host";

export const dynamic = "force-dynamic";
export const metadata: Metadata = {
  title: "Vista previa",
  robots: { index: false, follow: false },
};

const API_URL = (process.env.GROWUP_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

type PreviewPayload = {
  slug: string;
  title: string;
  /** Host primario del tenant dueño del token; opcional en respuestas viejas. */
  host?: string | null;
  layout: unknown;
};

async function loadPreview(token: string): Promise<PreviewPayload | null> {
  const response = await fetch(
    `${API_URL}/v1/storefront/pages/preview?token=${encodeURIComponent(token)}`,
    { cache: "no-store", headers: { Accept: "application/json" } },
  );
  if (!response.ok) {
    return null;
  }
  return (await response.json()) as PreviewPayload;
}

export default async function PreviewPage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }>;
}) {
  const { token } = await searchParams;
  if (!token) {
    return (
      <main className="mx-auto max-w-xl p-16 text-center">
        <h1 className="display text-2xl">Vista previa</h1>
        <p className="mt-4 text-[var(--muted)]">Falta el token de previsualización.</p>
      </main>
    );
  }

  const page = await loadPreview(token);
  const blocks = page ? parseLayoutBlocks(page.layout) : [];
  if (!page || blocks.length === 0) {
    return (
      <main className="mx-auto max-w-xl p-16 text-center">
        <h1 className="display text-2xl">Vista previa no disponible</h1>
        <p className="mt-4 text-[var(--muted)]">
          El token es inválido o expiró. Genera uno nuevo desde el builder.
        </p>
      </main>
    );
  }

  // Fijo el host del tenant dueño del token ANTES de renderizar los bloques:
  // bootstrap ya no aplica aquí (layout bare), pero helpers como
  // getStorefrontHost/listProducts lo leen para ProductGrid y compañía.
  setPreviewHost(page.host ?? null);

  return (
    <main>
      <div className="border-b border-[var(--hairline)] bg-[var(--signal)] px-6 py-2 text-center">
        <p className="label text-[var(--surface)]">vista previa · sin publicar</p>
      </div>
      {blocks.map((block) => (
        <BlockRenderer key={block.id} block={block} />
      ))}
    </main>
  );
}
