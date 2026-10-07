#!/usr/bin/env python3
# Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away.
"""Refuse to create a commit in a protected branch's checkout.

`process/worktrees.md` already states the rule this enforces:

    MUST NOT use the live/default checkout for implementation, remediation, test
    authoring, commit creation or any other repository mutation.

A prompt-level MUST cannot stop an agent that has already staged files in the
wrong directory. This is the mechanical check for that specific failure: a
commit carrying staged content while the current branch is a protected branch.

Scope is deliberately narrow. It does not verify that a worktree was assigned,
that the branch matches the active issue, or that any of the other isolation
rules were followed; those need the control plane. This only catches the case
that is both cheap to detect and easy to do by accident.

Opting out is explicit and reported, never silent:

    REPO_STANDARDS_ALLOW_PROTECTED_COMMIT=1

Per `AGENTS.md`, a deviation requires repository override configuration
recorded against a linked issue; editing these standards is not itself a
deviation path.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

DEFAULT_PROTECTED = ("main", "master")
OPT_OUT_ENV = "REPO_STANDARDS_ALLOW_PROTECTED_COMMIT"


def check(
    branch: str | None,
    has_staged: bool,
    protected: tuple[str, ...] = DEFAULT_PROTECTED,
) -> str | None:
    """Return a violation message, or None when the commit is acceptable.

    A detached HEAD is permitted: it carries no branch name to protect, and a
    worktree may legitimately be inspected in that state.
    """
    if not has_staged or branch is None:
        return None
    if branch not in protected:
        return None
    return (
        f"refusing to commit on protected branch {branch!r} with staged changes.\n"
        "The live/default checkout is not a valid mutation target: mutating work "
        "MUST run in a dedicated worktree assigned to the active WorkItem "
        "(docs/process/worktrees.md, Isolation rules).\n"
        "Move the staged work to the assigned worktree and commit there:\n"
        "  git worktree add ../<repo>-wt/issue-<n>-<slug> -b <type>/<n>-<slug>\n"
        f"If this commit is deliberate repository maintenance, re-run with "
        f"{OPT_OUT_ENV}=1 and record the deviation against a linked issue."
    )


def opt_out_requested(env: dict[str, str] | None = None) -> bool:
    source = os.environ if env is None else env
    return source.get(OPT_OUT_ENV, "").strip() in {"1", "true", "TRUE", "yes"}


def current_branch(root: Path) -> str | None:
    """Branch name, or None for a detached HEAD or a non-git directory.

    `git symbolic-ref --short HEAD` is used rather than
    `git rev-parse --abbrev-ref HEAD` because the latter fails when HEAD is
    unborn (a repository with no commits yet), which is exactly the state of the
    first commit on a branch. Mapping that failure to "detached" would exempt the
    protected branch at the moment it is most likely to be committed to by
    mistake. It is kept as a fallback for older git versions.
    """
    for cmd in (
        ["git", "symbolic-ref", "--short", "HEAD"],
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
    ):
        try:
            out = subprocess.run(
                cmd,
                cwd=root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            continue
        if not out:
            continue
        return None if out == "HEAD" else out
    return None


def has_staged_changes(root: Path) -> bool:
    """True when the index carries content the next commit would record.

    Uses `git status --porcelain` rather than `git diff --cached --quiet HEAD`
    because the latter needs an existing HEAD: in a repository with no commits
    yet it exits non-zero for a reason unrelated to staging, which would report
    "nothing staged" and wave through the very first commit on a branch.

    Porcelain v1 puts the index status in the first column; `?` marks untracked
    paths, which are not staged.
    """
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return False
    if out.returncode != 0:
        return False
    for line in out.stdout.splitlines():
        if not line:
            continue
        if line[0] == "?" or line[1:2] == "?":
            continue  # untracked, not staged
        if line[0] not in (" ", ""):
            return True
    return False


def main(
    argv: list[str] | None = None,
    root: Path | None = None,
    env: dict[str, str] | None = None,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--protected",
        action="append",
        default=None,
        help="protected branch name; repeatable (default: main master)",
    )
    parser.add_argument("--root", default=None, help="repository root (default: cwd)")
    args = parser.parse_args(argv)

    protected = tuple(args.protected) if args.protected else DEFAULT_PROTECTED
    repo = Path(args.root) if args.root else Path.cwd()

    branch = current_branch(repo)
    staged = has_staged_changes(repo)
    violation = check(branch, staged, protected)
    if violation is None:
        return 0

    if opt_out_requested(env):
        print(
            f"WARNING: committing on protected branch {branch!r} with an "
            f"explicit {OPT_OUT_ENV} override. This deviation should be "
            "recorded against a linked issue.",
            file=sys.stderr,
        )
        return 0

    print(violation, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
