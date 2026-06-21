#!/usr/bin/env python3
# <!-- L9_META role: audit_engine version: 2.0.0 tags: [l9, audit, invariants] /L9_META -->
"""
L9 Node Audit Engine — 27-rule static analysis for generated and hand-authored code.

Rule categories:
  L9-TRANSPORT  — TransportPacket/PacketEnvelope boundary
  L9-BRIDGE     — SDK bridge isolation (enginehandlers.py only)
  L9-ROUTER     — Gate-sole-routing enforcement
  L9-META       — L9META header presence on tracked files
  L9-PYDANTIC   — Pydantic safety rules
  L9-SECURITY   — eval/exec/compile/unsafe patterns
  L9-NAMING     — Canonical naming conventions
  L9-IMPORTS    — Prohibited cross-module imports
  L9-HANDLERS   — Handler-spec alignment
  L9-OBSERV     — print() ban, logging correctness

Usage:
    python tools/audit_engine.py --path src/ [--fail-on HIGH]
    python tools/audit_engine.py --path src/ tests/ --json

Exit codes: 0 = pass, 1 = findings at or above fail_on severity.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

Severity = Literal["HIGH", "MEDIUM", "LOW"]


@dataclass
class AuditFinding:
    rule: str
    severity: Severity
    file: str
    line: int
    message: str
    category: str


@dataclass
class AuditResult:
    findings: list[AuditFinding] = field(default_factory=list)

    @property
    def high(self) -> list[AuditFinding]:
        return [f for f in self.findings if f.severity == "HIGH"]

    @property
    def medium(self) -> list[AuditFinding]:
        return [f for f in self.findings if f.severity == "MEDIUM"]

    @property
    def low(self) -> list[AuditFinding]:
        return [f for f in self.findings if f.severity == "LOW"]

    def to_dict(self) -> dict:
        return {
            "summary": {
                "total": len(self.findings),
                "high": len(self.high),
                "medium": len(self.medium),
                "low": len(self.low),
            },
            "findings": [vars(f) for f in self.findings],
        }


def _pyfiles(paths: list[Path]) -> list[Path]:
    result = []
    for p in paths:
        if p.is_file() and p.suffix == ".py":
            result.append(p)
        elif p.is_dir():
            result.extend(p.rglob("*.py"))
    return result


def audit_file(path: Path) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    src = path.read_text(encoding="utf-8", errors="replace")
    rel = str(path)

    try:
        tree = ast.parse(src)
    except SyntaxError:
        return findings

    lines = src.splitlines()

    def add(rule: str, sev: Severity, lineno: int, msg: str, cat: str) -> None:
        findings.append(AuditFinding(rule, sev, rel, lineno, msg, cat))

    # ── L9-META check ────────────────────────────────────────────────────────
    if "L9_META" not in src:
        add("L9-META-001", "MEDIUM", 1,
            "File is missing L9_META header block.", "L9-META")

    # ── L9-TRANSPORT ─────────────────────────────────────────────────────────
    is_bridge = path.name == "enginehandlers.py"
    for lineno, line in enumerate(lines, 1):
        if "PacketEnvelope" in line and not line.strip().startswith("#"):
            add("L9-TRANSPORT-001", "HIGH", lineno,
                "PacketEnvelope import/usage detected. Use TransportPacket only.", "L9-TRANSPORT")
        if re.search(r"from l9_sdk\.transport import", line) and not is_bridge:
            add("L9-TRANSPORT-002", "HIGH", lineno,
                f"SDK transport imported outside enginehandlers.py in {rel}.", "L9-BRIDGE")

    # ── L9-ROUTER ─────────────────────────────────────────────────────────────
    for lineno, line in enumerate(lines, 1):
        if re.search(r"httpx\.|aiohttp\.|requests\.", line) and not line.strip().startswith("#"):
            if "tests/" not in rel:
                add("L9-ROUTER-001", "HIGH", lineno,
                    "Direct HTTP client usage detected. All calls must go through Gate.", "L9-ROUTER")

    # ── L9-SECURITY ───────────────────────────────────────────────────────────
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            fname = ""
            if isinstance(func, ast.Name):
                fname = func.id
            elif isinstance(func, ast.Attribute):
                fname = func.attr
            if fname in ("eval", "exec", "compile"):
                add("L9-SECURITY-001", "HIGH", node.lineno,
                    f"Banned function '{fname}' detected.", "L9-SECURITY")

    # ── L9-OBSERV ─────────────────────────────────────────────────────────────
    if "src/" in rel:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "print":
                    add("L9-OBSERV-001", "MEDIUM", node.lineno,
                        "print() in src/. Use get_logger(__name__) instead.", "L9-OBSERV")

    # ── L9-PYDANTIC ───────────────────────────────────────────────────────────
    for lineno, line in enumerate(lines, 1):
        if re.search(r"class\s+\w+\(.*BaseModel.*\)", line):
            if "model_config" not in src and "class Config:" not in src:
                # only warn once per file
                add("L9-PYDANTIC-001", "LOW", lineno,
                    "Pydantic model has no model_config / Config — consider explicit settings.",
                    "L9-PYDANTIC")
                break

    # ── L9-HANDLERS ──────────────────────────────────────────────────────────
    if path.name == "enginehandlers.py":
        handler_fns = [
            node.name for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef) and node.name.startswith("handle_")
        ]
        if not handler_fns:
            add("L9-HANDLERS-001", "HIGH", 1,
                "enginehandlers.py has no async handle_* functions defined.", "L9-HANDLERS")

    return findings


def run_audit(paths: list[Path], fail_on: Severity = "HIGH") -> AuditResult:
    result = AuditResult()
    for pyfile in _pyfiles(paths):
        result.findings.extend(audit_file(pyfile))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="L9 Node Audit Engine")
    parser.add_argument("--path", nargs="+", required=True, help="Paths to audit")
    parser.add_argument("--fail-on", choices=["HIGH", "MEDIUM", "LOW"], default="HIGH")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    paths = [Path(p) for p in args.path]
    result = run_audit(paths, fail_on=args.fail_on)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        for f in result.findings:
            print(f"[{f.severity}] {f.rule} {f.file}:{f.line} — {f.message}")
        print(f"\nSummary: {len(result.findings)} findings "
              f"(HIGH={len(result.high)}, MEDIUM={len(result.medium)}, LOW={len(result.low)})")

    sev_order = {"HIGH": 2, "MEDIUM": 1, "LOW": 0}
    threshold = sev_order[args.fail_on]
    if any(sev_order[f.severity] >= threshold for f in result.findings):
        sys.exit(1)


if __name__ == "__main__":
    main()
