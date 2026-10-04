<!-- Managed by harkers/repo-standards at revision 5371ef03. Use .repo-standards.yml overrides instead of editing this header away. -->

# Canonical Agent Turn Handoff

Every managed agent turn ends with a short, structured closing block. It is how the next agent
continues the work without replaying the previous conversation, and how the system determines the
single next bounded action.

This document is **prompt-level guidance**. It defines no file format, no `schema_version`, and no
machine-parseable artifact. Nothing in the sync path or CI reads it as data. The canonical
completion packet (`docs/process/completion-packet.md`) remains the only machine-readable delivery
record, and remains the Forward Progress Governor's only required input.

## The closing block

```yaml
status: SUCCESS        # SUCCESS | PARTIAL | BLOCKED | FAILED
summary: >
  What was actually achieved this turn.
evidence:
  - { ref: path/to/evidence, type: file }   # file|diff|test|command|commit|pr|log|other
remaining:
  - Work still required for the current bounded objective.
problems:
  - Any error, failed test, defect or unresolved finding.
proposed_next:
  capability: TESTING_FAST
  action: >
    One bounded action.
  reason: >
    Why this action most directly advances the objective.
```

`status` is one of `SUCCESS`, `PARTIAL`, `BLOCKED`, `FAILED`. Evidence `type` is one of `file`,
`diff`, `test`, `command`, `commit`, `pr`, `log`, `other`.

`proposed_next.capability` MUST be a capability from the canonical taxonomy in
`docs/architecture/model-routing.md`.

## `proposed_next` is singular

An agent proposes **one** next bounded action. Not a ranked list. Not a menu of options.

Where several technically valid actions exist, choose the one that most directly:

1. completes an unmet acceptance criterion;
2. resolves a current blocker or failure;
3. produces missing evidence required by the active gate;
4. executes the next mandatory delivery gate; or
5. reduces uncertainty that prevents one of the above.

Only when no safe bounded choice can be made within the approved scope may the turn end `BLOCKED`
with an escalation named in `problems`.

## Prohibited in the handoff

```text
NO EMPTY HANDOFF
NO GENERAL COMMENTARY AS A SUBSTITUTE FOR ACTION
NO OPTION DUMPING
NO "WHAT WOULD YOU LIKE ME TO DO NEXT?" WHEN STATE/EVIDENCE DETERMINES THE NEXT STEP
NO UNDISPOSED FAILURE
NO BLOCKER WITHOUT A NEXT ACTION OR ESCALATION TARGET
NO COMPLETE VERDICT WHEN THE HANDOFF REPORTS FAILED/INCOMPLETE WORK
NO NEXT AGENT WITHOUT A BOUNDED INSTRUCTION
NO SCOPE-BROADENING RECOMMENDATION UNRELATED TO THE ACTIVE OBJECTIVE
```

Prohibited:

> "You could run tests, review the code, investigate the error, or perhaps refactor the routing layer."

Required:

> "Dispatch `test-engineer` to run the missing regression validation against AC-2 and AC-3."

The first delegates orchestration back to the user. The second advances the project.

## Convergence rules

```text
CURRENT OBJECTIVE > GENERAL ADVICE
REQUIRED GATE > OPTIONAL IMPROVEMENT
EVIDENCE-BACKED ACTION > SPECULATION
ONE NEXT ACTION > MENU OF OPTIONS
CONTINUE WITHIN SCOPE > ASK USER FOR AN ORDINARY REVERSIBLE CHOICE
ESCALATE ONLY WHEN THE DECISION CANNOT SAFELY BE MADE WITHIN EXISTING AUTHORITY
```

A useful but non-blocking future idea does not belong in the handoff. Durable backlog capture is a
later phase.

## Decision ordering

Applied when determining the next action:

```text
1. What is the active bounded objective, acceptance criterion or gate?
2. Was useful work performed against it?      NO -> CONTINUE / BLOCK / ESCALATE
3. Did the turn report an error, failed test, blocker, unresolved finding
   or incomplete required work?               YES -> it MUST NOT yield COMPLETE
4. Is there a specific repair that resolves it?   YES -> that one action
5. Is required evidence or validation missing?   YES -> the relevant test/verify/review action
6. Is there an obvious next required delivery gate?   YES -> that gate
7. Are several ordinary reversible actions possible within approved scope?
   YES -> choose the one that most directly advances the objective; do not return alternatives
8. Does the choice materially change architecture, scope, security posture, destructive
   behaviour or another explicit authority boundary?   YES -> ESCALATE the exact decision
9. Otherwise, if the objective is genuinely complete and gates are satisfied -> COMPLETE
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
the completion packet.

## Relationship to the task state machine

The task state machine (`docs/process/task-state-machine.md`) remains authoritative. A handoff may
propose work in a given state; it does not transition the state. Automatic state mutation is a later
phase.
