import Link from "next/link";

import { login } from "@/app/login/actions";
import { isSupabaseConfigured } from "@/lib/supabase/server";

const errors: Record<string, string> = {
  config: "Falta configurar NEXT_PUBLIC_SUPABASE_URL y NEXT_PUBLIC_SUPABASE_ANON_KEY.",
  invalid: "Credenciales inválidas o usuario sin acceso.",
  missing: "Ingresa correo y contraseña.",
};

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { error } = await searchParams;
  const configured = isSupabaseConfigured();

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-12">
      <div className="w-full max-w-md border border-slate-200 bg-white p-8 shadow-[8px_8px_0_0_#111318]">
        <p className="mono text-xs uppercase tracking-[0.18em] text-slate-500">
          Growup / Admin
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight">
          Acceso al backoffice
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-500">
          Usa la cuenta de staff del tenant o de plataforma. El rol se resuelve
          desde Supabase Auth y las membresías.
        </p>

        {error ? (
          <p className="mt-5 border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {errors[error] ?? "No se pudo iniciar sesión."}
          </p>
        ) : null}

        {!configured ? (
          <div className="mt-5 border border-amber-200 bg-amber-50 px-3 py-3 text-sm leading-relaxed text-amber-800">
            <p className="font-medium">Supabase no está configurado.</p>
            <p className="mt-1">
              Copia <code className="mono">apps/admin/.env.example</code> a{" "}
              <code className="mono">.env.local</code> y completa la URL y la
              anon key del proyecto local.
            </p>
          </div>
        ) : null}

        <form action={login} className="mt-6 space-y-4">
          <label className="block">
            <span className="mono text-xs uppercase tracking-[0.14em] text-slate-500">
              Correo
            </span>
            <input
              className="mt-1 w-full border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-slate-950"
              type="email"
              name="email"
              autoComplete="email"
              required
              disabled={!configured}
            />
          </label>

          <label className="block">
            <span className="mono text-xs uppercase tracking-[0.14em] text-slate-500">
              Contraseña
            </span>
            <input
              className="mt-1 w-full border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-slate-950"
              type="password"
              name="password"
              autoComplete="current-password"
              required
              disabled={!configured}
            />
          </label>

          <button
            className="w-full bg-slate-950 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            type="submit"
            disabled={!configured}
          >
            Entrar
          </button>
        </form>

        <p className="mt-6 text-xs leading-relaxed text-slate-400">
          El storefront público no requiere login.{" "}
          <Link className="underline underline-offset-2" href="http://localhost:3000">
            Ir al storefront
          </Link>
        </p>
      </div>
    </main>
  );
}
