# Phase 8 Prompt — CI Pipeline and Final Repository Hardening

Implement Phase 8 only.

Objective:
Make the package CI-ready and robust for grading/demo.

Tasks:

1. Create .github/workflows/validate.yml:

   * trigger on push and pull_request
   * install Python dependencies
   * run make validate
   * upload validation reports as artifacts if possible

2. Add scripts/check_required_files.py:

   * verify all minimum, excellent, and top-tier files exist
   * verify v0.1/v0.2/v0.3 artifacts exist
   * verify reports exist
   * write validation/required-files-report.md

3. Add Makefile target:

   * make check-required-files
   * include it in make validate

4. Add scripts/check_links_and_paths.py:

   * detect broken local file references in Markdown where possible
   * detect absolute Windows-only paths in scripts
   * allow Windows paths only in documentation examples
   * write validation/path-link-report.md

5. Add docs/demo-script.md:
   A 5-minute demonstration script:

   * show repository structure
   * show model versions
   * show SHACL validation
   * show invalid metadata failure
   * show SPARQL competency questions
   * show Semantic Treehouse evidence
   * show A/D handoff
   * show quality metrics

6. Add docs/final-checklist.md with:

   * minimum checklist
   * excellent checklist
   * top-tier checklist
   * status: done/partial/not done
   * evidence path for each item

7. Run all validations and fix issues.

Acceptance criteria:

* make validate passes.
* Required-file check passes.
* CI file exists and is plausible.
* final-checklist.md maps every criterion to evidence.
* demo-script.md can be followed by a presenter.

Commands to run:

* make check-required-files
* make validate
* git status --short

Stop after Phase 8.

