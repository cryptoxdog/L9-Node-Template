# Repo Normalization Steps

Run on every new fork of `L9_REPO_TEMPLATE` before first commit.

## Quick run

```bash
uv run python scripts/repo_normalizer_v1.0.0.py
# or
make normalize
# or
just normalize
```

## What it checks and fixes

| Check | What it enforces | Action |
|-------|-----------------|--------|
| `required_dirs` | All standard directories exist | Creates missing dirs |
| `required_root_files` | All required root files present | Creates stubs |
| `required_scripts` | Tooling scripts present | Violation only (no auto-create) |
| `required_ci` | `.github/workflows/ci.yml` exists | Creates stub if missing |
| `src_package` | At least one `__init__.py` package under `src/` | Creates stub package |
| `plugin_config_keys` | `plugin-config.yaml` has all required keys | Violation only |

## Check-only mode (CI / pre-commit)

```bash
uv run python scripts/repo_normalizer_v1.0.0.py --check
```

Exits non-zero if any violation is found. Used in `post-checkout` pre-commit stage
and as Gate 5 in the CI ladder.

## Report

Every run writes `docs/repo_normalization_report.json` — a graphable record
with `schema: l9.repo_normalizer.report.v1`, suitable for emission to the L9 knowledge graph.
