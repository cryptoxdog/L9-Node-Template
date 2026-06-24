# =============================================================================
# L9 Service — Justfile
# L9_META role: task_runner version: 1.1.0 /L9_META
#
# Just never confuses recipes with files — no .PHONY equivalent needed.
# Run: just        → list all recipes
#      just <name> → run recipe
# =============================================================================

# Default: list all recipes
default:
    @just --list

# ── Environment ───────────────────────────────────────────────────────────────

# Install locked deps and pre-commit hooks
setup:
    uv sync --locked
    uv run pre-commit install --hook-type pre-commit --hook-type post-checkout

# Sync deps from uv.lock without upgrading
sync:
    uv sync --locked

# Regenerate uv.lock from pyproject.toml
lock:
    uv lock

# Upgrade all deps and regenerate uv.lock
upgrade:
    uv lock --upgrade

# ── Code Quality ──────────────────────────────────────────────────────────────

# Auto-format source (modifies files — confirm before running)
format:
    uv run ruff format src/ tests/
    uv run ruff check --fix src/ tests/

# Check formatting — read-only, CI-safe
format-check:
    uv run ruff format --check src/ tests/

# Lint without auto-fix — read-only, CI-safe
lint-check:
    uv run ruff check src/ tests/

# Pyright type check — 0 errors required
type:
    uv run pyright src/

# ── Tests ──────────────────────────────────────────────────────────────────────

# Run all tests
test:
    uv run pytest tests/ -v --tb=short

# Tests with coverage — fails below 70%
test-cov:
    uv run pytest tests/ -v --tb=short \
        --cov=src \
        --cov-report=term-missing \
        --cov-report=html:htmlcov \
        --cov-fail-under=70

# ── Full CI Ladder ─────────────────────────────────────────────────────────────

# Full local CI ladder — format-check → lint → type → test-cov
ci: format-check lint-check type test-cov

# ── Observability Stack ────────────────────────────────────────────────────────

# Start: Grafana :3000  Prometheus :9090  Tempo :3200  OTel Collector :4317
obs-up:
    docker compose -f observability/docker-compose.observability.yml up -d --wait

# Stop observability stack
obs-down:
    docker compose -f observability/docker-compose.observability.yml down

# Show observability stack container status
obs-ps:
    docker compose -f observability/docker-compose.observability.yml ps

# ── Cleanup ────────────────────────────────────────────────────────────────────

# Remove caches, build artifacts, coverage reports
clean:
    find . -type d -name __pycache__ -exec rm -rf {} + || true
    find . -type d -name htmlcov -exec rm -rf {} + || true
    find . -name "*.pyc" -delete || true
    rm -f .coverage

# Full reset — removes .venv
dev-clean: clean
    rm -rf .venv
# Render .cursor/rules/*.mdc from templates + plugin-config.yaml
render-rules:
    uv run python scripts/render_cursor_rules.py --force

# Verify rendered Cursor rules are current; fails on drift
check-rules:
    uv run python scripts/render_cursor_rules.py --check --diff

# Drift gate for rendered rules (future: ADR/graph drift too)
drift-check: check-rules

# Recommended CI expansion:
# ci: format-check lint-check type check-rules test-cov
