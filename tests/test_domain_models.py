"""Tests for src/l9_service/domain/models.py — reference pydantic models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from l9_service.domain.models import (
    TemplateBoundaryRequest,
    TemplateBoundaryResponse,
)


def test_request_round_trip() -> None:
    req = TemplateBoundaryRequest(id="abc", payload={"k": 1})
    assert req.id == "abc"
    assert req.payload == {"k": 1}
    # model_config extra='forbid'
    dumped = req.model_dump()
    assert dumped == {"id": "abc", "payload": {"k": 1}}


def test_request_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        TemplateBoundaryRequest(id="x", payload={}, extra="nope")  # type: ignore[call-arg]


def test_request_requires_fields() -> None:
    with pytest.raises(ValidationError):
        TemplateBoundaryRequest()  # type: ignore[call-arg]


def test_response_default_result_is_none() -> None:
    resp = TemplateBoundaryResponse(success=True)
    assert resp.success is True
    assert resp.result is None


def test_response_with_result() -> None:
    resp = TemplateBoundaryResponse(success=True, result={"ok": True})
    assert resp.result == {"ok": True}


def test_response_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        TemplateBoundaryResponse(success=True, foo="bar")  # type: ignore[call-arg]


def test_response_requires_success() -> None:
    with pytest.raises(ValidationError):
        TemplateBoundaryResponse()  # type: ignore[call-arg]
