export function KpiCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail?: string;
}) {
  return (
    <div className="border border-slate-200 bg-white p-5">
      <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">
        {label}
      </p>
      <p className="mono mt-3 text-2xl font-semibold tabular-nums tracking-tight text-slate-900">
        {value}
      </p>
      {detail ? (
        <p className="mt-1 text-[11px] text-slate-500">{detail}</p>
      ) : null}
    </div>
  );
}

/** Tarjeta con tono semántico para riesgos operativos. */
export function RiskCard({
  label,
  value,
  detail,
  severity,
}: {
  label: string;
  value: string;
  detail?: string;
  severity: "ok" | "warn" | "critical";
}) {
  const tone =
    severity === "critical"
      ? "border-red-200 bg-red-50 text-red-900"
      : severity === "warn"
        ? "border-amber-200 bg-amber-50 text-amber-900"
        : "border-emerald-200 bg-emerald-50 text-emerald-900";
  return (
    <div className={`border p-5 ${tone}`}>
      <p className="mono text-[10px] uppercase tracking-[0.16em] opacity-80">
        {label}
      </p>
      <p className="mono mt-3 text-2xl font-semibold tabular-nums">{value}</p>
      {detail ? <p className="mt-1 text-[11px] opacity-80">{detail}</p> : null}
    </div>
  );
}
