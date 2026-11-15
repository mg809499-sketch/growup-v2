// Override de host para la ruta /preview del builder (solo SSR).
//
// El token de previsualización identifica el tenant dueño del borrador, pero
// el host del request (p. ej. localhost:3000 en desarrollo) no tiene por qué
// existir en app.domains ni corresponder a ese tenant. En lugar de acoplar
// el preview al Host/env del request, la página /preview fija este override
// a partir del `host` que devuelve el API y todos los fetches posteriores
// (bootstrap, productos) resuelven el tenant correcto.
//
// `cache()` de React memoiza por request: nunca se comparte entre requests.
import { cache } from "react";

const scope = cache(() => ({ host: null as string | null }));

export function setPreviewHost(host: string | null): void {
  scope().host = host;
}

export function getPreviewTenantHost(): string | null {
  return scope().host;
}
