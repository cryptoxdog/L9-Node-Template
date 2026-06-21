<!-- L9_META
skill_schema: 1
role: project_readme
tags: [l9, template, quickstart]
owner: igor_beylin
status: active
version: 1.1.0
updated: 2026-06-07
/L9_META -->

# L9 Service Template

Frontier-grade Python microservice template with FastAPI, structured OTel observability (traces + metrics + logs), and a fully validated toolchain.

**Stack:** Python 3.12 · uv · FastAPI · Structlog · OpenTelemetry SDK 1.28+ · Pyright (basic) · Ruff · pytest · pre-commit · GitHub Actions CI

## Quickstart

```bash
# Prerequisites: uv installed
# curl -LsSf https://astral.sh/uv/install.sh | sh

git clone <repo> my-service && cd my-service
uv sync --locked
uv run pre-commit install
make ci              # format-check → lint → type → test-cov — ALL MUST PASS
```

## Dev Container

Open in VS Code or Cursor → **Reopen in Container**.
Python 3.12, uv, all deps, and pre-commit hooks install automatically on container start.

## Observability Stack

```bash
make obs-up     # Start: Grafana :3000  Prometheus :9090  Tempo :3200  OTelCol :4317
make obs-down   # Stop stack
make obs-ps     # Status
```

Grafana auto-provisions Prometheus and Tempo datasources. No manual setup required.

## Task Runner

```bash
make help       # list all Makefile targets
just            # list all Just recipes
make ci         # full validation ladder (same as CI)
make test-cov   # tests with coverage report
```

## Repository Structure

```
.
├── src/l9_service/
│   ├── main.py                        # FastAPI app factory + healthz/readyz
│   ├── observability/
│   │   ├── bootstrap.py               # OTel init — idempotent, Fix-B safe
│   │   ├── tracing.py                 # span(), @instrument, get_trace_context
│   │   ├── metrics.py                 # Metrics class — counter/timer/histogram
│   │   └── logging.py                 # Structlog + OTel trace context injection
├── tests/
│   ├── conftest.py                    # Root autouse: clears Fix-B overrides between tests
│   └── observability/
│       ├── conftest.py                # Fix-B fixtures: span_exporter, metric_reader
│       ├── test_tracing.py            # 10 tracing tests
│       ├── test_metrics.py            # 7 metrics tests
│       └── test_logging.py            # 7 logging tests (incl. 2 Fix-B isolation tests)
├── observability/                     # Docker Compose obs stack
├── .cursor/rules/                     # Cursor agent rules (.mdc)
├── .vscode/                           # Editor settings + launch configs
├── .devcontainer/                     # Dev Container (Python 3.12 + uv)
├── .github/workflows/ci.yml           # GitHub Actions CI
├── AGENTS.md                          # Agent contract — read first
├── Makefile                           # GNU Make (full .PHONY)
├── Justfile                           # Just recipes
└── pyproject.toml                     # Single source of truth for all tooling
```

## L9 Node Contract

This template ships an L9 node contract surface. Three pinned artifacts govern the node:

- `contracts/NODECONTRACT.yaml` — node birth contract (capabilities, lifecycle, gates).
- `nodespec.yaml` — node identity, version, and declared interfaces (read by `tools/verify_contracts.py`).
- `contracts/ENGINESPEC.yaml` — engine surface this node implements (bridged via `src/l9_service/enginehandlers.py`).

Governance docs: `docs/ARCHITECTURE.md`, `docs/GOVERNANCE.md`, `docs/LIFECYCLE.md`, `docs/NODESPEC_BOUNDARY.md`. Enforcement: `tools/verify_contracts.py`, `tools/audit_engine.py`, `.github/workflows/{contract-verify,audit,codegen-determinism}.yml`.

## OTel Fix-B Pattern

OTel SDK 1.28+ uses a `do_once` sentinel that prevents repeated `set_tracer_provider()` calls in one process. Fix-B bypasses this in tests by injecting providers into module-level override slots (`_provider_override`, `Metrics._test_provider`) that are cleared by an autouse root fixture. **Never reference these slots in production code.**

## Rename Checklist

1. `grep -r "l9_service" src/ tests/ pyproject.toml` → replace with your package name
2. Update `OTEL_SERVICE_NAME` in `.env.example`
3. Update `packages` in `[tool.hatch.build.targets.wheel]` in `pyproject.toml`
4. `uv lock` → `make ci` — all gates MUST pass before first commit
