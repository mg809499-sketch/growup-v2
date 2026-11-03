# Anexo — una página para enviar 48 h antes

> Adjuntar a la invitación. El abogado debe leerlo antes de la reunión; si no lo leyó, se lee en voz alta al inicio.
> No sustituye la reunión: la hace más corta.

---

## Qué es Growup

Software para que un comerciante colombiano publique su tienda en línea. La plataforma no vende, no cobra y no custodia fondos. El comerciante conecta su propia cuenta de Wompi, el comprador paga allá y el dinero llega directo al comerciante. Growup cobra una suscripción mensual por el software.

Piloto: dos comerciantes (ropa y joyería). Lanzamiento objetivo: Q1 2027.

## Flujo

```text
comprador
   │  compra
   ▼
storefront del tenant  ──►  Wompi (cuenta del tenant)  ──►  dinero al tenant
   │                                   │
   │ datos del pedido                  │ webhook firmado
   ▼                                   ▼
Growup (encargado)  ◄──────────────  orden pagada
   ▲
   │ suscripción mensual
   │
tenant  ──►  Stripe (cuenta de Growup)
```

## Reparto de roles

| Rol | Quién |
|---|---|
| Vendedor frente al comprador | El comerciante |
| Responsable de datos (*controller*) | El comerciante |
| Encargado del tratamiento (*processor*) | Growup |
| IVA, factura DIAN, garantías, retracto, contracargos | El comerciante |
| Proveedor tecnológico | Growup |

**Growup no es marketplace facilitator, no es intermediario fiscal y no custodia fondos.**

## Subencargados

Supabase (base de datos y auth) · Vercel (storefront) · Cloudflare (DNS, CDN, R2) · Fly.io (API y workers) · Resend o Postmark (correo transaccional) · Wompi (pagos del comprador) · Stripe (suscripción de la plataforma).

## Qué se decide en la reunión

| ID | Tema | Recomendación actual |
|---|---|---|
| D-09 | DPA plataforma ↔ comerciante | Plantilla + clickwrap del dueño + registro versionado |
| D-10 | Retención, derechos del titular y residencia | Flujo manual auditado, anonimización por campo, una sola región |
| D-12 | Notificación de brechas | Responsable, plazos y plantillas |
| D-13 | Política de devoluciones | Plantilla de plataforma editable por el comerciante |
| D-03 | Nota crédito tras reembolso | Definir si la emite el proveedor certificado o es manual |

## Qué se pide como resultado

1. DPA en borrador.
2. Términos y condiciones de la plataforma en borrador.
3. Política de tratamiento de datos.
4. Plantilla de política de devoluciones.
5. Matriz de retención por tipo de dato.
6. Protocolo de notificación de brechas.

Cada entregable con fecha y precio.

## Fuera de alcance

IVA del envío, proveedor DIAN, PCI/SAQ, SOC 2 y arquitectura técnica. Tienen otro responsable.

## Contexto societario

El proyecto está hoy a nombre de una persona natural. La primera pregunta de la reunión es si eso sirve para firmar el DPA y los términos, o si hay que constituir una SAS antes.
