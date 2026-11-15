export function PageHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="border-b border-black/10 pb-5">
      <p className="mono text-[10px] font-semibold uppercase tracking-[0.2em] text-[#525866]">
        {eyebrow}
      </p>
      <h1 className="display mt-2 text-2xl font-extrabold tracking-tight text-[#0d0d0d] md:text-3xl">
        {title}
      </h1>
      {description ? (
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-[#525866]">
          {description}
        </p>
      ) : null}
    </div>
  );
}
