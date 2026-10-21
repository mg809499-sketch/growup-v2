# Kiro kit

Este directorio contiene las reglas persistentes y las especificaciones ejecutables del proyecto.

```text
.kiro/
├─ steering/     # Reglas que el agente debe obedecer en cada sesión
├─ specs/        # SDD: requirements → design → tasks (se crean al cerrar decisiones)
└─ skills/       # Checks reutilizables (tenant isolation, block review, etc.)
```

## Orden de trabajo

1. Leer `docs/decisiones-pendientes.md`.
2. Leer `docs/adr/`.
3. Leer `steering/`.
4. Escribir o actualizar la spec en `.kiro/specs/`.
5. Implementar por olas, con evidencia verificable.

## Estado

- `steering/` creado.
- `specs/storefront-platform-v2/` creado con `requirements.md`, `design.md` y `tasks.md`.
- `skills/` pendiente: `tenant-isolation-check` y `block-review` se crean en Wave 1 y Wave 3.
