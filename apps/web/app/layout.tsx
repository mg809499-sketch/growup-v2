import type { Metadata, Viewport } from "next";
import { Anton, Space_Grotesk, Space_Mono } from "next/font/google";

import "./globals.css";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { site } from "@/content/site";

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

export const metadata: Metadata = {
  metadataBase: new URL(site.url),
  title: {
    default: "growup — la tiendita completa para marcas de ropa y joyería",
    template: "%s · growup",
  },
  description:
    "Storefront, builder de páginas, catálogo, inventario, pagos Wompi y facturación DIAN para marcas de ropa y joyería en Colombia. Piloto Q1 2027.",
  openGraph: {
    type: "website",
    locale: "es_CO",
    siteName: "growup",
  },
};

export const viewport: Viewport = {
  themeColor: "#f4f3ee",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es-CO" className={`${anton.variable} ${spaceGrotesk.variable} ${spaceMono.variable}`}>
      <body>
        <a
          href="#contenido"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:bg-[var(--ink)] focus:px-4 focus:py-2 focus:text-[var(--surface)]"
        >
          Saltar al contenido
        </a>
        <SiteHeader />
        <main id="contenido">{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
