import type { SafeGetError } from "@/lib/api";

/**
 * Tarjeta de error controlado para Server Components cuando la API falla.
 * No expone trazas ni mensajes internos sensibles: solo status + code + texto seguro.
 */
export function SectionError({
  title,
  error,
}: {
  title: string;
  error: SafeGetError;
}) {
  const codeLabel =
    error.status > 0
      ? `Error ${error.status}${error.code ? ` · ${error.code}` : ""}`
      : "No se pudo conectar con la API";

  return (
    <div
      role="alert"
      className="border border-amber-200 bg-amber-50 px-5 py-6 text-amber-900"
    >
      <p className="mono text-[10px] uppercase tracking-[0.18em] text-amber-700">
        {codeLabel}
      </p>
      <p className="mt-2 text-base font-medium">{title}</p>
      <p className="mt-1 text-sm leading-relaxed text-amber-800">
        {error.message}. Verifica que la API esté disponible y recarga la página.
      </p>
    </div>
  );
}
