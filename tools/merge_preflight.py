#!/usr/bin/env python3
# Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away.
"""Check a branch before starting work on it, and again before merging it.

Worktree isolation is per-task. It stops two agents sharing a *checkout*; it does
nothing about two agents editing the same *files*. Three collisions happened in
one session:

1. A branch implementing a feature was merged while another agent's open PR
   implemented the same feature. The port took a snapshot of in-flight work and
   the other PR conflicted.
2. That merge turned `main` red because the adopted test assumed a scanner the
   other agent's environment lacked; a follow-up PR fixed it minutes later.
3. A branch was re-prepared for work that had already landed under a different
   PR number, because its tree had no way to know.

The first failure was avoidable at merge time: open PRs were checked twenty
minutes before the merge, and not again. So this tool answers three questions,
and any "yes" is a stop:

* **Already landed?** — the branch has no patches absent from the base, so
  merging it changes nothing and re-doing its work is waste.
* **Local overlap?** — another unmerged local branch touches the same files.
* **Remote overlap?** — an open PR touches the same files. Needs `gh`; reported
  as unchecked when unavailable rather than assumed clean.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _git(root: Path, *args: str) -> tuple[int, str]:
    proc = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False
    )
    return proc.returncode, proc.stdout


def changed_files(root: Path, base: str, branch: str) -> set[str]:
    """Files the branch changes relative to the merge base with `base`."""
    code, out = _git(root, "diff", "--name-only", f"{base}...{branch}")
    if code != 0:
        return set()
    return {line.strip() for line in out.splitlines() if line.strip()}


def already_landed(root: Path, base: str, branch: str) -> bool:
    """True when no patch on the branch is absent from the base."""
    code, out = _git(root, "cherry", base, branch)
    if code != 0:
        return False
    return not any(line.startswith("+") for line in out.splitlines())


def local_branches(root: Path) -> list[str]:
    code, out = _git(root, "for-each-ref", "--format=%(refname:short)", "refs/heads")
    return [b.strip() for b in out.splitlines() if b.strip()] if code == 0 else []


def local_overlaps(
    root: Path, base: str, branch: str, files: set[str]
) -> list[tuple[str, list[str]]]:
    """Other unmerged local branches touching any of `files`."""
    overlaps: list[tuple[str, list[str]]] = []
    for other in local_branches(root):
        if other in (branch, base):
            continue
        if already_landed(root, base, other):
            continue
        shared = sorted(files & changed_files(root, base, other))
        if shared:
            overlaps.append((other, shared))
    return overlaps


def remote_overlaps(
    root: Path, branch: str, files: set[str]
) -> tuple[list[tuple[int, str, list[str]]], str]:
    """Open PRs touching any of `files`. Returns (overlaps, note)."""
    proc = subprocess.run(
        ["gh", "pr", "list", "--state", "open", "--json", "number,headRefName,files"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return [], "gh unavailable — open PRs NOT checked"
    try:
        prs = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return [], "gh output unparseable — open PRs NOT checked"

    overlaps: list[tuple[int, str, list[str]]] = []
    for pr in prs:
        if pr.get("headRefName") == branch:
            continue
        touched = {f.get("path") for f in (pr.get("files") or []) if f.get("path")}
        shared = sorted(files & touched)
        if shared:
            overlaps.append((pr.get("number"), pr.get("headRefName", "?"), shared))
    return overlaps, ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--branch", default=None, help="default: current branch")
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    branch = args.branch
    if branch is None:
        code, out = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
        branch = out.strip() if code == 0 else "HEAD"

    files = changed_files(root, args.base, branch)
    print(f"branch {branch} vs {args.base}: {len(files)} file(s) changed")

    problems: list[str] = []

    # "Already landed" is meaningless when the branch IS the base: on `main`,
    # `git cherry origin/main main` reports nothing unmerged by definition, so the
    # check fired on the default branch and turned the gate red on `main` while
    # passing in the feature worktree. A guard must be evaluated where it runs.
    _, head_sha = _git(root, "rev-parse", branch)
    _, base_sha = _git(root, "rev-parse", args.base)
    is_base = bool(head_sha.strip()) and head_sha.strip() == base_sha.strip()

    if not is_base and already_landed(root, args.base, branch):
        problems.append(
            f"{branch} has no patches absent from {args.base} — its work is already "
            "landed. Merging changes nothing; re-doing the work is waste."
        )
    if not files:
        print("  no changed files: nothing to overlap")

    # Local branch overlap is ADVISORY, not a failure. `git cherry` reports a
    # squash-merged branch as unmerged, because a squash rewrites the patch-id —
    # so a clone accumulates stale branches that look like active work. Nine of
    # them fired on this repository's first run, all long since landed. A check
    # that cries wolf on every run is a check people learn to ignore, which is
    # worse than no check. Open PRs are authoritative because a PR is live by
    # definition.
    advisories: list[str] = []
    for other, shared in local_overlaps(root, args.base, branch, files):
        advisories.append(
            f"local branch {other} looks unmerged and touches {len(shared)} of the "
            f"same file(s): {shared[:5]}"
        )

    remotes, note = remote_overlaps(root, branch, files)
    for number, head, shared in remotes:
        problems.append(
            f"open PR #{number} ({head}) touches {len(shared)} of the same file(s): "
            f"{shared[:5]}"
        )
    if note:
        print(f"  {note}", file=sys.stderr)

    if advisories:
        print("\nlocal branches that may overlap (advisory):")
        for advisory in advisories:
            print(f"  - {advisory}")

    if problems:
        print("\npre-flight found overlapping work:")
        for problem in problems:
            print(f"  - {problem}")
        print(
            "\nCoordinate before merging: the other work may already cover this, or "
            "may need rebasing first."
        )
        return 1 if args.check else 0

    print("  no blocking overlap found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
