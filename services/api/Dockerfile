# syntax=docker/dockerfile:1
# Growup API — imagen de producción (Fly.io). Usuario no-root, dependencias fijadas por uv.lock.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --home /app app
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /usr/local/bin/

# Capa de dependencias (cacheable mientras no cambien pyproject/uv.lock)
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project --no-editable

# Código de la aplicación
COPY app ./app
COPY scripts ./scripts
RUN uv sync --frozen --no-dev --no-editable && chown -R app:app /app

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=4); sys.exit(0)"]

CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
