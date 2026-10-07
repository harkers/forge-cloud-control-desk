<!-- Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away. -->

# Canonical Task State Machine

Managed repositories use an explicit delivery state machine so agents, CI and humans can reason about work consistently.

```text
DRAFT
  ↓
SPEC_READY
  ↓
PLAN_READY
  ↓
READY
  ↓
IN_PROGRESS
  ↓
TASK_IMPLEMENTED
  ↓
TASK_VALIDATED
  ↓
COMMITTED
  ↓
PR_DRAFT
  ↓
IMPLEMENTATION_COMPLETE
  ↓
TESTING
  ↓
REVIEW_LOCAL
  ↓
REVIEW_CLOUD        (conditional)
  ↓
SPECIALIST_REVIEW   (conditional)
  ↓
VERIFYING
  ↓
REPORTING
  ↓
PR_READY
  ↓
DONE

Fail-closed states (reachable from any active state during the assurance stages):
BLOCKED_TOOLING
BLOCKED_FINDING_TRACKING
```

## Build Assurance gate

`PR_READY` and `DONE` require a Verification Evidence Packet whose `state` is `PASS` for the commit under claim. The packet is the gate input, not a prose completion claim (see `standards/completion-evidence.md` and `process/completion-packet.md`).

The fail-closed states:

- `BLOCKED_TOOLING`: a required scanner, test runner or verification tool is unavailable. The state records `missing_control` and `missing_tool`; `tool unavailable` MUST NOT be recorded as `PASS`.
- `BLOCKED_FINDING_TRACKING`: a blocking finding requires a durable issue reference and issue creation cannot be completed. A blocking finding without a durable issue reference blocks `PR_READY` / `DONE`.

Both states block `PR_READY` / `DONE` until the missing tool becomes available or the finding is durably tracked and represented in the packet; the affected controls then re-run and the packet is regenerated.

The assurance stages sit between `task validation` and `atomic commit`:

```text
task validation
  → unit/integration tests
  → secret detection
  → SAST
  → SBOM generation
  → vulnerability scan
  → profile-specific assurance checks
  → classify findings
  → create/update deduplicated finding issues where required
  → atomic commit
```

## Planning decomposition

Broad work is decomposed before execution under `docs/process/planning-decomposition.md`. A broad
feature or epic remains a planning container; bounded executable child issues/WorkItems advance
through this state machine independently.

For decomposed work, an executable child may enter `PLAN_READY` only when its plan is dependency-valid,
independently verifiable and satisfies the canonical child-plan contract. A dependent child may be
fully documented but remains not ready for dispatch until its declared readiness conditions are met.

## TDD milestones inside `IN_PROGRESS`

RED / GREEN / REFACTOR are execution-evidence milestones, not additional WorkItem lifecycle states.
The canonical TDD rules are defined in `docs/process/test-driven-development.md`.

For TDD-applicable work the implementation path is:

```text
IN_PROGRESS
  ├── tdd.red       -> valid expected behavioural failure captured
  ├── tdd.green     -> the same behavioural test/check now passes
  └── tdd.refactor  -> relevant tests remain green, or refactor is explicitly not needed
        ↓
TASK_IMPLEMENTED
        ↓
TASK_VALIDATED
```

A task MUST NOT enter `TASK_IMPLEMENTED` merely because source files changed. Where TDD mode is
`REQUIRED`, `CHARACTERISATION` or `CONTRACT`, valid RED and GREEN evidence is required. Where mode
is `NOT_APPLICABLE`, the recorded reason and alternate deterministic validation are required.
`BLOCKED` TDD evidence cannot satisfy the gate.

## Repair loops

```text
TASK_VALIDATED     → IN_PROGRESS
TESTING            → IN_PROGRESS
REVIEW_LOCAL       → IN_PROGRESS
REVIEW_CLOUD       → IN_PROGRESS
SPECIALIST_REVIEW  → IN_PROGRESS
VERIFYING          → IN_PROGRESS
```

A supported blocking review finding creates a bounded fix task and returns the work to `IN_PROGRESS`. Re-review should focus on the changed delta plus any affected surrounding contract.

A repair that changes observable production behaviour re-enters the applicable TDD loop. A repair
MUST NOT reuse stale RED/GREEN evidence when the affected acceptance criterion or behavioural test
has materially changed.

## Blocking transitions

```text
ANY → BLOCKED
BLOCKED → READY
```

A blocked task must record:

- blocking condition;
- evidence;
- owner/dependency;
- next possible action;
- date/time last evaluated.

## Failure transitions

```text
IN_PROGRESS|TASK_VALIDATED|TESTING|REVIEW_LOCAL|REVIEW_CLOUD|SPECIALIST_REVIEW|VERIFYING → FAILED
FAILED → READY only after an explicit recovery/re-plan decision
```

## Gate definitions

- `SPEC_READY`: problem, goals, non-goals, interfaces, data/events, failure modes, security and measurable acceptance criteria are defined.
- `PLAN_READY`: bounded implementation tasks, dependencies, likely change surface and validation steps exist; when work was decomposed, the active executable child also satisfies `docs/process/planning-decomposition.md` and all declared readiness conditions required before dispatch.
- `READY`: dependencies and execution context are resolved. For any task that may mutate repository state, a single dedicated control-plane-assigned worktree MUST exist and be mechanically verified against the expected WorkItem, repository, branch and execution root before this state is entered. Read-only tasks may omit a worktree only when read-only behaviour is mechanically enforced. A worktree verification failure blocks the transition.
- `TASK_IMPLEMENTED`: the active bounded task has an implementation delta and, where TDD applies, reached GREEN for every TDD-required behaviour with valid RED/GREEN evidence; it has not yet passed the full task-level targeted validation gate.
- `TASK_VALIDATED`: targeted validation/regression checks for that task passed with captured evidence.
- `COMMITTED`: Delivery Ops created an atomic commit for the validated task.
- `PR_DRAFT`: branch is pushed and a draft PR exists using the correct template.
- `IMPLEMENTATION_COMPLETE`: all planned implementation tasks are committed and represented in the PR.
- `TESTING`: independent test engineer exercises completion claims and regression coverage. Builder TDD does not satisfy or replace this independent gate.
- `REVIEW_LOCAL`: independent fast local reviewer checks spec, diff, tests and scope.
- `REVIEW_CLOUD`: senior cloud engineering review when risk/routing policy triggers it.
- `SPECIALIST_REVIEW`: security, safety/policy, dissent/Jury or other specialist checks where triggered.
- `VERIFYING`: material completion/reviewer claims are resolved against source evidence.
- `REPORTING`: completion packet and engineering-memory handoff are generated.
- `PR_READY`: CI and configured gates pass; PR may move from draft to ready.
- `DONE`: repository completion policy is satisfied; a worker may not self-transition directly to this state.
- `BLOCKED_TOOLING`: a required assurance tool is unavailable; the state records `missing_control` and `missing_tool` and blocks `PR_READY` / `DONE`.
- `BLOCKED_FINDING_TRACKING`: a blocking finding has no durable issue reference because issue creation could not be completed; blocks `PR_READY` / `DONE`.

## Events

Implementations should emit or record transitions and evidence milestones using stable event names such as:

```text
worktree.allocated
worktree.verified
worktree.reverified
worktree.violation
worktree.released
tdd.red
tdd.green
tdd.refactor
tdd.not_applicable
tdd.blocked
task.implemented
task.validated
commit.created
branch.pushed
pr.created
pr.updated
testing.completed
review.local.completed
review.cloud.completed
review.finding.created
review.finding.verified
specialist_review.completed
verification.completed
fix.requested
report.generated
pr.ready
work.done
```

TDD events record evidence chronology only. They do not independently transition the WorkItem.
