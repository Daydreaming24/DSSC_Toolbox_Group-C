# Thin Make wrapper for Linux/CI. Does not implement validation logic.
# Windows core flow uses scripts/bootstrap.ps1 and scripts/validate.ps1 instead.

.PHONY: help bootstrap doctor validate-frozen validate-environment validate

SUITE ?= frozen
PUBLIC_SUITES := frozen environment baseline traceability v0.4-model v0.4 all

help:
	@echo "DSSC C Semantic Governance v0.4"
	@echo "  make bootstrap              # ./scripts/bootstrap.sh"
	@echo "  make doctor                 # doctor --profile host"
	@echo "  make validate-frozen        # validate.py --suite frozen"
	@echo "  make validate-environment   # validate.py --suite environment"
	@echo "  make validate SUITE=frozen  # generic suite dispatcher"

bootstrap:
	./scripts/bootstrap.sh

doctor:
	./.venv/bin/python -I scripts/doctor.py --profile host

validate-frozen:
	./scripts/validate.sh --suite frozen

validate-environment:
	./scripts/validate.sh --suite environment

validate:
ifeq ($(filter $(SUITE),$(PUBLIC_SUITES)),)
	@echo "SUITE must be one of: $(PUBLIC_SUITES)" >&2
	@exit 2
else
	./scripts/validate.sh --suite $(SUITE)
endif
