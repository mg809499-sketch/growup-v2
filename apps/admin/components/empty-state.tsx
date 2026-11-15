export function EmptyState({
  title,
  description,
}: {
  title: string;
  description?: string;
}) {
  return (
    <div className="vn-card border-dashed px-6 py-12 text-center">
      <p className="text-sm font-bold text-[#0d0d0d]">{title}</p>
      {description ? (
        <p className="mx-auto mt-2 max-w-md text-sm text-[#525866]">{description}</p>
      ) : null}
    </div>
  );
}
