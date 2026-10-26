# ADR-0010 — Checkout hosted, PCI SAQ A y gestión de scripts

- **Estado:** Propuesta
- **Fecha:** 2026-10-26
- **Decisores:** Producto, Ingeniería y Seguridad
- **Relacionado con:** D-02, D-11, D-14, ADR-0004, ADR-0008

## Contexto

D-02 define al comerciante como *merchant of record* y a Wompi como pasarela del checkout. Growup nunca debe capturar, transmitir ni almacenar PAN, CVV o datos de tarjeta. PCI-DSS v4.0.1 exige controles sobre los scripts que se ejecutan en la página de pago (6.4.3) y detección de alteraciones (11.6.1), aunque el checkout esté delegado.

Wompi todavía no tiene cuenta creada ni spike técnico. No se sabe si la integración será por redirect puro o por widget/iframe con JavaScript en nuestra página.

## Decisión

Se propone adoptar la opción A de D-11, condicionada al spike de Wompi:

1. **Redirect hosted como opción preferida.** El checkout de Growup redirige a Wompi; la captura de datos de tarjeta ocurre fuera de nuestro origen.
2. **Cero scripts de terceros en checkout.** Sin GTM, pixels, mapas de calor ni analítica en `/checkout`. Los scripts propios se inventarían y revisan.
3. **CSP estricta.** Allowlist limitada al origen propio y a los dominios confirmados de Wompi; sin `unsafe-inline` en el flujo de pago.
4. **SRI en assets propios** y monitoreo de integridad en el borde cuando el plan de Cloudflare lo permita.
5. **MFA en accesos administrativos** y gestión de cambios para todo lo que toque checkout.
6. **SAQ A o SAQ A-EP se decide después del spike.** Si Wompi exige un widget con JS en nuestra página, se evalúa A-EP y ASV; no se afirma SAQ A de antemano.
7. **Nada de datos de tarjeta en logs, Sentry, analytics ni base de datos.**

La integración real, la cuenta Wompi, los webhooks y la decisión final de SAQ quedan para el final de la secuencia (D-11).

## Alternativas consideradas

| Alternativa | Pros | Contras | ¿Por qué no? |
|---|---|---|---|
| Redirect hosted | Menor superficie, SAQ A más simple | Menos control visual, salida del dominio | Es la opción preferida |
| Widget/iframe embebido | Mejor continuidad visual | Puede arrastrar SAQ A-EP y más controles | Solo si Wompi lo exige |
| Checkout propio con tokenización | Control total | Nunca debe manejar PAN; complejidad PCI alta | Fuera de alcance |
| No formalizar SAQ | Cero trabajo | Incumple contrato con la pasarela/marcas | Riesgo inaceptable |

## Consecuencias

### Positivas

- Menor alcance PCI y menor riesgo de e-skimming.
- Menos código sensible y menos superficie de ataque.
- Flujo de checkout más fácil de auditar.

### Negativas / deuda asumida

- La experiencia de pago depende del diseño de Wompi.
- Hay que mantener inventario de scripts y CSP.
- Si Wompi obliga a widget, el alcance PCI puede crecer.
- La cuenta y el sandbox aún no existen; el checkout no está listo.

### Neutras

- El flujo de analytics del storefront debe excluir explícitamente `/checkout`.

## Cómo se verifica

- Test de headers: CSP, `X-Frame-Options`, `Referrer-Policy` en `/checkout`.
- Inventario de scripts versionado y test que falle si aparece un tercero en checkout.
- Prueba E2E en sandbox: redirect, pago aprobado, webhook firmado, orden creada.
- Revisión anual de SAQ y evidencia de MFA para accesos administrativos.

## Enlaces

- `docs/decisiones-pendientes (1).md` — D-02, D-11, D-14
- `docs/adr/0004-pagos-checkout-merchant-of-record.md`
- `docs/adr/0008-topologia-despliegue.md`
