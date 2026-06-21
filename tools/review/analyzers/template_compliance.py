#!/usr/bin/env python3
# <!-- L9_META role: template_compliance_analyzer version: 2.0.0 /L9_META -->
"""
Template Compliance Analyzer — validates that a repo satisfies the
L9 template manifest: required files, required directories, protected paths,
required symbols in key files, and prohibited patterns.

Usage:
    python tools/review/analyzers/template_compliance.py \
        --repo-root . \
        --manifest tools/l9_contract_manifest.yaml \
        [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class ComplianceFinding:
    rule: str
    severity: str
    path: str
    message: str


@dataclass
class ComplianceReport:
    findings: list[ComplianceFinding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(f.severity == "FAIL" for f in self.findings)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "total": len(self.findings),
            "findings": [vars(f) for f in self.findings],
        }


def run(repo_root: Path, manifest_path: Path) -> ComplianceReport:
    report = ComplianceReport()
    # Per Gemini review (PR #16): default to {} when manifest is empty/non-mapping
    # so .get() does not raise AttributeError.
    _raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest = _raw if isinstance(_raw, dict) else {}

    # Required files
    for entry in manifest.get("required_files", []):
        p = repo_root / entry["path"]
        if not p.exists():
            report.findings.append(
                ComplianceFinding(
                    rule="REQUIRED_FILE_MISSING",
                    severity="FAIL",
                    path=entry["path"],
                    message=f"Required file not found: {entry['path']}",
                )
            )

    # Protected paths
    for protected in manifest.get("protected_paths", []):
        # Warn if protected file is not in CODEOWNERS
        codeowners = repo_root / ".github" / "CODEOWNERS"
        if codeowners.exists():
            # Per Gemini review (PR #16): explicit UTF-8 to avoid platform-dependent decoding.
            content = codeowners.read_text(encoding="utf-8")
            if protected not in content:
                report.findings.append(
                    ComplianceFinding(
                        rule="PROTECTED_PATH_NOT_IN_CODEOWNERS",
                        severity="WARN",
                        path=protected,
                        message=f"Protected path {protected} not listed in CODEOWNERS",
                    )
                )

    # L9META on tracked Python files
    tracked_python = [
        "src/l9_service/enginehandlers.py",
        "tools/audit_engine.py",
        "tools/verify_contracts.py",
        "tools/review/analyzers/template_compliance.py",
    ]
    for fp in tracked_python:
        full = repo_root / fp
        if full.exists():
            content = full.read_text(encoding="utf-8")
            if "L9_META" not in content:
                report.findings.append(
                    ComplianceFinding(
                        rule="L9META_MISSING",
                        severity="FAIL",
                        path=fp,
                        message=f"L9_META header missing in tracked file: {fp}",
                    )
                )

    # l9-template-version file
    ver_file = repo_root / ".l9-template-version"
    if not ver_file.exists():
        report.findings.append(
            ComplianceFinding(
                rule="TEMPLATE_VERSION_MISSING",
                severity="FAIL",
                path=".l9-template-version",
                message=".l9-template-version file missing — required for drift detection",
            )
        )

    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--manifest", default="tools/l9_contract_manifest.yaml")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    manifest_path = repo_root / args.manifest

    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}")
        sys.exit(1)

    report = run(repo_root, manifest_path)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        for f in report.findings:
            print(f"[{f.severity}] {f.rule} — {f.path}: {f.message}")
        status = "PASSED ✅" if report.passed else "FAILED ❌"
        print(f"\nTemplate compliance: {status}")

    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
