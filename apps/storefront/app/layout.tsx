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
import { getBootstrap, getStorefrontHost } from "@/lib/api";
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

export const metadata: Metadata = {
  title: "Growup",
  description: "Comercio editorial multi-tenant.",
};

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
        {bootstrap ? <SiteHeader tenant={bootstrap.tenant} /> : null}
        {children}
        {bootstrap ? <SiteFooter tenant={bootstrap.tenant} /> : null}
      </body>
    </html>
  );
}
