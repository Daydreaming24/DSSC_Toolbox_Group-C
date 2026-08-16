@echo off
setlocal

set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=help"

if "%TARGET%"=="help" (
  echo DSSC C Group Semantic Governance Package
  echo.
  echo Available targets:
  echo   help                 Show this help message
  echo   validate             Run all currently available validation checks
  echo   validate-rdf         Validate RDF/Turtle artifacts ^(stub in Phase 0^)
  echo   validate-shacl       Validate SHACL cases ^(stub in Phase 0^)
  echo   validate-jsonld      Validate JSON-LD artifacts ^(stub in Phase 0^)
  echo   validate-jsonschema  Validate JSON Schema cases ^(stub in Phase 0^)
  echo   validate-openapi     Validate OpenAPI fragments ^(stub in Phase 0^)
  echo   test-sparql          Run SPARQL competency tests ^(stub in Phase 0^)
  echo   quality              Run model quality metrics ^(stub in Phase 0^)
  echo   validate-governance  Validate governance docs and provenance metadata
  echo   check-links-and-paths Check local Markdown links and script path portability
  echo   check-required-files Verify required minimum/excellent/top-tier deliverables
  echo   treehouse-clone      Clone or fetch Semantic Treehouse upstream for evidence
  echo   treehouse-up         Attempt Semantic Treehouse evidence deployment
  echo   treehouse-down       Stop only the Treehouse compose project started by this harness
  echo   treehouse-status     Capture Treehouse compose/container status
  echo   evidence             Summarize evidence collection status ^(stub in Phase 0^)
  echo   clean                Remove generated caches and temporary files
  exit /b 0
)

if "%TARGET%"=="validate" (
  python C_Semantic_Treehouse\scripts\run_all_validations.py || exit /b 1
  call "%~f0" test-sparql || exit /b 1
  call "%~f0" quality || exit /b 1
  call "%~f0" validate-governance || exit /b 1
  call "%~f0" check-links-and-paths || exit /b 1
  call "%~f0" check-required-files || exit /b 1
  call "%~f0" evidence || exit /b 1
  echo Local validation harness completed.
  exit /b 0
)

if "%TARGET%"=="validate-rdf" (
  python C_Semantic_Treehouse\scripts\validate_rdf.py
  if errorlevel 1 exit /b 1
  exit /b 0
)

if "%TARGET%"=="validate-shacl" (
  python C_Semantic_Treehouse\scripts\validate_shacl.py
  if errorlevel 1 exit /b 1
  exit /b 0
)

if "%TARGET%"=="validate-jsonld" (
  python C_Semantic_Treehouse\scripts\validate_jsonld.py
  if errorlevel 1 exit /b 1
  exit /b 0
)

if "%TARGET%"=="validate-jsonschema" (
  python C_Semantic_Treehouse\scripts\validate_jsonschema.py
  if errorlevel 1 exit /b 1
  exit /b 0
)

if "%TARGET%"=="validate-openapi" (
  python C_Semantic_Treehouse\scripts\validate_openapi.py
  if errorlevel 1 exit /b 1
  exit /b 0
)

if "%TARGET%"=="test-sparql" (
  python C_Semantic_Treehouse\scripts\run_sparql_tests.py
  if errorlevel 1 exit /b 1
  exit /b 0
)

if "%TARGET%"=="quality" (
  python C_Semantic_Treehouse\scripts\quality_metrics.py
  if errorlevel 1 exit /b 1
  exit /b 0
)

if "%TARGET%"=="validate-governance" (
  python C_Semantic_Treehouse\scripts\validate_governance.py
  if errorlevel 1 exit /b 1
  exit /b 0
)

if "%TARGET%"=="check-links-and-paths" (
  python C_Semantic_Treehouse\scripts\check_links_and_paths.py
  if errorlevel 1 exit /b 1
  exit /b 0
)

if "%TARGET%"=="check-required-files" (
  python C_Semantic_Treehouse\scripts\check_required_files.py
  if errorlevel 1 exit /b 1
  exit /b 0
)

if "%TARGET%"=="treehouse-clone" (
  powershell -NoProfile -ExecutionPolicy Bypass -File C_Semantic_Treehouse\scripts\treehouse_clone_or_update.ps1
  if errorlevel 1 exit /b 1
  exit /b 0
)

if "%TARGET%"=="treehouse-up" (
  powershell -NoProfile -ExecutionPolicy Bypass -File C_Semantic_Treehouse\scripts\treehouse_up.ps1
  if errorlevel 1 exit /b 1
  exit /b 0
)

if "%TARGET%"=="treehouse-down" (
  powershell -NoProfile -ExecutionPolicy Bypass -File C_Semantic_Treehouse\scripts\treehouse_down.ps1
  if errorlevel 1 exit /b 1
  exit /b 0
)

if "%TARGET%"=="treehouse-status" (
  powershell -NoProfile -ExecutionPolicy Bypass -File C_Semantic_Treehouse\scripts\treehouse_status.ps1
  if errorlevel 1 exit /b 1
  exit /b 0
)

if "%TARGET%"=="evidence" (
  echo Phase 0 stub: evidence collection instructions are in C_Semantic_Treehouse/evidence/README.md.
  exit /b 0
)

if "%TARGET%"=="clean" (
  powershell -NoProfile -Command "Get-ChildItem -Recurse -Force -Directory -Include __pycache__,.pytest_cache,.mypy_cache | Remove-Item -Recurse -Force; Get-ChildItem -Recurse -Force -File -Include *.pyc,*.tmp | Remove-Item -Force"
  exit /b 0
)

echo Unknown target: %TARGET%
exit /b 2
