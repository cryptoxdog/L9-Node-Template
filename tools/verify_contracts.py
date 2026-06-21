#!/usr/bin/env python3
# <!-- L9_META role: contract_verifier version: 2.0.0 tags: [l9, contracts, verification] /L9_META -->
"""
L9 Contract Verifier — checks that all contracts in the template manifest
exist on disk and are referenced in key instruction files.

Usage:
    python tools/verify_contracts.py [--repo-root .] [--manifest tools/l9_contract_manifest.yaml]

Exit: 0 = pass, 1 = violation.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import yaml


def sha256_12(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def load_manifest(manifest_path: Path) -> dict:
    return yaml.safe_load(manifest_path.read_text(encoding="utf-8"))


def verify(repo_root: Path, manifest_path: Path) -> list[str]:
    violations: list[str] = []
    # Per Gemini review (PR #16): default to {} when manifest is empty/non-mapping
    # so .get() does not raise AttributeError.
    _raw = load_manifest(manifest_path)
    manifest = _raw if isinstance(_raw, dict) else {}

    required_files: list[dict] = manifest.get("required_files", [])
    reference_targets: list[str] = manifest.get("reference_targets", [])

    for entry in required_files:
        path = repo_root / entry["path"]
        if not path.exists():
            violations.append(f"MISSING required file: {entry['path']}")
            continue

        # Optional SHA check
        expected_sha = entry.get("sha256_12")
        if expected_sha:
            actual = sha256_12(path)
            if actual != expected_sha:
                violations.append(
                    f"SHA DRIFT {entry['path']}: expected {expected_sha}, got {actual}"
                )

    # Check reference targets contain required mentions
    for ref_file in reference_targets:
        ref_path = repo_root / ref_file
        if not ref_path.exists():
            violations.append(f"MISSING reference target: {ref_file}")
            continue
        content = ref_path.read_text(encoding="utf-8")
        for entry in required_files:
            mention = entry.get("must_be_mentioned_in")
            if mention and ref_file in mention and entry["path"] not in content:
                violations.append(
                    f"CONTRACT NOT MENTIONED: {entry['path']} missing from {ref_file}"
                )

    return violations


def main() -> None:
    parser = argparse.ArgumentParser(description="L9 Contract Verifier")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--manifest", default="tools/l9_contract_manifest.yaml")
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    manifest_path = repo_root / args.manifest

    if not manifest_path.exists():
        print(f"ERROR: manifest not found at {manifest_path}")
        sys.exit(1)

    violations = verify(repo_root, manifest_path)

    if violations:
        for v in violations:
            print(f"[VIOLATION] {v}")
        print(f"\n{len(violations)} contract violation(s).")
        sys.exit(1)

    print("All contract verifications passed ✅")


if __name__ == "__main__":
    main()
