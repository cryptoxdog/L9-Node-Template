"""Tests for tools/review/analyzers/template_compliance.py"""

from __future__ import annotations

import importlib.util as _ilu
import json
import sys as _sys
from pathlib import Path

import pytest
import yaml

_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "review"
    / "analyzers"
    / "template_compliance.py"
)
_spec = _ilu.spec_from_file_location("template_compliance", _SCRIPT)
tc = _ilu.module_from_spec(_spec)
_sys.modules["template_compliance"] = tc
_spec.loader.exec_module(tc)  # type: ignore[union-attr]


def _scaffold(tmp_path: Path, manifest: dict, *, with_codeowners: bool = True) -> Path:
    m = tmp_path / "manifest.yaml"
    m.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    if with_codeowners:
        (tmp_path / ".github").mkdir(parents=True, exist_ok=True)
        (tmp_path / ".github" / "CODEOWNERS").write_text("", encoding="utf-8")
    (tmp_path / ".l9-template-version").write_text("v1\n", encoding="utf-8")
    return m


def test_compliance_finding_dataclass() -> None:
    f = tc.ComplianceFinding(rule="R", severity="FAIL", path="p", message="m")
    assert f.rule == "R"
    assert f.severity == "FAIL"


def test_report_passed_when_only_warn(tmp_path: Path) -> None:
    r = tc.ComplianceReport()
    r.findings.append(tc.ComplianceFinding("R", "WARN", "p", "m"))
    assert r.passed is True


def test_report_failed_when_any_fail(tmp_path: Path) -> None:
    r = tc.ComplianceReport()
    r.findings.append(tc.ComplianceFinding("R", "FAIL", "p", "m"))
    assert r.passed is False
    d = r.to_dict()
    assert d["passed"] is False
    assert d["total"] == 1


def test_run_required_file_missing(tmp_path: Path) -> None:
    m = _scaffold(tmp_path, {"required_files": [{"path": "missing.md"}]})
    report = tc.run(tmp_path, m)
    assert any(f.rule == "REQUIRED_FILE_MISSING" for f in report.findings)
    assert report.passed is False


def test_run_protected_not_in_codeowners_warns(tmp_path: Path) -> None:
    m = _scaffold(
        tmp_path,
        {"required_files": [], "protected_paths": ["src/critical.py"]},
    )
    report = tc.run(tmp_path, m)
    assert any(
        f.rule == "PROTECTED_PATH_NOT_IN_CODEOWNERS" and f.severity == "WARN"
        for f in report.findings
    )
    # WARN does not fail
    assert report.passed is True


def test_run_template_version_missing(tmp_path: Path) -> None:
    m = tmp_path / "manifest.yaml"
    m.write_text(yaml.safe_dump({"required_files": []}), encoding="utf-8")
    # no .l9-template-version
    report = tc.run(tmp_path, m)
    assert any(f.rule == "TEMPLATE_VERSION_MISSING" for f in report.findings)


def test_run_handles_empty_manifest(tmp_path: Path) -> None:
    """Per Gemini review: empty manifest must not raise."""
    (tmp_path / ".l9-template-version").write_text("v1\n")
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "CODEOWNERS").write_text("")
    m = tmp_path / "empty.yaml"
    m.write_text("", encoding="utf-8")
    report = tc.run(tmp_path, m)
    assert report.passed is True


def test_run_passes_when_clean(tmp_path: Path) -> None:
    m = _scaffold(tmp_path, {"required_files": []})
    report = tc.run(tmp_path, m)
    assert report.passed is True


def test_cli_json_pass(tmp_path: Path, monkeypatch, capsys) -> None:
    _scaffold(tmp_path, {"required_files": []})
    monkeypatch.setattr(
        _sys,
        "argv",
        [
            "template_compliance",
            "--repo-root",
            str(tmp_path),
            "--manifest",
            "manifest.yaml",
            "--json",
        ],
    )
    with pytest.raises(SystemExit) as e:
        tc.main()
    assert e.value.code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["passed"] is True


def test_cli_missing_manifest_exits_1(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        _sys,
        "argv",
        [
            "template_compliance",
            "--repo-root",
            str(tmp_path),
            "--manifest",
            "no.yaml",
        ],
    )
    with pytest.raises(SystemExit) as e:
        tc.main()
    assert e.value.code == 1


def test_cli_text_fail(tmp_path: Path, monkeypatch, capsys) -> None:
    _scaffold(tmp_path, {"required_files": [{"path": "missing.md"}]})
    monkeypatch.setattr(
        _sys,
        "argv",
        [
            "template_compliance",
            "--repo-root",
            str(tmp_path),
            "--manifest",
            "manifest.yaml",
        ],
    )
    with pytest.raises(SystemExit) as e:
        tc.main()
    assert e.value.code == 1
    assert "FAILED" in capsys.readouterr().out
