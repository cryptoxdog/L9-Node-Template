# L9 Repo Folder Map

```
<repo-root>/
├── src/<package_name>/          # Application source (one package per repo)
│   ├── __init__.py
│   ├── main.py                  # FastAPI app factory
│   └── observability/           # OTel bootstrap, logging, metrics, tracing
├── tests/                       # pytest suite (unit + integration)
│   └── observability/           # OTel-specific tests with Fix-B fixtures
├── scripts/                     # Repo-scoped tooling (non-application)
│   ├── render_cursor_rules.py   # Parametric .mdc renderer
│   └── repo_normalizer_v1.0.0.py  # Layout contract enforcer
├── docs/                        # Architecture docs, manifests, reports
├── observability/               # Docker Compose + OTel Collector config
├── .cursor/rules/               # Cursor .mdc rules (rendered, not hand-authored)
│   └── templates/               # Canonical .mdc.template source
├── .devcontainer/               # Dev Container spec
├── .github/workflows/           # CI (5-gate ladder + normalize gate)
├── .vscode/                     # Editor settings, launch, extensions
├── pyproject.toml               # Single source: deps + tool config
├── uv.lock                      # Locked dep manifest
├── plugin-config.yaml           # Domain cartridge values
├── Makefile                     # GNU Make targets (.PHONY declared)
├── Justfile                     # Just recipes (no .PHONY needed)
├── AGENTS.md                    # Agent contract
└── .pre-commit-config.yaml      # Pre-commit hooks (pre-commit + post-checkout)
```
