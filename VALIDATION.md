# Validation

## Executed local gates

| Gate | Status | Evidence |
|---|---|---|
| rendered_cursor_rules_match_templates | PASS | OK: 4 rendered Cursor rules are current |
| contracts_exist | PASS | All contract verifications passed ✅ |
| generated_boundary_validation | PASS | Generated boundary validation passed |
| audit_engine_high_findings | PASS | Summary: 0 findings after L9_META alignment |
| template_compliance | PASS | Template compliance: PASSED ✅ |
| python_compile_core_files | PASS | py_compile completed with exit 0 |
| pyproject_toml_parse | PASS | pyproject TOML parse passed |
| placeholder_scan_core_files | PASS | no placeholder tokens found in contracts/domain/enginehandlers/docs/core manifests |

## Skipped or Unknown gates

| Gate | Status | Reason |
|---|---|---|
| pytest | UNKNOWN | Local environment lacks installed project dependencies: E   ModuleNotFoundError: No module named 'opentelemetry.instrumentation' |
| ruff_format | UNKNOWN | ruff executable unavailable in sandbox |
| ruff_check | UNKNOWN | ruff executable unavailable in sandbox |
| pyright | UNKNOWN | pyright executable unavailable in sandbox |
| remote_ci | UNKNOWN | Not run in GitHub Actions from this sandbox |

## Validation rule

No unavailable tool is claimed as pass. Missing local executables and missing dependency installs are recorded as Unknown rather than faked.
