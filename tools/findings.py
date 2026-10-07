#!/usr/bin/env python3
# Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away.
"""Deterministic finding fingerprinting and escalation routing."""

from __future__ import annotations

import hashlib
import re
from typing import Any

FINGERPRINT_PATTERN = re.compile(r"finding-fingerprint:\s*(rsf1:[0-9a-f]{32})")
FINGERPRINT_PREFIX = "rsf1:"

ISSUE_TYPES = {
    "security_finding": "Security Finding",
    "bug_incident": "Bug / Incident",
    "implementation_task": "Implementation Task",
    "investigation": "Investigation",
}


def fingerprint(
    repository: str,
    control: str,
    scanner: str,
    rule_or_vuln_id: str,
    component: str,
) -> str:
    material = "|".join([repository, control, scanner, rule_or_vuln_id, component])
    return (
        FINGERPRINT_PREFIX + hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]
    )


def dedupe_key(finding: dict[str, Any]) -> str:
    recorded = finding.get("fingerprint")
    if isinstance(recorded, str) and recorded.startswith(FINGERPRINT_PREFIX):
        return recorded
    return fingerprint(
        str(finding.get("repository", "")),
        str(finding.get("control", "")),
        str(finding.get("scanner", "")),
        str(finding.get("id", "")),
        str(finding.get("component", "")),
    )


def classify(finding: dict[str, Any], policy: dict[str, Any]) -> str:
    create_issue = policy.get("create_issue", {}) or {}
    investigation = policy.get("investigation", []) or []
    if finding.get("kind") in investigation:
        return "investigation"
    # The `blocking_tool_failure` threshold is about *blocking* tool failures, so
    # the finding's own `blocking` flag is part of the condition. An absent flag
    # means the producer did not demote the failure and is treated as blocking,
    # matching the fail-closed convention used elsewhere in the assurance tooling
    # (an absent `requirement` defaults to REQUIRED, an absent `status` to FAIL).
    # Only an explicit False demotes a tool failure, which then falls through to
    # the severity check rather than being dropped outright.
    if (
        finding.get("kind") == "tool_failure"
        and finding.get("blocking", True) is not False
        and "blocking_tool_failure" in create_issue.get("bug_incident", [])
    ):
        return "bug_incident"
    if finding.get("kind") == "remediation_task":
        return "implementation_task"
    if str(finding.get("severity", "")).lower() in [
        str(s).lower() for s in create_issue.get("security", [])
    ]:
        return "security_finding"
    return "none"


def parse_existing_issues(issues: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for issue in issues:
        match = FINGERPRINT_PATTERN.search(str(issue.get("body", "")))
        if match:
            mapping[match.group(1)] = issue
    return mapping


def reconcile(
    findings: list[dict[str, Any]],
    existing: list[dict[str, Any]],
    policy: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {
        "create": [],
        "update": [],
        "reopen": [],
        "ignore": [],
    }
    known = parse_existing_issues(existing)
    deduplicate = policy.get("deduplicate", True)
    reopen = policy.get("reopen_regressions", True)

    for finding in findings:
        route = classify(finding, policy)
        if route == "none":
            result["ignore"].append({**finding, "action": "ignore"})
            continue
        key = dedupe_key(finding)
        issue = known.get(key) if deduplicate else None
        if issue is None:
            result["create"].append(
                {
                    **finding,
                    "action": "create",
                    "issue_type": ISSUE_TYPES[route],
                    "fingerprint": key,
                }
            )
            continue
        action = "reopen" if (issue.get("state") != "open" and reopen) else "update"
        result[action].append(
            {
                **finding,
                "action": action,
                "issue": issue.get("number"),
                "issue_type": ISSUE_TYPES[route],
                "fingerprint": key,
            }
        )
    return result
