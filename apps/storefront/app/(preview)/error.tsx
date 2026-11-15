"use client";

import { useEffect } from "react";

export default function PreviewError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="mx-auto flex min-h-[60vh] max-w-2xl flex-col items-start justify-center px-4 py-16">
      <p className="label text-[var(--signal)]">Vista previa</p>
      <h1 className="display mt-3 text-3xl leading-tight">
        No pudimos cargar la vista previa
      </h1>
      <p className="mt-4 max-w-md text-sm leading-relaxed text-[var(--muted)]">
        El token es válido, pero la API no respondió como se esperaba. Vuelve a
        intentarlo desde el builder.
      </p>
      <button
        type="button"
        onClick={reset}
        className="label mt-8 border border-[var(--ink)] px-5 py-3 hover:bg-[var(--ink)] hover:text-[var(--surface)]"
      >
        Reintentar
      </button>
    </main>
  );
}
