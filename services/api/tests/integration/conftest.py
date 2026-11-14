"""Harness de integración: stub mínimo de `auth.users` (Supabase/GoTrue).

La función SECURITY DEFINER `app.complete_client_signup()` hace
`update auth.users ... raw_app_meta_data`. Ese esquema solo existe en Supabase;
en un Postgres vanilla (p. ej. el service container de CI) la migración se
crea igual (el cuerpo plpgsql no se valida al crearla) pero fallaría al
llamarla. El stub replica únicamente lo que la función toca:

  - `id`              (clave, uuid)
  - `raw_app_meta_data` (jsonb, merge con tenant_id/role)

Es un test-double de un servicio externo: vive SOLO en la base de datos de
pruebas (GROWUP_TEST_DATABASE_URL), es idempotente y jamás se aplica a
desarrollo ni producción. Si el esquema auth ya existe (Supabase local),
no hace nada.
"""

from __future__ import annotations

import os

import pytest

TEST_DSN = os.getenv("GROWUP_TEST_DATABASE_URL")

_DDL = """
create schema if not exists auth;
create table if not exists auth.users (
    id uuid primary key,
    raw_app_meta_data jsonb
);
"""


@pytest.fixture(autouse=True)
async def ensure_auth_users_stub() -> None:
    if not TEST_DSN:
        return
    import asyncpg

    connection = await asyncpg.connect(TEST_DSN)
    try:
        await connection.execute(_DDL)
    finally:
        await connection.close()
