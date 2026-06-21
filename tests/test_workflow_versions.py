"""Unit tests for GitHub Actions workflow version bumps (actions/checkout@v7).

Covers the PR that bumped actions/checkout from v4 to v7 in:
  - .github/workflows/ci.yml
  - .github/workflows/dependency-review.yml
  - .github/workflows/gitleaks.yml
  - .github/workflows/pr-pipeline.yml
"""

from __future__ import annotations

import pathlib
import re

import pytest
import yaml

WORKFLOWS_DIR = pathlib.Path(__file__).resolve().parents[1] / ".github" / "workflows"

CI_YML = WORKFLOWS_DIR / "ci.yml"
DEPENDENCY_REVIEW_YML = WORKFLOWS_DIR / "dependency-review.yml"
GITLEAKS_YML = WORKFLOWS_DIR / "gitleaks.yml"
PR_PIPELINE_YML = WORKFLOWS_DIR / "pr-pipeline.yml"

CHECKOUT_V7 = "actions/checkout@v7"
CHECKOUT_V4 = "actions/checkout@v4"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_yaml(path: pathlib.Path) -> dict:
    """Parse a workflow YAML file and return its contents as a dict."""
    return yaml.safe_load(path.read_text())  # type: ignore[return-value]


def _all_step_uses(workflow: dict) -> list[str]:
    """Collect every `uses:` value from all steps across all jobs."""
    uses_values: list[str] = []
    for job in workflow.get("jobs", {}).values():
        for step in job.get("steps", []):
            if "uses" in step:
                uses_values.append(step["uses"])
    return uses_values


def _checkout_uses_values(workflow: dict) -> list[str]:
    """Return only the checkout `uses:` values from all steps."""
    return [u for u in _all_step_uses(workflow) if u.startswith("actions/checkout")]


# ---------------------------------------------------------------------------
# YAML validity
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ci_yml_is_valid_yaml() -> None:
    """ci.yml parses without error."""
    data = _load_yaml(CI_YML)
    assert isinstance(data, dict)


@pytest.mark.unit
def test_dependency_review_yml_is_valid_yaml() -> None:
    """dependency-review.yml parses without error."""
    data = _load_yaml(DEPENDENCY_REVIEW_YML)
    assert isinstance(data, dict)


@pytest.mark.unit
def test_gitleaks_yml_is_valid_yaml() -> None:
    """gitleaks.yml parses without error."""
    data = _load_yaml(GITLEAKS_YML)
    assert isinstance(data, dict)


@pytest.mark.unit
def test_pr_pipeline_yml_is_valid_yaml() -> None:
    """pr-pipeline.yml parses without error."""
    data = _load_yaml(PR_PIPELINE_YML)
    assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# actions/checkout version is v7 (the changed line)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ci_yml_uses_checkout_v7() -> None:
    """ci.yml checkout step uses actions/checkout@v7."""
    workflow = _load_yaml(CI_YML)
    checkout_uses = _checkout_uses_values(workflow)
    assert checkout_uses, "No checkout step found in ci.yml"
    assert all(u == CHECKOUT_V7 for u in checkout_uses), (
        f"Expected all checkout steps to use {CHECKOUT_V7}, got {checkout_uses}"
    )


@pytest.mark.unit
def test_dependency_review_yml_uses_checkout_v7() -> None:
    """dependency-review.yml checkout step uses actions/checkout@v7."""
    workflow = _load_yaml(DEPENDENCY_REVIEW_YML)
    checkout_uses = _checkout_uses_values(workflow)
    assert checkout_uses, "No checkout step found in dependency-review.yml"
    assert all(u == CHECKOUT_V7 for u in checkout_uses), (
        f"Expected all checkout steps to use {CHECKOUT_V7}, got {checkout_uses}"
    )


@pytest.mark.unit
def test_gitleaks_yml_uses_checkout_v7() -> None:
    """gitleaks.yml checkout step uses actions/checkout@v7."""
    workflow = _load_yaml(GITLEAKS_YML)
    checkout_uses = _checkout_uses_values(workflow)
    assert checkout_uses, "No checkout step found in gitleaks.yml"
    assert all(u == CHECKOUT_V7 for u in checkout_uses), (
        f"Expected all checkout steps to use {CHECKOUT_V7}, got {checkout_uses}"
    )


@pytest.mark.unit
def test_pr_pipeline_yml_uses_checkout_v7_in_all_jobs() -> None:
    """Every checkout step in pr-pipeline.yml uses actions/checkout@v7 (4 jobs)."""
    workflow = _load_yaml(PR_PIPELINE_YML)
    checkout_uses = _checkout_uses_values(workflow)
    assert len(checkout_uses) == 4, (
        f"Expected 4 checkout steps in pr-pipeline.yml, found {len(checkout_uses)}"
    )
    assert all(u == CHECKOUT_V7 for u in checkout_uses), (
        f"Expected all checkout steps to use {CHECKOUT_V7}, got {checkout_uses}"
    )


@pytest.mark.unit
def test_pr_pipeline_classify_job_uses_checkout_v7() -> None:
    """The classify job in pr-pipeline.yml uses actions/checkout@v7."""
    workflow = _load_yaml(PR_PIPELINE_YML)
    classify_steps = workflow["jobs"]["classify"]["steps"]
    checkout_steps = [s for s in classify_steps if s.get("uses", "").startswith("actions/checkout")]
    assert checkout_steps, "No checkout step in classify job"
    assert checkout_steps[0]["uses"] == CHECKOUT_V7


@pytest.mark.unit
def test_pr_pipeline_lint_job_uses_checkout_v7() -> None:
    """The lint job in pr-pipeline.yml uses actions/checkout@v7."""
    workflow = _load_yaml(PR_PIPELINE_YML)
    lint_steps = workflow["jobs"]["lint"]["steps"]
    checkout_steps = [s for s in lint_steps if s.get("uses", "").startswith("actions/checkout")]
    assert checkout_steps, "No checkout step in lint job"
    assert checkout_steps[0]["uses"] == CHECKOUT_V7


@pytest.mark.unit
def test_pr_pipeline_test_job_uses_checkout_v7() -> None:
    """The test job in pr-pipeline.yml uses actions/checkout@v7."""
    workflow = _load_yaml(PR_PIPELINE_YML)
    test_steps = workflow["jobs"]["test"]["steps"]
    checkout_steps = [s for s in test_steps if s.get("uses", "").startswith("actions/checkout")]
    assert checkout_steps, "No checkout step in test job"
    assert checkout_steps[0]["uses"] == CHECKOUT_V7


@pytest.mark.unit
def test_pr_pipeline_security_job_uses_checkout_v7() -> None:
    """The security job in pr-pipeline.yml uses actions/checkout@v7."""
    workflow = _load_yaml(PR_PIPELINE_YML)
    security_steps = workflow["jobs"]["security"]["steps"]
    checkout_steps = [s for s in security_steps if s.get("uses", "").startswith("actions/checkout")]
    assert checkout_steps, "No checkout step in security job"
    assert checkout_steps[0]["uses"] == CHECKOUT_V7


# ---------------------------------------------------------------------------
# Regression: no stale v4 references remain
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_no_checkout_v4_in_ci_yml() -> None:
    """ci.yml must not reference the old actions/checkout@v4."""
    assert CHECKOUT_V4 not in CI_YML.read_text(), (
        "Found stale actions/checkout@v4 reference in ci.yml"
    )


@pytest.mark.unit
def test_no_checkout_v4_in_dependency_review_yml() -> None:
    """dependency-review.yml must not reference actions/checkout@v4."""
    assert CHECKOUT_V4 not in DEPENDENCY_REVIEW_YML.read_text(), (
        "Found stale actions/checkout@v4 reference in dependency-review.yml"
    )


@pytest.mark.unit
def test_no_checkout_v4_in_gitleaks_yml() -> None:
    """gitleaks.yml must not reference actions/checkout@v4."""
    assert CHECKOUT_V4 not in GITLEAKS_YML.read_text(), (
        "Found stale actions/checkout@v4 reference in gitleaks.yml"
    )


@pytest.mark.unit
def test_no_checkout_v4_in_pr_pipeline_yml() -> None:
    """pr-pipeline.yml must not reference actions/checkout@v4 anywhere."""
    assert CHECKOUT_V4 not in PR_PIPELINE_YML.read_text(), (
        "Found stale actions/checkout@v4 reference in pr-pipeline.yml"
    )


# ---------------------------------------------------------------------------
# Structural integrity of the changed workflows
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_gitleaks_checkout_has_fetch_depth_zero() -> None:
    """gitleaks.yml checkout step retains fetch-depth: 0 (full history for secret scanning)."""
    workflow = _load_yaml(GITLEAKS_YML)
    scan_steps = workflow["jobs"]["scan"]["steps"]
    checkout_step = next(
        (s for s in scan_steps if s.get("uses", "").startswith("actions/checkout")), None
    )
    assert checkout_step is not None, "No checkout step in gitleaks scan job"
    assert checkout_step.get("with", {}).get("fetch-depth") == 0


@pytest.mark.unit
def test_pr_pipeline_classify_checkout_has_fetch_depth_zero() -> None:
    """pr-pipeline.yml classify job checkout retains fetch-depth: 0."""
    workflow = _load_yaml(PR_PIPELINE_YML)
    classify_steps = workflow["jobs"]["classify"]["steps"]
    checkout_step = next(
        (s for s in classify_steps if s.get("uses", "").startswith("actions/checkout")), None
    )
    assert checkout_step is not None, "No checkout step in pr-pipeline classify job"
    assert checkout_step.get("with", {}).get("fetch-depth") == 0


@pytest.mark.unit
def test_ci_yml_has_required_jobs() -> None:
    """ci.yml still defines the expected ci job after the version bump."""
    workflow = _load_yaml(CI_YML)
    assert "ci" in workflow["jobs"]


@pytest.mark.unit
def test_pr_pipeline_yml_has_required_jobs() -> None:
    """pr-pipeline.yml still defines classify, lint, test, security, gate jobs."""
    workflow = _load_yaml(PR_PIPELINE_YML)
    required_jobs = {"classify", "lint", "test", "security", "gate"}
    assert required_jobs.issubset(workflow["jobs"].keys())


@pytest.mark.unit
def test_dependency_review_yml_has_required_jobs() -> None:
    """dependency-review.yml still defines the review job."""
    workflow = _load_yaml(DEPENDENCY_REVIEW_YML)
    assert "review" in workflow["jobs"]


@pytest.mark.unit
def test_gitleaks_yml_has_required_jobs() -> None:
    """gitleaks.yml still defines the scan job."""
    workflow = _load_yaml(GITLEAKS_YML)
    assert "scan" in workflow["jobs"]


# ---------------------------------------------------------------------------
# Boundary / negative: checkout version is exactly v7 (not a partial match)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_checkout_version_is_exactly_v7_not_partial() -> None:
    """Ensure checkout version is exactly @v7, not @v70 or @v7x."""
    for path in (CI_YML, DEPENDENCY_REVIEW_YML, GITLEAKS_YML, PR_PIPELINE_YML):
        text = path.read_text()
        # Find all checkout action references
        matches = re.findall(r"actions/checkout@(\S+)", text)
        for version in matches:
            assert version == "v7", (
                f"Unexpected checkout version '{version}' in {path.name}; expected 'v7'"
            )
