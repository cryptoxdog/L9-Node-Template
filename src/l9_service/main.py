# L9_META
# role: fastapi_app
# version: 1.0.0
# status: template_infrastructure
"""FastAPI application factory."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from l9_service.observability import setup_telemetry
from l9_service.observability.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=os.getenv("OTEL_SERVICE_NAME", "l9-service"),
        version=os.getenv("OTEL_SERVICE_VERSION", "0.1.0"),
    )

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    @app.get("/readyz", include_in_schema=False)
    async def readyz() -> JSONResponse:
        return JSONResponse({"status": "ready"})

    return app


app = create_app()
setup_telemetry(app)
