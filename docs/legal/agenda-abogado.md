# Agenda — reunión con abogado

> **Estado:** borrador de trabajo · **Última actualización:** 2026-11-03
> **Objetivo:** salir de la reunión con entregables fechados, no con opiniones.
> **No es asesoría legal.** Es la preparación de la reunión; los plazos y umbrales se confirman con el abogado y el contador.
> **Para hablar:** [`guion-abogado.md`](guion-abogado.md). **Para enviar antes:** [`anexo-abogado.md`](anexo-abogado.md).
> **Origen:** D-09 a D-16 en [`decisiones-pendientes (1).md`](../decisiones-pendientes%20(1).md), ADR-0004, ADR-0009, ADR-0010, ADR-0011.

---

## 1. Encuadre (leer en voz alta al inicio, 2 min)

Growup es un SaaS multi-tenant: un comerciante crea su tienda, publica su catálogo y vende en su subdominio. La plataforma **no vende, no cobra y no custodia fondos**: el comerciante es el *merchant of record* y usa su propia cuenta de Wompi. La plataforma cobra una suscripción mensual por el software.

Eso define el reparto legal desde el minuto uno:

| Rol | Quién |
|---|---|
| Vendedor frente al comprador | El comerciante (tenant) |
| Responsable de datos de compradores (*controller*) | El comerciante |
| Encargado del tratamiento (*processor*) | Growup |
| Responsable de IVA, factura DIAN, garantías y chargebacks | El comerciante |
| Proveedor tecnológico | Growup |

Si el abogado está de acuerdo con ese reparto, todo lo demás se redacta encima. Si no, esa es la primera discusión de la reunión y hay que resolverla antes de seguir.

---

## 2. Antes de la reunión (enviar 48 h antes)

- [ ] Este documento.
- [ ] Diagrama corto: `host → tenant → storefront → Wompi → webhook → orden`.
- [ ] Lista de subencargados: Supabase, Vercel, Cloudflare, Fly.io, R2, Resend, Wompi, Stripe.
- [ ] Las cuatro decisiones abiertas con la opción recomendada marcada: D-09, D-10, D-12, D-13.
- [ ] Documentos de la persona natural: RUT, matrícula mercantil, cámara de comercio.
- [ ] Contrato o términos estándar de Wompi y Stripe, si ya los tienes.

Pedir explícitamente que **no** proponga un modelo distinto de negocio: la arquitectura ya está decidida (D-02, D-17) y lo que se busca es validar su legalidad, no rediseñarla.

---

## 3. Agenda de 90 minutos

### 0–10 min · Contexto y modelo

| Pregunta | Para qué |
|---|---|
| ¿Está bien el reparto de roles de la tabla anterior? | Base de todo el resto |
| ¿Hay algún punto donde Growup deja de ser "proveedor tecnológico" y pasa a ser comerciante, intermediario o facilitador de pagos? | Delimita responsabilidad y evita regulación no prevista |

**Decisión que desbloquea:** ninguna todavía. Si la respuesta es "no", se detiene y se replantea el modelo.

---

### 10–25 min · Forma jurídica y titularidad

| Pregunta | Entregable | Bloquea |
|---|---|---|
| ¿Persona natural o SAS para firmar DPA, ToS, Wompi y Stripe? | Recomendación escrita con razones | Wave 1 |
| ¿SAS unipersonal o con socio? Si hay socio: ¿pacto de socios y vesting? | Borrador de pacto de socios | Nada técnico; sí la relación entre fundadores |
| ¿La marca "Growup", el dominio y el código deben quedar en la SAS? | Lista de activos a titularizar | Due diligence futura |
| ¿El código portado desde `../multitiendas` tiene cesión o licencia válida? | Constancia de titularidad o advertencia | Publicación del storefront |
| ¿Constitución por documento privado en línea, sin notaría? | Ruta y costo del trámite | Nada técnico |

**Decisión que desbloquea:** D-09 y D-10 no se pueden firmar sin una contraparte con patrimonio.

---

### 25–50 min · Contratos con el comerciante (el corazón)

**a) DPA plataforma ↔ tenant (D-09)**

| Pregunta | Entregable |
|---|---|
| ¿Growup es *encargado* y el tenant *responsable* bajo Ley 1581/2012 y Decreto 1377/2013? | Confirmación o matices |
| ¿Basta clickwrap del owner o se exige firma? ¿Qué evidencia aguanta una disputa? | Mecanismo de aceptación |
| ¿Qué cláusulas son obligatorias: finalidad, seguridad, subencargados, transferencia internacional, auditoría, devolución/supresión? | Plantilla de DPA |
| ¿Cómo se listan y autorizan los subencargados? | Anexo de subencargados |
| ¿Tope de responsabilidad e indemnidad recíproca? | Cláusulas |
| ¿La plantilla debe ir en español, inglés o ambos? | Versión |

**b) Términos y condiciones de la plataforma**

| Pregunta | Entregable |
|---|---|
| ¿Cómo se redacta que el comerciante es el vendedor y responsable de IVA, factura, garantías y chargebacks? | Cláusula |
| ¿Cómo se limita la responsabilidad de Growup por contenido, precios e inventario del tenant? | Cláusula |
| Suspensión por impago, terminación, exportación de datos y licencia del contenido del tenant | Cláusulas |
| Uso aceptable y productos prohibidos | Anexo |

**c) Aceptaciones legales (ADR-0009)**

| Pregunta | Entregable |
|---|---|
| ¿Es válido el clickwrap con versión, hash, timestamp e IP hasheada? | Esquema de evidencia |
| ¿Cuánto tiempo se conservan las aceptaciones? | Plazo |

**Decisión que desbloquea:** D-09. Sin esto no hay onboarding.

---

### 50–65 min · Datos personales, retención y brechas

| Pregunta | Entregable | Bloquea |
|---|---|---|
| ¿Aplica el Registro Nacional de Bases de Datos (RNBD) ante la SIC? ¿Con qué umbral? | Sí/no y trámite | Go-live |
| ¿Qué autorización necesita el checkout invitado (D-04) para tratar datos del comprador? | Texto de aviso y aceptación | Checkout |
| Matriz de retención por tipo de dato: orden, factura, logs, emails, soporte | Matriz | D-10 |
| ¿Qué se anonimiza y qué se conserva por obligación fiscal? | Regla por campo | D-10 |
| Plazo legal para responder un DSR | Plazo | D-10 |
| ¿Colombia exige residencia local de datos? ¿Qué implica transferir a Supabase/Fly/Resend? | Postura | D-10, D-07 |
| Deber aplicable de notificación de brechas ante autoridades y titulares, según jurisdicción y roles | Protocolo y plazos | D-12 |
| ¿Cómo se reparte la notificación entre Growup (encargado) y tenant (responsable)? | Cláusula + runbook | D-12 |

**Decisión que desbloquea:** D-10 y D-12.

---

### 65–80 min · Consumidor, devoluciones y DIAN

| Pregunta | Entregable | Bloquea |
|---|---|---|
| ¿Quién responde frente al comprador: solo el tenant o también la plataforma que publica la tienda? | Postura | D-13 |
| Textos obligatorios: retracto, reversión del pago, garantía legal, información de precios | Plantilla de política | D-13 |
| ¿La plantilla es editable por el tenant? ¿Con qué campos acotados? | Estructura de campos | D-13 |
| ¿Quién es el emisor de la factura: el tenant? Si Growup contrata al proveedor certificado, ¿se vuelve "proveedor tecnológico" ante la DIAN? | Postura | D-03 |
| ¿Cómo se emite la nota crédito en refund o chargeback posterior a la factura? | Flujo | D-03 |

**Decisión que desbloquea:** D-13 y el pendiente de nota crédito de D-03.

---

### 80–90 min · Cierre

- [ ] Entregables acordados, cada uno con **responsable y fecha**.
- [ ] Honorarios: por entregable o por hora; qué incluye la revisión posterior.
- [ ] Disponibilidad para un incidente de datos (fuera de horario).
- [ ] Quién revisa cuando cambie una plantilla y con qué aviso.
- [ ] Fecha de la segunda reunión.

---

## 4. Si solo hay 45 minutos

Orden de corte, de arriba hacia abajo:

1. Forma jurídica y titularidad (bloque 10–25).
2. DPA + ToS (bloque 25–50).
3. Todo lo demás se agenda aparte.

Sin 1 y 2 no se puede firmar un tenant. Lo demás puede esperar a Wave 4.

---

## 5. Lo que NO se le pregunta

| Tema | Quién |
|---|---|
| IVA sobre el envío, redondeos, retenciones (D-06) | Contador |
| Selección y contrato del proveedor DIAN (D-03) | Contador + proveedor |
| Nivel SAQ, ASV scan, scripts de checkout (D-11) | QSA / seguridad |
| SOC 2 (D-18) | Auditor, cuando haya demanda enterprise |
| Arquitectura, RLS, checkout, elección de Wompi | Ingeniería (ya decidido) |

---

## 6. Decisiones que no se reabren

Están cerradas y solo se pide validación de legalidad, no rediseño:

| ID | Decisión |
|---|---|
| D-01 | Suscripción mensual, trial 14 días, 0 % comisión en MVP |
| D-02 | Merchant of record = tenant; Wompi checkout; Stripe billing; sin custodia |
| D-05 | MVP comercial; returns/RMA e IA diferidos |
| D-06 | COP, IVA 19 % incluido, montos en centavos |
| D-17 | Growup no es marketplace facilitator ni intermediario fiscal |

Si el abogado encuentra un problema de legalidad en alguna, se registra y se reabre formalmente; no se cambia en la reunión.

---

## 7. Después de la reunión

1. Escribir las respuestas en `docs/decisiones-pendientes (1).md` con fecha y responsable.
2. Cambiar el estado de D-09, D-10, D-12, D-13 según corresponda.
3. Crear `docs/adr/0012-forma-juridica-y-titularidad.md` si se decide SAS.
4. Actualizar `.kiro/steering/` solo si cambia una regla permanente.
5. Guardar las plantillas en `docs/legal/` con versión y hash (ADR-0009 lo exige).

---

## 8. Anexo — datos que el abogado va a pedir

- [ ] RUT y matrícula mercantil de la persona natural.
- [ ] Cámara de comercio y representación legal.
- [ ] Socios, porcentajes y aportes (si hay SAS).
- [ ] Dominio y marca: quién es el titular hoy.
- [ ] Contratos con Supabase, Vercel, Cloudflare, Fly, R2, Resend, Wompi, Stripe.
- [ ] Flujo de dinero exacto: quién cobra, a quién, en qué moneda.
- [ ] Países donde habrá compradores (define si GDPR/CCPA aplican).
- [ ] Si ya hay compradores reales y qué datos se capturan hoy.

---

## 9. Cómo saber si la reunión sirvió

La reunión sirvió si sales con:

- [ ] Una respuesta binaria sobre la forma jurídica.
- [ ] Un DPA en borrador con fecha de entrega.
- [ ] Un ToS en borrador con fecha de entrega.
- [ ] Una matriz de retención en borrador.
- [ ] Un protocolo de brechas con plazos.
- [ ] Un precio y un calendario.

Si sales solo con "hay que revisar", la reunión no sirvió.
