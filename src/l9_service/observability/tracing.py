# L9_META
# role: observability_tracing
# version: 1.0.0
# status: template_infrastructure
"""OTel tracing — span(), @instrument, add_event, get_trace_context. Fix-B design."""

from __future__ import annotations

import asyncio
import functools
import logging
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any, TypeVar

from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode

logger = logging.getLogger(__name__)
F = TypeVar("F", bound=Callable[..., Any])

# Fix-B: set by test fixtures only. Never set in production.
_provider_override: trace.TracerProvider | None = None
_SCHEMA_URL = "https://opentelemetry.io/schemas/1.24.0"


def _get_tracer() -> trace.Tracer:
    provider = _provider_override or trace.get_tracer_provider()
    return provider.get_tracer(__name__, schema_url=_SCHEMA_URL)


@contextmanager
def span(
    name: str,
    *,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
    attributes: dict[str, Any] | None = None,
) -> Generator[Span, None, None]:
    with _get_tracer().start_as_current_span(name, kind=kind) as s:
        if attributes:
            for k, v in attributes.items():
                s.set_attribute(k, v)
        try:
            yield s
        except Exception as exc:
            s.record_exception(exc)
            s.set_status(Status(StatusCode.ERROR, str(exc)))
            raise


def instrument(
    name: str | None = None,
    *,
    attributes: dict[str, Any] | None = None,
    record_exception: bool = True,
) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        sname = name or f"{func.__module__}.{func.__qualname__}"
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def aw(*a: Any, **kw: Any) -> Any:
                with _get_tracer().start_as_current_span(sname) as s:
                    if attributes:
                        for k, v in attributes.items():
                            s.set_attribute(k, v)
                    try:
                        return await func(*a, **kw)
                    except Exception as exc:
                        if record_exception:
                            s.record_exception(exc)
                            s.set_status(Status(StatusCode.ERROR, str(exc)))
                        raise

            return aw  # type: ignore[return-value]

        @functools.wraps(func)
        def sw(*a: Any, **kw: Any) -> Any:
            with _get_tracer().start_as_current_span(sname) as s:
                if attributes:
                    for k, v in attributes.items():
                        s.set_attribute(k, v)
                try:
                    return func(*a, **kw)
                except Exception as exc:
                    if record_exception:
                        s.record_exception(exc)
                        s.set_status(Status(StatusCode.ERROR, str(exc)))
                    raise

        return sw  # type: ignore[return-value]

    return decorator


def add_event(name: str, attributes: dict[str, Any] | None = None) -> None:
    s = trace.get_current_span()
    if s and s.is_recording():
        s.add_event(name, attributes=attributes or {})


def get_trace_context() -> dict[str, str]:
    s = trace.get_current_span()
    ctx = s.get_span_context()
    if ctx and ctx.is_valid:
        return {"trace_id": format(ctx.trace_id, "032x"), "span_id": format(ctx.span_id, "016x")}
    return {}
