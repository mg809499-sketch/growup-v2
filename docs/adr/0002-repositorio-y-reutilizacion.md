# ADR-0002 — Repositorio y reutilización de `multitiendas`

- **Estado:** Aceptada
- **Fecha:** 2026-10-21
- **Decisores:** equipo de ingeniería
- **Relacionado con:** ADR-0001, D-05

## Contexto

`growup` nace con solo dos documentos. El proyecto hermano `multitiendas` contiene una implementación real de la V1: FastAPI con ~33 módulos, 18 archivos de test, 6 migraciones con RLS, dos storefronts Next.js y un admin mínimo. Empezar de cero implicaría reescribir tenant context, RLS, catálogo, inventario, checkout, facturación y gobernanza.

Al mismo tiempo, `multitiendas` tiene deudas que no se deben arrastrar: autenticación que decodifica el JWT sin verificar firma, política `tenants USING (true)` y dos apps con tenant hardcodeado.

## Decisión

- `growup` es el monorepo destino.
- `multitiendas` queda **congelado y en solo lectura**: se usa como referencia y donante. No se edita, no se mueve y no se le ejecutan operaciones de git desde este repositorio.
- La migración es **selectiva y con tests**: cada módulo que se copia llega con su test; si no lo tiene, se escribe antes del merge.
- Antes de copiar, se corrigen los dos defectos críticos: auth con verificación JWKS y política de `tenants` sin `USING (true)`.
- Los dos storefronts no se copian: se reemplazan por `apps/storefront` y theme presets.

## Alternativas consideradas

| Alternativa | Pros | Contras | ¿Por qué no? |
|---|---|---|---|
| A. Greenfield puro | Cero deuda heredada | Reescribe lo que ya funciona; retrasa meses | El costo no se justifica |
| B. Seguir en `multitiendas` | Sin migración | Mezcla V1 y V2; dos arquitecturas en un repo | El producto cambió |
| C. `growup` destino + port selectivo (elegida) | Conserva lo probado y limpia la deuda | Requiere disciplina de migración | Mejor relación valor/riesgo |

## Consecuencias

### Positivas

- Se conservan RLS, reservas anti-overselling, checkout, facturación y tests.
- La deuda crítica se corrige una sola vez, antes de portar.
- `multitiendas` sigue disponible como referencia sin riesgo de divergencia.

### Negativas / deuda asumida

- Hay que mantener dos repositorios durante la transición.
- El port requiere adaptar imports, configuración y esquemas.
- El historial de git de `multitiendas` no se traslada automáticamente.

### Neutras

- `multitiendas` se puede archivar cuando `growup` alcance paridad en el MVP.

## Cómo se verifica

- `growup` tiene tests RLS y de concurrencia equivalentes o mejores que `multitiendas`.
- Ningún archivo de `multitiendas` cambia durante la migración (`git status` limpio).
- Cada módulo portado tiene su test y su commit de origen documentado.

## Enlaces

- [Decisiones D-05](../decisiones-pendientes.md)
- [Prompt v0](../prompts/v0-storefront.md)
