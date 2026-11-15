# ADR-0020 — Dirección visual Nova (Sistema Técnico Total)

- **Estado:** Aceptada (decisiones del usuario DU-01 a DU-06, 2026-11-15)
- **Fecha:** 2026-11-15
- **Decisores:** producto, diseño e ingeniería
- **Relacionado con:** ADR-0001, ADR-0005, ADR-0010, `docs/plan/suite-publica-growup.md` (DEC-2 reabierta)

## Contexto

Growup nació con dos presets iniciales en el storefront (`ropa` — *Sol de Calle* y `joyeria` — *Aurélia Atelier*) y adoptó la dirección editorial v0 para la suite pública (`apps/web`). Para diferenciar la plataforma con una identidad visual propia, contemporánea y de alta precisión técnica en todas sus superficies (`apps/web`, `apps/admin` y el motor `apps/storefront`), se define el sistema visual **Nova**.

Al mismo tiempo, el sistema debe respetar las restricciones duras de seguridad y rendimiento del proyecto:

- **Cero librerías externas de UI** en el storefront (`AGENTS.md`).
- **PCI-DSS v4.0.1 SAQ A** en checkout: cero scripts o hojas de estilo de terceros (`ADR-0010`).
- **Fuentes self-hosted** vía `next/font/google` (sin peticiones en tiempo de ejecución a `fonts.googleapis.com`).
- **Accesibilidad WCAG AA** y presupuesto de Core Web Vitals (`LCP < 2.5s`, `CLS < 0.1`, `INP < 200ms`).

## Decisión

### 1. Definición operativa y alcance (DU-01, DU-04, DU-06)

Nova es el sistema visual **Técnico Total** de Growup y se aplica en tres superficies:

1. **Sitio público (`apps/web` — `growup.com`):** identidad principal de la plataforma (reabre y actualiza `DEC-2`).
2. **Consola administrativa y Super Consola (`apps/admin`):** shell oscuro técnico, barra de comando, telemetría operativa y builder v2.
3. **Motor de Storefront (`apps/storefront`):** preset `nova` en el registro de temas (`ThemeTokensV1`), activo por defecto cuando el tenant selecciona `nova` (o como preset principal de plataforma), conservando `ropa` y `joyeria` como presets disponibles para reversión inmediata.

### 2. Tipografía oficial (Opción A — DU-03)

Se registran tres familias en el catálogo cerrado de fuentes (`FONT_REGISTRY`), servidas vía `next/font/google` con subsets `latin` y `latin-ext` y `display: swap`:

| Rol | Familia | Variable CSS | Ejes / Pesos | Uso |
|---|---|---|---|---|
| **Display** | `Unbounded` | `--font-unbounded` | `200..900` | Titulares de alto impacto, métricas primarias y cabeceras de sección. Tracking `-0.03em`, line-height `0.92–1.02`. |
| **Cuerpo / UI** | `Geist` | `--font-geist` | `100..900` | Cuerpo de lectura (`>= 16px`), controles de interfaz, tablas y formularios. |
| **Datos / Telemetría** | `Geist Mono` | `--font-geist-mono` | `100..900` | Precios tabulares COP, SKUs, coordenadas, índices `[01]`, badges técnicos, hashes de auditoría y versiones. |

### 3. Sistema de color en `oklch()` con soporte `light-dark()`

El tema `nova` es **oscuro por defecto (`color-scheme: dark`)** con soporte para modo claro:

- `--surface`: `oklch(0.155 0.012 265)` (fondo primario abisal)
- `--surface-2`: `oklch(0.205 0.015 265)` (superficie elevada / placas técnicas)
- `--surface-3`: `oklch(0.245 0.018 265)` (controles interactivos / hover)
- `--ink`: `oklch(0.975 0.004 265)` (texto primario de alto contraste)
- `--muted`: `oklch(0.76 0.015 265)` (texto secundario, contraste AA verificado sobre `--surface` y `--surface-2`)
- `--hairline`: `oklch(0.34 0.015 265)` (estructura de rejilla de `1px`)
- `--signal`: `oklch(0.88 0.19 128)` (acento volt/lima cibernético; texto sobre `--signal` usa `--surface` oscuro `oklch(0.155 0.012 265)`, nunca blanco)
- `--signal-glow`: `oklch(0.88 0.19 128 / 0.24)` (resplandor estático acotado)

### 4. Excepciones cerradas frente a `design-taste-frontend` (DU-02)

Para habilitar la estética **Técnico Total** de forma controlada, se autorizan exclusivamente estas 11 excepciones:

1. **Monoespaciado (`Geist Mono`)** en metadatos, precios, SKUs, tallas, telemetría y etiquetas técnicas (nunca en párrafos de lectura).
2. **Índices y códigos visuales** (`01`, `02`, `SYS.26`, coordenadas); cuando son decorativos llevan `aria-hidden="true"`.
3. **Líneas finas (`1px`) y rejillas estructurales** visibles en secciones, tablas, placas de datos y formularios.
4. **Brillo de acento estático (`--signal-glow`)** en hasta dos elementos por pantalla (CTA primario y estado activo). Nunca se anima `box-shadow`.
5. **Recortes angulares (`clip-path`)** de `8px–12px` en botones primarios, tarjetas destacadas y placas técnicas, con anillo de foco interno para que `clip-path` no recorte el indicador de teclado.
6. **Gradientes sutiles de campo** en fondos de sección (`radial-gradient` / `linear-gradient` sobre `--surface`), siempre que el texto mantenga contraste WCAG AA.
7. **`backdrop-filter: blur(12px)`** restringido al encabezado sticky y a un modal activo (máximo 2 capas por vista).
8. **Titulares de hasta 3 líneas** en escritorio y 2 en móvil, con `text-wrap: balance` y sin desbordamiento horizontal.
9. **Retícula o scanlines decorativas** estáticas en CSS puro (`aria-hidden`, `pointer-events: none`, cero impacto en LCP).
10. **Etiquetas técnicas de `11px–12px`** solo para metadatos secundarios; todo cuerpo informativo mide `>= 16px`.
11. **Un movimiento de firma por vista** basado únicamente en `transform` y `opacity`, desactivado bajo `prefers-reduced-motion: reduce`.

### 5. Límites no negociables

- **WCAG AA:** contraste `>= 4.5:1` en texto normal y `>= 3:1` en texto grande y bordes funcionales.
- **Teclado y foco:** `:focus-visible` evidente en cada control interactivo; objetivos táctiles `>= 24x24px`.
- **Presupuesto de rendimiento:** `LCP < 2.5s`, `CLS < 0.1`, `INP < 200ms`.
- **Seguridad de checkout (SAQ A):** ninguna fuente externa ni script de terceros en rutas de pago.
- **Honestidad de contenido (DEC-3, DEC-5, DEC-6):** en `apps/web` no se publican precios numéricos hasta ratificar `D-01` ni enlaces a la super consola interna.

## Consecuencias

### Positivas

- Coherencia visual moderna y diferenciada entre `growup.com`, el backoffice `apps/admin` y el preset `nova` de `apps/storefront`.
- Selección de tema por tenant (`bootstrap.theme`) y esquema tipado `ThemeTokensV1` que elimina el acoplamiento a `GROWUP_DEFAULT_THEME`.
- Reversión instantánea a los presets `ropa` y `joyeria` mediante datos (`app.themes.tokens`), sin redespliegue.

### Negativas / deuda asumida

- El catálogo de fuentes de `next/font/google` suma las tres variables de Nova (`--font-unbounded`, `--font-geist`, `--font-geist-mono`).
- Los componentes con `clip-path` deben usar bordes/sombras internas en `:focus-visible` para no cortar el foco de accesibilidad.
