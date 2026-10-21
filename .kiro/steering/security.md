---
inclusion: always
---

# Seguridad

## Identidad

- IdP: Supabase Auth.
- La API verifica el JWT con JWKS; prohibido decodificar el payload sin verificar firma.
- Tenant y rol se leen de `app_metadata` (`tenant_id`, `role`).
- Roles de personal: `owner`, `manager`, `treasurer`, `packer`, `support`.
- Compradores: guest checkout + magic link opcional (D-04).

## Tenancy

- Resolución: `Host` → `domains` → `tenant_id`; el claim JWT debe coincidir.
- `X-Tenant-ID` es solo un hint interno; nunca se confía en él desde internet.
- Mismatch → `403 TENANT_MISMATCH` + auditoría.
- Toda tabla de negocio: `tenant_id UUID NOT NULL`, `ENABLE` + `FORCE ROW LEVEL SECURITY`.
- Política base: `tenant_id = app.current_tenant()` en `USING` y `WITH CHECK`.
- `tenants` no usa `USING (true)`: se resuelve con función `SECURITY DEFINER` acotada o con el rol de servicio.
- Prohibido `BYPASSRLS` en el rol de la API.

## Base de datos

- Rol `app_rw` (sin `BYPASSRLS`) para la API.
- `service_role` solo para workers y tareas administrativas auditadas.
- `SET LOCAL app.current_tenant` dentro de una transacción; nunca `SET` de sesión.
- Prohibido el transaction pooler si rompe el contexto de transacción; documentar el modo de conexión.

## Media y uploads

- Catálogo: bucket público de solo lectura vía CDN, sin PII, con cache inmutable.
- Documentos (facturas, exports): bucket privado con URL firmada de corta duración.
- Prefijo por tenant: `tenant/{tenant_id}/...`.
- Validación de MIME real, tamaño máximo y dimensiones.
- PDFs: antivirus y allowlist.
- Imágenes: strip de EXIF y generación de variantes.

## Secretos y operación

- Secretos en `.env` local o vault; nunca en git.
- Rotación de claves de pasarela y de firma.
- Rate limiting por tenant y por IP en el borde.
- Logs sin PII; `prompt_hash` en lugar de prompts completos.
- Backups con PITR y prueba de restauración.

## Threat model

Se documenta en `docs/architecture/03-tenancy.md` con STRIDE y se valida con el pen-test de 12 vectores cross-tenant.
