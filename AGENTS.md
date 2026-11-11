# Reglas para agentes

## Contexto

`growup` es la plataforma SaaS multi-tenant de comercio (Cordiasolve V2): un storefront engine que renderiza layouts publicados por tenant y un admin con builder. Ropa y joyería son los dos tenants piloto, no dos aplicaciones separadas.

## Orden de lectura antes de tocar código

1. `docs/plan/README.md` — estado real del proyecto y trabajo pendiente por fases (auditoría 2026-11-10).
2. `docs/decisiones-pendientes.md` — si la tarea depende de una decisión abierta, **detente y pregunta**.
3. `docs/adr/` — decisiones de arquitectura.
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
uv sync                      # o: python -m uv sync
uv run uvicorn app.main:app --reload
uv run ruff check .
uv run mypy app
uv run pytest                # integración real si GROWUP_TEST_DATABASE_URL está configurada

# Monorepo
pnpm install
pnpm build
pnpm lint
pnpm typecheck
pnpm contracts:check         # debe fallar solo si openapi/schema.d.ts cambiaron legítimamente

# Datos demo y E2E
psql "$GROWUP_MIGRATION_URL" -f supabase/seed.demo.sql
pnpm --filter @growup/storefront test:e2e
```

## Definition of Done

- Tests unitarios/integración pasan.
- `ruff` y `mypy` en verde.
- `tsc --noEmit` y `next build` en verde (frontend).
- Sin secretos ni PII en logs.
- Documentación o ADR actualizado si cambió una decisión.
- Si el cambio toca aislamiento de tenants, ejecutar la skill de aislamiento o documentar en el PR las pruebas A/B realizadas.
- Si el cambio toca bloques/contenido, validar los schemas cerrados y el fallback de bloque desconocido.
- Si el cambio toca pagos/webhooks, verificar firma, idempotencia y que ningún PAN/CVV se loguea.

## Kiro

Steering y specs viven en `docs/` hasta que se cierre la migración del flujo de trabajo; no hay `.kiro/` en este repositorio. Ver `docs/plan/README.md` para el estado vigente.
