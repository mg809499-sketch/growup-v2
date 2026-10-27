# Reparto de trabajo — Growup

> **Cómo usar este archivo:** cuando tu compañero haga `pull` y abra OpenCode, debe pedirle:
> “Lee `AGENTS.md` y `docs/reparto-trabajo.md`, y empieza por la tarea `B-01`.”
>
> **Estado del documento:** 2026-10-26 · 2 personas · repositorio `growup`.

---

## 1. Resumen del proyecto

Growup es un SaaS multi-tenant de comercio electrónico con:

- **Storefront** público (`apps/storefront`): resuelve tenant por host y renderiza catálogo desde FastAPI.
- **Admin** privado (`apps/admin`): backoffice con login Supabase.
- **API** FastAPI (`services/api`) con RLS forzado en Postgres.
- **Base de datos** Supabase (`supabase/`).
- **Contratos** OpenAPI → TypeScript (`packages/contracts`).

Ya está implementado:

- Catálogo, variantes, inventario, reservas.
- Media con R2/MinIO, variantes AVIF/WebP y E2E con `moto`.
- Gobernanza, auditoría y cadena de hashes.
- Platform admin con listado de tenants.
- Storefront con home, colección y PDP.
- Admin con login, resumen, catálogo, media, auditoría y tenants.
- CI con API, pgTAP, contratos y frontends.

---

## 2. Reglas duras (leer antes de empezar)

1. **No tocar `../multitiendas`.** Es solo lectura.
2. **No asumir decisiones de negocio.** Si falta información, se pregunta.
3. **Aislamiento multi-tenant:** toda tabla de negocio lleva `tenant_id` y RLS forzado.
4. **Dinero en centavos (`int`), COP, nunca `float`.**
5. **Sin HTML arbitrario en bloques del builder.**
6. **Sin test no hay merge.**
7. **Secretos solo en `.env` local o vault.** Nunca en el repositorio.
8. **Sin librerías de UI** (shadcn, MUI, Chakra). Componentes propios.
9. Si tocas tenancy, usa la skill `tenant-isolation-check`.
10. Si tocas bloques/contenido, usa `block-review`.
11. Si tocas pagos/webhooks, usa `payment-webhook-review`.

---

## 3. Setup del entorno

```bash
pnpm install

# Base de datos local
pnpm dlx supabase start
pnpm dlx supabase db reset

# API
cd services/api
uv sync
$env:GROWUP_DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
uv run uvicorn app.main:app --reload

# Storefront (otra terminal)
pnpm --filter @growup/storefront dev

# Admin (otra terminal)
cp apps/admin/.env.example apps/admin/.env.local
pnpm --filter @growup/admin dev
```

### Tests y calidad

```bash
cd services/api
uv run ruff check .
uv run mypy app
uv run pytest

# pgTAP
pnpm dlx supabase db reset
pnpm dlx supabase test db

# Frontend
pnpm typecheck
pnpm lint
pnpm build

# Contratos
pnpm contracts:check
```

---

## 4. Reparto por persona

### Persona A — dueño del repo (tú)

Trabajas conmigo en el admin y en decisiones de producto.

**Tus tareas:**

| ID | Tarea | Estado |
|---|---|---|
| A-01 | CRUD de productos, variantes y media en el admin | Hecho |
| A-02 | Login admin local con signing keys ES256 y usuarios staff | Pendiente |
| A-03 | Integrar export visual de v0 cuando llegue | Pendiente |
| A-04 | Cerrar decisiones de negocio con abogado/contador | Pendiente |

### Persona B — compañero

Empieza por `B-01` y sigue en orden.

| ID | Tarea | Estado | Rama sugerida |
|---|---|---|---|
| B-01 | Seed/demo de dos tenants | Pendiente | `feat/seed-demo` |
| B-02 | Playwright E2E del storefront | Pendiente | `test/e2e-storefront` |
| B-03 | CI y seguridad | Pendiente | `chore/ci-security` |
| B-04 | Observabilidad con OTel | Pendiente | `feat/otel` |
| B-05 | Spike de email transaccional | Pendiente | `spike/email` |
| B-06 | Spike de Wompi | Bloqueado por cuenta | `spike/wompi` |
| B-07 | Export visual de v0 | Bloqueado por v0 | `feat/v0-export` |

---

## 5. Detalle de tareas de Persona B

### B-01 — Seed/demo de dos tenants

**Objetivo:** dejar datos demo reproducibles para `ropa` y `joyería` sin romper pgTAP.

**Importante:** no uses `supabase/seed.sql` si eso hace que `db reset` aplique datos globales, porque los tests pgTAP cuentan tenants y fallarían. Mejor crea un seed manual o script:

- `supabase/seed.demo.sql`, o
- `services/api/scripts/seed_demo.py`.

**Debe crear:**

- Tenant `ropa` con host `ropa.growup.com`.
- Tenant `joyeria` con host `joyeria.growup.com`.
- Categorías: 3 por tenant.
- Productos: 6 por tenant.
- Variantes: 2 por producto.
- Estado `active`.
- Precios en centavos.
- Sin media al inicio.

**Criterio de listo:**

1. El seed se ejecuta manualmente con un comando documentado.
2. `pnpm dlx supabase db reset` + seed deja las dos tiendas navegables.
3. `pnpm dlx supabase test db` sigue en verde.
4. No hay secretos ni PII.
5. El comando está en el README.

---

### B-02 — Playwright E2E del storefront

**Objetivo:** automatizar el flujo público del storefront.

**Depende de:** B-01.

**Tests mínimos:**

1. Home carga el nombre del tenant.
2. Colección muestra productos.
3. PDP muestra variantes y precio.
4. Producto inexistente devuelve 404.
5. Imágenes tienen `alt`.
6. Host incorrecto no muestra datos de otro tenant.
7. Axe no reporta errores críticos.

**Sugerencia técnica:**

- Crear `apps/storefront/playwright.config.ts`.
- Tests en `apps/storefront/e2e/`.
- Script `test:e2e`.
- Correr contra API local y seed demo.

**Criterio de listo:**

1. `pnpm --filter @growup/storefront test:e2e` pasa en local.
2. No depende de datos de producción.
3. `pnpm build` sigue en verde.
4. Evidencia en el PR.

---

### B-03 — CI y seguridad

**Objetivo:** endurecer el pipeline y preparar la postura SOC 2-ready.

**Tareas:**

1. Añadir `pip-audit` al job de API.
2. Añadir `pnpm audit --prod` al job de frontend.
3. Añadir Trivy o equivalente para imagen Docker.
4. Activar secret scanning en GitHub.
5. Proteger `main`: PR obligatorio, checks obligatorios.
6. Añadir `CODEOWNERS` si aplica.
7. Plantilla de PR con evidencia.

**Criterio de listo:**

1. CI en verde.
2. Ningún secreto en el repo.
3. Documentación actualizada.
4. Si se rompe algo, se arregla antes de merge.

---

### B-04 — Observabilidad con OTel

**Objetivo:** trazas distribuidas con `tenant_id` y `trace_id`.

**Tareas:**

1. Instrumentar FastAPI.
2. Instrumentar Next.js.
3. Propagar `trace_id` entre storefront → API.
4. Enviar a Sentry u otro backend.
5. Añadir alertas de 5xx y latencia.
6. Verificar que no haya PII en logs.

**Criterio de listo:**

1. Un request del storefront se ve completo en una traza.
2. Los logs tienen `tenant_id` y `trace_id`.
3. `ruff` y `mypy` siguen en verde.
4. No hay secretos en logs.

---

### B-05 — Spike de email transaccional

**Objetivo:** elegir proveedor y validar el modelo de dominio por tenant.

**Comparar:**

- Resend.
- Postmark.

**Verificar:**

1. Soporte de dominio/subdominio por tenant.
2. DKIM/SPF/DMARC.
3. Webhooks de rebote y queja.
4. API para verificar dominios automáticamente.
5. Región de envío.
6. Precios.
7. Compatibilidad con Supabase Auth SMTP.

**Entregable:** `docs/spikes/email.md` con recomendación y evidencia.

---

### B-06 — Spike de Wompi

**Bloqueado hasta tener cuenta sandbox.**

Cuando exista la cuenta, verificar:

1. Redirect vs widget.
2. Dominios exactos para CSP.
3. 3DS.
4. Campos de riesgo.
5. Webhooks firmados.
6. Idempotencia.
7. Tarifas.

**Entregable:** `docs/spikes/wompi.md`.

---

### B-07 — Export visual de v0

**Bloqueado hasta tener el export.**

Cuando llegue:

1. Revisar tokens y componentes.
2. Integrar en `apps/storefront`.
3. Mantener RSC y `next/image`.
4. Validar LCP móvil < 2.5 s.
5. Validar axe.

---

## 6. Qué NO tocar todavía

1. **Checkout real:** Wompi no existe y falta cerrar IVA del envío.
2. **Builder/publishing:** ADR-0005 sigue en Propuesta.
3. **DPA/DSR en base de datos:** D-09 y D-10 siguen abiertas.
4. **Suspensión de tenants:** falta definir el efecto en storefront.
5. **Edición del admin:** la está trabajando Persona A; evitar conflicto.

---

## 7. Definition of Done general

- [ ] Tests unitarios/integración pasan.
- [ ] `ruff` y `mypy` en verde.
- [ ] `tsc --noEmit` y `next build` en verde si tocas frontend.
- [ ] Sin secretos ni PII en logs.
- [ ] Documentación o ADR actualizado si cambió una decisión.
- [ ] Si tocas tenancy, ejecutaste `tenant-isolation-check`.
- [ ] Si tocas bloques, ejecutaste `block-review`.
- [ ] Si tocas pagos/webhooks, ejecutaste `payment-webhook-review`.

---

## 8. Flujo de trabajo sugerido

1. `git checkout main && git pull`.
2. Crear rama desde `main`.
3. Trabajar solo en tu tarea.
4. PR pequeño, con evidencia.
5. No editar `tasks.md` si no cierras la tarea.
6. Si hay conflicto con otra persona, coordinar antes de push.

---

## 9. Prompt para OpenCode (Persona B)

Cuando tu compañero abra OpenCode después del pull, puede pegar esto:

```text
Lee AGENTS.md y docs/reparto-trabajo.md.
Trabaja solo en la tarea B-01.
Crea la rama feat/seed-demo.
No toques apps/admin ni ../multitiendas.
Cumple el Definition of Done del documento.
```

Después de B-01, cambia `B-01` por `B-02`, y así.

---

## 10. Estado de decisiones

- **Cerradas:** D-01 a D-08, D-17, D-18.
- **En propuesta:** D-09 a D-16.
- **Bloqueos externos:**
  - Cuenta Wompi.
  - Export de v0.
  - Revisión legal.
  - Contador para IVA del envío.
