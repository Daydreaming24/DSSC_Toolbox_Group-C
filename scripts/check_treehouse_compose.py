#!/usr/bin/env python3
"""Static, fail-closed preflight for an opt-in Semantic Treehouse Compose file.

This checker never clones, builds, pulls, starts, or stops third-party resources.
It is deliberately separate from the core validation suite and must run before
any optional Treehouse Docker workload is considered.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import yaml
from yaml.nodes import MappingNode, ScalarNode, SequenceNode


SCHEMA = "dssc.treehouse.compose-preflight.v1"
BLOCK = "BLOCK"
REVIEW = "REVIEW"
INFO = "INFO"
_DIGEST_IMAGE = re.compile(r"^[^\s@]+@sha256:[0-9a-f]{64}$")
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")
_CONTROL_SOCKET_MARKERS = (
    "docker.sock",
    "containerd.sock",
    "podman.sock",
    "buildkitd.sock",
    "docker_engine",
)
_CREDENTIAL_MARKERS = (
    "/.ssh",
    "/.aws",
    "/.azure",
    "/.config/gcloud",
    "/.docker/config",
    "credentials",
    "id_rsa",
    "id_ed25519",
)
EXPECTED_REALIZED_NETWORK_OPTIONS = {
    "com.docker.network.enable_ipv4": "true",
    "com.docker.network.enable_ipv6": "false",
}


class _ComposeSafeLoader(yaml.SafeLoader):
    """SafeLoader with only the two value tags defined by Compose."""


def _construct_compose_value(loader: _ComposeSafeLoader, node: yaml.Node) -> Any:
    """Preserve a tagged value for single-file policy inspection."""

    if isinstance(node, ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, SequenceNode):
        return loader.construct_sequence(node, deep=True)
    if isinstance(node, MappingNode):
        return loader.construct_mapping(node, deep=True)
    raise yaml.constructor.ConstructorError(
        None,
        None,
        f"unsupported Compose tag node: {type(node).__name__}",
        node.start_mark,
    )


for _compose_tag in ("!override", "!reset"):
    _ComposeSafeLoader.add_constructor(_compose_tag, _construct_compose_value)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def _issue(
    issues: list[dict[str, str]],
    severity: str,
    code: str,
    location: str,
    message: str,
) -> None:
    issues.append(
        {
            "severity": severity,
            "code": code,
            "location": location,
            "message": message,
        }
    )


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def realized_network_options_match(value: Any) -> bool:
    """Return whether Docker's realized bridge options match the exact allowlist."""

    return (
        isinstance(value, dict)
        and all(isinstance(key, str) and isinstance(item, str) for key, item in value.items())
        and value == EXPECTED_REALIZED_NETWORK_OPTIONS
    )


def _is_path_source(source: str) -> bool:
    return (
        source.startswith((".", "..", "/", "~", "\\"))
        or bool(_WINDOWS_ABSOLUTE.match(source))
    )


def _resolve_source(source: str, compose_dir: Path) -> Path | None:
    if source.startswith("~"):
        return None
    if _WINDOWS_ABSOLUTE.match(source) or source.startswith(("/", "\\")):
        return Path(source)
    try:
        return (compose_dir / source).resolve()
    except OSError:
        return None


def _inspect_bind(
    issues: list[dict[str, str]],
    service: str,
    index: int,
    source: str,
    target: str,
    read_only: bool,
    compose_dir: Path,
    upstream_root: Path,
) -> None:
    location = f"services.{service}.volumes[{index}]"
    lowered = f"{source}:{target}".replace("\\", "/").lower()
    if any(marker in lowered for marker in _CONTROL_SOCKET_MARKERS):
        _issue(issues, BLOCK, "CONTROL_SOCKET_MOUNT", location, "daemon/control socket mount")
    if any(marker in lowered for marker in _CREDENTIAL_MARKERS):
        _issue(issues, BLOCK, "CREDENTIAL_MOUNT", location, "credential-bearing path mount")
    resolved = _resolve_source(source, compose_dir)
    if resolved is None or not _inside(resolved, upstream_root):
        _issue(issues, BLOCK, "BIND_OUTSIDE_UPSTREAM", location, "host bind is outside the pinned upstream root")
    else:
        _issue(
            issues,
            REVIEW,
            "HOST_BIND_MOUNT",
            location,
            "host bind mount requires explicit scope review" + (" (read-only)" if read_only else " (writable)"),
        )
    target_normalized = target.replace("\\", "/").lower()
    if not read_only and target_normalized in {"/", "/etc", "/usr", "/var", "/root", "/home"}:
        _issue(issues, BLOCK, "WRITABLE_SYSTEM_TARGET", location, "bind targets a writable system path")


def _inspect_volumes(
    issues: list[dict[str, str]],
    service: str,
    volumes: Any,
    compose_dir: Path,
    upstream_root: Path,
) -> None:
    for index, item in enumerate(_as_list(volumes)):
        location = f"services.{service}.volumes[{index}]"
        item_text = repr(item).replace("\\", "/").lower()
        if any(marker in item_text for marker in _CONTROL_SOCKET_MARKERS):
            _issue(issues, BLOCK, "CONTROL_SOCKET_MOUNT", location, "daemon/control socket mount")
        if any(marker in item_text for marker in _CREDENTIAL_MARKERS):
            _issue(issues, BLOCK, "CREDENTIAL_MOUNT", location, "credential-bearing mount source or target")
        if isinstance(item, str):
            windows_match = re.fullmatch(r"([A-Za-z]:[\\/][^:]*):([^:]+)(?::(.*))?", item)
            pieces = list(windows_match.groups()) if windows_match else item.split(":")
            if len(pieces) < 2:
                continue
            source, target = pieces[0], pieces[1]
            mode = pieces[2] if len(pieces) > 2 and pieces[2] else "rw"
            if _is_path_source(source):
                _inspect_bind(
                    issues,
                    service,
                    index,
                    source,
                    target,
                    "ro" in mode.split(","),
                    compose_dir,
                    upstream_root,
                )
        elif isinstance(item, dict):
            source = str(item.get("source", ""))
            target = str(item.get("target", ""))
            mount_type = str(item.get("type", "volume"))
            if mount_type == "bind":
                _inspect_bind(
                    issues,
                    service,
                    index,
                    source,
                    target,
                    bool(item.get("read_only", False)),
                    compose_dir,
                    upstream_root,
                )
            elif mount_type not in {"volume", "tmpfs"}:
                _issue(issues, BLOCK, "UNKNOWN_MOUNT_TYPE", location, mount_type)


def _parse_port(item: Any) -> tuple[str, str, str, str] | None:
    if isinstance(item, dict):
        host_ip = str(item.get("host_ip", ""))
        published = str(item.get("published", ""))
        target = str(item.get("target", ""))
        protocol = str(item.get("protocol", "tcp")).lower()
        return host_ip, published, target, protocol
    if isinstance(item, int) and not isinstance(item, bool):
        return "", "", str(item), "tcp"
    if not isinstance(item, str):
        return None
    value, separator, protocol = item.partition("/")
    protocol = protocol.lower() if separator else "tcp"
    if value.startswith("[") and "]:" in value:
        host, remainder = value.split("]:", 1)
        parts = remainder.split(":")
        if len(parts) == 2:
            return host + "]", parts[0], parts[1], protocol
    parts = value.split(":")
    if len(parts) == 3:
        return parts[0], parts[1], parts[2], protocol
    if len(parts) == 2:
        return "", parts[0], parts[1], protocol
    if len(parts) == 1:
        return "", "", parts[0], protocol
    return None


def _port_range(value: str) -> tuple[int, int] | None:
    if not value:
        return None
    match = re.fullmatch(r"([0-9]+)(?:-([0-9]+))?", value)
    if match is None:
        return None
    start = int(match.group(1))
    end = int(match.group(2) or match.group(1))
    if start > end or end > 65535:
        return None
    return start, end


def _hosts_overlap(left: str, right: str) -> bool:
    wildcards = {"", "0.0.0.0", "::", "[::]"}
    return left in wildcards or right in wildcards or left == right


def _inspect_ports(
    issues: list[dict[str, str]],
    service: str,
    ports: Any,
    seen: list[tuple[str, tuple[int, int], str, str]],
) -> None:
    for index, item in enumerate(_as_list(ports)):
        parsed = _parse_port(item)
        location = f"services.{service}.ports[{index}]"
        if parsed is None:
            _issue(issues, BLOCK, "INVALID_PORT", location, "unrecognized published port form")
            continue
        host, published, target, protocol = parsed
        host_normalized = host.lower()
        exposure = "loopback" if host_normalized in {"127.0.0.1", "::1", "[::1]"} else "external-or-unspecified"
        severity = REVIEW if exposure == "loopback" else BLOCK
        _issue(issues, severity, "PUBLISHED_PORT", location, f"{host or '*'}:{published or '*'}->{target}/{protocol} ({exposure})")
        published_range = _port_range(published)
        if published and published_range is None:
            _issue(issues, BLOCK, "INVALID_PORT", location, "published port or range is not understood")
            continue
        target_range = _port_range(target)
        if target_range is None or protocol not in {"tcp", "udp", "sctp"}:
            _issue(issues, BLOCK, "INVALID_PORT", location, "target port/range or protocol is not understood")
            continue
        if published_range is not None and published_range[1] - published_range[0] != target_range[1] - target_range[0]:
            _issue(issues, BLOCK, "INVALID_PORT", location, "published and target port ranges have different sizes")
            continue
        if published_range is None:
            continue
        for prior_host, prior_range, prior_protocol, prior_location in seen:
            overlap = published_range[0] <= prior_range[1] and prior_range[0] <= published_range[1]
            if protocol == prior_protocol and overlap and _hosts_overlap(host_normalized, prior_host):
                _issue(issues, BLOCK, "PORT_CONFLICT", location, f"conflicts with {prior_location}")
        seen.append((host_normalized, published_range, protocol, location))


def _inspect_reference_file(
    issues: list[dict[str, str]],
    code: str,
    location: str,
    source: str,
    compose_dir: Path,
    upstream_root: Path,
) -> None:
    resolved = _resolve_source(source, compose_dir)
    if resolved is None or not _inside(resolved, upstream_root):
        _issue(issues, BLOCK, code, location, "source resolves outside the pinned upstream root")
    elif not resolved.is_file():
        _issue(issues, BLOCK, code, location, "source file is missing")
    else:
        _issue(issues, REVIEW, code, location, "source file requires secret/log-redaction review")


def _dockerfile_logical_lines(source: str) -> list[str]:
    escape = "\\"
    escape_match = re.search(r"(?mi)^\s*#\s*escape\s*=\s*([\\`])\s*$", source)
    if escape_match is not None:
        escape = escape_match.group(1)
    logical: list[str] = []
    pending = ""
    for raw_line in source.splitlines():
        line = raw_line.rstrip()
        combined = pending + line.lstrip() if pending else line
        if combined.endswith(escape):
            pending = combined[: -len(escape)] + " "
        else:
            logical.append(combined)
            pending = ""
    if pending:
        logical.append(pending)
    return logical


def _dockerfile_reference_is_pinned(
    reference: str,
    stage_aliases: set[str],
    stage_count: int,
    *,
    allow_scratch: bool,
    allow_stage_index: bool,
) -> bool:
    value = reference.strip().strip('"\'').lower()
    if allow_scratch and value == "scratch":
        return True
    if value in stage_aliases:
        return True
    if allow_stage_index and value.isdigit() and int(value) < stage_count:
        return True
    return bool(_DIGEST_IMAGE.fullmatch(value))


def _dockerfile_image_risks(source: str) -> list[str]:
    risks: list[str] = []

    def add(message: str) -> None:
        if message not in risks:
            risks.append(message)

    for match in re.finditer(r"(?mi)^\s*#\s*syntax\s*=\s*([^\s]+)", source):
        frontend = match.group(1).lower()
        if not _DIGEST_IMAGE.fullmatch(frontend):
            add(f"Dockerfile syntax frontend is not digest-pinned: {frontend}")

    stage_aliases: set[str] = set()
    stage_count = 0
    from_count = 0
    for line_number, line in enumerate(_dockerfile_logical_lines(source), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        instruction = stripped.split(None, 1)[0].lower()
        if instruction == "from":
            match = re.fullmatch(
                r"(?i)from\s+(?:--platform=\S+\s+)?(\S+)(?:\s+as\s+([A-Za-z0-9_.-]+))?(?:\s+#.*)?",
                stripped,
            )
            if match is None:
                add(f"Dockerfile FROM instruction is not understood at line {line_number}")
                continue
            reference = match.group(1)
            if not _dockerfile_reference_is_pinned(
                reference,
                stage_aliases,
                stage_count,
                allow_scratch=True,
                allow_stage_index=False,
            ):
                add(f"Dockerfile FROM image is not digest-pinned at line {line_number}: {reference.lower()}")
            alias = match.group(2)
            if alias:
                stage_aliases.add(alias.lower())
            stage_count += 1
            from_count += 1
            continue

        if instruction == "copy":
            references = re.findall(r"(?i)(?:^|\s)--from=([^\s]+)", stripped)
            if "--from" in stripped.lower() and not references:
                add(f"Dockerfile COPY --from is not understood at line {line_number}")
            for reference in references:
                if not _dockerfile_reference_is_pinned(
                    reference,
                    stage_aliases,
                    stage_count,
                    allow_scratch=True,
                    allow_stage_index=True,
                ):
                    add(f"Dockerfile COPY --from image is not digest-pinned at line {line_number}: {reference.lower()}")

        if instruction == "run":
            mounts = re.findall(r"(?i)(?:^|\s)--mount=([^\s]+)", stripped)
            for mount in mounts:
                references = [part.split("=", 1)[1] for part in mount.split(",") if part.lower().startswith("from=")]
                if "from=" in mount.lower() and not references:
                    add(f"Dockerfile RUN --mount source is not understood at line {line_number}")
                for reference in references:
                    if not _dockerfile_reference_is_pinned(
                        reference,
                        stage_aliases,
                        stage_count,
                        allow_scratch=True,
                        allow_stage_index=True,
                    ):
                        add(f"Dockerfile RUN --mount image is not digest-pinned at line {line_number}: {reference.lower()}")

    if from_count == 0:
        add("Dockerfile contains no understood FROM instruction")
    return risks


def _inspect_build(
    issues: list[dict[str, str]],
    build_files: list[str],
    build_contexts: list[str],
    service: str,
    build: Any,
    compose_dir: Path,
    upstream_root: Path,
) -> None:
    if isinstance(build, str):
        context_value, dockerfile_value = build, "Dockerfile"
    elif isinstance(build, dict):
        context_value = str(build.get("context", "."))
        dockerfile_value = str(build.get("dockerfile", "Dockerfile"))
    else:
        _issue(issues, BLOCK, "INVALID_BUILD", f"services.{service}.build", "build definition is not understood")
        return
    context = _resolve_source(context_value, compose_dir)
    if context is None or not _inside(context, upstream_root) or not context.is_dir():
        _issue(issues, BLOCK, "BUILD_CONTEXT_BOUNDARY", f"services.{service}.build.context", "context is missing or outside pinned upstream")
        return
    dockerfile = (context / dockerfile_value).resolve()
    if not _inside(dockerfile, upstream_root) or not dockerfile.is_file():
        _issue(issues, BLOCK, "DOCKERFILE_BOUNDARY", f"services.{service}.build.dockerfile", "Dockerfile is missing or outside pinned upstream")
        return
    build_contexts.append(context.relative_to(upstream_root).as_posix() or ".")
    build_files.append(dockerfile.relative_to(upstream_root).as_posix())
    try:
        source = dockerfile.read_text(encoding="utf-8", errors="replace").lower()
    except OSError as exc:
        _issue(issues, BLOCK, "DOCKERFILE_READ", f"services.{service}.build.dockerfile", str(exc))
        return
    risky = _dockerfile_image_risks(source)
    if re.search(r"(?m)^\s*(copy|add)\s+[^\n]*(\.env|\.ssh|credential|secret)", source):
        risky.append("credential-like COPY/ADD")
    if re.search(r"(?m)^\s*add\s+https?://", source):
        risky.append("remote ADD")
    if re.search(r"(curl|wget)[^\n|]*\|\s*(sh|bash)", source):
        risky.append("download piped to shell")
    if risky:
        _issue(issues, BLOCK, "UNSAFE_BUILD_SCRIPT", f"services.{service}.build.dockerfile", ", ".join(risky))
    else:
        _issue(issues, REVIEW, "SOURCE_BUILD", f"services.{service}.build", "build is pinned by upstream commit; Dockerfile review still required")


def inspect_compose(compose_path: Path, upstream_root: Path, project_name: str) -> dict[str, Any]:
    """Return deterministic preflight findings without executing Compose."""

    compose_path = compose_path.resolve()
    upstream_root = upstream_root.resolve()
    issues: list[dict[str, str]] = []
    build_files: list[str] = []
    build_contexts: list[str] = []
    if not _inside(compose_path, upstream_root):
        raise ValueError("compose file must be inside the pinned upstream root")
    if not compose_path.is_file():
        raise ValueError("compose file does not exist")
    try:
        compose_text = compose_path.read_text(encoding="utf-8")
        document = yaml.load(compose_text, Loader=_ComposeSafeLoader)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ValueError(f"unable to parse compose file: {exc}") from exc
    if not isinstance(document, dict) or not isinstance(document.get("services"), dict) or not document["services"]:
        raise ValueError("compose document must contain a non-empty services mapping")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,62}", project_name):
        raise ValueError("project name must be an explicit lowercase Compose-safe identifier")
    # Compose expands both ``$NAME`` and ``${NAME}``.  ``$$`` is the only
    # supported literal-dollar escape, so remove escaped pairs before looking
    # for any remaining expansion token.  This also catches ``$$$NAME``: the
    # first pair is literal and the third dollar still expands at runtime.
    interpolation_surface = re.sub(r"\$\$", "", compose_text)
    if re.search(r"\$(?:[A-Za-z_][A-Za-z0-9_]*|\{)", interpolation_surface):
        _issue(issues, BLOCK, "UNRESOLVED_INTERPOLATION", "compose", "environment interpolation must be resolved and reviewed before preflight")
    if document.get("include") is not None:
        _issue(issues, BLOCK, "COMPOSE_INCLUDE", "include", "included compose files are outside this single-file preflight")

    declared_name = document.get("name")
    if declared_name is not None and declared_name != project_name:
        _issue(issues, BLOCK, "PROJECT_NAME_CONFLICT", "name", "compose name differs from the approved project name")
    elif declared_name is None:
        _issue(issues, INFO, "PROJECT_NAME_CLI_REQUIRED", "name", f"invoke Compose with --project-name {project_name}")

    seen_ports: list[tuple[str, tuple[int, int], str, str]] = []
    compose_dir = compose_path.parent
    for service, config in sorted(document["services"].items()):
        location = f"services.{service}"
        if not isinstance(config, dict):
            _issue(issues, BLOCK, "INVALID_SERVICE", location, "service definition is not a mapping")
            continue
        if config.get("privileged") not in {None, False}:
            _issue(issues, BLOCK, "PRIVILEGED", f"{location}.privileged", "privileged container")
        for key, code in (("cap_add", "CAP_ADD"), ("devices", "DEVICES")):
            if _as_list(config.get(key)):
                _issue(issues, BLOCK, code, f"{location}.{key}", "elevated host capability/resource access")
        security_opts = [str(value).lower() for value in _as_list(config.get("security_opt"))]
        unsafe_opts = [value for value in security_opts if value not in {"no-new-privileges:true", "no-new-privileges=true"}]
        if unsafe_opts:
            _issue(issues, BLOCK, "SECURITY_OPT", f"{location}.security_opt", ", ".join(unsafe_opts))
        user = config.get("user")
        if user is None:
            _issue(issues, REVIEW, "USER_UNDECLARED", f"{location}.user", "image default user requires inspection")
        elif str(user).strip().lower().split(":", 1)[0] in {"0", "root"}:
            _issue(issues, BLOCK, "ROOT_USER", f"{location}.user", "high-privilege user")
        for key, code in (("pid", "HOST_PID"), ("ipc", "HOST_IPC"), ("uts", "HOST_UTS")):
            if str(config.get(key, "")).lower() == "host":
                _issue(issues, BLOCK, code, f"{location}.{key}", "host namespace sharing")
        network_mode = str(config.get("network_mode", "")).lower()
        if network_mode == "host":
            _issue(issues, BLOCK, "HOST_NETWORK", f"{location}.network_mode", "host network mode")
        elif network_mode.startswith(("container:", "service:")):
            _issue(issues, BLOCK, "SHARED_NETWORK_NAMESPACE", f"{location}.network_mode", "shared container/service network namespace")
        if config.get("networks"):
            _issue(issues, REVIEW, "SERVICE_NETWORKS", f"{location}.networks", "additional networks require egress review")
        _inspect_ports(issues, service, config.get("ports"), seen_ports)
        _inspect_volumes(issues, service, config.get("volumes"), compose_dir, upstream_root)

        image = config.get("image")
        build = config.get("build")
        if image is not None and not _DIGEST_IMAGE.fullmatch(str(image)):
            _issue(issues, BLOCK, "IMAGE_NOT_DIGEST_PINNED", f"{location}.image", "third-party image must use @sha256:<64 hex>")
        if build is not None:
            _inspect_build(issues, build_files, build_contexts, service, build, compose_dir, upstream_root)
        if image is None and build is None:
            _issue(issues, BLOCK, "NO_IMAGE_OR_BUILD", location, "service has neither image nor pinned-commit build")

        for index, env_file in enumerate(_as_list(config.get("env_file"))):
            source = str(env_file.get("path", "")) if isinstance(env_file, dict) else str(env_file)
            _inspect_reference_file(issues, "ENV_FILE", f"{location}.env_file[{index}]", source, compose_dir, upstream_root)
        if config.get("secrets"):
            _issue(issues, REVIEW, "SERVICE_SECRETS", f"{location}.secrets", "secret sources and log exposure require review")
        if config.get("configs"):
            _issue(issues, REVIEW, "SERVICE_CONFIGS", f"{location}.configs", "config sources and log exposure require review")
        environment = config.get("environment")
        environment_text = repr(environment).lower() if environment is not None else ""
        if any(marker in environment_text for marker in ("token", "password", "passwd", "secret", "credential", "private_key")):
            _issue(issues, REVIEW, "SENSITIVE_ENVIRONMENT", f"{location}.environment", "credential-like environment names or values require source and log review")
        process_text = " ".join(str(value) for value in _as_list(config.get("entrypoint")) + _as_list(config.get("command"))).lower()
        if any(marker in process_text for marker in ("printenv", "env |", "set -x", "cat .env", "cat /.env")):
            _issue(issues, BLOCK, "LOG_DISCLOSURE_COMMAND", f"{location}.command", "command may print environment or secret material")
        if config.get("container_name"):
            _issue(issues, REVIEW, "FIXED_CONTAINER_NAME", f"{location}.container_name", "fixed name can collide outside the project boundary")
        if config.get("volumes_from"):
            _issue(issues, BLOCK, "VOLUMES_FROM", f"{location}.volumes_from", "inherits mounts outside this service review")
        if config.get("extends"):
            _issue(issues, BLOCK, "COMPOSE_EXTENDS", f"{location}.extends", "inherited service configuration is outside this single-file preflight")
        if config.get("userns_mode") == "host":
            _issue(issues, BLOCK, "HOST_USER_NAMESPACE", f"{location}.userns_mode", "host user namespace")
        if config.get("group_add"):
            _issue(issues, REVIEW, "GROUP_ADD", f"{location}.group_add", "supplementary groups require privilege review")
        if config.get("read_only") is not True:
            _issue(issues, REVIEW, "WRITABLE_ROOT_FILESYSTEM", f"{location}.read_only", "container root filesystem is writable")
        logging = config.get("logging")
        if isinstance(logging, dict) and str(logging.get("driver", "")).lower() not in {"", "json-file", "local", "none"}:
            _issue(issues, BLOCK, "REMOTE_LOG_DRIVER", f"{location}.logging", "logging driver may disclose data outside the project")

    for section, code in (("networks", "TOP_LEVEL_NETWORK"), ("volumes", "TOP_LEVEL_VOLUME")):
        values = document.get(section, {})
        if isinstance(values, dict):
            for name, config in sorted(values.items()):
                if isinstance(config, dict) and config.get("external") is True:
                    _issue(issues, BLOCK, f"EXTERNAL_{code}", f"{section}.{name}", "external resource exceeds project cleanup boundary")
                if section == "volumes" and isinstance(config, dict) and config.get("driver_opts"):
                    _issue(issues, BLOCK, "VOLUME_DRIVER_OPTS", f"{section}.{name}.driver_opts", "driver options can create unreviewed host binds or external storage")

    for section in ("secrets", "configs"):
        values = document.get(section, {})
        if not isinstance(values, dict):
            continue
        for name, config in sorted(values.items()):
            location = f"{section}.{name}"
            if not isinstance(config, dict):
                _issue(issues, BLOCK, "INVALID_SECRET_CONFIG", location, "definition is not a mapping")
            elif config.get("external") is True:
                _issue(issues, BLOCK, "EXTERNAL_SECRET_CONFIG", location, "external secret/config exceeds project boundary")
            elif isinstance(config.get("file"), str):
                _inspect_reference_file(issues, "SECRET_CONFIG_FILE", f"{location}.file", config["file"], compose_dir, upstream_root)
            elif section == "secrets":
                _issue(issues, REVIEW, "SECRET_SOURCE_UNKNOWN", location, "secret source requires explicit provenance review")

    issues.sort(key=lambda item: (item["severity"], item["code"], item["location"], item["message"]))
    blocking = sum(item["severity"] == BLOCK for item in issues)
    review = sum(item["severity"] == REVIEW for item in issues)
    status = "BLOCKED" if blocking else ("REVIEW_REQUIRED" if review else "PASS")
    return {
        "schema": SCHEMA,
        "status": status,
        "execution_authorized": False,
        "compose_path": compose_path.relative_to(upstream_root).as_posix(),
        "compose_sha256": _sha256(compose_path),
        "project_name": project_name,
        "service_count": len(document["services"]),
        "blocking_count": blocking,
        "review_count": review,
        "build_inputs": sorted(set(build_files + build_contexts)),
        "build_files": sorted(set(build_files)),
        "build_contexts": sorted(set(build_contexts)),
        "issues": issues,
        "cleanup_contract": {
            "compose_project_only": True,
            "default_down_removes_volumes": False,
            "required_resource_label": "com.docker.compose.project",
        },
    }


def verify_upstream_pin(
    upstream_root: Path,
    expected_commit: str,
    required_files: list[str],
    required_directories: list[str] | None = None,
) -> list[dict[str, str]]:
    """Verify HEAD, cleanliness, files, and build directories against one commit."""

    issues: list[dict[str, str]] = []
    if not re.fullmatch(r"[0-9a-f]{40}", expected_commit):
        _issue(issues, BLOCK, "INVALID_EXPECTED_COMMIT", "upstream.commit", "expected commit must be 40 lowercase hex characters")
        return issues

    def git(*arguments: str) -> tuple[int, str]:
        completed = subprocess.run(
            ["git", "-C", str(upstream_root), *arguments],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return completed.returncode, completed.stdout.strip()

    code, head = git("rev-parse", "--verify", "HEAD")
    if code != 0 or head != expected_commit:
        _issue(issues, BLOCK, "UPSTREAM_HEAD_MISMATCH", "upstream.commit", "checked-out HEAD differs from the approved full commit")
        return issues
    code, dirty = git("status", "--porcelain=v1", "--untracked-files=all")
    if code != 0:
        _issue(issues, BLOCK, "UPSTREAM_STATUS_ERROR", "upstream.worktree", "unable to inspect upstream worktree state")
    elif dirty:
        _issue(issues, BLOCK, "UPSTREAM_DIRTY", "upstream.worktree", "upstream worktree contains tracked or untracked changes")
    code, tree_text = git("ls-tree", "-r", "--name-only", "-z", expected_commit)
    if code != 0:
        _issue(issues, BLOCK, "UPSTREAM_TREE_ERROR", "upstream.commit", "unable to enumerate pinned commit")
        return issues
    tree = {path for path in tree_text.split("\0") if path}
    for relpath in sorted(set(required_files)):
        if relpath not in tree:
            _issue(issues, BLOCK, "BUILD_INPUT_NOT_PINNED", relpath, "required compose/Dockerfile is absent from the pinned commit tree")
    for relpath in sorted(set(required_directories or [])):
        prefix = "" if relpath == "." else relpath.rstrip("/") + "/"
        if not any(path.startswith(prefix) for path in tree):
            _issue(issues, BLOCK, "BUILD_CONTEXT_NOT_PINNED", relpath, "build context has no files in the pinned commit tree")
    return issues


def _merge_pin_issues(result: dict[str, Any], pin_issues: list[dict[str, str]], expected_commit: str) -> None:
    issues = list(result["issues"]) + pin_issues
    issues.sort(key=lambda item: (item["severity"], item["code"], item["location"], item["message"]))
    blocking = sum(item["severity"] == BLOCK for item in issues)
    review = sum(item["severity"] == REVIEW for item in issues)
    result["issues"] = issues
    result["blocking_count"] = blocking
    result["review_count"] = review
    result["status"] = "BLOCKED" if blocking else ("REVIEW_REQUIRED" if review else "PASS")
    result["upstream_commit"] = expected_commit


def _write_output(path: Path, result: dict[str, Any], repo_root: Path) -> None:
    allowed = (repo_root / "build" / "evidence" / "treehouse").resolve()
    resolved = path.resolve()
    if not _inside(resolved, allowed):
        raise ValueError("output must resolve inside build/evidence/treehouse")
    allowed.mkdir(parents=True, exist_ok=True)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _error_result(error: OSError | ValueError) -> dict[str, str]:
    return {"schema": SCHEMA, "status": "ERROR", "error": str(error)}


def _self_test(output: Path | None, repo_root: Path) -> int:
    cases = {
        "privileged": ("services:\n  app:\n    image: x/y@sha256:" + "a" * 64 + "\n    privileged: true\n    user: '1000'\n", "PRIVILEGED"),
        "socket": ("services:\n  app:\n    image: x/y@sha256:" + "a" * 64 + "\n    user: '1000'\n    volumes: ['./docker.sock:/var/run/docker.sock']\n", "CONTROL_SOCKET_MOUNT"),
        "unfixed_image": ("services:\n  app:\n    image: x/y:latest\n    user: '1000'\n", "IMAGE_NOT_DIGEST_PINNED"),
        "host_network": ("services:\n  app:\n    image: x/y@sha256:" + "a" * 64 + "\n    user: '1000'\n    network_mode: host\n", "HOST_NETWORK"),
        "public_port": ("services:\n  app:\n    image: x/y@sha256:" + "a" * 64 + "\n    user: '1000'\n    ports: ['8080:80']\n", "PUBLISHED_PORT"),
        "root_user": ("services:\n  app:\n    image: x/y@sha256:" + "a" * 64 + "\n    user: root\n", "ROOT_USER"),
        "root_user_with_group": ("services:\n  app:\n    image: x/y@sha256:" + "a" * 64 + "\n    user: '0:1000'\n", "ROOT_USER"),
        "interpolation": ("services:\n  app:\n    image: x/y@sha256:" + "a" * 64 + "\n    privileged: ${PRIVILEGED}\n    user: '1000'\n", "UNRESOLVED_INTERPOLATION"),
        "bare_interpolation": ("services:\n  app:\n    image: x/y@sha256:" + "a" * 64 + "\n    user: '$RUN_USER'\n    volumes: ['$MOUNT']\n", "UNRESOLVED_INTERPOLATION"),
        "windows_bind": ("services:\n  app:\n    image: x/y@sha256:" + "a" * 64 + "\n    user: '1000'\n    volumes: ['C:\\\\Users\\\\person:/data']\n", "BIND_OUTSIDE_UPSTREAM"),
        "volumes_from": ("services:\n  app:\n    image: x/y@sha256:" + "a" * 64 + "\n    user: '1000'\n    volumes_from: ['container:other']\n", "VOLUMES_FROM"),
        "shared_network": ("services:\n  app:\n    image: x/y@sha256:" + "a" * 64 + "\n    user: '1000'\n    network_mode: container:other\n", "SHARED_NETWORK_NAMESPACE"),
        "extends": ("services:\n  app:\n    image: x/y@sha256:" + "a" * 64 + "\n    user: '1000'\n    extends:\n      file: other.yml\n      service: base\n", "COMPOSE_EXTENDS"),
        "volume_driver_bind": ("services:\n  app:\n    image: x/y@sha256:" + "a" * 64 + "\n    user: '1000'\n    volumes: ['data:/data']\nvolumes:\n  data:\n    driver_opts:\n      type: none\n      o: bind\n      device: /etc\n", "VOLUME_DRIVER_OPTS"),
        "port_conflict": (
            "services:\n"
            "  first:\n    image: x/y@sha256:" + "a" * 64 + "\n    user: '1000'\n    ports: ['0.0.0.0:8080-8082:80-82']\n"
            "  second:\n    image: x/y@sha256:" + "a" * 64 + "\n    user: '1000'\n    ports: ['127.0.0.1:8081:81']\n",
            "PORT_CONFLICT",
        ),
        "compose_override_tag": (
            "services:\n"
            "  app:\n    image: x/y@sha256:" + "a" * 64 + "\n    user: '1000'\n    ports: !override ['8080:80']\n",
            "PUBLISHED_PORT",
        ),
        "compose_reset_tag": (
            "services:\n"
            "  app:\n    image: x/y@sha256:" + "a" * 64 + "\n    user: '1000'\n    privileged: !reset true\n",
            "PRIVILEGED",
        ),
    }
    observed: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="dssc-treehouse-preflight-") as directory:
        root = Path(directory)
        for name, (source, expected) in sorted(cases.items()):
            compose = root / f"{name}.yml"
            compose.write_text(source, encoding="utf-8", newline="\n")
            result = inspect_compose(compose, root, "dssc-treehouse-test")
            codes = {item["code"] for item in result["issues"]}
            passed = expected in codes and result["status"] in {"BLOCKED", "REVIEW_REQUIRED"}
            observed.append({"case": name, "expected_code": expected, "passed": passed})

        unknown_compose = root / "compose-unknown-tag.yml"
        unknown_compose.write_text(
            "services:\n  app:\n    image: !unknown x/y\n    user: '1000'\n",
            encoding="utf-8",
            newline="\n",
        )
        unknown_error: ValueError | None = None
        try:
            inspect_compose(unknown_compose, root, "dssc-treehouse-test")
        except ValueError as exc:
            unknown_error = exc
        observed.append(
            {
                "case": "compose_unknown_tag",
                "expected_code": "VALUE_ERROR",
                "passed": unknown_error is not None and "!unknown" in str(unknown_error),
            }
        )

        error_repo = root / "error-output-repo"
        error_output = error_repo / "build" / "evidence" / "treehouse" / "error.json"
        error_write_passed = False
        if unknown_error is not None:
            error_payload = _error_result(unknown_error)
            _write_output(error_output, error_payload, error_repo)
            written_payload = json.loads(error_output.read_text(encoding="utf-8"))
            error_write_passed = written_payload == error_payload
        observed.append(
            {
                "case": "compose_error_output",
                "expected_code": "ERROR_OUTPUT_WRITTEN",
                "passed": error_write_passed,
            }
        )

        digest = "a" * 64
        safe_dockerfile = (
            f"# syntax=docker/dockerfile:1@sha256:{digest}\n"
            "FROM scratch AS seed\n"
            f"FROM x/base@sha256:{digest} AS builder\n"
            "COPY --from=seed /seed /seed\n"
            "FROM builder AS final\n"
            "COPY --from=0 /seed /seed-copy\n"
            f"COPY --from=x/tool@sha256:{digest} /tool /tool\n"
            f"RUN --mount=type=bind,from=x/assets@sha256:{digest},target=/src true\n"
        )
        dockerfile_cases = {
            "dockerfile_unpinned_from": (f"FROM x/base:latest\n", False),
            "dockerfile_unpinned_syntax": (f"# syntax=docker/dockerfile:1\nFROM x/base@sha256:{digest}\n", False),
            "dockerfile_unpinned_copy_from": (f"FROM x/base@sha256:{digest}\nCOPY --from=x/tool:latest /tool /tool\n", False),
            "dockerfile_unpinned_run_mount": (f"FROM x/base@sha256:{digest}\nRUN --mount=type=bind,from=x/assets:latest,target=/src true\n", False),
            "dockerfile_safe_multistage": (safe_dockerfile, True),
        }
        for name, (dockerfile_source, should_be_safe) in sorted(dockerfile_cases.items()):
            case_root = root / name
            case_root.mkdir()
            (case_root / "Dockerfile").write_text(dockerfile_source, encoding="utf-8", newline="\n")
            compose = case_root / "compose.yml"
            compose.write_text(
                "services:\n  app:\n    build: .\n    user: '1000'\n    read_only: true\n",
                encoding="utf-8",
                newline="\n",
            )
            result = inspect_compose(compose, case_root, "dssc-treehouse-test")
            codes = {item["code"] for item in result["issues"]}
            passed = (
                "SOURCE_BUILD" in codes and "UNSAFE_BUILD_SCRIPT" not in codes
                if should_be_safe
                else "UNSAFE_BUILD_SCRIPT" in codes
            )
            observed.append(
                {
                    "case": name,
                    "expected_code": "SOURCE_BUILD" if should_be_safe else "UNSAFE_BUILD_SCRIPT",
                    "passed": passed,
                }
            )

        pin_root = root / "pin-case"
        (pin_root / "app").mkdir(parents=True)
        (pin_root / "compose.yml").write_text(
            "services:\n  app:\n    build: ./app\n    user: '1000'\n    read_only: true\n",
            encoding="utf-8",
            newline="\n",
        )
        (pin_root / "app" / "Dockerfile").write_text(
            f"FROM x/base@sha256:{digest}\n",
            encoding="utf-8",
            newline="\n",
        )
        git_commands = [
            ["init", "--quiet", "--object-format=sha1"],
            ["add", "."],
            [
                "-c",
                "user.name=DSSC Audit",
                "-c",
                "user.email=audit@example.invalid",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "--quiet",
                "--no-verify",
                "-m",
                "pin fixture",
            ],
        ]
        git_ok = True
        for command in git_commands:
            completed = subprocess.run(["git", "-C", str(pin_root), *command], check=False, capture_output=True)
            git_ok = git_ok and completed.returncode == 0
        head_result = subprocess.run(
            ["git", "-C", str(pin_root), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        head = head_result.stdout.strip()
        git_ok = git_ok and head_result.returncode == 0
        positive_pin = verify_upstream_pin(pin_root, head, ["compose.yml", "app/Dockerfile"], ["app"]) if git_ok else []
        observed.append(
            {
                "case": "pinned_build_directory",
                "expected_code": "NO_PIN_ISSUES",
                "passed": git_ok and not positive_pin,
            }
        )
        missing_file = verify_upstream_pin(pin_root, head, ["missing.yml"], ["app"]) if git_ok else []
        observed.append(
            {
                "case": "unpinned_required_file",
                "expected_code": "BUILD_INPUT_NOT_PINNED",
                "passed": git_ok and any(item["code"] == "BUILD_INPUT_NOT_PINNED" for item in missing_file),
            }
        )
        missing_directory = verify_upstream_pin(pin_root, head, ["compose.yml"], ["missing-context"]) if git_ok else []
        observed.append(
            {
                "case": "unpinned_build_directory",
                "expected_code": "BUILD_CONTEXT_NOT_PINNED",
                "passed": git_ok and any(item["code"] == "BUILD_CONTEXT_NOT_PINNED" for item in missing_directory),
            }
        )
        invalid_pin = verify_upstream_pin(root, "main", [])
        invalid_pin_passed = any(item["code"] == "INVALID_EXPECTED_COMMIT" for item in invalid_pin)
        observed.append({"case": "invalid_expected_commit", "expected_code": "INVALID_EXPECTED_COMMIT", "passed": invalid_pin_passed})

        runtime_option_cases = {
            "realized_network_options_exact": (dict(EXPECTED_REALIZED_NETWORK_OPTIONS), True),
            "realized_network_options_exact_reversed": (dict(reversed(tuple(EXPECTED_REALIZED_NETWORK_OPTIONS.items()))), True),
            "realized_network_options_empty": ({}, False),
            "realized_network_options_missing_ipv4": ({"com.docker.network.enable_ipv6": "false"}, False),
            "realized_network_options_missing_ipv6": ({"com.docker.network.enable_ipv4": "true"}, False),
            "realized_network_options_extra_key": ({**EXPECTED_REALIZED_NETWORK_OPTIONS, "com.docker.network.bridge.enable_icc": "true"}, False),
            "realized_network_options_extra_host_binding": ({**EXPECTED_REALIZED_NETWORK_OPTIONS, "com.docker.network.bridge.host_binding_ipv4": "0.0.0.0"}, False),
            "realized_network_options_extra_masquerade": ({**EXPECTED_REALIZED_NETWORK_OPTIONS, "com.docker.network.bridge.enable_ip_masquerade": "true"}, False),
            "realized_network_options_extra_mtu": ({**EXPECTED_REALIZED_NETWORK_OPTIONS, "com.docker.network.driver.mtu": "1500"}, False),
            "realized_network_options_extra_gateway_mode": ({**EXPECTED_REALIZED_NETWORK_OPTIONS, "com.docker.network.bridge.gateway_mode_ipv4": "nat"}, False),
            "realized_network_options_extra_unknown": ({**EXPECTED_REALIZED_NETWORK_OPTIONS, "dssc.example.unknown": "true"}, False),
            "realized_network_options_key_case_changed": ({"com.docker.network.enable_IPv4": "true", "com.docker.network.enable_ipv6": "false"}, False),
            "realized_network_options_wrong_ipv4": ({**EXPECTED_REALIZED_NETWORK_OPTIONS, "com.docker.network.enable_ipv4": "false"}, False),
            "realized_network_options_wrong_ipv6": ({**EXPECTED_REALIZED_NETWORK_OPTIONS, "com.docker.network.enable_ipv6": "true"}, False),
            "realized_network_options_boolean_values": ({"com.docker.network.enable_ipv4": True, "com.docker.network.enable_ipv6": False}, False),
            "realized_network_options_not_mapping": (["com.docker.network.enable_ipv4=true"], False),
            "realized_network_options_null": (None, False),
        }
        for name, (projection, expected) in runtime_option_cases.items():
            observed.append(
                {
                    "case": name,
                    "case_group": "runtime-network-options",
                    "expected_code": "EXACT_RUNTIME_NETWORK_OPTIONS" if expected else "REJECT_RUNTIME_NETWORK_OPTIONS",
                    "passed": realized_network_options_match(projection) is expected,
                }
            )
    runtime_option_results = [
        item for item in observed if item.get("case_group") == "runtime-network-options"
    ]
    result = {
        "schema": "dssc.treehouse.compose-preflight-self-test.v1",
        "status": "PASS" if all(item["passed"] for item in observed) else "FAIL",
        "executed": len(observed),
        "passed": sum(bool(item["passed"]) for item in observed),
        "failed": sum(not bool(item["passed"]) for item in observed),
        "runtime_options_controls": {
            "expected_options": EXPECTED_REALIZED_NETWORK_OPTIONS,
            "executed": len(runtime_option_results),
            "passed": sum(bool(item["passed"]) for item in runtime_option_results),
            "failed": sum(not bool(item["passed"]) for item in runtime_option_results),
            "execution_boundary": {
                "docker_calls": 0,
                "subprocess_calls": 0,
                "filesystem_inputs": 0,
            },
        },
        "cases": observed,
    }
    if output is not None:
        _write_output(output, result, repo_root)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compose", type=Path)
    parser.add_argument("--upstream-root", type=Path)
    parser.add_argument("--project-name", default="dssc-semantic-treehouse-v04")
    parser.add_argument("--expected-commit")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    if args.self_test:
        return _self_test(args.output, repo_root)
    if args.compose is None or args.upstream_root is None or args.expected_commit is None:
        parser.error("--compose, --upstream-root, and --expected-commit are required unless --self-test is used")
    try:
        result = inspect_compose(args.compose, args.upstream_root, args.project_name)
        required_files = [result["compose_path"], *result["build_files"]]
        pin_issues = verify_upstream_pin(
            args.upstream_root.resolve(),
            args.expected_commit,
            required_files,
            result["build_contexts"],
        )
        _merge_pin_issues(result, pin_issues, args.expected_commit)
        if args.output is not None:
            _write_output(args.output, result, repo_root)
    except (OSError, ValueError) as exc:
        result = _error_result(exc)
        if args.output is not None:
            try:
                _write_output(args.output, result, repo_root)
            except (OSError, ValueError) as output_exc:
                result["output_error"] = str(output_exc)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
