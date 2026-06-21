# Lifecycle — L9 Node Repo Template

## Template lifecycle

1. Author or update `nodespec.yaml` as the birth input contract.
2. Run `l9-codegen-engine` outside this repo template to generate concrete node-owned files.
3. Validate generated-only markers, contracts, Cursor rule drift, static audit, type checks, and tests.
4. Commit the generated node repo only after validation evidence is recorded.

## Ownership lifecycle

The repo template owns validation and structure throughout the lifecycle. `l9-codegen-engine` owns generated output creation. The harness library owns reusable agent/coding doctrine. Commit packs own provenance only.

## Stop conditions

- `enginehandlers.py` is manually edited.
- SDK transport imports appear outside `enginehandlers.py`.
- Handler generation logic appears inside the repo template.
- The codegen engine or harness library is copied into the template.
- Validation cannot distinguish pass, fail, skipped, and Unknown.
