<!-- Managed by harkers/repo-standards at revision dc639067. Use .repo-standards.yml overrides instead of editing this header away. -->

# Logging and Diagnostics Standard

Owner standing instruction, 2026-11-06: **software built or changed in this estate ships with
useful logs and a verbose mode from its first version.** This file is the canonical logging
policy; `AGENTS.md` and the global Claude instructions point here rather than repeating it.

Origin: a MediaFlow film failed to play after a host move and the server log said nothing. The
file-open failure was logged only at `debug`, the level was fixed at `info`, and the web player
showed a generic message (vulcan/mediaflow PR 40). The cause, an NFS permission, took an
investigation that one log line would have answered.

## Rules

1. **Adjustable level.** A service or tool MUST let an operator change its log level without a
   rebuild: a config key, an environment variable (`RUST_LOG`, `LOG_LEVEL` or the ecosystem's
   usual name), or both. The default is `info`; `debug` is the verbose mode. An invalid level is
   a startup error, not silently ignored.
2. **Failures are visible by default.** Every failure a user or operator can hit (file open,
   permission, network, external API, database, timeout, rejected input, subprocess exit) MUST be
   logged at `warn` or `error`, never only at `debug`, and MUST NOT be swallowed. The line carries
   the context needed to act: the object's id, path or URL, host, status code and the underlying
   error text.
3. **Verbose mode explains decisions.** `debug` covers the decisions behind normal operation
   (which plan, which branch, which retry, which cache hit) so a reproduction with `debug` on
   shows why, not only what.
4. **Clients report to the server.** A client the estate builds (web app, TV app, CLI talking to
   a service) MUST report user-visible failures to the server log, with what the user saw and
   the client's own error detail, so one log holds both sides. The message shown to the user
   says what went wrong in plain words, not only "something went wrong".
5. **Long work shows progress.** Jobs that run for minutes (scans, imports, migrations, backups)
   log start, periodic progress (done / total) and a summary with counts and failures.
6. **No secrets.** Logs MUST NOT contain passwords, tokens, API keys, session cookies or private
   keys, at any level. Text from untrusted sources (clients, files, remote APIs) has control
   characters stripped and is length-capped before it is logged.
7. **Findable.** Each service documents where its logs go (file path, journald unit or
   container) in its runbook or README, and the vault note for the service links to it.

## Review

Missing or inadequate logging is a review finding, graded by effect: a failure path that would
leave an operator with no log line is at least `Important`. When troubleshooting a failure that
left no trace, add the missing logging in the same change as the fix, with a test where the
failure path is testable.

## Not in scope

Metrics, tracing backends and log shipping are optional per service; this standard asks for
good local logs first.
