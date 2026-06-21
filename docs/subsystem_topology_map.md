# L9 Subsystem Topology

```
┌─────────────────────────────────────────────────────────┐
│  BODY layer (devcontainer)                              │
│  Runtime: Python 3.12 · uv · Docker-in-Docker          │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  APPLICATION (src/<package>/)                    │  │
│  │  FastAPI app  ◄──►  OTel bootstrap               │  │
│  │  routes/      ◄──►  tracing / metrics / logging  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  QUALITY gates (CI ladder, pre-commit)           │  │
│  │  ruff format → ruff lint → pyright               │  │
│  │  → cursor-rule-drift → normalize-check           │  │
│  │  → pytest 80% cov                                │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  TOOLING (scripts/)                              │  │
│  │  render_cursor_rules.py  → .cursor/rules/*.mdc   │  │
│  │  repo_normalizer_v1.0.0.py → layout contract     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  MIND layer (Cursor plugin)                             │
│  .cursor/rules/*.mdc  — rendered from templates        │
│  plugin-config.yaml   — domain cartridge values        │
└─────────────────────────────────────────────────────────┘
```
