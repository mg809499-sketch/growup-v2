import type { CSSProperties } from "react";
import type { Metadata } from "next";

import "../globals.css";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { ApiError, getBootstrap, getStorefrontHost } from "@/lib/api";
import type { BootstrapResponse } from "@/lib/api";
import { resolveStorefrontStyle, resolveStorefrontTheme } from "@/lib/format";
import { fontVariablesForTheme } from "@/lib/fonts";

export async function generateMetadata(): Promise<Metadata> {
  const host = await getStorefrontHost();
  try {
    const { tenant } = await getBootstrap(host);
    return {
      title: tenant.name,
      description: `Descubre el catálogo y las novedades de ${tenant.name}.`,
    };
  } catch (error) {
    if (error instanceof ApiError) {
      return {
        title: "Growup",
        description: "Tienda online de cada marca en Growup.",
      };
    }
    throw error;
  }
}

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const host = await getStorefrontHost();

  let bootstrap: BootstrapResponse | null = null;
  try {
    bootstrap = await getBootstrap(host);
  } catch {
    bootstrap = null;
  }

  const theme = resolveStorefrontTheme(bootstrap);
  const themeStyle = resolveStorefrontStyle(bootstrap) as CSSProperties;

  return (
    <html lang="es-CO" data-theme={theme}>
      <body
        className={fontVariablesForTheme(theme)}
        data-theme={theme}
        style={themeStyle}
      >
        {bootstrap ? (
          <>
            <SiteHeader tenant={bootstrap.tenant} />
            {children}
            <SiteFooter tenant={bootstrap.tenant} />
          </>
        ) : (
          <div className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center gap-4 p-8 text-center">
            <p className="label text-[var(--muted)]">growup // nova.os</p>
            <h1 className="display text-3xl">Tienda en configuración</h1>
            <p className="text-[var(--muted)]">
              Esta tienda aún no está publicada o está suspendida. Escríbenos a{" "}
              <a className="underline" href="mailto:soporte@growup.com">
                soporte@growup.com
              </a>
              .
            </p>
          </div>
        )}
      </body>
    </html>
  );
}
