import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="max-w-md border border-slate-200 bg-white p-8">
        <p className="mono text-xs uppercase tracking-[0.18em] text-slate-500">
          404
        </p>
        <h1 className="mt-2 text-2xl font-semibold">Vista no encontrada</h1>
        <p className="mt-2 text-sm text-slate-500">
          El recurso no existe o no pertenece a tu tenant.
        </p>
        <Link
          className="mono mt-6 inline-block border border-slate-950 px-4 py-2 text-[11px] uppercase tracking-[0.12em] hover:bg-slate-950 hover:text-white"
          href="/"
        >
          Volver al resumen
        </Link>
      </div>
    </main>
  );
}
