<!-- Managed by harkers/repo-standards at revision dc639067. Use .repo-standards.yml overrides instead of editing this header away. -->

# Engineering and Operability Standard

Owner instruction, 2026-11-06. These rules came out of moving MediaFlow from athena to Zeus VM 221,
where each gap below cost time. This file is the canonical source; `AGENTS.md`, the global Claude
instructions and the Harker Knowledge vault note **Engineering standards** point here. Logging has
its own standard: `docs/process/logging.md`.

## How work is done

1. **New work, new worktree.** Every change starts on a new branch in its own git worktree. Work
   MUST NOT be done in the live or default checkout, and one worktree serves one piece of work
   (see the worktree rule in `AGENTS.md`). The worktree is removed once its branch is merged.
2. **CLI-first tools.** A tool or service the estate builds exposes each capability through a
   non-interactive command line (flags, exit codes, machine-readable output such as JSON) before
   or alongside any UI, so agents and scripts can drive it. When operating systems and services,
   prefer their CLI or API over a web UI, and record the commands used.
3. **The vault is the human reference.** After a standard, decision or runbook changes, the
   affected Harker Knowledge vault note is updated in the same piece of work
   (`docs/process/knowledge.md`). The vault links to the canonical file here rather than copying it.

## Running software

4. **Startup self-check.** On start, a service MUST check that it can use what it depends on
   (data directories writable, media roots and network mounts readable as the service user,
   credential files present, required binaries runnable) and log each failure at `error` naming
   the path and the error. A missing hard dependency stops startup; a missing optional one is a
   `warn` and the feature is marked unavailable.
5. **External services.** Request rates and concurrency for third-party APIs are configuration
   with documented safe defaults, not constants in code. A `429` or `503` MUST be retried with
   backoff, honouring `Retry-After`, up to a bounded number of attempts, then logged at `warn`.
6. **Long jobs run inside the service.** Work that takes minutes (scans, imports, migrations)
   runs inside the service and reports progress through its API and UI: stage, done, total and
   an estimate. It is safe to stop and re-run. A command-line entry point may start it, but it
   goes through the service rather than running unseen beside it.
7. **Version identity.** Every build carries its version and commit. It is printed by
   `--version`, logged at startup and, for services, returned by a version or health endpoint,
   so what is deployed can be checked without comparing file hashes.

## Delivering software

8. **Every deploy records a rollback.** Before replacing a running version, keep the previous
   binary or image and its config, back up any database it writes, and record the version id
   and the exact rollback command where the deploy is logged (vault note or `DECISIONS.md`).
   After the deploy, check the logs (see the global post-deploy rule).
9. **Tests do not depend on real time.** Tests MUST NOT rely on wall-clock sleeps or machine
   speed for correctness: use paused or fake clocks and explicit synchronisation. A test that
   fails intermittently is quarantined with an issue and a named owner, and fixed rather than
   re-run until green.
10. **Moving a service to another host** follows the vault runbook **Moving a service to another
    host**: user and group ids, share and file permissions tested as the service user, DNS and
    host overrides, firewall rules, absolute paths stored in data, secrets, backups and the
    rollback path. The move is not done until every file the service needs has been opened as
    the service user on the new host.

## Review

A change that skips one of these rules without a recorded reason is a review finding, graded by
its effect on the person running the software.
