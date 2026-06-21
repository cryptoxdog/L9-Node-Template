# Nodespec Boundary

`nodespec.yaml` is the birth input contract. The template may reference it and carry a reference example. The template must not own nodespec parsing, handler generation, manifest generation, or codegen determinism. Those responsibilities belong to `l9-codegen-engine`.

Boundary: spec in, generated repo out.
