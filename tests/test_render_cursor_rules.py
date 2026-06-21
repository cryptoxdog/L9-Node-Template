"""Tests for scripts/render_cursor_rules.py — idempotency and drift detection."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def copy_pack(tmp_path: Path, repo_root: Path) -> None:
    for rel in [
        "scripts/render_cursor_rules.py",
        "plugin-config.yaml",
        ".cursor/rules/templates/00-global.mdc.template",
        ".cursor/rules/templates/fastapi.mdc.template",
        ".cursor/rules/templates/l9-agents.mdc.template",
        ".cursor/rules/templates/10-domain-cartridge.mdc.template",
    ]:
        src = repo_root / rel
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def test_render_and_check_are_idempotent(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    copy_pack(tmp_path, repo_root)
    render = tmp_path / "scripts/render_cursor_rules.py"
    first = subprocess.run(
        [sys.executable, str(render), "--force"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert first.returncode == 0, first.stderr
    assert (tmp_path / ".cursor/rules/00-global.mdc").exists()
    assert "L9_RENDERED" in (tmp_path / ".cursor/rules/00-global.mdc").read_text(encoding="utf-8")
    check = subprocess.run(
        [sys.executable, str(render), "--check", "--diff"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert check.returncode == 0, check.stderr


def test_check_detects_drift(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    copy_pack(tmp_path, repo_root)
    render = tmp_path / "scripts/render_cursor_rules.py"
    subprocess.run([sys.executable, str(render), "--force"], cwd=tmp_path, check=True)
    target = tmp_path / ".cursor/rules/fastapi.mdc"
    target.write_text(target.read_text(encoding="utf-8") + "\nmanual drift\n", encoding="utf-8")
    check = subprocess.run(
        [sys.executable, str(render), "--check"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert check.returncode == 1
    assert "DRIFT" in check.stderr
