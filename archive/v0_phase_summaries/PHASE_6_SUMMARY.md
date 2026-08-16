# Phase 6 Summary — Semantic Treehouse Local Deployment Evidence Track

## Files Created Or Modified

- `tools/semantic-treehouse/README.md`
- `C_Semantic_Treehouse/scripts/treehouse_clone_or_update.sh`
- `C_Semantic_Treehouse/scripts/treehouse_up.sh`
- `C_Semantic_Treehouse/scripts/treehouse_down.sh`
- `C_Semantic_Treehouse/scripts/treehouse_status.sh`
- `C_Semantic_Treehouse/scripts/treehouse_clone_or_update.ps1`
- `C_Semantic_Treehouse/scripts/treehouse_up.ps1`
- `C_Semantic_Treehouse/scripts/treehouse_down.ps1`
- `C_Semantic_Treehouse/scripts/treehouse_status.ps1`
- `Makefile`
- `make.cmd`
- `.gitignore`
- `C_Semantic_Treehouse/evidence/semantic-treehouse-local-deployment.md`
- `C_Semantic_Treehouse/evidence/semantic-treehouse-upstream-version.txt`
- `C_Semantic_Treehouse/evidence/treehouse-compose-candidates.txt`
- `C_Semantic_Treehouse/evidence/treehouse-compose-file.txt`
- `C_Semantic_Treehouse/evidence/treehouse-docker-compose.log`
- `C_Semantic_Treehouse/evidence/treehouse-docker-ps.txt`
- `C_Semantic_Treehouse/evidence/treehouse-smoke-check.txt`

## Commands Run

- `cmd /c make treehouse-clone` — passed; upstream commit captured as `33cf285c187f58c773f4e0d8c2826eeb2f6b3778`.
- `cmd /c make treehouse-up` — passed; selected upstream root `docker-compose.yml`, used `--profile dev`, created required volumes, copied `.env.example` to `.env` when needed, ran `composer install`, and ran Doctrine migrations.
- `cmd /c make treehouse-status` — passed; captured compose/container status in `evidence/treehouse-docker-ps.txt`.
- `cmd /c make validate` — passed; independent validation remains separate from the Semantic Treehouse deployment evidence track.

## Evidence Result

- Semantic Treehouse development UI smoke check: `http://localhost:4200/` returned `HTTP/1.1 200 OK`.
- Backend/root port smoke check: `http://localhost:8014/` is mapped by Compose but the root HEAD request timed out after 5 seconds.
- The Treehouse result is recorded as supporting evidence only. It is not part of `make validate` and does not block RDF, JSON-LD, SHACL, JSON Schema, OpenAPI, SPARQL, quality, or governance validation.

## Pass/Fail Status

- `treehouse-clone`: pass.
- `treehouse-up`: pass with partial smoke caveat on backend root path.
- `treehouse-status`: pass.
- `validate`: pass.

## Remaining Risks

- The local Treehouse instance was verified through a smoke check, not through a full UI workflow or screenshot capture.
- Backend root path behavior needs manual follow-up if the final report requires API-level Treehouse screenshots.
- The upstream repository is stored under `tools/semantic-treehouse/upstream` and intentionally ignored by git to avoid vendoring the external project.
