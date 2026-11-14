import { PageHeader } from "@/components/page-header";
import { PlanCard } from "@/components/plan-card";
import { requireSession } from "@/lib/auth";
import { apiGetSafe } from "@/lib/api";
import type { PlanOut } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function PlanesPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { token } = await requireSession();
  const { error } = await searchParams;
  const result = await apiGetSafe<PlanOut[]>("/v1/platform/plans", token);
  const plans = result.redirectToLogin ? [] : (result.data ?? []);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Plataforma"
        title="Planes de la plataforma"
        description="Catálogo de planes de suscripción Growup. El staff de operaciones edita precio, trial y orden de aparición."
      />

      {error ? (
        <p className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </p>
      ) : null}

      {result.error ? (
        <p className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          No se pudo cargar el catálogo. Revisa que la API esté disponible.
        </p>
      ) : (
        <div className="space-y-4">
          {plans.map((plan) => (
            <PlanCard key={plan.id} plan={plan} />
          ))}
          {plans.length === 0 ? (
            <p className="text-sm text-slate-500">
              Aún no hay planes cargados. Seed de `plans` con `starter` y `pro` está
              preparado (ver `supabase/seed.sql`).
            </p>
          ) : null}
        </div>
      )}
    </div>
  );
}
