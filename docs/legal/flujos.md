# Flujos legales

Diagramas de los cinco flujos que se discuten con el abogado. Todos son SVG editables, sin dependencias externas ni fuentes remotas: se ven igual en GitHub, en el navegador y en un PDF.

| Flujo | Pregunta que responde |
|---|---|
| [Reparto de roles](flujo-roles.svg) | ¿Quién vende, quién trata los datos y por dónde va el dinero? |
| [Ruta legal](flujo-ruta-legal.svg) | ¿En qué orden se cierran las decisiones y qué bloquea cada una? |
| [Onboarding legal](flujo-onboarding-legal.svg) | ¿Cómo acepta el DPA un comerciante y qué pasa si no acepta? |
| [Solicitud de un titular](flujo-dsr.svg) | ¿Qué se anonimiza y qué se conserva cuando alguien pide borrar sus datos? |
| [Brecha de datos](flujo-brecha.svg) | ¿Quién notifica, a quién y en qué plazo? |

---

## 1. Reparto de roles

![Reparto de roles entre comprador, tenant, Wompi y Growup](flujo-roles.svg)

Tres líneas separadas: la venta del comprador, los datos del pedido y la suscripción de la plataforma. El comerciante es el vendedor y el responsable de los datos; Growup es el proveedor tecnológico y el encargado, sin custodia de fondos.

## 2. Ruta legal

![Cuatro compuertas: entidad, onboarding, checkout y go-live](flujo-ruta-legal.svg)

Cada compuerta desbloquea la siguiente. Si la reunión se acorta a 45 minutos, solo se cubren las compuertas 0 y 1: sin DPA y sin términos no se puede firmar un comerciante.

## 3. Onboarding legal de un tenant

![Estados del tenant desde el alta hasta la publicación](flujo-onboarding-legal.svg)

El tenant nace en `pending_legal`. El dueño acepta el DPA con un clic, la aceptación se registra con versión, hash, timestamp e IP hasheada, y solo entonces se activa y publica. Sin aceptación no hay activación, y un cambio de versión obliga a aceptar de nuevo.

## 4. Solicitud de un titular (DSR)

![Flujo de una solicitud de derechos del titular](flujo-dsr.svg)

La decisión se toma por campo: lo que no es fiscal ni de auditoría se anonimiza; lo que sí lo es se conserva en su mínimo y se anonimiza el resto. La operación queda registrada aunque el dato desaparezca.

## 5. Brecha de datos

![Tres fases de respuesta a una brecha](flujo-brecha.svg)

Growup detecta, contiene y avisa al tenant. El tenant, como responsable, notifica a la autoridad y a los titulares. La plataforma entrega evidencia, no asume la notificación que no le corresponde.

---

## Cómo editarlos

- Los colores están en línea; no hay clases ni estilos externos.
- Paleta: tinta `#16181A`, plataforma `#2E5E4E`, comerciante `#B4553C`, comprador `#3C5A8A`, alerta `#C08A2E`, riesgo `#B4483A`.
- Tipografía: `Inter` con respaldo en `Segoe UI` y `system-ui`. No se carga ninguna fuente remota.
- Cada archivo tiene `viewBox`, `title` y `desc` para accesibilidad y para exportar a PDF sin perder nitidez.
