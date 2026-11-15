import type { Metadata } from "next";
import { Geist, Geist_Mono, Unbounded } from "next/font/google";

import "./globals.css";

const unbounded = Unbounded({
  subsets: ["latin", "latin-ext"],
  variable: "--font-display",
  display: "swap",
});

const geist = Geist({
  subsets: ["latin", "latin-ext"],
  variable: "--font-body",
  display: "swap",
});

const geistMono = Geist_Mono({
  subsets: ["latin", "latin-ext"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Growup — Consolas Staff & Cliente",
  description: "Consola Staff All-in-One y Consola Cliente Owner con Store Builder v3.0.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es-CO" className={`${unbounded.variable} ${geist.variable} ${geistMono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
