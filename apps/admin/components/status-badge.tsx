const styles: Record<string, string> = {
  active: "border-emerald-300 bg-emerald-50 text-emerald-900",
  paid: "border-emerald-300 bg-emerald-50 text-emerald-900",
  delivered: "border-emerald-300 bg-emerald-50 text-emerald-900",
  trialing: "border-amber-300 bg-amber-50 text-amber-900",
  preparing: "border-amber-300 bg-amber-50 text-amber-900",
  shipped: "border-sky-300 bg-sky-50 text-sky-900",
  ready: "border-emerald-300 bg-emerald-50 text-emerald-900",
  uploading: "border-black/15 bg-slate-100 text-[#525866]",
  draft: "border-black/15 bg-slate-100 text-[#525866]",
  failed: "border-rose-300 bg-rose-50 text-rose-900",
  suspended: "border-rose-300 bg-rose-50 text-rose-900",
  past_due: "border-amber-300 bg-amber-50 text-amber-900",
  canceled: "border-black/15 bg-slate-100 text-[#525866]",
  archived: "border-black/15 bg-slate-100 text-[#525866]",
  ALLOW: "border-emerald-300 bg-emerald-50 text-emerald-900",
  DENY: "border-rose-300 bg-rose-50 text-rose-900",
  HANDOFF: "border-amber-300 bg-amber-50 text-amber-900",
};

export function StatusBadge({ value }: { value: string }) {
  return (
    <span
      className={`mono inline-flex rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-[0.08em] ${
        styles[value] ?? "border-black/15 bg-slate-100 text-[#0d0d0d]"
      }`}
    >
      {value}
    </span>
  );
}
