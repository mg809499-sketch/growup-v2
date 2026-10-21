# Reglas para agentes

## Contexto

`growup` es la plataforma SaaS multi-tenant de comercio (Cordiasolve V2): un storefront engine que renderiza layouts publicados por tenant y un admin con builder. Ropa y joyería son los dos tenants piloto, no dos aplicaciones separadas.

## Orden de lectura antes de tocar código

1. `docs/decisiones-pendientes.md` — si la tarea depende de una decisión abierta, **detente y pregunta**.
2. `docs/adr/` — decisiones de arquitectura aceptadas.
3. `.kiro/steering/` — reglas permanentes de producto, stack, gobernanza y seguridad.
4. `docs/prompts/v0-storefront.md` — dirección visual del storefront.
5. `docs/arquitectura-plataforma-inteligente-cordiasolve-v2.md` — documento base (legado, puede contener contradicciones).

## Reglas duras

- **`../multitiendas` es solo lectura.** Prohibido editar, mover, renombrar o ejecutar git allí. Solo se copia código hacia `growup`, con sus tests.
- **No asumir decisiones de negocio.** Si falta una respuesta, se consulta; no se inventa.
- **Aislamiento multi-tenant:** toda tabla de negocio lleva `tenant_id` y RLS forzado. Ninguna consulta puede omitir el filtro.
- **El backend no confía en `X-Tenant-ID`.** Valida `host → tenant` y el claim del JWT verificado por JWKS.
- **`service_role` solo para workers.** La API usa un rol sujeto a RLS.
- **Dinero en enteros (centavos), COP en el MVP.** Nunca `float`.
- **Builder con schemas cerrados.** No se permite HTML arbitrario en bloques.
- **Cada módulo llega con tests.** Sin test no hay merge.
- **Secretos solo en `.env` local o vault.** Nunca en el repositorio.
- **Sin librerías de UI en el storefront.** Prohibido shadcn, MUI, Chakra o similares; los componentes son propios.

## Comandos

```bash
# API
cd services/api
uv sync
uv run uvicorn app.main:app --reload
uv run ruff check .
uv run mypy app
uv run pytest

# Monorepo (cuando existan apps)
pnpm install
pnpm build
pnpm lint
pnpm typecheck
```

## Definition of Done

- Tests unitarios/integración pasan.
- `ruff` y `mypy` en verde.
- `tsc --noEmit` y `next build` en verde (frontend).
- Sin secretos ni PII en logs.
- Documentación o ADR actualizado si cambió una decisión.
- Si el cambio toca aislamiento de tenants, se ejecuta la skill `tenant-isolation-check`.
