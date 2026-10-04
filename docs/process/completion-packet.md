<!-- Managed by harkers/repo-standards at revision d65d8d54. Use .repo-standards.yml overrides instead of editing this header away. -->

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
- A supported blocking finding prevents `pr_ready: true` until resolved or explicitly accepted under repository policy.
- The reporter may transform the packet into worklogs/summaries but must not alter source evidence or silently upgrade verification status.
