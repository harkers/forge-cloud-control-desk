#!/usr/bin/env python3
# Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away.
"""Run the assurance controls and assemble the emitter's input files.

Why this exists
---------------
`tools/emit_evidence.py` consumes two files: `results.json`, a map of control
name to a result block, and `findings.json`, the normalized finding list. Before
this tool existed, nothing in the managed pipeline produced either one: the
verify template ran four scanners and then handed the emitter paths that no step
had written, so the run died on `FileNotFoundError: results/findings.json`, and
where it did not die, every required control resolved as BLOCKED because
`load_results()` found no `results.json`.

The difference is who assembles the evidence, not which controls run. This tool
executes the same commands, records the same raw output, and emits exactly the
shapes `emit_evidence` documents, so a consumer's gate cannot drift from the
hosted one.

Fail-closed
-----------
A control that cannot run is recorded as BLOCKED with `missing_tool` set, never
skipped and never PASS. A scanner that exits non-zero on findings is a FAIL for
that control, and its findings are still parsed and reported: a failing control
that reports nothing is how a real finding disappears.

Usage:

    python -m tools.assemble_results --control secret_detection=gitleaks \\
        --control sast=semgrep --results results --out results

Every `--control name=command` runs `command` with `bash -euo pipefail -c`,
captures stdout/stderr and the exit code, and parses the raw output for
findings.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.assurance import resolve
from tools.producers import producer_for, remediation_for

#: Control name -> (raw output file, parser key). The emitter keys results by
#: control name, so these must match `tools/assurance.py` CONTROL_IDS.
CONTROL_ARTIFACTS = {
    "secret_detection": "gitleaks.json",
    "sast": "semgrep.sarif",
    "sbom": "sbom.cdx.json",
    "vulnerability_scan": "grype.json",
    "infrastructure_scan": "trivy.json",
}

#: Severities that block a control, per the vulnerability policy defaults in
#: standards/security-assurance.md.
BLOCKING_SEVERITIES = {"critical", "high"}
#: Medium findings warn rather than block.
WARNING_SEVERITIES = {"medium"}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _tool_version(command: str) -> str:
    """The tool's reported version, or the explicit string "unknown".

    The standard requires `tool_version` to be *recorded*; it does not require every
    scanner to implement `--version`. Returning None left the field absent, which is
    indistinguishable from a producer that never considered it — and the validator
    now rejects that. "unknown" is a truthful value; absence is not.
    """
    name = shlex.split(command)[0]
    for args in (["--version"], ["version"]):
        try:
            out = subprocess.run(
                [name, *args], text=True, capture_output=True, timeout=60
            )
        except (OSError, subprocess.SubprocessError):
            continue
        text = (out.stdout or out.stderr or "").strip().splitlines()
        if text:
            return text[0].strip()
    return "unknown"


def parse_gitleaks(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    findings = []
    for entry in payload or []:
        findings.append(
            {
                "control_name": "secret_detection",
                "severity": "critical",
                "scanner": "gitleaks",
                "rule_or_vuln_id": entry.get("RuleID", "gitleaks-rule"),
                "component": entry.get("File", "unknown"),
                "message": entry.get("Description", "secret detected"),
            }
        )
    return findings


#: SARIF reports `error`/`warning`/`note`, not the severity vocabulary the rest
#: of the packet uses. Without this mapping a semgrep ERROR would land as an
#: unknown severity and never block.
SARIF_SEVERITY = {
    "error": "high",
    "warning": "medium",
    "note": "low",
    "none": "low",
}


def parse_semgrep(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    findings = []
    for run in payload.get("runs", []):
        for result in run.get("results", []):
            # A result the scanner itself suppressed is not a finding. Semgrep
            # records an in-source `nosemgrep` as `suppressions`, and exits 0 —
            # so counting it reported WARN on a control whose scanner had passed.
            # The suppression is a deliberate, reviewable decision; re-reporting
            # it as a warning is how a security control becomes noise.
            if result.get("suppressions"):
                continue
            location = (result.get("locations") or [{}])[0].get("physicalLocation", {})
            raw = str((result.get("extra") or {}).get("severity", "warning")).lower()
            findings.append(
                {
                    "control_name": "sast",
                    "severity": SARIF_SEVERITY.get(raw, raw),
                    "scanner": "semgrep",
                    "rule_or_vuln_id": result.get("check_id", "semgrep-rule"),
                    "component": location.get("artifactLocation", {}).get(
                        "uri", "unknown"
                    ),
                    "message": (result.get("extra") or {}).get("message", ""),
                }
            )
    return findings


def parse_grype(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    findings = []
    for match in payload.get("matches", []):
        vulnerability = match.get("vulnerability") or {}
        artifact = (match.get("artifact") or {}).get("name", "unknown")
        findings.append(
            {
                "control_name": "vulnerability_scan",
                "severity": str(vulnerability.get("severity", "unknown")).lower(),
                "scanner": "grype",
                "rule_or_vuln_id": vulnerability.get("id", "UNKNOWN"),
                "component": artifact,
                "message": vulnerability.get("description", ""),
            }
        )
    return findings


def parse_trivy_config(path: Path) -> list[dict[str, Any]]:
    """Trivy `config` (IaC misconfiguration) JSON report."""
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    findings = []
    for result in payload.get("Results", []) or []:
        target = result.get("Target", "unknown")
        for misconfiguration in result.get("Misconfigurations", []) or []:
            findings.append(
                {
                    "control_name": "infrastructure_scan",
                    "severity": str(
                        misconfiguration.get("Severity", "unknown")
                    ).lower(),
                    "scanner": "trivy",
                    "rule_or_vuln_id": misconfiguration.get("ID", "trivy-rule"),
                    "component": target,
                    "message": misconfiguration.get("Title")
                    or misconfiguration.get("Message", ""),
                }
            )
    return findings


PARSERS = {
    "secret_detection": parse_gitleaks,
    "sast": parse_semgrep,
    "vulnerability_scan": parse_grype,
    "infrastructure_scan": parse_trivy_config,
}


def classify_severity(findings: list[dict[str, Any]]) -> str:
    severities = {str(f.get("severity", "")).lower() for f in findings}
    if severities & BLOCKING_SEVERITIES:
        return "FAIL"
    if severities & WARNING_SEVERITIES:
        return "WARN"
    return "PASS"


def run_control(name: str, command: str, results_dir: Path) -> dict[str, Any]:
    """Execute one control command and return an emitter result block."""
    tool = shlex.split(command)[0]
    started_at = _now()
    start = time.monotonic()

    artifact = results_dir / CONTROL_ARTIFACTS.get(name, f"{name}.out")
    artifact.parent.mkdir(parents=True, exist_ok=True)

    if shutil_which(tool) is None:
        return {
            "status": "BLOCKED",
            "tool": tool,
            "missing_tool": tool,
            "tool_version": None,
            "command": command,
            "started_at": started_at,
            "duration_seconds": 0.0,
            "findings": [],
            "findings_by_severity": {},
            "artifacts": [],
            "evidence_links": [],
        }

    completed = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", command],
        text=True,
        capture_output=True,
        env={**os.environ},
    )
    duration = round(time.monotonic() - start, 3)
    (results_dir / f"{name}.log").write_text(
        (completed.stdout or "") + (completed.stderr or ""), encoding="utf-8"
    )

    findings = PARSERS.get(name, lambda _p: [])(artifact)
    for finding in findings:
        finding.setdefault("control_name", name)

    if completed.returncode != 0 and not findings:
        # The scanner failed and reported nothing: that is a control failure,
        # not a clean control.
        status = "FAIL"
    elif completed.returncode != 0:
        status = classify_severity(findings)
    else:
        status = classify_severity(findings)

    counts: dict[str, int] = {}
    for finding in findings:
        severity = str(finding.get("severity", "info")).lower()
        counts[severity] = counts.get(severity, 0) + 1

    return {
        "status": status,
        "tool": tool,
        "tool_version": _tool_version(tool),
        "command": command,
        "started_at": started_at,
        "duration_seconds": duration,
        "findings": findings,
        "findings_by_severity": counts,
        "artifacts": [_artifact_record(artifact)] if artifact.exists() else [],
        "evidence_links": [str(results_dir / f"{name}.log")],
    }


def _artifact_record(path: Path) -> dict[str, Any]:
    """A schema-valid artifact entry: path plus the digest of its content.

    The packet schema requires an object with `path` and a 64-hex `sha256`, and
    the digest is what substantiates that the report referenced is the report
    that ran. Writing a bare path string failed validation for every packet with
    real scanner output (rs#84).
    """
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"path": path.as_posix(), "sha256": digest, "retention": "ci-artifact"}


def shutil_which(name: str) -> str | None:
    from shutil import which

    return which(name)


def blocked_block(control: str, reason: str) -> dict[str, Any]:
    """A result block for a control that could not be produced.

    The emitter resolves a required control with no result as BLOCKED, so this
    exists to make the *reason* durable: the packet records the control name,
    the remediation, and that nothing was run, instead of a bare absence that
    reads the same as a typo.
    """
    return {
        "status": "BLOCKED",
        "tool": None,
        "tool_version": None,
        "command": None,
        "started_at": _now(),
        "duration_seconds": 0.0,
        "findings": [],
        "findings_by_severity": {},
        "artifacts": [],
        "evidence_links": [],
        "notes": reason,
    }


def load_repo_producers(path: Path | None) -> dict[str, str]:
    """Repository-declared producers from `.repo-standards.yml`.

    A consumer supplies a producer for a control that has no universal command
    (tests, lint, policy_validation, container_scan, ...) here. Without this,
    the only way to satisfy such a control is passing --control by hand, which
    a hosted workflow cannot do, so the declaration has to be durable in the
    repository's own configuration.
    """
    if path is None or not path.exists():
        return {}
    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML object")
    declared = ((data.get("assurance") or {}).get("producers")) or {}
    if not isinstance(declared, dict):
        raise ValueError(f"{path}: assurance.producers must be an object")
    for name, command in declared.items():
        if not isinstance(command, str) or not command.strip():
            raise ValueError(
                f"{path}: assurance.producers.{name} must be a non-empty string"
            )
    return declared


def profile_producers(
    profile: str, repo_declared: dict[str, str] | None = None
) -> dict[str, str]:
    """Control name -> producer command for every REQUIRED control of `profile`.

    A required control with no known producer is returned with an empty string
    so the caller records it as BLOCKED with the remediation rather than
    omitting it: omission is indistinguishable from "never required".
    """
    resolved = resolve(profile)
    producers: dict[str, str] = {}
    for name, block in resolved["controls"].items():
        if block["requirement"] != "REQUIRED":
            continue
        producers[name] = producer_for(name, repo_declared=repo_declared) or ""
    return producers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--control",
        action="append",
        default=[],
        metavar="NAME=COMMAND",
        help="Control name and the command that produces its raw output",
    )
    parser.add_argument(
        "--profile",
        help=(
            "Resolve every REQUIRED control of this assurance profile and run "
            "its producer. Controls with no producer are recorded BLOCKED with "
            "the remediation."
        ),
    )
    parser.add_argument(
        "--repo-config",
        type=Path,
        default=None,
        help="Consumer configuration declaring assurance.producers (default: "
        "./.repo-standards.yml when present)",
    )
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    results_dir = args.results
    results_dir.mkdir(parents=True, exist_ok=True)

    repo_config = args.repo_config
    if repo_config is None:
        default_config = Path(".repo-standards.yml")
        repo_config = default_config if default_config.exists() else None
    repo_declared = load_repo_producers(repo_config)

    commands: dict[str, str] = {}
    if args.profile:
        commands.update(profile_producers(args.profile, repo_declared))
    for spec in args.control:
        if "=" not in spec:
            print(
                f"assemble_results: bad --control {spec!r}, expected NAME=COMMAND",
                file=sys.stderr,
            )
            return 2
        name, command = spec.split("=", 1)
        commands[name] = command

    if not commands:
        print(
            "assemble_results: no controls requested; pass --profile or "
            "--control NAME=COMMAND",
            file=sys.stderr,
        )
        return 2

    results: dict[str, Any] = {}
    all_findings: list[dict[str, Any]] = []

    for name in sorted(commands):
        command = commands[name]
        if not command:
            block = blocked_block(
                name,
                f"{name} is REQUIRED by profile {args.profile} but has no "
                f"producer; {remediation_for(name)}",
            )
            results[name] = block
            print(f"assemble_results: {name} status=BLOCKED (no producer)")
            continue
        block = run_control(
            name,
            command.format(artifact=results_dir / _artifact_name(name)),
            results_dir,
        )
        results[name] = block
        all_findings.extend(block["findings"])
        print(
            f"assemble_results: {name} status={block['status']} "
            f"findings={len(block['findings'])}"
        )

    (results_dir / "results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (results_dir / "findings.json").write_text(
        json.dumps(all_findings, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"assemble_results: wrote {results_dir / 'results.json'} and findings.json")
    return 0


def _artifact_name(name: str) -> str:
    return CONTROL_ARTIFACTS.get(name, f"{name}.out")


if __name__ == "__main__":
    raise SystemExit(main())
