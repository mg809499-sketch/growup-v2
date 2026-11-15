// Fuentes compartidas por los root layouts de (site) y (preview).
// El "preview" del builder debe verse idéntico al storefront publicado,
// por eso ambas superficies usan las mismas variables de fuente.

import {
  Anton,
  Playfair_Display,
  Plus_Jakarta_Sans,
  Space_Grotesk,
  Space_Mono,
} from "next/font/google";

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

export const fontVariables = `${anton.variable} ${spaceGrotesk.variable} ${spaceMono.variable} ${playfair.variable} ${jakarta.variable}`;
