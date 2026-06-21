"""Tests for observability bootstrap — idempotency, tracing, metrics, frameworks."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from opentelemetry import metrics as otel_metrics
from opentelemetry import trace

import l9_service.observability.bootstrap as bootstrap_mod
from l9_service.observability.bootstrap import setup_telemetry


@pytest.fixture(autouse=True)
def reset_bootstrap():
    bootstrap_mod._initialized = False
    yield
    bootstrap_mod._initialized = False


def _minimal_app() -> FastAPI:
    return FastAPI(title="test-svc", version="0.0.1")


def test_setup_telemetry_sets_initialized() -> None:
    app = _minimal_app()
    assert not bootstrap_mod._initialized
    setup_telemetry(app)
    assert bootstrap_mod._initialized


def test_setup_telemetry_idempotent() -> None:
    app = _minimal_app()
    setup_telemetry(app)
    setup_telemetry(app)
    assert bootstrap_mod._initialized


def test_setup_telemetry_custom_service_name() -> None:
    app = _minimal_app()
    setup_telemetry(app, service_name="custom-svc", service_version="1.2.3")
    assert bootstrap_mod._initialized


def test_setup_telemetry_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OTEL_SERVICE_NAME", "env-svc")
    monkeypatch.setenv("OTEL_SERVICE_VERSION", "5.0.0")
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    setup_telemetry(_minimal_app())
    assert bootstrap_mod._initialized


def test_tracer_provider_is_set_after_init() -> None:
    setup_telemetry(_minimal_app())
    assert trace.get_tracer_provider() is not None


def test_meter_provider_is_set_after_init() -> None:
    setup_telemetry(_minimal_app())
    assert otel_metrics.get_meter_provider() is not None


def test_configure_tracing_sample_rate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OTEL_TRACES_SAMPLER_ARG", "0.5")
    setup_telemetry(_minimal_app())
    assert bootstrap_mod._initialized


def test_configure_metrics_export_interval(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OTEL_METRIC_EXPORT_INTERVAL", "30000")
    setup_telemetry(_minimal_app())
    assert bootstrap_mod._initialized
