import type { Metadata } from "next";

import "../globals.css";
import { defaultTheme } from "@/lib/format";
import { fontVariablesForTheme } from "@/lib/fonts";

export const metadata: Metadata = {
  // El <title> del admin/isPreview es gestionado por la propia página; aquí
  // solo un hint neutro para crawlers si alguien abre la URL directamente.
  title: "Growup preview",
  robots: { index: false, follow: false },
};

/**
 * Root layout de la vista previa del builder (/preview).
 *
 * Deliberadamente NO resuelve el tenant ni pinta el SiteHeader/SiteFooter:
 * el borrador que se previsualiza pertenece al tenant dueño del token, no al
 * host del request (que puede ser localhost:3000 en desarrollo). Así el
 * preview siempre monta, aunque el host no exista en app.domains; el tenant
 * correcto lo fija la página vía `setPreviewHost()` a partir del `host` que
 * devuelve el API con el token.
 */
export default function PreviewLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const theme = defaultTheme();
  return (
    <html lang="es-CO" data-theme={theme}>
      <body className={fontVariablesForTheme(theme)} data-theme={theme}>
        {children}
      </body>
    </html>
  );
}
