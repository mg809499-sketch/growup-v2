import Link from "next/link";

export default function NotFound() {
  return (
    <section className="mx-auto max-w-xl px-6 py-24 text-center">
      <p className="label text-[var(--muted)]">[ 404 ]</p>
      <h1 className="display mt-4 text-6xl">Esta página no existe</h1>
      <p className="mt-4 text-[var(--muted)]">
        Puede que el enlace cambió o que el contenido se movió.
      </p>
      <Link
        href="/"
        className="label mt-8 inline-flex border border-[var(--ink)] px-6 py-3"
      >
        Volver al inicio
      </Link>
    </section>
  );
}
