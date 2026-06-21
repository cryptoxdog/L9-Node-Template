"""Tests for tools/audit_engine.py — exercises core audit rules and CLI."""

from __future__ import annotations

import importlib.util as _ilu
import json
import sys as _sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "audit_engine.py"
_spec = _ilu.spec_from_file_location("audit_engine", _SCRIPT)
audit = _ilu.module_from_spec(_spec)
_sys.modules["audit_engine"] = audit
_spec.loader.exec_module(audit)  # type: ignore[union-attr]


def _write(tmp_path: Path, rel: str, body: str) -> Path:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def test_l9_meta_missing_flagged(tmp_path: Path) -> None:
    f = _write(tmp_path, "src/x.py", "x = 1\n")
    findings = audit.audit_file(f)
    rules = [f.rule for f in findings]
    assert "L9-META-001" in rules


def test_l9_meta_present_not_flagged(tmp_path: Path) -> None:
    f = _write(tmp_path, "src/x.py", "# L9_META role: test /L9_META\nx = 1\n")
    findings = audit.audit_file(f)
    assert "L9-META-001" not in [f.rule for f in findings]


def test_l9_transport_packet_envelope_high(tmp_path: Path) -> None:
    f = _write(
        tmp_path,
        "src/y.py",
        "# L9_META /L9_META\nfrom somewhere import PacketEnvelope\n",
    )
    findings = audit.audit_file(f)
    assert any(x.rule == "L9-TRANSPORT-001" and x.severity == "HIGH" for x in findings)


def test_l9_router_direct_http_in_src(tmp_path: Path) -> None:
    f = _write(
        tmp_path,
        "src/svc.py",
        "# L9_META /L9_META\nimport httpx\nhttpx.get('https://x')\n",
    )
    findings = audit.audit_file(f)
    assert any(x.rule == "L9-ROUTER-001" for x in findings)


def test_l9_router_catches_import_form(tmp_path: Path) -> None:
    """Per Gemini review: must catch `import httpx` and `from httpx import X` too."""
    for body in (
        "# L9_META /L9_META\nimport requests\n",
        "# L9_META /L9_META\nfrom httpx import AsyncClient\n",
        "# L9_META /L9_META\nimport aiohttp\n",
    ):
        f = _write(tmp_path, "src/x.py", body)
        findings = audit.audit_file(f)
        assert any(x.rule == "L9-ROUTER-001" for x in findings), body


def test_l9_transport_catches_bare_import(tmp_path: Path) -> None:
    """Per Gemini review: must catch `import l9_sdk.transport` and bare dotted refs."""
    for body in (
        "# L9_META /L9_META\nimport l9_sdk.transport\n",
        "# L9_META /L9_META\nx = l9_sdk.transport.TransportPacket\n",
        "# L9_META /L9_META\nfrom l9_sdk.transport import X\n",
    ):
        f = _write(tmp_path, "src/x.py", body)
        findings = audit.audit_file(f)
        assert any(x.rule == "L9-TRANSPORT-002" for x in findings), body


def test_l9_router_skipped_in_tests(tmp_path: Path) -> None:
    f = _write(
        tmp_path,
        "tests/test_x.py",
        "# L9_META /L9_META\nimport httpx\nhttpx.get('https://x')\n",
    )
    findings = audit.audit_file(f)
    assert not any(x.rule == "L9-ROUTER-001" for x in findings)


def test_l9_security_eval_flagged(tmp_path: Path) -> None:
    f = _write(tmp_path, "src/z.py", "# L9_META /L9_META\neval('1+1')\n")
    findings = audit.audit_file(f)
    assert any(x.rule == "L9-SECURITY-001" for x in findings)


def test_l9_observ_print_in_src_flagged(tmp_path: Path) -> None:
    f = _write(tmp_path, "src/p.py", "# L9_META /L9_META\nprint('hi')\n")
    findings = audit.audit_file(f)
    assert any(x.rule == "L9-OBSERV-001" for x in findings)


def test_l9_pydantic_missing_config_warned(tmp_path: Path) -> None:
    body = (
        "# L9_META /L9_META\nfrom pydantic import BaseModel\nclass M(BaseModel):\n    x: int = 1\n"
    )
    f = _write(tmp_path, "src/m.py", body)
    findings = audit.audit_file(f)
    assert any(x.rule == "L9-PYDANTIC-001" for x in findings)


def test_l9_pydantic_config_present_not_warned(tmp_path: Path) -> None:
    body = (
        "# L9_META /L9_META\n"
        "from pydantic import BaseModel, ConfigDict\n"
        "class M(BaseModel):\n"
        "    model_config = ConfigDict()\n"
        "    x: int = 1\n"
    )
    f = _write(tmp_path, "src/m.py", body)
    findings = audit.audit_file(f)
    assert not any(x.rule == "L9-PYDANTIC-001" for x in findings)


def test_l9_handlers_empty_engine_flagged(tmp_path: Path) -> None:
    f = _write(tmp_path, "src/enginehandlers.py", "# L9_META /L9_META\nx = 1\n")
    findings = audit.audit_file(f)
    assert any(x.rule == "L9-HANDLERS-001" for x in findings)


def test_l9_handlers_with_handler_not_flagged(tmp_path: Path) -> None:
    body = "# L9_META /L9_META\nasync def handle_foo():\n    return None\n"
    f = _write(tmp_path, "src/enginehandlers.py", body)
    findings = audit.audit_file(f)
    assert not any(x.rule == "L9-HANDLERS-001" for x in findings)


def test_syntax_error_returns_empty(tmp_path: Path) -> None:
    f = _write(tmp_path, "src/bad.py", "# L9_META /L9_META\ndef (")
    findings = audit.audit_file(f)
    assert findings == []


def test_pyfiles_collects_recursively(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "one.py").write_text("")
    (tmp_path / "a" / "skip.txt").write_text("")
    (tmp_path / "two.py").write_text("")
    files = audit._pyfiles([tmp_path])
    names = sorted(p.name for p in files)
    assert names == ["one.py", "two.py"]


def test_audit_result_summary() -> None:
    r = audit.AuditResult()
    r.findings.append(audit.AuditFinding("R", "HIGH", "f.py", 1, "m", "C"))
    r.findings.append(audit.AuditFinding("R", "MEDIUM", "f.py", 2, "m", "C"))
    r.findings.append(audit.AuditFinding("R", "LOW", "f.py", 3, "m", "C"))
    d = r.to_dict()
    assert d["summary"]["total"] == 3
    assert d["summary"]["high"] == 1
    assert d["summary"]["medium"] == 1
    assert d["summary"]["low"] == 1


def test_run_audit_pipeline(tmp_path: Path) -> None:
    _write(tmp_path, "x.py", "x = 1\n")
    result = audit.run_audit([tmp_path])
    # missing L9_META should produce at least one finding
    assert any(f.rule == "L9-META-001" for f in result.findings)


def test_cli_json_output(tmp_path: Path, monkeypatch, capsys) -> None:
    _write(tmp_path, "x.py", "# L9_META /L9_META\nx = 1\n")
    monkeypatch.setattr(_sys, "argv", ["audit_engine", "--path", str(tmp_path), "--json"])
    audit.main()
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "summary" in data
    assert "findings" in data


def test_cli_text_output(tmp_path: Path, monkeypatch, capsys) -> None:
    _write(tmp_path, "x.py", "# L9_META /L9_META\nx = 1\n")
    monkeypatch.setattr(_sys, "argv", ["audit_engine", "--path", str(tmp_path)])
    audit.main()  # no exit because no HIGH findings
    out = capsys.readouterr().out
    assert "Summary:" in out


def test_cli_fail_on_high(tmp_path: Path, monkeypatch) -> None:
    _write(
        tmp_path,
        "src/bad.py",
        "# L9_META /L9_META\nimport httpx\nhttpx.get('https://x')\n",
    )
    monkeypatch.setattr(
        _sys, "argv", ["audit_engine", "--path", str(tmp_path), "--fail-on", "HIGH"]
    )
    with pytest.raises(SystemExit) as e:
        audit.main()
    assert e.value.code == 1
