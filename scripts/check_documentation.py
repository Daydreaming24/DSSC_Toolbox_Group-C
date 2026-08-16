#!/usr/bin/env python3
"""Fail-closed Phase 07 documentation and Mermaid structure checker.

The checker validates the current documentation package against repository
manifests.  Mermaid checks are deliberately structural: this module does not
invoke a Mermaid parser or renderer and never reports syntax/render PASS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shlex
import subprocess
import sys
import tempfile
from unittest import mock
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]

CHECK_ID = "all.documentation"
RESULT_SCHEMA_VERSION = "1.0.0"
EXPECTED_CONTRACT_VERSION = "1.6.0"
PUBLIC_SUITES = (
    "frozen",
    "environment",
    "baseline",
    "traceability",
    "v0.4-model",
    "v0.4",
    "all",
)
EXPECTED_ALL_DEPENDENCIES = PUBLIC_SUITES[:-1]
EXPECTED_ALL_COMPONENTS = (
    {"id": "all.composition", "entrypoint": "check_all_composition"},
    {"id": "all.semantic-sparql", "entrypoint": "check_semantic_sparql"},
    {"id": "all.quality", "entrypoint": "check_quality_metrics"},
    {"id": "all.governance", "entrypoint": "check_governance"},
    {"id": "all.documentation", "entrypoint": "check_documentation"},
)
EXPECTED_SUITE_PROJECTION: dict[str, dict[str, Any]] = {
    "frozen": {
        "status": "IMPLEMENTED",
        "depends_on": (),
        "components": (("frozen.manifest", "check_frozen_files"),),
        "owner_phase": "01",
    },
    "environment": {
        "status": "IMPLEMENTED",
        "depends_on": (),
        "components": (("environment.doctor", "check_environment"),),
        "owner_phase": "01",
    },
    "baseline": {
        "status": "IMPLEMENTED",
        "depends_on": ("environment",),
        "components": (("baseline.reproduction", "check_baseline"),),
        "owner_phase": "02",
    },
    "traceability": {
        "status": "IMPLEMENTED",
        "depends_on": ("environment",),
        "components": (("traceability.contract-audit", "check_traceability"),),
        "owner_phase": "03",
    },
    "v0.4-model": {
        "status": "IMPLEMENTED",
        "depends_on": ("environment", "traceability"),
        "components": (("v0.4-model.release-contract", "check_v04_model"),),
        "owner_phase": "04",
    },
    "v0.4": {
        "status": "IMPLEMENTED",
        "depends_on": ("environment", "v0.4-model"),
        "components": (
            ("v0.4.test-case-schema", "check_v04_test_case_schema"),
            ("v0.4.manifest-semantics", "check_v04_manifest_semantics"),
            ("v0.4.fixture-hashes", "check_v04_fixture_hashes"),
            ("v0.4.four-state", "check_v04_four_state"),
            ("v0.4.report-assertions", "check_v04_report_assertions"),
            ("v0.4.target-activation", "check_v04_target_activation"),
            ("v0.4.fault-injection", "check_v04_fault_injection"),
        ),
        "owner_phase": "05",
    },
    "all": {
        "status": "IMPLEMENTED",
        "depends_on": EXPECTED_ALL_DEPENDENCIES,
        "components": tuple(
            (component["id"], component["entrypoint"])
            for component in EXPECTED_ALL_COMPONENTS
        ),
        "owner_phase": "05",
    },
}

DOCUMENT_PATHS = (
    "README.md",
    "迁移清单.md",
    "docs/v0.4/README.md",
    "C_Semantic_Treehouse/README.md",
    "C_Semantic_Treehouse/scripts/README.md",
    "C_Semantic_Treehouse/C_semantic_model_design.md",
    "C_Semantic_Treehouse/C_semantic_treehouse_usage.md",
    "C_Semantic_Treehouse/C_semantic_treehouse_user_guide.md",
    "C_Semantic_Treehouse/C_model_versioning_demo.md",
    "C_Semantic_Treehouse/C_export_for_validation.md",
    "C_Semantic_Treehouse/handoff/handoff-to-A-offering-metadata.md",
    "C_Semantic_Treehouse/handoff/handoff-to-B-model-uri-provenance.md",
    "C_Semantic_Treehouse/handoff/handoff-to-D-shacl-validation.md",
    "C_Semantic_Treehouse/docs/ai-assisted-human-governed-semantic-modeling.md",
)

CORE_REPORT_PATHS = (
    "C_Semantic_Treehouse/C_semantic_model_design.md",
    "C_Semantic_Treehouse/C_semantic_treehouse_usage.md",
    "C_Semantic_Treehouse/C_model_versioning_demo.md",
    "C_Semantic_Treehouse/C_export_for_validation.md",
)

DIAGRAM_SPECS: dict[str, dict[str, Any]] = {
    "C_Semantic_Treehouse/diagrams/metadata-record-model.mmd": {
        "nodes": (
            "Provider",
            "PackageRelease",
            "DatasetV04",
            "RecordV03",
            "DShape",
            "Harness",
            "PASS",
            "FAIL",
            "INAPPLICABLE",
            "UNTESTABLE",
            "AOffering",
            "BProvenance",
            "DValidation",
        ),
        "edges": (
            ("Provider", "DatasetV04"),
            ("PackageRelease", "DatasetV04"),
            ("PackageRelease", "RecordV03"),
            ("DShape", "Harness"),
            ("DatasetV04", "Harness"),
            ("Harness", "PASS"),
            ("Harness", "FAIL"),
            ("Harness", "INAPPLICABLE"),
            ("Harness", "UNTESTABLE"),
            ("DatasetV04", "AOffering"),
            ("PackageRelease", "BProvenance"),
            ("Harness", "DValidation"),
        ),
        "labels": (
            "Provider",
            "package/release contract",
            "dcat:Dataset",
            "v0.4",
            "v0.3",
            "D Shape",
            "A offering",
            "B provenance",
            "D validation",
        ),
    },
    "C_Semantic_Treehouse/diagrams/semantic-governance-flow.mmd": {
        "nodes": (
            "FrozenD",
            "Requirements",
            "Decision",
            "ReleaseManifest",
            "Fixtures",
            "TestManifest",
            "Validation",
            "SemanticReview",
            "DomainReview",
            "Handoff",
            "Release",
            "Monitor",
            "Deprecate",
            "Treehouse",
        ),
        "edges": (
            ("FrozenD", "Requirements"),
            ("FrozenD", "Decision"),
            ("Requirements", "ReleaseManifest"),
            ("Decision", "ReleaseManifest"),
            ("ReleaseManifest", "Fixtures"),
            ("ReleaseManifest", "TestManifest"),
            ("Fixtures", "Validation"),
            ("TestManifest", "Validation"),
            ("Validation", "SemanticReview"),
            ("SemanticReview", "DomainReview"),
            ("DomainReview", "Handoff"),
            ("Handoff", "Release"),
            ("Release", "Monitor"),
            ("Monitor", "Deprecate"),
            ("Validation", "Treehouse"),
        ),
        "labels": (
            "D frozen",
            "requirement",
            "decision",
            "release manifest",
            "test manifest",
            "semantic review",
            "domain review",
            "handoff",
            "monitor",
            "deprecate",
            "optional",
        ),
    },
}

BINDING_TABLE_SPECS: dict[str, tuple[dict[str, Any], ...]] = {
    "C_Semantic_Treehouse/handoff/handoff-to-A-offering-metadata.md": (
        {
            "headers": ("artifact_id", "path", "sha_256"),
            "paths": (
                "C_Semantic_Treehouse/model/v0.4/data-product-context.jsonld",
                "C_Semantic_Treehouse/model/v0.4/data-product-valid.jsonld",
            ),
        },
    ),
    "C_Semantic_Treehouse/handoff/handoff-to-B-model-uri-provenance.md": (
        {
            "headers": ("item", "manifest_id_ref", "repository_path", "sha_256"),
            "paths": (
                "inputs/d-group/v0.4/received/building-energy-shapes_D.ttl",
                "inputs/d-group/v0.4/received/初始TTL到最终TTL修改说明.md",
                "C_Semantic_Treehouse/model/v0.4/building-energy-ontology.ttl",
                "C_Semantic_Treehouse/model/v0.4/data-product-context.jsonld",
                "C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl",
                "C_Semantic_Treehouse/model/v0.4/data-product-valid.jsonld",
                "C_Semantic_Treehouse/manifests/release-manifest.json",
                "C_Semantic_Treehouse/manifests/validation-suites.json",
            ),
        },
    ),
    "C_Semantic_Treehouse/handoff/handoff-to-D-shacl-validation.md": (
        {
            "headers": ("role", "manifest_ref_artifact_id", "repository_path", "sha_256"),
            "paths": (
                "inputs/d-group/v0.4/received/building-energy-shapes_D.ttl",
                "C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl",
            ),
        },
        {
            "headers": ("authority", "path", "sha_256_scope"),
            "paths": (
                "C_Semantic_Treehouse/manifests/v0.4-requirements.json",
                "C_Semantic_Treehouse/manifests/v0.4-test-cases.json",
                "C_Semantic_Treehouse/fixtures/v0.4",
            ),
        },
    ),
}

SOURCE_PATHS = (
    ("scripts/check_documentation.py", ("checker", "reporter")),
    ("scripts/validate.py", ("dispatcher",)),
    ("scripts/dssc_validation/suite_registry.py", ("registry-loader",)),
    ("scripts/dssc_validation/entrypoint_catalog.py", ("entrypoint-catalog",)),
    ("scripts/dssc_validation/checks_all.py", ("all-composition-checker",)),
)

AUTHORITY_JSON_PATHS = (
    "C_Semantic_Treehouse/manifests/release-manifest.json",
    "C_Semantic_Treehouse/manifests/baseline-test-cases.json",
    "C_Semantic_Treehouse/manifests/v0.4-requirements.json",
    "C_Semantic_Treehouse/manifests/v0.4-test-cases.json",
    "C_Semantic_Treehouse/manifests/validation-suites.json",
    "build/validation/v0.4/results.json",
    "build/validation/sparql/results.json",
    "build/validation/quality/results.json",
    "build/validation/governance/results.json",
)

GENERATED_OUTPUT_PATHS = frozenset(
    {
        # Exact generated-evidence references used by the checked reports.  A
        # clean source tree intentionally contains none of these build files.
        "build/validation",
        "build/phase-05",
        "build/phase-07",
        "build/evidence/treehouse",
        "build/evidence/treehouse/decision.json",
        "build/evidence/treehouse/runtime-auth-storage-recovery-admin-only-2026-08-12.json",
        "build/evidence/treehouse/v0.4-import-2026-08-12.json",
        "build/evidence/treehouse/v0.4-import-post-restart-2026-08-12.json",
        "build/evidence/treehouse/browser-ui-import-verification-2026-08-12.json",
        # Phase 08 SHACL validator / pause addendum evidence (host-only ignored
        # runtime outputs). Allow clean-room documentation checks when the
        # empty Docker build mount does not contain these generated files.
        "build/evidence/treehouse/shacl-validator-execution-2026-08-12.json",
        "build/evidence/treehouse/shacl-validator-execution-idempotent-recheck-2026-08-12.json",
        "build/evidence/treehouse/runtime-pause-after-shacl-validation-2026-08-12.json",
        "build/evidence/itb-semic/decision.json",
        "build/validation/v0.4/results.json",
        "build/validation/v0.4/report.md",
        "build/validation/v0.4/run-environment.json",
        "build/validation/sparql/results.json",
        "build/validation/quality/results.json",
        "build/validation/governance/results.json",
        "build/validation/documentation/results.json",
        "build/validation/documentation/report.md",
        "build/validation/documentation/run-environment.json",
        "build/phase-07/documentation-negative-controls.json",
    }
)

CONTENT_REQUIREMENTS: dict[str, tuple[tuple[str, ...], ...]] = {
    "README.md": (
        ("Building Energy",),
        ("building-energy-hourly-v1",),
        ("frozen",),
        ("build/", "build\\"),
        ("environment",),
        ("baseline",),
        ("traceability",),
        ("v0.4-model",),
        ("PASS",),
        ("FAIL",),
        ("INAPPLICABLE",),
        ("UNTESTABLE",),
        ("SUCCESS",),
        ("ERROR",),
        ("网络", "network"),
        ("Phase 08",),
        ("Phase 09",),
        ("NOT RUN",),
    ),
    "迁移清单.md": (
        ("Phase 07",),
        ("Phase 08",),
        ("Phase 09",),
        ("STATUS.md",),
        ("Docker",),
        ("CI",),
        ("GitHub",),
    ),
    "docs/v0.4/README.md": (
        ("requirements-traceability.md",),
        ("decisions",),
        ("STATUS.md",),
        ("CHECKPOINT.md",),
        ("compatibility", "兼容"),
        ("model-derivation.md",),
        ("reproducibility-contract.md",),
        ("Phase 08",),
        ("Phase 09",),
    ),
    "C_Semantic_Treehouse/README.md": (
        ("release-manifest.json",),
        ("validation-suites.json",),
        ("governance",),
        ("handoff",),
        ("evidence",),
        ("demo",),
    ),
    "C_Semantic_Treehouse/scripts/README.md": (
        ("scripts/validate.py", "scripts\\validate.py"),
        ("dispatcher",),
        ("check_documentation.py",),
        ("Treehouse",),
        ("Phase 08",),
        ("历史", "historical"),
    ),
    "C_Semantic_Treehouse/C_semantic_model_design.md": (
        ("scope", "范围"),
        ("DSSC",),
        ("两层", "two-layer"),
        ("JSON-LD",),
        ("SHACL",),
        ("record",),
        ("competency",),
        ("局限", "limitations"),
        ("future", "后续"),
    ),
    "C_Semantic_Treehouse/C_semantic_treehouse_usage.md": (
        ("v0",),
        ("v0.4",),
        ("validation harness", "验证 harness"),
        ("Phase 08",),
        ("UI",),
        ("API",),
        ("import", "导入"),
        ("export", "导出"),
        ("NOT RUN",),
        ("fallback", "回退"),
    ),
    "C_Semantic_Treehouse/C_model_versioning_demo.md": (
        ("v0.1",),
        ("v0.2",),
        ("v0.3",),
        ("v0.4",),
        ("wire-profile breaking", "wire profile breaking", "不兼容 wire"),
        ("namespace",),
        ("record", "继承"),
        ("deprecat", "弃用"),
        ("A 组", "A group"),
        ("B 组", "B group"),
        ("D 组", "D group"),
    ),
    "C_Semantic_Treehouse/C_export_for_validation.md": (
        ("building-energy-shapes_D.ttl",),
        ("v0.4-requirements.json",),
        ("v0.4-test-cases.json",),
        ("focus",),
        ("source shape", "sourceShape"),
        ("constraint component", "constraintComponent"),
        ("SEMIC",),
        ("ITB",),
        ("pySHACL",),
        ("NOT RUN",),
    ),
    "C_Semantic_Treehouse/handoff/handoff-to-A-offering-metadata.md": (
        ("requirement_id",),
        ("JSON key",),
        ("cardinality",),
        ("allowed value",),
        ("data-product-valid.jsonld",),
        ("https://",),
        ("dct:conformsTo",),
        ("Closed Shape",),
        ("expected",),
    ),
    "C_Semantic_Treehouse/handoff/handoff-to-B-model-uri-provenance.md": (
        ("https://w3id.org/dssc-demo/building-energy/v0.4",),
        ("profile",),
        ("provenance",),
        ("entity",),
        ("activity",),
        ("agent",),
        ("Gaia-X",),
        ("法律", "legal"),
    ),
    "C_Semantic_Treehouse/handoff/handoff-to-D-shacl-validation.md": (
        ("building-energy-shapes_D.ttl",),
        ("v0.4-requirements.json",),
        ("v0.4-test-cases.json",),
        ("focus node", "focusNode"),
        ("source shape", "sourceShape"),
        ("constraint component", "constraintComponent"),
        ("severity",),
        ("message",),
        ("value",),
        ("ITB",),
        ("NOT RUN",),
    ),
    "C_Semantic_Treehouse/docs/ai-assisted-human-governed-semantic-modeling.md": (
        ("AI",),
        ("fixture",),
        ("D 契约", "D contract"),
        ("semantic",),
        ("domain",),
        ("validator",),
        ("发布授权", "release authorization"),
        ("prompt",),
        ("manifest",),
        ("diff",),
        ("provenance",),
        ("demo",),
    ),
}

CURRENT_NOT_RUN_RULES: dict[str, tuple[str, ...]] = {
    "C_Semantic_Treehouse/C_semantic_treehouse_usage.md": (
        "Semantic Treehouse publication",
        "SEMIC external validation",
        "DSSC ITB execution",
    ),
    "C_Semantic_Treehouse/C_export_for_validation.md": (
        "SEMIC Validator",
        "DSSC ITB",
        "Semantic Treehouse",
    ),
    "C_Semantic_Treehouse/handoff/handoff-to-D-shacl-validation.md": (
        "外部 SEMIC validator",
        "外部 ITB test suite/service",
        "Semantic Treehouse",
    ),
    "C_Semantic_Treehouse/docs/ai-assisted-human-governed-semantic-modeling.md": (
        "Semantic Treehouse",
        "外部 SEMIC/ITB",
        "Mermaid parser",
    ),
}

PUBLICATION_RECORD_PATH = "docs/v0.4/publication-record.md"
CANONICAL_REPOSITORY_URL = "https://github.com/Daydreaming24/DSSC_Toolbox_Group-C.git"
FINAL_NAVIGATION_PATHS = (
    "README.md",
    "docs/v0.4/README.md",
    "C_Semantic_Treehouse/README.md",
)
HISTORICAL_REPOSITORY_STATUS_RULES: dict[str, tuple[tuple[str, str], ...]] = {
    "C_Semantic_Treehouse/C_semantic_treehouse_usage.md": (
        ("GitHub Actions / remote publication（上一已确认候选）", "PASS"),
    ),
}

TREEHOUSE_USAGE_PATH = "C_Semantic_Treehouse/C_semantic_treehouse_usage.md"
TREEHOUSE_CURRENT_DOC_PATHS = (
    TREEHOUSE_USAGE_PATH,
    "tools/semantic-treehouse/README.md",
    "C_Semantic_Treehouse/scripts/README.md",
    "scripts/README.md",
    "docs/environment.md",
    "docs/v0.4/reproducibility-contract.md",
)
TREEHOUSE_SCOPED_SUMMARY_PATHS = TREEHOUSE_CURRENT_DOC_PATHS
TREEHOUSE_RECOVERY_EVIDENCE_PATHS = (
    "build/evidence/treehouse/runtime-auth-storage-recovery-admin-only-2026-08-12.json",
    "build/evidence/treehouse/v0.4-import-2026-08-12.json",
    "build/evidence/treehouse/v0.4-import-post-restart-2026-08-12.json",
    "build/evidence/treehouse/browser-ui-import-verification-2026-08-12.json",
    "build/evidence/treehouse/shacl-validator-execution-2026-08-12.json",
    "build/evidence/treehouse/shacl-validator-execution-idempotent-recheck-2026-08-12.json",
    "build/evidence/treehouse/runtime-pause-after-shacl-validation-2026-08-12.json",
)
TREEHOUSE_SHACL_VALIDATOR_MANIFEST_DIGEST = "sha256:208dc8b9be042d96164ef85d2f9a904c8a0da8f7df366057d5ba5f43dffc2b0b"
CURRENT_TREEHOUSE_SCOPED_BOUNDARY_TOKENS = (
    f"`SHACL validator manifest digest={TREEHOUSE_SHACL_VALIDATOR_MANIFEST_DIGEST}`",
    "`SHACL validator security boundary=non-root/internal-only/zero-host-port/read-only-rootfs/drop-all/no-new-privileges/resource-bounded`",
    "`SHACL validation controls=positive-pass/negative-fail/idempotent-recheck-pass/EasyRDF-4-pattern-local-review-patch`",
    "`PAUSED persistence=containers-networks-app-db-volumes-preserved`",
)
HISTORICAL_TREEHOUSE_STATUS_RULES: tuple[tuple[str, str], ...] = (
    ("Semantic Treehouse fixed checkout/materialization", "PASS"),
    ("Semantic Treehouse raw upstream compose preflight", "BLOCKED"),
    ("Semantic Treehouse finding-specific human opt-in", "APPROVED"),
    ("Semantic Treehouse PrepareOnly runtime boundary", "PASS"),
    ("Semantic Treehouse image build attempt", "BLOCKED"),
    ("Semantic Treehouse deployment", "NOT DEPLOYED"),
    ("Semantic Treehouse workload/container execution", "NOT RUN"),
    ("Semantic Treehouse database migration", "NOT RUN"),
    ("Semantic Treehouse UI workflow", "NOT RUN"),
    ("Semantic Treehouse API", "NOT RUN"),
    ("Semantic Treehouse model import", "NOT RUN"),
    ("Semantic Treehouse export", "NOT RUN"),
    ("Semantic Treehouse publication", "NOT RUN"),
)
CURRENT_TREEHOUSE_SCOPED_STATUS_RULES: tuple[tuple[str, str], ...] = (
    ("checkout", "PASS"),
    ("raw preflight", "BLOCKED"),
    ("opt-in", "APPROVED"),
    ("PrepareOnly", "PASS"),
    ("image build", "PASS"),
    ("deployment", "PASS"),
    ("workload", "PASS"),
    ("database migration", "PASS"),
    ("current runtime", "PAUSED"),
    ("root loopback smoke", "PASS"),
    ("API loopback availability smoke", "PASS"),
    ("UI workflow", "PASS"),
    ("model import", "PASS"),
    ("export", "PASS"),
    ("publication", "NOT RUN"),
    ("SHACL validator execution", "PASS"),
)

EXPECTED_FIELD_ALLOWED: dict[str, str] = {
    "D04-R003": "至少 1 个字符并匹配 `\\S`，即至少含一个非空白字符",
    "D04-R004": "至少 1 个字符并匹配 `\\S`，即至少含一个非空白字符",
    "D04-R005": "至少 1 个字符并匹配 `\\S`，即至少含一个非空白字符",
    "D04-R006": "至少 1 个字符并匹配 `\\S`，即至少含一个非空白字符",
    "D04-R007": "`hourly`，精确且大小写敏感",
    "D04-R008": "`kWh`，精确且大小写敏感",
    "D04-R009": "`application/json`，精确值",
    "D04-R010": "IRI 字符串匹配 `^https://`",
    "D04-R011": "合法的 `xsd:date` lexical form",
    "D04-R012": "合法的 `xsd:date` lexical form",
    "D04-R014": "出现时为一个字符串",
    "D04-R015": "出现时 IRI 字符串匹配 `^https://`",
}

REQUIRED_INLINE_BINDINGS: dict[str, tuple[str, ...]] = {
    "C_Semantic_Treehouse/C_semantic_model_design.md": (
        "inputs/d-group/v0.4/received/building-energy-shapes_D.ttl",
    ),
    "C_Semantic_Treehouse/C_export_for_validation.md": (
        "inputs/d-group/v0.4/received/building-energy-shapes_D.ttl",
        "C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl",
    ),
}

REQUIRED_STATUS_COUNT_PATHS = (
    "迁移清单.md",
    "C_Semantic_Treehouse/C_semantic_model_design.md",
    "C_Semantic_Treehouse/C_export_for_validation.md",
    "C_Semantic_Treehouse/handoff/handoff-to-A-offering-metadata.md",
)

MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
REFERENCE_LINK_RE = re.compile(r"!?\[([^\]]+)\]\[([^\]]*)\]")
REFERENCE_DEF_RE = re.compile(r"^\s*\[([^\]]+)\]:\s*(\S+)", re.MULTILINE)
SHORTCUT_REFERENCE_RE = re.compile(r"!?\[([^\]]+)\](?![\[(])")
CODE_SPAN_RE = re.compile(r"`([^`\r\n]+)`")
HASH_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])")
ARTIFACT_ID_RE = re.compile(r"\bv0[1-4]-[a-z0-9][a-z0-9-]*\b")
CASE_ID_RE = re.compile(r"^D04-PC\d{3}$")
WINDOWS_ABSOLUTE_RE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]")
UNC_RE = re.compile(r"\\\\[^\\\s]+[\\/]")
POSIX_PERSONAL_RE = re.compile(r"(?<![:A-Za-z0-9])/(?:home|Users|tmp|private/tmp|var/tmp|usr|opt|etc|root|mnt)/")
HOME_EXPANSION_RE = re.compile(r"(?:\$HOME|\$\{HOME\}|~|%USERPROFILE%|\$env:USERPROFILE)[\\/]", re.IGNORECASE)
TEMP_TOKEN_RE = re.compile(r"(?:%TEMP%|\$env:TEMP|\$TMPDIR|<TEMP(?:_DIR)?>)", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|PLACEHOLDER|FIXME|XXX)\b|待补充|占位符", re.IGNORECASE)
STATUS_VALUES = frozenset({"PASS", "FAIL", "INAPPLICABLE", "UNTESTABLE"})
GLOBAL_PYTHON_PATTERN = r"(?:python(?:3(?:\.\d+)?)?(?:\.exe)?|py(?:\.exe)?)"
GLOBAL_PYTHON_INVOCATION_PATTERN = rf"{GLOBAL_PYTHON_PATTERN}(?:\s+-\d+(?:\.\d+)?)?"
VENV_PYTHON_PATTERN = r"(?:\.\\\.venv\\Scripts\\python\.exe|\./\.venv/bin/python)"
ANY_PYTHON_PATTERN = rf"(?:{GLOBAL_PYTHON_INVOCATION_PATTERN}|{VENV_PYTHON_PATTERN})"
REPOSITORY_SCRIPT_PATTERN = (
    r"(?:\.?[\\/]?)?(?:scripts|C_Semantic_Treehouse[\\/]scripts)"
    r"[\\/][A-Za-z0-9_.-]+\.(?:py|ps1|sh)"
)


@dataclass(frozen=True)
class Issue:
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="wb", prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_json(path: Path, value: Any) -> None:
    _atomic_write(path, _json_bytes(value))


def _write_text(path: Path, value: str) -> None:
    _atomic_write(path, value.encode("utf-8"))


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str):
                yield key
            yield from _walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)


def _strip_cell(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^[*_]+|[*_]+$", "", value)
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        value = value[1:-1]
    return value.strip()


def _split_table_row(line: str) -> list[str]:
    """Split a CommonMark pipe-table row without splitting escaped/code pipes."""

    raw = line.strip()
    if not raw:
        return []
    cells: list[str] = []
    buffer: list[str] = []
    code_delimiter = 0
    saw_delimiter = False
    index = 0
    while index < len(raw):
        character = raw[index]
        if character == "\\" and index + 1 < len(raw) and raw[index + 1] == "|":
            buffer.extend((character, raw[index + 1]))
            index += 2
            continue
        if character == "`":
            cursor = index
            while cursor < len(raw) and raw[cursor] == "`":
                cursor += 1
            run_length = cursor - index
            if code_delimiter == 0:
                code_delimiter = run_length
            elif code_delimiter == run_length:
                code_delimiter = 0
            buffer.append(raw[index:cursor])
            index = cursor
            continue
        if character == "|" and code_delimiter == 0:
            cells.append(_strip_cell("".join(buffer)))
            buffer = []
            saw_delimiter = True
        else:
            buffer.append(character)
        index += 1
    cells.append(_strip_cell("".join(buffer)))
    if not saw_delimiter:
        return []
    if raw.startswith("|") and cells and cells[0] == "":
        cells.pop(0)
    if raw.endswith("|") and not raw.endswith("\\|") and cells and cells[-1] == "":
        cells.pop()
    return cells


def _table_rows(
    text: str,
) -> Iterable[tuple[list[str], list[list[str]], list[tuple[int, str]]]]:
    lines = text.splitlines()
    index = 0
    while index + 1 < len(lines):
        header = _split_table_row(lines[index])
        separators = _split_table_row(lines[index + 1])
        if len(header) < 2 or len(header) != len(separators):
            index += 1
            continue
        if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in separators):
            index += 1
            continue
        rows: list[list[str]] = []
        malformed: list[tuple[int, str]] = []
        cursor = index + 2
        while cursor < len(lines):
            cells = _split_table_row(lines[cursor])
            if not cells:
                break
            if len(cells) == len(header):
                rows.append(cells)
            else:
                malformed.append((cursor + 1, lines[cursor]))
            cursor += 1
        yield header, rows, malformed
        index = cursor


def _case_sensitive_state(root: Path, target: Path) -> tuple[bool, bool]:
    """Return (exists, exact_case) for a repository-local path."""

    # ``Path.resolve`` canonicalizes on-disk case on Windows and would hide a
    # misspelled Markdown path.  Keep the caller's lexical case while folding
    # ``..`` segments, then walk each directory with exact-name comparisons.
    root_resolved = Path(os.path.abspath(os.path.normpath(str(root))))
    target_resolved = Path(os.path.abspath(os.path.normpath(str(target))))
    try:
        relative = target_resolved.relative_to(root_resolved)
    except ValueError:
        return target.exists(), False
    current = root_resolved
    exact_case = True
    for part in relative.parts:
        if not current.is_dir():
            return False, False
        names = [item.name for item in current.iterdir()]
        if part in names:
            current = current / part
            continue
        casefold_matches = [name for name in names if name.casefold() == part.casefold()]
        if casefold_matches:
            exact_case = False
            current = current / casefold_matches[0]
            continue
        return False, False
    return current.exists(), exact_case


def _link_target(raw: str) -> str:
    value = raw.strip()
    if value.startswith("<") and ">" in value:
        value = value[1 : value.index(">")]
    else:
        value = re.sub(r"\s+[\"'].*[\"']\s*$", "", value)
    return unquote(value.split("#", 1)[0].split("?", 1)[0].strip())


def _is_external(target: str) -> bool:
    lowered = target.lower()
    return lowered.startswith(("http://", "https://", "mailto:", "app://", "data:"))


def _repository_relative_path(root: Path, target: Path) -> str | None:
    root_resolved = Path(os.path.abspath(os.path.normpath(str(root))))
    target_resolved = Path(os.path.abspath(os.path.normpath(str(target))))
    try:
        return target_resolved.relative_to(root_resolved).as_posix()
    except ValueError:
        return None


def _read_sources(
    root: Path,
    paths: Sequence[str],
    overrides: Mapping[str, str] | None = None,
) -> tuple[dict[str, str], list[Issue]]:
    sources: dict[str, str] = {}
    issues: list[Issue] = []
    overrides = overrides or {}
    for relative in paths:
        if relative in overrides:
            sources[relative] = overrides[relative]
            continue
        path = root / relative
        if not path.is_file():
            issues.append(Issue("DOC_MISSING", relative, "required documentation file is absent"))
            continue
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            issues.append(Issue("DOC_EMPTY", relative, "required documentation file is empty"))
            continue
        sources[relative] = text
    if not sources:
        issues.append(Issue("DOC_ZERO_DISCOVERY", ".", "zero documentation files were discovered"))
    return sources, issues


def _check_links(root: Path, sources: Mapping[str, str]) -> list[Issue]:
    issues: list[Issue] = []
    for relative, text in sources.items():
        source = root / relative

        def inspect(raw: str, line_number: int) -> None:
            if raw.strip().startswith("#"):
                return
            target = _link_target(raw)
            if not target:
                return
            if _is_external(target):
                return
            if Path(target).is_absolute() or WINDOWS_ABSOLUTE_RE.search(target) or target.startswith(("/", "\\")):
                issues.append(Issue("ABSOLUTE_LINK", relative, f"line {line_number}: absolute local link {raw!r}"))
                return
            resolved = source.parent / target.replace("/", os.sep).replace("\\", os.sep)
            exists, exact_case = _case_sensitive_state(root, resolved)
            if not exists:
                repository_path = _repository_relative_path(root, resolved)
                if repository_path in GENERATED_OUTPUT_PATHS:
                    return
                issues.append(Issue("BROKEN_LINK", relative, f"line {line_number}: missing link target {raw!r}"))
            elif not exact_case:
                issues.append(Issue("LINK_CASE_MISMATCH", relative, f"line {line_number}: link case differs from repository path {raw!r}"))

        without_comments = re.sub(
            r"<!--.*?-->",
            lambda match: "\n" * match.group(0).count("\n"),
            text,
            flags=re.DOTALL,
        )
        visible_lines: list[str] = []
        inside_fence = False
        for line in without_comments.splitlines():
            if line.strip().startswith("```"):
                inside_fence = not inside_fence
                visible_lines.append("")
            else:
                visible_lines.append("" if inside_fence else line)
        visible_text = "\n".join(visible_lines)
        definitions: dict[str, tuple[str, int]] = {}
        for match in REFERENCE_DEF_RE.finditer(visible_text):
            definitions.setdefault(
                match.group(1).casefold(),
                (match.group(2), visible_text.count("\n", 0, match.start()) + 1),
            )
        for line_number, line in enumerate(visible_lines, start=1):
            scan_line = CODE_SPAN_RE.sub("", line)
            for match in MARKDOWN_LINK_RE.finditer(scan_line):
                inspect(match.group(1), line_number)
            for match in REFERENCE_LINK_RE.finditer(scan_line):
                reference = (match.group(2) or match.group(1)).casefold()
                definition = definitions.get(reference)
                if definition is None:
                    issues.append(Issue("BROKEN_LINK", relative, f"line {line_number}: undefined reference-style link {reference!r}"))
                else:
                    inspect(definition[0], definition[1])
            if REFERENCE_DEF_RE.match(scan_line):
                continue
            for match in SHORTCUT_REFERENCE_RE.finditer(scan_line):
                reference = match.group(1).casefold()
                definition = definitions.get(reference)
                if definition is not None:
                    inspect(definition[0], definition[1])
    return issues


def _check_absolute_and_temporary_paths(sources: Mapping[str, str]) -> list[Issue]:
    issues: list[Issue] = []
    for relative, text in sources.items():
        for line_number, line in enumerate(text.splitlines(), start=1):
            code_has_posix_absolute = any(
                token.strip().startswith("/")
                and not token.strip().startswith("//")
                and not (
                    relative in TREEHOUSE_CURRENT_DOC_PATHS
                    and token.strip() in {"/api/environment/info", "/app/var/user_data"}
                )
                for token in CODE_SPAN_RE.findall(line)
            )
            if (
                WINDOWS_ABSOLUTE_RE.search(line)
                or UNC_RE.search(line)
                or POSIX_PERSONAL_RE.search(line)
                or code_has_posix_absolute
                or HOME_EXPANSION_RE.search(line)
            ):
                issues.append(Issue("PERSONAL_ABSOLUTE_PATH", relative, f"line {line_number}: personal or repository-external absolute path"))
            if TEMP_TOKEN_RE.search(line):
                issues.append(Issue("TEMPORARY_PATH", relative, f"line {line_number}: temporary directory token is not allowed in current documentation"))
    return issues


def _command_lines(text: str) -> Iterable[tuple[int, str]]:
    inside_fence = False
    for line_number, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if stripped.startswith("```"):
            inside_fence = not inside_fence
            continue
        if inside_fence and stripped and not stripped.startswith(("#", "<!--")):
            yield line_number, stripped
        elif not inside_fence:
            for token in CODE_SPAN_RE.findall(raw):
                candidate = token.strip()
                if re.match(
                    rf"^(?:{GLOBAL_PYTHON_PATTERN}(?:\s|$)|\.\\\.venv[\\/]|\./\.venv/|\.\\scripts\\validate\.ps1|\./scripts/validate\.sh)",
                    candidate,
                    re.IGNORECASE,
                ):
                    yield line_number, candidate


def _explicit_venv_invocation(command: str) -> tuple[str | None, str | None]:
    """Return the explicit repository venv interpreter and executed repo script."""

    match = re.match(rf"^(?P<interpreter>{VENV_PYTHON_PATTERN})(?:\s|$)", command, re.IGNORECASE)
    if match is None:
        return None, None
    interpreter = match.group("interpreter")
    try:
        tokens = shlex.split(command, posix="/" in interpreter)
    except ValueError:
        return interpreter, None
    tokens = [token[1:-1] if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'" else token for token in tokens]
    index = 1
    while index < len(tokens):
        token = tokens[index]
        if token == "--":
            index += 1
            break
        if token in {"-c", "-m"}:
            return interpreter, None
        if token in {"-W", "-X", "--check-hash-based-pycs"}:
            index += 2
            continue
        if token.startswith("-"):
            index += 1
            continue
        break
    if index < len(tokens) and re.fullmatch(REPOSITORY_SCRIPT_PATTERN, tokens[index], re.IGNORECASE):
        return interpreter, tokens[index]
    return interpreter, None


def _normalized_command_path(raw_path: str) -> str:
    candidate = raw_path
    if candidate.startswith((".\\", "./")):
        candidate = candidate[2:]
    return candidate.replace("\\", "/")


def _generated_venv_interpreter(
    candidate: str,
    explicit_interpreter: str | None,
    explicit_script: str | None,
) -> bool:
    if (
        explicit_interpreter is None
        or explicit_script is None
        or candidate != _normalized_command_path(explicit_interpreter)
    ):
        return False
    return candidate in {".venv/Scripts/python.exe", ".venv/bin/python"}


def _command_path_contract(command: str) -> tuple[str | None, str | None, list[str]]:
    explicit_interpreter, explicit_script = _explicit_venv_invocation(command)
    path_matches = re.findall(
        rf"(?:^|\s)({REPOSITORY_SCRIPT_PATTERN}|\.?[\\/]?\.venv[\\/](?:Scripts[\\/]python\.exe|bin[\\/]python))",
        command,
        re.IGNORECASE,
    )
    if explicit_script is not None and explicit_script not in path_matches:
        path_matches.append(explicit_script)
    return explicit_interpreter, explicit_script, path_matches


def _check_commands_and_suites(
    root: Path,
    sources: Mapping[str, str],
    suite_ids: set[str],
) -> list[Issue]:
    issues: list[Issue] = []
    for relative, text in sources.items():
        for line_number, command in _command_lines(text):
            normalized = command.removeprefix("PS> ").removeprefix("$ ")
            if normalized.startswith("/") and not normalized.startswith("//"):
                issues.append(Issue("PERSONAL_ABSOLUTE_PATH", relative, f"line {line_number}: command uses a repository-external POSIX absolute path"))
            if re.match(rf"^{GLOBAL_PYTHON_PATTERN}(?:\s|$)", normalized, re.IGNORECASE):
                issues.append(Issue("BARE_PYTHON_COMMAND", relative, f"line {line_number}: host command may fall back to a global interpreter"))
            if re.match(r"^(?:\.\\|\./)?make\.cmd\b", normalized, re.IGNORECASE):
                issues.append(Issue("STALE_COMMAND", relative, f"line {line_number}: archived make.cmd entrypoint is presented as current"))
            if re.match(
                rf"^(?:{ANY_PYTHON_PATTERN}\s+)?(?:\.\\|\./)?C_Semantic_Treehouse[\\/]scripts[\\/]run_all_validations\.py\b",
                normalized,
                re.IGNORECASE,
            ):
                issues.append(Issue("STALE_COMMAND", relative, f"line {line_number}: package-local historical runner is presented as authoritative"))
            if re.search(r"validate\.ps1\s+--suite\b", normalized, re.IGNORECASE):
                issues.append(Issue("WRONG_SUITE_SWITCH", relative, f"line {line_number}: PowerShell wrapper requires -Suite"))
            if re.search(r"validate\.sh\s+-Suite\b", normalized):
                issues.append(Issue("WRONG_SUITE_SWITCH", relative, f"line {line_number}: Linux wrapper requires --suite"))
            linux_switch = re.search(r"validate\.sh\s+(-{1,2}[Ss]uite)\b", normalized)
            if linux_switch and linux_switch.group(1) != "--suite":
                issues.append(Issue("WRONG_SUITE_SWITCH", relative, f"line {line_number}: Linux wrapper requires lowercase --suite"))
            for match in re.finditer(
                r"(?:(?i:-suite)|--suite)\s+(?:[\"']([^\"']+)[\"']|([A-Za-z0-9._-]+))",
                normalized,
            ):
                suite = match.group(1) or match.group(2)
                if suite not in suite_ids:
                    issues.append(Issue("UNKNOWN_SUITE", relative, f"line {line_number}: unknown public suite {suite!r}"))
            explicit_interpreter, explicit_script, path_matches = _command_path_contract(normalized)
            for raw_path in path_matches:
                candidate_text = _normalized_command_path(raw_path)
                if _generated_venv_interpreter(candidate_text, explicit_interpreter, explicit_script):
                    # Repository venvs are generated bootstrap outputs and may
                    # be absent from a clean source tree.  The exemption is
                    # earned only by an invocation whose repo script was parsed;
                    # that script remains in path_matches and is checked below.
                    continue
                candidate = root / candidate_text
                exists, exact_case = _case_sensitive_state(root, candidate)
                if not exists:
                    issues.append(Issue("COMMAND_PATH_MISSING", relative, f"line {line_number}: command path {raw_path!r} does not exist"))
                elif not exact_case:
                    issues.append(Issue("COMMAND_PATH_CASE_MISMATCH", relative, f"line {line_number}: command path case mismatch for {raw_path!r}"))
    return issues


def _check_suite_tables(
    sources: Mapping[str, str],
    suite_ids: set[str],
) -> list[Issue]:
    issues: list[Issue] = []
    expected_order = list(PUBLIC_SUITES)
    root_rows: list[str] | None = None
    for relative, text in sources.items():
        for header, rows, malformed in _table_rows(text):
            keys = [_header_key(item) for item in header]
            if "suite" not in keys:
                continue
            suite_index = keys.index("suite")
            for line_number, _ in malformed:
                issues.append(Issue("SUITE_TABLE_MALFORMED", relative, f"line {line_number}: suite row has a different column count from its header"))
            declared = [row[suite_index] for row in rows]
            for suite in declared:
                if suite not in suite_ids:
                    issues.append(Issue("UNKNOWN_SUITE", relative, f"suite table references unknown public suite {suite!r}"))
            if relative == "README.md":
                if root_rows is not None:
                    issues.append(Issue("SUITE_TABLE_DUPLICATE", relative, "root README contains more than one Suite table"))
                root_rows = declared
    if root_rows is None:
        issues.append(Issue("SUITE_TABLE_MISSING", "README.md", "root README lacks the fixed public Suite table"))
    elif root_rows != expected_order:
        issues.append(Issue("SUITE_TABLE_MISMATCH", "README.md", f"expected public suites {expected_order!r}, actual {root_rows!r}"))
    return issues


def _release_projection(release_manifest: dict[str, Any]) -> tuple[dict[str, dict[str, str]], set[str]]:
    artifacts: dict[str, dict[str, str]] = {}
    all_hashes: set[str] = set()
    for value in _walk_strings(release_manifest):
        if re.fullmatch(r"[0-9a-f]{64}", value):
            all_hashes.add(value)
    for release in release_manifest.get("releases", []):
        version = release.get("id")
        for artifact in release.get("artifacts", []):
            artifact_id = artifact.get("id")
            if isinstance(artifact_id, str):
                artifacts[artifact_id] = {
                    "artifact_id": artifact_id,
                    "version": str(version),
                    "role": str(artifact.get("role")),
                    "path": str(artifact.get("path")),
                    "sha256": str(artifact.get("sha256")),
                }
    return artifacts, all_hashes


def _check_artifacts_and_tables(
    root: Path,
    sources: Mapping[str, str],
    release_manifest: dict[str, Any],
) -> list[Issue]:
    issues: list[Issue] = []
    artifacts, _ = _release_projection(release_manifest)
    known_reference_ids = set(artifacts)
    known_reference_ids.update(
        item.get("id")
        for item in release_manifest.get("sourceCatalog", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    )
    known_reference_ids.update(
        item.get("id")
        for item in release_manifest.get("requirementRegistries", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    )
    expected_v04_artifacts = {
        artifact_id for artifact_id, item in artifacts.items() if item["version"] == "v0.4"
    }
    for relative, text in sources.items():
        for code_token in CODE_SPAN_RE.findall(text):
            artifact_id = code_token.strip()
            if ARTIFACT_ID_RE.fullmatch(artifact_id) and artifact_id not in known_reference_ids:
                issues.append(Issue("UNKNOWN_ARTIFACT", relative, f"unknown release artifact ID {artifact_id!r}"))
        table_count = 0
        projected_artifact_ids: list[str] = []
        for header, rows, malformed in _table_rows(text):
            normalized = [item.lower().replace("-", "_").replace(" ", "_") for item in header]
            required = ("artifact_id", "version", "role", "path", "sha256")
            if not all(item in normalized for item in required):
                continue
            table_count += 1
            for line_number, _ in malformed:
                issues.append(
                    Issue(
                        "ARTIFACT_TABLE_MALFORMED",
                        relative,
                        f"line {line_number}: artifact row has a different column count from its header",
                    )
                )
            if not rows:
                issues.append(Issue("ARTIFACT_TABLE_EMPTY", relative, "artifact projection table has zero rows"))
            positions = {name: normalized.index(name) for name in required}
            for row in rows:
                artifact_id = row[positions["artifact_id"]]
                if artifact_id not in artifacts:
                    issues.append(Issue("UNKNOWN_ARTIFACT", relative, f"artifact table references {artifact_id!r}"))
                    continue
                projected_artifact_ids.append(artifact_id)
                expected = artifacts[artifact_id]
                for column in required:
                    actual = row[positions[column]]
                    if actual != expected[column]:
                        issues.append(Issue("ARTIFACT_MISMATCH", relative, f"{artifact_id} {column}: expected {expected[column]!r}, actual {actual!r}"))
                artifact_path = root / expected["path"]
                if not artifact_path.is_file():
                    issues.append(Issue("ARTIFACT_PATH_MISSING", relative, f"{artifact_id} path is absent"))
                elif _sha256(artifact_path) != expected["sha256"]:
                    issues.append(Issue("ARTIFACT_HASH_MISMATCH", relative, f"{artifact_id} bytes differ from release manifest"))
        if relative in CORE_REPORT_PATHS and table_count == 0:
            issues.append(Issue("ARTIFACT_TABLE_MISSING", relative, "core report lacks the manifest-projection artifact table"))
        if relative in CORE_REPORT_PATHS:
            if set(projected_artifact_ids) != expected_v04_artifacts or len(projected_artifact_ids) != len(expected_v04_artifacts):
                missing = sorted(expected_v04_artifacts - set(projected_artifact_ids))
                extra = sorted(set(projected_artifact_ids) - expected_v04_artifacts)
                issues.append(
                    Issue(
                        "ARTIFACT_TABLE_INCOMPLETE",
                        relative,
                        "core report must project every v0.4 release artifact exactly once; "
                        f"rows={len(projected_artifact_ids)}, missing={missing}, extra={extra}",
                    )
                )
    return issues


def _header_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _normalized_repository_path(value: str) -> str | None:
    normalized = value.strip().replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.rstrip("/")
    parts = normalized.split("/")
    if (
        not normalized
        or normalized.startswith("/")
        or WINDOWS_ABSOLUTE_RE.match(normalized)
        or any(part in {"", ".", ".."} for part in parts)
    ):
        return None
    return normalized


def _manifest_id_bindings(root: Path) -> dict[str, tuple[str, str]]:
    release = _load_json(root / "C_Semantic_Treehouse/manifests/release-manifest.json")
    bindings: dict[str, tuple[str, str]] = {}

    def add(item: Any) -> None:
        if not isinstance(item, dict):
            return
        identifier = item.get("id")
        path = item.get("path")
        digest = item.get("sha256")
        if all(isinstance(value, str) for value in (identifier, path, digest)):
            bindings[identifier] = (path, digest.lower())

    for item in release.get("sourceCatalog", []):
        add(item)
    for item in release.get("requirementRegistries", []):
        add(item)
    for release_record in release.get("releases", []):
        for item in release_record.get("artifacts", []):
            add(item)
    return bindings


def _check_path_hash_bindings(root: Path, sources: Mapping[str, str]) -> list[Issue]:
    """Verify every table row that declares both a repository path and SHA-256."""

    issues: list[Issue] = []
    id_bindings = _manifest_id_bindings(root)
    observed_tables: dict[tuple[str, tuple[str, ...]], list[list[list[str]]]] = {}
    repository_prefixes = ("C_Semantic_Treehouse/", "docs/", "scripts/", "inputs/", "build/")
    for relative, text in sources.items():
        for header, rows, malformed in _table_rows(text):
            keys = [_header_key(item) for item in header]
            header_signature = tuple(keys)
            observed_tables.setdefault((relative, header_signature), []).append(rows)
            path_positions = [index for index, key in enumerate(keys) if key == "path" or key.endswith("_path")]
            hash_positions = [index for index, key in enumerate(keys) if "sha256" in key or "sha_256" in key or key == "hash"]
            if not path_positions or not hash_positions:
                continue
            for line_number, _ in malformed:
                issues.append(
                    Issue(
                        "PATH_HASH_TABLE_MALFORMED",
                        relative,
                        f"line {line_number}: hash-bound row has a different column count from its header",
                    )
                )
            path_index = path_positions[0]
            hash_index = hash_positions[0]
            id_positions = [
                index
                for index, key in enumerate(keys)
                if key == "id" or key.endswith("_id") or "artifact_id" in key or "manifest_id" in key
            ]
            for row in rows:
                raw_path = row[path_index]
                declared_path = _normalized_repository_path(raw_path)
                if declared_path is None:
                    issues.append(Issue("PATH_HASH_PATH_INVALID", relative, f"hash-bound table path {raw_path!r} is not a normalized repository-relative path"))
                    continue
                if not declared_path.startswith(repository_prefixes):
                    issues.append(Issue("PATH_HASH_PATH_INVALID", relative, f"hash-bound table path {declared_path!r} is not repository-relative"))
                    continue
                path = root / declared_path
                declared_hashes = [item.lower() for item in HASH_RE.findall(row[hash_index])]
                if path.is_dir() and not declared_hashes:
                    # A directory row can truthfully delegate byte binding to a
                    # manifest scope; file rows must carry exactly one digest.
                    continue
                if not path.is_file():
                    issues.append(Issue("PATH_HASH_PATH_MISSING", relative, f"hash-bound table path {declared_path!r} is absent"))
                    continue
                if len(declared_hashes) != 1:
                    issues.append(
                        Issue(
                            "PATH_HASH_VALUE_INVALID",
                            relative,
                            f"{declared_path}: file row must declare exactly one SHA-256; actual={len(declared_hashes)}",
                        )
                    )
                    continue
                declared_hash = declared_hashes[0]
                actual_hash = _sha256(path)
                if actual_hash != declared_hash:
                    issues.append(Issue("PATH_HASH_MISMATCH", relative, f"{declared_path}: expected current SHA-256 {actual_hash}, documented {declared_hash}"))
                if id_positions:
                    identifier = row[id_positions[0]]
                    looks_machine_id = re.fullmatch(r"[a-z0-9][a-z0-9.-]*(?:-[a-z0-9][a-z0-9.-]*)+", identifier)
                    if looks_machine_id and identifier not in id_bindings:
                        issues.append(Issue("PATH_HASH_ID_UNKNOWN", relative, f"hash-bound table references unknown manifest ID {identifier!r}"))
                    elif identifier in id_bindings:
                        expected_path, expected_hash = id_bindings[identifier]
                        if (declared_path, declared_hash) != (expected_path, expected_hash):
                            issues.append(
                                Issue(
                                    "PATH_HASH_ID_MISMATCH",
                                    relative,
                                    f"{identifier}: expected ({expected_path}, {expected_hash}), documented ({declared_path}, {declared_hash})",
                                )
                            )
    for relative, specs in BINDING_TABLE_SPECS.items():
        if relative not in sources:
            continue
        for spec in specs:
            signature = tuple(spec["headers"])
            matches = observed_tables.get((relative, signature), [])
            if len(matches) != 1:
                issues.append(
                    Issue(
                        "BINDING_TABLE_COUNT",
                        relative,
                        f"required binding table {signature!r} must appear exactly once; actual={len(matches)}",
                    )
                )
                continue
            path_index = next(
                index
                for index, key in enumerate(signature)
                if key == "path" or key.endswith("_path")
            )
            declared_paths = [
                _normalized_repository_path(row[path_index])
                for row in matches[0]
            ]
            expected_paths = list(spec["paths"])
            if declared_paths != expected_paths:
                issues.append(
                    Issue(
                        "BINDING_TABLE_ROWS",
                        relative,
                        f"required binding paths/order differ: expected={expected_paths!r}, actual={declared_paths!r}",
                    )
                )
    return issues


def _check_inline_path_hash_bindings(
    root: Path,
    sources: Mapping[str, str],
) -> list[Issue]:
    """Bind prose/table lines that co-declare repository paths and digests."""

    issues: list[Issue] = []
    valid_required: dict[str, set[str]] = {relative: set() for relative in REQUIRED_INLINE_BINDINGS}
    prefixes = ("C_Semantic_Treehouse/", "docs/", "scripts/", "inputs/", "build/")
    for relative, text in sources.items():
        for line_number, line in enumerate(text.splitlines(), start=1):
            hashes = [item.lower() for item in HASH_RE.findall(line)]
            path_tokens: list[str] = []
            for token in CODE_SPAN_RE.findall(line):
                normalized = _normalized_repository_path(token)
                if normalized is not None and normalized.startswith(prefixes):
                    path_tokens.append(normalized)
            file_paths = [item for item in path_tokens if (root / item).is_file()]
            if not file_paths or not hashes:
                continue
            actual_hashes = [_sha256(root / item) for item in file_paths]
            if len(file_paths) == 1:
                if len(hashes) != 1 or hashes[0] != actual_hashes[0]:
                    issues.append(
                        Issue(
                            "INLINE_PATH_HASH_MISMATCH",
                            relative,
                            f"line {line_number}: {file_paths[0]} requires exactly its current SHA-256 {actual_hashes[0]}; documented={hashes!r}",
                        )
                    )
                else:
                    valid_required.setdefault(relative, set()).add(file_paths[0])
            else:
                if len(hashes) != len(set(actual_hashes)) or set(hashes) != set(actual_hashes):
                    issues.append(
                        Issue(
                            "INLINE_PATH_HASH_MISMATCH",
                            relative,
                            f"line {line_number}: path/hash set mismatch; paths={file_paths!r}, documented={hashes!r}",
                        )
                    )
                else:
                    valid_required.setdefault(relative, set()).update(file_paths)
    for relative, required_paths in REQUIRED_INLINE_BINDINGS.items():
        if relative not in sources:
            continue
        missing = sorted(set(required_paths) - valid_required.get(relative, set()))
        if missing:
            issues.append(
                Issue(
                    "INLINE_PATH_HASH_REQUIRED",
                    relative,
                    f"required same-line path/SHA-256 bindings are missing or invalid: {missing!r}",
                )
            )
    return issues


def _context_json_keys(root: Path) -> dict[str, str]:
    context = _load_json(root / "C_Semantic_Treehouse/model/v0.4/data-product-context.jsonld")["@context"]
    mapping: dict[str, str] = {}
    for key, value in context.items():
        iri = value.get("@id") if isinstance(value, dict) else value
        if isinstance(iri, str) and ":" in iri and key not in {"ex", "dcat", "dct", "xsd", "Dataset"}:
            mapping[iri] = key
    return mapping


def _expected_field_rows(root: Path, requirements: dict[str, Any]) -> dict[str, dict[str, str]]:
    json_keys = _context_json_keys(root)
    rows: dict[str, dict[str, str]] = {}
    excluded = {"D04-R001", "D04-R002", "D04-R013", "D04-R016", "D04-R017"}
    for requirement in requirements.get("requirements", []):
        requirement_id = requirement.get("id")
        if requirement_id in excluded:
            continue
        locator = requirement.get("sources", [{}])[0].get("locator", {})
        iri = locator.get("path")
        constraints = locator.get("constraints", [])
        constraint_values: dict[str, Any] = {}
        for item in constraints:
            if not isinstance(item, dict):
                continue
            value = item.get("value", {})
            extracted = value.get("value")
            if extracted is None and isinstance(value.get("items"), list) and value["items"]:
                extracted = value["items"][0].get("value")
            constraint_values[str(item.get("predicate"))] = extracted
        minimum = constraint_values.get("sh:minCount")
        maximum = constraint_values.get("sh:maxCount")
        datatype = constraint_values.get("sh:datatype") or constraint_values.get("sh:nodeKind")
        allowed = constraint_values.get("sh:in") or constraint_values.get("sh:pattern") or ""
        rows[str(requirement_id)] = {
            "required": "true" if minimum == 1 else "false",
            "iri": str(iri),
            "json_key": json_keys.get(str(iri), ""),
            "datatype": str(datatype),
            "cardinality": "1..1" if minimum == 1 and maximum == 1 else "0..1",
            "allowed": str(allowed),
        }
    return rows


def _check_field_table(
    root: Path,
    sources: Mapping[str, str],
    requirements: dict[str, Any],
) -> list[Issue]:
    relative = "C_Semantic_Treehouse/handoff/handoff-to-A-offering-metadata.md"
    text = sources.get(relative, "")
    expected_rows = _expected_field_rows(root, requirements)
    found: dict[str, int] = {}
    issues: list[Issue] = []
    required_headers = {
        "requirement_id",
        "required",
        "iri",
        "json_key",
        "datatype_/_node_kind",
        "cardinality",
        "allowed_value",
    }
    temporal_rule_count = 0
    for header, rows, malformed in _table_rows(text):
        normalized = [item.lower().replace(" ", "_") for item in header]
        if required_headers.issubset(set(normalized)):
            for line_number, _ in malformed:
                issues.append(
                    Issue(
                        "FIELD_TABLE_MALFORMED",
                        relative,
                        f"line {line_number}: field row has a different column count from its header",
                    )
                )
            positions = {name: normalized.index(name) for name in required_headers}
            for row in rows:
                requirement_id = row[positions["requirement_id"]]
                if requirement_id not in expected_rows:
                    issues.append(
                        Issue(
                            "FIELD_UNKNOWN_REQUIREMENT",
                            relative,
                            f"field table references unexpected requirement {requirement_id!r}",
                        )
                    )
                    continue
                found[requirement_id] = found.get(requirement_id, 0) + 1
                expected = expected_rows[requirement_id]
                actual = {
                    "required": row[positions["required"]].lower(),
                    "iri": row[positions["iri"]],
                    "json_key": row[positions["json_key"]],
                    "datatype": row[positions["datatype_/_node_kind"]],
                    "cardinality": row[positions["cardinality"]],
                    "allowed": row[positions["allowed_value"]],
                }
                for key in ("required", "iri", "json_key", "datatype", "cardinality"):
                    if actual[key] != expected[key]:
                        issues.append(Issue("FIELD_MISMATCH", relative, f"{requirement_id} {key}: expected {expected[key]!r}, actual {actual[key]!r}"))
                expected_allowed = EXPECTED_FIELD_ALLOWED[requirement_id]
                if actual["allowed"] != expected_allowed:
                    issues.append(
                        Issue(
                            "FIELD_MISMATCH",
                            relative,
                            f"{requirement_id} allowed value: expected {expected_allowed!r}, actual {actual['allowed']!r}",
                        )
                    )
            continue
        if {"requirement_id", "fields", "rule"}.issubset(set(normalized)):
            positions = {name: normalized.index(name) for name in ("requirement_id", "fields", "rule")}
            for row in rows:
                if row[positions["requirement_id"]] != "D04-R013":
                    continue
                temporal_rule_count += 1
                fields = row[positions["fields"]]
                rule = row[positions["rule"]]
                if not all(field in fields for field in ("temporalStart", "temporalEnd")):
                    issues.append(Issue("FIELD_MISMATCH", relative, "D04-R013 must bind temporalStart and temporalEnd"))
                if "xsd:date" not in rule or "≤" not in rule:
                    issues.append(Issue("FIELD_MISMATCH", relative, "D04-R013 must state xsd:date temporalStart ≤ temporalEnd"))
    for requirement_id in sorted(expected_rows):
        count = found.get(requirement_id, 0)
        if count != 1:
            issues.append(Issue("FIELD_ROW_COUNT", relative, f"{requirement_id} must appear exactly once in the field table; actual={count}"))
    if temporal_rule_count != 1:
        issues.append(Issue("FIELD_ROW_COUNT", relative, f"D04-R013 must appear exactly once in the cross-field table; actual={temporal_rule_count}"))
    return issues


def _check_case_status_rows(
    sources: Mapping[str, str],
    test_manifest: dict[str, Any],
) -> list[Issue]:
    expected = {case["case_id"]: case["expected_business_status"] for case in test_manifest.get("cases", [])}
    issues: list[Issue] = []
    required_relative = "C_Semantic_Treehouse/C_export_for_validation.md"
    required_signature = ("case_id", "expected_business_status", "scope")
    required_tables: list[list[list[str]]] = []
    for relative, text in sources.items():
        for header, rows, malformed in _table_rows(text):
            keys = [_header_key(item) for item in header]
            if relative == required_relative and tuple(keys) == required_signature:
                required_tables.append(rows)
            case_positions = [index for index, key in enumerate(keys) if key == "case_id"]
            status_positions = [
                index
                for index, key in enumerate(keys)
                if key in {"status", "business_status", "expected_business_status"}
            ]
            if not case_positions or not status_positions:
                continue
            for line_number, _ in malformed:
                issues.append(Issue("STATUS_TABLE_MALFORMED", relative, f"line {line_number}: case-status row has a different column count from its header"))
            case_index = case_positions[0]
            status_index = status_positions[0]
            for row in rows:
                case_id = row[case_index]
                if not CASE_ID_RE.fullmatch(case_id):
                    continue
                status = row[status_index]
                if status not in STATUS_VALUES:
                    issues.append(Issue("STATUS_VALUE_INVALID", relative, f"{case_id} declares invalid business status {status!r}"))
                    continue
                if case_id not in expected:
                    issues.append(Issue("UNKNOWN_TEST_CASE", relative, f"unknown test case {case_id}"))
                elif status != expected[case_id]:
                    issues.append(Issue("STATUS_MISMATCH", relative, f"{case_id} expected {expected[case_id]}, documented {status}"))
    if required_relative in sources:
        if len(required_tables) != 1:
            issues.append(
                Issue(
                    "STATUS_TABLE_COUNT",
                    required_relative,
                    f"required case-status table must appear exactly once; actual={len(required_tables)}",
                )
            )
        else:
            actual_ids = [row[0] for row in required_tables[0]]
            expected_ids = [f"D04-PC{number:03d}" for number in range(59, 67)]
            if actual_ids != expected_ids:
                issues.append(
                    Issue(
                        "STATUS_TABLE_ROWS",
                        required_relative,
                        f"required case-status row set/order differs: expected={expected_ids!r}, actual={actual_ids!r}",
                    )
                )
    return issues


def _check_business_status_counts(
    sources: Mapping[str, str],
    test_manifest: dict[str, Any],
) -> list[Issue]:
    expected = {status: 0 for status in STATUS_VALUES}
    for case in test_manifest.get("cases", []):
        status = case.get("expected_business_status")
        if status in expected:
            expected[status] += 1
    issues: list[Issue] = []
    valid_summaries: dict[str, int] = {relative: 0 for relative in REQUIRED_STATUS_COUNT_PATHS}
    for relative in REQUIRED_STATUS_COUNT_PATHS:
        if relative not in sources:
            continue
        text = sources[relative]
        for line_number, line in enumerate(text.splitlines(), start=1):
            if sum(status in line for status in STATUS_VALUES) < 3 or not re.search(r"\d", line):
                continue
            declared: dict[str, int] = {}
            for status in STATUS_VALUES:
                before = re.search(rf"(?<!\d)(\d+)\s*`?{status}`?", line)
                after = re.search(rf"`?{status}\s*:?\s*(\d+)`?", line)
                match = before or after
                if match:
                    declared[status] = int(match.group(1))
            if not declared:
                continue
            if declared == expected:
                valid_summaries[relative] += 1
            else:
                issues.append(
                    Issue(
                        "STATUS_COUNT_MISMATCH",
                        relative,
                        f"line {line_number}: expected status distribution {expected!r}, documented {declared!r}",
                    )
                )
    for relative in REQUIRED_STATUS_COUNT_PATHS:
        if relative in sources and valid_summaries[relative] != 1:
            issues.append(
                Issue(
                    "STATUS_COUNT_SUMMARY_COUNT",
                    relative,
                    f"manifest-derived four-status summary must appear exactly once; actual={valid_summaries[relative]}",
                )
            )
    return issues


def _known_hashes(root: Path, release_manifest: dict[str, Any]) -> set[str]:
    _, known = _release_projection(release_manifest)
    known.add(TREEHOUSE_SHACL_VALIDATOR_MANIFEST_DIGEST.removeprefix("sha256:"))
    for relative in AUTHORITY_JSON_PATHS:
        path = root / relative
        if not path.is_file():
            continue
        try:
            value = _load_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        for text in _walk_strings(value):
            if re.fullmatch(r"[0-9a-f]{64}", text):
                known.add(text)
        known.add(_sha256(path))
    for relative, _ in SOURCE_PATHS:
        path = root / relative
        if path.is_file():
            known.add(_sha256(path))
    for relative in (
        "requirements.lock",
        "C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json",
        "inputs/d-group/v0.4/received/building-energy-shapes_D.ttl",
    ):
        path = root / relative
        if path.is_file():
            known.add(_sha256(path))
    return known


def _check_hash_declarations(
    root: Path,
    sources: Mapping[str, str],
    release_manifest: dict[str, Any],
) -> list[Issue]:
    known = _known_hashes(root, release_manifest)
    issues: list[Issue] = []
    for relative, text in sources.items():
        for declared in HASH_RE.findall(text):
            if declared.lower() not in known:
                issues.append(Issue("HASH_MISMATCH", relative, f"declared SHA-256 {declared.lower()} is not bound to a current authority, artifact, result, or checker source"))
    return issues


def _check_repository_references(root: Path, sources: Mapping[str, str]) -> list[Issue]:
    issues: list[Issue] = []
    prefixes = ("C_Semantic_Treehouse/", "docs/", "scripts/", "inputs/", "build/")
    for relative, text in sources.items():
        scan_text = MARKDOWN_LINK_RE.sub("", text)
        scan_text = REFERENCE_LINK_RE.sub("", scan_text)
        for token in CODE_SPAN_RE.findall(scan_text):
            raw = token.strip().replace("\\", "/")
            if ".." in raw.split("/"):
                issues.append(Issue("REFERENCE_PATH_ESCAPE", relative, f"referenced repository path {raw!r} contains parent traversal"))
                continue
            normalized = _normalized_repository_path(raw)
            if normalized is None:
                continue
            if not normalized.startswith(prefixes):
                continue
            if any(symbol in normalized for symbol in ("{", "}", "*", "|", "<", ">")) or " " in normalized:
                continue
            normalized = normalized.rstrip(".,;:")
            candidate = root / normalized
            exists, exact_case = _case_sensitive_state(root, candidate)
            if not exists:
                if normalized in GENERATED_OUTPUT_PATHS:
                    continue
                issues.append(Issue("REFERENCE_PATH_MISSING", relative, f"referenced repository path {normalized!r} is absent"))
            elif not exact_case:
                issues.append(Issue("REFERENCE_PATH_CASE_MISMATCH", relative, f"referenced repository path {normalized!r} has incorrect case"))
    return issues


def _markdown_level_two_sections(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, list[str]]] = []
    title = "<preamble>"
    lines: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^##(?!#)\s+(.+?)\s*$", line)
        if match:
            sections.append((title, lines))
            title = match.group(1)
            lines = []
        else:
            lines.append(line)
    sections.append((title, lines))
    return [(heading, "\n".join(body)) for heading, body in sections]


def _publication_table_rows(text: str) -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    for line in text.splitlines():
        cells = _split_table_row(line)
        if len(cells) < 2 or not cells[0] or set(cells[0]) <= {"-", ":"}:
            continue
        rows.setdefault(cells[0], []).append(cells[1])
    return rows


def _publication_value(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("`", "").strip())


def _publication_unique_row(
    rows: Mapping[str, list[str]],
    aliases: Sequence[str],
    *,
    section_title: str,
    display_label: str,
    issues: list[Issue],
) -> str:
    matches = [
        (label, value)
        for label in aliases
        for value in rows.get(label, [])
    ]
    if len(matches) != 1:
        issues.append(
            Issue(
                "REPOSITORY_PUBLICATION_EVIDENCE",
                PUBLICATION_RECORD_PATH,
                f"section {section_title!r} requires exactly one {display_label!r} row; found {len(matches)}",
            )
        )
        return ""
    return matches[0][1]


def _validate_publication_candidate(
    section_title: str,
    section_text: str,
    *,
    clone_url: str,
) -> tuple[dict[str, Any], list[Issue]]:
    rows = _publication_table_rows(section_text)
    issues: list[Issue] = []
    candidate_sha = _publication_unique_row(
        rows,
        ("候选 commit SHA",),
        section_title=section_title,
        display_label="候选 commit SHA",
        issues=issues,
    )
    push = _publication_unique_row(
        rows,
        ("Push",),
        section_title=section_title,
        display_label="Push",
        issues=issues,
    )
    run_id = _publication_unique_row(
        rows,
        ("Actions run ID",),
        section_title=section_title,
        display_label="Actions run ID",
        issues=issues,
    )
    run_url = _publication_unique_row(
        rows,
        ("Actions run URL",),
        section_title=section_title,
        display_label="Actions run URL",
        issues=issues,
    )
    run_head_sha = _publication_unique_row(
        rows,
        ("Run `head_sha`", "Run event / `head_sha`"),
        section_title=section_title,
        display_label="Run head_sha",
        issues=issues,
    )
    resolved_sha = _publication_unique_row(
        rows,
        ("Resolved SHA", "Remote clean-clone resolved SHA"),
        section_title=section_title,
        display_label="remote clean-clone resolved SHA",
        issues=issues,
    )

    candidate_sha = _publication_value(candidate_sha)
    run_id = _publication_value(run_id)
    run_url = _publication_value(run_url).strip("<>")
    run_head_value = _publication_value(run_head_sha)
    run_head_match = re.fullmatch(
        r"(?:push\s*/\s*)?([0-9a-f]{40})",
        run_head_value,
        re.IGNORECASE,
    )
    run_head_sha = run_head_match.group(1) if run_head_match else run_head_value
    resolved_sha = _publication_value(resolved_sha)

    for label, value in {
        "候选 commit SHA": candidate_sha,
        "Run head_sha": run_head_sha,
        "Resolved SHA": resolved_sha,
    }.items():
        if value and not re.fullmatch(r"[0-9a-f]{40}", value, re.IGNORECASE):
            issues.append(
                Issue(
                    "REPOSITORY_PUBLICATION_EVIDENCE",
                    PUBLICATION_RECORD_PATH,
                    f"section {section_title!r} {label} must be one full 40-hex commit SHA; actual={value!r}",
                )
            )
    sha_equal = bool(
        candidate_sha
        and candidate_sha.casefold() == run_head_sha.casefold()
        and candidate_sha.casefold() == resolved_sha.casefold()
    )
    if candidate_sha and not sha_equal:
        issues.append(
            Issue(
                "REPOSITORY_PUBLICATION_EVIDENCE",
                PUBLICATION_RECORD_PATH,
                f"section {section_title!r} candidate SHA, Actions head_sha and remote-clone resolved SHA must be identical",
            )
        )

    normalized_push = _publication_value(push)
    allowed_push_values = {
        "普通 push main（无 force）",
        "普通 git push -u origin main（无 force）",
    }
    push_pass = normalized_push in allowed_push_values
    if push and not push_pass:
        issues.append(
            Issue(
                "REPOSITORY_PUBLICATION_EVIDENCE",
                PUBLICATION_RECORD_PATH,
                f"section {section_title!r} Push row must be an approved ordinary main push without force; actual={push!r}",
            )
        )

    run_url_match = re.fullmatch(
        r"https://github\.com/Daydreaming24/DSSC_Toolbox_Group-C/actions/runs/(\d+)",
        run_url,
    )
    run_binding_pass = bool(run_id.isdigit() and run_url_match)
    if not run_id.isdigit():
        issues.append(
            Issue(
                "REPOSITORY_PUBLICATION_EVIDENCE",
                PUBLICATION_RECORD_PATH,
                f"section {section_title!r} Actions run ID must be numeric; actual={run_id!r}",
            )
        )
    if not run_url_match:
        issues.append(
            Issue(
                "REPOSITORY_PUBLICATION_EVIDENCE",
                PUBLICATION_RECORD_PATH,
                f"section {section_title!r} Actions run URL is outside the canonical repository or malformed: {run_url!r}",
            )
        )
    elif run_id and run_url_match.group(1) != run_id:
        run_binding_pass = False
        issues.append(
            Issue(
                "REPOSITORY_PUBLICATION_EVIDENCE",
                PUBLICATION_RECORD_PATH,
                f"section {section_title!r} Actions run ID {run_id!r} does not match URL run ID {run_url_match.group(1)!r}",
            )
        )

    combined_jobs = rows.get("Ubuntu / Windows / Docker job", [])
    separate_jobs = {
        "ubuntu": rows.get("Ubuntu job", []),
        "windows": rows.get("Windows job", []),
        "docker": rows.get("Docker job", []),
    }
    job_values: dict[str, str] = {key: "" for key in separate_jobs}
    if combined_jobs and any(separate_jobs.values()):
        issues.append(
            Issue(
                "REPOSITORY_PUBLICATION_EVIDENCE",
                PUBLICATION_RECORD_PATH,
                f"section {section_title!r} must use either combined or separate job rows, not both",
            )
        )
    if combined_jobs:
        if len(combined_jobs) != 1:
            issues.append(
                Issue(
                    "REPOSITORY_PUBLICATION_EVIDENCE",
                    PUBLICATION_RECORD_PATH,
                    f"section {section_title!r} requires exactly one combined job row; found {len(combined_jobs)}",
                )
            )
        combined = _publication_value(combined_jobs[0])
        if combined == "success / success / success":
            job_values = {key: "success" for key in separate_jobs}
        else:
            issues.append(
                Issue(
                    "REPOSITORY_PUBLICATION_EVIDENCE",
                    PUBLICATION_RECORD_PATH,
                    f"section {section_title!r} combined Ubuntu/Windows/Docker row must equal 'success / success / success'; actual={combined!r}",
                )
            )
    else:
        for job, values in separate_jobs.items():
            if len(values) != 1:
                issues.append(
                    Issue(
                        "REPOSITORY_PUBLICATION_EVIDENCE",
                        PUBLICATION_RECORD_PATH,
                        f"section {section_title!r} requires exactly one {job} job row; found {len(values)}",
                    )
                )
                continue
            job_values[job] = _publication_value(values[0]).casefold()
            if job_values[job] != "success":
                issues.append(
                    Issue(
                        "REPOSITORY_PUBLICATION_EVIDENCE",
                        PUBLICATION_RECORD_PATH,
                        f"section {section_title!r} required GitHub Actions {job} job must equal success; actual={values[0]!r}",
                    )
                )
    ci_jobs_pass = all(value == "success" for value in job_values.values())

    combined_clone = rows.get("Remote clone 一键复现 / Phase 09 三 checker", [])
    separate_clone = {
        "reproduce": rows.get("一键复现", []),
        "phase09_checkers": rows.get("Phase 09 三 checker", []),
    }
    clone_values = {key: "" for key in separate_clone}
    if combined_clone and any(separate_clone.values()):
        issues.append(
            Issue(
                "REPOSITORY_PUBLICATION_EVIDENCE",
                PUBLICATION_RECORD_PATH,
                f"section {section_title!r} must use either combined or separate remote-clone result rows, not both",
            )
        )
    if combined_clone:
        if len(combined_clone) != 1:
            issues.append(
                Issue(
                    "REPOSITORY_PUBLICATION_EVIDENCE",
                    PUBLICATION_RECORD_PATH,
                    f"section {section_title!r} requires exactly one combined remote-clone row; found {len(combined_clone)}",
                )
            )
        combined = _publication_value(combined_clone[0]).casefold()
        if combined == "exit 0 / exit 0":
            clone_values = {key: "exit 0" for key in separate_clone}
        else:
            issues.append(
                Issue(
                    "REPOSITORY_PUBLICATION_EVIDENCE",
                    PUBLICATION_RECORD_PATH,
                    f"section {section_title!r} combined remote-clone row must equal 'exit 0 / exit 0'; actual={combined!r}",
                )
            )
    else:
        for check, values in separate_clone.items():
            if len(values) != 1:
                issues.append(
                    Issue(
                        "REPOSITORY_PUBLICATION_EVIDENCE",
                        PUBLICATION_RECORD_PATH,
                        f"section {section_title!r} requires exactly one remote-clone {check} row; found {len(values)}",
                    )
                )
                continue
            clone_values[check] = _publication_value(values[0]).casefold()
            if clone_values[check] != "exit 0":
                issues.append(
                    Issue(
                        "REPOSITORY_PUBLICATION_EVIDENCE",
                        PUBLICATION_RECORD_PATH,
                        f"section {section_title!r} remote-clone {check} must equal exit 0; actual={values[0]!r}",
                    )
                )
    clone_checks_pass = all(value == "exit 0" for value in clone_values.values())

    repository_publication_pass = bool(push_pass and clone_url == CANONICAL_REPOSITORY_URL)
    ci_pass = bool(run_binding_pass and sha_equal and ci_jobs_pass)
    remote_clone_pass = bool(sha_equal and clone_checks_pass)
    return {
        "section": section_title,
        "status": "PASS" if not issues else "FAIL",
        "candidate_sha": candidate_sha,
        "repository_publication": "PASS" if repository_publication_pass else "FAIL",
        "github_actions": {
            "status": "PASS" if ci_pass else "FAIL",
            "run_id": run_id,
            "run_url": run_url,
            "head_sha": run_head_sha,
            "jobs": job_values,
        },
        "remote_clean_clone": {
            "status": "PASS" if remote_clone_pass else "FAIL",
            "resolved_sha": resolved_sha,
            "reproduce": clone_values["reproduce"],
            "phase09_checkers": clone_values["phase09_checkers"],
        },
    }, issues


def _check_repository_publication(
    sources: Mapping[str, str],
) -> tuple[dict[str, Any], list[Issue]]:
    """Separate the last confirmed candidate from the current candidate state."""

    text = sources.get(PUBLICATION_RECORD_PATH, "")
    sections = _markdown_level_two_sections(text)
    issues: list[Issue] = []

    stable_sections = [(title, body) for title, body in sections if "稳定目标" in title]
    if len(stable_sections) != 1:
        issues.append(
            Issue(
                "REPOSITORY_PUBLICATION_EVIDENCE",
                PUBLICATION_RECORD_PATH,
                f"publication record requires exactly one stable-target section; found {len(stable_sections)}",
            )
        )
        clone_url = ""
        stable_rows: dict[str, list[str]] = {}
    else:
        stable_title, stable_text = stable_sections[0]
        stable_rows = _publication_table_rows(stable_text)
        clone_url = _publication_unique_row(
            stable_rows,
            ("Clone URL",),
            section_title=stable_title,
            display_label="Clone URL",
            issues=issues,
        )
        clone_url = _publication_value(clone_url)
        if clone_url != CANONICAL_REPOSITORY_URL:
            issues.append(
                Issue(
                    "REPOSITORY_PUBLICATION_EVIDENCE",
                    PUBLICATION_RECORD_PATH,
                    f"Clone URL {clone_url!r} does not equal canonical {CANONICAL_REPOSITORY_URL!r}",
                )
            )

    historical_sections = [
        (title, body)
        for title, body in sections
        if "上一次已确认候选" in title or "历史已确认候选" in title
    ]
    if len(historical_sections) != 1:
        issues.append(
            Issue(
                "REPOSITORY_PUBLICATION_EVIDENCE",
                PUBLICATION_RECORD_PATH,
                f"publication record requires exactly one historical confirmed-candidate section; found {len(historical_sections)}",
            )
        )
        historical = {"status": "FAIL"}
    else:
        historical, historical_issues = _validate_publication_candidate(
            historical_sections[0][0],
            historical_sections[0][1],
            clone_url=clone_url,
        )
        issues.extend(historical_issues)

    current_sections = [
        (title, body)
        for title, body in sections
        if "审计恢复" in title or "当前同步候选" in title or "新候选" in title
    ]
    if len(current_sections) != 1:
        issues.append(
            Issue(
                "REPOSITORY_PUBLICATION_EVIDENCE",
                PUBLICATION_RECORD_PATH,
                f"publication record requires exactly one current-candidate section; found {len(current_sections)}",
            )
        )
        current: dict[str, Any] = {"status": "UNKNOWN"}
    else:
        current_title, current_text = current_sections[0]
        current_rows = _publication_table_rows(current_text)
        candidate_labels = {
            "候选 commit SHA",
            "Push",
            "Actions run ID",
            "Actions run URL",
            "Run `head_sha`",
            "Run event / `head_sha`",
            "Ubuntu / Windows / Docker job",
            "Ubuntu job",
            "Windows job",
            "Docker job",
            "Resolved SHA",
            "Remote clean-clone resolved SHA",
            "Remote clone 一键复现 / Phase 09 三 checker",
            "一键复现",
            "Phase 09 三 checker",
        }
        has_candidate_rows = any(label in current_rows for label in candidate_labels)
        if has_candidate_rows:
            current, current_issues = _validate_publication_candidate(
                current_title,
                current_text,
                clone_url=clone_url,
            )
            issues.extend(current_issues)
        else:
            pending_marker = re.search(
                r"(?:必须重新执行|旧[^\n。；]*不作为新候选证据|尚未[^\n。；]*候选|候选提交尚未形成)",
                current_text,
                re.IGNORECASE,
            )
            if not pending_marker:
                issues.append(
                    Issue(
                        "REPOSITORY_PUBLICATION_EVIDENCE",
                        PUBLICATION_RECORD_PATH,
                        f"section {current_title!r} has no current candidate binding and no explicit pending boundary",
                    )
                )
            current = {
                "section": current_title,
                "status": "PENDING",
                "reason": "new candidate binding is not yet recorded",
                "repository_publication": "PENDING",
                "github_actions": {"status": "PENDING"},
                "remote_clean_clone": {"status": "PENDING"},
            }

    return {
        "record_path": PUBLICATION_RECORD_PATH,
        "canonical_clone_url": clone_url,
        "last_confirmed_candidate": historical,
        "current_candidate": current,
        "tag": (stable_rows.get("Tag") or [None])[0],
        "github_release": (stable_rows.get("GitHub Release") or [None])[0],
    }, issues


def _check_final_navigation_statuses(sources: Mapping[str, str]) -> list[Issue]:
    """Reject the pre-publication Phase 09 navigation projection."""

    issues: list[Issue] = []
    phase_regression = re.compile(r"Phase\s*09.*?\bIN_PROGRESS\b", re.IGNORECASE | re.DOTALL)
    publication_regression = re.compile(
        r"(?:GitHub\s+(?:Actions|CI|run|publication|发布|公开\s*push)|"
        r"(?:remote|远程)\s+clean\s+clone|repository\s+publication)"
        r".*?\bNOT\s+RUN\b",
        re.IGNORECASE | re.DOTALL,
    )

    def logical_blocks(text: str) -> Iterable[tuple[int, str]]:
        """Keep wrapped prose together while isolating pipe-table rows."""

        start = 1
        buffer: list[str] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip() or line.lstrip().startswith("|"):
                if buffer:
                    yield start, "\n".join(buffer)
                    buffer = []
                if line.lstrip().startswith("|"):
                    yield line_number, line
                start = line_number + 1
                continue
            if not buffer:
                start = line_number
            buffer.append(line)
        if buffer:
            yield start, "\n".join(buffer)

    for relative in FINAL_NAVIGATION_PATHS:
        text = sources.get(relative, "")
        for line_number, block in logical_blocks(text):
            for sentence in re.split(r"(?<=[。；;])\s*", block):
                current_revalidation_boundary = (
                    re.search(r"(?:本轮|当前)[^。；;]*候选", sentence)
                    and re.search(r"重新(?:完成|执行)", sentence)
                )
                if phase_regression.search(sentence) and not current_revalidation_boundary:
                    issues.append(
                        Issue(
                            "FINAL_NAVIGATION_PHASE09_REGRESSION",
                            relative,
                            f"line {line_number}: final navigation regressed Phase 09 to IN_PROGRESS",
                        )
                    )
                if publication_regression.search(sentence):
                    issues.append(
                        Issue(
                            "FINAL_NAVIGATION_PUBLICATION_REGRESSION",
                            relative,
                            f"line {line_number}: completed GitHub CI/repository publication or remote clean clone regressed to NOT RUN",
                        )
                    )
    return issues


def _check_truthful_statuses(sources: Mapping[str, str]) -> list[Issue]:
    issues: list[Issue] = []
    invalid = re.compile(
        r"(?:NOT RUN|PARTIAL)\s*(?:(?:->|→|=>|=|:|/)\s*|(?:and|but)\s+)"
        r"(?:DONE|PASS|SUCCESS|COMPLETE|completed(?:\s+successfully)?|succeeded)",
        re.IGNORECASE,
    )
    historical_upgrade = re.compile(
        r"(?:historical|历史).*(?:->|→|=>).*(?:current|当前).*(?:DONE|PASS|SUCCESS|COMPLETE)",
        re.IGNORECASE,
    )
    external_terms = ("semantic treehouse", "semic", "itb", "mermaid parser", "mermaid renderer")
    completion = re.compile(r"\b(?:DONE|COMPLETE|PASS|SUCCESS)\b|\bRUN\s*/\s*PASS\b", re.IGNORECASE)
    for relative, text in sources.items():
        for line_number, line in enumerate(text.splitlines(), start=1):
            if invalid.search(line) or historical_upgrade.search(line):
                issues.append(Issue("FALSE_COMPLETION_STATUS", relative, f"line {line_number}: incomplete, optional, or historical evidence is summarized as complete"))
            lowered = line.lower()
            cells = _split_table_row(line)
            approved_treehouse_stage = (
                relative == TREEHOUSE_USAGE_PATH
                and len(cells) >= 2
                and any(
                    cells[0].casefold() == label.casefold()
                    and cells[1] == expected_status
                    and expected_status in {"PASS", "APPROVED"}
                    for label, expected_status in HISTORICAL_TREEHOUSE_STATUS_RULES
                )
            )
            if (
                any(term in lowered for term in external_terms)
                and completion.search(line)
                and "NOT RUN" not in line.upper()
                and "historical" not in lowered
                and "历史" not in line
                and not approved_treehouse_stage
            ):
                issues.append(Issue("FALSE_COMPLETION_STATUS", relative, f"line {line_number}: current external evidence is declared complete without a run"))
    for relative, labels in CURRENT_NOT_RUN_RULES.items():
        lines = sources.get(relative, "").splitlines()
        for label in labels:
            matching = [line for line in lines if label.casefold() in line.casefold()]
            valid = False
            for line in matching:
                cells = _split_table_row(line)
                exact_status = (
                    "NOT RUN" in cells
                    if cells
                    else "NOT RUN" in [token.strip() for token in CODE_SPAN_RE.findall(line)]
                )
                if exact_status and not invalid.search(line):
                    valid = True
                    break
            if not valid:
                issues.append(Issue("FALSE_COMPLETION_STATUS", relative, f"current evidence label {label!r} must remain explicitly NOT RUN"))
    for relative, rules in HISTORICAL_REPOSITORY_STATUS_RULES.items():
        lines = sources.get(relative, "").splitlines()
        for label, expected_status in rules:
            matching = [
                line
                for line in lines
                if (cells := _split_table_row(line))
                and cells[0].casefold() == label.casefold()
            ]
            exact = [
                line
                for line in matching
                if (cells := _split_table_row(line))
                and len(cells) >= 2
                and cells[0].casefold() == label.casefold()
                and cells[1] == expected_status
            ]
            if len(matching) != 1 or len(exact) != 1:
                issues.append(
                    Issue(
                        "REPOSITORY_PUBLICATION_STATUS_MISMATCH",
                        relative,
                        f"historically confirmed repository label {label!r} must occur once with exact status {expected_status!r}",
                    )
                )
    treehouse_lines = sources.get(TREEHOUSE_USAGE_PATH, "").splitlines()
    for label, expected_status in HISTORICAL_TREEHOUSE_STATUS_RULES:
        matching = [line for line in treehouse_lines if label.casefold() in line.casefold()]
        exact = [
            line
            for line in matching
            if (cells := _split_table_row(line))
            and len(cells) >= 2
            and cells[0].casefold() == label.casefold()
            and cells[1] == expected_status
        ]
        if len(matching) != 1 or len(exact) != 1:
            issues.append(
                Issue(
                    "TREEHOUSE_STATUS_MISMATCH",
                    TREEHOUSE_USAGE_PATH,
                    f"historical Treehouse label {label!r} must occur once with exact status {expected_status!r}",
                )
            )
    return issues


def _check_treehouse_scoped_statuses(sources: Mapping[str, str]) -> list[Issue]:
    issues: list[Issue] = []
    for relative in TREEHOUSE_SCOPED_SUMMARY_PATHS:
        text = sources.get(relative, "")
        for label, expected_status in CURRENT_TREEHOUSE_SCOPED_STATUS_RULES:
            token_pattern = re.compile(
                rf"`{re.escape(label)}=([^`\r\n]+)`",
                re.IGNORECASE,
            )
            matching = list(token_pattern.finditer(text))
            expected_token = f"`{label}={expected_status}`"
            if len(matching) != 1 or matching[0].group(0) != expected_token:
                issues.append(
                    Issue(
                        "TREEHOUSE_STATUS_MISMATCH",
                        relative,
                        f"current scoped Treehouse token {expected_token!r} must occur exactly once",
                    )
                )
        for evidence_path in TREEHOUSE_RECOVERY_EVIDENCE_PATHS:
            expected_reference = f"`{evidence_path}`"
            if text.count(expected_reference) != 1:
                issues.append(
                    Issue(
                        "TREEHOUSE_EVIDENCE_MISMATCH",
                        relative,
                        f"current Treehouse evidence reference {expected_reference!r} must occur exactly once",
                    )
                )
        for expected_token in CURRENT_TREEHOUSE_SCOPED_BOUNDARY_TOKENS:
            if text.count(expected_token) != 1:
                issues.append(
                    Issue(
                        "TREEHOUSE_RUNTIME_BOUNDARY_MISMATCH",
                        relative,
                        f"current Treehouse runtime-boundary token {expected_token!r} must occur exactly once",
                    )
                )
    return issues


def _check_content(sources: Mapping[str, str]) -> list[Issue]:
    issues: list[Issue] = []
    for relative, groups in CONTENT_REQUIREMENTS.items():
        text = sources.get(relative, "")
        lowered = text.lower()
        for group in groups:
            if not any(token.lower() in lowered for token in group):
                issues.append(Issue("REQUIRED_CONTENT_MISSING", relative, "required content tokens missing: " + " + ".join(group)))
    return issues


def _edge_pattern(source: str, target: str) -> re.Pattern[str]:
    return re.compile(
        rf"^\s*{re.escape(source)}\b\s*(?:-->|==>|-\.->|---)(?:\|[^|\r\n]*\|)?\s*\b{re.escape(target)}\b",
        re.MULTILINE,
    )


def _check_diagrams(root: Path, diagrams: Mapping[str, str]) -> list[Issue]:
    issues: list[Issue] = []
    for relative, spec in DIAGRAM_SPECS.items():
        text = diagrams.get(relative, "")
        if not text.strip():
            issues.append(Issue("MERMAID_EMPTY", relative, "required Mermaid source is missing or empty"))
            continue
        active_lines = [line for line in text.splitlines() if not line.lstrip().startswith("%%")]
        active_text = "\n".join(active_lines)
        meaningful = [line.strip() for line in active_lines if line.strip()]
        if not meaningful or not re.match(r"^(?:flowchart|graph)\s+(?:TD|TB|BT|RL|LR)\b", meaningful[0]):
            issues.append(Issue("MERMAID_GRAPH_TYPE", relative, "first meaningful line must declare a supported flowchart/graph direction"))
        if PLACEHOLDER_RE.search(text):
            issues.append(Issue("MERMAID_PLACEHOLDER", relative, "placeholder text is not allowed"))
        for node in spec["nodes"]:
            node_pattern = r"^\s*" + re.escape(node) + r"\b\s*[\[({]"
            if not re.search(node_pattern, active_text, re.MULTILINE):
                issues.append(Issue("MERMAID_NODE_MISSING", relative, f"required node definition {node!r} is absent"))
        for source, target in spec["edges"]:
            if not _edge_pattern(source, target).search(active_text):
                issues.append(Issue("MERMAID_EDGE_MISSING", relative, f"required edge {source} -> {target} is absent"))
        lowered = active_text.lower()
        for label in spec["labels"]:
            if label.lower() not in lowered:
                issues.append(Issue("MERMAID_LABEL_MISSING", relative, f"required label {label!r} is absent"))
        for match in re.finditer(r"^\s*click\s+\w+\s+[\"']([^\"']+)[\"']", active_text, re.MULTILINE):
            target = match.group(1)
            if _is_external(target):
                continue
            candidate = (root / relative).parent / target
            exists, exact_case = _case_sensitive_state(root, candidate)
            if not exists:
                issues.append(Issue("MERMAID_LOCAL_REFERENCE_BROKEN", relative, f"click target {target!r} is absent"))
            elif not exact_case:
                issues.append(Issue("MERMAID_LOCAL_REFERENCE_CASE", relative, f"click target {target!r} has incorrect case"))
    return issues


def _check_registry(root: Path) -> tuple[list[Issue], dict[str, Any]]:
    issues: list[Issue] = []
    registry_path = root / "C_Semantic_Treehouse/manifests/validation-suites.json"
    schema_path = root / "C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json"
    release_path = root / "C_Semantic_Treehouse/manifests/release-manifest.json"
    registry = _load_json(registry_path)
    schema = _load_json(schema_path)
    release = _load_json(release_path)
    try:
        from jsonschema import Draft202012Validator

        schema_errors = sorted(Draft202012Validator(schema).iter_errors(registry), key=lambda item: list(item.path))
    except Exception as exc:  # noqa: BLE001
        schema_errors = []
        issues.append(Issue("REGISTRY_SCHEMA_RUNTIME", str(schema_path.relative_to(root)).replace("\\", "/"), f"schema validator failed: {exc}"))
    for error in schema_errors:
        location = "/".join(str(item) for item in error.path) or "/"
        issues.append(Issue("REGISTRY_SCHEMA", str(registry_path.relative_to(root)).replace("\\", "/"), f"{location}: {error.message}"))

    scripts_dir = str((root / "scripts").resolve())
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    try:
        from dssc_validation.entrypoint_catalog import (
            ENTRYPOINT_CATALOG,
            LazyEntrypoint,
            resolve_entrypoint,
        )
        from dssc_validation.suite_registry import semantic_validate_registry

        for item in semantic_validate_registry(registry):
            issues.append(Issue("REGISTRY_SEMANTIC", str(registry_path.relative_to(root)).replace("\\", "/"), f"{item.code}: {item.message}"))
        documentation_entry = ENTRYPOINT_CATALOG.get("check_documentation")
        if documentation_entry is None:
            issues.append(Issue("REGISTRY_IMPLEMENTATION", "scripts/dssc_validation/entrypoint_catalog.py", "check_documentation is absent from the controlled entrypoint catalog"))
        else:
            if documentation_entry.allowed_suites != frozenset({"all"}):
                issues.append(Issue("REGISTRY_IMPLEMENTATION", "scripts/dssc_validation/entrypoint_catalog.py", "check_documentation must be allowed for exactly the all suite"))
            function = documentation_entry.function
            if (
                type(function) is not LazyEntrypoint
                or function.target_module != "check_documentation"
                or function.target_function != "run_documentation_check"
            ):
                issues.append(Issue("REGISTRY_IMPLEMENTATION", "scripts/dssc_validation/entrypoint_catalog.py", "check_documentation must target check_documentation.run_documentation_check through the controlled lazy adapter"))
            elif resolve_entrypoint("check_documentation", "all") is not function:
                issues.append(Issue("REGISTRY_IMPLEMENTATION", "scripts/dssc_validation/entrypoint_catalog.py", "dispatcher resolution differs from the catalog-bound documentation callable"))
    except Exception as exc:  # noqa: BLE001
        issues.append(Issue("REGISTRY_IMPLEMENTATION", "scripts/dssc_validation/entrypoint_catalog.py", f"controlled registry implementation could not be loaded: {exc}"))

    suites = {item.get("id"): item for item in registry.get("suites", []) if isinstance(item, dict)}
    if tuple(item.get("id") for item in registry.get("suites", [])) != PUBLIC_SUITES:
        issues.append(Issue("REGISTRY_PUBLIC_SUITES", str(registry_path.relative_to(root)).replace("\\", "/"), "public suites must remain in the fixed seven-suite order"))
    if registry.get("contract_version") != EXPECTED_CONTRACT_VERSION:
        issues.append(Issue("REGISTRY_VERSION", str(registry_path.relative_to(root)).replace("\\", "/"), f"expected contract_version {EXPECTED_CONTRACT_VERSION}"))
    registry_relative = str(registry_path.relative_to(root)).replace("\\", "/")
    for suite_id, expected in EXPECTED_SUITE_PROJECTION.items():
        suite = suites.get(suite_id)
        if not isinstance(suite, dict):
            issues.append(Issue("REGISTRY_SUITE_PROJECTION", registry_relative, f"suite {suite_id!r} is absent"))
            continue
        actual_components = tuple(
            (component.get("id"), component.get("entrypoint"))
            if isinstance(component, dict)
            else (None, None)
            for component in suite.get("components", [])
        )
        actual = {
            "status": suite.get("status"),
            "depends_on": tuple(suite.get("depends_on", [])),
            "components": actual_components,
            "owner_phase": suite.get("owner_phase"),
        }
        for field, expected_value in expected.items():
            if actual[field] != expected_value:
                issues.append(
                    Issue(
                        "REGISTRY_SUITE_PROJECTION",
                        registry_relative,
                        f"suite {suite_id!r} field {field!r} differs: expected={expected_value!r}, actual={actual[field]!r}",
                    )
                )

    all_suite = suites.get("all", {})

    registry_hash = _sha256(registry_path)
    binding = release.get("validationSuiteRegistry", {})
    expected_binding = {
        "path": "C_Semantic_Treehouse/manifests/validation-suites.json",
        "sha256": registry_hash,
        "contractVersion": EXPECTED_CONTRACT_VERSION,
    }
    if binding != expected_binding:
        issues.append(Issue("REGISTRY_RELEASE_BINDING", str(release_path.relative_to(root)).replace("\\", "/"), f"expected validationSuiteRegistry binding {expected_binding!r}"))
    return issues, {
        "path": "C_Semantic_Treehouse/manifests/validation-suites.json",
        "schema_path": "C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json",
        "schema_sha256": _sha256(schema_path),
        "contract_version": registry.get("contract_version"),
        "sha256": registry_hash,
        "all_components": [item.get("id") for item in all_suite.get("components", [])],
    }


def _source_hashes(root: Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for relative, roles in SOURCE_PATHS:
        path = root / relative
        result.append({"path": relative, "roles": list(roles), "sha256": _sha256(path)})
    return result


def _loaded_source_hashes(root: Path) -> tuple[dict[str, str], list[str]]:
    """Hash every repository checker/helper source loaded for this run."""

    scripts_dir = str((root / "scripts").resolve())
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    try:
        from dssc_validation.provenance import collect_loaded_source_hashes

        return collect_loaded_source_hashes(
            root,
            (
                "scripts/check_documentation.py",
                "scripts/validate.py",
                "scripts/dssc_validation/provenance.py",
            ),
        )
    except Exception as exc:  # noqa: BLE001
        return {}, [f"loaded source hash collection failed: {exc}"]


def _input_hashes(root: Path, paths: Iterable[str]) -> list[dict[str, str]]:
    result = []
    for relative in sorted(paths):
        path = root / relative
        if path.is_file():
            result.append({"path": relative, "sha256": _sha256(path)})
    return result


def _git_value(root: Path, *arguments: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *arguments], cwd=root, check=False, text=True, encoding="utf-8", capture_output=True
        )
    except OSError:
        return "UNKNOWN"
    return completed.stdout.strip() if completed.returncode == 0 else "UNKNOWN"


def _machine_environment(
    root: Path,
    result_path: Path,
    result: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        pip_version = metadata.version("pip")
    except metadata.PackageNotFoundError:
        pip_version = "UNKNOWN"
    try:
        jsonschema_version = metadata.version("jsonschema")
    except metadata.PackageNotFoundError:
        jsonschema_version = "UNKNOWN"
    return {
        "schema_version": "1.0.0",
        "check_id": CHECK_ID,
        "os": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "pip_version": pip_version,
        "jsonschema_version": jsonschema_version,
        "git_commit": _git_value(root, "rev-parse", "HEAD"),
        "git_dirty": bool(_git_value(root, "status", "--short")),
        "lock_sha256": _sha256(root / "requirements.lock"),
        "command": result.get("command"),
        "source_hashes": result.get("source_hashes", {}),
        "source_hash_issues": result.get("source_hash_issues", []),
        "external_evidence": result.get("external_evidence", {}),
        "result_path": str(result_path.relative_to(root)).replace("\\", "/"),
        "result_sha256": _sha256(result_path),
    }


def _report_markdown(result: dict[str, Any]) -> str:
    repository = result["external_evidence"]["repository_github"]
    historical = repository["last_confirmed_candidate"]
    current = repository["current_candidate"]
    lines = [
        "# Documentation Validation Report",
        "",
        f"- Check: `{result['check_id']}`",
        f"- Program status: `{result['program_status']}`",
        f"- Result: `{result['status']}`",
        f"- Invocation: `{result['command']}`",
        f"- Documents: `{result['counts']['documents']}`",
        f"- Diagrams: `{result['counts']['diagrams']}`",
        f"- Checks: `{result['counts']['executed']}` executed, `{result['counts']['failed']}` failed, `0` skipped",
        f"- Loaded checker/dispatcher/helper sources: `{len(result['source_hashes'])}`",
        "- Mermaid scope: structural lint only; Mermaid syntax validation, rendering and visual QA are `NOT RUN`.",
        f"- Last confirmed GitHub candidate: `{historical['status']}`.",
        f"- Current synchronized candidate: `{current['status']}`.",
        "",
        "## Checks",
        "",
        "| check | status | issue_count |",
        "|---|---|---:|",
    ]
    for check in result["checks"]:
        lines.append(f"| `{check['id']}` | `{check['status']}` | {check['issue_count']} |")
    lines.extend(["", "## Issues", ""])
    if result["issues"]:
        for issue in result["issues"]:
            lines.append(f"- `{issue['code']}` `{issue['path']}` — {issue['message']}")
    else:
        lines.append("No documentation consistency issues were found.")
    lines.extend(
        [
            "",
            "## Registry",
            "",
            f"- Contract version: `{result['registry']['contract_version']}`",
            f"- SHA-256: `{result['registry']['sha256']}`",
            f"- Ordered `all` internal components: `{', '.join(result['registry']['all_components'])}`",
            "",
            "## Evidence boundary",
            "",
            (
                "This report proves deterministic documentation consistency and Mermaid structural lint only. "
                "The scoped Semantic Treehouse deployment, workload, database migration, real-browser UI workflow, "
                "canonical six-asset API import, ontology TTL RDF-isomorphic export round-trip and SHACL validator "
                "execution passed. The retained containers are safely `PAUSED` with the application and database "
                "volumes preserved. Semantic Treehouse publication remains `NOT RUN`; Mermaid parsing/rendering and "
                "external SEMIC/ITB remain `NOT RUN`. The last confirmed repository publication, GitHub Actions "
                "Ubuntu/Windows/Docker run and remote clean clone are "
                f"`{historical['status']}` for candidate `{historical.get('candidate_sha', 'UNKNOWN')}`. "
                f"The current synchronized candidate is `{current['status']}`. These separate historical/current "
                "states are bound by `docs/v0.4/publication-record.md`; tag and GitHub Release keep their "
                "separately recorded governance status."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def _evaluate(
    root: Path,
    document_paths: Sequence[str] = DOCUMENT_PATHS,
    document_overrides: Mapping[str, str] | None = None,
    diagram_overrides: Mapping[str, str] | None = None,
    *,
    command: str | None = None,
    expected_suite: str | None = None,
    expected_contract_version: str | None = None,
    expected_registry_sha256: str | None = None,
) -> dict[str, Any]:
    documents, document_read_issues = _read_sources(root, document_paths, document_overrides)
    publication_sources, publication_read_issues = _read_sources(
        root,
        (PUBLICATION_RECORD_PATH,),
        document_overrides,
    )
    treehouse_current_documents, treehouse_current_read_issues = _read_sources(
        root,
        TREEHOUSE_CURRENT_DOC_PATHS,
        document_overrides,
    )
    diagrams, diagram_read_issues = _read_sources(root, tuple(DIAGRAM_SPECS), diagram_overrides)
    release_manifest = _load_json(root / "C_Semantic_Treehouse/manifests/release-manifest.json")
    requirements = _load_json(root / "C_Semantic_Treehouse/manifests/v0.4-requirements.json")
    test_manifest = _load_json(root / "C_Semantic_Treehouse/manifests/v0.4-test-cases.json")
    registry_issues, registry_summary = _check_registry(root)
    repository_publication, repository_publication_issues = _check_repository_publication(
        publication_sources
    )
    suite_ids = {item.get("id") for item in _load_json(root / "C_Semantic_Treehouse/manifests/validation-suites.json").get("suites", [])}
    dispatcher_issues: list[Issue] = []
    if expected_suite is not None and expected_suite != "all":
        dispatcher_issues.append(Issue("DISPATCHER_SUITE_MISMATCH", "scripts/validate.py", f"documentation component requires suite 'all'; actual={expected_suite!r}"))
    if expected_contract_version is not None and expected_contract_version != registry_summary.get("contract_version"):
        dispatcher_issues.append(Issue("DISPATCHER_CONTRACT_MISMATCH", "scripts/validate.py", f"dispatcher contract_version {expected_contract_version!r} differs from checker registry {registry_summary.get('contract_version')!r}"))
    if expected_registry_sha256 is not None and expected_registry_sha256 != registry_summary.get("sha256"):
        dispatcher_issues.append(Issue("DISPATCHER_REGISTRY_HASH_MISMATCH", "scripts/validate.py", f"dispatcher registry SHA-256 {expected_registry_sha256!r} differs from checker registry {registry_summary.get('sha256')!r}"))
    source_hashes, source_hash_issues = _loaded_source_hashes(root)
    source_issues = [
        Issue("SOURCE_HASH_ERROR", "scripts", message)
        for message in sorted(source_hash_issues)
    ]
    if not source_hashes:
        source_issues.append(
            Issue(
                "SOURCE_HASH_ZERO_DISCOVERY",
                "scripts",
                "zero loaded repository checker/helper sources were hashed",
            )
        )

    check_results: list[tuple[str, list[Issue]]] = [
        ("required-documents", document_read_issues + diagram_read_issues),
        ("markdown-links", _check_links(root, documents)),
        ("absolute-and-temporary-paths", _check_absolute_and_temporary_paths(documents)),
        ("commands-and-suites", _check_commands_and_suites(root, documents, suite_ids)),
        ("suite-table-projection", _check_suite_tables(documents, suite_ids)),
        ("repository-references", _check_repository_references(root, documents)),
        ("artifact-manifest-projection", _check_artifacts_and_tables(root, documents, release_manifest)),
        ("path-hash-bindings", _check_path_hash_bindings(root, documents)),
        ("inline-path-hash-bindings", _check_inline_path_hash_bindings(root, documents)),
        ("a-handoff-field-projection", _check_field_table(root, documents, requirements)),
        ("test-case-status-projection", _check_case_status_rows(documents, test_manifest)),
        ("business-status-count-projection", _check_business_status_counts(documents, test_manifest)),
        ("hash-declarations", _check_hash_declarations(root, documents, release_manifest)),
        (
            "truthful-status-boundaries",
            treehouse_current_read_issues
            + _check_truthful_statuses(documents)
            + _check_final_navigation_statuses(documents)
            + _check_treehouse_scoped_statuses(treehouse_current_documents),
        ),
        (
            "repository-publication-evidence",
            publication_read_issues + repository_publication_issues,
        ),
        ("required-content", _check_content(documents)),
        ("mermaid-structure", _check_diagrams(root, diagrams)),
        ("suite-registry", registry_issues),
        ("dispatcher-envelope", dispatcher_issues),
        ("source-hash-coverage", source_issues),
    ]
    issues = sorted(
        [issue for _, group in check_results for issue in group],
        key=lambda item: (item.code, item.path, item.message),
    )
    checks = [
        {"id": check_id, "status": "PASS" if not group else "FAIL", "issue_count": len(group)}
        for check_id, group in check_results
    ]
    failed = sum(1 for item in checks if item["status"] == "FAIL")
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "check_id": CHECK_ID,
        "status": "PASS" if not issues else "FAIL",
        "program_status": "SUCCESS" if not issues else "ERROR",
        "command": command or _standalone_command(),
        "counts": {
            "documents": len(documents),
            "diagrams": len(diagrams),
            "discovered": len(documents) + len(diagrams),
            "executed": len(checks),
            "passed": len(checks) - failed,
            "failed": failed,
            "skipped": 0,
        },
        "checks": checks,
        "issues": [issue.as_dict() for issue in issues],
        "registry": registry_summary,
        "diagram_validation": {
            "scope": "STRUCTURAL_LINT_ONLY",
            "syntax_validation": "NOT RUN",
            "render_validation": "NOT RUN",
            "visual_qa": "NOT RUN",
        },
        "external_evidence": {
            "semantic_treehouse": {
                "track_status": "PASS",
                "attempt_status": "DEPLOYMENT_IMPORT_UI_RDF_ROUND_TRIP_AND_SHACL_PASS_RUNTIME_PAUSED",
                "core_suite_impact": "NONE",
                "fixed_checkout_materialization": "PASS",
                "raw_upstream_compose_preflight": "BLOCKED",
                "raw_preflight_execution_authorized": False,
                "finding_specific_human_opt_in": "APPROVED",
                "prepare_only_runtime_boundary": "PASS",
                "image_build_attempt": "PASS",
                "deployment": "PASS",
                "workload_container_execution": "PASS",
                "database_migration": "PASS",
                "current_runtime": "PAUSED",
                "root_loopback_smoke": "PASS",
                "api_loopback_availability_smoke": "PASS",
                "ui_workflow": "PASS",
                "model_import": "PASS",
                "model_import_scope": "CANONICAL_SIX_ASSETS",
                "export": "PASS",
                "export_semantic_check": "ONTOLOGY_TTL_RDF_ISOMORPHIC",
                "publication": "NOT RUN",
                "shacl_validator_execution": "PASS",
                "evidence": {
                    "runtime_auth_storage_recovery": TREEHOUSE_RECOVERY_EVIDENCE_PATHS[0],
                    "canonical_six_asset_import": TREEHOUSE_RECOVERY_EVIDENCE_PATHS[1],
                    "post_restart_inventory_and_round_trip": TREEHOUSE_RECOVERY_EVIDENCE_PATHS[2],
                    "real_browser_ui_verification": TREEHOUSE_RECOVERY_EVIDENCE_PATHS[3],
                    "shacl_validator_execution": TREEHOUSE_RECOVERY_EVIDENCE_PATHS[4],
                    "shacl_validator_idempotent_recheck": TREEHOUSE_RECOVERY_EVIDENCE_PATHS[5],
                    "runtime_pause_after_shacl_validation": TREEHOUSE_RECOVERY_EVIDENCE_PATHS[6],
                },
            },
            "semic": "NOT RUN",
            "itb": "NOT RUN",
            "repository_github": repository_publication,
        },
        "input_hashes": _input_hashes(
            root,
            tuple(documents)
            + tuple(publication_sources)
            + tuple(treehouse_current_documents)
            + tuple(diagrams)
            + AUTHORITY_JSON_PATHS,
        ),
        "source_hashes": source_hashes,
        "source_hash_issues": sorted(source_hash_issues),
    }
    if result["counts"]["discovered"] == 0 or result["counts"]["skipped"] != 0:
        raise AssertionError("zero discovery or skipped required checks must not be summarized as success")
    return result


def _standalone_command(*, self_test: bool = False) -> str:
    base = (
        ".\\.venv\\Scripts\\python.exe scripts\\check_documentation.py"
        if os.name == "nt"
        else "./.venv/bin/python scripts/check_documentation.py"
    )
    return base + (" --self-test" if self_test else "")


def _exit_code(result: Mapping[str, Any]) -> int:
    return 0 if result.get("program_status") == "SUCCESS" else 1


def run_canonical(
    root: Path = ROOT,
    *,
    write_evidence: bool = True,
    command: str | None = None,
    expected_suite: str | None = None,
    expected_contract_version: str | None = None,
    expected_registry_sha256: str | None = None,
) -> dict[str, Any]:
    result = _evaluate(
        root,
        command=command,
        expected_suite=expected_suite,
        expected_contract_version=expected_contract_version,
        expected_registry_sha256=expected_registry_sha256,
    )
    if write_evidence:
        output_dir = root / "build/validation/documentation"
        result_path = output_dir / "results.json"
        report_path = output_dir / "report.md"
        machine_path = output_dir / "run-environment.json"
        _write_json(result_path, result)
        _write_text(report_path, _report_markdown(result))
        _write_json(machine_path, _machine_environment(root, result_path, result))
    return result


def run_documentation_check(context: dict[str, Any]) -> dict[str, Any]:
    root = context.get("repository_root", ROOT)
    if not isinstance(root, Path):
        return {
            "status": "FAIL",
            "program_status": "ERROR",
            "message": "documentation checker requires repository_root",
            "details": {},
            "machine_details": {},
        }
    result = run_canonical(
        root,
        command="dispatcher suite=all component=all.documentation entrypoint=check_documentation",
        expected_suite=context.get("suite") if isinstance(context.get("suite"), str) else "<INVALID>",
        expected_contract_version=(
            context.get("contract_version")
            if isinstance(context.get("contract_version"), str)
            else "<INVALID>"
        ),
        expected_registry_sha256=(
            context.get("registry_sha256")
            if isinstance(context.get("registry_sha256"), str)
            else "<INVALID>"
        ),
    )
    return {
        "status": result["status"],
        "program_status": result["program_status"],
        "message": (
            "Phase 07 documentation and Mermaid structural checks passed"
            if result["status"] == "PASS"
            else "Phase 07 documentation checks failed"
        ),
        "details": {
            "check_id": CHECK_ID,
            "counts": result["counts"],
            "registry": result["registry"],
            "issues": result["issues"],
            "result_path": "build/validation/documentation/results.json",
            "report_path": "build/validation/documentation/report.md",
            "mermaid_scope": "STRUCTURAL_LINT_ONLY; syntax/render NOT RUN",
        },
        "machine_details": {
            "environment_path": "build/validation/documentation/run-environment.json"
        },
    }


def _mutate_field_table(text: str) -> str:
    original = "| `D04-R003` | `true` | `ex:datasetId` |"
    mutated = "| `D04-R003` | `true` | `ex:wrongDatasetId` |"
    if text.count(original) != 1:
        raise AssertionError("negative-control field row is not uniquely identifiable")
    return text.replace(original, mutated, 1)


def _mutate_case_status(text: str) -> str:
    original = "| `D04-PC059` | `INAPPLICABLE` |"
    mutated = "| `D04-PC059` | `PASS` |"
    if text.count(original) != 1:
        raise AssertionError("negative-control case-status row is not uniquely identifiable")
    return text.replace(original, mutated, 1)


def _remove_node(text: str, node: str) -> str:
    pattern = r"^.*\b" + re.escape(node) + r"\b\s*[\[({].*$"
    return re.sub(pattern, "", text, count=1, flags=re.MULTILINE)


def _remove_edge(text: str, source: str, target: str) -> str:
    pattern = _edge_pattern(source, target)
    return pattern.sub(f"{source} --> BrokenTarget", text, count=1)


def _replace_first_hash_with_second(text: str) -> str:
    matches = list(HASH_RE.finditer(text))
    if len(matches) < 2:
        raise AssertionError("negative-control source needs at least two SHA-256 values")
    first = matches[0]
    replacement = next(
        (item.group(0) for item in matches[1:] if item.group(0) != first.group(0)),
        None,
    )
    if replacement is None:
        raise AssertionError("negative-control source needs two distinct SHA-256 values")
    return text[: first.start()] + replacement + text[first.end() :]


def _append_empty_artifact_table(text: str) -> str:
    return text + (
        "\n\n| artifact_id | version | role | path | sha256 |\n"
        "|---|---|---|---|---|\n"
    )


def _replace_treehouse_status(text: str, label: str, expected: str, mutated: str) -> str:
    original = f"| {label} | `{expected}` |"
    replacement = f"| {label} | `{mutated}` |"
    if text.count(original) != 1:
        raise AssertionError(f"negative-control Treehouse row {label!r} is not uniquely identifiable")
    return text.replace(original, replacement, 1)


def _publication_control_row_positions(text: str, label: str) -> tuple[list[str], list[int]]:
    """Locate one control row in the current candidate, falling back to history.

    The canonical publication record contains both a historical confirmed candidate and,
    after section 6.11, a current confirmed candidate.  Negative controls must mutate one
    section deliberately instead of assuming publication labels are globally unique.
    """

    lines = text.splitlines()
    sections: list[tuple[str, int, int]] = []
    headings = [
        (index, match.group(1))
        for index, line in enumerate(lines)
        if (match := re.match(r"^##(?!#)\s+(.+?)\s*$", line))
    ]
    for position, (start, title) in enumerate(headings):
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        sections.append((title, start + 1, end))

    current_sections = [
        (start, end)
        for title, start, end in sections
        if "审计恢复" in title or "当前同步候选" in title or "新候选" in title
    ]
    if len(current_sections) != 1:
        raise AssertionError("negative-control current publication section is not uniquely identifiable")

    def positions_within(bounds: tuple[int, int]) -> list[int]:
        start, end = bounds
        return [
            index
            for index in range(start, end)
            if (cells := _split_table_row(lines[index])) and cells[0] == label
        ]

    positions = positions_within(current_sections[0])
    if len(positions) != 1:
        raise AssertionError(
            f"negative-control publication row {label!r} is not uniquely identifiable in the current section"
        )
    return lines, positions


def _replace_publication_row(text: str, label: str, value: str) -> str:
    lines, positions = _publication_control_row_positions(text, label)
    lines[positions[0]] = f"| {label} | {value} |"
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _duplicate_publication_row(text: str, label: str, value: str) -> str:
    lines, positions = _publication_control_row_positions(text, label)
    lines.insert(positions[0] + 1, f"| {label} | {value} |")
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _publication_with_confirmed_current_candidate(text: str) -> str:
    """Build a dual-confirmed-candidate fixture for publication negative controls."""

    sections = _markdown_level_two_sections(text)
    historical = [
        body
        for title, body in sections
        if "上一次已确认候选" in title or "历史已确认候选" in title
    ]
    if len(historical) != 1:
        raise AssertionError("negative-control historical publication section is not unique")

    lines = text.splitlines()
    current_headings = [
        index
        for index, line in enumerate(lines)
        if (match := re.match(r"^##(?!#)\s+(.+?)\s*$", line))
        and ("审计恢复" in match.group(1) or "当前同步候选" in match.group(1) or "新候选" in match.group(1))
    ]
    if len(current_headings) != 1:
        raise AssertionError("negative-control current publication section is not unique")
    start = current_headings[0] + 1
    end = next(
        (index for index in range(start, len(lines)) if re.match(r"^##(?!#)\s+", lines[index])),
        len(lines),
    )
    replacement = historical[0].splitlines()
    mutated = lines[:start] + replacement + lines[end:]
    return "\n".join(mutated) + ("\n" if text.endswith("\n") else "")


def _rename_current_candidate_section(text: str) -> str:
    lines = text.splitlines()
    positions = [
        index
        for index, line in enumerate(lines)
        if re.match(r"^##(?!#)\s+", line)
        and ("审计恢复" in line or "当前同步候选" in line or "新候选" in line)
    ]
    if len(positions) != 1:
        raise AssertionError(
            "negative-control current-candidate section is not uniquely identifiable"
        )
    lines[positions[0]] = "## 3. Unrelated notes"
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _replace_treehouse_scoped_status(text: str, label: str, expected: str, mutated: str) -> str:
    original = f"`{label}={expected}`"
    replacement = f"`{label}={mutated}`"
    if text.count(original) != 1:
        raise AssertionError(f"negative-control scoped Treehouse token {original!r} is not uniquely identifiable")
    return text.replace(original, replacement, 1)


def _replace_treehouse_scoped_token(text: str, expected: str, mutated: str) -> str:
    if text.count(expected) != 1:
        raise AssertionError(f"negative-control scoped Treehouse token {expected!r} is not uniquely identifiable")
    return text.replace(expected, mutated, 1)


def _insert_after_unique_line(text: str, prefix: str, line: str) -> str:
    lines = text.splitlines()
    positions = [index for index, value in enumerate(lines) if value.startswith(prefix)]
    if len(positions) != 1:
        raise AssertionError(f"negative-control row prefix is not unique: {prefix}")
    lines.insert(positions[0] + 1, line)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _strip_outer_pipes_from_b_hash_table(text: str) -> str:
    lines = text.splitlines()
    header = "| item | manifest ID / ref | repository path | SHA-256 |"
    positions = [index for index, value in enumerate(lines) if value == header]
    if len(positions) != 1:
        raise AssertionError("B handoff hash table header is not uniquely identifiable")
    cursor = positions[0]
    while cursor < len(lines) and lines[cursor].strip().startswith("|"):
        value = lines[cursor].strip()
        lines[cursor] = value[1:-1].strip()
        cursor += 1
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _malform_first_artifact_row(text: str) -> str:
    lines = text.splitlines()
    header_positions = [
        index
        for index, value in enumerate(lines)
        if value.strip() == "| artifact_id | version | role | path | sha256 |"
    ]
    if len(header_positions) != 1:
        raise AssertionError("artifact table header is not uniquely identifiable")
    row_index = header_positions[0] + 2
    lines[row_index] = lines[row_index].rstrip().rstrip("|") + "| unexpected |"
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _remove_pipe_table(text: str, header: str) -> str:
    lines = text.splitlines()
    positions = [index for index, value in enumerate(lines) if value == header]
    if len(positions) != 1:
        raise AssertionError(f"table header is not uniquely identifiable: {header}")
    start = positions[0]
    cursor = start
    while cursor < len(lines) and lines[cursor].strip().startswith("|"):
        cursor += 1
    del lines[start:cursor]
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _venv_command_contract_controls(
    root: Path,
    documents: Mapping[str, str],
    suite_ids: set[str],
    fixture_dir: Path,
) -> list[dict[str, Any]]:
    def probe(command: str) -> dict[str, str]:
        return {"command-probe.md": f"```text\n{command}\n```\n"}

    with tempfile.TemporaryDirectory(prefix="phase-07-venv-contract-") as temporary:
        clean_root = Path(temporary)
        canonical_commands: list[str] = []
        for text in documents.values():
            for _, command in _command_lines(text):
                canonical_commands.append(command)
                _, _, paths = _command_path_contract(command)
                for raw_path in paths:
                    candidate = _normalized_command_path(raw_path)
                    if candidate.startswith(".venv/"):
                        continue
                    _write_text(clean_root / candidate, "synthetic source placeholder\n")

        cases: list[tuple[str, str | None, Mapping[str, str], str]] = [
            (
                "clean-linux-no-venv-canonical",
                None,
                documents,
                "\n".join(canonical_commands) + "\n",
            ),
            (
                "windows-venv-missing-source-clean",
                "COMMAND_PATH_MISSING",
                probe(r".\.venv\Scripts\python.exe -I scripts\missing-phase-07-source.py"),
                r".\.venv\Scripts\python.exe -I scripts\missing-phase-07-source.py" + "\n",
            ),
            (
                "posix-venv-missing-source-clean",
                "COMMAND_PATH_MISSING",
                probe("./.venv/bin/python -I scripts/missing-phase-07-source.py"),
                "./.venv/bin/python -I scripts/missing-phase-07-source.py\n",
            ),
            (
                "windows-venv-source-case-clean",
                "COMMAND_PATH_CASE_MISMATCH",
                probe(r".\.venv\Scripts\python.exe -I Scripts\check_documentation.py"),
                r".\.venv\Scripts\python.exe -I Scripts\check_documentation.py" + "\n",
            ),
            (
                "posix-venv-source-case-clean",
                "COMMAND_PATH_CASE_MISMATCH",
                probe("./.venv/bin/python -I Scripts/check_documentation.py"),
                "./.venv/bin/python -I Scripts/check_documentation.py\n",
            ),
            (
                "windows-venv-no-script-clean",
                "COMMAND_PATH_MISSING",
                probe(
                    ".\\.venv\\Scripts\\python.exe -c \"pass\"\n"
                    ".\\.venv\\Scripts\\python.exe -m pip --version\n"
                    ".\\.venv\\Scripts\\python.exe"
                ),
                ".\\.venv\\Scripts\\python.exe -c \"pass\"\n"
                ".\\.venv\\Scripts\\python.exe -m pip --version\n"
                ".\\.venv\\Scripts\\python.exe\n",
            ),
            (
                "posix-venv-no-script-clean",
                "COMMAND_PATH_MISSING",
                probe(
                    "./.venv/bin/python -c \"pass\"\n"
                    "./.venv/bin/python -m pip --version\n"
                    "./.venv/bin/python"
                ),
                "./.venv/bin/python -c \"pass\"\n"
                "./.venv/bin/python -m pip --version\n"
                "./.venv/bin/python\n",
            ),
        ]

        results: list[dict[str, Any]] = []
        for control_id, expected_code, sources, snippet in cases:
            with mock.patch.object(platform, "system", return_value="Linux"):
                issues = _check_commands_and_suites(clean_root, sources, suite_ids)
            codes = sorted({issue.code for issue in issues})
            actual_exit_code = 1 if issues else 0
            passed = not issues if expected_code is None else expected_code in codes
            fixture_path = fixture_dir / f"{control_id}.txt"
            _write_text(fixture_path, snippet)
            fixture_bytes = fixture_path.read_bytes()
            results.append(
                {
                    "id": control_id,
                    "expected_issue_code": expected_code,
                    "expected_exit_code": "zero" if expected_code is None else "nonzero",
                    "actual_exit_code": actual_exit_code,
                    "observed_issue_codes": codes,
                    "input_evidence": str(fixture_path.relative_to(root)).replace("\\", "/"),
                    "input_evidence_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
                    "input_evidence_bytes": len(fixture_bytes),
                    "target_paths": sorted(sources),
                    "override_sha256": {
                        path: hashlib.sha256(value.encode("utf-8")).hexdigest()
                        for path, value in sorted(sources.items())
                    },
                    "status": "PASS" if passed else "FAIL",
                }
            )
        return results


def run_self_test(root: Path = ROOT) -> dict[str, Any]:
    self_test_command = _standalone_command(self_test=True)
    canonical = run_canonical(root, command=self_test_command)
    documents, _ = _read_sources(root, DOCUMENT_PATHS)
    publication_record = (root / PUBLICATION_RECORD_PATH).read_text(encoding="utf-8")
    confirmed_publication_fixture = _publication_with_confirmed_current_candidate(publication_record)
    treehouse_current_documents, _ = _read_sources(root, TREEHOUSE_CURRENT_DOC_PATHS)
    diagrams, _ = _read_sources(root, tuple(DIAGRAM_SPECS))
    suite_ids = set(PUBLIC_SUITES)
    first_doc = DOCUMENT_PATHS[0]
    core_report = CORE_REPORT_PATHS[0]
    a_handoff = "C_Semantic_Treehouse/handoff/handoff-to-A-offering-metadata.md"
    b_handoff = "C_Semantic_Treehouse/handoff/handoff-to-B-model-uri-provenance.md"
    d_handoff = "C_Semantic_Treehouse/handoff/handoff-to-D-shacl-validation.md"
    treehouse_usage = "C_Semantic_Treehouse/C_semantic_treehouse_usage.md"
    treehouse_scoped_summary = "tools/semantic-treehouse/README.md"
    export_report = "C_Semantic_Treehouse/C_export_for_validation.md"
    metadata_diagram = "C_Semantic_Treehouse/diagrams/metadata-record-model.mmd"

    controls: list[tuple[str, str, dict[str, str], dict[str, str], Sequence[str]]] = [
        ("broken-link", "BROKEN_LINK", {first_doc: documents[first_doc] + "\n[broken](missing-phase-07-target.md)\n"}, {}, DOCUMENT_PATHS),
        ("broken-image-link", "BROKEN_LINK", {first_doc: documents[first_doc] + "\n![broken](missing-phase-07-image.png)\n"}, {}, DOCUMENT_PATHS),
        ("undefined-reference-link", "BROKEN_LINK", {first_doc: documents[first_doc] + "\n![broken][missing-phase-07-reference]\n"}, {}, DOCUMENT_PATHS),
        ("broken-shortcut-image-reference", "BROKEN_LINK", {first_doc: documents[first_doc] + "\n![shortcut-broken]\n[shortcut-broken]: missing-phase-07-shortcut.png\n"}, {}, DOCUMENT_PATHS),
        ("link-case-mismatch", "LINK_CASE_MISMATCH", {first_doc: documents[first_doc] + "\n[case mismatch](readme.md)\n"}, {}, DOCUMENT_PATHS),
        ("personal-absolute-path", "PERSONAL_ABSOLUTE_PATH", {first_doc: documents[first_doc] + "\n`C:\\Users\\Example\\private.txt`\n"}, {}, DOCUMENT_PATHS),
        ("posix-absolute-path", "PERSONAL_ABSOLUTE_PATH", {first_doc: documents[first_doc] + "\n`/opt/private-repo/file.txt`\n"}, {}, DOCUMENT_PATHS),
        ("home-expansion-path", "PERSONAL_ABSOLUTE_PATH", {first_doc: documents[first_doc] + "\n`$HOME/private-repo/file.txt`\n"}, {}, DOCUMENT_PATHS),
        ("unknown-suite", "UNKNOWN_SUITE", {first_doc: documents[first_doc] + "\n```powershell\n.\\scripts\\validate.ps1 -Suite ghost\n```\n"}, {}, DOCUMENT_PATHS),
        ("quoted-unknown-suite", "UNKNOWN_SUITE", {first_doc: documents[first_doc] + "\n```powershell\n.\\scripts\\validate.ps1 -suite \"ghost-quoted\"\n```\n"}, {}, DOCUMENT_PATHS),
        ("inline-unknown-suite", "UNKNOWN_SUITE", {first_doc: documents[first_doc] + "\n`.\\scripts\\validate.ps1 -Suite ghost-inline`\n"}, {}, DOCUMENT_PATHS),
        ("unknown-suite-table-row", "UNKNOWN_SUITE", {first_doc: _insert_after_unique_line(documents[first_doc], "| `all` |", "| `ghost-table` | invalid suite |")}, {}, DOCUMENT_PATHS),
        ("bare-python3", "BARE_PYTHON_COMMAND", {first_doc: documents[first_doc] + "\n```bash\npython3 scripts/check_documentation.py\n```\n"}, {}, DOCUMENT_PATHS),
        ("bare-python-options", "BARE_PYTHON_COMMAND", {first_doc: documents[first_doc] + "\n```bash\npython3.12 -B scripts/check_documentation.py\n```\n"}, {}, DOCUMENT_PATHS),
        ("stale-venv-runner", "STALE_COMMAND", {first_doc: documents[first_doc] + "\n```powershell\n.\\.venv\\Scripts\\python.exe C_Semantic_Treehouse\\scripts\\run_all_validations.py\n```\n"}, {}, DOCUMENT_PATHS),
        ("generated-evidence-link-lookalike", "BROKEN_LINK", {first_doc: documents[first_doc] + "\n[unknown generated evidence](build/validation/v0.4/unknown-results.json)\n"}, {}, DOCUMENT_PATHS),
        ("generated-evidence-code-lookalike", "REFERENCE_PATH_MISSING", {first_doc: documents[first_doc] + "\n`build/validation/v0.4/results.json.bak`\n"}, {}, DOCUMENT_PATHS),
        ("missing-real-source-reference", "REFERENCE_PATH_MISSING", {first_doc: documents[first_doc] + "\n`scripts/missing-phase-07-source.py`\n"}, {}, DOCUMENT_PATHS),
        ("unknown-artifact", "UNKNOWN_ARTIFACT", {first_doc: documents[first_doc] + "\n`v04-unknown-document-artifact`\n"}, {}, DOCUMENT_PATHS),
        ("empty-artifact-table", "ARTIFACT_TABLE_EMPTY", {core_report: _append_empty_artifact_table(documents[core_report])}, {}, DOCUMENT_PATHS),
        ("malformed-artifact-row", "ARTIFACT_TABLE_MALFORMED", {core_report: _malform_first_artifact_row(documents[core_report])}, {}, DOCUMENT_PATHS),
        ("path-hash-mismatch", "PATH_HASH_MISMATCH", {b_handoff: _replace_first_hash_with_second(documents[b_handoff])}, {}, DOCUMENT_PATHS),
        ("binding-table-missing", "BINDING_TABLE_COUNT", {b_handoff: _remove_pipe_table(documents[b_handoff], "| item | manifest ID / ref | repository path | SHA-256 |")}, {}, DOCUMENT_PATHS),
        ("binding-table-header-drift", "BINDING_TABLE_COUNT", {b_handoff: documents[b_handoff].replace("| item | manifest ID / ref | repository path | SHA-256 |", "| item | manifest ID / ref | repository location | SHA-256 |", 1)}, {}, DOCUMENT_PATHS),
        ("path-hash-parent-traversal", "PATH_HASH_PATH_INVALID", {b_handoff: documents[b_handoff].replace("`inputs/d-group/v0.4/received/building-energy-shapes_D.ttl`", "`../../inputs/d-group/v0.4/received/building-energy-shapes_D.ttl`", 1)}, {}, DOCUMENT_PATHS),
        ("outer-pipe-free-path-hash-mismatch", "PATH_HASH_MISMATCH", {b_handoff: _replace_first_hash_with_second(_strip_outer_pipes_from_b_hash_table(documents[b_handoff]))}, {}, DOCUMENT_PATHS),
        ("id-path-hash-mismatch", "PATH_HASH_ID_MISMATCH", {a_handoff: documents[a_handoff].replace("`v04-metadata-context`", "`v04-metadata-valid`", 1)}, {}, DOCUMENT_PATHS),
        ("scoped-hash-mismatch", "PATH_HASH_MISMATCH", {d_handoff: documents[d_handoff].replace("53953e915d6da6159b342a04f1dc6d0ff6a8f53bd5892eb7933551710ebe014e", "87e367ea285ddc7feb5fa7f3f4b6c0035be0b768de5e56398ac422abaf494e5a", 1)}, {}, DOCUMENT_PATHS),
        ("inline-contextual-hash-mismatch", "INLINE_PATH_HASH_MISMATCH", {core_report: documents[core_report].replace("a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda", "d95a98be50641dbf4c131818547756183bf795edc426668c7c43c00f934bc7b4", 1)}, {}, DOCUMENT_PATHS),
        ("inline-contextual-hash-ambiguity", "INLINE_PATH_HASH_MISMATCH", {core_report: documents[core_report].replace("`a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda`", "`a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda` or `d95a98be50641dbf4c131818547756183bf795edc426668c7c43c00f934bc7b4`", 1)}, {}, DOCUMENT_PATHS),
        ("field-mismatch", "FIELD_MISMATCH", {a_handoff: _mutate_field_table(documents[a_handoff])}, {}, DOCUMENT_PATHS),
        ("field-unknown-requirement", "FIELD_UNKNOWN_REQUIREMENT", {a_handoff: _insert_after_unique_line(documents[a_handoff], "| `D04-R015` |", "| `D04-R999` | `false` | `ex:unknown` | `unknown` | `xsd:string` | `0..1` | none |")}, {}, DOCUMENT_PATHS),
        ("field-ambiguous-datatype", "FIELD_MISMATCH", {a_handoff: documents[a_handoff].replace("| `D04-R003` | `true` | `ex:datasetId` | `datasetId` | `xsd:string` |", "| `D04-R003` | `true` | `ex:datasetId` | `datasetId` | `xsd:string OR xsd:integer` |", 1)}, {}, DOCUMENT_PATHS),
        ("field-ambiguous-allowed-value", "FIELD_MISMATCH", {a_handoff: documents[a_handoff].replace("`hourly`，精确且大小写敏感", "`hourly or daily`", 1)}, {}, DOCUMENT_PATHS),
        ("hash-mismatch", "HASH_MISMATCH", {first_doc: documents[first_doc] + "\nSHA-256: `0000000000000000000000000000000000000000000000000000000000000000`\n"}, {}, DOCUMENT_PATHS),
        ("status-mismatch", "STATUS_MISMATCH", {export_report: _mutate_case_status(documents[export_report])}, {}, DOCUMENT_PATHS),
        ("status-table-missing", "STATUS_TABLE_COUNT", {export_report: _remove_pipe_table(documents[export_report], "| case_id | expected_business_status | scope |")}, {}, DOCUMENT_PATHS),
        ("status-count-mismatch", "STATUS_COUNT_MISMATCH", {a_handoff: documents[a_handoff].replace("`PASS: 6`", "`PASS: 7`", 1)}, {}, DOCUMENT_PATHS),
        ("invalid-status-value", "STATUS_VALUE_INVALID", {export_report: documents[export_report].replace("| `D04-PC059` | `INAPPLICABLE` |", "| `D04-PC059` | `DONE` |", 1)}, {}, DOCUMENT_PATHS),
        ("final-navigation-phase09-regression", "FINAL_NAVIGATION_PHASE09_REGRESSION", {first_doc: documents[first_doc] + "\nPhase 09 为 `IN_PROGRESS`。\n"}, {}, DOCUMENT_PATHS),
        ("final-navigation-publication-regression", "FINAL_NAVIGATION_PUBLICATION_REGRESSION", {first_doc: documents[first_doc] + "\nPhase 09 当前：GitHub Actions、remote clean clone 与 repository publication 仍为 `NOT RUN`。\n"}, {}, DOCUMENT_PATHS),
        ("final-navigation-phase09-multiline-regression", "FINAL_NAVIGATION_PHASE09_REGRESSION", {first_doc: documents[first_doc] + "\nPhase 09\n" + ("long wrapped status context " * 30) + "`IN_PROGRESS`。\n"}, {}, DOCUMENT_PATHS),
        ("final-navigation-publication-multiline-regression", "FINAL_NAVIGATION_PUBLICATION_REGRESSION", {first_doc: documents[first_doc] + "\nGitHub Actions\n" + ("long wrapped status context " * 30) + "`NOT RUN`。\n"}, {}, DOCUMENT_PATHS),
        ("publication-push-failure-token", "REPOSITORY_PUBLICATION_EVIDENCE", {PUBLICATION_RECORD_PATH: _replace_publication_row(confirmed_publication_fixture, "Push", "push FAILED")}, {}, DOCUMENT_PATHS),
        ("publication-run-id-url-mismatch", "REPOSITORY_PUBLICATION_EVIDENCE", {PUBLICATION_RECORD_PATH: _replace_publication_row(confirmed_publication_fixture, "Actions run ID", "999")}, {}, DOCUMENT_PATHS),
        ("publication-job-conflict", "REPOSITORY_PUBLICATION_EVIDENCE", {PUBLICATION_RECORD_PATH: _replace_publication_row(confirmed_publication_fixture, "Ubuntu job", "success / failure")}, {}, DOCUMENT_PATHS),
        ("publication-clone-exit-conflict", "REPOSITORY_PUBLICATION_EVIDENCE", {PUBLICATION_RECORD_PATH: _replace_publication_row(confirmed_publication_fixture, "一键复现", "exit 0 / exit 1")}, {}, DOCUMENT_PATHS),
        ("publication-duplicate-conflicting-row", "REPOSITORY_PUBLICATION_EVIDENCE", {PUBLICATION_RECORD_PATH: _duplicate_publication_row(confirmed_publication_fixture, "Push", "NOT RUN")}, {}, DOCUMENT_PATHS),
        ("publication-current-section-missing", "REPOSITORY_PUBLICATION_EVIDENCE", {PUBLICATION_RECORD_PATH: _rename_current_candidate_section(publication_record)}, {}, DOCUMENT_PATHS),
        ("zero-discovery", "DOC_ZERO_DISCOVERY", {}, {}, ()),
        ("mermaid-missing-node", "MERMAID_NODE_MISSING", {}, {metadata_diagram: _remove_node(diagrams[metadata_diagram], "Provider")}, DOCUMENT_PATHS),
        ("mermaid-node-only-in-comment", "MERMAID_NODE_MISSING", {}, {metadata_diagram: _remove_node(diagrams[metadata_diagram], "Provider") + "\n%% Provider[comment-only decoy]\n"}, DOCUMENT_PATHS),
        ("mermaid-node-only-in-label", "MERMAID_NODE_MISSING", {}, {metadata_diagram: _remove_node(diagrams[metadata_diagram], "Provider") + "\nDecoy[\"Provider[quoted decoy]\"]\n"}, DOCUMENT_PATHS),
        ("mermaid-missing-edge", "MERMAID_EDGE_MISSING", {}, {metadata_diagram: _remove_edge(diagrams[metadata_diagram], "Provider", "DatasetV04")}, DOCUMENT_PATHS),
        ("mermaid-edge-only-in-comment", "MERMAID_EDGE_MISSING", {}, {metadata_diagram: _remove_edge(diagrams[metadata_diagram], "Provider", "DatasetV04") + "\n%% Provider --> DatasetV04\n"}, DOCUMENT_PATHS),
        ("mermaid-edge-only-in-label", "MERMAID_EDGE_MISSING", {}, {metadata_diagram: _remove_edge(diagrams[metadata_diagram], "Provider", "DatasetV04") + "\nDecoy[\"Provider --> DatasetV04\"]\n"}, DOCUMENT_PATHS),
        ("treehouse-raw-preflight-as-pass", "TREEHOUSE_STATUS_MISMATCH", {treehouse_usage: _replace_treehouse_status(documents[treehouse_usage], "Semantic Treehouse raw upstream compose preflight", "BLOCKED", "PASS")}, {}, DOCUMENT_PATHS),
        ("treehouse-build-attempt-as-pass", "TREEHOUSE_STATUS_MISMATCH", {treehouse_usage: _replace_treehouse_status(documents[treehouse_usage], "Semantic Treehouse image build attempt", "BLOCKED", "PASS")}, {}, DOCUMENT_PATHS),
        ("treehouse-deployment-as-pass", "TREEHOUSE_STATUS_MISMATCH", {treehouse_usage: _replace_treehouse_status(documents[treehouse_usage], "Semantic Treehouse deployment", "NOT DEPLOYED", "PASS")}, {}, DOCUMENT_PATHS),
        ("treehouse-historical-workload-as-pass", "TREEHOUSE_STATUS_MISMATCH", {treehouse_usage: _replace_treehouse_status(documents[treehouse_usage], "Semantic Treehouse workload/container execution", "NOT RUN", "PASS")}, {}, DOCUMENT_PATHS),
        ("treehouse-historical-migration-as-pass", "TREEHOUSE_STATUS_MISMATCH", {treehouse_usage: _replace_treehouse_status(documents[treehouse_usage], "Semantic Treehouse database migration", "NOT RUN", "PASS")}, {}, DOCUMENT_PATHS),
        ("treehouse-historical-ui-as-pass", "TREEHOUSE_STATUS_MISMATCH", {treehouse_usage: _replace_treehouse_status(documents[treehouse_usage], "Semantic Treehouse UI workflow", "NOT RUN", "PASS")}, {}, DOCUMENT_PATHS),
        ("treehouse-historical-import-as-pass", "TREEHOUSE_STATUS_MISMATCH", {treehouse_usage: _replace_treehouse_status(documents[treehouse_usage], "Semantic Treehouse model import", "NOT RUN", "PASS")}, {}, DOCUMENT_PATHS),
        ("treehouse-historical-export-as-pass", "TREEHOUSE_STATUS_MISMATCH", {treehouse_usage: _replace_treehouse_status(documents[treehouse_usage], "Semantic Treehouse export", "NOT RUN", "PASS")}, {}, DOCUMENT_PATHS),
        ("treehouse-publication-as-pass", "TREEHOUSE_STATUS_MISMATCH", {treehouse_usage: _replace_treehouse_status(documents[treehouse_usage], "Semantic Treehouse publication", "NOT RUN", "PASS")}, {}, DOCUMENT_PATHS),
        ("treehouse-prepareonly-demoted", "TREEHOUSE_STATUS_MISMATCH", {treehouse_usage: _replace_treehouse_status(documents[treehouse_usage], "Semantic Treehouse PrepareOnly runtime boundary", "PASS", "NOT RUN")}, {}, DOCUMENT_PATHS),
        ("not-run-completion-contradiction", "FALSE_COMPLETION_STATUS", {treehouse_usage: _replace_treehouse_status(documents[treehouse_usage], "Semantic Treehouse UI workflow", "NOT RUN", "NOT RUN / DONE")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-checkout-demoted", "TREEHOUSE_STATUS_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_status(treehouse_current_documents[treehouse_scoped_summary], "checkout", "PASS", "NOT RUN")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-raw-preflight-as-pass", "TREEHOUSE_STATUS_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_status(treehouse_current_documents[treehouse_scoped_summary], "raw preflight", "BLOCKED", "PASS")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-opt-in-demoted", "TREEHOUSE_STATUS_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_status(treehouse_current_documents[treehouse_scoped_summary], "opt-in", "APPROVED", "NOT RUN")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-prepareonly-demoted", "TREEHOUSE_STATUS_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_status(treehouse_current_documents[treehouse_scoped_summary], "PrepareOnly", "PASS", "NOT RUN")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-image-build-demoted", "TREEHOUSE_STATUS_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_status(treehouse_current_documents[treehouse_scoped_summary], "image build", "PASS", "BLOCKED")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-deployment-demoted", "TREEHOUSE_STATUS_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_status(treehouse_current_documents[treehouse_scoped_summary], "deployment", "PASS", "NOT DEPLOYED")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-workload-demoted", "TREEHOUSE_STATUS_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_status(treehouse_current_documents[treehouse_scoped_summary], "workload", "PASS", "NOT RUN")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-migration-demoted", "TREEHOUSE_STATUS_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_status(treehouse_current_documents[treehouse_scoped_summary], "database migration", "PASS", "NOT RUN")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-runtime-demoted", "TREEHOUSE_STATUS_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_status(treehouse_current_documents[treehouse_scoped_summary], "current runtime", "PAUSED", "RUNNING")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-root-smoke-demoted", "TREEHOUSE_STATUS_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_status(treehouse_current_documents[treehouse_scoped_summary], "root loopback smoke", "PASS", "NOT RUN")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-api-generalized", "TREEHOUSE_STATUS_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_token(treehouse_current_documents[treehouse_scoped_summary], "`API loopback availability smoke=PASS`", "`API=PASS`")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-ui-demoted", "TREEHOUSE_STATUS_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_status(treehouse_current_documents[treehouse_scoped_summary], "UI workflow", "PASS", "NOT RUN")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-import-demoted", "TREEHOUSE_STATUS_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_status(treehouse_current_documents[treehouse_scoped_summary], "model import", "PASS", "NOT RUN")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-export-demoted", "TREEHOUSE_STATUS_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_status(treehouse_current_documents[treehouse_scoped_summary], "export", "PASS", "NOT RUN")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-publication-as-pass", "TREEHOUSE_STATUS_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_status(treehouse_current_documents[treehouse_scoped_summary], "publication", "NOT RUN", "PASS")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-shacl-validator-demoted", "TREEHOUSE_STATUS_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_status(treehouse_current_documents[treehouse_scoped_summary], "SHACL validator execution", "PASS", "NOT RUN")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-evidence-replaced", "TREEHOUSE_EVIDENCE_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_token(treehouse_current_documents[treehouse_scoped_summary], f"`{TREEHOUSE_RECOVERY_EVIDENCE_PATHS[0]}`", "`build/evidence/treehouse/missing-recovery-evidence.json`")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-evidence-duplicated", "TREEHOUSE_EVIDENCE_MISMATCH", {treehouse_scoped_summary: treehouse_current_documents[treehouse_scoped_summary] + f"\n`{TREEHOUSE_RECOVERY_EVIDENCE_PATHS[0]}`\n"}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-validator-evidence-replaced", "TREEHOUSE_EVIDENCE_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_token(treehouse_current_documents[treehouse_scoped_summary], f"`{TREEHOUSE_RECOVERY_EVIDENCE_PATHS[4]}`", "`build/evidence/treehouse/missing-validator-execution-evidence.json`")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-validator-recheck-evidence-replaced", "TREEHOUSE_EVIDENCE_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_token(treehouse_current_documents[treehouse_scoped_summary], f"`{TREEHOUSE_RECOVERY_EVIDENCE_PATHS[5]}`", "`build/evidence/treehouse/missing-validator-recheck-evidence.json`")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-runtime-pause-evidence-replaced", "TREEHOUSE_EVIDENCE_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_token(treehouse_current_documents[treehouse_scoped_summary], f"`{TREEHOUSE_RECOVERY_EVIDENCE_PATHS[6]}`", "`build/evidence/treehouse/missing-runtime-pause-evidence.json`")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-validator-digest-drift", "TREEHOUSE_RUNTIME_BOUNDARY_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_token(treehouse_current_documents[treehouse_scoped_summary], CURRENT_TREEHOUSE_SCOPED_BOUNDARY_TOKENS[0], "`SHACL validator manifest digest=DRIFTED`")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-validator-security-demoted", "TREEHOUSE_RUNTIME_BOUNDARY_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_token(treehouse_current_documents[treehouse_scoped_summary], CURRENT_TREEHOUSE_SCOPED_BOUNDARY_TOKENS[1], "`SHACL validator security boundary=host-exposed`")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-validator-controls-demoted", "TREEHOUSE_RUNTIME_BOUNDARY_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_token(treehouse_current_documents[treehouse_scoped_summary], CURRENT_TREEHOUSE_SCOPED_BOUNDARY_TOKENS[2], "`SHACL validation controls=positive-only`")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-paused-persistence-demoted", "TREEHOUSE_RUNTIME_BOUNDARY_MISMATCH", {treehouse_scoped_summary: _replace_treehouse_scoped_token(treehouse_current_documents[treehouse_scoped_summary], CURRENT_TREEHOUSE_SCOPED_BOUNDARY_TOKENS[3], "`PAUSED persistence=volumes-removed`")}, {}, DOCUMENT_PATHS),
        ("treehouse-scoped-status-duplicated", "TREEHOUSE_STATUS_MISMATCH", {treehouse_scoped_summary: treehouse_current_documents[treehouse_scoped_summary] + "\n`deployment=PASS`\n"}, {}, DOCUMENT_PATHS),
    ]

    control_results: list[dict[str, Any]] = []
    fixture_dir = root / "build/phase-07/documentation-negative-controls"
    for control_id, expected_code, doc_override, diagram_override, paths in controls:
        result = _evaluate(
            root,
            paths,
            doc_override,
            diagram_override,
            command=self_test_command,
        )
        codes = sorted({issue["code"] for issue in result["issues"]})
        actual_exit_code = _exit_code(result)
        passed = actual_exit_code != 0 and expected_code in codes
        snippet_parts = list(doc_override.values()) + list(diagram_override.values())
        snippet = (snippet_parts[0] if snippet_parts else "<zero discovered documents>\n")
        fixture_path = fixture_dir / f"{control_id}.txt"
        _write_text(fixture_path, snippet if snippet.endswith("\n") else snippet + "\n")
        fixture_bytes = fixture_path.read_bytes()
        control_results.append(
            {
                "id": control_id,
                "expected_issue_code": expected_code,
                "expected_exit_code": "nonzero",
                "actual_exit_code": actual_exit_code,
                "observed_issue_codes": codes,
                "input_evidence": str(fixture_path.relative_to(root)).replace("\\", "/"),
                "input_evidence_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
                "input_evidence_bytes": len(fixture_bytes),
                "target_paths": sorted(set(doc_override) | set(diagram_override)),
                "override_sha256": {
                    path: hashlib.sha256(value.encode("utf-8")).hexdigest()
                    for path, value in sorted({**doc_override, **diagram_override}.items())
                },
                "status": "PASS" if passed else "FAIL",
            }
        )

    control_results.extend(
        _venv_command_contract_controls(root, documents, suite_ids, fixture_dir)
    )

    passed_count = sum(item["status"] == "PASS" for item in control_results)
    self_test = {
        "schema_version": "1.0.0",
        "check_id": CHECK_ID,
        "canonical_status": canonical["status"],
        "counts": {
            "discovered": len(control_results),
            "executed": len(control_results),
            "passed": passed_count,
            "failed": len(control_results) - passed_count,
            "skipped": 0,
        },
        "controls": control_results,
        "status": "PASS" if canonical["status"] == "PASS" and passed_count == len(control_results) else "FAIL",
    }
    self_test["program_status"] = "SUCCESS" if self_test["status"] == "PASS" else "ERROR"
    _write_json(root / "build/phase-07/documentation-negative-controls.json", self_test)
    return self_test


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run all in-memory negative controls after the canonical check")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.self_test:
        result = run_self_test(ROOT)
        print(
            f"documentation self-test status={result['status']} "
            f"passed={result['counts']['passed']}/{result['counts']['executed']} "
            "result=build/phase-07/documentation-negative-controls.json"
        )
        return _exit_code(result)
    result = run_canonical(ROOT, command=_standalone_command())
    print(
        f"documentation check status={result['status']} program_status={result['program_status']} "
        f"documents={result['counts']['documents']} diagrams={result['counts']['diagrams']} "
        "result=build/validation/documentation/results.json"
    )
    return _exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main())
