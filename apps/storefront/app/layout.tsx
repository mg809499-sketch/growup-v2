import type { Metadata } from "next";
import {
  Anton,
  Playfair_Display,
  Plus_Jakarta_Sans,
  Space_Grotesk,
  Space_Mono,
} from "next/font/google";

import "./globals.css";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { ApiError, getBootstrap, getStorefrontHost } from "@/lib/api";
import type { BootstrapResponse } from "@/lib/api";
import { defaultTheme } from "@/lib/format";

const anton = Anton({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-anton",
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space",
  display: "swap",
});

const spaceMono = Space_Mono({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-mono",
  display: "swap",
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  display: "swap",
});

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-jakarta",
  display: "swap",
});

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

  return (
    <html lang="es">
      <body
        className={`${anton.variable} ${spaceGrotesk.variable} ${spaceMono.variable} ${playfair.variable} ${jakarta.variable}`}
        data-theme={defaultTheme()}
      >
        {bootstrap ? (
          <>
            <SiteHeader tenant={bootstrap.tenant} />
            {children}
            <SiteFooter tenant={bootstrap.tenant} />
          </>
        ) : (
          <div className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center gap-4 p-8 text-center">
            <p className="label text-[var(--muted)]">growup</p>
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
