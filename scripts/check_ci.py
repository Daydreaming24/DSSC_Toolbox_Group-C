#!/usr/bin/env python3
"""Deterministic GitHub Actions policy checker for Phase 08.

The functions named ``check_*_policy`` form the reusable, trigger-agnostic
policy API.  ``check_validate_profile`` adds only the three-trigger and
three-job contract for ``.github/workflows/validate.yml``.  A future release
workflow can therefore import the common predicates while supplying its own,
narrower trigger and job profile.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode


__all__ = [
    "PolicyIssue",
    "load_workflow_text",
    "check_permissions_policy",
    "check_action_pins_policy",
    "check_checkout_policy",
    "check_runner_policy",
    "check_timeout_policy",
    "check_shell_policy",
    "check_artifact_policy",
    "check_common_workflow_policy",
    "check_validate_triggers",
    "check_validate_profile",
    "evaluate_workflow_policy",
    "build_policy_report",
]


POLICY_SCHEMA = "dssc.ci-policy.result.v1"
SELF_TEST_SCHEMA = "dssc.ci-policy.self-test.v1"
MACHINE_SCHEMA = "dssc.ci-policy.machine.v1"
VALIDATE_PROFILE = "validate"

REQUIRED_TRIGGERS = ("push", "pull_request", "workflow_dispatch")
APPROVED_BRANCHES = ("main",)
REQUIRED_JOBS = (
    "ubuntu-native",
    "windows-powershell",
    "docker-clean-room",
)
EXPECTED_RUNNERS = {
    "ubuntu-native": "ubuntu-24.04",
    "windows-powershell": "windows-2022",
    "docker-clean-room": "ubuntu-24.04",
}
EXPECTED_SHELLS = {
    "ubuntu-native": "bash",
    "windows-powershell": "powershell",
    "docker-clean-room": "bash",
}
PUBLIC_SUITES = (
    "frozen",
    "environment",
    "baseline",
    "traceability",
    "v0.4-model",
    "v0.4",
    "all",
)

_ACTION_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_ACTION_VERSION_COMMENT_RE = re.compile(r"#\s*v\d+\.\d+(?:\.\d+)?(?:\s|$)")
_UNTRUSTED_RUN_EXPRESSION_RE = re.compile(
    r"\$\{\{\s*(?:inputs\.|github\.event\.inputs(?:\.|\s|\}\})|"
    r"github\.event\.pull_request\.(?:title|body|head\.ref)|"
    r"github\.event\.(?:issue|comment|discussion)|secrets\.)",
    re.IGNORECASE,
)


@dataclass(frozen=True, order=True)
class PolicyIssue:
    """One deterministic policy violation."""

    code: str
    location: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "location": self.location,
            "message": self.message,
        }


class GitHubActionsLoader(yaml.SafeLoader):
    """PyYAML SafeLoader with YAML 1.2-like booleans and duplicate rejection."""


# PyYAML's YAML 1.1 resolver treats the GitHub key ``on`` as boolean true.
# Copy the resolver table before narrowing booleans so the global SafeLoader is
# not modified for callers that import this module.
GitHubActionsLoader.yaml_implicit_resolvers = copy.deepcopy(
    yaml.SafeLoader.yaml_implicit_resolvers
)
for _resolver_key, _resolvers in list(
    GitHubActionsLoader.yaml_implicit_resolvers.items()
):
    GitHubActionsLoader.yaml_implicit_resolvers[_resolver_key] = [
        entry for entry in _resolvers if entry[0] != "tag:yaml.org,2002:bool"
    ]
GitHubActionsLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


def _construct_unique_mapping(
    loader: GitHubActionsLoader, node: MappingNode, deep: bool = False
) -> dict[Any, Any]:
    if not isinstance(node, MappingNode):
        raise ConstructorError(
            None,
            None,
            f"expected a mapping node, found {node.id}",
            node.start_mark,
        )
    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable key",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


GitHubActionsLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def repository_root() -> Path:
    return Path(__file__).resolve().parent.parent


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_workflow_text(source_text: str) -> Mapping[str, Any]:
    """Parse workflow YAML safely, preserving ``on`` and rejecting duplicates."""

    loaded = yaml.load(source_text, Loader=GitHubActionsLoader)
    if not isinstance(loaded, Mapping):
        raise ValueError("workflow document must be a mapping")
    return loaded


def _jobs(workflow: Mapping[str, Any]) -> Mapping[str, Any]:
    jobs = workflow.get("jobs")
    return jobs if isinstance(jobs, Mapping) else {}


def _steps(job: Any) -> list[Mapping[str, Any]]:
    if not isinstance(job, Mapping):
        return []
    steps = job.get("steps")
    if not isinstance(steps, Sequence) or isinstance(steps, (str, bytes)):
        return []
    return [step for step in steps if isinstance(step, Mapping)]


def _iter_steps(
    workflow: Mapping[str, Any],
) -> list[tuple[str, int, Mapping[str, Any]]]:
    result: list[tuple[str, int, Mapping[str, Any]]] = []
    for job_id, job in _jobs(workflow).items():
        if not isinstance(job_id, str):
            continue
        for index, step in enumerate(_steps(job)):
            result.append((job_id, index, step))
    return result


def _step_location(job_id: str, index: int) -> str:
    return f"jobs.{job_id}.steps[{index}]"


def _action_name(uses: str) -> str:
    return uses.split("@", 1)[0]


def _is_remote_github_action(uses: str) -> bool:
    return not uses.startswith(("./", "../", "docker://"))


def _always_expression(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = re.sub(r"\s+", "", value).lower()
    return normalized in ("always()", "${{always()}}")


def check_permissions_policy(
    workflow: Mapping[str, Any],
    *,
    allowed: Mapping[str, str] | None = None,
    exact: bool = True,
) -> list[PolicyIssue]:
    """Require an explicit least-privilege workflow and job permission map."""

    expected = dict(allowed or {"contents": "read"})
    issues: list[PolicyIssue] = []

    def inspect(value: Any, location: str) -> None:
        if not isinstance(value, Mapping):
            issues.append(
                PolicyIssue(
                    "permissions.missing",
                    location,
                    "permissions must be an explicit mapping",
                )
            )
            return
        actual = dict(value)
        for scope, level in actual.items():
            if level == "write" or str(level).endswith("write"):
                issues.append(
                    PolicyIssue(
                        "permissions.write",
                        f"{location}.{scope}",
                        "write permission is forbidden by this policy",
                    )
                )
        if exact and actual != expected:
            issues.append(
                PolicyIssue(
                    "permissions.not_exact",
                    location,
                    f"permissions must equal {expected!r}",
                )
            )
        elif not exact:
            for scope, level in expected.items():
                if actual.get(scope) != level:
                    issues.append(
                        PolicyIssue(
                            "permissions.required_scope",
                            f"{location}.{scope}",
                            f"permission must be {level!r}",
                        )
                    )

    inspect(workflow.get("permissions"), "permissions")
    for job_id, job in _jobs(workflow).items():
        if isinstance(job, Mapping) and "permissions" in job:
            inspect(job.get("permissions"), f"jobs.{job_id}.permissions")
    return issues


def check_action_pins_policy(
    workflow: Mapping[str, Any],
    source_text: str,
    *,
    require_version_comments: bool = True,
) -> list[PolicyIssue]:
    """Require immutable remote action SHAs and human-readable version comments."""

    issues: list[PolicyIssue] = []
    for job_id, index, step in _iter_steps(workflow):
        uses = step.get("uses")
        if uses is None:
            continue
        location = _step_location(job_id, index) + ".uses"
        if not isinstance(uses, str) or not uses:
            issues.append(
                PolicyIssue("action.invalid", location, "uses must be a string")
            )
            continue
        if "${{" in uses:
            issues.append(
                PolicyIssue(
                    "action.dynamic",
                    location,
                    "action references must not contain expressions",
                )
            )
            continue
        if uses.startswith(("./", "../")):
            continue
        if uses.startswith("docker://"):
            if not re.search(r"@sha256:[0-9a-f]{64}$", uses):
                issues.append(
                    PolicyIssue(
                        "action.unpinned",
                        location,
                        "docker actions must use a sha256 digest",
                    )
                )
            continue
        if "@" not in uses or not _ACTION_SHA_RE.fullmatch(uses.rsplit("@", 1)[1]):
            issues.append(
                PolicyIssue(
                    "action.unpinned",
                    location,
                    "remote actions must use a full 40-character commit SHA",
                )
            )

    if require_version_comments:
        for line_number, line in enumerate(source_text.splitlines(), start=1):
            match = re.match(r"^\s*uses:\s*([^\s#]+)", line)
            if not match:
                continue
            uses = match.group(1).strip("'\"")
            if _is_remote_github_action(uses) and not _ACTION_VERSION_COMMENT_RE.search(
                line
            ):
                issues.append(
                    PolicyIssue(
                        "action.version_comment",
                        f"line:{line_number}",
                        "remote action pins require an inline release-version comment",
                    )
                )
    return issues


def check_checkout_policy(
    workflow: Mapping[str, Any], *, require_each_job: bool = True
) -> list[PolicyIssue]:
    """Require checkout in each job with credential persistence disabled."""

    issues: list[PolicyIssue] = []
    for job_id, job in _jobs(workflow).items():
        checkouts: list[tuple[int, Mapping[str, Any]]] = []
        for index, step in enumerate(_steps(job)):
            uses = step.get("uses")
            if isinstance(uses, str) and _action_name(uses) == "actions/checkout":
                checkouts.append((index, step))
        if require_each_job and not checkouts:
            issues.append(
                PolicyIssue(
                    "checkout.missing",
                    f"jobs.{job_id}",
                    "each validation job must check out the repository",
                )
            )
        for index, step in checkouts:
            location = _step_location(str(job_id), index)
            options = step.get("with")
            persist = options.get("persist-credentials") if isinstance(options, Mapping) else None
            if persist is not False:
                issues.append(
                    PolicyIssue(
                        "checkout.persist_credentials",
                        f"{location}.with.persist-credentials",
                        "persist-credentials must be the boolean false",
                    )
                )
    return issues


def check_runner_policy(
    workflow: Mapping[str, Any],
    *,
    allowed_runners: Mapping[str, str] | None = None,
) -> list[PolicyIssue]:
    """Require static runner labels and reject floating ``*-latest`` labels."""

    issues: list[PolicyIssue] = []
    for job_id, job in _jobs(workflow).items():
        location = f"jobs.{job_id}.runs-on"
        runner = job.get("runs-on") if isinstance(job, Mapping) else None
        labels: list[str]
        if isinstance(runner, str):
            labels = [runner]
        elif isinstance(runner, Sequence) and not isinstance(runner, (str, bytes)):
            labels = [label for label in runner if isinstance(label, str)]
            if len(labels) != len(runner):
                issues.append(
                    PolicyIssue(
                        "runner.invalid",
                        location,
                        "runner labels must be strings",
                    )
                )
        else:
            labels = []
            issues.append(
                PolicyIssue(
                    "runner.missing", location, "runs-on must be explicit"
                )
            )
        for label in labels:
            if "${{" in label:
                issues.append(
                    PolicyIssue(
                        "runner.dynamic",
                        location,
                        "runner labels must not contain expressions",
                    )
                )
            if label.lower().endswith("-latest"):
                issues.append(
                    PolicyIssue(
                        "runner.latest",
                        location,
                        "floating *-latest runner labels are forbidden",
                    )
                )
        if allowed_runners is not None and allowed_runners.get(str(job_id)) != runner:
            issues.append(
                PolicyIssue(
                    "runner.profile",
                    location,
                    f"runner must equal {allowed_runners.get(str(job_id))!r}",
                )
            )
    return issues


def check_timeout_policy(
    workflow: Mapping[str, Any],
    *,
    maximum_minutes: int = 30,
    exact_minutes: int | None = None,
) -> list[PolicyIssue]:
    """Require bounded integer timeouts on every job."""

    issues: list[PolicyIssue] = []
    for job_id, job in _jobs(workflow).items():
        location = f"jobs.{job_id}.timeout-minutes"
        timeout = job.get("timeout-minutes") if isinstance(job, Mapping) else None
        if isinstance(timeout, bool) or not isinstance(timeout, int):
            issues.append(
                PolicyIssue(
                    "timeout.missing",
                    location,
                    "timeout-minutes must be an explicit integer",
                )
            )
            continue
        if timeout < 1 or timeout > maximum_minutes:
            issues.append(
                PolicyIssue(
                    "timeout.out_of_range",
                    location,
                    f"timeout must be between 1 and {maximum_minutes} minutes",
                )
            )
        if exact_minutes is not None and timeout != exact_minutes:
            issues.append(
                PolicyIssue(
                    "timeout.profile",
                    location,
                    f"timeout must equal {exact_minutes} minutes",
                )
            )
    return issues


def check_shell_policy(
    workflow: Mapping[str, Any],
    *,
    allowed_shells: Sequence[str] = ("bash", "powershell", "pwsh"),
    expected_shells: Mapping[str, str] | None = None,
) -> list[PolicyIssue]:
    """Require explicit static shells and reject untrusted expression splicing."""

    allowed = set(allowed_shells)
    issues: list[PolicyIssue] = []
    for job_id, index, step in _iter_steps(workflow):
        run = step.get("run")
        if run is None:
            continue
        location = _step_location(job_id, index)
        if not isinstance(run, str) or not run.strip():
            issues.append(
                PolicyIssue(
                    "shell.empty_run", f"{location}.run", "run must be non-empty"
                )
            )
            continue
        shell = step.get("shell")
        if not isinstance(shell, str) or not shell:
            issues.append(
                PolicyIssue(
                    "shell.missing",
                    f"{location}.shell",
                    "every run step must select an explicit shell",
                )
            )
        else:
            if "${{" in shell or shell not in allowed:
                issues.append(
                    PolicyIssue(
                        "shell.unsafe",
                        f"{location}.shell",
                        f"shell must be one of {sorted(allowed)!r}",
                    )
                )
            if expected_shells is not None and shell != expected_shells.get(job_id):
                issues.append(
                    PolicyIssue(
                        "shell.profile",
                        f"{location}.shell",
                        f"shell must equal {expected_shells.get(job_id)!r}",
                    )
                )
        if _UNTRUSTED_RUN_EXPRESSION_RE.search(run):
            issues.append(
                PolicyIssue(
                    "shell.untrusted_expression",
                    f"{location}.run",
                    "untrusted dispatch, PR text, or secret expressions must not "
                    "be spliced into run",
                )
            )
    return issues


def _artifact_paths(value: Any) -> list[str]:
    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def check_artifact_policy(
    workflow: Mapping[str, Any],
    *,
    require_each_job: bool = True,
    allowed_prefix: str = "build/",
) -> list[PolicyIssue]:
    """Require fail-closed, unconditional uploads of scoped machine evidence."""

    issues: list[PolicyIssue] = []
    for job_id, job in _jobs(workflow).items():
        uploads: list[tuple[int, Mapping[str, Any]]] = []
        for index, step in enumerate(_steps(job)):
            uses = step.get("uses")
            if isinstance(uses, str) and _action_name(uses) == "actions/upload-artifact":
                uploads.append((index, step))
        if require_each_job and not uploads:
            issues.append(
                PolicyIssue(
                    "artifact.missing",
                    f"jobs.{job_id}",
                    "each validation job must upload evidence",
                )
            )
        for index, step in uploads:
            location = _step_location(str(job_id), index)
            if not _always_expression(step.get("if")):
                issues.append(
                    PolicyIssue(
                        "artifact.always",
                        f"{location}.if",
                        "artifact upload must use if: always()",
                    )
                )
            options = step.get("with")
            if not isinstance(options, Mapping):
                issues.append(
                    PolicyIssue(
                        "artifact.options",
                        f"{location}.with",
                        "artifact upload options must be a mapping",
                    )
                )
                continue
            if options.get("if-no-files-found") != "error":
                issues.append(
                    PolicyIssue(
                        "artifact.if_no_files",
                        f"{location}.with.if-no-files-found",
                        "if-no-files-found must be error",
                    )
                )
            if options.get("include-hidden-files") is True:
                issues.append(
                    PolicyIssue(
                        "artifact.hidden_files",
                        f"{location}.with.include-hidden-files",
                        "hidden-file uploads are forbidden",
                    )
                )
            paths = _artifact_paths(options.get("path"))
            if not paths:
                issues.append(
                    PolicyIssue(
                        "artifact.path",
                        f"{location}.with.path",
                        "artifact path must be non-empty",
                    )
                )
                continue
            normalized_paths = [path.replace("\\", "/") for path in paths]
            for path, normalized in zip(paths, normalized_paths, strict=True):
                if (
                    not normalized.startswith(allowed_prefix)
                    or normalized.startswith("/")
                    or ".." in Path(normalized).parts
                    or normalized.startswith("!")
                ):
                    issues.append(
                        PolicyIssue(
                            "artifact.path_scope",
                            f"{location}.with.path",
                            f"artifact path must remain under {allowed_prefix!r}: {path!r}",
                        )
                    )
            normalized_prefix = allowed_prefix.replace("\\", "/").rstrip("/") + "/"
            required_json_pattern = normalized_prefix + "**/*.json"
            required_markdown_pattern = normalized_prefix + "**/*.md"
            coverage = {
                "all_machine_json": required_json_pattern in normalized_paths,
                "markdown": required_markdown_pattern in normalized_paths,
            }
            missing = sorted(name for name, present in coverage.items() if not present)
            if missing:
                issues.append(
                    PolicyIssue(
                        "artifact.coverage",
                        f"{location}.with.path",
                        "artifact patterns must cover: " + ", ".join(missing),
                    )
                )
    return issues


def check_fail_closed_policy(workflow: Mapping[str, Any]) -> list[PolicyIssue]:
    """Reject weakened jobs and core steps."""

    issues: list[PolicyIssue] = []
    for job_id, job in _jobs(workflow).items():
        if not isinstance(job, Mapping):
            continue
        if "continue-on-error" in job:
            issues.append(
                PolicyIssue(
                    "job.continue_on_error",
                    f"jobs.{job_id}.continue-on-error",
                    "continue-on-error must be absent from fail-closed jobs",
                )
            )
        if "if" in job:
            issues.append(
                PolicyIssue(
                    "job.conditional",
                    f"jobs.{job_id}.if",
                    "required validation jobs must not be conditionally skipped",
                )
            )
        for index, step in enumerate(_steps(job)):
            location = _step_location(str(job_id), index)
            if "continue-on-error" in step:
                issues.append(
                    PolicyIssue(
                        "step.continue_on_error",
                        f"{location}.continue-on-error",
                        "continue-on-error must be absent from fail-closed steps",
                    )
                )
            if "run" in step and "if" in step and not _always_expression(step.get("if")):
                issues.append(
                    PolicyIssue(
                        "step.conditional_run",
                        f"{location}.if",
                        "run steps must not use a skip-capable condition",
                    )
                )
    return issues


def check_no_secrets_policy(workflow: Mapping[str, Any]) -> list[PolicyIssue]:
    """Reject repository secret and protected-environment dependencies."""

    issues: list[PolicyIssue] = []

    def walk(value: Any, location: str) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                child_location = f"{location}.{key}" if location else str(key)
                if str(key).lower() == "secrets":
                    issues.append(
                        PolicyIssue(
                            "secrets.dependency",
                            child_location,
                            "workflow secrets are forbidden",
                        )
                    )
                walk(child, child_location)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for index, child in enumerate(value):
                walk(child, f"{location}[{index}]")
        elif isinstance(value, str) and re.search(
            r"\$\{\{\s*secrets\.", value, re.IGNORECASE
        ):
            issues.append(
                PolicyIssue(
                    "secrets.expression",
                    location,
                    "secret expressions are forbidden",
                )
            )

    walk(workflow, "")
    for job_id, job in _jobs(workflow).items():
        if isinstance(job, Mapping) and "environment" in job:
            issues.append(
                PolicyIssue(
                    "secrets.environment",
                    f"jobs.{job_id}.environment",
                    "protected GitHub environments are not part of validation",
                )
            )
    return issues


def check_concurrency_policy(workflow: Mapping[str, Any]) -> list[PolicyIssue]:
    """Require workflow-level cancellation of superseded validation runs."""

    concurrency = workflow.get("concurrency")
    if not isinstance(concurrency, Mapping):
        return [
            PolicyIssue(
                "concurrency.missing",
                "concurrency",
                "workflow concurrency must be an explicit mapping",
            )
        ]
    issues: list[PolicyIssue] = []
    group = concurrency.get("group")
    if not isinstance(group, str) or not group.strip():
        issues.append(
            PolicyIssue(
                "concurrency.group",
                "concurrency.group",
                "concurrency group must be a non-empty string",
            )
        )
    elif re.search(r"(?:inputs\.|github\.event\.inputs)", group, re.IGNORECASE):
        issues.append(
            PolicyIssue(
                "concurrency.untrusted_group",
                "concurrency.group",
                "dispatch inputs must not select the concurrency group",
            )
        )
    if concurrency.get("cancel-in-progress") is not True:
        issues.append(
            PolicyIssue(
                "concurrency.cancel",
                "concurrency.cancel-in-progress",
                "cancel-in-progress must be the boolean true",
            )
        )
    return issues


def check_common_workflow_policy(
    workflow: Mapping[str, Any], source_text: str
) -> list[PolicyIssue]:
    """Run reusable policy predicates without imposing a trigger profile."""

    issues: list[PolicyIssue] = []
    predicates: tuple[Callable[[], list[PolicyIssue]], ...] = (
        lambda: check_permissions_policy(workflow),
        lambda: check_action_pins_policy(workflow, source_text),
        lambda: check_checkout_policy(workflow),
        lambda: check_runner_policy(workflow),
        lambda: check_timeout_policy(workflow),
        lambda: check_shell_policy(workflow),
        lambda: check_artifact_policy(workflow),
        lambda: check_fail_closed_policy(workflow),
        lambda: check_no_secrets_policy(workflow),
        lambda: check_concurrency_policy(workflow),
    )
    for predicate in predicates:
        issues.extend(predicate())
    return sorted(set(issues))


def _validate_branch_trigger(name: str, value: Any) -> list[PolicyIssue]:
    location = f"on.{name}"
    if not isinstance(value, Mapping):
        return [
            PolicyIssue(
                "trigger.branch_filter.missing",
                location,
                f"{name} must define an approved branches filter",
            )
        ]
    issues: list[PolicyIssue] = []
    if "branches-ignore" in value:
        issues.append(
            PolicyIssue(
                "trigger.branch_filter.unsafe",
                f"{location}.branches-ignore",
                "branches-ignore is forbidden for the validation profile",
            )
        )
    branches = value.get("branches")
    if not isinstance(branches, Sequence) or isinstance(branches, (str, bytes)):
        issues.append(
            PolicyIssue(
                "trigger.branch_filter.missing",
                f"{location}.branches",
                "branches must be an explicit list",
            )
        )
    else:
        actual = tuple(branches)
        if actual != APPROVED_BRANCHES:
            issues.append(
                PolicyIssue(
                    "trigger.branch_filter.unsafe",
                    f"{location}.branches",
                    f"branches must equal {list(APPROVED_BRANCHES)!r}",
                )
            )
        for branch in actual:
            if not isinstance(branch, str) or re.search(r"[*?\[\]!]", branch):
                issues.append(
                    PolicyIssue(
                        "trigger.branch_filter.unsafe",
                        f"{location}.branches",
                        "wildcards, negation, and non-string branch rules are forbidden",
                    )
                )
                break
    extra = sorted(set(value) - {"branches"}, key=lambda item: repr(item))
    if extra:
        issues.append(
            PolicyIssue(
                "trigger.branch_filter.unsafe",
                location,
                "unsupported trigger filters: " + ", ".join(map(str, extra)),
            )
        )
    return issues


def check_validate_triggers(workflow: Mapping[str, Any]) -> list[PolicyIssue]:
    """Apply only the approved validate.yml trigger and branch profile."""

    triggers = workflow.get("on")
    if not isinstance(triggers, Mapping):
        return [
            PolicyIssue(
                "trigger.missing",
                "on",
                "on must be a mapping with three approved triggers",
            )
        ]
    issues: list[PolicyIssue] = []
    actual = set(triggers)
    required = set(REQUIRED_TRIGGERS)
    for missing in sorted(required - actual):
        issues.append(
            PolicyIssue(
                "trigger.required",
                f"on.{missing}",
                f"required trigger {missing!r} is missing",
            )
        )
    for forbidden in sorted(actual - required, key=lambda item: repr(item)):
        code = (
            "trigger.forbidden"
            if forbidden in ("pull_request_target", "workflow_run")
            else "trigger.unapproved"
        )
        issues.append(
            PolicyIssue(
                code,
                f"on.{forbidden}",
                f"trigger {forbidden!r} is not approved",
            )
        )
    for trigger_name in ("push", "pull_request"):
        if trigger_name in triggers:
            issues.extend(_validate_branch_trigger(trigger_name, triggers[trigger_name]))
    dispatch = triggers.get("workflow_dispatch")
    if "workflow_dispatch" in triggers and dispatch not in (None, {}):
        issues.append(
            PolicyIssue(
                "trigger.dispatch_inputs",
                "on.workflow_dispatch",
                "validate.yml workflow_dispatch must not define inputs",
            )
        )
    return issues


@dataclass(frozen=True)
class _CanonicalRunStep:
    identity: str
    name: str
    shell: str
    run: str
    issue_code: str


_CHECKOUT_USES = (
    "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683"
)
_SETUP_PYTHON_USES = (
    "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065"
)
_UPLOAD_ARTIFACT_USES = (
    "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02"
)
_VALIDATE_WORKFLOW_KEYS = {"name", "on", "permissions", "concurrency", "jobs"}
_VALIDATE_JOB_KEYS = {"name", "runs-on", "timeout-minutes", "steps"}
_EXPECTED_JOB_NAMES = {
    "ubuntu-native": "Ubuntu native Python validation",
    "windows-powershell": "Windows PowerShell 5.1 validation",
    "docker-clean-room": "Docker clean-room validation",
}
_ARTIFACT_PATHS = "\n".join(
    (
        "build/**/*.json",
        "build/**/*.md",
    )
)


_SUITE_STEP_NAMES = {
    "frozen": "Validate frozen",
    "environment": "Validate environment",
    "baseline": "Validate baseline",
    "traceability": "Validate traceability",
    "v0.4-model": "Validate v0.4 model",
    "v0.4": "Validate v0.4 fixtures",
    "all": "Validate complete contract",
}


def _run_block(*lines: str) -> str:
    return "\n".join(lines)


def _canonical_core_steps(job_id: str) -> tuple[_CanonicalRunStep, ...]:
    if job_id == "ubuntu-native":
        return (
            _CanonicalRunStep(
                "bootstrap/hash-lock",
                "Bootstrap from hash locks",
                "bash",
                _run_block(
                    "set -euo pipefail",
                    'PYTHON_PATH="$(command -v python)" '
                    "DOCTOR_PROFILE=host-no-docker ./scripts/bootstrap.sh",
                ),
                "lock.install",
            ),
            _CanonicalRunStep(
                "pip check",
                "Verify installed dependency graph",
                "bash",
                _run_block(
                    "set -euo pipefail",
                    "./.venv/bin/python -I -m pip --isolated "
                    "--disable-pip-version-check check",
                ),
                "lock.pip_check",
            ),
            _CanonicalRunStep(
                "CI normal+self-test",
                "Check CI policy",
                "bash",
                _run_block(
                    "set -euo pipefail",
                    "./.venv/bin/python -I scripts/check_ci.py",
                    "./.venv/bin/python -I scripts/check_ci.py --self-test",
                ),
                "ci.self_test",
            ),
        )
    if job_id == "windows-powershell":
        return (
            _CanonicalRunStep(
                "bootstrap/hash-lock",
                "Bootstrap from hash locks",
                "powershell",
                _run_block(
                    "$ErrorActionPreference = 'Stop'",
                    "$BasePython = (Get-Command python.exe -ErrorAction Stop).Source",
                    r"& .\scripts\bootstrap.ps1 -PythonPath $BasePython "
                    "-DoctorProfile host-no-docker",
                    "if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }",
                ),
                "lock.install",
            ),
            _CanonicalRunStep(
                "pip check",
                "Verify installed dependency graph",
                "powershell",
                _run_block(
                    r"& .\.venv\Scripts\python.exe -I -m pip --isolated "
                    "--disable-pip-version-check check",
                    "exit $LASTEXITCODE",
                ),
                "lock.pip_check",
            ),
            _CanonicalRunStep(
                "CI normal+self-test",
                "Check CI policy",
                "powershell",
                _run_block(
                    r"& .\.venv\Scripts\python.exe -I scripts\check_ci.py",
                    "if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }",
                    r"& .\.venv\Scripts\python.exe -I scripts\check_ci.py --self-test",
                    "exit $LASTEXITCODE",
                ),
                "ci.self_test",
            ),
        )
    if job_id == "docker-clean-room":
        return (
            _CanonicalRunStep(
                "Docker source provenance",
                "Prepare isolated Docker evidence directory",
                "bash",
                _run_block(
                    "set -euo pipefail",
                    "sudo install -d -o 10001 -g 10001 build/ci/docker",
                    'source_commit="$(git rev-parse HEAD)"',
                    'if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then',
                    "  source_dirty=true",
                    "else",
                    "  source_dirty=false",
                    "fi",
                    "{",
                    '  echo "DSSC_SOURCE_COMMIT=$source_commit"',
                    '  echo "DSSC_SOURCE_DIRTY=$source_dirty"',
                    '} >> "$GITHUB_ENV"',
                ),
                "lock.install",
            ),
            _CanonicalRunStep(
                "Docker no-cache hash-lock build",
                "Build fixed validation image without cache",
                "bash",
                _run_block(
                    "set -euo pipefail",
                    "docker compose -f docker-compose.validation.yml build "
                    "--no-cache --pull validation",
                ),
                "lock.install",
            ),
            _CanonicalRunStep(
                "pip check",
                "Verify installed dependency graph",
                "bash",
                _run_block(
                    "set -euo pipefail",
                    "docker compose -f docker-compose.validation.yml run --rm "
                    "--entrypoint python validation -I -m pip --isolated "
                    "--disable-pip-version-check check",
                ),
                "lock.pip_check",
            ),
            _CanonicalRunStep(
                "CI normal+self-test",
                "Check CI policy in validation image",
                "bash",
                _run_block(
                    "set -euo pipefail",
                    "docker compose -f docker-compose.validation.yml run --rm "
                    "--entrypoint python validation -I scripts/check_ci.py",
                    "docker compose -f docker-compose.validation.yml run --rm "
                    "--entrypoint python validation -I scripts/check_ci.py --self-test",
                ),
                "ci.self_test",
            ),
        )
    return ()


def _canonical_doctor_step(job_id: str) -> _CanonicalRunStep:
    if job_id == "ubuntu-native":
        run = _run_block(
            "set -euo pipefail",
            "./.venv/bin/python -I scripts/doctor.py --profile host-no-docker",
        )
        name = "Run host doctor"
    elif job_id == "windows-powershell":
        run = _run_block(
            r"& .\.venv\Scripts\python.exe -I scripts\doctor.py "
            "--profile host-no-docker",
            "exit $LASTEXITCODE",
        )
        name = "Run host doctor"
    else:
        run = _run_block(
            "set -euo pipefail",
            "docker compose -f docker-compose.validation.yml run --rm "
            "--entrypoint python validation -I scripts/doctor.py --profile container",
        )
        name = "Run container doctor"
    return _CanonicalRunStep(
        "doctor",
        name,
        EXPECTED_SHELLS[job_id],
        run,
        "doctor.required",
    )


def _canonical_suite_steps(job_id: str) -> tuple[_CanonicalRunStep, ...]:
    shell = EXPECTED_SHELLS[job_id]
    result: list[_CanonicalRunStep] = []
    for suite in PUBLIC_SUITES:
        if job_id == "ubuntu-native":
            command = f"./scripts/validate.sh --suite {suite}"
        elif job_id == "windows-powershell":
            command = rf".\scripts\validate.ps1 -Suite {suite}"
        else:
            command = (
                "docker compose -f docker-compose.validation.yml run --rm "
                f"validation --suite {suite}"
            )
        result.append(
            _CanonicalRunStep(
                f"suite {suite}",
                _SUITE_STEP_NAMES[suite],
                shell,
                command,
                "suite.required",
            )
        )
    return tuple(result)


def _normalized_run_block(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    return value.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")


def _canonical_run_step_mapping(specification: _CanonicalRunStep) -> dict[str, Any]:
    return {
        "name": specification.name,
        "shell": specification.shell,
        "run": specification.run,
    }


def _canonical_checkout_step() -> dict[str, Any]:
    return {
        "name": "Check out repository",
        "uses": _CHECKOUT_USES,
        "with": {"persist-credentials": False},
    }


def _canonical_setup_python_step() -> dict[str, Any]:
    return {
        "name": "Set up CPython 3.12.10",
        "uses": _SETUP_PYTHON_USES,
        "with": {"python-version": "3.12.10"},
    }


def _canonical_summary_step(job_id: str) -> dict[str, Any]:
    heading = {
        "ubuntu-native": "Ubuntu",
        "windows-powershell": "Windows",
        "docker-clean-room": "Docker",
    }[job_id]
    if job_id == "windows-powershell":
        run = _run_block(
            '@"',
            f"## {heading} validation status",
            "### Business status",
            "Fixture-level PASS, FAIL, INAPPLICABLE, and UNTESTABLE outcomes are "
            "recorded in the uploaded suite result JSON.",
            "### Program status",
            "Authoritative SUCCESS or ERROR values and exit codes are recorded "
            "separately in the suite result JSON. GitHub job status: "
            "${{ job.status }}.",
            '"@ | Out-File -FilePath $env:GITHUB_STEP_SUMMARY -Encoding utf8 -Append',
        )
    elif job_id == "docker-clean-room":
        # Container uid 10001 writes build/ci/docker; relax perms before upload.
        run = _run_block(
            "set -euo pipefail",
            "{",
            f'  echo "## {heading} validation status"',
            '  echo "### Business status"',
            '  echo "Fixture-level PASS, FAIL, INAPPLICABLE, and UNTESTABLE outcomes '
            'are recorded in the uploaded suite result JSON."',
            '  echo "### Program status"',
            '  echo "Authoritative SUCCESS or ERROR values and exit codes are '
            "recorded separately in the suite result JSON. GitHub job status: "
            '${{ job.status }}."',
            '} >> "$GITHUB_STEP_SUMMARY"',
            "if [[ -d build/ci/docker ]]; then",
            "  sudo chmod -R a+rX build/ci/docker",
            "fi",
        )
    else:
        run = _run_block(
            "{",
            f'  echo "## {heading} validation status"',
            '  echo "### Business status"',
            '  echo "Fixture-level PASS, FAIL, INAPPLICABLE, and UNTESTABLE outcomes '
            'are recorded in the uploaded suite result JSON."',
            '  echo "### Program status"',
            '  echo "Authoritative SUCCESS or ERROR values and exit codes are '
            "recorded separately in the suite result JSON. GitHub job status: "
            '${{ job.status }}."',
            '} >> "$GITHUB_STEP_SUMMARY"',
        )
    return {
        "name": "Summarize business and program status",
        "if": "always()",
        "shell": EXPECTED_SHELLS[job_id],
        "run": run,
    }


def _canonical_upload_step() -> dict[str, Any]:
    return {
        "name": "Upload CI evidence",
        "if": "always()",
        "uses": _UPLOAD_ARTIFACT_USES,
        "with": {
            "name": "validation-${{ github.job }}",
            "path": _ARTIFACT_PATHS,
            "if-no-files-found": "error",
        },
    }


def _canonical_ordered_steps(job_id: str) -> tuple[dict[str, Any], ...]:
    core = _canonical_core_steps(job_id)
    suites = tuple(
        _canonical_run_step_mapping(step) for step in _canonical_suite_steps(job_id)
    )
    doctor = _canonical_run_step_mapping(_canonical_doctor_step(job_id))
    if job_id == "docker-clean-room":
        prefix = (
            _canonical_checkout_step(),
            _canonical_run_step_mapping(core[0]),
            _canonical_run_step_mapping(core[1]),
            doctor,
            _canonical_run_step_mapping(core[2]),
            _canonical_run_step_mapping(core[3]),
        )
    else:
        prefix = (
            _canonical_checkout_step(),
            _canonical_setup_python_step(),
            _canonical_run_step_mapping(core[0]),
            _canonical_run_step_mapping(core[1]),
            doctor,
            _canonical_run_step_mapping(core[2]),
        )
    return prefix + suites + (_canonical_summary_step(job_id), _canonical_upload_step())


EXPECTED_VALIDATE_STRUCTURE: dict[str, Any] = {
    "name": "Validate C Semantic Governance Package",
    "on": {
        "push": {"branches": ["main"]},
        "pull_request": {"branches": ["main"]},
        "workflow_dispatch": None,
    },
    "permissions": {"contents": "read"},
    "concurrency": {
        "group": (
            "validate-${{ github.workflow }}-"
            "${{ github.event.pull_request.number || github.ref }}"
        ),
        "cancel-in-progress": True,
    },
    "jobs": {
        job_id: {
            "name": _EXPECTED_JOB_NAMES[job_id],
            "runs-on": EXPECTED_RUNNERS[job_id],
            "timeout-minutes": 30,
            "steps": list(_canonical_ordered_steps(job_id)),
        }
        for job_id in REQUIRED_JOBS
    },
}


def _normalized_validate_step(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    normalized = dict(value)
    if "run" in normalized:
        normalized["run"] = _normalized_run_block(normalized["run"])
    options = normalized.get("with")
    if isinstance(options, Mapping):
        normalized_options = dict(options)
        if "path" in normalized_options:
            normalized_options["path"] = _normalized_run_block(
                normalized_options["path"]
            )
        normalized["with"] = normalized_options
    return normalized


def _check_exact_named_step(
    job_id: str,
    job: Any,
    *,
    name: str,
    expected: Mapping[str, Any],
    issue_code: str,
    identity: str,
) -> list[PolicyIssue]:
    matches = [
        (index, step)
        for index, step in enumerate(_steps(job))
        if step.get("name") == name
    ]
    if len(matches) != 1:
        return [
            PolicyIssue(
                issue_code,
                f"jobs.{job_id}",
                f"{identity} requires exactly one dedicated step named {name!r}",
            )
        ]
    index, step = matches[0]
    if _normalized_validate_step(step) == _normalized_validate_step(expected):
        return []
    return [
        PolicyIssue(
            issue_code,
            _step_location(job_id, index),
            f"{identity} must match the complete canonical step mapping",
        )
    ]


def _check_validate_step_inventory(job_id: str, job: Any) -> list[PolicyIssue]:
    raw_steps = job.get("steps") if isinstance(job, Mapping) else None
    if not isinstance(raw_steps, Sequence) or isinstance(raw_steps, (str, bytes)):
        return [
            PolicyIssue(
                "step.inventory",
                f"jobs.{job_id}.steps",
                "steps must be the complete ordered canonical validation sequence",
            )
        ]
    actual = tuple(_normalized_validate_step(step) for step in raw_steps)
    expected = tuple(
        _normalized_validate_step(step)
        for step in EXPECTED_VALIDATE_STRUCTURE["jobs"][job_id]["steps"]
    )
    if actual == expected:
        return []
    return [
        PolicyIssue(
            "step.inventory",
            f"jobs.{job_id}.steps",
            "steps must be the exact ordered 15-step validation sequence; extra, "
            "missing, reordered, or modified steps are forbidden",
        )
    ]


def _check_canonical_run_step(
    job_id: str, job: Any, specification: _CanonicalRunStep
) -> list[PolicyIssue]:
    matches = [
        (index, step)
        for index, step in enumerate(_steps(job))
        if step.get("name") == specification.name
    ]
    if len(matches) != 1:
        return [
            PolicyIssue(
                specification.issue_code,
                f"jobs.{job_id}",
                f"{specification.identity} requires exactly one dedicated step "
                f"named {specification.name!r}",
            )
        ]
    index, step = matches[0]
    actual_keys = set(step)
    allowed_keys = {"name", "shell", "run"}
    correct = (
        actual_keys == allowed_keys
        and step.get("shell") == specification.shell
        and _normalized_run_block(step.get("run")) == specification.run
    )
    if correct:
        return []
    return [
        PolicyIssue(
            specification.issue_code,
            _step_location(job_id, index),
            f"{specification.identity} step must contain only name/shell/run and "
            "match the complete canonical command block",
        )
    ]


def _check_canonical_validate_steps(job_id: str, job: Any) -> list[PolicyIssue]:
    issues: list[PolicyIssue] = []
    specifications = (
        _canonical_core_steps(job_id)
        + (_canonical_doctor_step(job_id),)
        + _canonical_suite_steps(job_id)
    )
    for specification in specifications:
        issues.extend(_check_canonical_run_step(job_id, job, specification))
    return issues


def _check_python_setup(job_id: str, job: Any) -> list[PolicyIssue]:
    issues: list[PolicyIssue] = []
    setup_steps = [
        (index, step)
        for index, step in enumerate(_steps(job))
        if isinstance(step.get("uses"), str)
        and _action_name(str(step["uses"])) == "actions/setup-python"
    ]
    if job_id == "docker-clean-room":
        if setup_steps:
            issues.append(
                PolicyIssue(
                    "python.container_setup",
                    f"jobs.{job_id}",
                    "Docker clean-room must use the image's pinned Python",
                )
            )
        return issues
    return _check_exact_named_step(
        job_id,
        job,
        name="Set up CPython 3.12.10",
        expected=_canonical_setup_python_step(),
        issue_code="python.setup",
        identity="setup-python",
    )


def _check_job_summary(job_id: str, job: Any) -> list[PolicyIssue]:
    return _check_exact_named_step(
        job_id,
        job,
        name="Summarize business and program status",
        expected=_canonical_summary_step(job_id),
        issue_code="summary.profile",
        identity="job summary",
    )


def _check_validate_action_steps(job_id: str, job: Any) -> list[PolicyIssue]:
    issues = _check_exact_named_step(
        job_id,
        job,
        name="Check out repository",
        expected=_canonical_checkout_step(),
        issue_code="checkout.profile",
        identity="checkout",
    )
    issues.extend(
        _check_exact_named_step(
            job_id,
            job,
            name="Upload CI evidence",
            expected=_canonical_upload_step(),
            issue_code="artifact.profile",
            identity="artifact upload",
        )
    )
    return issues


def check_validate_profile(workflow: Mapping[str, Any]) -> list[PolicyIssue]:
    """Apply the validate.yml-specific trigger, job, suite, and summary profile."""

    issues = check_validate_triggers(workflow)
    if set(workflow) != _VALIDATE_WORKFLOW_KEYS:
        issues.append(
            PolicyIssue(
                "workflow.keys",
                "workflow",
                "validate workflow keys must exactly match the approved profile",
            )
        )
    if workflow.get("name") != "Validate C Semantic Governance Package":
        issues.append(
            PolicyIssue(
                "workflow.name",
                "name",
                "validate workflow name must match the approved profile",
            )
        )
    actual_context = {key: value for key, value in workflow.items() if key != "jobs"}
    expected_context = {
        key: value
        for key, value in EXPECTED_VALIDATE_STRUCTURE.items()
        if key != "jobs"
    }
    if actual_context != expected_context:
        issues.append(
            PolicyIssue(
                "workflow.context",
                "workflow",
                "workflow context must deeply equal the approved validate profile",
            )
        )
    jobs = _jobs(workflow)
    actual_jobs = set(jobs)
    required_jobs = set(REQUIRED_JOBS)
    for missing in sorted(required_jobs - actual_jobs):
        issues.append(
            PolicyIssue(
                "job.required",
                f"jobs.{missing}",
                f"required job {missing!r} is missing",
            )
        )
    for unexpected in sorted(actual_jobs - required_jobs, key=lambda item: repr(item)):
        issues.append(
            PolicyIssue(
                "job.unapproved",
                f"jobs.{unexpected}",
                f"job {unexpected!r} is not part of the validation profile",
            )
        )
    for job_id in REQUIRED_JOBS:
        job = jobs.get(job_id)
        if not isinstance(job, Mapping):
            continue
        if set(job) != _VALIDATE_JOB_KEYS:
            issues.append(
                PolicyIssue(
                    "job.keys",
                    f"jobs.{job_id}",
                    "job keys must exactly match the approved validation profile",
                )
            )
        if job.get("name") != _EXPECTED_JOB_NAMES[job_id]:
            issues.append(
                PolicyIssue(
                    "job.name",
                    f"jobs.{job_id}.name",
                    "job name must match the approved validation profile",
                )
            )
        actual_job_context = {key: value for key, value in job.items() if key != "steps"}
        expected_job = EXPECTED_VALIDATE_STRUCTURE["jobs"][job_id]
        expected_job_context = {
            key: value for key, value in expected_job.items() if key != "steps"
        }
        if actual_job_context != expected_job_context:
            issues.append(
                PolicyIssue(
                    "job.context",
                    f"jobs.{job_id}",
                    "job context must deeply equal the approved validate profile",
                )
            )
        if job.get("runs-on") != EXPECTED_RUNNERS[job_id]:
            issues.append(
                PolicyIssue(
                    "runner.profile",
                    f"jobs.{job_id}.runs-on",
                    f"runner must equal {EXPECTED_RUNNERS[job_id]!r}",
                )
            )
        if job.get("timeout-minutes") != 30:
            issues.append(
                PolicyIssue(
                    "timeout.profile",
                    f"jobs.{job_id}.timeout-minutes",
                    "validation jobs must use timeout-minutes: 30",
                )
            )
        issues.extend(_check_python_setup(job_id, job))
        issues.extend(_check_job_summary(job_id, job))
        issues.extend(_check_validate_action_steps(job_id, job))
        issues.extend(_check_canonical_validate_steps(job_id, job))
        issues.extend(_check_validate_step_inventory(job_id, job))
        for index, step in enumerate(_steps(job)):
            if "run" in step and step.get("shell") != EXPECTED_SHELLS[job_id]:
                issues.append(
                    PolicyIssue(
                        "shell.profile",
                        _step_location(job_id, index) + ".shell",
                        f"run steps must use {EXPECTED_SHELLS[job_id]!r}",
                    )
                )
    return sorted(set(issues))


def evaluate_workflow_policy(
    workflow: Mapping[str, Any], source_text: str, *, profile: str = VALIDATE_PROFILE
) -> list[PolicyIssue]:
    """Evaluate parsed YAML through common predicates and a named profile."""

    issues = check_common_workflow_policy(workflow, source_text)
    if profile == VALIDATE_PROFILE:
        issues.extend(check_validate_profile(workflow))
    else:
        issues.append(
            PolicyIssue(
                "profile.unknown", "profile", f"unknown workflow profile {profile!r}"
            )
        )
    return sorted(set(issues))


def _relative_display(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def _source_provenance(
    root: Path, workflow_path: Path
) -> tuple[dict[str, Any], list[PolicyIssue]]:
    issues: list[PolicyIssue] = []
    registry_path = root / "C_Semantic_Treehouse" / "manifests" / "validation-suites.json"
    lock_path = root / "requirements.lock"
    checker_path = root / "scripts" / "check_ci.py"
    registry_contract: str | None = None
    registry_sha: str | None = None
    lock_sha: str | None = None
    workflow_sha: str | None = None

    if registry_path.is_file():
        registry_sha = sha256_file(registry_path)
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            value = registry.get("contract_version") if isinstance(registry, dict) else None
            if isinstance(value, str) and value:
                registry_contract = value
            else:
                raise ValueError("contract_version must be a non-empty string")
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            issues.append(
                PolicyIssue(
                    "provenance.registry",
                    "C_Semantic_Treehouse/manifests/validation-suites.json",
                    f"cannot read registry contract: {exc}",
                )
            )
    else:
        issues.append(
            PolicyIssue(
                "provenance.registry",
                "C_Semantic_Treehouse/manifests/validation-suites.json",
                "validation suite registry is missing",
            )
        )
    if lock_path.is_file():
        lock_sha = sha256_file(lock_path)
    else:
        issues.append(
            PolicyIssue(
                "provenance.lock",
                "requirements.lock",
                "runtime requirements lock is missing",
            )
        )
    if workflow_path.is_file():
        workflow_sha = sha256_file(workflow_path)
    else:
        issues.append(
            PolicyIssue(
                "provenance.workflow",
                _relative_display(workflow_path, root),
                "workflow file is missing",
            )
        )
    return (
        {
            "validation_suites": {
                "path": "C_Semantic_Treehouse/manifests/validation-suites.json",
                "contract_version": registry_contract,
                "sha256": registry_sha,
            },
            "requirements_lock": {
                "path": "requirements.lock",
                "sha256": lock_sha,
            },
            "workflow": {
                "path": _relative_display(workflow_path, root),
                "sha256": workflow_sha,
            },
            "checker": {
                "path": "scripts/check_ci.py",
                "sha256": sha256_file(checker_path) if checker_path.is_file() else None,
            },
        },
        issues,
    )


def build_policy_report(
    workflow_path: Path,
    *,
    root: Path | None = None,
    profile: str = VALIDATE_PROFILE,
) -> dict[str, Any]:
    """Read and evaluate one workflow, returning deterministic JSON data."""

    repo = (root or repository_root()).resolve()
    provenance, provenance_issues = _source_provenance(repo, workflow_path)
    issues = list(provenance_issues)
    source_text = ""
    if workflow_path.is_file():
        try:
            source_text = workflow_path.read_text(encoding="utf-8")
            workflow = load_workflow_text(source_text)
            issues.extend(evaluate_workflow_policy(workflow, source_text, profile=profile))
        except (OSError, UnicodeError, yaml.YAMLError, ValueError) as exc:
            issues.append(
                PolicyIssue(
                    "yaml.parse",
                    provenance["workflow"]["path"],
                    f"workflow YAML could not be parsed: {exc}",
                )
            )
    issues = sorted(set(issues))
    passed = not issues
    return {
        "schema": POLICY_SCHEMA,
        "profile": profile,
        "policy_status": "PASS" if passed else "FAIL",
        "program_status": "SUCCESS" if passed else "ERROR",
        "exit_code": 0 if passed else 1,
        "provenance": provenance,
        "predicates": {
            "common": [
                "permissions",
                "action_pins",
                "checkout",
                "runner",
                "timeout",
                "shell",
                "artifact",
                "fail_closed",
                "no_secrets",
                "concurrency",
            ],
            "profile": ["validate_triggers", "validate_jobs"],
        },
        "issue_count": len(issues),
        "issues": [issue.as_dict() for issue in issues],
    }


def _replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) < 1:
        raise ValueError(f"self-test fixture text not found: {old!r}")
    return source.replace(old, new, 1)


def _remove_indented_block(source: str, header: str, indent: int) -> str:
    lines = source.splitlines(keepends=True)
    prefix = " " * indent + header
    starts = [index for index, line in enumerate(lines) if line.rstrip("\r\n") == prefix]
    if len(starts) != 1:
        raise ValueError(f"expected one block {prefix!r}, found {len(starts)}")
    start = starts[0]
    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].rstrip("\r\n")
        if not stripped or stripped.lstrip().startswith("#"):
            continue
        current_indent = len(stripped) - len(stripped.lstrip(" "))
        if current_indent <= indent:
            end = index
            break
    return "".join(lines[:start] + lines[end:])


def _remove_named_step(source: str, job_id: str, step_name: str) -> str:
    lines = source.splitlines(keepends=True)
    job_header = f"  {job_id}:"
    job_start = next(
        (index for index, line in enumerate(lines) if line.rstrip("\r\n") == job_header),
        None,
    )
    if job_start is None:
        raise ValueError(f"job not found: {job_id}")
    job_end = len(lines)
    for index in range(job_start + 1, len(lines)):
        line = lines[index].rstrip("\r\n")
        if line and not line.startswith(" "):
            job_end = index
            break
        if line.startswith("  ") and not line.startswith("    "):
            job_end = index
            break
    step_header = f"      - name: {step_name}"
    start = next(
        (
            index
            for index in range(job_start, job_end)
            if lines[index].rstrip("\r\n") == step_header
        ),
        None,
    )
    if start is None:
        raise ValueError(f"step not found: {job_id}/{step_name}")
    end = job_end
    for index in range(start + 1, job_end):
        if lines[index].startswith("      - name:"):
            end = index
            break
    return "".join(lines[:start] + lines[end:])


def _dispatch_injection(source: str) -> str:
    changed = _replace_once(
        source,
        "  workflow_dispatch:\n",
        "  workflow_dispatch:\n"
        "    inputs:\n"
        "      suite:\n"
        "        description: Untrusted suite\n"
        "        required: false\n"
        "        type: string\n",
    )
    return _replace_once(
        changed,
        "run: ./scripts/validate.sh --suite frozen",
        'run: ./scripts/validate.sh --suite "${{ github.event.inputs.suite }}"',
    )


def _negative_controls() -> list[tuple[str, tuple[str, ...], Callable[[str], str]]]:
    checkout_sha = "11bd71901bbe5b1630ceea73d27597364c9af683"
    return [
        (
            "forbidden-pull-request-target",
            ("trigger.forbidden",),
            lambda text: _replace_once(
                text,
                "  workflow_dispatch:\n",
                "  workflow_dispatch:\n  pull_request_target:\n",
            ),
        ),
        (
            "missing-push-trigger",
            ("trigger.required",),
            lambda text: _remove_indented_block(text, "push:", 2),
        ),
        (
            "missing-pull-request-trigger",
            ("trigger.required",),
            lambda text: _remove_indented_block(text, "pull_request:", 2),
        ),
        (
            "missing-workflow-dispatch-trigger",
            ("trigger.required",),
            lambda text: _remove_indented_block(text, "workflow_dispatch:", 2),
        ),
        (
            "missing-branch-filter",
            ("trigger.branch_filter.missing",),
            lambda text: _replace_once(
                text, "  push:\n    branches:\n      - main\n", "  push:\n"
            ),
        ),
        (
            "wildcard-branch-filter",
            ("trigger.branch_filter.unsafe",),
            lambda text: _replace_once(text, "      - main\n", "      - '**'\n"),
        ),
        (
            "branches-ignore-filter",
            ("trigger.branch_filter.unsafe",),
            lambda text: _replace_once(
                text,
                "  push:\n    branches:\n      - main\n",
                "  push:\n    branches:\n      - main\n    branches-ignore:\n      - dev\n",
            ),
        ),
        (
            "dispatch-input-shell-injection",
            ("shell.untrusted_expression", "trigger.dispatch_inputs"),
            _dispatch_injection,
        ),
        (
            "write-permission",
            ("permissions.write",),
            lambda text: _replace_once(text, "  contents: read\n", "  contents: write\n"),
        ),
        (
            "persist-credentials-true",
            ("checkout.persist_credentials",),
            lambda text: _replace_once(
                text,
                "          persist-credentials: false\n",
                "          persist-credentials: true\n",
            ),
        ),
        (
            "floating-action-tag",
            ("action.unpinned",),
            lambda text: _replace_once(
                text, f"actions/checkout@{checkout_sha}", "actions/checkout@v4"
            ),
        ),
        (
            "missing-action-version-comment",
            ("action.version_comment",),
            lambda text: _replace_once(text, " # v4.2.2\n", "\n"),
        ),
        (
            "latest-runner",
            ("runner.latest",),
            lambda text: _replace_once(text, "runs-on: ubuntu-24.04", "runs-on: ubuntu-latest"),
        ),
        (
            "continue-on-error",
            ("step.continue_on_error",),
            lambda text: _replace_once(
                text,
                "      - name: Validate frozen\n        shell: bash\n",
                "      - name: Validate frozen\n"
                "        continue-on-error: true\n"
                "        shell: bash\n",
            ),
        ),
        (
            "continue-on-error-step-false",
            ("step.continue_on_error",),
            lambda text: _replace_once(
                text,
                "      - name: Validate frozen\n        shell: bash\n",
                "      - name: Validate frozen\n"
                "        continue-on-error: false\n"
                "        shell: bash\n",
            ),
        ),
        (
            "continue-on-error-step-expression",
            ("step.continue_on_error",),
            lambda text: _replace_once(
                text,
                "      - name: Validate frozen\n        shell: bash\n",
                "      - name: Validate frozen\n"
                "        continue-on-error: ${{ true }}\n"
                "        shell: bash\n",
            ),
        ),
        (
            "continue-on-error-job-false",
            ("job.continue_on_error",),
            lambda text: _replace_once(
                text,
                "    timeout-minutes: 30\n    steps:\n",
                "    timeout-minutes: 30\n"
                "    continue-on-error: false\n"
                "    steps:\n",
            ),
        ),
        (
            "continue-on-error-job-expression",
            ("job.continue_on_error",),
            lambda text: _replace_once(
                text,
                "    timeout-minutes: 30\n    steps:\n",
                "    timeout-minutes: 30\n"
                "    continue-on-error: ${{ true }}\n"
                "    steps:\n",
            ),
        ),
        (
            "no-op-bootstrap-echo",
            ("lock.install",),
            lambda text: _replace_once(
                text,
                '          PYTHON_PATH="$(command -v python)" '
                "DOCTOR_PROFILE=host-no-docker ./scripts/bootstrap.sh\n",
                "          echo 'PYTHON_PATH=\"$(command -v python)\" "
                "DOCTOR_PROFILE=host-no-docker ./scripts/bootstrap.sh'\n",
            ),
        ),
        (
            "no-op-pip-check-echo",
            ("lock.pip_check",),
            lambda text: _replace_once(
                text,
                "          ./.venv/bin/python -I -m pip --isolated "
                "--disable-pip-version-check check\n",
                "          echo './.venv/bin/python -I -m pip --isolated "
                "--disable-pip-version-check check'\n",
            ),
        ),
        (
            "no-op-ci-self-test-echo",
            ("ci.self_test",),
            lambda text: _replace_once(
                text,
                "          ./.venv/bin/python -I scripts/check_ci.py\n"
                "          ./.venv/bin/python -I scripts/check_ci.py --self-test\n",
                "          echo './.venv/bin/python -I scripts/check_ci.py'\n"
                "          echo './.venv/bin/python -I scripts/check_ci.py "
                "--self-test'\n",
            ),
        ),
        (
            "no-op-docker-build-echo",
            ("lock.install",),
            lambda text: _replace_once(
                text,
                "          docker compose -f docker-compose.validation.yml "
                "build --no-cache --pull validation\n",
                "          echo 'docker compose -f docker-compose.validation.yml "
                "build --no-cache --pull validation'\n",
            ),
        ),
        (
            "no-op-suite-echo",
            ("suite.required",),
            lambda text: _replace_once(
                text,
                "        run: ./scripts/validate.sh --suite frozen\n",
                "        run: echo './scripts/validate.sh --suite frozen'\n",
            ),
        ),
        (
            "no-op-suite-write-output",
            ("suite.required",),
            lambda text: _replace_once(
                text,
                "        run: .\\scripts\\validate.ps1 -Suite frozen\n",
                "        run: Write-Output '.\\scripts\\validate.ps1 -Suite frozen'\n",
            ),
        ),
        (
            "no-op-suite-comment",
            ("suite.required",),
            lambda text: _replace_once(
                text,
                "        run: docker compose -f docker-compose.validation.yml "
                "run --rm validation --suite frozen\n",
                "        run: |\n"
                "          # docker compose -f docker-compose.validation.yml "
                "run --rm validation --suite frozen\n"
                "          true\n",
            ),
        ),
        (
            "no-op-suite-here-doc",
            ("suite.required",),
            lambda text: _replace_once(
                text,
                "        run: ./scripts/validate.sh --suite environment\n",
                "        run: |\n"
                "          cat <<'EOF'\n"
                "          ./scripts/validate.sh --suite environment\n"
                "          EOF\n",
            ),
        ),
        (
            "suite-pipeline-wrapper",
            ("suite.required",),
            lambda text: _replace_once(
                text,
                "        run: ./scripts/validate.sh --suite baseline\n",
                "        run: ./scripts/validate.sh --suite baseline | cat\n",
            ),
        ),
        (
            "suite-success-suffix",
            ("suite.required",),
            lambda text: _replace_once(
                text,
                "        run: ./scripts/validate.sh --suite traceability\n",
                "        run: ./scripts/validate.sh --suite traceability || true\n",
            ),
        ),
        (
            "suite-compound-shell",
            ("suite.required",),
            lambda text: _replace_once(
                text,
                "        run: ./scripts/validate.sh --suite v0.4-model\n",
                "        run: true; ./scripts/validate.sh --suite v0.4-model\n",
            ),
        ),
        (
            "extra-mutating-run-step",
            ("step.inventory",),
            lambda text: _replace_once(
                text,
                "      - name: Summarize business and program status\n",
                "      - name: Mutate repository\n"
                "        shell: bash\n"
                "        run: touch injected.txt\n\n"
                "      - name: Summarize business and program status\n",
            ),
        ),
        (
            "extra-remote-action-step",
            ("step.inventory",),
            lambda text: _replace_once(
                text,
                "      - name: Set up CPython 3.12.10\n",
                "      - name: Extra remote action\n"
                f"        uses: actions/checkout@{checkout_sha} # v4.2.2\n"
                "        with:\n"
                "          persist-credentials: false\n\n"
                "      - name: Set up CPython 3.12.10\n",
            ),
        ),
        (
            "extra-local-action-step",
            ("step.inventory",),
            lambda text: _replace_once(
                text,
                "      - name: Set up CPython 3.12.10\n",
                "      - name: Local action\n"
                "        uses: ./actions/local-validation\n\n"
                "      - name: Set up CPython 3.12.10\n",
            ),
        ),
        (
            "doctor-command-echo",
            ("doctor.required",),
            lambda text: _replace_once(
                text,
                "          ./.venv/bin/python -I scripts/doctor.py "
                "--profile host-no-docker\n",
                "          echo './.venv/bin/python -I scripts/doctor.py "
                "--profile host-no-docker'\n",
            ),
        ),
        (
            "workflow-bash-env",
            ("workflow.keys",),
            lambda text: _replace_once(
                text,
                "permissions:\n",
                "env:\n  BASH_ENV: ./scripts/injected.sh\n\npermissions:\n",
            ),
        ),
        (
            "job-bash-env",
            ("job.keys",),
            lambda text: _replace_once(
                text,
                "    timeout-minutes: 30\n    steps:\n",
                "    timeout-minutes: 30\n"
                "    env:\n"
                "      BASH_ENV: ./scripts/injected.sh\n"
                "    steps:\n",
            ),
        ),
        (
            "step-bash-env",
            ("step.inventory",),
            lambda text: _replace_once(
                text,
                "      - name: Validate frozen\n        shell: bash\n",
                "      - name: Validate frozen\n"
                "        env:\n"
                "          BASH_ENV: ./scripts/injected.sh\n"
                "        shell: bash\n",
            ),
        ),
        (
            "step-working-directory",
            ("step.inventory",),
            lambda text: _replace_once(
                text,
                "      - name: Validate environment\n        shell: bash\n",
                "      - name: Validate environment\n"
                "        shell: bash\n"
                "        working-directory: scripts\n",
            ),
        ),
        (
            "job-container",
            ("job.keys",),
            lambda text: _replace_once(
                text,
                "    timeout-minutes: 30\n    steps:\n",
                "    timeout-minutes: 30\n"
                "    container: python:3.12\n"
                "    steps:\n",
            ),
        ),
        (
            "job-services",
            ("job.keys",),
            lambda text: _replace_once(
                text,
                "    timeout-minutes: 30\n    steps:\n",
                "    timeout-minutes: 30\n"
                "    services:\n"
                "      database:\n"
                "        image: postgres:16\n"
                "    steps:\n",
            ),
        ),
        (
            "workflow-defaults",
            ("workflow.keys",),
            lambda text: _replace_once(
                text,
                "permissions:\n",
                "defaults:\n  run:\n    shell: bash\n\npermissions:\n",
            ),
        ),
        (
            "job-defaults",
            ("job.keys",),
            lambda text: _replace_once(
                text,
                "    timeout-minutes: 30\n    steps:\n",
                "    timeout-minutes: 30\n"
                "    defaults:\n"
                "      run:\n"
                "        working-directory: scripts\n"
                "    steps:\n",
            ),
        ),
        (
            "job-strategy",
            ("job.keys",),
            lambda text: _replace_once(
                text,
                "    timeout-minutes: 30\n    steps:\n",
                "    timeout-minutes: 30\n"
                "    strategy:\n"
                "      fail-fast: false\n"
                "    steps:\n",
            ),
        ),
        (
            "checkout-ref-option",
            ("checkout.profile",),
            lambda text: _replace_once(
                text,
                "          persist-credentials: false\n",
                "          persist-credentials: false\n          ref: main\n",
            ),
        ),
        (
            "checkout-extra-option",
            ("checkout.profile",),
            lambda text: _replace_once(
                text,
                "          persist-credentials: false\n",
                "          persist-credentials: false\n          fetch-depth: 0\n",
            ),
        ),
        (
            "setup-python-extra-option",
            ("python.setup",),
            lambda text: _replace_once(
                text,
                '          python-version: "3.12.10"\n',
                '          python-version: "3.12.10"\n          cache: pip\n',
            ),
        ),
        (
            "upload-extra-option",
            ("artifact.profile",),
            lambda text: _replace_once(
                text,
                "          if-no-files-found: error\n",
                "          if-no-files-found: error\n          retention-days: 7\n",
            ),
        ),
        (
            "reordered-suite-steps",
            ("step.inventory",),
            lambda text: _replace_once(
                text,
                "      - name: Validate frozen\n"
                "        shell: bash\n"
                "        run: ./scripts/validate.sh --suite frozen\n\n"
                "      - name: Validate environment\n"
                "        shell: bash\n"
                "        run: ./scripts/validate.sh --suite environment\n",
                "      - name: Validate environment\n"
                "        shell: bash\n"
                "        run: ./scripts/validate.sh --suite environment\n\n"
                "      - name: Validate frozen\n"
                "        shell: bash\n"
                "        run: ./scripts/validate.sh --suite frozen\n",
            ),
        ),
        (
            "removed-suite-step",
            ("step.inventory", "suite.required"),
            lambda text: _remove_named_step(text, "ubuntu-native", "Validate frozen"),
        ),
        (
            "missing-required-job",
            ("job.required",),
            lambda text: _remove_indented_block(text, "docker-clean-room:", 2),
        ),
        (
            "missing-artifact-upload",
            ("artifact.missing",),
            lambda text: _remove_named_step(text, "ubuntu-native", "Upload CI evidence"),
        ),
        (
            "artifact-not-always",
            ("artifact.always",),
            lambda text: _replace_once(
                text,
                "      - name: Upload CI evidence\n        if: always()\n",
                "      - name: Upload CI evidence\n        if: success()\n",
            ),
        ),
        (
            "artifact-missing-files-warn",
            ("artifact.if_no_files",),
            lambda text: _replace_once(
                text, "          if-no-files-found: error\n", "          if-no-files-found: warn\n"
            ),
        ),
        (
            "artifact-narrow-json-patterns",
            ("artifact.coverage", "artifact.profile"),
            lambda text: _replace_once(
                text,
                "            build/**/*.json\n",
                "            build/**/*result.json\n"
                "            build/**/*machine.json\n"
                "            build/**/*environment.json\n",
            ),
        ),
        (
            "artifact-missing-general-json",
            ("artifact.coverage", "artifact.profile"),
            lambda text: _replace_once(text, "            build/**/*.json\n", ""),
        ),
        (
            "artifact-markdown-lookalike-suffix",
            ("artifact.coverage", "artifact.profile"),
            lambda text: _replace_once(
                text,
                "            build/**/*.md\n",
                "            build/**/*.md.bak\n",
            ),
        ),
        (
            "missing-timeout",
            ("timeout.missing",),
            lambda text: _replace_once(text, "    timeout-minutes: 30\n", ""),
        ),
        (
            "missing-explicit-shell",
            ("shell.missing",),
            lambda text: _replace_once(text, "        shell: bash\n", ""),
        ),
        (
            "disabled-concurrency-cancellation",
            ("concurrency.cancel",),
            lambda text: _replace_once(
                text, "  cancel-in-progress: true\n", "  cancel-in-progress: false\n"
            ),
        ),
        (
            "merged-business-program-summary",
            ("summary.profile",),
            lambda text: _replace_once(text, '            echo "### Business status"\n', ""),
        ),
    ]


def _run_checker_subprocess(path: Path) -> tuple[int, dict[str, Any] | None]:
    command = [
        sys.executable,
        "-I",
        str(Path(__file__).resolve()),
        "--workflow",
        str(path),
        "--no-write",
    ]
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    completed = subprocess.run(
        command,
        cwd=str(path.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
        timeout=30,
    )
    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError:
        parsed = None
    return completed.returncode, parsed


def run_self_test(workflow_path: Path, *, root: Path | None = None) -> dict[str, Any]:
    """Execute isolated positive and negative CLI controls in a temp directory."""

    repo = (root or repository_root()).resolve()
    provenance, provenance_issues = _source_provenance(repo, workflow_path)
    source = workflow_path.read_text(encoding="utf-8") if workflow_path.is_file() else ""
    controls: list[dict[str, Any]] = []
    failures: list[str] = []
    baseline_exit = -1
    baseline_codes: list[str] = []

    with tempfile.TemporaryDirectory(prefix="dssc-ci-policy-") as temp_name:
        temp = Path(temp_name)
        baseline_path = temp / "baseline.yml"
        baseline_path.write_text(source, encoding="utf-8", newline="\n")
        baseline_exit, baseline_report = _run_checker_subprocess(baseline_path)
        if isinstance(baseline_report, Mapping):
            baseline_codes = sorted(
                str(issue.get("code"))
                for issue in baseline_report.get("issues", [])
                if isinstance(issue, Mapping)
            )
        if baseline_exit != 0:
            failures.append("positive baseline returned nonzero")

        for control_id, expected_codes, mutate in _negative_controls():
            try:
                mutated = mutate(source)
                if mutated == source:
                    raise ValueError("mutation did not change the workflow")
                control_path = temp / f"{control_id}.yml"
                control_path.write_text(mutated, encoding="utf-8", newline="\n")
                exit_code, report = _run_checker_subprocess(control_path)
                observed_codes = sorted(
                    str(issue.get("code"))
                    for issue in report.get("issues", [])
                    if isinstance(report, Mapping)
                    and isinstance(issue, Mapping)
                ) if isinstance(report, Mapping) else []
                expected_observed = all(code in observed_codes for code in expected_codes)
                rejected = exit_code != 0
                passed = rejected and expected_observed
                if not passed:
                    failures.append(control_id)
                controls.append(
                    {
                        "id": control_id,
                        "expected_codes": list(expected_codes),
                        "observed_codes": observed_codes,
                        "exit_code": exit_code,
                        "rejected": rejected,
                        "expected_codes_observed": expected_observed,
                        "status": "PASS" if passed else "FAIL",
                    }
                )
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                failures.append(control_id)
                controls.append(
                    {
                        "id": control_id,
                        "expected_codes": list(expected_codes),
                        "observed_codes": [],
                        "exit_code": None,
                        "rejected": False,
                        "expected_codes_observed": False,
                        "status": "FAIL",
                        "error": str(exc),
                    }
                )

    if provenance_issues:
        failures.extend(issue.code for issue in provenance_issues)
    passed = baseline_exit == 0 and not failures and len(controls) == len(_negative_controls())
    return {
        "schema": SELF_TEST_SCHEMA,
        "profile": VALIDATE_PROFILE,
        "policy_status": "PASS" if passed else "FAIL",
        "program_status": "SUCCESS" if passed else "ERROR",
        "exit_code": 0 if passed else 1,
        "provenance": provenance,
        "positive_control": {
            "id": "canonical-validate-workflow",
            "exit_code": baseline_exit,
            "observed_codes": baseline_codes,
            "status": "PASS" if baseline_exit == 0 else "FAIL",
        },
        "counts": {
            "discovered": len(_negative_controls()),
            "executed": len(controls),
            "passed": sum(control["status"] == "PASS" for control in controls),
            "failed": sum(control["status"] != "PASS" for control in controls),
            "skipped": len(_negative_controls()) - len(controls),
        },
        "negative_controls": controls,
        "failures": sorted(set(failures)),
    }


def _git_inventory(root: Path) -> dict[str, Any]:
    def run(arguments: list[str]) -> tuple[int, str]:
        try:
            completed = subprocess.run(
                arguments,
                cwd=str(root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=10,
            )
            return completed.returncode, (completed.stdout or completed.stderr).strip()
        except (OSError, subprocess.SubprocessError) as exc:
            return 127, type(exc).__name__

    commit_exit, commit = run(["git", "rev-parse", "HEAD"])
    dirty_exit, dirty = run(["git", "status", "--porcelain"])
    return {
        "commit": commit if commit_exit == 0 else None,
        "dirty": bool(dirty) if dirty_exit == 0 else None,
        "exit_codes": {"commit": commit_exit, "dirty": dirty_exit},
    }


def build_machine_inventory(
    *, mode: str, provenance: Mapping[str, Any], root: Path | None = None
) -> dict[str, Any]:
    """Build the intentionally environment-specific companion JSON."""

    repo = (root or repository_root()).resolve()
    return {
        "schema": MACHINE_SCHEMA,
        "mode": mode,
        "profile": VALIDATE_PROFILE,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "architecture": platform.architecture()[0],
        },
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
        },
        "pyyaml_version": yaml.__version__,
        "git": _git_inventory(repo),
        "provenance": dict(provenance),
    }


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _resolve_ci_output(path: Path, root: Path) -> Path:
    ci_root = (root / "build" / "ci").resolve()
    candidate = path if path.is_absolute() else root / path
    resolved = candidate.resolve()
    try:
        resolved.relative_to(ci_root)
    except ValueError as exc:
        raise ValueError("output must resolve within repository build/ci") from exc
    if resolved.suffix.lower() != ".json":
        raise ValueError("output must use a .json filename")
    return resolved


def _default_result_path(root: Path, self_test: bool) -> Path:
    name = "check-ci-self-test.result.json" if self_test else "check-ci.result.json"
    return root / "build" / "ci" / name


def _default_machine_path(result_path: Path) -> Path:
    name = result_path.name
    if name.endswith(".result.json"):
        name = name[: -len(".result.json")] + ".machine.json"
    else:
        name = result_path.stem + ".machine.json"
    return result_path.with_name(name)


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check GitHub Actions common policy and validate.yml profile"
    )
    parser.add_argument(
        "--workflow",
        type=Path,
        default=None,
        help="workflow to check (default: .github/workflows/validate.yml)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run isolated positive and negative controls",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="result JSON path under build/ci",
    )
    parser.add_argument(
        "--machine-output",
        type=Path,
        default=None,
        help="machine JSON path under build/ci",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="print deterministic JSON without writing result or machine files",
    )
    args = parser.parse_args(argv)

    root = repository_root().resolve()
    workflow_path = args.workflow
    if workflow_path is None:
        workflow_path = root / ".github" / "workflows" / "validate.yml"
    elif not workflow_path.is_absolute():
        workflow_path = (Path.cwd() / workflow_path).resolve()

    try:
        report = (
            run_self_test(workflow_path, root=root)
            if args.self_test
            else build_policy_report(workflow_path, root=root)
        )
    except Exception as exc:  # noqa: BLE001 - CLI must emit JSON and fail closed
        provenance, _ = _source_provenance(root, workflow_path)
        report = {
            "schema": SELF_TEST_SCHEMA if args.self_test else POLICY_SCHEMA,
            "profile": VALIDATE_PROFILE,
            "policy_status": "FAIL",
            "program_status": "ERROR",
            "exit_code": 1,
            "provenance": provenance,
            "issues": [
                {
                    "code": "checker.error",
                    "location": "check_ci",
                    "message": f"checker failed closed: {type(exc).__name__}: {exc}",
                }
            ],
        }

    result_text = _json_text(report)
    if not args.no_write:
        try:
            result_path = _resolve_ci_output(
                args.output or _default_result_path(root, args.self_test), root
            )
            machine_path = _resolve_ci_output(
                args.machine_output or _default_machine_path(result_path), root
            )
            machine = build_machine_inventory(
                mode="self-test" if args.self_test else "normal",
                provenance=report.get("provenance", {}),
                root=root,
            )
            _atomic_write(result_path, result_text)
            _atomic_write(machine_path, _json_text(machine))
        except (OSError, ValueError) as exc:
            failure = dict(report)
            failure["policy_status"] = "FAIL"
            failure["program_status"] = "ERROR"
            failure["exit_code"] = 1
            failure["output_error"] = f"{type(exc).__name__}: {exc}"
            result_text = _json_text(failure)
            report = failure

    sys.stdout.write(result_text)
    return int(report.get("exit_code", 1))


if __name__ == "__main__":
    raise SystemExit(main())
