import { requireSession } from "@/lib/auth";
import { apiGetText } from "@/lib/api";

export const dynamic = "force-dynamic";

export async function GET() {
  const { token } = await requireSession();
  try {
    const csv = await apiGetText("/v1/platform/tenants/export.csv", token);
    return new Response(csv, {
      headers: {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": 'attachment; filename="tenants.csv"',
      },
    });
  } catch {
    return new Response("No se pudo exportar el directorio.", { status: 502 });
  }
}
