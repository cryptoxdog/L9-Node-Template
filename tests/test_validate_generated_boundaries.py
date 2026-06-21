"""Tests for tools/validate_generated_boundaries.py

The script computes ROOT = Path(__file__).resolve().parents[1]. To test it
in-process (so coverage is tracked), we import the module, monkeypatch its
ROOT/ENGINE module-level globals, and call main() directly.
"""

from __future__ import annotations

import importlib.util as _ilu
import sys as _sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "validate_generated_boundaries.py"
_spec = _ilu.spec_from_file_location("validate_generated_boundaries", _SCRIPT)
vgb = _ilu.module_from_spec(_spec)
_sys.modules["validate_generated_boundaries"] = vgb
_spec.loader.exec_module(vgb)  # type: ignore[union-attr]


_GOOD_ENGINE = (
    "# GENERATED FILE\n"
    "# generated_by: l9-codegen-engine\n"
    "# source_contract: nodespec.yaml\n"
    "# hand_editing: forbidden\n"
    "async def handle_x():\n"
    "    return None\n"
)


def _stage(tmp_path: Path, engine_body: str, extra: dict[str, str] | None = None) -> Path:
    repo = tmp_path / "repo"
    (repo / "src" / "l9_service").mkdir(parents=True)
    (repo / "tools").mkdir(parents=True)
    (repo / "src" / "l9_service" / "enginehandlers.py").write_text(engine_body, encoding="utf-8")
    for rel, body in (extra or {}).items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    return repo


@pytest.fixture
def patched_root(monkeypatch: pytest.MonkeyPatch):
    def _apply(repo: Path) -> None:
        monkeypatch.setattr(vgb, "ROOT", repo)
        monkeypatch.setattr(vgb, "ENGINE", repo / "src" / "l9_service" / "enginehandlers.py")

    return _apply


def test_passes_with_good_engine(tmp_path: Path, patched_root) -> None:
    repo = _stage(tmp_path, _GOOD_ENGINE)
    patched_root(repo)
    assert vgb.main() == 0


def test_fails_when_marker_missing(tmp_path, patched_root, capsys):
    bad = _GOOD_ENGINE.replace("hand_editing: forbidden\n", "")
    repo = _stage(tmp_path, bad)
    patched_root(repo)
    assert vgb.main() == 1
    out = capsys.readouterr().out
    assert "missing marker" in out


def test_fails_when_sdk_transport_imported_elsewhere(tmp_path, patched_root, capsys):
    repo = _stage(
        tmp_path,
        _GOOD_ENGINE,
        extra={"src/l9_service/leak.py": "from l9_sdk.transport import TransportPacket\n"},
    )
    patched_root(repo)
    assert vgb.main() == 1
    out = capsys.readouterr().out
    assert "SDK transport reference/import outside" in out


def test_fails_when_legacy_envelope_present(tmp_path, patched_root, capsys):
    repo = _stage(tmp_path, _GOOD_ENGINE)
    # Write the literal PacketEnvelope symbol that the script detects via concat
    (repo / "src" / "l9_service" / "legacy.py").write_text("x = PacketEnvelope\n", encoding="utf-8")
    patched_root(repo)
    assert vgb.main() == 1
    out = capsys.readouterr().out
    assert "legacy envelope" in out


def test_fails_when_generator_term_in_template_owned(tmp_path, patched_root, capsys):
    repo = _stage(
        tmp_path,
        _GOOD_ENGINE,
        extra={"tools/some_template_tool.py": "def generate_handler(): pass\n"},
    )
    patched_root(repo)
    assert vgb.main() == 1
    out = capsys.readouterr().out
    assert "generator ownership term" in out


def test_fails_when_engine_missing(tmp_path, patched_root, capsys):
    repo = tmp_path / "repo"
    (repo / "src" / "l9_service").mkdir(parents=True)
    patched_root(repo)
    assert vgb.main() == 1
    out = capsys.readouterr().out
    assert "missing" in out.lower()
