# L9_META
# role: service_package
# version: 1.0.0
# status: template_infrastructure
"""l9_service — L9 service template. Rename to your package."""

from __future__ import annotations

from l9_service.observability import setup_telemetry

__version__ = "0.1.0"
__all__ = ["setup_telemetry", "__version__"]
