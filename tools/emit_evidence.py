#!/usr/bin/env python3
# Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away.
"""Assemble a Verification Evidence Packet from resolved control results.

Keying contract (harkers/repo-standards#23): ``controls`` is keyed by canonical
control ID, not by the profile's producer name. Several producer names can map
to one control ID (``tests``/``lint``/``markdown_lint``/``link_check`` all feed
``RS-BUILD-001``), so the block aggregates its members: the requirement is
REQUIRED if any member is REQUIRED, and the status is the worst member status.

Every control ID in the taxonomy appears in every packet. A control with no
producer name in the current profile (``RS-BUILD-002``, ``RS-SEC-006`` today)
is emitted as ``NOT_APPLICABLE`` with an explicit reason rather than omitted:
omission is indistinguishable from "never required", which is the ambiguity
the completion evidence standard exists to remove.

A required control whose producer reported no result is ``BLOCKED`` with
``missing_control``/``missing_tool`` set. It is never omitted and never PASS.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tools.assurance import resolve
from tools.producers import remediation_for
from tools.validate_evidence import overall_status

CONTROL_ORDER = [
    "RS-BUILD-001",
    "RS-BUILD-002",
    "RS-SEC-001",
    "RS-SEC-002",
    "RS-SEC-003",
    "RS-SEC-004",
    "RS-SEC-005",
    "RS-SEC-006",
]

STATUS_PRECEDENCE = ["PASS", "NOT_APPLICABLE", "WARN", "BLOCKED", "FAIL"]

DEFAULT_TOOLS = {
    "secret_detection": "gitleaks",
    "sbom": "syft",
    "vulnerability_scan": "grype",
    "sast": "semgrep",
    "infrastructure_scan": "trivy",
}

NO_PRODUCER_REASON = "no producer mapped for this control in the current profile"

#: RS-BUILD-002 is satisfied by the gate's own validate step, so it can have no
#: producer by construction. Saying so explicitly is better than a generic
#: "no producer mapped" that reads like a missing tool (rs#77).
GATE_ONLY_REASON = (
    "completion evidence is validated by the gate's validate-evidence step; "
    "this control has no separate producer by design"
)


def _base_entry(control_id: str, requirement: str, status: str) -> dict[str, Any]:
    return {
        "control_id": control_id,
        "requirement": requirement,
        "tool": None,
        "tool_version": None,
        "command": None,
        "started_at": None,
        "duration_seconds": None,
        "status": status,
        "findings_by_severity": {},
        "findings": [],
        "artifacts": [],
        "evidence_links": [],
    }


def _worst(
    member_results: list[tuple[str, dict[str, Any]]],
) -> tuple[str, dict[str, Any]]:
    return max(
        member_results,
        key=lambda pair: STATUS_PRECEDENCE.index(pair[1].get("status", "FAIL")),
    )


def _merge_from_results(
    entry: dict[str, Any],
    member_results: list[tuple[str, dict[str, Any]]],
    preferred: dict[str, Any],
) -> None:
    for key in (
        "tool",
        "tool_version",
        "command",
        "started_at",
        "duration_seconds",
    ):
        if preferred.get(key) is not None:
            entry[key] = preferred[key]
    for name, result in member_results:
        for key in (
            "tool",
            "tool_version",
            "command",
            "started_at",
            "duration_seconds",
        ):
            if entry.get(key) is None and result.get(key) is not None:
                entry[key] = result[key]
        for key in ("artifacts", "evidence_links"):
            entry[key].extend(result.get(key) or [])
        # A member that recorded itself BLOCKED carries the reason. Dropping it
        # left the packet stating a control failed with no explanation (rs#77).
        if result.get("status") == "BLOCKED":
            entry.setdefault("missing_control", name)
            if entry.get("missing_tool") is None:
                entry["missing_tool"] = result.get("missing_tool") or DEFAULT_TOOLS.get(
                    name, name
                )
            if entry.get("notes") is None and result.get("notes") is not None:
                entry["notes"] = result["notes"]
        if entry.get("exception") is None and result.get("exception") is not None:
            entry["exception"] = result["exception"]
        for key, value in (result.get("findings_by_severity") or {}).items():
            entry["findings_by_severity"][key] = (
                entry["findings_by_severity"].get(key, 0) + value
            )


def build_packet(
    profile: str,
    repository: str,
    commit: str,
    baseline: str,
    results: dict[str, dict[str, Any]],
    findings: list[dict[str, Any]],
    generated_at: str,
    build: str | None = None,
) -> dict[str, Any]:
    resolved = resolve(baseline)
    members_by_id: dict[str, list[str]] = {
        control_id: [] for control_id in CONTROL_ORDER
    }
    for name, block in resolved["controls"].items():
        control_id = block["control_id"]
        if control_id in members_by_id:
            members_by_id[control_id].append(name)

    controls: dict[str, Any] = {}
    for control_id in CONTROL_ORDER:
        members = members_by_id[control_id]
        required_members = [
            name
            for name in members
            if resolved["controls"][name]["requirement"] == "REQUIRED"
        ]

        if not required_members:
            if control_id == "RS-BUILD-002":
                reason = GATE_ONLY_REASON
            elif members:
                reason = resolved["controls"][members[0]]["reason"]
            else:
                reason = NO_PRODUCER_REASON
            entry = _base_entry(control_id, "NOT_APPLICABLE", "NOT_APPLICABLE")
            entry["notes"] = reason
            controls[control_id] = entry
            continue

        missing = next((name for name in required_members if name not in results), None)
        if missing is not None:
            entry = _base_entry(control_id, "REQUIRED", "BLOCKED")
            entry.update(
                {
                    "missing_control": missing,
                    "missing_tool": DEFAULT_TOOLS.get(missing, missing),
                    "notes": (
                        f"{missing} did not report a result; treated as BLOCKED. "
                        f"{remediation_for(missing)}"
                    ),
                }
            )
            controls[control_id] = entry
            continue

        member_results = [(name, results[name]) for name in required_members]
        _, worst_result = _worst(member_results)
        entry = _base_entry(control_id, "REQUIRED", worst_result.get("status", "FAIL"))
        entry["findings"] = [
            {key: value for key, value in finding.items() if key != "control_name"}
            for finding in findings
            if finding.get("control_name") in (None, control_id, *members)
        ]
        counts: dict[str, int] = {}
        for finding in entry["findings"]:
            severity = str(finding.get("severity", "info")).lower()
            counts[severity] = counts.get(severity, 0) + 1
        entry["findings_by_severity"] = counts
        _merge_from_results(entry, member_results, worst_result)
        controls[control_id] = entry

    packet: dict[str, Any] = {
        "schema_version": "1.0",
        "repository": repository,
        "commit": commit,
        "generated_at": generated_at,
        "profile": profile,
        "build": build,
        "controls": controls,
        "tracked_findings": [
            {key: value for key, value in finding.items() if key != "control_name"}
            for finding in findings
        ],
    }
    packet["state"] = overall_status(packet)
    return packet


def load_results(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    target = path / "results.json" if path.is_dir() else path
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def load_findings(path: Path | None) -> list[dict[str, Any]]:
    """Normalized findings, or an empty list when the file is absent.

    An absent findings file means "this run produced none", not "the run is
    broken": `load_results` has always tolerated a missing file, and a hard
    failure here turned a clean run into a traceback. A genuinely broken run is
    still caught, because `results.json` is what resolves control status and a
    missing one leaves every required control BLOCKED.
    """
    if path is None or not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--results", type=Path, default=None)
    parser.add_argument("--findings", type=Path, default=None)
    parser.add_argument("--generated-at", default=None)
    parser.add_argument("--build", default=None)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    packet = build_packet(
        profile=args.profile,
        repository=args.repository,
        commit=args.commit,
        baseline=args.baseline,
        results=load_results(args.results),
        findings=load_findings(args.findings),
        generated_at=args.generated_at or "1970-01-01T00:00:00Z",
        build=args.build,
    )
    args.out.write_text(
        json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"{args.out}: state={packet['state']}")
    return 0 if packet["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
