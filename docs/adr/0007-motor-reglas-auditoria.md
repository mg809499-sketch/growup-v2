# ADR-0007 — Motor de reglas y auditoría

- **Estado:** Aceptada
- **Fecha:** 2026-10-21
- **Decisores:** equipo de ingeniería
- **Relacionado con:** ADR-0004, ADR-0005, `.kiro/steering/governance.md`

## Contexto

La gobernanza del producto se resume en una frase: **la IA recomienda, las reglas deciden**. Ninguna mutación sensible (pagos, reembolsos, publicación, cambios de rol, suspensión de tenant) puede depender de un modelo, de una captura o de texto libre. Además, cada decisión debe poder auditarse y explicarse sin el modelo.

El MVP no tiene IA conversacional (D-05), pero el marco debe existir desde el inicio para que añadirla después no obligue a reescribir los flujos sensibles.

## Decisión

### 1. Interfaz determinista

```python
class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HANDOFF = "HANDOFF"

@dataclass(frozen=True)
class PolicyInput:
    tenant_id: UUID
    actor: Actor
    action: str
    resource: Resource
    context: Mapping[str, object]
    trace_id: str

@dataclass(frozen=True)
class PolicyResult:
    decision: Decision
    policy_id: str
    policy_version: str
    reason_code: str
    reasons: tuple[str, ...]
    latency_ms: int

def decide(policy_id: str, input: PolicyInput) -> PolicyResult:
    ...
```

- `decide` es síncrono, determinista y sin llamadas a red.
- Las políticas viven en `services/api/app/governance/policies/`, versionadas en el repositorio.
- Cada política declara `id`, `version` y `evaluate(input) -> PolicyResult`.
- Si una política lanza una excepción, el resultado es `DENY` con `POLICY_ERROR`; nunca `ALLOW` por defecto.
- OPA/Cedar se pueden adoptar después detrás de la misma interfaz.

### 2. Compuertas obligatorias del MVP

| Acción | Política | Resultado esperado |
|---|---|---|
| Confirmar pago | `payments.confirm` | Solo webhook firmado; el cliente no confirma |
| Reembolsar | `payments.refund` | `ALLOW` bajo umbral; `HANDOFF` sobre umbral |
| Publicar página | `content.publish` | `ALLOW` si schema y permisos son válidos |
| Cambiar rol | `identity.change_role` | Solo `owner`; `DENY` si intenta escalar |
| Suspender tenant | `platform.suspend_tenant` | `HANDOFF` con razón y auditoría |
| Aplicar descuento | `commerce.discount` | Fuera del MVP; si se añade, `HANDOFF` sobre umbral |
| Acceso cross-tenant | `platform.cross_tenant_access` | `HANDOFF` + auditoría; nunca silencioso |

- Los umbrales (por ejemplo, reembolso máximo automático) son configuración por tenant y se versionan con la política.
- Un endpoint sensible que no llame a `decide` es un bug de implementación; un test enumera las rutas y lo verifica.

### 3. Registro de auditoría append-only

Tabla `decision_logs`:

| Campo | Tipo | Nota |
|---|---|---|
| `id` | uuid | PK |
| `tenant_id` | uuid | FK, RLS |
| `actor_type` | text | `staff`, `customer`, `system`, `ai` |
| `actor_id` | text | Nullable para system |
| `action` | text | Acción evaluada |
| `resource_type`, `resource_id` | text | Recurso afectado |
| `policy_id`, `policy_version` | text | Política aplicada |
| `decision` | text | `ALLOW`, `DENY`, `HANDOFF` |
| `reason_code` | text | Código estable |
| `input_hash` | text | SHA-256 del input canónico |
| `context_summary` | jsonb | Redactado, sin PII |
| `latency_ms` | int | Medición de `decide` |
| `trace_id` | text | Correlación |
| `created_at` | timestamptz | UTC |
| `prev_hash` | text | Hash de la fila anterior del tenant |
| `hash` | text | SHA-256 de la fila + `prev_hash` |

Reglas:

- `INSERT` permitido para la API y workers; `UPDATE` y `DELETE` bloqueados por trigger y por permisos.
- Cadena por tenant; génesis = 64 ceros. La escritura se serializa con `pg_advisory_xact_lock(hashtext(tenant_id))` para evitar bifurcaciones.
- Un job diario verifica la cadena. Si falla: alerta crítica `GOVERNANCE_INTEGRITY_FAILURE` y bloqueo de mutaciones sensibles hasta que operaciones resuelva.
- `context_summary` solo guarda campos allowlist; nunca prompts, tokens, datos de tarjeta ni PII.
- Retención mínima de 5 años o la que exija la ley; exportable a R2 para archivo.

### 4. Handoff humano

- `HANDOFF` crea una tarea en `approval_tasks` con `tenant_id`, acción, recurso, razón, rol asignado, `expires_at` y `trace_id`.
- El admin muestra la bandeja de aprobaciones; la resolución (`approved`/`rejected`) se registra en `decision_logs`.
- Reembolsos altos y accesos cross-tenant requieren cuatro ojos: quien solicita no puede aprobar.
- Sin respuesta antes de `expires_at`, la tarea expira y la acción queda denegada.

### 5. IA futura (marco)

- Solo intents de una allowlist versionada.
- La IA produce una `ActionProposal` (`intent`, `params`, `confidence`, `model`, `prompt_hash`); **no ejecuta** la mutación.
- `decide` evalúa la propuesta como cualquier otra entrada.
- Confianza menor al umbral configurado → `HANDOFF`.
- Presupuesto por tenant y por agente; circuit breaker con fallback a plantillas estáticas.
- `prompt_hash` en lugar de prompt completo; sin PII cruda.
- Métricas: tasa de `HANDOFF`, costo por tenant, latencia, errores del modelo.

### 6. Observabilidad de gobernanza

- Métricas por `policy_id`, `decision`, `reason_code` y latencia.
- Alertas:
  - Aumento anómalo de `DENY` o `HANDOFF`.
  - Cadena de auditoría inválida.
  - Endpoint sensible sin política (detectado en CI).
  - `HANDOFF` expirado sin resolver.

### 7. Testing

- Tests table-driven por política: input → decisión y `reason_code`.
- Test de cobertura: enumera rutas sensibles y verifica que llaman a `decide`.
- Property-based tests de la cadena: appends concurrentes no bifurcan; tamper detectado.
- Tests de handoff: expiración, cuatro ojos, resolución auditada.
- Golden tests de `reason_code` para no romper contratos de API.

## Alternativas consideradas

| Alternativa | Pros | Contras | ¿Por qué no? |
|---|---|---|---|
| A. Políticas en código Python (elegida) | Simple, tipado, testeable | Requiere deploy para cambiar | El MVP no necesita config dinámica |
| B. OPA/Rego desde el día 1 | Estándar, configurable | Otro servicio y lenguaje | Se puede adoptar después |
| C. Reglas en la base de datos | Centralizadas | Difíciles de testear y versionar | Menos expresivas |
| D. Auditoría con logs de aplicación | Cero esquema | Sin garantía de integridad | No cumple gobernanza |
| E. Auditar con triggers | Automático | Difícil de enriquecer con contexto | La app conoce la decisión |

## Consecuencias

### Positivas

- Toda mutación sensible es explicable y auditable sin el modelo.
- La cadena de hash detecta manipulación del registro.
- El marco de IA está listo sin acoplar el MVP a un proveedor.
- Las políticas se testean como código y se versionan con el producto.

### Negativas / deuda asumida

- Hay que instrumentar cada endpoint sensible y mantener las políticas.
- La serialización por tenant puede ser un cuello de botella si hay muchas decisiones concurrentes; se mitiga con lotes o colas.
- El handoff requiere UI y proceso operativo.
- La retención de 5 años implica costo de almacenamiento y anonimización.

### Neutras

- Las políticas son código en el MVP; un cambio de umbral requiere deploy.
- La IA no está en el MVP, pero su interfaz ya está definida.

## Cómo se verifica

- `payments.confirm` sin webhook firmado → `DENY`.
- Reembolso sobre umbral → `HANDOFF` y tarea creada.
- `owner` del tenant A no puede cambiar roles del tenant B.
- Modificar una fila de `decision_logs` rompe la verificación diaria.
- Un endpoint sensible sin `decide` falla el test de cobertura.
- Un `HANDOFF` expirado no se ejecuta.
- No hay PII en `context_summary`.

## Pendientes

- Definir umbrales de reembolso y de descuentos.
- Definir SLA de handoff y roles aprobadores.
- Definir política de retención y anonimización.
- Evaluar OPA/Cedar cuando haya más de 20 políticas.

## Enlaces

- [ADR-0004](0004-pagos-checkout-merchant-of-record.md)
- [ADR-0005](0005-contenido-y-publishing.md)
- [Governance steering](../../.kiro/steering/governance.md)
