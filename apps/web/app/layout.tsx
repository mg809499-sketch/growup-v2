import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono, Unbounded } from "next/font/google";

import "./globals.css";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { site } from "@/content/site";

const unbounded = Unbounded({
  subsets: ["latin", "latin-ext"],
  variable: "--font-unbounded",
  display: "swap",
});

const geist = Geist({
  subsets: ["latin", "latin-ext"],
  variable: "--font-geist",
  display: "swap",
});

const geistMono = Geist_Mono({
  subsets: ["latin", "latin-ext"],
  variable: "--font-geist-mono",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(site.url),
  title: {
    default: "growup — infraestructura de comercio multi-tenant para ropa y joyería",
    template: "%s · growup",
  },
  description:
    "Storefront engine, builder de páginas, catálogo, inventario atómico, pagos Wompi y facturación DIAN para marcas de ropa y joyería en Colombia. Piloto Q1 2027.",
  openGraph: {
    type: "website",
    locale: "es_CO",
    siteName: "growup",
  },
};

export const viewport: Viewport = {
  themeColor: "#0d0f17",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="es-CO"
      data-theme="nova"
      className={`${unbounded.variable} ${geist.variable} ${geistMono.variable}`}
    >
      <body data-theme="nova">
        <a
          href="#contenido"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:bg-[var(--signal)] focus:px-4 focus:py-2 focus:text-[var(--signal-ink)]"
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
