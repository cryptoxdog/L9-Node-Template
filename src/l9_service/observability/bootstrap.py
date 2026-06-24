# L9_META
# role: observability_bootstrap
# version: 1.0.0
# status: template_infrastructure
"""OTel bootstrap — single-call initialisation. Idempotent."""

from __future__ import annotations

import importlib
import os
from typing import TYPE_CHECKING

from opentelemetry import metrics as otel_metrics
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio

from l9_service.observability.logging import get_logger

if TYPE_CHECKING:
    from fastapi import FastAPI

# Use observability framework per coding guideline (PR #17 CodeRabbit critical).
logger = get_logger(__name__)
_initialized: bool = False

_OPTIONAL_INSTRUMENTORS = [
    ("opentelemetry.instrumentation.redis", "RedisInstrumentor"),
    ("opentelemetry.instrumentation.asyncpg", "AsyncPGInstrumentor"),
    ("opentelemetry.instrumentation.sqlalchemy", "SQLAlchemyInstrumentor"),
]


def setup_telemetry(
    app: FastAPI,
    *,
    service_name: str | None = None,
    service_version: str | None = None,
) -> None:
    """Initialise OTel tracing + metrics + auto-instrumentation. Idempotent."""
    global _initialized
    if _initialized:
        return
    name = service_name or os.getenv("OTEL_SERVICE_NAME", "l9-service")
    version = service_version or os.getenv("OTEL_SERVICE_VERSION", "0.0.0")
    env = os.getenv("ENVIRONMENT", "dev")
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    resource = Resource.create(
        {"service.name": name, "service.version": version, "deployment.environment": env}
    )
    _configure_tracing(resource, endpoint)
    _configure_metrics(resource, endpoint)
    _instrument_frameworks(app)
    _initialized = True
    logger.info("OTel initialised: service=%s env=%s", name, env)


def _configure_tracing(resource: Resource, endpoint: str) -> None:
    sample_rate = float(os.getenv("OTEL_TRACES_SAMPLER_ARG", "1.0"))
    provider = TracerProvider(resource=resource, sampler=ParentBasedTraceIdRatio(sample_rate))
    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=endpoint, insecure=True),
            max_queue_size=2048,
            max_export_batch_size=512,
            export_timeout_millis=30_000,
        )
    )
    trace.set_tracer_provider(provider)


def _configure_metrics(resource: Resource, endpoint: str) -> None:
    export_interval = int(os.getenv("OTEL_METRIC_EXPORT_INTERVAL", "60000"))
    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=endpoint, insecure=True),
        export_interval_millis=export_interval,
    )
    otel_metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))


def _instrument_frameworks(app: FastAPI) -> None:
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=trace.get_tracer_provider(),
        excluded_urls="healthz,readyz,metrics",
    )
    HTTPXClientInstrumentor().instrument()
    for module_path, class_name in _OPTIONAL_INSTRUMENTORS:
        try:
            mod = importlib.import_module(module_path)
            getattr(mod, class_name)().instrument()
        except Exception as exc:
            # Per CodeRabbit review (PR #17): log at debug so failures are
            # observable without breaking the graceful-degradation contract.
            logger.debug(
                "Optional instrumentor unavailable",
                module=module_path,
                class_name=class_name,
                error=str(exc),
            )
