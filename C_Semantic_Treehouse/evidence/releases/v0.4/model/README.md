# Phase 04 model release evidence

This directory contains audited, deterministic v0.4 model and release-manifest evidence. Machine-local environment inventories, the Docker image audit, and raw execution material remain under `build/phase-04/`.

- source commit: `6f993661e7c4d8be6a5d92b933bc366682a13372`
- source dirty at evidence build: `true`
- Docker image ID: `sha256:4e19f9cf2962abc51e4c15d345f4244eb8e5f949d52b9a2d1f515d2a3b955fcf`
- fixed base image digest: `sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db`
- host/container normalized semantic SHA-256: `e25c0511a66f20cda0cc8471c6cc1f53c9fa4597ae141d17254b88ec029a0aaa`
- host/container model checks: `11/11` in each profile
- host/container contract smoke cases: `6/6` in each profile
- Phase 04 negative controls: `38/38`
- release manifest SHA-256: `7d75676b898fdbc00c9b1da78900054aec5f426690822e07970200b5fd88076a`
- release manifest schema SHA-256: `9029520a45dfc9933cbd254d9cbf4c65e7669ecbd0b20cf916c793a09ac695d3`
- requirements registry SHA-256: `53953e915d6da6159b342a04f1dc6d0ff6a8f53bd5892eb7933551710ebe014e`
- validation-suite contract/hash: `1.3.0` / `1ae6361e956c2bf41f86e987caf0879ce4483f76f9f1e042b0442edb3f049829`

The two result JSON files are the normative host and container records. Their Markdown files are deterministic renderings. The comparison proves normalized semantic equality; `negative-controls.json` records fail-closed mutation coverage; `git-attribute-audit.json` records the D Shape byte-copy and exact `-text` rule.
