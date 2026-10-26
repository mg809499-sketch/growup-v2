import { formatPrice } from "@/lib/format";

export function Price({
  cents,
  compareAtCents,
  className = "",
}: {
  cents: number;
  compareAtCents?: number | null;
  className?: string;
}) {
  return (
    <span className={`inline-flex items-baseline gap-2 ${className}`}>
      <span>{formatPrice(cents)}</span>
      {compareAtCents && compareAtCents > cents ? (
        <span className="text-sm text-[var(--muted)] line-through">
          {formatPrice(compareAtCents)}
        </span>
      ) : null}
    </span>
  );
}
