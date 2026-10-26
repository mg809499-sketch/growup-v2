const styles: Record<string, string> = {
  active: "border-emerald-200 bg-emerald-50 text-emerald-700",
  trialing: "border-amber-200 bg-amber-50 text-amber-700",
  ready: "border-emerald-200 bg-emerald-50 text-emerald-700",
  uploading: "border-slate-200 bg-slate-50 text-slate-600",
  draft: "border-slate-200 bg-slate-50 text-slate-600",
  failed: "border-red-200 bg-red-50 text-red-700",
  suspended: "border-red-200 bg-red-50 text-red-700",
  past_due: "border-amber-200 bg-amber-50 text-amber-700",
  canceled: "border-slate-200 bg-slate-50 text-slate-500",
  archived: "border-slate-200 bg-slate-50 text-slate-500",
  ALLOW: "border-emerald-200 bg-emerald-50 text-emerald-700",
  DENY: "border-red-200 bg-red-50 text-red-700",
  HANDOFF: "border-amber-200 bg-amber-50 text-amber-700",
};

export function StatusBadge({ value }: { value: string }) {
  return (
    <span
      className={`mono inline-flex border px-2 py-0.5 text-[10px] uppercase tracking-[0.08em] ${
        styles[value] ?? "border-slate-200 bg-slate-50 text-slate-600"
      }`}
    >
      {value}
    </span>
  );
}
