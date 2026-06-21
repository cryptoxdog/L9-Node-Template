"""Tests for l9_service.main — app factory, health routes, telemetry init."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import l9_service.observability.bootstrap as bootstrap_mod
from l9_service.main import create_app


@pytest.fixture
def app():
    bootstrap_mod._initialized = False
    _app = create_app()
    bootstrap_mod.setup_telemetry(_app)
    return _app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_healthz_returns_ok(client) -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_readyz_returns_ready(client) -> None:
    resp = client.get("/readyz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}


def test_app_title_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OTEL_SERVICE_NAME", "my-test-svc")
    monkeypatch.setenv("OTEL_SERVICE_VERSION", "9.9.9")
    _app = create_app()
    assert _app.title == "my-test-svc"
    assert _app.version == "9.9.9"


def test_app_title_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OTEL_SERVICE_NAME", raising=False)
    monkeypatch.delenv("OTEL_SERVICE_VERSION", raising=False)
    _app = create_app()
    assert _app.title == "l9-service"
    assert _app.version == "0.1.0"
