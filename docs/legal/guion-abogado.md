# Guion — reunión con el abogado

> **Cómo usar este documento:** imprímelo. Solo se lee literal la apertura (§3) y el cierre (§11). El resto son preguntas sueltas: hazlas en el orden escrito, no improvises el orden.
> **No es asesoría legal.** Es el guion de una conversación.
> **Acompaña a:** [`agenda-abogado.md`](agenda-abogado.md) y [`anexo-abogado.md`](anexo-abogado.md).

---

## 1. Cinco reglas para no salir con las manos vacías

1. **Habla en hechos, no en adjetivos.** "El comerciante cobra con su cuenta de Wompi" vale. "Es un SaaS innovador" no vale.
2. **Toda pregunta se contesta con binario o con fecha.** Si la respuesta es "depende", la siguiente pregunta es "¿de qué depende y cómo lo cerramos?".
3. **No dejes que rediseñe el negocio.** Si propone otro modelo, responde: *"Eso ya está decidido por producto. Lo que necesito es saber si el modelo actual es legal y cómo se documenta."*
4. **No firmes nada en la reunión.** Ni el DPA, ni una hoja de encargo, ni un "preliminar". Todo pasa por correo.
5. **Toma nota con nombre y fecha.** Cada tarea que salga se escribe como *quién / qué / para cuándo*.

---

## 2. Antes de entrar (5 minutos)

- [ ] Este guion impreso y el anexo.
- [ ] Diagrama del flujo abierto en pantalla.
- [ ] Lista de subencargados.
- [ ] RUT y matrícula mercantil.
- [ ] Cuaderno con tres columnas: **pregunta / respuesta / pendiente**.
- [ ] Reloj: 90 minutos, con alarma a los 75 para forzar el cierre.

Mentalidad: no vas a aprender derecho. Vas a **comprar cuatro documentos con fecha**. La conversación es una negociación de entregables.

---

## 3. Apertura (literal, 2 minutos)

> "Gracias por el tiempo. Te doy contexto en dos minutos porque de ahí depende todo lo demás, y después voy directo a las preguntas.
>
> Growup es un software para que un comerciante colombiano publique su tienda en línea. Nosotros no vendemos, no cobramos y no tocamos la plata del comprador. El comerciante abre su propia cuenta en Wompi, el comprador paga allá, y el dinero llega directo al comerciante. A nosotros nos paga una suscripción mensual por usar el software, con Stripe.
>
> En términos legales: el comerciante es el vendedor, es el responsable de los datos de sus compradores y es quien factura. Nosotros somos el proveedor tecnológico y el encargado del tratamiento de esos datos.
>
> Tenemos dos comerciantes piloto, ropa y joyería, y queremos lanzar en el primer trimestre de 2027.
>
> No vengo a que rediseñes el modelo. Vengo a que me digas si ese reparto se sostiene, y a salir con cuatro documentos: el DPA, los términos de la plataforma, la política de datos y el protocolo de brechas. Si el reparto no se sostiene, dímelo de una y paramos ahí."

**Después de decirlo, cállate.** Deja que responda él primero. Lo que diga en los siguientes treinta segundos te dice si la reunión va a servir.

---

## 4. Bloque 1 — Reparto de roles (10 min)

**Pregunta 1.**
> "Con ese reparto, ¿hay algún punto donde Growup deja de ser proveedor tecnológico y pasa a ser vendedor, intermediario o facilitador de pagos?"

**Pregunta 2.**
> "Guardamos las credenciales de Wompi de cada comerciante para crear el checkout. ¿Eso nos convierte en algo regulado por la Superfinanciera?"

**Pregunta 3.**
> "Si el comerciante es el vendedor, ¿la plataforma tiene alguna responsabilidad frente al comprador por lo que se publica en la tienda? Si la tiene, ¿cómo la acotamos en los términos?"

**Qué esperas oír:** que el reparto se sostiene, que guardar credenciales es custodia técnica y no custodia de fondos, y que la responsabilidad de la plataforma se limita con contrato.

**Si dice que no se sostiene:** para todo. No sigas a los otros bloques. Pregunta:
> "¿Qué habría que cambiar como mínimo para que se sostenga y que no implique rediseñar el producto?"

Anota la respuesta y vuelve al equipo antes de decidir nada.

**Si empieza a hablar de marketplace o de split:** interrumpe con respeto:
> "Eso es fase 2. Hoy no hay comisión ni custodia. Anótalo como gatillo de reapertura, no como parte de esta reunión."

---

## 5. Bloque 2 — Forma jurídica y titularidad (15 min)

**Apertura del bloque:**
> "El proyecto está hoy a nombre de una persona natural. Vas a firmar el DPA y los términos. ¿Qué recomiendas: seguir así o constituir una SAS?"

**Si dice SAS:**
> "¿Unipersonal o con socio? Hoy el proyecto es mío. Si entra un socio, ¿qué cambia?"

**Si dice que la persona natural sirve:**
> "¿Qué pasa si firmamos el DPA como persona natural y en seis meses constituimos la SAS? ¿Hay que volver a firmar todo? ¿Tiene algún costo tributario pasar los contratos, la cuenta de Wompi, el dominio y la marca?"

**Pregunta de titularidad (no la omitas):**
> "¿La marca, el dominio y el código deben estar en la sociedad? Si están a mi nombre, ¿qué riesgo tiene para los comerciantes o para un inversionista futuro?"

**Pregunta sobre el código heredado:**
> "Parte del código viene de un proyecto anterior mío. ¿Qué necesito para que la sociedad pueda usarlo sin riesgo de que un tercero lo reclame?"

**Pregunta de trámite:**
> "¿La constitución se puede hacer por documento privado en línea en la Cámara de Comercio, sin notaría?"

**Qué esperas oír:** una recomendación binaria y el costo de migrar después.

**Regla:** si no hay claridad en cinco minutos, pide que te lo mande por escrito:
> "Esto es una decisión, no una opinión. ¿Me la dejas por escrito esta semana con la ruta y el costo?"

---

## 6. Bloque 3 — DPA (15 min)

**Apertura:**
> "Vamos al documento que nos bloquea el lanzamiento. Somos encargados y el comerciante es responsable."

**Preguntas, en este orden:**

1. > "¿Bajo la Ley 1581 y el Decreto 1377 ese reparto es correcto, o hay matices cuando nosotros definimos qué campos captura el checkout?"
2. > "¿Sirve un DPA plantilla aceptado con un clic en el primer ingreso del dueño, o necesitas firma? ¿Qué evidencia hay que guardar para que aguante una disputa?"
3. > "¿Qué tiene que decir el DPA sí o sí: finalidad, seguridad, subencargados, transferencia internacional, auditoría, devolución o supresión al terminar?"
4. > "Te paso la lista de subencargados. ¿Cómo se autorizan y qué pasa cuando cambiamos uno?"
5. > "¿Qué tope de responsabilidad es razonable y a la vez exigible por un comerciante?"
6. > "¿Basta en español o necesitamos inglés?"

**Si dice que el DPA de Wompi cubre esto:**
> "El de Wompi cubre mi relación con Wompi. El de mis comerciantes es otro contrato: ellos me entregan datos de sus compradores y yo los proceso. Son dos relaciones distintas."

**Si dice que basta una cláusula en los términos:**
> "Eso es la opción C de nuestra evaluación y la descartamos porque no cumple el contrato específico de encargado. ¿Estás de acuerdo o tienes un argumento distinto?"

---

## 7. Bloque 4 — Términos de la plataforma (10 min)

1. > "Necesito una cláusula que diga que el comerciante es el vendedor y responsable de IVA, factura, garantías y contracargos. ¿Cómo la redactas para que aguante un cobro revertido?"
2. > "¿Cómo limitamos la responsabilidad por el contenido, los precios y el inventario del comerciante?"
3. > "Si el comerciante no paga la suscripción, ¿puedo suspender la tienda? ¿Puedo retener sus datos hasta que pague?"
4. > "¿De quién es el contenido que el comerciante sube y qué licencia necesitamos para alojarlo y mostrarlo?"
5. > "¿Qué productos o categorías deberíamos prohibir desde el primer día?"

**Qué esperas oír:** cláusulas concretas, no principios. Si te da principios, pide el texto:
> "¿Me lo pasas redactado como cláusula? Yo no puedo implementar un principio."

---

## 8. Bloque 5 — Aceptaciones y evidencia (5 min)

1. > "Vamos a aceptar el DPA con un clic en el primer ingreso del dueño. ¿Es válido bajo la Ley 527? ¿Qué hay que guardar: versión, hash, fecha, IP?"
2. > "¿La IP se guarda completa o hasheada? Nos preocupa la minimización de datos."
3. > "¿Cuánto tiempo conservamos la aceptación?"

---

## 9. Bloque 6 — Datos, retención y brechas (15 min)

1. > "¿Tenemos que registrar las bases de datos ante la SIC? Somos dos comerciantes y probablemente no llegamos al umbral, pero quiero confirmarlo."
2. > "El comprador puede comprar como invitado. ¿Qué aviso y qué aceptación necesita? ¿Basta el aviso en el checkout?"
3. > "Necesito una matriz de retención por tipo de dato: orden, factura, logs, correos, soporte. ¿Qué plazos son obligatorios y cuáles los definimos nosotros?"
4. > "Tenemos una bitácora de auditoría que no se puede borrar. Si un comprador pide que borren sus datos, ¿qué se anonimiza y qué se conserva por obligación fiscal?"
5. > "¿En cuánto tiempo hay que responder una solicitud de un titular?"
6. > "¿Colombia exige que los datos estén en Colombia? Trabajamos con Supabase, Fly y un proveedor de correo."
7. > "Si hay una brecha: ¿a quién notificamos, en qué plazo y con qué formato? Las 72 horas que conozco son de GDPR, no de Colombia, y quiero el deber real."
8. > "¿Cómo repartimos esa notificación con el comerciante? Nosotros somos encargados; él es responsable."

**Si dice "eso es GDPR":**
> "Hoy vendemos en Colombia y no ofrecemos a la Unión Europea. ¿GDPR aplica igual? Si no aplica, no quiero pagar compliance que no necesito. Si aplica por el proveedor de nube, quiero saber qué parte."

**Qué esperas oír:** plazos concretos, no "hay que revisar".

---

## 10. Bloque 7 — Consumidor, devoluciones y DIAN (10 min)

1. > "¿Quién responde frente al comprador: el comerciante solo, o también nosotros por publicar la tienda?"
2. > "¿Qué tiene que decir la política de devoluciones? Retracto, reversión del pago, garantía legal, plazos."
3. > "¿Podemos dar una plantilla y dejar que el comerciante la edite? ¿Con qué límites para que no la deje incumpliendo?"
4. > "En facturación: el comerciante factura. Si nosotros contratamos al proveedor certificado y emitimos por él, ¿nos volvemos proveedores tecnológicos ante la DIAN?"
5. > "Si hay un reembolso después de facturar, ¿quién y cómo emite la nota crédito?"

**Si se desvía a IVA del envío o a elegir proveedor DIAN:**
> "Eso lo cierra el contador. Lo dejo fuera de esta reunión."

---

## 11. Cierre (literal, 5 minutos)

> "Con esto me basta. Antes de terminar necesito concretar cuatro cosas: qué entra en cada documento, quién lo redacta, para cuándo y cuánto cuesta.
>
> Prefiero precio por entregable y no por hora, para poder planear. ¿Me puedes dejar la propuesta por escrito esta semana?
>
> Y una última: si tenemos un incidente de datos, ¿tienes disponibilidad fuera de horario? ¿Eso está cubierto en el mismo contrato o es aparte?"

**Luego, en voz alta, repite el resumen:**
> "Entonces quedamos en: DPA para el viernes, términos la semana siguiente, política de datos y matriz de retención al mismo tiempo, y protocolo de brechas después. ¿Correcto?"

No cuelgues hasta que él diga "correcto" o corrija las fechas.

---

## 12. Manejo de objeciones

| Si dice… | Respondes… |
|---|---|
| "Esto es muy pronto, primero factura." | "Entiendo. ¿Qué es lo mínimo para poder firmar el primer comerciante sin quedar expuesto? Eso es exactamente lo que quiero comprar." |
| "Necesito ver la arquitectura." | "Te paso el diagrama y el modelo de datos. Pero la decisión no depende de la arquitectura: depende de quién vende y quién trata los datos." |
| "GDPR aplica." | "¿Aplica si no ofrecemos a la UE? Si no, dime por qué, porque no quiero pagar compliance que no necesito." |
| "El DPA de Wompi ya cubre eso." | "Cubre mi relación con Wompi. La de mis comerciantes es otra relación y otro contrato." |
| "Mejor una SAS con socios." | "Hoy el proyecto es mío. Si entra un socio, ¿qué cambia y qué documento hace falta el día que entre?" |
| "Te cobro por hora." | "Prefiero precio cerrado por entregable. ¿Puedes darme un rango por documento y un máximo?" |
| "Eso lo decide un contador." | "De acuerdo. ¿Me lo dejas escrito para llevárselo al contador con la pregunta exacta?" |
| "Hay que revisar la norma." | "¿Cuánto tarda la revisión y cuánto cuesta? Lo pongo en el calendario." |

---

## 13. Señales de alerta

Corta la reunión o cambia de abogado si:

- No pregunta **quién cobra el dinero**. Es la primera pregunta de cualquier abogado serio en e-commerce.
- Recomienda GDPR sin preguntar en qué países hay compradores.
- Propone que la plataforma cobre y liquide a los comerciantes "para simplificar".
- Da un precio "todo incluido" sin haber leído el modelo.
- No puede nombrar la Ley 1581 ni el Estatuto del Consumidor.
- Te pide firmar una hoja de encargo en la misma reunión.

---

## 14. Email de seguimiento (enviar el mismo día)

> Asunto: Resumen y acuerdos — reunión [fecha]
>
> [Nombre], gracias por el tiempo.
>
> Resumen de lo acordado:
>
> 1. [Documento] — responsable: [ ] — fecha: [ ]
> 2. [Documento] — responsable: [ ] — fecha: [ ]
> 3. [Documento] — responsable: [ ] — fecha: [ ]
>
> Preguntas que quedaron abiertas: [lista].
>
> Precio acordado: [ ] por entregable / [ ] por hora con máximo de [ ].
>
> Si algo de esto no coincide con lo que entendiste, corrígeme por este medio antes del [fecha].
>
> Gracias.

Si no contesta en 48 horas, reenvía el mismo correo con una línea: *"¿Puedes confirmarme las fechas para poder planear el lanzamiento?"*

---

## 15. Acta mínima (llenar antes de salir del edificio)

| Campo | Qué escribir |
|---|---|
| Fecha y hora | |
| Abogado y firma | |
| ¿El reparto de roles se sostiene? | Sí / No / Condicionado a |
| Forma jurídica recomendada | Persona natural / SAS / Pendiente |
| Documentos comprometidos | |
| Fechas comprometidas | |
| Precio | |
| Riesgos que mencionó | |
| Preguntas sin responder | |
| Próxima reunión | |

---

## 16. Qué hago con esto después

1. Pasar las respuestas a `docs/decisiones-pendientes (1).md` con fecha y responsable.
2. Cambiar el estado de D-09, D-10, D-12 y D-13 solo si el abogado lo aprobó por escrito.
3. Crear `docs/adr/0012-forma-juridica-y-titularidad.md` si se decide SAS.
4. Guardar las plantillas en `docs/legal/` con versión y hash (lo exige ADR-0009).
5. Actualizar la agenda con lo que quedó pendiente para la segunda reunión.
