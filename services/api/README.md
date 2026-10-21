# Growup API

API multi-tenant en FastAPI. En esta etapa solo existe el esqueleto y el endpoint de salud; los dominios se añaden por olas.

## Requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Comandos

```bash
cd services/api
uv sync
cp .env.example .env      # completar variables
uv run uvicorn app.main:app --reload
```

- Salud: `GET http://localhost:8000/healthz`
- OpenAPI: `GET http://localhost:8000/openapi.json`
- Docs: `GET http://localhost:8000/docs`

## Calidad

```bash
uv run ruff check .
uv run mypy app
uv run pytest
```

## Estructura

```text
services/api/
├─ app/
│  ├─ main.py          # FastAPI app
│  └─ core/            # config, db, auth, tenant, cache, observability
├─ tests/
├─ pyproject.toml
└─ .env.example
```

La estructura por dominios (`app/domains/...`) se crea en la Wave 1, después de cerrar D-04 y D-07.
