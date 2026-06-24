# =============================================================================
# L9 Service — Makefile
# L9_META role: task_runner version: 1.1.0 /L9_META
#
# .PHONY: declares every target that does NOT produce a file with the same name.
# Without this, if a file named e.g. "test" exists on disk, Make silently skips
# the target. Every non-file-producing target MUST appear in .PHONY.
# =============================================================================

.PHONY: help \
        setup sync lock upgrade \
        format lint-check format-check type \
        test test-cov \
        ci \
        obs-up obs-down obs-ps \
        clean dev-clean

# Default target — show help when `make` is run with no arguments
.DEFAULT_GOAL := help

help: ## Show all targets with descriptions
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Environment ───────────────────────────────────────────────────────────────
setup: ## Install locked deps + pre-commit hooks
	uv sync --locked
	uv run pre-commit install --hook-type pre-commit --hook-type post-checkout

sync: ## Sync deps from uv.lock without upgrading
	uv sync --locked

lock: ## Regenerate uv.lock from pyproject.toml
	uv lock

upgrade: ## Upgrade all deps and regenerate uv.lock
	uv lock --upgrade

# ── Code Quality ──────────────────────────────────────────────────────────────
format: ## Auto-format source (modifies files — confirm before running)
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

format-check: ## Check formatting — read-only, CI-safe
	uv run ruff format --check src/ tests/

lint-check: ## Lint without auto-fix — read-only, CI-safe
	uv run ruff check src/ tests/

type: ## Pyright type check — 0 errors required
	uv run pyright src/

# ── Tests ──────────────────────────────────────────────────────────────────────
test: ## Run all tests
	uv run pytest tests/ -v --tb=short

test-cov: ## Tests with coverage — fails below 70%
	uv run pytest tests/ -v --tb=short \
		--cov=src \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		--cov-fail-under=70

# ── Full CI Ladder ─────────────────────────────────────────────────────────────
ci: format-check lint-check type test-cov ## Full local CI ladder (matches GitHub Actions exactly)

# ── Observability Stack ────────────────────────────────────────────────────────
obs-up: ## Start observability stack: Grafana :3000  Prometheus :9090  Tempo :3200
	docker compose -f observability/docker-compose.observability.yml up -d --wait

obs-down: ## Stop observability stack
	docker compose -f observability/docker-compose.observability.yml down

obs-ps: ## Show observability stack container status
	docker compose -f observability/docker-compose.observability.yml ps

# ── Cleanup ────────────────────────────────────────────────────────────────────
clean: ## Remove caches, build artifacts, and coverage reports
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -f .coverage

dev-clean: clean ## Full reset — removes .venv (run: make setup after)
	rm -rf .venv
	@echo "Environment removed. Run: make setup"
.PHONY: render-rules check-rules drift-check

render-rules: ## Render .cursor/rules/*.mdc from .mdc.template + plugin-config.yaml
	uv run python scripts/render_cursor_rules.py --force

check-rules: ## Verify rendered Cursor rules are current; fails on drift
	uv run python scripts/render_cursor_rules.py --check --diff

drift-check: check-rules ## Drift gate for rendered rules (future: ADR/graph drift too)

# Recommended CI expansion:
# ci: format-check lint-check type check-rules test-cov
