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
- `specs/` pendiente: depende de las decisiones D-01 a D-08.
- `skills/` pendiente: se crea junto con la primera ola.
