"""Tests for tools/verify_contracts.py"""

from __future__ import annotations

import importlib.util as _ilu
import sys as _sys
from pathlib import Path

import pytest
import yaml

_SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "verify_contracts.py"
_spec = _ilu.spec_from_file_location("verify_contracts", _SCRIPT)
vc = _ilu.module_from_spec(_spec)
_sys.modules["verify_contracts"] = vc
_spec.loader.exec_module(vc)  # type: ignore[union-attr]


def _write_manifest(tmp_path: Path, data: dict) -> Path:
    m = tmp_path / "manifest.yaml"
    m.write_text(yaml.safe_dump(data), encoding="utf-8")
    return m


def test_sha256_12_stable(tmp_path: Path) -> None:
    p = tmp_path / "f.txt"
    p.write_bytes(b"hello")
    digest = vc.sha256_12(p)
    assert len(digest) == 12
    # Stable: same content same digest
    assert digest == vc.sha256_12(p)


def test_load_manifest_roundtrip(tmp_path: Path) -> None:
    m = _write_manifest(tmp_path, {"required_files": [], "reference_targets": []})
    data = vc.load_manifest(m)
    assert data == {"required_files": [], "reference_targets": []}


def test_verify_passes_when_all_present(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("# A mentions b.md\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("# B\n", encoding="utf-8")
    m = _write_manifest(
        tmp_path,
        {
            "required_files": [
                {"path": "b.md", "must_be_mentioned_in": ["a.md"]},
            ],
            "reference_targets": ["a.md"],
        },
    )
    assert vc.verify(tmp_path, m) == []


def test_verify_missing_required_file(tmp_path: Path) -> None:
    m = _write_manifest(
        tmp_path,
        {
            "required_files": [{"path": "missing.md"}],
            "reference_targets": [],
        },
    )
    violations = vc.verify(tmp_path, m)
    assert any("MISSING required file" in v for v in violations)


def test_verify_sha_drift(tmp_path: Path) -> None:
    p = tmp_path / "x.txt"
    p.write_bytes(b"hello")
    m = _write_manifest(
        tmp_path,
        {
            "required_files": [{"path": "x.txt", "sha256_12": "000000000000"}],
            "reference_targets": [],
        },
    )
    violations = vc.verify(tmp_path, m)
    assert any("SHA DRIFT" in v for v in violations)


def test_verify_missing_reference_target(tmp_path: Path) -> None:
    m = _write_manifest(
        tmp_path,
        {
            "required_files": [],
            "reference_targets": ["nonexistent.md"],
        },
    )
    violations = vc.verify(tmp_path, m)
    assert any("MISSING reference target" in v for v in violations)


def test_verify_handles_empty_manifest(tmp_path: Path) -> None:
    """Per Gemini review: empty YAML must not raise AttributeError."""
    m = tmp_path / "empty.yaml"
    m.write_text("", encoding="utf-8")
    assert vc.verify(tmp_path, m) == []


def test_verify_handles_list_manifest(tmp_path: Path) -> None:
    """Per Gemini review: non-mapping YAML must not raise."""
    m = tmp_path / "list.yaml"
    m.write_text("- a\n- b\n", encoding="utf-8")
    # Should not raise; falls back to empty manifest
    assert vc.verify(tmp_path, m) == []


def test_verify_contract_not_mentioned(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("# A — no mention here\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("# B\n", encoding="utf-8")
    m = _write_manifest(
        tmp_path,
        {
            "required_files": [{"path": "b.md", "must_be_mentioned_in": ["a.md"]}],
            "reference_targets": ["a.md"],
        },
    )
    violations = vc.verify(tmp_path, m)
    assert any("CONTRACT NOT MENTIONED" in v for v in violations)


def test_cli_missing_manifest_exits_1(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        _sys,
        "argv",
        ["verify_contracts", "--repo-root", str(tmp_path), "--manifest", "no.yaml"],
    )
    with pytest.raises(SystemExit) as e:
        vc.main()
    assert e.value.code == 1


def test_cli_pass(tmp_path: Path, monkeypatch, capsys) -> None:
    _write_manifest(tmp_path, {"required_files": [], "reference_targets": []})
    monkeypatch.setattr(
        _sys,
        "argv",
        [
            "verify_contracts",
            "--repo-root",
            str(tmp_path),
            "--manifest",
            "manifest.yaml",
        ],
    )
    vc.main()
    assert "passed" in capsys.readouterr().out.lower()


def test_cli_violations_exit_1(tmp_path: Path, monkeypatch) -> None:
    _write_manifest(
        tmp_path,
        {"required_files": [{"path": "missing.md"}], "reference_targets": []},
    )
    monkeypatch.setattr(
        _sys,
        "argv",
        [
            "verify_contracts",
            "--repo-root",
            str(tmp_path),
            "--manifest",
            "manifest.yaml",
        ],
    )
    with pytest.raises(SystemExit) as e:
        vc.main()
    assert e.value.code == 1
