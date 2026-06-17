#!/usr/bin/env python3
"""
L9 PR Classifier — Routes CI jobs based on changed files.

Required outputs (emitted to GITHUB_OUTPUT):
  - run_lint: boolean
  - run_test: boolean
  - run_security: boolean
  - run_infrastructure: boolean
  - is_docs_only: boolean
  - requires_human_review: boolean
  - detected_labels: comma-separated string

Routing logic:
  - Changed files are the primary signal.
  - Unknown extensions fail closed (all gates run).
  - Labels are hints only — evidence beats labels.
"""
import os
import subprocess
import sys

# --- Extension-to-class mapping ---

CODE_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".go", ".rs", ".java", ".rb"}
INFRA_EXTENSIONS = {".tf", ".hcl", ".yaml", ".yml", ".toml"}
DOC_EXTENSIONS = {".md", ".rst", ".txt"}
CI_PATTERNS = {".github/"}
SECURITY_PATTERNS = {".semgrep", ".gitleaks", "security"}

# --- Helpers ---

def get_changed_files():
    """Get list of changed files vs main."""
    # Try git diff first (works locally and in CI with fetch-depth: 0)
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "origin/main...HEAD"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split("\n")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback: check GITHUB_EVENT_PATH for PR changed files
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if event_path and os.path.exists(event_path):
        import json
        with open(event_path) as f:
            event = json.load(f)
        # For pull_request events, list files via API would be needed
        # Fall through to fail-closed behavior
        pass

    return []


def classify(changed_files):
    """Classify changed files and determine which gates to run."""
    run_lint = False
    run_test = False
    run_security = False
    run_infrastructure = False
    is_docs_only = True
    requires_human_review = False
    detected_labels = set()

    if not changed_files:
        # No files detected — fail closed
        return {
            "run_lint": "true",
            "run_test": "true",
            "run_security": "true",
            "run_infrastructure": "true",
            "is_docs_only": "false",
            "requires_human_review": "true",
            "detected_labels": "type:ci",
        }

    for filepath in changed_files:
        ext = os.path.splitext(filepath)[1].lower()
        filepath_lower = filepath.lower()

        # Code files
        if ext in CODE_EXTENSIONS:
            run_lint = True
            run_test = True
            run_security = True
            is_docs_only = False
            detected_labels.add("type:feature")

        # Infrastructure files
        elif ext in INFRA_EXTENSIONS or any(p in filepath_lower for p in [".tf", "terraform", "infra"]):
            run_lint = True
            run_infrastructure = True
            run_security = True
            is_docs_only = False
            detected_labels.add("area:infrastructure")

        # CI/workflow files
        elif any(filepath_lower.startswith(p) for p in CI_PATTERNS):
            run_lint = True
            run_security = True
            is_docs_only = False
            detected_labels.add("type:ci")
            detected_labels.add("area:workflows")

        # Documentation files
        elif ext in DOC_EXTENSIONS or filepath_lower.startswith("docs/"):
            detected_labels.add("type:docs")
            # Lint is advisory for docs, but we still run it
            run_lint = True

        # Security-related files
        elif any(p in filepath_lower for p in SECURITY_PATTERNS):
            run_security = True
            is_docs_only = False
            detected_labels.add("type:security")

        # Unknown extension — fail closed
        else:
            run_lint = True
            run_test = True
            run_security = True
            run_infrastructure = True
            is_docs_only = False
            requires_human_review = True

    return {
        "run_lint": str(run_lint).lower(),
        "run_test": str(run_test).lower(),
        "run_security": str(run_security).lower(),
        "run_infrastructure": str(run_infrastructure).lower(),
        "is_docs_only": str(is_docs_only).lower(),
        "requires_human_review": str(requires_human_review).lower(),
        "detected_labels": ",".join(sorted(detected_labels)) if detected_labels else "",
    }


def emit_outputs(outputs):
    """Write outputs to GITHUB_OUTPUT or print to stdout."""
    github_output = os.environ.get("GITHUB_OUTPUT")

    if github_output:
        with open(github_output, "a") as f:
            for key, value in outputs.items():
                f.write(f"{key}={value}\n")
    else:
        # Local execution — print to stdout
        print("=== Classifier Outputs ===")
        for key, value in outputs.items():
            print(f"  {key}={value}")


def main():
    changed_files = get_changed_files()
    print(f"Changed files detected: {len(changed_files)}")
    for f in changed_files[:20]:
        print(f"  {f}")
    if len(changed_files) > 20:
        print(f"  ... and {len(changed_files) - 20} more")

    outputs = classify(changed_files)
    emit_outputs(outputs)

    print("\nClassification complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
