export function EmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="border border-[var(--hairline)] px-6 py-16 text-center">
      <p className="display text-2xl">{title}</p>
      <p className="mx-auto mt-3 max-w-md text-sm text-[var(--muted)]">{description}</p>
    </div>
  );
}
