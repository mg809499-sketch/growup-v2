import type { SafeGetError } from "@/lib/api";

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
      className="vn-card border-amber-300 px-5 py-6 text-[#0d0d0d]"
    >
      <p className="mono text-[10px] font-bold uppercase tracking-[0.18em] text-amber-800">
        {codeLabel}
      </p>
      <p className="mt-2 text-base font-bold text-[#0d0d0d]">{title}</p>
      <p className="mt-1 text-sm leading-relaxed text-[#525866]">
        {error.message}. Verifica que la API esté disponible y recarga la página.
      </p>
    </div>
  );
}
