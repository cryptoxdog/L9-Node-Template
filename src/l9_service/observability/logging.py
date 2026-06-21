# L9_META
# role: observability_logging
# version: 1.0.0
# status: template_infrastructure
"""Structured logging — structlog + OTel trace context injection."""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger

from .tracing import get_trace_context


def _inject_trace_context(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    ctx = get_trace_context()
    if ctx:
        event_dict["trace_id"] = ctx["trace_id"]
        event_dict["span_id"] = ctx["span_id"]
    return event_dict


def _add_log_level(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    event_dict["level"] = method_name.upper()
    return event_dict


def configure_logging(*, level: str | None = None, json: bool | None = None) -> None:
    resolved_level = level or os.getenv("LOG_LEVEL", "INFO")
    env = os.getenv("ENVIRONMENT", "dev")
    resolved_json = json if json is not None else (env != "dev")
    logging.basicConfig(
        level=getattr(logging, resolved_level.upper(), logging.INFO),
        stream=sys.stdout,
        format="%(message)s",
    )
    for noisy in ("uvicorn.access", "httpx", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    shared: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        _add_log_level,
        _inject_trace_context,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
    ]
    if resolved_json:
        shared.append(structlog.processors.dict_tracebacks)
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        shared.append(structlog.dev.set_exc_info)
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    structlog.configure(
        processors=[*shared, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    fmt = structlog.stdlib.ProcessorFormatter(
        processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, renderer],
        foreign_pre_chain=shared,
    )
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(fmt)
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(h)
    root.setLevel(getattr(logging, resolved_level.upper(), logging.INFO))


def get_logger(name: str | None = None, **initial_values: Any) -> structlog.stdlib.BoundLogger:
    bound = structlog.get_logger(name)
    if initial_values:
        bound = bound.bind(**initial_values)
    return bound
