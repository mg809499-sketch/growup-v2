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

El mismo harness hace upsert de los planes placeholder `starter` y `pro`
(idénticos a supabase/seed.sql): la CI con Postgres vanilla aplica solo las
migraciones (nunca el seed) y los tests de onboarding exigen que existan.
Los precios/límites de planes los cierra D-01 derivado; hasta entonces son
placeholders deliberados.
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

_PLANS_DDL = """
insert into app.plans (code, name, price_cents, currency, billing_interval, trial_days, features)
values
    ('starter', 'Starter', 0, 'COP', 'month', 14, '{"placeholder": true}'::jsonb),
    ('pro',     'Pro',     0, 'COP', 'month', 14, '{"placeholder": true}'::jsonb)
on conflict (code) do nothing;
"""


@pytest.fixture(autouse=True)
async def ensure_test_fixtures() -> None:
    if not TEST_DSN:
        return
    import asyncpg

    connection = await asyncpg.connect(TEST_DSN)
    try:
        await connection.execute(_DDL)
        await connection.execute(_PLANS_DDL)
    finally:
        await connection.close()
