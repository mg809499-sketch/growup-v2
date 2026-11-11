import Link from "next/link";
import { redirect } from "next/navigation";

import { completeSignup, login, loginWithGoogle } from "@/app/login/actions";
import { createClient, isSupabaseConfigured } from "@/lib/supabase/server";
import { apiGet } from "@/lib/api";
import type { MeResponse } from "@/lib/api";

const errors: Record<string, string> = {
  config: "Falta configurar NEXT_PUBLIC_SUPABASE_URL y NEXT_PUBLIC_SUPABASE_ANON_KEY.",
  invalid: "Credenciales inválidas o usuario sin acceso.",
  missing: "Completa todos los campos obligatorios.",
  oauth: "No se pudo continuar con Google. Inténtalo de nuevo.",
  session: "Tu sesión expiró. Vuelve a intentarlo.",
  slug: "Ese slug ya está tomado. Elige otro.",
  domain: "Ese dominio ya está registrado por otra tienda.",
  plan: "El plan elegido no está disponible.",
  signup: "No se pudo completar el registro. Inténtalo de nuevo.",
};

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; tab?: string }>;
}) {
  const { error, tab } = await searchParams;
  const configured = isSupabaseConfigured();

  const supabase = configured ? await createClient() : null;
  const {
    data: { user },
  } = supabase
    ? await supabase.auth.getUser()
    : { data: { user: null } };
  const {
    data: { session },
  } = supabase
    ? await supabase.auth.getSession()
    : { data: { session: null } };

  // Si ya cuenta con membresía, no hay nada que completar: al dashboard.
  if (session) {
    let me: MeResponse | null = null;
    try {
      me = await apiGet<MeResponse>("/v1/admin/me", session.access_token);
    } catch {
      me = null; // 401/403: usuario autenticado aún sin membresía
    }
    if (me !== null) {
      redirect("/");
    }
  }

  const needsCompletion = Boolean(user && session);
  const showTab = tab === "crear" ? "crear" : tab === "iniciar" ? "iniciar" : null;
  const errorMessage = error ? errors[error] ?? "No se pudo completar la operación." : null;

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-12">
      <div className="w-full max-w-4xl">
        <p className="mono text-xs uppercase tracking-[0.18em] text-slate-500">
          Growup / Acceso
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight">
          Accede a la plataforma
        </h1>
        <p className="mt-2 max-w-xl text-sm leading-relaxed text-slate-500">
          ¿Ya tienes cuenta? Inicia sesión. ¿Estás abriendo tu tienda? Crea tu
          cuenta: eliges plan, slug y dominio y tu tienda queda lista.
        </p>

        {errorMessage ? (
          <p className="mt-5 border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {errorMessage}
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

        <div className="mt-6 grid gap-6 md:grid-cols-2">
          {/* Panel: Crear cuenta */}
          <section
            aria-label="Crear cuenta"
            className={`border border-slate-200 bg-white p-6 shadow-[8px_8px_0_0_#111318] ${
              showTab === "crear" ? "ring-2 ring-slate-950" : ""
            }`}
          >
            <p className="mono text-xs uppercase tracking-[0.18em] text-slate-500">
              Crear cuenta
            </p>
            <h2 className="mt-2 text-xl font-semibold tracking-tight">
              Abre tu tienda
            </h2>

            {needsCompletion ? (
              <>
                <p className="mt-2 text-xs leading-relaxed text-slate-500">
                  Continúa con Google, completa los datos y tu tienda queda
                  creada (trial de 14 días).
                </p>
                <form action={completeSignup} className="mt-4 space-y-3">
                  <label className="block">
                    <span className="mono text-[11px] uppercase tracking-[0.14em] text-slate-500">
                      Correo
                    </span>
                    <input
                      className="mono mt-1 w-full border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500"
                      type="email"
                      value={user?.email ?? ""}
                      disabled
                      readOnly
                    />
                  </label>

                  <label className="block">
                    <span className="mono text-[11px] uppercase tracking-[0.14em] text-slate-500">
                      Nombre completo
                    </span>
                    <input
                      className="mt-1 w-full border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-slate-950"
                      type="text"
                      name="full_name"
                      autoComplete="name"
                      required
                      disabled={!configured}
                    />
                  </label>

                  <label className="block">
                    <span className="mono text-[11px] uppercase tracking-[0.14em] text-slate-500">
                      Celular
                    </span>
                    <input
                      className="mt-1 w-full border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-slate-950"
                      type="tel"
                      name="phone"
                      autoComplete="tel"
                      placeholder="+57 300 000 0000"
                      required
                      disabled={!configured}
                    />
                  </label>

                  <div className="grid grid-cols-3 gap-3">
                    <label className="block">
                      <span className="mono text-[11px] uppercase tracking-[0.14em] text-slate-500">
                        Tipo doc.
                      </span>
                      <select
                        className="mt-1 w-full border border-slate-300 bg-white px-2 py-2 text-sm outline-none focus:border-slate-950"
                        name="doc_type"
                        required
                        disabled={!configured}
                        defaultValue="CC"
                      >
                        <option value="CC">CC</option>
                        <option value="CE">CE</option>
                        <option value="NIT">NIT</option>
                        <option value="PP">Pasaporte</option>
                      </select>
                    </label>
                    <label className="col-span-2 block">
                      <span className="mono text-[11px] uppercase tracking-[0.14em] text-slate-500">
                        Número de identificación
                      </span>
                      <input
                        className="mt-1 w-full border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-slate-950"
                        type="text"
                        name="doc_number"
                        inputMode="numeric"
                        required
                        disabled={!configured}
                      />
                    </label>
                  </div>

                  <label className="block">
                    <span className="mono text-[11px] uppercase tracking-[0.14em] text-slate-500">
                      Nombre de la tienda
                    </span>
                    <input
                      className="mt-1 w-full border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-slate-950"
                      type="text"
                      name="store_name"
                      required
                      disabled={!configured}
                    />
                  </label>

                  <div className="grid grid-cols-2 gap-3">
                    <label className="block">
                      <span className="mono text-[11px] uppercase tracking-[0.14em] text-slate-500">
                        Tipo de tienda
                      </span>
                      <select
                        className="mt-1 w-full border border-slate-300 bg-white px-2 py-2 text-sm outline-none focus:border-slate-950"
                        name="store_type"
                        required
                        disabled={!configured}
                        defaultValue="ropa"
                      >
                        <option value="ropa">Ropa</option>
                        <option value="joyeria">Joyería</option>
                        <option value="otro">Otro</option>
                      </select>
                    </label>
                    <label className="block">
                      <span className="mono text-[11px] uppercase tracking-[0.14em] text-slate-500">
                        Plan
                      </span>
                      <select
                        className="mt-1 w-full border border-slate-300 bg-white px-2 py-2 text-sm outline-none focus:border-slate-950"
                        name="plan_code"
                        required
                        disabled={!configured}
                        defaultValue="starter"
                      >
                        <option value="starter">Starter</option>
                        <option value="pro">Pro</option>
                      </select>
                    </label>
                  </div>
                  <p className="text-[11px] leading-snug text-slate-400">
                    Los precios de los planes se confirman antes del lanzamiento;
                    tu tienda empieza en trial de 14 días.
                  </p>

                  <label className="block">
                    <span className="mono text-[11px] uppercase tracking-[0.14em] text-slate-500">
                      Slug (subdominio)
                    </span>
                    <div className="mt-1 flex items-stretch">
                      <input
                        className="w-full min-w-0 border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-slate-950"
                        type="text"
                        name="slug"
                        placeholder="mi-tienda"
                        pattern="[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?"
                        required
                        disabled={!configured}
                      />
                      <span className="mono flex items-center border border-l-0 border-slate-300 bg-slate-50 px-2 text-[11px] text-slate-500">
                        .growup.com
                      </span>
                    </div>
                  </label>

                  <fieldset className="space-y-2 border border-slate-200 p-3">
                    <legend className="mono px-1 text-[11px] uppercase tracking-[0.14em] text-slate-500">
                      Dominio
                    </legend>
                    <label className="flex items-start gap-2 text-sm text-slate-700">
                      <input
                        type="radio"
                        name="domain_choice"
                        value="subdomain"
                        defaultChecked
                        disabled={!configured}
                        className="mt-1"
                      />
                      <span>
                        Quiero el subdominio <strong>slug.growup.com</strong>
                      </span>
                    </label>
                    <label className="flex items-start gap-2 pl-6 text-xs text-slate-600">
                      <input
                        type="checkbox"
                        name="wants_subdomain"
                        disabled={!configured}
                        className="mt-0.5"
                      />
                      Quiero comprarlo en Growup (te contactamos para
                      activarlo)
                    </label>
                    <label className="flex items-start gap-2 text-sm text-slate-700">
                      <input
                        type="radio"
                        name="domain_choice"
                        value="custom"
                        disabled={!configured}
                        className="mt-1"
                      />
                      <span>Ya tengo mi dominio propio (DNS después)</span>
                    </label>
                    <input
                      className="ml-6 mt-1 w-[calc(100%-1.5rem)] border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-slate-950 placeholder:text-slate-400"
                      type="text"
                      name="custom_domain"
                      placeholder="www.mitienda.co"
                      pattern="[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+"
                      disabled={!configured}
                    />
                    <p className="pl-6 text-[11px] leading-snug text-slate-400">
                      Solo si elegiste dominio propio. Se registra sin verificar;
                      la activación DNS sigue después.
                    </p>
                  </fieldset>

                  <button
                    className="w-full bg-slate-950 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                    type="submit"
                    disabled={!configured}
                  >
                    Crear mi tienda
                  </button>
                </form>
              </>
            ) : (
              <>
                <p className="mt-2 text-sm leading-relaxed text-slate-500">
                  Continúa con Google y tu tienda se crea con el plan que
                  elijas: catálogo, pedidos, builder y auditoría incluidos.
                </p>
                <form action={loginWithGoogle} className="mt-5">
                  <button
                    className="w-full border border-slate-950 bg-white px-4 py-3 text-sm font-medium text-slate-950 transition-colors hover:bg-slate-950 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
                    type="submit"
                    disabled={!configured}
                  >
                    Continuar con Google
                  </button>
                </form>
                <p className="mt-4 text-[11px] leading-relaxed text-slate-400">
                  Al crear tu cuenta aceptas los términos de la plataforma. Tu
                  tienda empieza en trial de 14 días.
                </p>
              </>
            )}
          </section>

          {/* Panel: Iniciar sesión */}
          <section
            aria-label="Iniciar sesión"
            className={`border border-slate-200 bg-white p-6 shadow-[8px_8px_0_0_#111318] ${
              showTab === "iniciar" ? "ring-2 ring-slate-950" : ""
            }`}
          >
            <p className="mono text-xs uppercase tracking-[0.18em] text-slate-500">
              Iniciar sesión
            </p>
            <h2 className="mt-2 text-xl font-semibold tracking-tight">
              Entra a tu cuenta
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-500">
              Usa tu cuenta de tienda (Google o correo y contraseña).
            </p>

            <form action={login} className="mt-5 space-y-4">
              <label className="block">
                <span className="mono text-[11px] uppercase tracking-[0.14em] text-slate-500">
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
                <span className="mono text-[11px] uppercase tracking-[0.14em] text-slate-500">
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

            <div className="my-5 flex items-center gap-3">
              <span className="h-px flex-1 bg-slate-200" />
              <span className="mono text-[10px] uppercase tracking-[0.2em] text-slate-400">
                o
              </span>
              <span className="h-px flex-1 bg-slate-200" />
            </div>

            <form action={loginWithGoogle}>
              <button
                className="w-full border border-slate-950 bg-white px-4 py-3 text-sm font-medium text-slate-950 transition-colors hover:bg-slate-950 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
                type="submit"
                disabled={!configured}
              >
                Continuar con Google
              </button>
            </form>
          </section>
        </div>

        <p className="mt-8 text-xs leading-relaxed text-slate-400">
          El storefront público no requiere login.{" "}
          <Link
            className="underline underline-offset-2"
            href={process.env.NEXT_PUBLIC_STOREFRONT_URL ?? "http://localhost:3000"}
          >
            Ir al storefront
          </Link>
        </p>
      </div>
    </main>
  );
}
