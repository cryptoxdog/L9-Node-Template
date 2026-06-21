"""Tests for scripts/repo_normalizer_v1.0.0.py"""

import importlib.util as _ilu
import json
import sys as _sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "repo_normalizer_v1.0.0.py"
_spec = _ilu.spec_from_file_location("repo_normalizer_v1_0_0", _SCRIPT)
norm = _ilu.module_from_spec(_spec)
_sys.modules["repo_normalizer_v1_0_0"] = norm
_spec.loader.exec_module(norm)  # type: ignore[union-attr]


PLUGIN_CFG = (
    "plugin_version: '1.0.0'\n"
    "repo_name: test\n"
    "domain: test\n"
    "package_name: my_service\n"
    "python_version: '3.12'\n"
)


def minimal_repo(tmp_path: Path) -> Path:
    for d in [
        "src/my_service",
        "tests",
        "scripts",
        "docs",
        "observability",
        ".cursor/rules/templates",
        ".devcontainer",
        ".github/workflows",
        ".vscode",
    ]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    (tmp_path / "src/my_service/__init__.py").write_text("")
    for f in norm.REQUIRED_ROOT_FILES:
        (tmp_path / f).write_text("# stub\n")
    (tmp_path / "plugin-config.yaml").write_text(PLUGIN_CFG)
    for s in norm.REQUIRED_SCRIPTS:
        (tmp_path / s).write_text("# stub\n")
    for c in norm.REQUIRED_CI:
        (tmp_path / c).write_text("# stub\n")
    return tmp_path


def test_required_dirs_ok(tmp_path: Path) -> None:
    assert all(r.status == "ok" for r in norm.check_required_dirs(minimal_repo(tmp_path), True))


def test_required_dirs_missing_check_only(tmp_path: Path) -> None:
    results = norm.check_required_dirs(tmp_path, True)
    assert len([r for r in results if r.is_violation()]) == len(norm.REQUIRED_DIRS)


def test_required_dirs_missing_fix(tmp_path: Path) -> None:
    results = norm.check_required_dirs(tmp_path, False)
    assert len([r for r in results if r.is_fixed()]) == len(norm.REQUIRED_DIRS)
    for d in norm.REQUIRED_DIRS:
        assert (tmp_path / d).exists()


def test_required_root_files_ok(tmp_path: Path) -> None:
    assert all(
        r.status == "ok" for r in norm.check_required_root_files(minimal_repo(tmp_path), True)
    )


def test_required_root_files_fix(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    results = norm.check_required_root_files(tmp_path, False)
    assert len([r for r in results if r.is_fixed()]) == len(norm.REQUIRED_ROOT_FILES)


def test_required_root_files_check_violation(tmp_path: Path) -> None:
    assert all(r.is_violation() for r in norm.check_required_root_files(tmp_path, True))


def test_required_scripts_ok(tmp_path: Path) -> None:
    assert all(r.status == "ok" for r in norm.check_required_scripts(minimal_repo(tmp_path), True))


def test_required_scripts_missing(tmp_path: Path) -> None:
    assert all(r.is_violation() for r in norm.check_required_scripts(tmp_path, True))


def test_src_package_ok(tmp_path: Path) -> None:
    assert norm.check_src_package(minimal_repo(tmp_path), True)[0].status == "ok"


def test_src_package_missing_src(tmp_path: Path) -> None:
    assert norm.check_src_package(tmp_path, True)[0].is_violation()


def test_src_package_no_init(tmp_path: Path) -> None:
    (tmp_path / "src/mypkg").mkdir(parents=True)
    assert norm.check_src_package(tmp_path, True)[0].is_violation()


def test_src_package_fix_creates_stub(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    results = norm.check_src_package(tmp_path, False)
    assert results[0].is_fixed()
    assert (tmp_path / "src/my_service/__init__.py").exists()


def test_plugin_config_ok(tmp_path: Path) -> None:
    assert norm.check_plugin_config_keys(minimal_repo(tmp_path), True)[0].status == "ok"


def test_plugin_config_missing_file(tmp_path: Path) -> None:
    assert norm.check_plugin_config_keys(tmp_path, True)[0].is_violation()


def test_plugin_config_missing_keys(tmp_path: Path) -> None:
    (tmp_path / "plugin-config.yaml").write_text("plugin_version: '1.0.0'\n")
    r = norm.check_plugin_config_keys(tmp_path, True)[0]
    assert r.is_violation() and "missing keys" in r.detail


def test_plugin_config_bad_yaml(tmp_path: Path) -> None:
    (tmp_path / "plugin-config.yaml").write_text(": bad: [\n")
    assert norm.check_plugin_config_keys(tmp_path, True)[0].is_violation()


def test_report_summary() -> None:
    r = norm.NormalizationReport(violations=2, fixed=1, ok=5)
    s = r.summary()
    assert "ok=5" in s and "fixed=1" in s and "violations=2" in s


def test_report_to_dict() -> None:
    d = norm.NormalizationReport(violations=0, fixed=0, ok=3).to_dict()
    assert d["schema"] == "l9.repo_normalizer.report.v1"


def test_run_checks_clean_repo(tmp_path: Path) -> None:
    assert norm.run_checks(minimal_repo(tmp_path), check_only=True).violations == 0


def test_run_checks_empty_repo_check_only(tmp_path: Path) -> None:
    assert norm.run_checks(tmp_path, check_only=True).violations > 0


def test_run_checks_idempotent(tmp_path: Path) -> None:
    norm.run_checks(tmp_path, check_only=False)
    assert norm.run_checks(tmp_path, check_only=False).fixed == 0


def test_write_report(tmp_path: Path) -> None:
    repo = minimal_repo(tmp_path)
    path = norm.write_report(norm.run_checks(repo, check_only=True), repo)
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["schema"] == "l9.repo_normalizer.report.v1"


def test_main_check_clean_repo(tmp_path: Path) -> None:
    assert norm.main(["--check", "--root", str(minimal_repo(tmp_path))]) == 0


def test_main_check_empty_repo(tmp_path: Path) -> None:
    assert norm.main(["--check", "--root", str(tmp_path)]) == 1


def test_main_fix_empty_repo(tmp_path: Path) -> None:
    assert norm.main(["--root", str(tmp_path)]) == 0


def test_main_report_flag(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    rc = norm.main(["--report", "--root", str(minimal_repo(tmp_path))])
    out = capsys.readouterr().out
    assert rc == 0 and "results" in json.loads(out)


def test_main_no_args_uses_cwd(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(minimal_repo(tmp_path))
    assert norm.main([]) == 0
