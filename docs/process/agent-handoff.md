<!-- Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away. -->

# Canonical Agent Turn Handoff

Every managed agent turn ends with a short, structured closing block. It is how the next agent
continues the work without replaying the previous conversation, and how the system determines the
single next bounded action.

This document is **prompt-level guidance**. It defines no file format, no `schema_version`, and no
machine-parseable artifact. Nothing in the sync path or CI reads it as data. The canonical
completion packet (`docs/process/completion-packet.md`) remains the only machine-readable delivery
record, and remains the Forward Progress Governor's only required input.

The handoff is nevertheless a mandatory behavioural contract. A free-text paragraph saying
"testing found four defects" is not a valid disposition of those defects. Each material problem must
be individually classified, prioritised and either durably tracked or explicitly recorded as fixed
in the current turn.

## The closing block

```yaml
status: PARTIAL        # SUCCESS | PARTIAL | BLOCKED | FAILED
summary: >
  What was actually achieved this turn.
evidence:
  - { ref: path/to/evidence, type: file }   # file|diff|test|command|commit|pr|log|other
remaining:
  - Work still required for the current bounded objective.
problems:
  - id: DEFECT-001
    priority: P0       # P0 | P1 | P2 | P3
    state: OPEN        # OPEN | FIX_IN_PROGRESS | FOUND_AND_FIXED | VERIFIED_FIXED | DEFERRED | BLOCKED
    summary: >
      A deliberately false claim can pass the verification gate.
    evidence:
      - { ref: tests/test_spec_claims.py::test_false_claim_fails, type: test }
    github_issue: "#123"   # issue ref | FIXED_IN_TURN | NOT_RAISED — BLOCKING REASON: <reason>
highest_unresolved_priority: P0   # P0 | P1 | P2 | P3 | NONE
proposed_next:
  capability: COMPLEX_CODE
  action: >
    Fix DEFECT-001 and add regression evidence before any lower-priority work.
  reason: >
    P0 is the highest unresolved priority and invalidates the completion gate.
```

`status` is one of `SUCCESS`, `PARTIAL`, `BLOCKED`, `FAILED`. Evidence `type` is one of `file`,
`diff`, `test`, `command`, `commit`, `pr`, `log`, `other`.

`proposed_next.capability` MUST be a capability from the canonical taxonomy in
`routing/capabilities.md`.

When there are no material problems, emit:

```yaml
problems: []
highest_unresolved_priority: NONE
```

Do not omit these fields merely because the turn was successful.

## Worktree identity in mutating turns

For a turn that mutates the repository, the closing block's `evidence` MUST reference the verified
worktree identity for that turn: the issue branch and the worktree path, as recorded by the control
plane before dispatch.

A mutating turn with no such evidence reference is not a valid handoff. It indicates either that the
turn ran outside its assigned worktree or that worktree verification evidence was never captured.
Both block the mutating gate rather than passing silently.

Read-only turns carry no worktree evidence requirement, consistent with the read-only condition in
`docs/process/worktrees.md`.

## Problem contract

Every material problem in `problems` has:

```text
id             stable turn-local identifier
priority       P0 / P1 / P2 / P3
state          OPEN / FIX_IN_PROGRESS / FOUND_AND_FIXED / VERIFIED_FIXED / DEFERRED / BLOCKED
summary        concise falsifiable description
evidence       one or more references when evidence exists
github_issue   durable issue reference, FIXED_IN_TURN, or explicit NOT_RAISED blocking reason
```

The canonical meanings of P0–P3 and the defect states are defined in
`docs/process/behavioral-policy.md`.

Rules:

1. **Classify immediately.** Do not collect defects in prose and defer triage to the next agent.
2. **False-green validation is P0 by default.** A test, evidence verifier or release gate that accepts
   a claim known to be false is P0 unless evidence proves it cannot affect a completion/release
   decision.
3. **Fixed defects stay visible.** `FOUND_AND_FIXED` / `VERIFIED_FIXED` use
   `github_issue: FIXED_IN_TURN` when a redundant issue is not required and include regression
   evidence in the turn/completion evidence.
4. **Unresolved defects are tracked.** `OPEN`, `FIX_IN_PROGRESS`, `DEFERRED` and `BLOCKED` material
   defects must have a durable GitHub issue before completion. If issue creation genuinely failed,
   say `NOT_RAISED — BLOCKING REASON: ...`; that is not a completion-ready state.
5. **Derive the highest priority.** `highest_unresolved_priority` must agree with the unresolved
   problem items. Never lower it to make the turn look complete.
6. **Severity and effort do not set priority.** Priority expresses remediation urgency from impact
   and risk. Action queue order is a separate concept.

## `proposed_next` is singular and fix-first

An agent proposes **one** next bounded action. Not a ranked list. Not a menu of options.

Apply this order before ordinary feature continuation:

```text
P0 → P1 → P2 → current requested feature/delivery work → P3
```

Where several technically valid actions exist, choose the one that most directly:

1. remediates or contains the highest unresolved P0;
2. remediates the highest unresolved/unwaived P1;
3. durably tracks an unresolved material defect that is not yet tracked;
4. remediates P2 where the fix-first policy requires it before unrelated discretionary work;
5. completes an unmet acceptance criterion;
6. resolves another current blocker or failure;
7. produces missing evidence required by the active gate;
8. executes the next mandatory delivery gate; or
9. reduces uncertainty that prevents one of the above.

P3 does not displace a required delivery gate. A P2/P3 defect may be non-blocking, but it may never
become transcript-only: durable tracking is still required when it remains unresolved.

Only when no safe bounded choice can be made within the approved scope may the turn end `BLOCKED`
with an escalation named in `problems`.

## Prohibited in the handoff

```text
NO EMPTY HANDOFF
NO FREE-TEXT DEFECT DUMP WITHOUT P0-P3 PRIORITY AND STATE
NO UNTRACKED MATERIAL UNRESOLVED DEFECT
NO GENERAL COMMENTARY AS A SUBSTITUTE FOR ACTION
NO OPTION DUMPING
NO "WHAT WOULD YOU LIKE ME TO DO NEXT?" WHEN STATE/EVIDENCE DETERMINES THE NEXT STEP
NO UNDISPOSED FAILURE
NO BLOCKER WITHOUT A NEXT ACTION OR ESCALATION TARGET
NO COMPLETE VERDICT WITH UNRESOLVED P0 OR UNWAVIED P1
NO COMPLETE VERDICT WHEN THE HANDOFF REPORTS FAILED/INCOMPLETE WORK
NO NEXT AGENT WITHOUT A BOUNDED INSTRUCTION
NO SCOPE-BROADENING RECOMMENDATION UNRELATED TO THE ACTIVE OBJECTIVE
```

Prohibited:

> "Testing found four defects. You should decide what to do next."

Required:

> "DEFECT-004 is P0 because the verification gate accepted a deliberately false claim. It is the
> highest unresolved priority. Dispatch `builder-primary` to fix DEFECT-004 and prove the gate fails
> on the regression case before lower-priority work continues."

The first delegates triage and orchestration back to the user. The second advances the project.

## Convergence rules

```text
HIGHEST UNRESOLVED DEFECT PRIORITY > LOWER-PRIORITY WORK
CURRENT OBJECTIVE > GENERAL ADVICE
REQUIRED GATE > OPTIONAL IMPROVEMENT
EVIDENCE-BACKED ACTION > SPECULATION
ONE NEXT ACTION > MENU OF OPTIONS
CONTINUE WITHIN SCOPE > ASK USER FOR AN ORDINARY REVERSIBLE CHOICE
ESCALATE ONLY WHEN THE DECISION CANNOT SAFELY BE MADE WITHIN EXISTING AUTHORITY
```

A useful but non-blocking future idea that is **not a material defect** does not belong in the
handoff. A material defect does belong and must be prioritised/tracked even when it is non-blocking.

## Decision ordering

Applied when determining the next action:

```text
1. Are there unresolved P0 defects?             YES -> FIX/CONTAIN highest P0; never COMPLETE
2. Are there unresolved P1 defects?             YES -> FIX highest P1 or validate explicit authorised waiver
3. Is any material unresolved defect untracked? YES -> CREATE/UPDATE durable GitHub issue
4. Is there P2 work that fix-first policy requires before unrelated discretionary work?
                                                YES -> that repair/tracking action
5. What is the active bounded objective, acceptance criterion or gate?
6. Was useful work performed against it?        NO -> CONTINUE / BLOCK / ESCALATE
7. Did the turn report another error, failed test, blocker, unresolved finding
   or incomplete required work?                 YES -> it MUST NOT yield COMPLETE when blocking
8. Is there a specific repair that resolves it? YES -> that one action
9. Is required evidence or validation missing?  YES -> the relevant test/verify/review action
10. Is there an obvious next required delivery gate? YES -> that gate
11. Are several ordinary reversible actions possible within approved scope?
    YES -> choose the one that most directly advances the objective; do not return alternatives
12. Does the choice materially change architecture, scope, security posture, destructive
    behaviour or another explicit authority boundary? YES -> ESCALATE the exact decision
13. Otherwise, if the objective is genuinely complete and gates are satisfied -> COMPLETE
```

## Handoff, review, and the completion packet are three different things

```text
Agent Handoff      -> small, per-turn continuation record. Prompt-level. This document.
Last-Turn Review   -> converges a previous turn's state and evidence into one next bounded action.
                     The Forward Progress Governor. Not ordinary code review.
Completion Packet  -> final verified audit record. docs/process/completion-packet.md.
Ordinary Review    -> correctness, scope and quality of a diff. Unchanged by this document.
```

The handoff does not replace ordinary functional or code review, and it does not assemble or mutate
the completion packet. Defect priority/state must agree across the handoff and completion packet;
the packet is authoritative for machine enforcement.

## Relationship to the task state machine

The task state machine (`docs/process/task-state-machine.md`) remains authoritative. A handoff may
propose work in a given state; it does not transition the state. Automatic state mutation is a later
phase.
