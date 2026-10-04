<!-- Managed by harkers/repo-standards at revision 5371ef03. Use .repo-standards.yml overrides instead of editing this header away. -->

# Test-Driven Development Standard

Managed builder workflows use test-driven development for behaviour-changing implementation when a
deterministic automated test is reasonably possible.

The purpose of this standard is not to maximise test count. It is to require evidence that the
requested behaviour was absent or incorrect before production code changed, then prove that the
same behaviour is satisfied after the change.

The canonical builder loop is:

```text
approved bounded task
        ↓
identify smallest observable behaviour
        ↓
RED
write or modify the behavioural test first
run it
prove it fails for the expected reason
        ↓
GREEN
make the minimum production change
run the same test
prove it passes
        ↓
REFACTOR
clean implementation/test code while relevant tests remain green
        ↓
task-level validation / regression checks
        ↓
validated atomic commit
        ↓
independent test engineer / review / verification
```

RED / GREEN / REFACTOR are evidence milestones inside `IN_PROGRESS`. They are not additional
WorkItem lifecycle states and do not replace the canonical task state machine.

## Applicability

Every bounded implementation task declares one TDD mode:

```text
REQUIRED
CHARACTERISATION
CONTRACT
NOT_APPLICABLE
BLOCKED
```

### `REQUIRED`

Use for features, bug fixes, refactors and other observable behaviour changes where a deterministic
automated test can reasonably demonstrate the requirement.

### `CHARACTERISATION`

Use when changing legacy behaviour that is insufficiently specified by tests. First capture the
existing behaviour with a deterministic characterisation test, then introduce the required failing
case before changing production behaviour.

### `CONTRACT`

Use where the best executable proof is a schema, protocol, CLI, configuration, API or other contract
check rather than a conventional unit test. The same RED-before-GREEN requirement applies to the
contract check.

### `NOT_APPLICABLE`

Use only when a behavioural RED/GREEN test is not reasonably meaningful, for example a prose-only
documentation correction. Record the reason and the alternate deterministic validation that will be
used instead.

`NOT_APPLICABLE` is not a convenience escape from writing a difficult test.

### `BLOCKED`

Use when TDD should apply but the repository, test harness, environment or another dependency makes
a valid RED/GREEN cycle impossible. Record the blocker and the single action required to resolve or
escalate it. Do not silently continue as though TDD passed.

## Mandatory builder sequence

For `REQUIRED`, `CHARACTERISATION` and `CONTRACT` tasks, the builder MUST:

1. read the approved issue/specification/plan and identify the acceptance criterion being changed;
2. identify the smallest externally observable behaviour that demonstrates that criterion;
3. write or modify the test/check before changing the production implementation for that behaviour;
4. run the targeted test/check and capture the RED result;
5. establish that RED failed for the expected behavioural reason;
6. make the minimum production change required to satisfy the behaviour;
7. run the same targeted test/check and capture the GREEN result;
8. refactor only while the relevant tests remain green;
9. run the task-level targeted regression/validation gate;
10. preserve the commands/results as evidence and only then hand off for independent testing.

A builder MUST NOT claim TDD compliance from a test created only after the production behaviour was
implemented.

## Valid RED evidence

A non-zero command exit is not automatically a valid RED.

A valid RED demonstrates all of the following:

```text
new or deliberately changed behavioural test/check executed
+
behaviour is not currently satisfied
+
failure is causally related to the missing/incorrect requested behaviour
+
failure is not merely a pre-existing baseline failure
```

Classify the RED outcome as one of:

```text
EXPECTED_BEHAVIOUR_FAILURE
INVALID_TEST
BASELINE_FAILURE
INFRASTRUCTURE_FAILURE
UNRELATED_FAILURE
```

Only `EXPECTED_BEHAVIOUR_FAILURE` permits progression to GREEN.

The following are not valid RED evidence unless the approved requirement is specifically about that
condition:

- syntax errors in the new test;
- missing imports or dependencies;
- test-runner/configuration failure;
- unavailable infrastructure;
- unrelated tests already failing on the baseline;
- a timeout with no demonstrated behavioural cause;
- a test that already passes before the production change.

If the test already passes, determine whether the behaviour already exists, the test is vacuous, or
the acceptance criterion/test is wrong. Do not manufacture a failure to satisfy the ritual.

## GREEN evidence

GREEN requires the same behavioural test/check used for RED to execute successfully after the
production change.

GREEN proves only that the targeted behaviour now satisfies that check. It does not prove the whole
task is complete. The builder must still run the required targeted regression/validation gate, and
the independent test/review/verification stages remain mandatory where configured.

A builder MUST NOT weaken, delete or rewrite a correct failing test merely to make incorrect
production behaviour pass. If the approved specification establishes that the test itself is wrong,
record that decision and evidence explicitly.

## REFACTOR evidence

Refactoring is optional when there is nothing useful to clean up. When performed, relevant targeted
tests MUST remain green throughout or be rerun immediately after the refactor.

Do not add speculative refactors outside the bounded task merely because the tests are green.

## Evidence contract

TDD chronology is execution evidence, not a Git-history convention. Separate RED and GREEN commits
are not required.

The evidence should be representable as:

```yaml
tdd:
  mode: REQUIRED
  acceptance_criteria:
    - AC-003

  red:
    test_ref: tests/test_router.py::test_retries_failed_request
    command: pytest tests/test_router.py::test_retries_failed_request -q
    exit_code: 1
    classification: EXPECTED_BEHAVIOUR_FAILURE
    reason: retry behaviour is not implemented
    evidence_ref: path/to/red.log

  green:
    test_ref: tests/test_router.py::test_retries_failed_request
    command: pytest tests/test_router.py::test_retries_failed_request -q
    exit_code: 0
    result: 1 passed
    evidence_ref: path/to/green.log

  refactor:
    performed: true
    validation_command: pytest tests/test_router.py -q
    exit_code: 0
    evidence_ref: path/to/refactor.log
```

For `NOT_APPLICABLE`, record instead:

```yaml
tdd:
  mode: NOT_APPLICABLE
  reason: documentation-only change; no executable behaviour changes
  alternate_validation:
    command: make docs-check
    exit_code: 0
    evidence_ref: path/to/docs-check.log
```

For `BLOCKED`, record the blocking condition and its evidence. `BLOCKED` cannot be translated into
successful TDD evidence.

## Relationship to the task state machine

For TDD-applicable work:

```text
IN_PROGRESS
  ├── tdd.red       -> valid expected behavioural failure captured
  ├── tdd.green     -> same behaviour now passes
  └── tdd.refactor  -> refactor validation passes or refactor is explicitly not needed
        ↓
TASK_IMPLEMENTED
        ↓
TASK_VALIDATED
```

`TASK_IMPLEMENTED` means the bounded implementation reached GREEN for all TDD-required behaviours.
`TASK_VALIDATED` means the subsequent task-specific validation/regression gate passed with evidence.

The later canonical `TESTING` state remains independent testing. Builder TDD must not be used as a
substitute for the independent test engineer.

## Relationship to independent testing

The builder answers:

> Did I demonstrate the requested behaviour failing before implementation and passing after it?

The independent test engineer answers:

> What did the builder miss, and does the implementation survive independent regression testing?

The test engineer does not accept builder prose as proof, and the builder may not self-approve the
independent testing gate.

## Completion and handoff rules

A builder MUST NOT propose the independent testing gate as the next action for TDD-applicable work
unless required RED and GREEN evidence exists and task-level validation has passed.

If RED evidence is missing, invalid or unrelated, the next action is to repair/establish the test
contract, not to advance the workflow.

If GREEN fails, the task remains implementation work.

If regression validation fails after GREEN, the task returns to implementation/repair and cannot be
reported complete.

The completion packet records or references TDD evidence; the evidence itself remains authoritative.
