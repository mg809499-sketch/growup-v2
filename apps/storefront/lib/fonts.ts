// Fuentes compartidas por los root layouts de (site) y (preview).
// Se cargan selectivamente por preset activo (C-3 / ADR-0020):
// - nova: Unbounded + Geist + Geist Mono
// - ropa: Anton + Space Grotesk + Space Mono
// - joyeria: Playfair Display + Plus Jakarta Sans

import {
  Anton,
  Geist,
  Geist_Mono,
  Playfair_Display,
  Plus_Jakarta_Sans,
  Space_Grotesk,
  Space_Mono,
  Unbounded,
} from "next/font/google";

import type { ThemePreset } from "@growup/config";

export const unbounded = Unbounded({
  subsets: ["latin", "latin-ext"],
  variable: "--font-unbounded",
  display: "swap",
});

export const geist = Geist({
  subsets: ["latin", "latin-ext"],
  variable: "--font-geist",
  display: "swap",
});

export const geistMono = Geist_Mono({
  subsets: ["latin", "latin-ext"],
  variable: "--font-geist-mono",
  display: "swap",
});

export const anton = Anton({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-anton",
  display: "swap",
});

export const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space",
  display: "swap",
});

export const spaceMono = Space_Mono({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-mono",
  display: "swap",
});

export const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  display: "swap",
});

export const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-jakarta",
  display: "swap",
});

export function fontVariablesForTheme(theme: ThemePreset): string {
  switch (theme) {
    case "ropa":
      return `${anton.variable} ${spaceGrotesk.variable} ${spaceMono.variable}`;
    case "joyeria":
      return `${playfair.variable} ${jakarta.variable}`;
    case "nova":
    default:
      return `${unbounded.variable} ${geist.variable} ${geistMono.variable}`;
  }
}

export const fontVariables = fontVariablesForTheme("nova");
