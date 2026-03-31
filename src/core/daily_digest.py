#!/usr/bin/env python3
"""
Forge Compute Control Desk — Daily Digest Workflow

Scans the local evidence store for action records from the current UTC date,
produces a summary of all VM actions, and writes a digest report.

Follows the local-first evidence model: output goes to
data/evidence/reports/daily_digest_YYYY-MM-DD.md.
"""

import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pathlib import Path

def _resolve_root() -> Path:
    """Return the GCCD project root."""
    # data/evidence lives at <project-root>/data/evidence
    # this file is at <project-root>/src/core/daily_digest.py
    return Path(__file__).resolve().parent.parent.parent


EVIDENCE_ROOT = _resolve_root() / "data" / "evidence"
REPORTS_DIR   = EVIDENCE_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _parse_action_filename(filename: str) -> Optional[dict]:
    """Parse instance name, date, and action from an evidence filename.

    Filenames look like:
      forge-test-vm_2026-03-30_start.md
      forge-rt-224659_2026-03-31_delete.md
    """
    stem = Path(filename).stem
    m = re.match(r"^(.+?)_(\d{4}-\d{2}-\d{2})_(start|stop|restart|create|delete|inspect)$", stem)
    if not m:
        return None
    return {"instance": m.group(1), "date": m.group(2), "action": m.group(3)}


def _read_action_record(path: Path) -> Optional[dict]:
    """Parse a single action evidence file and return structured fields."""
    try:
        text = path.read_text()
    except Exception:
        return None

    def extract(label: str) -> str:
        m = re.search(rf"\*\*{re.escape(label)}:\*\*\s*(.+)", text)
        return m.group(1).strip() if m else ""

    def extract_link(label: str) -> str:
        m = re.search(rf"\[{re.escape(label)}\]\((.+?)\)", text)
        return m.group(1).strip() if m else ""

    return {
        "instance": extract("Instance"),
        "action": extract("Action"),
        "timestamp": extract("Timestamp"),
        "status": extract("Status"),
        "operation": extract("Operation"),
        "result": extract("Result"),
        "sheets_link": extract_link("Sheets Register"),
        "gcp_link": extract_link("GCP Console"),
    }


def generate_daily_digest(date: Optional[str] = None) -> dict:
    """Scan evidence store for today's actions and produce a digest report.

    Args:
        date: ISO date string (YYYY-MM-DD) to digest. Defaults to today UTC.

    Returns:
        dict with keys: success (bool), date, total_actions, instances, report_path
    """
    if date is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Collect all action records for the target date
    actions: List[dict] = []
    for f in EVIDENCE_ROOT.glob(f"*_{date}_*.md"):
        parsed = _parse_action_filename(f.name)
        if not parsed:
            continue
        record = _read_action_record(f)
        if not record:
            continue
        record["filename"] = f.name
        actions.append(record)

    # Sort by timestamp ascending
    actions.sort(key=lambda a: a.get("timestamp", ""))

    # Build per-instance summary
    by_instance: Dict[str, dict] = {}
    for a in actions:
        inst = a.get("instance", "unknown")
        if inst not in by_instance:
            by_instance[inst] = {"instance": inst, "actions": [], "last_action": None, "last_status": None}
        by_instance[inst]["actions"].append(a)
        by_instance[inst]["last_action"] = a.get("action", "?")
        by_instance[inst]["last_status"] = a.get("status", "?")

    # Render markdown
    lines = [
        f"# Daily Governance Digest — {date}",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"**Evidence root:** {EVIDENCE_ROOT}",
        "",
        "## Summary",
        "",
        f"| Instance | Actions | Last Action | Last Status |",
        f"|----------|---------|-------------|--------------|",
    ]

    for inst in sorted(by_instance.keys()):
        info = by_instance[inst]
        action_count = len(info["actions"])
        # Collapse repeated same-action into count
        unique_actions = list(dict.fromkeys(a.get("action","?") for a in info["actions"]))
        action_str = ", ".join(unique_actions) if action_count <= 3 else ", ".join(unique_actions[:2]) + f" (+{action_count - 2} more)"
        lines.append(f"| {inst} | {action_count} | {info['last_action']} | {info['last_status']} |")

    lines += ["", "## Action Details", ""]

    if actions:
        for a in actions:
            inst = a.get("instance", "?")
            act = a.get("action", "?")
            ts  = a.get("timestamp", "?")
            st  = a.get("status", "?")
            op  = a.get("operation", "?")
            res = a.get("result", "?")
            lines += [
                f"### {inst} — {act} ({ts})",
                "",
                f"**Status:** {st}",
                f"**Operation:** {op}",
                f"**Result:** {res}",
                "",
            ]
    else:
        lines.append("*No VM actions recorded on this date.*")
        lines.append("")

    lines += [
        "---",
        f"*Digest generated by Forge Compute Control Desk — {datetime.now(timezone.utc).isoformat()}*",
    ]

    report_content = "\n".join(lines)

    report_path = REPORTS_DIR / f"daily_digest_{date}.md"
    report_path.write_text(report_content)

    return {
        "success": True,
        "date": date,
        "total_actions": len(actions),
        "instances": list(sorted(by_instance.keys())),
        "report_path": str(report_path),
        "report_content": report_content,
    }


if __name__ == "__main__":
    result = generate_daily_digest()
    print(f"Digest: {result['total_actions']} actions for {result['date']}")
    print(f"Report: {result['report_path']}")
    if result["instances"]:
        print("Instances:", ", ".join(result["instances"]))
    else:
        print("No actions found.")
