# CORS para subida directa a R2 / MinIO (admin → bucket)

**Contexto:** el flujo de carga es navegador → URL prefirmada (PUT directo, sin credenciales) → R2. El navegador bloquea ese PUT si el bucket no permite el origen del admin vía CORS. La API no puede solucionarlo; es configuración del bucket.

## Cloudflare R2 (producción / staging)

En la consola de R2 → bucket `growup-catalog` → Settings → CORS policy:

```json
[
  {
    "AllowedOrigins": [
      "https://admin.growup.com",
      "https://admin-staging.growup.com"
    ],
    "AllowedMethods": ["PUT", "HEAD"],
    "AllowedHeaders": ["Content-Type", "Content-Length"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 900
  }
]
```

`AllowedOrigins` no admite `*` junto con credenciales; aquí no hay cookies de terceros (la URL va firmada), así que el PUT es seguro siempre que los orígenes sean exactamente el admin.

## MinIO (desarrollo local, `infra/docker-compose.yml`)

```bash
docker exec growup-minio mc alias set local http://localhost:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"
docker exec growup-minio mc cors set local/growup-catalog-local --method PUT \
  --origin 'http://localhost:3001' --header 'Content-Type' --header 'Content-Length'
```

(o el equivalente con `mc cors set` / JSON si tu versión de `mc` lo exige.)

## Verificación rápida

1. Admin → Media → Subir imagen → elegir JPEG → Subir.
2. Estado “Subiendo a R2… 100%” → “Procesando…” → “Imagen lista”.
3. En DevTools → Network: el PUT a `*.r2.cloudflarestorage.com` (o `localhost:9000`) no muestra errores CORS; la respuesta es 200/204.

Si ves error CORS: el bucket no permite el origen del admin o faltan cabeceras; corrige la política del bucket. Si ves `403` de firma: la URL caducó (900 s) o el `Content-Type`/tamaño no coincide — recarga el flujo (botón Reintentar).

## Seguridad

- La URL prefirmada expira en 900 s y está restringida a la clave del tenant (`tenant/{tenant_id}/originals/…`) y al `Content-Type`/tamaño exactos.
- El MIME real se verifica en el worker al procesar (Pillow); la firma no es la autoridad de formato.
- Nunca exponer `r2_access_key_id` / `r2_secret_access_key` al admin: solo vive en la API (Fly) y `.env` local.
