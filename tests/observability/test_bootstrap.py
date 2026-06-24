"""Bootstrap unit tests — covers PR #17 CodeRabbit findings.

Validates:
1. `get_logger` (observability framework) is used, not stdlib `logging.getLogger`.
2. The optional-instrumentor `except` block logs a debug entry with
   structured fields when an instrumentor import or instantiation fails
   (per CodeRabbit MINOR finding).
"""

from __future__ import annotations

import importlib
import logging as stdlib_logging
from unittest.mock import MagicMock, patch

import pytest

import l9_service.observability.bootstrap as bootstrap_mod
from l9_service.observability.logging import get_logger


def test_logger_is_observability_framework_logger() -> None:
    """The module-level logger must come from the observability framework,
    not from stdlib logging (PR #17 CodeRabbit CRITICAL)."""
    # Logger must be the same class returned by get_logger().
    expected = get_logger("l9_service.observability.bootstrap")
    assert type(bootstrap_mod.logger) is type(expected)
    # And it should not be a stdlib logging.Logger.
    assert not isinstance(bootstrap_mod.logger, stdlib_logging.Logger)


def test_instrument_frameworks_logs_debug_on_optional_instrumentor_failure() -> None:
    """When an optional instrumentor raises during import or instantiation,
    the except block must log at debug with structured fields (module,
    class_name, error) — PR #17 CodeRabbit MINOR finding."""
    fake_app = MagicMock()

    debug_calls: list[tuple[str, dict]] = []

    class _CaptureLogger:
        def debug(self, msg: str, **kwargs: object) -> None:  # type: ignore[override]
            debug_calls.append((msg, dict(kwargs)))

        def info(self, *a: object, **k: object) -> None:
            pass

        def warning(self, *a: object, **k: object) -> None:
            pass

        def error(self, *a: object, **k: object) -> None:
            pass

    # Force every optional instrumentor import_module call to raise.
    def _raise_import(_path: str) -> object:
        raise ImportError("simulated missing optional dependency")

    with (
        patch.object(bootstrap_mod, "logger", _CaptureLogger()),
        patch.object(bootstrap_mod, "FastAPIInstrumentor") as fastapi_inst,
        patch.object(bootstrap_mod, "HTTPXClientInstrumentor") as httpx_inst,
        patch.object(bootstrap_mod.importlib, "import_module", side_effect=_raise_import),
    ):
        fastapi_inst.instrument_app = MagicMock()
        httpx_inst.return_value = MagicMock()
        bootstrap_mod._instrument_frameworks(fake_app)

    # Each optional instrumentor in the list should have produced one debug call.
    assert len(debug_calls) == len(bootstrap_mod._OPTIONAL_INSTRUMENTORS), (
        f"expected one debug log per optional instrumentor "
        f"({len(bootstrap_mod._OPTIONAL_INSTRUMENTORS)}); got {len(debug_calls)}"
    )
    for _msg, kwargs in debug_calls:
        # Structured fields required by the review.
        assert "module" in kwargs
        assert "class_name" in kwargs
        assert "error" in kwargs
        assert "simulated missing optional dependency" in kwargs["error"]


def test_instrument_frameworks_logs_debug_on_instantiation_failure() -> None:
    """Cover the case where import succeeds but `Class().instrument()` raises."""
    fake_app = MagicMock()
    debug_calls: list[tuple[str, dict]] = []

    class _CaptureLogger:
        def debug(self, msg: str, **kwargs: object) -> None:
            debug_calls.append((msg, dict(kwargs)))

        def info(self, *a: object, **k: object) -> None:
            pass

    class _BoomInstrumentor:
        def __init__(self) -> None:
            raise RuntimeError("instantiation failed")

    class _FakeModule:
        # Each attribute name in _OPTIONAL_INSTRUMENTORS resolves to the
        # boom class so getattr(mod, class_name)() raises.
        def __getattr__(self, _name: str) -> type:
            return _BoomInstrumentor

    with (
        patch.object(bootstrap_mod, "logger", _CaptureLogger()),
        patch.object(bootstrap_mod, "FastAPIInstrumentor") as fastapi_inst,
        patch.object(bootstrap_mod, "HTTPXClientInstrumentor") as httpx_inst,
        patch.object(bootstrap_mod.importlib, "import_module", return_value=_FakeModule()),
    ):
        fastapi_inst.instrument_app = MagicMock()
        httpx_inst.return_value = MagicMock()
        bootstrap_mod._instrument_frameworks(fake_app)

    assert len(debug_calls) == len(bootstrap_mod._OPTIONAL_INSTRUMENTORS)
    for _msg, kwargs in debug_calls:
        assert kwargs["error"] == "instantiation failed"


def test_bootstrap_module_does_not_import_stdlib_logging_module_level() -> None:
    """Guard against regression: the module must not re-introduce
    `import logging` at module level (per CodeRabbit CRITICAL)."""
    src_path = bootstrap_mod.__file__
    assert src_path is not None
    with open(src_path, encoding="utf-8") as fh:
        source = fh.read()
    # Reject the bare top-level form. Allow `import logging as ...` inside
    # functions for tests if ever needed, but at module scope a bare
    # `import logging` would defeat the framework guarantee.
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        assert stripped != "import logging", (
            "bootstrap.py must not import stdlib `logging` at module level"
        )


# Sanity import to ensure module-level execution counts toward coverage.
def test_module_imports_cleanly() -> None:
    importlib.reload(bootstrap_mod)
    assert hasattr(bootstrap_mod, "setup_telemetry")
    assert hasattr(bootstrap_mod, "_instrument_frameworks")
    assert callable(bootstrap_mod.setup_telemetry)


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__, "-v"])
