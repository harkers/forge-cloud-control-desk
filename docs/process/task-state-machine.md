<!-- Managed by harkers/repo-standards at revision cea6cf0c. Use .repo-standards.yml overrides instead of editing this header away. -->

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
```

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
- `PLAN_READY`: bounded implementation tasks, dependencies, likely change surface and validation steps exist.
- `READY`: dependencies, branch/worktree and execution context are resolved.
- `TASK_IMPLEMENTED`: the active bounded task has an implementation delta but has not yet passed its targeted validation.
- `TASK_VALIDATED`: targeted validation for that task passed with captured evidence.
- `COMMITTED`: Delivery Ops created an atomic commit for the validated task.
- `PR_DRAFT`: branch is pushed and a draft PR exists using the correct template.
- `IMPLEMENTATION_COMPLETE`: all planned implementation tasks are committed and represented in the PR.
- `TESTING`: independent test engineer exercises completion claims and regression coverage.
- `REVIEW_LOCAL`: independent fast local reviewer checks spec, diff, tests and scope.
- `REVIEW_CLOUD`: senior cloud engineering review when risk/routing policy triggers it.
- `SPECIALIST_REVIEW`: security, safety/policy, dissent/Jury or other specialist checks where triggered.
- `VERIFYING`: material completion/reviewer claims are resolved against source evidence.
- `REPORTING`: completion packet and engineering-memory handoff are generated.
- `PR_READY`: CI and configured gates pass; PR may move from draft to ready.
- `DONE`: repository completion policy is satisfied; a worker may not self-transition directly to this state.

## Events

Implementations should emit or record transitions using stable event names such as:

```text
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
