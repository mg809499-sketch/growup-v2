# Paquete de plan — Growup (auditoría → ejecución completa)

Fecha: 2026-11-10 · Origen: auditoría completa 2026-11-10 · Objetivo: cerrar todos los pendientes y llevar Growup al piloto ropa+joyería (Q1 2027).

## Documentos

1. **`plan-maestro-growup.md`** — Estado real, principios, fases F0–F7, tareas con IDs y DoD, dependencias, cronograma (~16–22 semanas), riesgos, métricas y protocolo de actualización.
2. **`decisiones-proveedores-growup.md`** — Cierre de D-01..D-18 derivados, ADR-0005/0009/0010/0011, región (sa-east-1) y stack de observabilidad. Cada elección: proveedor, justificación de eficiencia, alternativa rechazada y gate de ratificación (abogado/contador/equipo).
3. **`guias-pendientes-growup.md`** — Guías ejecutables paso a paso: ratificación de decisiones, Dockerfile/Supabase/Vercel/Cloudflare/Fly, CI/CD con seguridad, observabilidad, hardening, builder/contenido, Wompi, DIAN/Factus, Stripe Billing, Resend, DPA/DSR/brecha/soporte, seed, Playwright, B-03, go-live y plantillas de revisión.
4. **`sincronizacion-frontend-apps-docker.md`** — Especificación ejecutable de todos los cambios en `apps/storefront`, `apps/admin`, `packages/contracts|config`, borrado de zombies, `infra/docker-compose.yml` endurecido, Dockerfiles API/worker, fly.toml, variables de entorno y CI/CD extendido, con criterio de "sincronizado" verificable.
5. **`suite-publica-growup.md`** — Plan FINAL (decisiones DEC-1…DEC-7 ratificadas 2026-11-10) de la suite pública `apps/web`: growup.com con dirección v0, planes sin precios, consola, 8 servicios MVP y contenido editorial honesto.

## Estado de implementación (2026-11-10)

- **`apps/web` implementado y verificado**: 19 rutas SSG (home Welcome con dirección v0, `/planes` con carrusel + modal accesible sin precios, `/servicios` con 8 sub-páginas SSG, `/consola`, `/solicitar-acceso`), `lint`/`tsc`/`next build` en verde, servido y verificado por HTTP (sin precios visibles en público, acentos correctos). Ver `apps/web/README.md`.

## Decisiones clave propuestas (resumen)

| Eje | Elección |
|---|---|
| Región | sa-east-1 (São Paulo): Supabase + Fly (gru) + Upstash |
| DNS/WAF | Cloudflare free (wildcard Vercel, API tras proxy naranja) |
| Email | Resend (subdominio por tenant `mail.{slug}`, ARQ) |
| DIAN | Factus (adaptador aislado; fallback Alegra) |
| Checkout | Wompi hosted redirect → SAQ A |
| Suscripción plataforma | Stripe Billing (fallback MercadoPago preapproval) |
| Observabilidad | Sentry + OTel → Grafana Cloud Free |
| Planes | Starter COP 49.000 · Pro COP 129.000 · trial 14 días |

## Cómo usar el paquete

1. Ejecutar la sesión **G-F0** (ratificación) con abogado/contador/equipo; editar `docs/decisiones-pendientes.md` in situ.
2. Seguir fases F0→F6 en orden; cada tarea tiene DoD; nada avanza dependencias sin cerrar su gate.
3. Actualizar el progreso marcando checkboxes en `plan-maestro-growup.md` vía PR.
4. Mantener evidencia (pgTAP/E2E/Trivy/logs) en cada PR; sin evidencia, no hay merge.

## Advertencias honestas

- Las decisiones legales (D-09/D-10/D-11/D-12/D-13, textos del abogado) y fiscales (D-06 envío, IVA de suscripción, precios de plan) **no pueden ser cerradas por ingeniería**: requieren firma profesional. El plan propone valores por defecto y congela el trabajo dependiente hasta la firma.
- Scope "tipo Shopify" completo supera la capacidad de 2 personas antes del piloto; todo lo excedente está explícito como fase 2 en el plan maestro §10.
- Wompi/Stripe/Factus/Resend en sandbox deben crearse en F0-08; sin cuentas, F4 no inicia.

## Siguiente paso

F0 (decisiones) → F1/F2 → piloto ropa+joyería. La suite pública (`apps/web`) está implementada; falta publicarla en Vercel (proyecto `growup-web`, apex `growup.com`) tras ratificar D-01 y obtener el permiso de los pilotos para los testimonios.
