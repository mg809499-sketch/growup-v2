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
    <div className="vn-card flex flex-col justify-between p-5">
      <p className="mono text-[10px] font-semibold uppercase tracking-[0.16em] text-[#525866]">
        {label}
      </p>
      <p className="display mt-3 text-2xl font-extrabold tabular-nums tracking-tight text-[#0d0d0d] md:text-3xl">
        {value}
      </p>
      {detail ? (
        <p className="mt-1.5 text-[11px] text-[#525866]">{detail}</p>
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
      ? "border-rose-300 bg-rose-50/80 text-rose-950"
      : severity === "warn"
        ? "border-amber-300 bg-amber-50/80 text-amber-950"
        : "border-emerald-300 bg-emerald-50/80 text-emerald-950";
  return (
    <div className={`rounded-2xl border p-5 backdrop-blur-xl shadow-xs ${tone}`}>
      <p className="mono text-[10px] font-semibold uppercase tracking-[0.16em] opacity-80">
        {label}
      </p>
      <p className="display mt-3 text-2xl font-extrabold tabular-nums text-[#0d0d0d]">
        {value}
      </p>
      {detail ? <p className="mt-1.5 text-[11px] opacity-85">{detail}</p> : null}
    </div>
  );
}
