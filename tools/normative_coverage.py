#!/usr/bin/env python3
# Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away.
"""Bound the backlog of normative statements that nothing enforces.

Every incident in this repository's recent history had one shape: a rule existed
and nothing checked it. Worktree isolation (#57), the CI gate (#51), SAST (#76),
profile controls (#77), worktree cleanup (#49) — each was a MUST with no
enforcement, discovered by failing rather than by audit.

The count was unbounded because nothing measured it. This tool measures it.

Design: **baseline the debt, prevent growth.** Classifying every normative
statement by hand produces a document nobody maintains, so instead:

* each normative block is fingerprinted;
* `coverage/enforced.yml` names the rules that *are* enforced, and by what;
* `coverage/wireable.yml` is the backlog: mechanically checkable, not yet wired;
* `coverage/judgement.yml` is rules that constrain conduct or reasoning and cannot
  be mechanically enforced, recorded so they stop counting as failure;
* `coverage/delegated.yml` is rules that bind a component outside this repository
  (the control plane, WorkHub, Agent Fabric). They are not wireable *here* — no
  check in this repository can verify them — and recording that stops them sitting
  in the backlog implying work that should not be done;
* a statement in none of the three fails `--check`.

A flat "unenforced" bucket is not a backlog, it is an unclassified pile: it cannot
be prioritised, and it counts "be honest" alongside "verify the commit hash". The
three classes make the remainder legible — `wireable` is the work, `judgement` is
by design. Adding a MUST now forces the decision at authoring time, which is the
point.

Fingerprints are taken over the *normalised block* (paragraph or bullet with
newlines collapsed), so reflowing a paragraph does not invalidate coverage while
editing its substance does — which is the point: changing a rule should force
someone to re-affirm how it is enforced.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

import yaml

NORMATIVE = re.compile(r"\bMUST(?: NOT)?\b")
SOURCES = ("AGENTS.md", "standards", "process")
# Generated artefacts: the runtime contract DUPLICATES policy rule text by
# design (it is what consumers compose). Scanning it would double-count every
# defect-priority rule and permanently show 9 unclassified statements. Its
# freshness is checked against the policy by tools/gen_runtime_contract.py
# --check (wired into validate.yml), which is the correct guard for generated
# content -- classification of a generated copy is meaningless.
EXCLUDE = ("standards/runtime-contract.md",)
COVERAGE_DIR = Path("coverage")
ENFORCED_FILE = COVERAGE_DIR / "enforced.yml"
WIREABLE_FILE = COVERAGE_DIR / "wireable.yml"
JUDGEMENT_FILE = COVERAGE_DIR / "judgement.yml"
DELEGATED_FILE = COVERAGE_DIR / "delegated.yml"


def normalise(text: str) -> str:
    """Collapse a block to one canonical line.

    Markdown emphasis and backticks are stripped and whitespace collapsed, so a
    fingerprint tracks the rule's substance rather than its formatting.
    """
    text = text.replace("`", "").replace("*", "").replace("_", "")
    return re.sub(r"\s+", " ", text).strip().lower()


def fingerprint(text: str) -> str:
    return hashlib.sha256(normalise(text).encode("utf-8")).hexdigest()[:12]


def blocks(text: str) -> list[str]:
    """Split markdown into paragraph/bullet blocks.

    A block ends at a blank line or at the start of the next bullet, so a wrapped
    bullet stays one unit and reflow does not change its fingerprint.
    """
    out: list[str] = []
    current: list[str] = []

    def flush() -> None:
        if current:
            out.append("\n".join(current).strip())
            current.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if stripped.startswith(("#", "|", "```", "---", ">")):
            flush()
            continue
        if re.match(r"^([-*+]|\d+\.)\s", stripped) and current:
            flush()
        current.append(stripped)
    flush()
    return [b for b in out if b]


def normative_blocks(root: Path) -> dict[str, str]:
    """fingerprint -> "path: preview" for every block containing a MUST."""
    found: dict[str, str] = {}
    paths: list[Path] = []
    for entry in SOURCES:
        target = root / entry
        if target.is_dir():
            paths.extend(sorted(target.rglob("*.md")))
        elif target.is_file():
            paths.append(target)
    for path in paths:
        if path.relative_to(root).as_posix() in EXCLUDE:
            continue
        for block in blocks(path.read_text(encoding="utf-8")):
            if NORMATIVE.search(block):
                rel = path.relative_to(root).as_posix()
                preview = normalise(block)[:88]
                found.setdefault(fingerprint(block), f"{rel}: {preview}")
    return found


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def report(root: Path) -> tuple[dict[str, str], dict[str, set[str]]]:
    """Return (statements, {class: fingerprints})."""
    statements = normative_blocks(root)
    classes = {
        "enforced": set((_load(root / ENFORCED_FILE).get("enforced") or {})),
        "wireable": set((_load(root / WIREABLE_FILE).get("wireable") or {})),
        "judgement": set((_load(root / JUDGEMENT_FILE).get("judgement") or {})),
        "delegated": set((_load(root / DELEGATED_FILE).get("delegated") or {})),
    }
    return statements, classes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--backlog", action="store_true", help="list the wireable rules")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    statements, classes = report(root)
    known = set().union(*classes.values())
    uncovered = sorted(set(statements) - known)
    # "Exactly one class" is the contract: a rule in both `enforced` and
    # `wireable` would count twice and hide the fact that nobody decided.
    overlaps = [
        f"{a}/{b}"
        for a, b in (
            ("enforced", "wireable"), ("enforced", "judgement"), ("enforced", "delegated"),
            ("wireable", "judgement"), ("wireable", "delegated"), ("judgement", "delegated"),
        )
        if classes[a] & classes[b]
    ]
    stale = {name: sorted(fps - set(statements)) for name, fps in classes.items()}

    total = len(statements)
    print(f"normative statements: {total}")
    for name in ("enforced", "wireable", "judgement", "delegated"):
        print(f"  {name + ':':<12}{len(classes[name] & set(statements))}")
    print(f"  unclassified: {len(uncovered)}")

    ok = True
    if uncovered:
        ok = False
        print("\nUnclassified normative statements (put each in exactly one class):")
        for fp in uncovered:
            print(f"  {fp}  {statements[fp]}")
    if overlaps:
        ok = False
        print(f"\nstatements present in more than one class: {overlaps}")
    for name, fps in stale.items():
        if fps:
            ok = False
            print(f"\n{name}.yml entries matching no statement (remove them):")
            for fp in fps:
                print(f"  {fp}")

    if args.backlog:
        print(f"\nwireable backlog ({len(classes['wireable'])}):")
        for fp in sorted(classes["wireable"]):
            print(f"  {fp}  {statements.get(fp, '(stale)')}")

    if args.check and not ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
