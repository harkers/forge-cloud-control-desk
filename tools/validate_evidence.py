#!/usr/bin/env python3
# Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away.
"""Validate Verification Evidence Packets against the canonical schema."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "schemas" / "verification-evidence.schema.json"

STATUS_PRECEDENCE = ["PASS", "NOT_APPLICABLE", "WARN", "BLOCKED", "FAIL"]
BLOCKING_SEVERITIES = {"critical", "high"}

#: Versions this validator understands. A packet claiming anything else must be
#: refused rather than read on a best-effort basis: the fields it relies on may
#: have changed meaning, and a silent misread is worse than a refusal
#: (completion-evidence.md: a consumer MUST refuse a packet whose schema_version
#: it does not understand).
KNOWN_SCHEMA_VERSIONS = {"1.0"}

#: Statuses that mean a tool actually produced a result. A control that ran must
#: name the tool that produced it — "a result that cannot name the tool that
#: produced it is invalid" (completion-evidence.md).
#:
#: BLOCKED is deliberately excluded: it means the tool was *unavailable*, so there
#: is no tool to name. Including it failed the blocked-tooling fixture, which is
#: correct — the fixture caught the rule being wrong, not the packet.
EXECUTED_STATUSES = {"PASS", "WARN", "FAIL"}


def load_schema(schema_path: Path | None = None) -> dict[str, Any]:
    return json.loads((schema_path or DEFAULT_SCHEMA).read_text(encoding="utf-8"))


def validate_packet(
    packet: dict[str, Any], schema_path: Path | None = None
) -> list[str]:
    validator = jsonschema.Draft202012Validator(load_schema(schema_path))
    structural = [
        f"{'/'.join(str(p) for p in error.path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(packet), key=lambda e: list(e.path))
    ]
    return structural + semantic_errors(packet)


def semantic_errors(packet: dict[str, Any]) -> list[str]:
    """Checks the JSON Schema cannot express.

    Schema validation covers structure and enums; these are the rules that depend
    on other fields' values, and each was previously enforced by nothing.
    """
    errors: list[str] = []

    version = packet.get("schema_version")
    if version not in KNOWN_SCHEMA_VERSIONS:
        errors.append(
            f"schema_version {version!r} is not understood "
            f"(known: {sorted(KNOWN_SCHEMA_VERSIONS)}) — refusing rather than guessing"
        )

    for control_id, block in (packet.get("controls") or {}).items():
        if not isinstance(block, dict):
            continue
        status = block.get("status")
        if status in EXECUTED_STATUSES:
            for field in ("tool", "tool_version"):
                if not block.get(field):
                    errors.append(
                        f"{control_id}: status {status} but no {field} — a result that "
                        "cannot name the tool that produced it is invalid"
                    )
        if status == "NOT_APPLICABLE" and not (block.get("notes") or "").strip():
            errors.append(
                f"{control_id}: NOT_APPLICABLE with no notes — a control silent about "
                "why it does not apply is indistinguishable from one never run"
            )
    return errors


def _exception_active(exception: dict[str, Any] | None, today: date) -> bool:
    if not exception:
        return False
    expires = exception.get("expires")
    if not expires:
        return True
    try:
        return date.fromisoformat(expires) >= today
    except ValueError:
        return False


def overall_status(packet: dict[str, Any], today: date | None = None) -> str:
    today = today or date.today()
    controls: dict[str, Any] = packet.get("controls", {})
    blocking_finding_untracked = False
    worst = "PASS"

    for control_id, block in controls.items():
        requirement = block.get("requirement", "REQUIRED")
        status = block.get("status", "FAIL")
        exception_active = _exception_active(block.get("exception"), today)

        if status == "BLOCKED" and requirement != "NOT_APPLICABLE":
            return "BLOCKED_TOOLING"

        for finding in block.get("findings", []) or []:
            if finding.get("severity") in BLOCKING_SEVERITIES and not finding.get(
                "issue"
            ):
                blocking_finding_untracked = True

        if requirement == "NOT_APPLICABLE":
            continue
        if exception_active and status == "FAIL":
            continue
        if requirement == "OPTIONAL" and status in {"FAIL", "BLOCKED"}:
            status = "WARN"
        if STATUS_PRECEDENCE.index(status) > STATUS_PRECEDENCE.index(worst):
            worst = status

    if worst == "FAIL":
        return "BLOCKED_FINDING_TRACKING" if blocking_finding_untracked else "FAIL"
    if blocking_finding_untracked:
        return "BLOCKED_FINDING_TRACKING"
    if worst in {"WARN", "NOT_APPLICABLE"}:
        return "PASS"
    return worst


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packets", nargs="+", type=Path)
    parser.add_argument("--schema", type=Path, default=None)
    parser.add_argument(
        "--expect",
        choices=["PASS", "FAIL", "BLOCKED_TOOLING", "BLOCKED_FINDING_TRACKING"],
        help="Require this overall state instead of PASS",
    )
    parser.add_argument(
        "--expect-commit",
        default=None,
        help=(
            "Require the packet to name this commit. A packet is valid only for the "
            "commit it names; evidence from one commit says nothing about another"
        ),
    )
    args = parser.parse_args(argv)

    failures = 0
    for path in args.packets:
        packet = json.loads(path.read_text(encoding="utf-8"))
        errors = validate_packet(packet, args.schema)
        if args.expect_commit and packet.get("commit") != args.expect_commit:
            errors.append(
                f"commit {packet.get('commit')!r} does not match expected "
                f"{args.expect_commit!r} — evidence is valid only for the commit it names"
            )
        for error in errors:
            print(f"INVALID {path}: {error}", file=sys.stderr)
        state = overall_status(packet)
        expected = args.expect or "PASS"
        ok = not errors and state == expected
        if not ok:
            failures += 1
            print(
                f"FAIL {path}: state={state} expected={expected} errors={len(errors)}",
                file=sys.stderr,
            )
        else:
            print(f"OK {path}: state={state}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
