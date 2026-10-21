# ARQUITECTURA DE SOFTWARE E-COMMERCE MULTITIENDA ENTERPRISE V2
## Plataforma de Comercio Electrónico Inteligente Cordiasolve
**Modelo:** Híbrido Shopify Core + WordPress Customizer  
**Enfoque:** Screaming Architecture, Spec-Driven Development (SDD), Gobernanza Cognitiva WaitOps & Resiliencia Enterprise  
**Fecha:** Octubre 2026  

---

## 🗺️ Mapa Global de la Arquitectura (Con 10 Componentes Integrados)

```text
                                  [ CLIENTE FINAL / COMERCIANTE / AGENTE IA ]
                                                       │
                                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. ENTORNO DE GESTIÓN Y FLUJO DE TRABAJO (3 NIVELES STRATEGIC-TACTICAL-OPERATIONAL)          │
│  • Notion (Estratégico)    : Portafolio de proyectos, presupuestos y WIP Limit (Máx 1).      │
│  • GitHub Projects (Táctico): Tablero Kanban por Olas (Waves), Tenants y Layers.             │
│  • Kiro IDE (Operativo)    : Desarrollo SDD (.kiro/specs/), Steering y Hooks de código.      │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                                       │
                                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. PRESENTACIÓN, RENDERIZADO & MULTIMEDIA (NEXT.JS 16 + EDGE CDN)                            │
│  • Storefront Engine (RSC + PPR): Renderizado dinámico en < 1s leyendo esquemas JSONB.        │
│  • Admin Customizer Builder     : Editor Drag-and-Drop tipo WordPress para comerciantes.     │
│  • Tenant Detector Middleware   : Inyección dinámica de cabecera X-Tenant-ID.                │
│  • [Componente 1] S3 & Media CDN: Storage S3 (Cloudflare R2) + Optimización On-the-Fly (WebP) │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                                       │ (API REST / Async Requests)
                                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. BACKEND & SCREAMING ARCHITECTURE (FASTAPI PYTHON 3.12)                                    │
│  ├── /tenants        : Aislamiento multi-tienda y gestión de subdominios.                    │
│  ├── /theme_builder  : Validación Pydantic v2 de JSONB e índices GIN.                         │
│  ├── /catalog        : Ropa (Variantes) / Joyería (Serialización 1 de 1) + Stock determinista.│
│  ├── /checkout       : Carrito 1-paso, reserva temporal pesimista anti-sobreventas.          │
│  ├── /orders         : Facturación electrónica y Cierres Mensuales Contables.                │
│  ├── [Módulo 402]    : Middleware HTTP 402 (Micropagos L402 / WebLN) para APIs y Agentes IA. │
│  ├── [Componente 2] Búsqueda Dedicada: Meilisearch / Typesense (Fuzzy Search < 10ms).        │
│  └── [Componente 3] Asincronía & Event Bus: Redis + Celery / NATS (Tareas pesadas fuera HTTP)│
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                                       │
                                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ 4. GOBERNANZA COGNITIVA, OBSERVABILIDAD & RESILIENCIA DE IA                                  │
│  • Axioma Central      : "La IA recomienda, las reglas deciden".                             │
│  • Compuerta Cedar/Rego: Evaluación binaria determinista (pass/fail) de precios/descuentos.  │
│  • [Componente 4] Observabilidad: OpenTelemetry + Sentry + LangFuse/Helicone (Trazabilidad)  │
│  • [Componente 5] Resiliencia & FinOps: Circuit Breakers + Budget Caps en uso de LLMs/APIs.  │
│  • Audit Trail         : Log inmutable en ai_audit_logs con firmas criptográficas.           │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                                       │
                                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ 5. CAPA DE DATOS E INFRAESTRUCTURA RELACIONAL & CACHÉ                                        │
│  • PostgreSQL + Supabase RLS : Variable de sesión app.current_tenant = tenant_id.            │
│  • Tablas e Índices GIN      : Columnas JSONB para temas gráficos y catálogos.              │
│  • Redis In-Memory           : Caché de sesiones, colas de trabajo y bloqueos de stock.      │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Desglose Detallado de los 5 Nuevos Componentes Integrados

### 1. Asincronía y Procesamiento en Segundo Plano (Redis + Celery / NATS)
* **Propósito:** Desacoplar la ejecución de tareas pesadas del hilo de atención síncrono de FastAPI para garantizar tiempos de respuesta de API inferiores a 100 ms.
* **Mecanismo:**
  * Las peticiones HTTP entrantes solo realizan validaciones inmediatas y publican eventos de dominio (`order.created`, `invoice.generate`, `whatsapp.notification`).
  * Trabajadores asíncronos (*Workers*) procesan en segundo plano la generación de PDFs, sincronizaciones externas y reintentos de Webhooks.
* **Justificación de Gobernanza (TOGAF® 10 / COBIT® 2019 BAI04):** Mantiene la disponibilidad del sistema ante picos de demanda masiva (*Black Friday*), evitando bloqueos de servidor por agotamiento de tiempo de espera (*timeouts*).

### 2. Almacenamiento S3 y Optimización Multimedia (Cloudflare R2 / Cloudinary)
* **Propósito:** Almacenar fotografías de alta resolución de moda y certificados PDF/GIA de joyería sin saturar la base de datos relacional.
* **Mecanismo:**
  * Subida directa desde el navegador mediante URLs firmadas (*Pre-signed URLs*) a contenedores S3 compatibles.
  * Transformación y redimensionamiento dinámico en servidores Edge (*On-the-Fly*) convirtiendo archivos a formatos ultra-ligeros (`WebP` / `AVIF`).
* **Justificación de Gobernanza (TOGAF® 10 Architecture Content Framework):** Separación estricta entre datos estructurados (PostgreSQL) y activos binarios no estructurados (Object Storage), reduciendo el costo de respaldos y mejorando el tiempo de carga móvil.

### 3. Observabilidad, Monitoreo y Trazabilidad (OpenTelemetry + Sentry + LangFuse / `ai_audit_logs`)
* **Propósito:** Proporcionar visibilidad total de la salud del software, rendimiento por cliente (*tenant*) y comportamiento de los agentes de IA.
* **Mecanismo:**
  * **Sentry + OpenTelemetry:** Rastreo distribuido (*Distributed Tracing*) de errores en FastAPI y Next.js inyectando el `X-Tenant-ID`.
  * **LangFuse / Helicone:** Monitoreo del consumo de tokens, latencia de respuestas de LLM y costo por interacción conversacional.
  * **`ai_audit_logs`:** Registro inmutable *append-only* en PostgreSQL para almacenar cada sugerencia de la IA y la decisión final de la compuerta.
* **Justificación de Gobernanza (NIST AI RMF 1.0 MEASURE 2.4 & COBIT® 2019 MEA03):** Garantiza la auditoría inmutable exigida por normativas de protección de datos y responsabilidad algorítmica.

### 4. Motor de Búsqueda Dedicado y Búsqueda Difusa (Meilisearch / Typesense)
* **Propósito:** Ofrecer búsquedas instantáneas (< 10 ms) con auto-completado, tolerancia a errores tipográficos (*fuzzy search*), sinonimia y filtros facetados por talla, color y precio.
* **Mecanismo:**
  * Sincronización asíncrona mediante el Bus de Eventos desde PostgreSQL hacia el índice de Meilisearch/Typesense cada vez que cambia el catálogo o el stock.
* **Justificación de Gobernanza (TOGAF® 10 Phase C - Data & Application Architecture):** Evita la saturación del motor relacional PostgreSQL con consultas complejas de texto libre (`LIKE` / ILIKE), reservando la base de datos para operaciones transaccionales críticas.

### 5. Resiliencia, FinOps y *Circuit Breakers* para IA (Cedar/Rego + Budget Caps)
* **Propósito:** Proteger la viabilidad financiera del negocio contra la espiral de costos de LLMs (*cost spiral*) y prevenir fallos en cadena cuando APIs externas (WhatsApp, OpenAI, Pasarelas) se caen.
* **Mecanismo:**
  * **Circuit Breakers:** Si la API de un proveedor de IA o pasarela falla, el sistema conmuta automáticamente a un modo de degradación controlada (respuestas basadas en plantillas estáticas).
  * **Budget Caps (FinOps):** Límites rígidos de consumo diario por cliente y por agente de IA. Al alcanzar el 90% de cuota, se activa una alerta y el agente pasa a modo económico.
* **Justificación de Gobernanza (WaitOps & NIST AI RMF 1.0 MANAGE 4.3):** Aplicación estricta del axioma *"La IA recomienda, las reglas deciden"*, asegurando que ni alucinaciones del modelo ni picos inesperados de consumo comprometan la operación.

---

## 🛡️ Matriz Completa de Control de Riesgos Integrada (10 Componentes)

| Riesgo Identificado | Componente / Solución Arquitectónica Aplicada | Marco de Referencia |
| :--- | :--- | :--- |
| **Divergencia de reglas entre tiendas** | Patrón Core + Extensión por Dominios (Screaming Architecture). | TOGAF® 10 / PMBOK® 6 |
| **Fuga de datos entre tenants** | Row Level Security (RLS) en DB + Skill `tenant-isolation-check`. | COBIT® 2019 / ISO 27001 |
| **Sobreventas por compras simultáneas** | Bloqueo pesimista y reserva temporal de stock en Checkout. | PMBOK® 6 / Core E-commerce |
| **Saturación del servidor HTTP por tareas pesadas** | Cola asíncrona y Bus de Eventos con Redis + Celery/NATS. | COBIT® 2019 BAI04 |
| **Pérdida de velocidad móvil por fotos pesadas** | Storage S3 (Cloudflare R2) + CDN de optimización WebP/AVIF. | TOGAF® 10 ACF |
| **Caídas de DB por búsquedas de texto complejas** | Motor de búsqueda dedicado (Meilisearch / Typesense < 10ms). | TOGAF® 10 Phase C |
| **Alucinaciones o cobros erróneos de la IA** | Compuerta determinista Cedar/Rego ("La IA recomienda, las reglas deciden"). | WaitOps / NIST AI RMF 1.0 |
| **Sobrecostos descontrolados por consumo de LLM** | FinOps Budget Caps + Circuit Breakers con fallback estático. | NIST AI RMF MANAGE 4.3 |
| **Falta de trazabilidad ante reclamos legales** | Logging distribuido OpenTelemetry + Tabla inmutable `ai_audit_logs`. | COBIT® 2019 MEA03 |
| **Brechas de seguridad en manejo de pagos** | Delegación PCI-DSS a pasarelas oficiales (Wompi/MercadoPago/Stripe). | PCI-DSS v4.0 |

---

## 📜 Marco Legal y Regulatorio Integrado

1. **Protección de Datos (Habeas Data / Ley 1581 / GDPR):** La plataforma opera como *Data Processor* (Encargado) y cada tienda como *Data Controller* (Responsable).
2. **Responsabilidad Legal por Mercancía:** Exención explícita en Términos de Servicio (ToS) trasladando la responsabilidad de marcas, garantías y licencias al comerciante.
3. **Cumplimiento PCI-DSS:** Procesamiento delegado mediante tokenización sin almacenar datos de tarjeta en servidores propios.
4. **Validez Jurídica de Ofertas con IA:** Términos legales que establecen que la IA actúa como asistente informativo y que solo las órdenes confirmadas por el servidor backend constituyen contratos vinculantes.

---

📄 *Documento oficial de arquitectura actualizado y sincronizado en el entorno de trabajo Cordiasolve V2.*
