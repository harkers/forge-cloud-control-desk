#!/usr/bin/env python3
# Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away.
"""Validate and repair the append-only remote-action ledger.

Why this exists
---------------
`.project/remote-actions.jsonl` records every GitHub mutation an agent performed:
the evidence that a claimed remote action actually happened. It is append-only and
committed, so two branches appending concurrently used to *conflict* — and the
conflict was resolved by taking one side. Observed: `origin/main` held 6 entries, a
local branch held 11, with **zero overlap**. A blind reset would have destroyed the
creation records for issues #31-#34.

`.gitattributes` now routes the file through git's built-in `union` driver, so
disjoint appends merge cleanly and both sides survive with no configuration on any
clone. That removes the loss, and introduces one failure mode of its own: `union`
concatenates, so an entry appended identically on both sides appears twice.

This tool covers both halves:

* `--check` fails on a malformed line, a missing key, or a duplicate `intent_id`;
* `--dedupe` rewrites the ledger deduplicated by `intent_id` and ordered by
  `created_at`, which is the repair.

It is deliberately strict about keys: a ledger entry that cannot be keyed or dated
cannot be deduplicated later, and the loss is silent.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LEDGER = Path(".project/remote-actions.jsonl")
REQUIRED_KEYS = ("intent_id", "action", "status", "created_at", "repository")


def parse(text: str) -> tuple[list[dict], list[str]]:
    """Return (records, problems). A malformed line is a problem, not a crash."""
    records: list[dict] = []
    problems: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            problems.append(f"line {number}: blank line")
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            problems.append(f"line {number}: invalid JSON ({exc.msg})")
            continue
        if not isinstance(record, dict):
            problems.append(f"line {number}: not a JSON object")
            continue
        missing = [k for k in REQUIRED_KEYS if not record.get(k)]
        if missing:
            problems.append(f"line {number}: missing {', '.join(missing)}")
        records.append(record)
    return records, problems


def duplicates(records: list[dict]) -> list[str]:
    seen: set[str] = set()
    dupes: list[str] = []
    for record in records:
        key = record.get("intent_id")
        if not key:
            continue
        if key in seen and key not in dupes:
            dupes.append(key)
        seen.add(key)
    return dupes


def merged(records: list[dict]) -> list[dict]:
    """Deduplicate by intent_id, keeping the first, ordered by created_at.

    Ordering makes the file's diff stable: without it, a union merge interleaves
    two branches' appends in merge order, so the same content produces different
    files and every later merge conflicts on ordering alone.
    """
    by_key: dict[str, dict] = {}
    for record in records:
        key = record.get("intent_id")
        if key and key not in by_key:
            by_key[key] = record
    return sorted(
        by_key.values(), key=lambda r: (str(r.get("created_at", "")), r["intent_id"])
    )


def _write(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in records),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--ledger", default=None, help=f"default: {LEDGER}")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--dedupe", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    path = Path(args.ledger) if args.ledger else root / LEDGER
    if not path.is_file():
        print(f"ledger not found: {path}", file=sys.stderr)
        return 2

    records, problems = parse(path.read_text(encoding="utf-8"))
    dupes = duplicates(records)

    print(
        f"entries: {len(records)}  unique: {len({r.get('intent_id') for r in records})}"
    )

    if args.dedupe:
        _write(path, merged(records))
        print(
            f"deduplicated: {len(problems)} problem(s) dropped, {len(dupes)} duplicate(s) removed"
        )
        return 0

    ok = True
    if problems:
        ok = False
        print("\nmalformed entries:")
        for problem in problems:
            print(f"  {problem}")
    if dupes:
        ok = False
        print("\nduplicate intent_id (union merge appends both sides):")
        for key in dupes[:10]:
            print(f"  {key}")
        print("  repair with --dedupe")

    if args.check and not ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
