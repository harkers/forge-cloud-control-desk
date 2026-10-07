# Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away.
"""Worktree audit: find worktrees whose work is already landed, and prune them.

`process/worktrees.md` requires every worktree to be removed once its work is
merged (`git worktree remove` + `git worktree prune`). Nothing enforced it, so it
was not done: rs#49 collected six stale worktrees, and five more accumulated
within hours — four of them from work that had already merged.

That debris is not harmless. Twice in one session an agent nearly re-fixed
already-merged work because a leftover worktree made it look outstanding.

The safety rule this tool exists to enforce: **never remove a worktree that is
not provably landed.** A worktree is removable only when its branch has no
unmerged patches and its tree is clean. Everything else is reported with the
reason, and left alone.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SAFE = "SAFE_TO_REMOVE"
DIRTY = "DIRTY"
UNMERGED = "UNMERGED"
DETACHED = "DETACHED"
PRIMARY = "PRIMARY"
MISSING = "PATH_MISSING"


def _run(args: list[str], cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def primary_path(root: Path) -> Path | None:
    """The main working tree, regardless of which worktree the tool runs from.

    `git worktree list` always prints the main working tree first. Relying on
    `--root` instead mislabels the main checkout as a removable worktree whenever
    the tool is run from inside a linked worktree — and proposing to remove the
    main checkout is not a mistake worth leaving to git's own refusal.
    """
    records = worktrees(root)
    return Path(records[0]["path"]).resolve() if records else None


def worktrees(root: Path) -> list[dict[str, str]]:
    """Parse `git worktree list --porcelain` into records."""
    code, out, _ = _run(["git", "worktree", "list", "--porcelain"], root)
    if code != 0:
        return []
    records: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in out.splitlines():
        if line.startswith("worktree "):
            if current:
                records.append(current)
            current = {"path": line[len("worktree ") :]}
        elif line.startswith("branch "):
            current["branch"] = line[len("branch ") :].removeprefix("refs/heads/")
        elif line == "detached":
            current["detached"] = "true"
        elif line.startswith("HEAD "):
            current["head"] = line[len("HEAD ") :]
    if current:
        records.append(current)
    return records


def classify(record: dict[str, str], root: Path, base: str) -> str:
    """Why a worktree is or is not safe to remove."""
    path = Path(record["path"])
    if not path.is_dir():
        return MISSING
    primary = primary_path(root)
    if primary is not None and path.resolve() == primary:
        return PRIMARY
    if record.get("detached"):
        return DETACHED

    code, out, _ = _run(["git", "status", "--porcelain"], path)
    if code != 0:
        return MISSING
    if out.strip():
        return DIRTY

    branch = record.get("branch")
    if not branch:
        return DETACHED

    # `git cherry` prints '+' for a patch not present in base, '-' when present.
    code, out, _ = _run(["git", "cherry", base, branch], path)
    if code != 0:
        return UNMERGED
    if any(line.startswith("+") for line in out.splitlines()):
        return UNMERGED
    return SAFE


def audit(root: Path, base: str) -> list[dict[str, str]]:
    results = []
    for record in worktrees(root):
        status = classify(record, root, base)
        results.append(
            {
                "path": record["path"],
                "branch": record.get("branch", "(detached)"),
                "status": status,
            }
        )
    return results


def prune(root: Path, base: str) -> tuple[list[str], list[str]]:
    """Remove every SAFE_TO_REMOVE worktree. Returns (removed, failed)."""
    removed: list[str] = []
    failed: list[str] = []
    for row in audit(root, base):
        if row["status"] != SAFE:
            continue
        code, _, err = _run(["git", "worktree", "remove", row["path"]], root)
        if code == 0:
            removed.append(row["path"])
        else:
            failed.append(f"{row['path']}: {err.strip()[:120]}")
    if removed:
        _run(["git", "worktree", "prune"], root)
    return removed, failed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--base",
        default="origin/main",
        help="ref that work must already be merged into (default: origin/main)",
    )
    parser.add_argument("--prune", action="store_true", help="remove safe worktrees")
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero when a safe-to-remove worktree exists",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    rows = audit(root, args.base)

    if args.json:
        print(json.dumps({"base": args.base, "worktrees": rows}, indent=2))
    else:
        width = max((len(r["path"]) for r in rows), default=10)
        for row in rows:
            mark = {
                SAFE: "prunable",
                DIRTY: "dirty",
                UNMERGED: "unmerged",
                DETACHED: "detached",
                PRIMARY: "primary",
                MISSING: "missing-on-disk",
            }[row["status"]]
            print(f"  {row['path']:<{width}}  {row['branch']:<44} {mark}")

    prunable = [r for r in rows if r["status"] == SAFE]

    if args.prune:
        removed, failed = prune(root, args.base)
        for path in removed:
            print(f"removed {path}")
        for message in failed:
            print(f"FAILED {message}", file=sys.stderr)
        if failed:
            return 1
        return 0

    if args.check and prunable:
        print(
            f"{len(prunable)} worktree(s) hold only already-merged work; "
            "remove them with --prune",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
