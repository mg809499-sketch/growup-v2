import { logout } from "@/app/login/actions";
import { ConsoleShell } from "@/components/console-shell";
import { requireSession } from "@/lib/auth";
import { isDesignPreview } from "@/lib/design-preview";

export const dynamic = "force-dynamic";

export default async function DashboardLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const { user } = await requireSession();
  const preview = isDesignPreview();

  return (
    <ConsoleShell
      userEmail={user.email ?? user.id}
      preview={preview}
      logoutAction={logout}
    >
      {children}
    </ConsoleShell>
  );
}
