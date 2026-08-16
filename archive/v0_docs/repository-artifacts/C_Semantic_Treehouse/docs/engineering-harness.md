# Engineering Harness

The package uses local and Docker-based validation so the core semantic artifacts can be checked reproducibly without relying on a hosted Semantic Treehouse instance.

Semantic Treehouse remains important evidence for the C Group task, but it is not a blocker for model validation. If a local Semantic Treehouse deployment fails, the failure should be captured in `evidence/` and the independent local validation path must still run.

CI will later run the same validation commands used locally. This keeps grading and demo evidence aligned with day-to-day development checks.

Phase 0 defines the harness shape only. Concrete validation scripts are added in later phases.
