"use client";

import { useTransition, useState } from "react";

import { resolveSuggestionAction } from "@/app/(dashboard)/suggestions/actions";

export function SuggestionActionForm({ id }: { id: string }) {
  const [pending, startTransition] = useTransition();
  const [message, setMessage] = useState<string | null>(null);

  const act = (action: "accept" | "dismiss") => () =>
    startTransition(async () => {
      const result = await resolveSuggestionAction(id, action);
      setMessage(result.ok ? null : (result.error ?? "Error"));
    });

  return (
    <div className="mt-3 flex items-center gap-2">
      <button
        type="button"
        onClick={act("accept")}
        disabled={pending}
        className="border border-emerald-700 bg-emerald-700 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-600 disabled:opacity-50"
      >
        {pending ? "…" : "Marcar reordenado"}
      </button>
      <button
        type="button"
        onClick={act("dismiss")}
        disabled={pending}
        className="border border-slate-200 px-3 py-1.5 text-xs hover:border-slate-400 disabled:opacity-50"
      >
        {pending ? "…" : "Descartar"}
      </button>
      {message ? <p className="text-xs text-red-700">{message}</p> : null}
    </div>
  );
}
