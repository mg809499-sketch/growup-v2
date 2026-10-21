---
name: block-review
description: Revisa un bloque del builder o un cambio de contenido contra schemas cerrados, seguridad XSS, accesibilidad, publish atómico y rendimiento del storefront. Úsala al crear o modificar bloques, temas, layouts, componentes del builder o endpoints de contenido.
---

# Block Review

## Objetivo

Asegurar que un bloque nuevo o modificado es seguro, accesible, versionable y compatible con el publish atómico, sin abrir HTML arbitrario ni romper el rendimiento móvil.

## Cuándo usarla

- Nuevo tipo de bloque o cambio de props.
- Cambio en `page_versions.layout`, `BlockRenderer` o builder.
- Nuevo tema o tokens.
- Cambio en preview, publish, rollback o purga de caché.

## Checklist

### Schema y seguridad

- [ ] El bloque tiene schema Pydantic/Zod cerrado y discriminated union.
- [ ] `type` está en el registry; no hay tipos dinámicos.
- [ ] No acepta HTML, `<script>`, `iframe` libre, CSS arbitrario ni `javascript:`.
- [ ] `rich_text` solo permite Markdown restringido y se sanea en servidor.
- [ ] Los links se validan (https/http/mailto allowlist; sin `javascript:`).
- [ ] Los límites de items, longitud y anidamiento están definidos.
- [ ] Las imágenes exigen `alt` y dimensiones.
- [ ] Los IDs de producto/colección se validan contra el mismo tenant.

### Contenido y publishing

- [ ] El borrador se guarda con control optimista (`expected_version`).
- [ ] Publicar valida schema, permisos y render antes de crear la versión.
- [ ] La versión publicada es inmutable.
- [ ] Rollback apunta a una versión anterior sin borrar la nueva.
- [ ] El bloque desconocido tiene fallback seguro y se registra.
- [ ] La purga de caché usa tags por tenant/página.

### Accesibilidad

- [ ] Jerarquía de headings correcta (un `h1` por página).
- [ ] Contraste de tokens WCAG 2.2 AA.
- [ ] Foco visible y navegación por teclado.
- [ ] `alt` significativo o decorativo vacío.
- [ ] Carruseles con controles accesibles y pausa.
- [ ] Videos con subtítulos/transcripción cuando aplique.

### Rendimiento

- [ ] Imágenes con `next/image`, `sizes` y formatos modernos.
- [ ] `priority` solo en el hero.
- [ ] Sin JS de cliente innecesario; RSC por defecto.
- [ ] El bloque no bloquea el LCP móvil (< 2.5 s).
- [ ] Sin dependencias nuevas sin justificación.

### Tests

- [ ] Props inválidas → error de validación.
- [ ] Payload XSS → rechazado/saneado.
- [ ] Bloque desconocido → fallback.
- [ ] Publish inválido no cambia `published_version_id`.
- [ ] Rollback sirve la versión anterior.
- [ ] axe sin violaciones críticas.
- [ ] Screenshot visual del bloque en los dos temas.

## Comandos

```bash
pnpm lint
pnpm typecheck
pnpm build

cd services/api
uv run pytest tests/content tests/domains/content
```

## Salida esperada

```text
BLOCK REVIEW: PASS | FAIL
- Bloque: <type>
- Schema: <archivo>
- Seguridad: <HTML/XSS/links>
- Accesibilidad: <axe + manual>
- Publish: <atomicidad/rollback>
- Performance: <LCP estimado>
- Tests: <comando + resultado>
```

Sin schema cerrado, sin alt text o con HTML arbitrario: FAIL.
