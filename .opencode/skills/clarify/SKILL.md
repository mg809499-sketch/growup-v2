---
id: clarify
name: clarify
description: Resolución estructurada de ambigüedades antes de implementar. Desvía decisiones de negocio a docs/decisiones-pendientes.md y técnicas a docs/adr/. Nunca asume en silencio.
---

# clarify — Resolución estructurada de ambigüedades

## Propósito

Detectar ambigüedades en requirements/spec antes de tocar código y resolverlas de forma estructurada, sin asumir decisiones de negocio en silencio (regla dura del repo).

## Cuándo se dispara

- Al iniciar una feature o cuando un requerimiento tiene términos vagos ("según corresponda", "de forma razonable", "configurable").
- Antes de escribir cualquier endpoint, migración, schema o componente.
- Cuando requirements.md, design.md o tasks.md dejan abierta una elección que afecte al comportamiento.

## Entradas

- `docs/decisiones-pendientes.md` — registro de decisiones de negocio abiertas/cerradas.
- `docs/adr/` — decisiones de arquitectura aceptadas.
- El spec/requirements de la feature en curso.

## Flujo

1. **Inventariar ambigüedades.** Listar cada término o elección sin definir que afecte al comportamiento del sistema.
2. **Clasificar por tipo:**
   - **Negocio** (precio, moneda, alcance MVP, dominios, facturación): desviar a `docs/decisiones-pendientes.md`. No se asume. Si la decisión ya está cerrada, aplicar la respuesta registrada.
   - **Técnica/arquitectura** (stack, RLS, tenancy, pagos): buscar ADR vigente. Si no hay ADR, registrar como propuesta o consultar.
   - **Seguridad** (RLS, secrets, PII, webhooks): aplicar reglas de seguridad y consultar si hay conflicto.
   - **UX/diseño** (storefront): aplicar dirección de producto y storefront.
3. **Decidir o consultar.** Si hay una respuesta cerrada en decisiones-pendientes o ADR, aplicarla. Si no, plantear al usuario las opciones con implicaciones y pedir una elección explícita. No inventar.
4. **Registrar.** Cerrar la ambigüedad con fecha, responsable y, si cambia la arquitectura, crear o actualizar un ADR. Actualizar reglas permanentes si afecta reglas del repo.
5. **Bloquear hasta resolver.** No implementar lo que depende de una ambigüedad sin resolver.

## Salida

- Lista de ambigüedades detectadas con clasificación.
- Para cada una: decisión aplicada (con referencia a decisiones-pendientes/ADR) o pregunta al usuario con opciones.
- Estado de bloqueo: qué tareas quedan bloqueadas pendiente de decisión.

## Integración con growup

- `docs/decisiones-pendientes.md` ya cumple la función de registro de decisiones de negocio; clarify no duplica esa lógica, solo la invoca y obliga a consultarla antes de implementar.
- Los ADR en `docs/adr/` usan la plantilla `docs/adr/0000-template.md`.
