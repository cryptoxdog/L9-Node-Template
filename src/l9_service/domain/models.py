# L9_META
# role: domain_models
# version: 1.1.0
# status: template_reference
"""Domain model reference types for the L9 Node Repo Template.

These models are safe, concrete reference types used by template tests and examples.
Concrete nodes may replace or extend this module through normal source edits, while
transport handlers remain generated-only.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class TemplateBoundaryRequest(BaseModel):
    """Reference request model for template boundary validation."""

    model_config = ConfigDict(extra="forbid")

    id: str
    payload: dict[str, Any]


class TemplateBoundaryResponse(BaseModel):
    """Reference response model for template boundary validation."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    result: dict[str, Any] | None = None
