"use client";

import { useEffect } from "react";

export default function DashboardError({
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
    <div className="border border-red-200 bg-red-50 p-6 text-sm text-red-800">
      <p className="font-medium">No se pudo cargar esta vista</p>
      <p className="mt-2">
        Revisa que la API esté disponible y que la sesión siga vigente.
      </p>
      <button
        type="button"
        onClick={reset}
        className="mono mt-4 border border-red-300 bg-white px-3 py-1.5 text-[11px] uppercase tracking-[0.12em] hover:border-red-700"
      >
        Reintentar
      </button>
    </div>
  );
}
