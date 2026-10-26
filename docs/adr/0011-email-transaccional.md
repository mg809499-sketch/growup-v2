# ADR-0011 — Email transaccional multi-tenant

- **Estado:** Propuesta
- **Fecha:** 2026-10-26
- **Decisores:** Producto, Ingeniería y Operaciones
- **Relacionado con:** D-15, ADR-0006, ADR-0008, ADR-0009

## Contexto

Los emails transaccionales son parte del flujo crítico: confirmación de orden, envío, magic link, factura y dunning. Hoy no hay proveedor elegido ni dominio de envío. La dirección acordada es **identidad por tenant**: cada comercio debe poder enviar con su propio dominio o subdominio, sin que un tenant comprometa la reputación de los demás.

Restricciones:

- El stack de workers es **ARQ**, no Celery.
- Supabase Auth gestiona los magic links de staff y compradores; su SMTP debe configurarse con el proveedor elegido.
- Los emails contienen PII y deben cumplir D-10 (retención/región).
- La verificación DKIM/SPF/DMARC por tenant debe automatizarse; si el proveedor no lo permite por API, el onboarding se vuelve manual.

## Decisión

Se propone adoptar la opción A de D-15, con estas condiciones:

1. **Proveedor dedicado** (Resend o Postmark) elegido tras un spike de entregabilidad, webhooks y región. No SMTP propio.
2. **Identidad por tenant.** Cada tenant usa un dominio o subdominio verificado (`pedidos@tenant.growup.com` en el MVP; dominio propio en fase posterior) con DKIM/SPF/DMARC.
3. **Automatización del onboarding.** El alta del tenant genera los registros DNS necesarios y verifica el dominio por API; si el proveedor no lo soporta, se usa un dominio compartido como fallback temporal y se documenta.
4. **Aislamiento de reputación.** El dominio de la plataforma (`growup.com`) se reserva para auth, billing y alertas; los emails de compradores salen por la identidad del tenant.
5. **Worker ARQ** para envío asíncrono, reintentos, rebotes y quejas. Tabla de eventos de email para auditoría y supresión.
6. **Supabase Auth SMTP** configurado con el mismo proveedor para magic links, o se decide explícitamente que Auth use su propio canal.
7. **Retención y PII.** El cuerpo del email no se guarda en logs; se guardan metadatos y el ID del proveedor. Región alineada con D-10.

La elección Resend/Postmark y la estrategia definitiva de dominio por tenant quedan pendientes de spike.

## Alternativas consideradas

| Alternativa | Pros | Contras | ¿Por qué no? |
|---|---|---|---|
| Dominio compartido para todos | Simple y rápido | Reputación compartida; menos branding | Fallback, no objetivo |
| Subdominio por tenant con DKIM | Aislamiento y marca | Más operación y automatización | Es la dirección elegida |
| SMTP propio | Control total | Reputación, entregabilidad y operación | No recomendado |
| Solo Supabase Auth | Menos integración | No cubre órdenes/facturas/dunning | Insuficiente |

## Consecuencias

### Positivas

- Mejor entregabilidad y aislamiento entre tenants.
- Branding coherente en los emails del comercio.
- Reintentos y observabilidad desacoplados del request.

### Negativas / deuda asumida

- La verificación por tenant es más compleja que un dominio único.
- Hay que gestionar rebotes, quejas, supresión y reputación.
- El proveedor debe soportar la automatización; si no, el onboarding se frena.
- El coste y la región dependen del proveedor.

### Neutras

- Los magic links de Supabase Auth requieren configuración SMTP separada.

## Cómo se verifica

- Test de envío con dominio verificado y DKIM/SPF/DMARC en verde.
- Test de rebote/queja y lista de supresión.
- Test de idempotencia y reintentos del worker ARQ.
- Revisión de que los logs no contienen cuerpo ni destinatarios completos.

## Enlaces

- `docs/decisiones-pendientes (1).md` — D-15
- `docs/adr/0006-stack-satelite.md`
- `docs/adr/0008-topologia-despliegue.md`
- `docs/adr/0009-privacidad-dpa-dsr.md`
