# Phase 6 Prompt — Semantic Treehouse Local Deployment Evidence Track

Implement Phase 6 only.

Objective:
Create a non-blocking local Docker-based Semantic Treehouse deployment evidence track. The purpose is to try local deployment, capture logs, and document UI/API availability. This must not break independent validation.

Important:
Do not make this phase a hard dependency for make validate. If deployment fails, capture the failure and produce an honest report.

Tasks:

1. Create tools/semantic-treehouse/README.md explaining:

   * local deployment objective
   * Docker prerequisite
   * expected ports
   * how this evidence relates to the C Group task
   * known risks
   * fallback: independent validation harness

2. Create scripts/treehouse_clone_or_update.sh:

   * clone [https://gitlab.com/semantic-treehouse/semantic-treehouse.git](https://gitlab.com/semantic-treehouse/semantic-treehouse.git) into tools/semantic-treehouse/upstream if not present
   * if present, fetch updates but do not overwrite local modifications
   * capture git commit hash into evidence/semantic-treehouse-upstream-version.txt

3. Create scripts/treehouse_up.sh:

   * inspect upstream README and docker compose files
   * attempt Docker Compose dev deployment using upstream-supported commands
   * write logs to evidence/treehouse-docker-compose.log
   * write container status to evidence/treehouse-docker-ps.txt
   * never delete unrelated containers or volumes
   * on failure, exit non-zero but leave evidence files

4. Create scripts/treehouse_down.sh:

   * stop only the Semantic Treehouse compose project if it was started by this harness

5. Update Makefile:

   * make treehouse-clone
   * make treehouse-up
   * make treehouse-down
   * make treehouse-status

6. Create evidence/semantic-treehouse-local-deployment.md with sections:

   * environment
   * Docker version
   * upstream commit
   * commands run
   * result
   * UI/API URLs checked
   * screenshots to capture manually
   * errors and interpretation
   * impact on C Group deliverables
   * fallback validation path

7. If possible, add a minimal smoke check:

   * curl localhost port if documented by upstream
   * write result to evidence/treehouse-smoke-check.txt

8. Do not assume the exact upstream service names. The script should inspect docker compose files and be defensive.

Acceptance criteria:

* make treehouse-clone works.
* make treehouse-up attempts deployment and records evidence.
* Failure is acceptable only if logs and interpretation are generated.
* make validate remains independent and still passes.

Commands to run:

* make treehouse-clone
* make treehouse-up
* make treehouse-status
* make validate

Stop after Phase 6.

