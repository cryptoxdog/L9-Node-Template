#!/usr/bin/env python3
"""L9 Repo Normalizer v1.0.0

Validates and enforces the L9 repo layout contract.

Design goals:
- Idempotent: running multiple times produces identical results.
- Auditable: emits a structured JSON report to docs/repo_normalization_report.json.
- Safe: creates missing directories/stub files only; never deletes or overwrites.
- Graphable: report record is suitable for emission to the L9 knowledge graph.
- Modular: checks are registered functions, easy to extend.

Usage:
    uv run python scripts/repo_normalizer_v1.0.0.py          # check + fix
    uv run python scripts/repo_normalizer_v1.0.0.py --check  # check only, exit 1 if violations
    uv run python scripts/repo_normalizer_v1.0.0.py --report # print JSON report and exit
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

VERSION = "1.0.0"
REPORT_PATH = Path("docs/repo_normalization_report.json")

REQUIRED_DIRS = [
    "src",
    "tests",
    "scripts",
    "docs",
    "observability",
    ".cursor/rules",
    ".cursor/rules/templates",
    ".devcontainer",
    ".github/workflows",
    ".vscode",
]

REQUIRED_ROOT_FILES = [
    "pyproject.toml",
    "uv.lock",
    ".python-version",
    ".gitignore",
    ".pre-commit-config.yaml",
    "README.md",
    "AGENTS.md",
    ".env.example",
    "plugin-config.yaml",
    "Makefile",
    "Justfile",
]

REQUIRED_SCRIPTS = [
    "scripts/render_cursor_rules.py",
    "scripts/repo_normalizer_v1.0.0.py",
]

REQUIRED_CI = [
    ".github/workflows/ci.yml",
]

STUB_CONTENT: dict[str, str] = {
    "README.md": "# Project\n\nReplace this stub.\n",
    "AGENTS.md": "# Agents\n\nReplace this stub.\n",
    ".env.example": "# Environment variables\n",
    "plugin-config.yaml": (
        "plugin_version: \"1.0.0\"\nrepo_name: \"my-service\"\ndomain: \"my-domain\"\n"
        "protected_paths: []\nhigh_risk_commands: []\nci_gates: []\n"
        "package_name: \"my_service\"\napp_entrypoint: \"my_service.main:app\"\n"
        "python_version: \"3.12\"\nvenv_path: \".venv/bin/python\"\n"
    ),
}


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str
    path: str = ""

    def is_violation(self) -> bool:
        return self.status == "violation"

    def is_fixed(self) -> bool:
        return self.status == "fixed"


@dataclass
class NormalizationReport:
    schema: str = "l9.repo_normalizer.report.v1"
    version: str = VERSION
    repo_root: str = ""
    generated_at: str = ""
    check_only: bool = False
    results: list[CheckResult] = field(default_factory=list)
    violations: int = 0
    fixed: int = 0
    ok: int = 0

    def summary(self) -> str:
        return (
            f"ok={self.ok} fixed={self.fixed} violations={self.violations} "
            f"(check_only={self.check_only})"
        )

    def to_dict(self) -> dict:
        d = asdict(self)
        d["results"] = [asdict(r) for r in self.results]
        return d


CheckFn = Callable[[Path, bool], list[CheckResult]]
_CHECKS: list[CheckFn] = []


def check(fn: CheckFn) -> CheckFn:
    _CHECKS.append(fn)
    return fn


@check
def check_required_dirs(root: Path, check_only: bool) -> list[CheckResult]:
    results = []
    for rel in REQUIRED_DIRS:
        p = root / rel
        if p.exists():
            results.append(CheckResult("required_dir", "ok", "exists", rel))
        elif check_only:
            results.append(CheckResult("required_dir", "violation", "missing directory", rel))
        else:
            p.mkdir(parents=True, exist_ok=True)
            results.append(CheckResult("required_dir", "fixed", "created directory", rel))
    return results


@check
def check_required_root_files(root: Path, check_only: bool) -> list[CheckResult]:
    results = []
    for rel in REQUIRED_ROOT_FILES:
        p = root / rel
        if p.exists():
            results.append(CheckResult("required_file", "ok", "exists", rel))
        elif check_only:
            results.append(CheckResult("required_file", "violation", "missing file", rel))
        else:
            stub = STUB_CONTENT.get(rel, f"# {rel} — stub created by repo_normalizer\n")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(stub, encoding="utf-8")
            results.append(CheckResult("required_file", "fixed", "created stub", rel))
    return results


@check
def check_required_scripts(root: Path, check_only: bool) -> list[CheckResult]:  # noqa: ARG001
    results = []
    for rel in REQUIRED_SCRIPTS:
        p = root / rel
        if p.exists():
            results.append(CheckResult("required_script", "ok", "exists", rel))
        else:
            results.append(CheckResult(
                "required_script", "violation",
                f"missing script — add manually: {rel}", rel,
            ))
    return results


@check
def check_required_ci(root: Path, check_only: bool) -> list[CheckResult]:
    results = []
    for rel in REQUIRED_CI:
        p = root / rel
        if p.exists():
            results.append(CheckResult("required_ci", "ok", "exists", rel))
        elif check_only:
            results.append(CheckResult("required_ci", "violation", "missing CI config", rel))
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("# ci.yml stub — replace with full CI config\n", encoding="utf-8")
            results.append(CheckResult("required_ci", "fixed", "created stub", rel))
    return results


@check
def check_src_package(root: Path, check_only: bool) -> list[CheckResult]:
    src = root / "src"
    if not src.exists():
        return [CheckResult("src_package", "violation", "src/ directory missing", "src")]
    packages = [d for d in src.iterdir() if d.is_dir() and (d / "__init__.py").exists()]
    if packages:
        return [CheckResult("src_package", "ok", f"found {len(packages)} package(s)", "src")]
    if check_only:
        return [CheckResult("src_package", "violation", "no Python package found in src/", "src")]
    pkg = src / "my_service"
    pkg.mkdir(exist_ok=True)
    (pkg / "__init__.py").write_text('"""my_service package stub."""\n', encoding="utf-8")
    return [CheckResult("src_package", "fixed", "created stub package src/my_service/", "src/my_service")]


@check
def check_plugin_config_keys(root: Path, check_only: bool) -> list[CheckResult]:  # noqa: ARG001
    p = root / "plugin-config.yaml"
    if not p.exists():
        return [CheckResult("plugin_config", "violation", "plugin-config.yaml missing", "plugin-config.yaml")]
    try:
        import yaml  # noqa: PLC0415
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001
        return [CheckResult("plugin_config", "violation", f"parse error: {exc}", "plugin-config.yaml")]
    required_keys = {"plugin_version", "repo_name", "domain", "package_name", "python_version"}
    missing = required_keys - set(data.keys())
    if not missing:
        return [CheckResult("plugin_config", "ok", "all required keys present", "plugin-config.yaml")]
    return [CheckResult("plugin_config", "violation", f"missing keys: {sorted(missing)}", "plugin-config.yaml")]


def run_checks(root: Path, *, check_only: bool) -> NormalizationReport:
    report = NormalizationReport(
        repo_root=str(root.resolve()),
        generated_at=datetime.now(UTC).isoformat(),
        check_only=check_only,
    )
    for fn in _CHECKS:
        for result in fn(root, check_only):
            report.results.append(result)
            if result.is_violation():
                report.violations += 1
            elif result.is_fixed():
                report.fixed += 1
            else:
                report.ok += 1
    return report


def write_report(report: NormalizationReport, root: Path) -> Path:
    path = root / REPORT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check only; exit 1 if violations found")
    parser.add_argument("--report", action="store_true", help="Print JSON report to stdout and exit")
    parser.add_argument("--root", default=".", help="Repo root directory (default: cwd)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = Path(args.root).resolve()
    report = run_checks(root, check_only=args.check)
    if args.report:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0
    report_path = write_report(report, root)
    status = "CHECK" if args.check else "NORMALIZE"
    print(f"[{status}] {report.summary()} → {report_path.relative_to(root)}")
    if report.violations:
        print(f"\nVIOLATIONS ({report.violations}):")
        for r in report.results:
            if r.is_violation():
                print(f"  ✗ [{r.name}] {r.path}: {r.detail}")
        if args.check:
            return 1
    if report.fixed:
        print(f"\nFIXED ({report.fixed}):")
        for r in report.results:
            if r.is_fixed():
                print(f"  ✓ [{r.name}] {r.path}: {r.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
