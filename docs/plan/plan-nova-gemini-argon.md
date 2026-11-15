# Plan de ejecución: Growup Nova y ruta completa

**Constructor:** `opencode-go/gemini-4-argon` (variantes low, medium, high) · **Revisores:** aprobados (DU-05)
**Fecha:** 2026-11-14 · **Versión:** 4 (H-10 eliminado por decisión del usuario; Nova en tiendas desde ya)
**Estado:** listo para ejecutar con un agente de construcción. No ejecutado. No modifica decisiones (D-xx) ni ADR aceptados sin el registro de WP-04. Las decisiones DU-xx son del usuario.
**Origen:** la conversación (paridad por capacidades, hoja de ruta por gates, agenda legal, prioridades post-piloto) más la dirección visual Nova.

---

## 0. Decisiones del usuario (2026-11-14)

| ID | Decisión | Consecuencia en el plan |
|---|---|---|
| DU-01 | Nova se aplica al storefront y a la plataforma (growup.com y admin) | Incluye WP-30 y WP-31. Reabre DEC-2 (gate H-03) |
| DU-02 | Nivel de futurismo: técnico total, con los límites no negociables de la sección 6.2 | Excepciones ampliadas en ADR-0020. Los medidores pasan `--allow` solo para esas excepciones |
| DU-03 | Tipografía: Opción A (Unbounded, Geist y Geist Mono) | WP-22 y WP-23 usan esta pareja. Bricolage Grotesque y Funnel quedan descartadas |
| DU-04 | Nova se aplica desde ya: growup.com, admin, preset del storefront y tiendas de comerciantes | Adelanta los bloques 2 y 3 del calendario |
| DU-05 | Modelos de revisión aprobados: arquitecto, auditor, juez y redacción | La sección 5 queda activa y los subagentes se lanzan con esos IDs |
| DU-06 | Se elimina el gate de consentimiento de comerciantes (H-10). Nova se aplica también a sus tiendas. Para la plataforma, el principio "tema propio" de DEC-2 queda superado; esto resuelve H-11 con alcance de toda la plataforma | WP-04 registra el cambio y el texto nuevo de DEC-2. WP-54 se elimina. Se mantienen la reversión a v0 y el orden staging → producción |

### 0.1 Qué se aplica ya

| Superficie | Nova desde ya | Requisito |
|---|---|---|
| growup.com (`apps/web`) | Sí | H-03 registrado en WP-04 y revisión del prototipo (H-02) |
| Admin | Sí: primero en staging y después en producción, con aviso a los usuarios | H-02 y H-03. Sin cambios de flujos ni de permisos |
| Preset `nova` del storefront | Sí, en staging | WP-02 y WP-03 antes de publicar en cualquier tienda |
| Tiendas de comerciantes (ropa y joyería) | Sí, en el orden staging → producción | WP-02, WP-03 y WP-26 aprobados en staging. Reversión a v0 disponible |

DU-06 supera para la plataforma el principio de DEC-2 "la tienda de cada tenant sigue con su tema propio". WP-04 lo registra en `docs/decisiones-pendientes.md` con fecha y responsable, según el protocolo del repo, y redacta el texto nuevo de DEC-2. Lo que no cambia: nombre, logo, copy, productos, precios y datos de cada comerciante. Los presets v0 se conservan como reversión.

## 1. Alcance y resultado esperado

**Incluido**
- Piloto ropa y joyería: plan maestro F0 a F6, referenciado por IDs (no duplicado).
- Nivel 2 del comerciante: analítica básica, dominio propio, API y webhooks públicos, descuentos, devoluciones automatizadas, más sus prerequisitos.
- Frontend Nova en growup.com, en el admin y en el storefront (DU-01, DU-04, DU-06).
- Mejoras propuestas para el builder (WP-28).

**Excluido**
- Nivel 3 y 4: multi-moneda e impuestos multi-país, SDK de temas, apps de terceros, POS, B2B, pagos como facilitador, financiación, identidad de comprador compartida entre tiendas.
- Cualquier réplica de código, UI, textos, assets o implementación interna de Shopify.
- Cambios de nombre, logo, copy, productos, precios o datos de los comerciantes.

**Resultado esperado**
1. growup.com y el admin en Nova.
2. Preset `nova` aplicado al storefront de ropa y joyería, con reversión a v0 disponible.
3. Piloto con dos tiendas públicas, compra sandbox de extremo a extremo y aislamiento host A/B demostrado.
4. Las cinco capacidades del nivel 2 entregadas en su orden de dependencias.
5. Evidencia de cumplimiento actualizada en `docs/compliance/`.

## 2. Reglas para el constructor (no negociables)

1. Lee `AGENTS.md` y el WP antes de tocar código. Si el WP contradice `AGENTS.md` o un ADR aceptado, detente y pregunta.
2. No tomes decisiones de negocio ni cambies el estado de ninguna D-xx. Si falta información, usa la skill `clarify`: las decisiones de negocio van a `docs/decisiones-pendientes.md` y las técnicas a `docs/adr/`.
3. No toques `../multitiendas` (solo lectura). No leas, crees ni pegues `.env`, secretos ni credenciales.
4. Shopify: no uses material no público, no copies código, UI, textos, iconos ni assets. Dawn y Polaris no se usan: sus licencias los limitan a integraciones con Shopify.
5. Storefront: sin librerías de UI; sin scripts ni estilos de terceros en checkout; fuentes self-hosted vía `next/font`.
6. Multi-tenant: toda tabla de negocio lleva `tenant_id` con RLS `ENABLE` + `FORCE`. Todo cambio que toque tenants trae prueba A/B.
7. Dinero en enteros (centavos), COP en el MVP. Nunca float.
8. Bloques con schemas cerrados. Un bloque desconocido se muestra con fallback y se registra.
9. Cada módulo llega con tests. Sin tests no hay merge.
10. Commits por unidad de trabajo (skill `work-unit-commits`). PR de 400 líneas o menos cuando sea posible; si no, dividir.
11. Entrega: lista de archivos cambiados, comandos ejecutados con su salida real, riesgos y preguntas abiertas.
12. Nunca declares algo verificado sin haber ejecutado el comando que lo verifica.
13. Modelos gratuitos: no los uses con código de pagos, RLS, datos reales ni volcados de base de datos. Asume que pueden conservar los prompts.
14. Las tiendas de comerciantes reciben Nova en el orden staging → producción, con el preset v0 disponible como reversión en todo momento. Nombre, logo, copy, productos, precios y datos no cambian en el proceso.

## 3. Gates humanos

| Gate | Qué decide o hace | Quién | Estado | Desbloquea |
|---|---|---|---|---|
| H-01 | Aprobar la reconciliación documental (WP-01), el registro de decisiones (WP-04) y el enfoque "paridad por capacidades" | Producto | Pendiente | WP-01 y el resto |
| H-02 | Revisar el prototipo (WP-21) y aprobar ADR-0020 | Producto y diseño | Dirección decidida (DU-02 y DU-03). Falta revisar el prototipo | WP-22 a WP-27 y WP-30 |
| H-03 | Reabrir DEC-2 para growup.com y el admin | Producto | Decidido en DU-01. Falta registrar la reapertura en WP-04 | WP-30 y WP-31 |
| H-04 | Abogado: marca, código portado, diseño limpio; D-09 a D-13 | Abogado | Pendiente | Publicación legal, WP-46 y WP-52 |
| H-05 | Contador: IVA del envío, redondeo y zonas (derivados de D-06) | Contador | Pendiente | WP-45 (descuentos) |
| H-06 | Crear cuentas y guardar credenciales en vault o `.env` local: Wompi, Stripe, Factus sandbox, Resend, Cloudflare, Supabase, Fly, Vercel, Sentry | Humano | Pendiente | WP-12, WP-41, WP-47, F1 |
| H-07 | Aprobar vistas previas del piloto (F6-02, ahora con Nova) y criterios de aceptación (F6-05) | Comerciantes piloto y producto | Pendiente | F6 |
| H-08 | Go/no-go del piloto | Producto | Pendiente | Nivel 2 |
| H-09 | Desplegar a producción, DNS y on-call | Humano | Pendiente | Go-live |

H-10 (consentimiento de comerciantes) se eliminó por decisión del usuario (DU-06). H-11 queda resuelto por DU-06 con alcance de toda la plataforma.

Gemini no puede firmar, aceptar términos, crear cuentas, poner credenciales, ejecutar migraciones contra producción, cambiar DNS ni publicar en producción. Eso lo hace una persona.

## 4. Conflictos con decisiones vigentes

| # | Conflicto | Dónde está | Resolución | Estado |
|---|---|---|---|---|
| C-1 | El tema del storefront se elige con la variable `GROWUP_DEFAULT_THEME` del despliegue, no por tenant. Con un solo despliegue, ropa y joyería verían el mismo tema | `apps/storefront/lib/format.ts` (`defaultTheme`), `app/(site)/layout.tsx`, `app/(preview)/layout.tsx`, `README.md` | WP-02 antes de publicar Nova en tiendas. Ya previsto en `docs/plan/sincronizacion-frontend-apps-docker.md` §1.1, pero no implementado | Abierto: WP-02 |
| C-2 | ADR-0005 §5 pide tokens con esquema cerrado y CSS generado desde tokens. El validador actual es genérico (profundidad, tamaño, patrón de claves). El storefront no lee `tokens` | `services/api/app/domains/content/schemas.py`, `apps/storefront` | WP-03 (esquema tipado y registro de fuentes) y WP-02 | Abierto: WP-03 |
| C-3 | Se cargan siempre las cinco familias de fuentes | `apps/storefront/lib/fonts.ts` | Cargar solo las familias del tema activo (ya previsto en sincronización §1.1) | Abierto: WP-23 |
| C-4 | DEC-2 fija la dirección v0 para growup.com | `docs/plan/suite-publica-growup.md` | Reabierta para growup.com por DU-01 | Resuelto con H-03 |
| C-5 | La guía v0 prohíbe gradientes, vidrio, sombras suaves y radios distintos de 0 | `docs/prompts/v0-storefront.md` | Nova entra como preset nuevo (ADR-0005 §5). Las excepciones quedan en ADR-0020 | Resuelto con DU-02 |
| C-6 | La skill `design-taste-frontend` prohíbe mono decorativo, índices, líneas finas, brillos y vidrio | Skill del entorno | Excepciones cerradas en ADR-0020 (sección 6.2). Los medidores pasan `--allow` solo para esas excepciones | Resuelto con DU-02 |
| C-7 | El "click-to-select" del builder vuelve a usar postMessage, descartado en el commit `a80444a` | `docs/decisiones-pendientes.md`, actualización del 2026-11-14 | Solo si producto reabre la decisión. Por defecto no se implementa | Condicionado: WP-29 |
| C-8 | Ocultar un bloque (`hidden`) cambia el esquema cerrado de bloques | ADR-0005 §4 | Enmienda de ADR-0005, contrato y pruebas de fallback. Solo con aprobación | Condicionado: WP-29 |
| C-9 | DEC-2 dice que "la tienda de cada tenant sigue con su tema propio". Cambiar el tema de las tiendas de comerciantes afecta sus derechos | `docs/plan/suite-publica-growup.md` (DEC-2) | Superado para la plataforma por DU-06. WP-04 registra el cambio y redacta el texto nuevo de DEC-2 | Resuelto por DU-06; falta registrar (WP-04) |
| C-10 | Cambiar el sistema visual no debe cambiar la identidad del comerciante (nombre, logo, copy, productos, precios) | Plan y ADR-0005 | El plan no toca esos elementos. Cualquier cambio sobre ellos queda fuera de alcance | Resuelto por alcance |
| C-11 | DU-04 aplica Nova desde ya a tiendas de comerciantes que pueden tener marca propia | Esta sección y `docs/plan/suite-publica-growup.md` | Reversión a v0 disponible; orden staging → producción; decisión registrada en DU-06 | Resuelto por DU-06 |

## 5. Modelos y roles

### 5.1 Asignación (aprobada, DU-05)

| Rol | Modelo (ID exacto) | Variante | Uso | Precio USD por millón de tokens (entrada / salida) |
|---|---|---|---|---|
| Constructor | `opencode-go/gemini-4-argon` | `high` para multi-archivo; `medium` para trabajo acotado | Código, tests y documentos | 2 / 10 |
| Arquitecto | `opencode-go/kimi-k3.1-pro` | `high` | Lista de archivos y contratos en WP de tamaño M o L | 2 / 10 |
| Auditor | `opencode-go/gpt-6-luna` | `high` | Revisa el diff contra el DoD y los ADR. No corrige. Otra familia que el constructor, para no repetir sus errores | 0,10 / 0,50 hasta 272k de contexto |
| Juez | `opencode-go/deepseek-v4.1-flash` | `high` | Ejecuta los comandos y reporta la salida. No corrige | 0,15 / 0,60 |
| Redacción y copy es-CO | `opencode-go/glm-5.3-flash` | `high` | Textos de documentos, copy de bloques y plantillas | 0,15 / 0,50 |
| Segunda opinión SQL y RLS | `opencode-go/kimi-k2.7-code` | sin variante | Revisa migraciones y políticas RLS | 0,95 / 4 |

Los precios son los del listado de modelos del proveedor. No hay benchmarks propios: la asignación se calibra con WP-02 (sección 5.4).

### 5.2 Pipeline por WP

1. **Arquitecto** (solo WP de tamaño M o L): lista de archivos, contratos y pruebas.
2. **Constructor:** implementa y ejecuta los comandos del WP.
3. **Juez:** ejecuta la batería completa y reporta los fallos con su salida.
4. **Auditor:** revisa el diff contra `AGENTS.md`, los ADR y el DoD del WP.
5. Si el juez o el auditor encuentran fallos, vuelve al constructor con la lista exacta. Máximo dos iteraciones.
6. **Humano:** revisa el PR y la evidencia. Solo el humano aprueba el merge y los gates.

### 5.3 Lanzamiento

- Constructor: subagente `coder` con `model: "opencode-go/gemini-4-argon#high"`.
- Arquitecto: `arquitecto` con `model: "opencode-go/kimi-k3.1-pro#high"`.
- Auditor: `auditor` con `model: "opencode-go/gpt-6-luna#high"`.
- Juez: `juez` con `model: "opencode-go/deepseek-v4.1-flash#high"`.
- Redacción: `general` con `model: "opencode-go/glm-5.3-flash#high"`, solo para documentos.

### 5.4 Calibración

WP-02 es el piloto de calibración: tamaño medio, multi-archivo y con criterio de aceptación automático (E2E A/B). Medir: si pasa la batería al primer intento, iteraciones necesarias, tokens consumidos y cambios fuera de alcance. Si el constructor falla en más de dos iteraciones, subir a `high` o reducir el WP.

## 6. Dirección visual Nova (base de ADR-0020)

### 6.1 Definición operativa

Nova es un sistema visual de "técnico total" con tres usos:

- **Sistema visual de growup.com y del admin** (DU-01, DU-04).
- **Preset de tema del storefront.** Cualquier comerciante puede elegirlo. Las tiendas de ropa y joyería lo adoptan en el orden staging → producción (DU-06).
- **Referencia para el builder**, con el mismo sistema de tokens.

Su lenguaje:

- Oscuro por defecto, con equivalente claro generado con `light-dark()`.
- Display ancho y de peso variable; cuerpo neutro; datos, etiquetas e índices en mono.
- Estructura visible: rejillas, líneas finas, coordenadas y códigos de lote como parte del diseño.
- Un acento luminoso por preset, usado en acciones, foco y estados.
- Recortes angulares en controles y tarjetas.
- Movimiento CSS con propósito. Sin WebGL ni 3D en el storefront.

### 6.2 Excepciones permitidas frente a design-taste-frontend (lista cerrada, DU-02)

Solo estas. Cualquier otra desviación exige enmendar ADR-0020.

1. **Mono** (Geist Mono) para datos, etiquetas, metadatos, SKU, tallas, medidas y titulares secundarios. Nunca para cuerpo de texto informativo.
2. **Índices y códigos visuales:** numeración (01, 02, 03), códigos de lote, coordenadas y marcas de corte. Si son decorativos, llevan `aria-hidden`.
3. **Líneas finas** (1 px) y rejillas visibles como estructura de secciones, tablas, formularios y separadores.
4. **Brillo de acento** (sombra de color estática) en hasta dos elementos por pantalla. Nunca animado.
5. **Esquinas recortadas** (`clip-path`) y ángulos en botones, tarjetas, campos y etiquetas.
6. **Gradientes de fondo** por sección. Nunca detrás de texto informativo ni de botones, salvo que pasen el contraste medido.
7. **`backdrop-filter`** en el encabezado y en un panel modal, como máximo dos por pantalla. Nunca sobre imágenes en movimiento.
8. **Titulares de hasta tres líneas** en escritorio y dos en móvil. Sin desbordamiento en ningún ancho.
9. **Grano o scanlines** decorativos: estáticos, `aria-hidden`, `pointer-events: none` y sin costo medido en LCP.
10. **Etiquetas técnicas de 11 a 12 px** solo como metadato decorativo. Ningún texto informativo por debajo de 12 px.
11. **Un único movimiento decorativo por pantalla** (por ejemplo, un barrido de la línea de acento), solo con `transform` y `opacity`, y desactivado con reduced-motion.

**Límites no negociables** (ninguna excepción los cubre):

- Contraste WCAG AA: 4,5:1 para texto normal; 3:1 para texto grande y componentes de interfaz con significado.
- Foco visible en todo elemento interactivo (ver 6.7 sobre `clip-path`).
- Cuerpo de texto de 16 px o más. Ninguna información solo por color.
- `prefers-reduced-motion` respetado. CLS menor de 0,1. LCP móvil menor de 2,5 s. INP menor de 200 ms.
- Checkout y fuentes: cero recursos de terceros.
- Ningún contenido de relleno, emoji ni prueba social inventada (la regla de la skill "proof is never invented" se mantiene).
- Objetivos táctiles de al menos 24 × 24 px.
- Contenido visible sin JavaScript.

### 6.3 Tipografía (Opción A, DU-03; verificada en el catálogo de Google Fonts)

| Rol | Familia | Ejes disponibles | Uso |
|---|---|---|---|
| Display | Unbounded | Peso 200 a 900 | Titulares. Es una familia ancha: el titular ocupa más espacio. No tiene eje de ancho, así que los titulares estrechos se resuelven con tamaño y tracking, no con `font-stretch` |
| Cuerpo | Geist | Peso 100 a 900 | Texto corrido, formularios y UI |
| Datos y etiquetas | Geist Mono | Peso 100 a 900 | Precios técnicos, SKU, tallas, medidas, metadatos e índices |

**Evitar en Nova:** Anton, Space Grotesk, Space Mono, Playfair Display, Plus Jakarta Sans e Inter. Ya están en uso en ropa, joyería, la web pública o el admin. Evitar también los estilos de ciencia ficción de catálogo (Orbitron, Michroma, Oxanium, Audiowide) y los pixel (Silkscreen, Doto): son disfraces, no diseño.

**Carga:** `next/font/google` con subsets `latin` y `latin-ext` (cubren el español de Colombia), `display: swap`, solo las tres familias del preset y solo las del tema activo (C-3).

### 6.4 Color (valores iniciales; los confirma la medición de contraste)

Oscuro (por defecto):

- Fondo `oklch(0.155 0.012 265)`
- Superficie `oklch(0.205 0.015 265)`
- Línea `oklch(0.34 0.015 265)`
- Texto `oklch(0.975 0.004 265)`
- Texto secundario `oklch(0.76 0.015 265)`
- Acento (uno solo) `oklch(0.88 0.19 128)`. El texto sobre acento usa el color de fondo, nunca blanco.

Claro: mismo tono de neutros (matiz 265) con luminosidades invertidas. El acento se recalcula para contraste.

Reglas: un acento por preset. Los estados (éxito, aviso, error) llevan icono o texto además de color. El medidor debe confirmar AA en todos los pares usados, incluidos los gradientes de fondo permitidos en 6.2.

### 6.5 Forma, composición y "producto en vivo"

- Radio: 0 en el preset v0 de ropa y joyería (cambia con DU-06 y el orden staging → producción). En Nova, recorte angular de 8 a 12 px según H-02.
- Rejilla de 12 columnas con márgenes fluidos (`clamp()`). Los bloques responden a su contenedor con `@container`.
- Cada sección tiene una composición distinta. Ninguna es una fila de tarjetas idénticas con icono arriba.
- Se permiten tablas de especificaciones y "placas de datos" en la PDP.
- Un "producto en vivo" por página, con datos reales. En la PDP, el selector de variante actualiza precio y stock. En la home, un marquee de colecciones reales. Debe funcionar sin JavaScript (fallback).

### 6.6 Movimiento

- CSS primero. Duración de interfaz de 120 a 180 ms; revelados de 500 a 700 ms; easing estándar o `linear()` con fallback.
- Entradas escalonadas de 60 a 90 ms, una vez por sección, con `animation-timeline: view()` dentro de `@supports`. Sin soporte, el contenido se muestra sin animar.
- Solo `transform` y `opacity`. No animar `box-shadow`, `filter` ni `backdrop-filter`.
- Como máximo ocho elementos animándose a la vez. El medidor de la skill falla con menos de ocho en carga y scroll.
- `prefers-reduced-motion: reduce`: sin desplazamientos; el contenido permanece visible.
- Marquee pausado en hover y con reduced-motion.
- Usar las skills `animate` y `animation-performance`.

### 6.7 CSS moderno

Cada función con `@supports` o fallback. Verificar compatibilidad en MDN antes de usarla.

- `@layer` (reset, tokens, base, componentes, utilidades, sobreescrituras).
- `oklch()`, `color-mix()`, `light-dark()` y `color-scheme`.
- `@container` para bloques, `clamp()` para tipografía y espaciado, `dvh` y `svh` en lugar de `100vh`.
- `text-wrap: balance` en titulares y `text-wrap: pretty` en párrafos.
- `:focus-visible` y `:has()` para estados.
- View Transitions API para la imagen de producto que va al carrito (progresivo).
- `clip-path` recorta también el `outline`. El foco se dibuja dentro de la forma, con un pseudo-elemento o un borde interior. Verificar con Playwright.
- `subgrid` para alinear el interior de las tarjetas de producto.

### 6.8 Rendimiento, privacidad y accesibilidad

- Métricas del plan maestro (§13): LCP móvil menor de 2,5 s; CLS menor de 0,1; INP menor de 200 ms. Lighthouse móvil: rendimiento ≥ 80, accesibilidad ≥ 90, SEO ≥ 90.
- Como máximo dos capas de blur por pantalla, nunca sobre imágenes.
- Fuentes self-hosted. Prueba E2E: el storefront no hace peticiones a dominios de fuentes de terceros.
- Checkout: sin scripts ni estilos externos; CSP estricta; ningún cambio añade recursos de terceros (D-11, SAQ A).
- Foco visible en todo elemento interactivo; objetivos de al menos 24 × 24 px; ninguna información solo por color; `lang="es-CO"`.
- Comportamiento táctil y móvil: skill `mobile-native`.

### 6.9 Gates de diseño (Definition of Done visual)

Además del DoD de `AGENTS.md`:

1. `node <skill>/scripts/lint.mjs` y `node <skill>/scripts/inspect.mjs` sin FAIL fuera de las excepciones de 6.2. Esas excepciones se pasan con `--allow <regla>` y quedan listadas en ADR-0020. Cualquier otra regla que falle bloquea el merge.
2. Axe sin violaciones críticas ni serias en las rutas tocadas.
3. Contraste AA medido en todos los pares, incluidos los fondos con gradiente.
4. Prueba de reduced-motion.
5. Capturas de 1440, 768 y 390 px revisadas por una persona (H-02 y H-07).
6. Prueba de peor caso con la skill `break-ui`: nombres de producto largos, precios grandes y textos en otros idiomas. Las tipografías anchas rompen más fácil.

Para el admin, usar la skill `impeccable` (cubre paneles y shells de aplicación). `design-taste-frontend` excluye paneles. En el admin, además, las rutas protegidas y los permisos no cambian.

## 7. Work packages

Columnas: ID · trabajo · entregables · aceptación · bloqueo · modelo sugerido · tamaño en sesiones.

### Bloque 0: verdad, decisiones y cimientos (semanas 0 a 3)

| ID | Trabajo | Entregables | Aceptación | Bloqueo | Modelo | Tam. |
|---|---|---|---|---|---|---|
| WP-00 | Verificar el estado real | `docs/estado/verificacion-AAAA-MM-DD.md` con resultados de pytest, ruff, mypy, pgTAP, `pnpm lint`, `typecheck`, `build` y E2E | Informe con salidas reales. Ningún cambio de código | Entorno con uv, pnpm y Postgres (Docker) | Constructor `medium` y juez | 1 |
| WP-01 | Reconciliar la documentación | Tabla de contradicciones (plan §0 frente a ADR-0005 frente a decisiones); corrección de la referencia §9 a §10 del principio 5; una sola numeración de fases | Ningún estado de decisión cambia. Cada cambio cita su fuente | H-01 | Redacción (`glm`) y auditor | 1 |
| WP-02 | Tema por tenant (cierra C-1 y C-3) | `lib/format.ts` sin `GROWUP_DEFAULT_THEME`; los layouts leen el tema del bootstrap del tenant resuelto por host; variables CSS generadas desde tokens; solo fuentes del tema activo; seed con tokens de ropa y joyería en el preset v0 | Cero referencias a `GROWUP_DEFAULT_THEME`; E2E con dos hosts muestra temas distintos desde un mismo despliegue; regresión visual de ropa y joyería sin diferencias en el preset v0; pytest del bootstrap | WP-00 | Constructor `high` y auditor | 2 |
| WP-03 | Tokens tipados y registro de fuentes (cierra C-2) | `ThemeTokensV1` en Pydantic con `extra="forbid"`, `schema_version`, enums de preset (`ropa`, `joyeria`, `nova`), fuente, esquema de color, radio y movimiento; registro de fuentes en `packages/config` leído por Python y TypeScript; migración expand y contract | Token fuera de registro devuelve 422 `VALIDATION_ERROR`; prueba de paridad entre registro de front y back; `pnpm contracts:check` con cambio legítimo documentado | WP-02 | Constructor `high`; SQL con `kimi-k2.7-code` | 2 |
| WP-04 | Registrar decisiones DU-01 a DU-06 y reabrir DEC-2 | Entradas en `docs/decisiones-pendientes.md` con fecha y responsable para DU-01 a DU-06; nota de reapertura y texto nuevo de DEC-2 en `docs/plan/suite-publica-growup.md`; precisión del principio "tema propio" (C-9) | Ninguna D-xx cambia de estado; DEC-2 aparece como reabierta con referencia a DU-01 y DU-06 | H-01 y H-03 | Redacción (`glm`) y auditor | 1 |

### Bloque 1: piloto y base segura (semanas 1 a 18)

| ID | Trabajo | Entregables | Aceptación | Bloqueo | Modelo | Tam. |
|---|---|---|---|---|---|---|
| WP-10 | Piloto F1 a F6 (plan maestro) | Dockerfiles, CI con Trivy (F1-07), seeds (F6-01), E2E de compra y aislamiento host A/B (F6-03), runbooks borrador | Según el DoD de cada ID del plan maestro | H-06 (cuentas) y H-07 (aprobación) | Constructor y juez | Varias |
| WP-11 | Estados separados de la orden | ADR nuevo; `payment_status`, `fulfillment_status` y ciclo de vida como campos independientes; máquinas de estado puras | Pruebas de transiciones válidas e inválidas; pgTAP. Debe cerrarse antes de congelar el DDL de órdenes (F4) | Ninguno | Constructor `high` | 1 a 2 |
| WP-12 | Outbox, inbox e idempotencia | Tablas con RLS; relay worker; inbox de webhooks con verificación de firma en tiempo constante; claves de idempotencia por tenant y operación con hash canónico | Implementadas las pruebas de Plan C §2 que bloquean el release de pagos: firma inválida, repetición, concurrencia y caída de la base | H-06 para pruebas reales; primero con mocks | Constructor `high` y auditor | 3 |
| WP-13 | Fronteras entre dominios | Chequeo automático de importaciones (verificar la herramienta antes de elegirla); regla en CI | Un import prohibido rompe CI; prueba con caso malo | Ninguno | Constructor `medium` | 1 |

### Bloque 2: Nova

| ID | Trabajo | Entregables | Aceptación | Bloqueo | Modelo | Tam. |
|---|---|---|---|---|---|---|
| WP-20 | ADR-0020 Nova | `docs/adr/0020-direccion-visual-nova.md` con las secciones 6.1 a 6.9, la lista cerrada de excepciones y los límites no negociables | Revisado por una persona | H-02 | Arquitecto y redacción | 1 |
| WP-21 | Prototipo principal y dos variantes de composición, fuera de `apps/` | `docs/design/nova/{principal,variante-a,variante-b}/index.html` y capturas de 1440, 768 y 390 px | Medidor sin FAIL fuera de las excepciones; contraste AA; cero peticiones externas; prueba con `break-ui` | H-02 | Constructor `high` | 2 |
| WP-22 | Tokens del preset `nova` | `@layer tokens`; colores en oklch con `light-dark()`; escala tipográfica fluida (Unbounded, Geist, Geist Mono); espaciado; radio; tokens de movimiento | Contraste AA calculado por script; ningún color fuera de tokens | WP-21 | Constructor `high` | 1 a 2 |
| WP-23 | Fuentes Nova | Entradas en el registro de fuentes con Unbounded, Geist y Geist Mono; `next/font` solo para el tema activo | E2E: cero peticiones a terceros; sin cambios de CLS | WP-03 y WP-22 | Constructor `medium` | 1 |
| WP-24 | Componentes base Nova | Button, Tag, Field, Price, Link y estados de foco; sin librerías de UI | Axe sin críticos; estados hover, focus y disabled probados; objetivos de al menos 24 px | WP-22 | Constructor `high` | 2 |
| WP-25 | Bloques Nova | Los 16 bloques como variantes de estilo; ningún bloque nuevo (ADR-0005 §4). Dos sesiones: 25a hero, grilla y carrusel; 25b el resto | Bloque desconocido sigue con fallback; snapshot visual por bloque; axe | WP-24 | Constructor `high` | 2 a 3 |
| WP-26 | Páginas Nova del storefront | Home, colección, PDP, carrito y checkout en el preset `nova`. Publicación en las tiendas de ropa y joyería en el orden staging → producción (DU-06) | E2E de compra sandbox (B-02); LCP móvil menor de 2,5 s; Lighthouse ≥ 80; checkout sin recursos externos; reversión a v0 probada en staging | WP-25, WP-02 y WP-03 | Constructor `high` | 3 |
| WP-27 | Capa de movimiento | Entradas por sección, feedback de controles y un movimiento decorativo por pantalla | Sección 6.6 cumplida; reduced-motion probado; medidor sin FAIL | WP-26 | Constructor `high` | 1 |
| WP-28 | Builder v2 (mejoras propuestas) | Pantalla completa; selector de viewport (escritorio 100 %, tablet 768, móvil 390); deshacer y rehacer en cliente; selector de página; cajón de tokens del tema | Pruebas de componentes y E2E; sin cambios de contrato | WP-03 | Constructor `high` | 2 |
| WP-29 | Condicionados | Ocultar bloque (C-8); click-to-select (C-7) | Solo con aprobación explícita y enmienda de ADR | Decisión de producto | No asignado | n/a |
| WP-30 | growup.com (`apps/web`) en Nova | Aplicación de Nova al sitio público. Primer entregable visible | Se mantienen DEC-3 (sin precios públicos) y DEC-5 (sin super consola pública). Requiere H-03 registrado en WP-04 | H-02 y H-03 | Constructor `high` | 2 |
| WP-31 | Admin en Nova | Shell oscuro y tokens primero; después las páginas. Staging primero y aviso a los usuarios antes de producción | Skill `impeccable`; rutas protegidas y permisos sin cambios; pruebas de rutas de plataforma | H-02 y H-03 | Constructor `high` | 3 o más |

### Bloque 3: nivel 2 (después del go/no-go)

| ID | Trabajo | Entregables | Aceptación | Bloqueo | Modelo | Tam. |
|---|---|---|---|---|---|---|
| WP-40 | Analítica básica | Vistas SQL con `security_invoker = true` (ventas, pedidos, productos más vendidos, ticket promedio); página en el admin | pgTAP: el tenant A no ve datos del B a través de las vistas; prueba A/B | WP-11 | Constructor `high` | 2 |
| WP-41 | Dominio propio | ADR con el proveedor de D-07; verificación de propiedad por TXT; emisión de TLS; normalización de `domains.host` (minúsculas, punycode, sin puerto) | Pruebas de host: mayúsculas, puerto, punycode y dominio desconocido (404); prueba A/B | H-06 (Cloudflare) y decisión de proveedor | Constructor `high` | 3 |
| WP-42 | Credenciales de integración | ADR nuevo; tokens con hash, scopes, expiración, rotación y auditoría; límite de tasa por credencial | Token revocado devuelve 401; scope insuficiente devuelve 403; ningún token en logs | WP-12 | Constructor `high` y auditor | 2 |
| WP-43 | API pública v1 | Endpoints de lectura de productos y pedidos; escritura limitada; `Idempotency-Key`; OpenAPI publicado | Pruebas de contrato; `pnpm contracts:check` | WP-11 y WP-42 | Constructor `high` | 3 |
| WP-44 | Webhooks públicos | Suscripciones por tenant; catálogo de eventos; firma HMAC; reintentos; reenvío | Pruebas de firma, reintento y aislamiento entre tenants | WP-12 | Constructor `high` | 2 |
| WP-45 | Descuentos | Códigos y reglas simples; límite de usos con actualización atómica; snapshot en `order_items`; base gravable con IVA incluido | Prueba de concurrencia en el último uso; totales en centavos; redondeo según D-06 | H-05 y WP-11 | Constructor `high` y auditor | 3 |
| WP-46 | Devoluciones automatizadas | Máquina de estados (solicitada, aprobada, recibida, reembolsada, rechazada); reembolso parcial; reembolso vía Wompi; nota crédito por adaptador si D-03 lo permite | Transiciones probadas; un reembolso repetido no se duplica; HANDOFF manual si falta un adaptador | H-04 (D-13), D-03, WP-11 y WP-12 | Constructor `high` y auditor | 3 |
| WP-47 | Correos transaccionales | Adaptador de Resend; webhooks de rebote; plantillas | Rebote registrado; ningún dato personal en logs | H-06 y D-15 | Constructor `medium` | 2 |

### Bloque 4: calidad y cumplimiento (transversal)

| ID | Trabajo | Entregables | Aceptación | Bloqueo | Modelo | Tam. |
|---|---|---|---|---|---|---|
| WP-50 | Pruebas de aislamiento reutilizables | Helpers para pruebas A/B de host y de JWT | Usados por todos los WP que tocan tenants | Ninguno | Constructor `medium` | 1 |
| WP-51 | Evidencia SOC 2-ready | Borradores en `docs/compliance/` (D-18) | Aprobado por una persona | H-04 | Redacción y auditor | 1 |
| WP-52 | Documentos legales (borrador) | Plantilla de DPA, matriz de retención, protocolo de brechas, política de devoluciones | Marcados como borrador; no se publican sin firma del abogado | H-04 (D-09 a D-13) | Redacción y auditor | 2 |
| WP-53 | Seguridad continua | pip-audit, pnpm audit y Trivy en CI; checklist OWASP; pentest externo | Sin críticos abiertos al go-live | H-06 | Constructor `medium` y juez | 1 |

## 8. Calendario orientativo

Base: arranque el 16 de noviembre de 2026. Caso base del plan: piloto en la semana 18 (22 de marzo de 2027). Nova empieza desde ya (DU-04). growup.com y el admin van primero porque son el primer entregable visible.

| Ventana | Trabajo | Notas |
|---|---|---|
| Semana 0 (desde ya) | H-01 y WP-04 (registro de DU-01 a DU-06 y reapertura de DEC-2); WP-00 arranca; WP-20 (ADR-0020) | Sin WP-04, growup.com no puede cambiar de identidad con soporte documental |
| Semanas 1 a 2 | WP-21 (prototipo) y revisión de H-02; WP-22 y WP-23 (tokens y fuentes); WP-01; WP-02 (calibración) | La revisión de H-02 es el primer cuello de botella |
| Semanas 2 a 4 | WP-30 (growup.com en Nova) y WP-24 (componentes); WP-03 | growup.com es el primer entregable visible |
| Semanas 3 a 8 | WP-25 y WP-31 (admin, en staging); WP-26 en staging; piloto F1 a F5; WP-11, WP-12 y WP-13 | El admin sale a producción con aviso a los usuarios y sin cambios de flujo |
| Semanas 8 a 12 | WP-27 y WP-28; WP-26 en producción para las tiendas de ropa y joyería, con reversión a v0 lista; vistas previas de F6-02 con Nova (H-07) | "Desde ya" significa que el plan no espera a nadie. El código y tu revisión marcan el ritmo |
| Semanas 12 a 18 | F6 (E2E, QA, criterios de aceptación); go-live en la semana 18 | Caso base: 22 de marzo de 2027 |
| Después del go/no-go | Nivel 2 (WP-40 a WP-47) | Descuentos y devoluciones esperan H-04 y H-05 |

**Plan B:** si la revisión de Nova se retrasa más allá de la semana 10, las tiendas siguen con v0 y Nova se publica en ellas después del go-live. growup.com y el admin no dependen de esa fecha.

Con constructores de IA, el cuello de botella pasa de escribir código a decidir y revisar. Propuesta: dos bloques fijos de revisión humana por semana, con la lista de PR y gates pendientes. Con DU-04, esa revisión se reparte entre el piloto y Nova; hay que priorizar la revisión de los gates que bloquean publicaciones.

## 9. Riesgos específicos de construir con IA

| Riesgo | Mitigación |
|---|---|
| Inventar APIs de Wompi, Factus, Stripe o Resend | Adaptadores aislados con pruebas de contrato; verificación contra la documentación oficial y la sandbox (H-06) |
| Desviarse de los ADR | Cada WP cita sus ADR; el auditor revisa contra ellos |
| Regresión de seguridad multi-tenant | Prueba A/B obligatoria en cada WP que toque tenants |
| Cambio de identidad de tiendas de comerciantes sin su consentimiento, aceptado por DU-06 | Decisión registrada en DEC-2 con fecha y responsable (WP-04); reversión a v0; no se tocan nombre, logo, copy, productos ni precios. Si alguna marca es de un tercero, conviene que el abogado revise su contrato antes del go-live (riesgo contractual, no un gate del plan) |
| Contraste o legibilidad insuficientes por el futurismo técnico | Límites no negociables de 6.2 medidos en CI; revisión humana de capturas |
| Carga de revisión humana: Nova y piloto en paralelo | Bloques fijos de revisión; el plan B de la sección 8 protege el piloto |
| Reapertura de DEC-2 sin registro formal | WP-04 antes de cualquier cambio en growup.com o en las tiendas |
| Pérdida de contexto entre sesiones | Cada WP lista sus archivos y comandos; `AGENTS.md` es la fuente de reglas |
| Alcance que crece | La lista de WP es cerrada. Las ideas nuevas van a backlog, no al WP en curso |
| Costo de tokens | Medir en WP-02; limitar iteraciones; usar `medium` para trabajo acotado |
| Modelos gratuitos con datos sensibles | Regla 13 de la sección 2 |

## 10. Plantilla de sesión para el constructor

```text
Eres el constructor de WP-XX de Growup. Antes de tocar código lee, en este orden:
1. AGENTS.md
2. docs/decisiones-pendientes.md (solo lectura; no cambies estados)
3. Los ADR citados en el WP (y ADR-0020 cuando el WP sea de Nova)
4. Este WP (copiado abajo, con sus gates)

Objetivo: <objetivo del WP>
Entregables: <lista>
Fuera de alcance: <lista explícita>
Gates que debes detener: <H-xx si aplica>
Excepciones de diseño permitidas: <solo las de ADR-0020 sección 6.2, si aplica>

Al terminar entrega:
- archivos cambiados
- comandos ejecutados y su salida
- riesgos y preguntas abiertas
- no declares nada como verificado sin salida de comando
```

## 11. Primeros pasos (desde ya)

1. **H-01 y WP-04:** aprobar y registrar DU-01 a DU-06. Incluye la eliminación de H-10, el resultado de H-11 y el texto nuevo de DEC-2. La edición de `docs/plan/suite-publica-growup.md` la hace el agente de construcción dentro de WP-04.
2. **WP-20 y WP-21:** redactar ADR-0020 y el prototipo principal. H-02 revisa las capturas.
3. **WP-22, WP-23 y WP-30:** tokens, fuentes y growup.com en Nova. Es el primer entregable visible.
4. **WP-00:** verificar el estado real en un entorno con uv, pnpm y Postgres. Corre en paralelo.
5. **WP-02 como calibración:** medir a Gemini 4 Argon antes de lanzar el resto del programa.
6. Copiar este plan a `docs/plan/` del repo y abrir un PR de documentación.
