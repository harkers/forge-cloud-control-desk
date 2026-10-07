#!/usr/bin/env python3
# Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away.
"""Resolve which assurance controls a repository profile requires."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROFILES_DIR = ROOT / "profiles"

CONTROL_IDS = {
    "tests": "RS-BUILD-001",
    "lint": "RS-BUILD-001",
    "markdown_lint": "RS-BUILD-001",
    "link_check": "RS-BUILD-001",
    "secret_detection": "RS-SEC-001",
    "sbom": "RS-SEC-002",
    "vulnerability_scan": "RS-SEC-003",
    "sast": "RS-SEC-004",
    "container_scan": "RS-SEC-005",
    "infrastructure_scan": "RS-SEC-005",
    "policy_validation": "RS-SEC-005",
}

BASELINE_PROFILES: dict[str, dict[str, list[str]]] = {
    "library": {
        "requires": [
            "tests",
            "lint",
            "secret_detection",
            "sast",
            "sbom",
            "vulnerability_scan",
        ]
    },
    "service": {
        "requires": [
            "tests",
            "lint",
            "secret_detection",
            "sast",
            "sbom",
            "vulnerability_scan",
            "container_scan",
        ]
    },
    "infrastructure": {
        "requires": [
            "secret_detection",
            "infrastructure_scan",
            "policy_validation",
        ]
    },
    "documentation": {
        "requires": [
            "markdown_lint",
            "link_check",
            "secret_detection",
        ]
    },
}

DEFAULT_FINDING_ESCALATION = {
    "create_issue": {
        "security": ["critical", "high"],
        "bug_incident": ["blocking_tool_failure"],
    },
    "deduplicate": True,
    "reopen_regressions": True,
}


def _profile_assurance(profile: str) -> dict[str, Any]:
    path = PROFILES_DIR / f"{profile}.yml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("assurance", {}) or {}


def finding_escalation(
    baseline: str, repo_config: dict[str, Any] | None = None
) -> dict[str, Any]:
    policy = dict(DEFAULT_FINDING_ESCALATION)
    for source in (
        _profile_assurance(baseline),
        (repo_config or {}).get("assurance", {}) or {},
    ):
        escalation = source.get("finding_escalation")
        if escalation:
            merged = dict(policy)
            for key, value in escalation.items():
                if isinstance(value, dict) and isinstance(policy.get(key), dict):
                    merged[key] = {**policy[key], **value}
                else:
                    merged[key] = value
            policy = merged
    return policy


def resolve(baseline: str, repo_config: dict[str, Any] | None = None) -> dict[str, Any]:
    if baseline not in BASELINE_PROFILES:
        raise ValueError(f"Unknown baseline profile: {baseline}")

    required = list(BASELINE_PROFILES[baseline]["requires"])
    controls: dict[str, dict[str, Any]] = {}
    for name, control_id in CONTROL_IDS.items():
        if name in required:
            controls[name] = {
                "control_id": control_id,
                "requirement": "REQUIRED",
                "reason": None,
                "override_by": None,
                "tool": None,
            }
        else:
            controls[name] = {
                "control_id": control_id,
                "requirement": "NOT_APPLICABLE",
                "reason": f"{name} is not part of the {baseline} baseline profile",
                "override_by": None,
                "tool": None,
            }

    overrides = ((repo_config or {}).get("assurance", {}) or {}).get(
        "controls", {}
    ) or {}
    for name, override in overrides.items():
        if name not in controls:
            raise ValueError(f"Override references unknown assurance control: {name}")
        if controls[name]["requirement"] == "NOT_APPLICABLE":
            raise ValueError(
                f"Override cannot add a control outside the {baseline} baseline: {name}"
            )
        requirement = override.get("requirement")
        if requirement not in {"REQUIRED", "OPTIONAL", "NOT_APPLICABLE"}:
            raise ValueError(f"Invalid requirement for {name}: {requirement}")
        if not override.get("reason") or not override.get("override_by"):
            raise ValueError(f"Override for {name} requires reason and override_by")
        controls[name]["requirement"] = requirement
        controls[name]["reason"] = override["reason"]
        controls[name]["override_by"] = override["override_by"]

    return {
        "baseline": baseline,
        "controls": controls,
        "finding_escalation": finding_escalation(baseline, repo_config),
    }
