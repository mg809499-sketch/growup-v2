from __future__ import annotations

import logging
import sys
from typing import cast

import structlog

from app.core.config import settings

_configured = False


def configure_logging() -> None:
    """Logs estructurados: JSON fuera de local, consola legible en local."""
    global _configured
    if _configured:
        return

    level = logging.DEBUG if settings.debug else logging.INFO
    logging.basicConfig(level=level, stream=sys.stdout, format="%(message)s")

    processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if settings.environment in ("local", "test"):
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    _configured = True


def configure_sentry() -> None:
    """Sentry opcional; sin DSN no se inicializa y no hay overhead."""
    if not settings.sentry_dsn:
        return

    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        send_default_pii=False,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))
