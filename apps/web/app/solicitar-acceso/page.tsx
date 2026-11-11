import { permanentRedirect } from "next/navigation";

import { site } from "@/content/site";

// Esta ruta se conservaba solo por enlaces históricos; ahora redirige al login.
export default function SolicitarAccesoRedirect() {
  permanentRedirect(site.admin_login_url);
}
