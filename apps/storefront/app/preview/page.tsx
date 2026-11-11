import type { Metadata } from "next";

import { BlockRenderer } from "@/components/blocks";
import type { Block } from "@/lib/blocks";

export const dynamic = "force-dynamic";
export const metadata: Metadata = {
  title: "Vista previa",
  robots: { index: false, follow: false },
};

const API_URL = (process.env.GROWUP_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

async function loadPreview(token: string) {
  const response = await fetch(
    `${API_URL}/v1/storefront/pages/preview?token=${encodeURIComponent(token)}`,
    { cache: "no-store", headers: { Accept: "application/json" } },
  );
  if (!response.ok) {
    return null;
  }
  return (await response.json()) as {
    slug: string;
    title: string;
    layout: { blocks?: Block[] };
  };
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
  if (!page || !Array.isArray(page.layout?.blocks)) {
    return (
      <main className="mx-auto max-w-xl p-16 text-center">
        <h1 className="display text-2xl">Vista previa no disponible</h1>
        <p className="mt-4 text-[var(--muted)]">
          El token es inválido o expiró. Genera uno nuevo desde el builder.
        </p>
      </main>
    );
  }

  return (
    <main>
      <div className="border-b border-[var(--hairline)] bg-[var(--signal)] px-6 py-2 text-center">
        <p className="label text-[var(--surface)]">vista previa · sin publicar</p>
      </div>
      {page.layout.blocks.map((block) => (
        <BlockRenderer key={block.id} block={block} />
      ))}
    </main>
  );
}
