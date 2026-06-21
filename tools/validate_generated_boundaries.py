#!/usr/bin/env python3
# L9_META
# role: generated_boundary_validator
# version: 1.0.0
# status: template_tool
# tags: [l9, validation, generated_files, boundaries]
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "src" / "l9_service" / "enginehandlers.py"
REQUIRED_MARKERS = [
    "GENERATED FILE",
    "generated_by: l9-codegen-engine",
    "source_contract: nodespec.yaml",
    "hand_editing: forbidden",
]
FORBIDDEN_TEMPLATE_OWNED_GENERATOR_TERMS = [
    "def " + "generate_handler",
    "class " + "HandlerGenerator",
    "nodespec " + "parsing",
    "parse_" + "nodespec",
]


def main() -> int:
    if not ENGINE.exists():
        print(f"[FAIL] missing {ENGINE.relative_to(ROOT)}")
        return 1
    text = ENGINE.read_text(encoding="utf-8")
    failures = [marker for marker in REQUIRED_MARKERS if marker not in text]
    for marker in failures:
        print(f"[FAIL] missing marker in enginehandlers.py: {marker}")
    for path in [ROOT / "src", ROOT / "tools"]:
        for py in path.rglob("*.py"):
            rel = py.relative_to(ROOT)
            if rel.as_posix() == "src/l9_service/enginehandlers.py":
                continue
            body = py.read_text(encoding="utf-8", errors="replace")
            if rel.as_posix() not in {
                "tools/audit_engine.py",
                "tools/validate_generated_boundaries.py",
            }:
                # Broadened per Gemini review: catches `from l9_sdk.transport import X`,
                # `import l9_sdk.transport`, `from l9_sdk import transport`, etc.
                if "l9_sdk.transport" in body:
                    print(f"[FAIL] SDK transport reference/import outside enginehandlers.py: {rel}")
                    failures.append(str(rel))
                legacy_marker = "Packet" + "Envelope"
                if legacy_marker in body:
                    print(f"[FAIL] legacy envelope reference found: {rel}")
                    failures.append(str(rel))
            for term in FORBIDDEN_TEMPLATE_OWNED_GENERATOR_TERMS:
                if term in body:
                    print(
                        f"[FAIL] generator ownership term found in template-owned file {rel}: {term}"
                    )
                    failures.append(str(rel))
    if failures:
        return 1
    print("Generated boundary validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
