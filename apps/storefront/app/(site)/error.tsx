"use client";

import { useEffect } from "react";

export default function ErrorPage({
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
    <main className="mx-auto flex min-h-[60vh] max-w-3xl flex-col items-start justify-center px-4 py-16 md:px-10">
      <p className="label text-[var(--signal)]">Tienda no disponible</p>
      <h1 className="display mt-3 text-[clamp(2.4rem,6vw,4.2rem)] leading-none">
        No pudimos cargar la tienda
      </h1>
      <p className="mt-4 max-w-md text-sm leading-relaxed text-[var(--muted)]">
        Revisa que la API esté disponible y que el host corresponda a un tenant
        activo.
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
