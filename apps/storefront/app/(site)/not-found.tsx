import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-[60vh] max-w-3xl flex-col items-start justify-center px-4 py-16 md:px-10">
      <p className="label text-[var(--signal)]">404</p>
      <h1 className="display mt-3 text-[clamp(2.8rem,8vw,5rem)] leading-none">
        Pieza no encontrada
      </h1>
      <p className="mt-4 max-w-md text-sm leading-relaxed text-[var(--muted)]">
        La página o el producto que buscas no existe, no está activo o pertenece
        a otra tienda.
      </p>
      <Link
        className="label mt-8 border border-[var(--ink)] px-5 py-3 hover:bg-[var(--ink)] hover:text-[var(--surface)]"
        href="/collection"
      >
        Volver a la colección
      </Link>
    </main>
  );
}
