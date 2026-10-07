<!-- Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away. -->

# Completion Packet Standard

Every implementation issue must produce a machine-readable completion packet before it can enter `DONE`.

The packet is a handoff between builder, test engineer, reviewers, evidence verifier, reporter and delivery tooling. It records claims and evidence; it is not a substitute for the evidence itself.

## Required schema

```yaml
schema_version: 1

work:
  repository: owner/repo
  issue: 123
  parent: 100
  status: COMPLETE # COMPLETE | PARTIAL | BLOCKED
  branch: feature/123-example
  worktree: ../repo-wt/issue-123-example

specification:
  path: docs/specs/ISSUE-123-example.md
  commit: null

plan:
  path: docs/plans/ISSUE-123-plan.md
  commit: null

changes:
  - file: src/example.py
    purpose: bounded description

commands_run:
  - command: pytest tests/example -q
    exit_code: 0
    result: 12 passed
    evidence_ref: null

tdd:
  mode: REQUIRED # REQUIRED | CHARACTERISATION | CONTRACT | NOT_APPLICABLE | BLOCKED
  acceptance_criteria:
    - AC-001
  red:
    test_ref: tests/test_example.py::test_example_behaviour
    command: pytest tests/test_example.py::test_example_behaviour -q
    exit_code: 1
    classification: EXPECTED_BEHAVIOUR_FAILURE
    reason: requested behaviour is not implemented
    evidence_ref: evidence/tdd/red.log
  green:
    test_ref: tests/test_example.py::test_example_behaviour
    command: pytest tests/test_example.py::test_example_behaviour -q
    exit_code: 0
    result: 1 passed
    evidence_ref: evidence/tdd/green.log
  refactor:
    performed: true
    validation_command: pytest tests/test_example.py -q
    exit_code: 0
    evidence_ref: evidence/tdd/refactor.log

tests:
  status: passed
  added: []
  changed: []
  uncovered_cases: []

commits:
  - sha: abc123
    message: "feat: implement example"

pull_request:
  number: 456
  state: draft
  url: null
  ci_status: passed

claims:
  - id: CLAIM-001
    claim: Example behaviour is implemented.
    evidence:
      - src/example.py
      - tests/test_example.py
    verification: SUPPORTED

# Required for packets produced after adoption of the defect-priority standard.
# Legacy schema_version: 1 packets may omit this block during rollout.
defects:
  highest_unresolved_priority: NONE # P0 | P1 | P2 | P3 | NONE
  items:
    - id: DEFECT-001
      priority: P1
      state: VERIFIED_FIXED # OPEN | FIX_IN_PROGRESS | FOUND_AND_FIXED | VERIFIED_FIXED | DEFERRED | BLOCKED
      summary: Parser used the wrong acceptance-criterion result column.
      evidence:
        - tests/test_spec_claims.py::test_declared_four_column_row
      regression_evidence:
        - mutation: reverting to three-column parsing makes three tests fail
      github_issue: null
      blocks_pr: false

review:
  local:
    reviewer: swift-qwen38-27b-oq6-mtp
    status: PASS
    findings: []
  cloud:
    required: false
    reviewer: null
    status: NOT_REQUIRED
    findings: []
  specialist:
    security_required: false
    safety_policy_required: false
    dissent_required: false
    findings: []

evidence_verification:
  verifier: granite-4.2-8b
  status: PASS
  findings: []

verification_evidence:
  schema_version: "1.0"
  packet: .repo-standards/evidence/<sha>.json
  sha256: <digest>
  state: PASS # PASS | FAIL | BLOCKED_TOOLING | BLOCKED_FINDING_TRACKING
  controls:
    - control_id: RS-SEC-001
      status: PASS
  tracked_findings: []
  ci_run: https://github.com/owner/repo/actions/runs/1

risks:
  known: []
  accepted: []
  unresolved: []

reporter:
  required: true
  status: COMPLETE
  artefacts: []

completion:
  pr_ready: true
  done_eligible: true
  completed_at: null
```

For `NOT_APPLICABLE`, the TDD section records a reason and alternate deterministic validation instead
of RED/GREEN evidence:

```yaml
tdd:
  mode: NOT_APPLICABLE
  reason: documentation-only change; no executable behaviour changed
  alternate_validation:
    command: make docs-check
    exit_code: 0
    evidence_ref: evidence/docs-check.log
```

For `BLOCKED`, record the blocking condition and evidence. A blocked TDD requirement cannot support
`pr_ready: true` or `done_eligible: true`.

## Defect priority semantics

Defect priority is not action queue order and is not estimated fix effort. It expresses remediation urgency from impact and risk:

| Priority | Meaning | Delivery effect |
| --- | --- | --- |
| `P0` | Critical: false-green safety/quality/release gate, security/privacy exposure, data loss/corruption, invalid evidence represented as verified, or systemic validation failure | Stop discretionary work. Always block `pr_ready` and `done_eligible` until verified fixed. |
| `P1` | High: core functionality incorrect, acceptance criterion invalid, major regression, required review/testing/delivery gate unavailable, or material correctness/reliability failure | Fix before `PR_READY` unless an explicit repository-authorised waiver is recorded. |
| `P2` | Medium: genuine defect, edge case, test weakness or maintainability problem that does not invalidate the current delivery | Track and normally remediate before unrelated discretionary work. May be non-blocking under repository policy. |
| `P3` | Low: cleanup, minor documentation/cosmetic issue, optimisation or low-risk technical debt | Track/backlog; does not block delivery by default. |

Defect state is exactly one of:

```text
OPEN | FIX_IN_PROGRESS | FOUND_AND_FIXED | VERIFIED_FIXED | DEFERRED | BLOCKED
```

`highest_unresolved_priority` is derived only from defects whose state is `OPEN`, `FIX_IN_PROGRESS`, `DEFERRED` or `BLOCKED`. `FOUND_AND_FIXED` and `VERIFIED_FIXED` remain in the packet as provenance and regression evidence but do not count as unresolved.

A defect fixed during the current work does not require a redundant open GitHub issue solely because it once existed. It must remain recorded in the packet with fix/regression evidence. Any defect that remains unresolved at turn completion must carry a durable GitHub issue reference unless issue creation itself is blocked and that blocking reason is recorded elsewhere in the completion evidence.

## Fix-first ordering

The default remediation order is:

```text
P0 → P1 → P2 → requested feature work → P3
```

The forward-progress governor and dispatch tooling must use `highest_unresolved_priority` before ordinary delivery sequencing. In particular:

- unresolved `P0` always becomes the primary remediation path and prevents `pr_ready: true` / `done_eligible: true`;
- unresolved `P1` prevents `pr_ready: true` / `done_eligible: true` unless a valid authorised waiver exists under repository policy;
- `P2` is tracked and queued ahead of unrelated discretionary work where practical;
- `P3` is backlog work and does not pre-empt required delivery gates.

## Rules

- Do not claim a command passed unless it actually ran.
- Do not treat a builder/reviewer summary as source evidence.
- Evidence references must resolve to actual files, diffs, logs, CI results or other authoritative artefacts.
- For behaviour-changing implementation, TDD evidence follows `docs/process/test-driven-development.md`.
- `REQUIRED`, `CHARACTERISATION` and `CONTRACT` modes require valid RED and GREEN evidence tied to the affected acceptance criterion before the packet can support completion.
- RED must be classified `EXPECTED_BEHAVIOUR_FAILURE`; syntax/import/infrastructure/baseline/unrelated failures do not satisfy the TDD gate.
- GREEN must refer to the same behavioural test/check demonstrated by RED.
- `NOT_APPLICABLE` requires a reason and alternate deterministic validation; it is not an unverified bypass.
- `BLOCKED` cannot be translated into successful TDD evidence.
- Builder TDD does not replace the independent `TESTING` state or independent review.
- `UNCLEAR` is valid when evidence is insufficient.
- Every material discovered defect receives exactly one `P0`–`P3` priority and one defect state.
- Priority is based on impact/risk, never on how easy the fix appears.
- A false-green verification or release gate is `P0` unless stronger evidence proves the reported behaviour did not occur.
- An unresolved `P0` prevents `pr_ready: true` and `done_eligible: true` without exception.
- An unresolved `P1` prevents `pr_ready: true` and `done_eligible: true` unless an explicit repository-authorised waiver is present in evidence.
- A supported blocking finding prevents `pr_ready: true` until resolved or explicitly accepted under repository policy.
- Fixed-in-turn defects remain in `defects.items` with regression evidence; do not erase the fact that the defect existed.
- The reporter may transform the packet into worklogs/summaries but must not alter source evidence, defect priority/state, or silently upgrade verification status.
- `status: COMPLETE` is invalid when `verification_evidence.state != PASS` unless every non-PASS control carries an unexpired `exception`.
