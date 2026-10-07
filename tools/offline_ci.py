#!/usr/bin/env python3
# Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away.
"""Run a GitHub Actions workflow's steps locally, offline.

Why this exists
---------------
`standards/build-assurance.md` RS-BUILD-001 requires a repository to expose one
canonical verification entrypoint, and its evidence rules assume remote CI. Some
repositories cannot run hosted CI at all — a spending limit, a quota, an air-gapped
environment, or a policy decision not to send a repository to a third-party runner.

For those, the gate can still be satisfied honestly: run **the same workflow steps**,
locally, against **the same tree**, and record that run as the CI evidence. The
difference is who executes the checks, not what is checked.

This tool does not reimplement any control. It extracts each step of a workflow file
and executes it verbatim, so the local gate cannot silently drift from the hosted one.

What it cannot do
-----------------
- Steps using `uses:` (third-party or GitHub-provided actions) are **skipped and
  reported**. They cannot run offline; a skipped `uses:` step is a gap in the local
  evidence and must be declared, not assumed to have passed.
- Anything needing the network (dependency installation, live API calls) is skipped
  for the same reason.
- Hosted-runner environment specifics (OS image, package versions, services) are not
  reproduced. A local pass is strong evidence, not proof of a hosted pass.

Exit status
-----------
0 only if every executed step passed. Any failure exits non-zero. Skipped steps are
listed on stderr so a caller can decide whether the skips are acceptable; they never
turn a failure into a pass.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

STEP_RE = re.compile(r"^      - name: (?P<name>.+?)\n(?P<body>(?:        .*\n|\n)*)", re.MULTILINE)
RUN_RE = re.compile(
    r"^        run:[ \t]*(?P<inline>[^\n]*)\n(?P<block>(?:          .*\n|\n)*)",
    re.MULTILINE,
)
USES_RE = re.compile(r"^        uses: (?P<uses>\S+)", re.MULTILINE)

# Steps that cannot produce local evidence without a network or a hosted runner.
OFFLINE_UNSAFE = re.compile(
    # A download cannot succeed offline, and attempting it produced a spurious
    # step failure rather than a declared skip — the gate must name what it
    # cannot run, not half-run it. `curl`/`wget` cover the pinned-release
    # scanner installs this repository's own workflow uses.
    r"pip install|npm ci|npm install|actions/checkout|upload-artifact"
    r"|\bcurl\b|\bwget\b",
    re.IGNORECASE,
)

# The #125 P0.5 drift gate needs the network (pinned clone of a private
# repository) AND a repository secret (REPOCTL_CHECKOUT_TOKEN). Declared by
# name, not by script pattern: since the gate went fail-closed, a missing token
# is an `exit 1`, which is indistinguishable from a real local failure — and
# pattern-matching `git clone` would sweep up unrelated steps.
OFFLINE_UNSAFE_NAMES = {
    "Install repoctl (pinned)",
    "Validate agent baseline and authority graph are current",
}
DRIFT_GATE_REASON = "drift gate requires network + REPOCTL_CHECKOUT_TOKEN"


class Step:
    """One workflow step.

    `lang` is "python" when the step is a `python - <<'PY'` heredoc (executed
    directly) and "shell" otherwise (executed through bash, matching the hosted
    runner's default shell). Treating a shell step as Python is a silent
    mis-execution, so the distinction is explicit.
    """

    __slots__ = ("name", "script", "uses", "runnable", "reason", "lang")

    def __init__(
        self,
        name: str,
        script: str | None,
        uses: str | None,
        lang: str = "shell",
    ) -> None:
        self.name = name
        self.script = script
        self.uses = uses
        self.lang = lang
        if uses is not None:
            self.runnable, self.reason = False, f"uses {uses}"
        elif name in OFFLINE_UNSAFE_NAMES:
            self.runnable, self.reason = False, DRIFT_GATE_REASON
        elif script is None:
            self.runnable, self.reason = False, "no run: block"
        elif OFFLINE_UNSAFE.search(script):
            self.runnable, self.reason = False, "requires network or hosted runner"
        else:
            self.runnable, self.reason = True, ""


def parse_steps(workflow: str) -> list[Step]:
    """Extract runnable steps from a workflow file's contents."""
    steps: list[Step] = []
    for match in STEP_RE.finditer(workflow):
        name = match.group("name").strip()
        body = match.group("body")
        run = RUN_RE.search(body)
        uses = USES_RE.search(body)
        script: str | None = None
        lang = "shell"
        if run:
            inline = (run.group("inline") or "").strip()
            block = run.group("block")
            if inline and inline != "|":
                # Single-line form, e.g. `run: python -m py_compile sync/*.py`.
                script = inline
            elif block:
                # Strip the YAML block indent.
                lines = [ln[10:] if ln.startswith(" " * 10) else ln for ln in block.splitlines()]
                script = "\n".join(lines)
            # The whole step body runs through bash, exactly as the hosted runner
            # does. An earlier version extracted `python - <<'PY'` heredocs and ran
            # only the Python — so a step mixing shell and a heredoc silently
            # skipped its shell commands and reported PASS. A gate must not
            # half-run a step; bash handles heredocs natively.
        steps.append(Step(name, script, uses.group("uses") if uses else None, lang))
    return steps


def run_step(step: Step, root: Path, timeout: float | None = None) -> tuple[str, str]:
    """Return (status, detail) where status is PASS, FAIL or SKIP."""
    if not step.runnable:
        return "SKIP", step.reason
    if step.script is None:
        return "SKIP", "nothing to run"
    env = dict(os.environ)
    # Workflows are written for the hosted runner, where `python` exists. Many
    # developer machines (including macOS with Homebrew Python) expose only
    # `python3`, which would otherwise fail every step for a reason unrelated to
    # the check itself. Shim it rather than editing the workflow.
    if step.lang == "shell" and shutil.which("python", path=env.get("PATH")) is None:
        if shutil.which("python3", path=env.get("PATH")) is not None:
            shim = Path(tempfile.mkdtemp(prefix="offline-ci-shim."))
            (shim / "python").symlink_to(shutil.which("python3", path=env.get("PATH")))
            env["PATH"] = f"{shim}{os.pathsep}{env.get('PATH', '')}"
    try:
        if step.lang == "python":
            argv = [sys.executable, "-c", step.script]
        else:
            # The hosted runner's default shell on Linux is bash; match it so
            # line continuations and pipes behave identically.
            argv = ["bash", "-euo", "pipefail", "-c", step.script]
        proc = subprocess.run(
            argv,
            cwd=root,
            capture_output=True,
            text=True,
            env=env,
            # A hosted runner gives a step no interactive stdin. Without this a
            # step that reads stdin blocks forever when the parent happens to
            # have an open terminal (observed under pytest).
            stdin=subprocess.DEVNULL,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "FAIL", f"timed out after {timeout}s"
    except OSError as exc:  # pragma: no cover - platform failure
        return "FAIL", f"could not execute: {exc}"
    if proc.returncode == 0:
        return "PASS", ""
    lines = (proc.stdout + proc.stderr).strip().splitlines()
    return "FAIL", next((ln for ln in reversed(lines) if ln.strip()), f"exit {proc.returncode}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workflow", default=".github/workflows/validate.yml")
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--fail-on-skip", action="store_true", help="treat a skipped step as a failure"
    )
    parser.add_argument(
        "--step-timeout",
        type=float,
        default=600.0,
        help="per-step timeout in seconds (default: 600); 0 disables",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    path = Path(args.workflow)
    if not path.is_absolute():
        path = root / path
    if not path.is_file():
        print(f"offline gate: workflow not found: {path}", file=sys.stderr)
        return 2

    steps = parse_steps(path.read_text(encoding="utf-8"))
    if not steps:
        print(f"offline gate: no steps parsed from {path}", file=sys.stderr)
        return 2

    width = max(len(s.name) for s in steps)
    results = []
    for step in steps:
        status, detail = run_step(step, root, args.step_timeout)
        results.append((step.name, status, detail))

    for name, status, detail in results:
        mark = {"PASS": "ok  ", "FAIL": "FAIL", "SKIP": "skip"}[status]
        print(f"{mark} {name:<{width}}  {detail if status != 'PASS' else ''}".rstrip())

    failed = [r for r in results if r[1] == "FAIL"]
    skipped = [r for r in results if r[1] == "SKIP"]
    executed = [r for r in results if r[1] != "SKIP"]

    print(f"\n{len(executed) - len(failed)}/{len(executed)} steps passed ({len(skipped)} skipped)")
    if skipped:
        print("skipped steps are NOT evidence; declare them: ", file=sys.stderr)
        for name, _, detail in skipped:
            print(f"  - {name}: {detail}", file=sys.stderr)

    if failed:
        print("FAILED: " + "; ".join(n for n, _, _ in failed), file=sys.stderr)
        return 1
    if skipped and args.fail_on_skip:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
