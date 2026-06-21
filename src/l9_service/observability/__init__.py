# L9_META
# role: observability_package
# version: 1.0.0
# status: template_infrastructure
"""L9 Observability — OTel tracing, metrics, structured logging."""

from __future__ import annotations

from .bootstrap import setup_telemetry

__all__ = ["setup_telemetry"]
