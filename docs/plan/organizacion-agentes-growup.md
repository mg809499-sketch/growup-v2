# Organización de agentes · Growup

**Fecha:** 2026-11-15 · **Relacionado:** `plan-nova-gemini-argon.md` (v4)
**Estado:** organización aprobada en el plan. Lista para usar.

---

## 1. Principio

Yo (orquestador) no escribo código ni edito archivos. Delego y verifico. La cadena es fija:

```text
arquitecto → coder → juez → auditor → (humano: revisa PR y gates)
```

- **arquitecto**: diseña archivos y contratos. Solo para WP de tamaño M o L.
- **coder**: único agente que genera código. Implementa el WP.
- **juez**: ejecuta la batería y reporta salidas reales. No corrige.
- **auditor**: revisa el diff contra AGENTS.md, ADR y DoD. No corrige.
- **humano**: aprueba merge y gates (H-xx). Ningún agente lo hace.

Si juez o auditor encuentran fallos, vuelve al coder con la lista exacta. Máximo dos iteraciones. Después, escalar a humano.

## 2. Roster

| Agente | Subagente | Modelo (ID exacto) | Variante | Puede | No puede |
|---|---|---|---|---|---|
| Orquestador | (yo) | Claude Haiku 5.5 (`opencode-go/claude-haiku-5-5`) | — | Delegar, resumir, llevar el tablero | Escribir código o editar archivos |
| Arquitecto | `arquitecto` | `opencode-go/kimi-k3.1-pro` | `high` | Listar archivos, contratos y pruebas | Generar código |
| Constructor | `coder` | `opencode-go/gemini-4-argon` | `high` (multi-archivo) o `medium` (acotado) | Código, tests, documentos técnicos | Aprobar su propio trabajo |
| Auditor | `auditor` | `opencode-go/gpt-6-luna` | `high` | Revisar diff contra reglas y ADR | Corregir |
| Juez | `juez` | `opencode-go/deepseek-v4.1-flash` | `high` | Ejecutar comandos y reportar salidas | Corregir |
| Redacción | `general` | `opencode-go/glm-5.3-flash` | `high` | Documentos y copy es-CO | Código (ver regla 4) |
| SQL y RLS | `general` | `opencode-go/kimi-k2.7-code` | — | Segunda opinión de migraciones y políticas | Aplicar migraciones |
| Explorador | `explore` | predeterminado | — | Buscar archivos y patrones (quick, medium, very thorough) | Editar |

Formato de modelo al lanzar: `providerID/modelID#variant`, por ejemplo `opencode-go/gemini-4-argon#high`.

## 3. Reglas de enrutamiento

1. **Un WP, un coder.** No se asignan dos coders al mismo archivo a la vez.
2. **Paralelo solo si los archivos no se tocan.** Ejemplo válido: WP-21 (prototipo fuera de `apps/`) junto con WP-20 (ADR). Inválido: WP-02 y WP-03 (ambos tocan `storefront/lib`).
3. **Tamaño decide arquitecto.** S: sin arquitecto. M y L: arquitecto primero.
4. **Documentos.** El plan dice `general` para redacción. Como regla estricta del entorno, solo el coder genera código. Los documentos (`.md`) no son código, así que `general` es válido. Si un documento contiene código ejecutable (SQL, TS), va por el coder.
5. **SQL y RLS.** Toda migración pasa por `kimi-k2.7-code` (revisión) antes del juez.
6. **Sin asignación automática de modelos.** Los modelos distintos de Gemini necesitan confirmación explícita del usuario. Ya están aprobados en DU-05, así que puedo usarlos.

## 4. Gates y quién los cierra

| Gate | Quién | Cómo lo sabe el orquestador |
|---|---|---|
| H-01 | Producto | Respuesta explícita antes de WP-01 |
| H-02 | Producto y diseño | Revisión de capturas de WP-21 |
| H-03 | Producto | Registro de DEC-2 en WP-04 |
| H-04 | Abogado | Dictamen escrito (marca, código, D-09 a D-13) |
| H-05 | Contador | Dictamen de IVA y redondeo |
| H-06 | Humano | Cuentas creadas; credenciales fuera del repo |
| H-07 | Comerciantes y producto | Vistas previas firmadas |
| H-08 | Producto | Go/no-go escrito |
| H-09 | Humano | Despliegue y on-call |

El orquestador **nunca** marca un gate como cerrado por su cuenta. Si un WP lo requiere, lo deja en pausa y avisa.

## 5. Tablero de trabajo

Estados por WP: `pendiente` → `arquitectura` → `construcción` → `juez` → `auditoría` → `revisión humana` → `hecho`. Se llevan en `docs/plan/` (WP-00 lo crea) o aquí, y se actualizan al cerrar cada etapa.

Cada WP cerrado deja:
- archivos cambiados
- salida del juez
- hallazgos del auditor y su resolución
- gates pendientes

## 6. Plantilla de delegación

Para cada WP, lanzo:

```text
subagente: coder
modelo: opencode-go/gemini-4-argon#high
descripción: WP-XX <título corto>
prompt: plantilla de sesión (sección 10 del plan) con objetivo, entregables,
        fuera de alcance, gates, excepciones de diseño (ADR-0020 §6.2) y
        la instrucción "no declares nada verificado sin salida de comando".
```

Luego `juez` y `auditor` reciben el mismo WP y el diff resultante, no el razonamiento del coder.

## 7. Control de costo y contexto

- Precios: Kimi K3.1 Pro 2/10 USD por millón (entrada/salida); Gemini 4 Argon 2/10; GPT-6 Luna 0,10/0,50; DeepSeek V4.1 Flash 0,15/0,60; GLM-5.3 Flash 0,15/0,50; Kimi K2.7 Code 0,95/4. Precios por millón de tokens, según el listado del proveedor.
- **Advertencia:** el modo original de este entorno era "APIs gratuitas + nube Ollama". Estos modelos son de pago por token en opencode-go. Hay que aprobar un presupuesto antes de empezar. Yo no lo fijo.
- Medir en WP-02 (calibración): tokens por WP, iteraciones y fallos. Si un WP consume más de tres veces lo estimado, parar y revisar.
- Un solo WP activo por coder. Los resultados largos se resumen; no se pegan archivos enteros en el contexto del orquestador.

## 8. Cadencia

- **Semanal:** dos bloques fijos de revisión humana con la lista de PR y gates pendientes.
- **Al cerrar un bloque o un gate importante:** sugerir guardar un resumen de sesión.
- **Cada WP:** juez y auditor antes de la revisión humana, sin excepción.

## 9. Primeros lanzamientos (en este orden)

1. `general` (GLM) → WP-04: registrar DU-01 a DU-06 en `docs/decisiones-pendientes.md` y reabrir DEC-2. Pendiente: H-01 y H-03 confirmados.
2. `coder` (Gemini `#medium`) → WP-00: verificar pytest, ruff, mypy, pgTAP, `pnpm lint`, `typecheck` y `build`. Entrega solo el informe; no cambia código.
3. `juez` (DeepSeek `#high`) → repetir la batería de WP-00 y contrastar con el informe.
4. `arquitecto` (Kimi `#high`) → ADR-0020 (WP-20).
5. `coder` (Gemini `#high`) → WP-21 prototipo, fuera de `apps/`. Puede correr en paralelo con el paso 4 si no toca los mismos archivos.
6. `coder` (Gemini `#high`) → WP-02 calibración, luego `juez` y `auditor`.

## 10. Qué no hago

- No ejecuto código ni migraciones contra producción.
- No firmo ni acepto términos ni contratos.
- No creo cuentas ni guardo credenciales.
- No cambio DNS ni publico en producción.
- No toco `../multitiendas`.
- No pido ni muestro `.env` ni secretos.
