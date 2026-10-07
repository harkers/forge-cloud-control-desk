<!-- Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away. -->

# Issue Standard

Structured issues are the entry point for engineering work.

## Issue types

- **Epic** — large capability; never a direct implementation instruction.
- **Feature Request** — desired capability/outcome; may require decomposition.
- **Implementation Task** — bounded unit of work with spec, plan, branch/worktree and measurable acceptance criteria.
- **Investigation** — evidence-first analysis before a decision or implementation.
- **Spike / Research** — time-bounded experiment ending in an explicit decision gate.
- **Architecture Decision / ADR** — significant decision, alternatives, evidence, consequences and revisit trigger.
- **Bug / Incident** — defect/failure with reproduction, diagnostics, severity, priority and evidence.
- **Model Evaluation** — reproducible capability/routing experiment.
- **Review Finding** — falsifiable independent-review claim with verification state.
- **Security Finding** — structured security/trust-boundary claim with evidence and mitigation.

## Mandatory defect tracking

Agents discover defects while doing other work. `docs/process/behavioral-policy.md` makes durable
tracking mandatory for each **material unresolved** defect and requires fixed-in-turn defects to remain
in the completion packet with regression evidence.

Every material discovered defect receives exactly one priority:

```text
P0 | P1 | P2 | P3
```

Priority is remediation urgency from impact/risk, not estimated effort. The canonical meanings live
in `docs/process/behavioral-policy.md` and `docs/process/completion-packet.md`.

### Priority labels

Preferred GitHub labels are:

```text
priority:P0
priority:P1
priority:P2
priority:P3
```

Automation creating or updating an unresolved defect issue MUST apply the matching label when that
label exists in the repository. If label provisioning is unavailable, the issue body still carries
`Priority: P0|P1|P2|P3`, and the inability to apply the label is reported explicitly. Priority must
never disappear merely because a repository lacks the label.

The labels are not severity aliases. Severity describes impact; priority determines remediation
ordering. They commonly map Critical→P0, High→P1, Medium→P2, Low→P3, but the priority may be promoted
when a lower-severity defect blocks critical delivery work.

### Form selection

1. Inspect the repository's issue forms (`config.yml` contacts plus the canonical forms inherited
   from `harkers/.github`).
2. Choose the form whose nature matches the finding: `bug-incident.yml` for defects,
   `security-finding.yml` for vulnerabilities and dependency/supply-chain risk,
   `investigation.yml` for an unresolved unknown, `architecture-decision.yml` for a decision,
   `review-finding.yml` for a falsifiable review claim.
3. File through that form with every relevant required field populated.
4. Include the canonical `Priority` even if the selected form does not yet expose a dedicated field.
5. A generic free-form issue is a defect in itself when a matching form exists.

If no canonical form matches the class of defect — for example a performance, CI/build-failure or
technical-debt finding with no dedicated form — use the closest valid form and raise a separate
issue against `harkers/.github` requesting the missing canonical form. Record that request as
`Related work` in the defect issue.

### Duplicate prevention

Before opening a new issue:

1. Search open **and** recently closed issues for the same root cause.
2. If already tracked, comment the new evidence on that issue and reference it.
3. If the finding materially expands scope or evidence, extend the existing issue rather than
   duplicating it.
4. Do not suppress a finding because a vaguely similar issue exists. Match on root cause and
   actionable scope.
5. A defect fully fixed and regression-verified in the current bounded work does not require a
   redundant open issue solely because it was discovered; retain it as `FOUND_AND_FIXED` or
   `VERIFIED_FIXED` in the completion packet.

### Issue quality contract

Agent-raised defect issues carry: title, classification, priority, defect state, observed behaviour,
expected behaviour, evidence, reproduction, impact, root cause (or explicitly `UNKNOWN`), recommended
resolution, acceptance criteria and related work. See `docs/process/behavioral-policy.md` for the full
contract.

Minimum structured metadata:

```text
Priority:       P0 / P1 / P2 / P3
Defect state:   OPEN / FIX_IN_PROGRESS / DEFERRED / BLOCKED
Priority label: priority:P0 / priority:P1 / priority:P2 / priority:P3, when available
```

### Reporting a finding

```text
Issue: / Priority: / State: / Evidence: / Impact: / Resolution: / GitHub issue: / Next action:
```

`GitHub issue:` is never omitted. A fixed-in-turn finding uses `FIXED_IN_TURN` and points to its
regression evidence. If an unresolved issue could not be raised, the field reads
`NOT RAISED — BLOCKING REASON: <reason>`.

## Rules

1. Do not implement broad epics directly.
2. Implementation tasks require a specification and plan before coding.
3. Acceptance criteria must be measurable.
4. Scope and non-goals must both be explicit.
5. Investigation findings distinguish fact, inference, hypothesis and experiment result.
6. Review/security findings are claims; they are not automatically true because a reviewer produced them.
7. Model evaluations record build/quant, runtime, hardware, prompt/harness provenance, tasks, metrics and evidence.
8. Automatically raised incidents should include as much deterministic debugging context as safely available.
9. Every material unresolved defect is raised/updated as an issue; terminal output, chat history, TODO comments and handover notes are not the durable record.
10. Every material defect receives exactly one `P0`–`P3` priority before turn completion.
11. Every agent-raised issue uses the appropriate issue form, with all relevant required fields populated.
12. Every agent-raised issue carries the issue quality contract, including `Root cause: UNKNOWN` when the cause is not yet established.
13. Every material finding reported to another agent carries `Priority:`, `State:` and `GitHub issue:` fields.
14. Duplicate root causes are updated in place, not re-filed.
15. Unresolved `P0` prevents `PR_READY` and `DONE` without exception.
16. Unresolved `P1` prevents `PR_READY` and `DONE` unless an explicit repository-authorised waiver is represented in evidence.
17. `P2` is tracked and normally scheduled before unrelated discretionary feature work; `P3` is backlog work by default.
18. A known blocking defect prevents `DONE`; the work is `BLOCKED`, `FAILED` or `REQUIRES_REMEDIATION` until it is remediated and re-verified.

## Naming

Recommended issue-title prefixes are supplied by the shared Issue Forms:

```text
[Epic]
[Feature]
[Task]
[Investigation]
[Spike]
[ADR]
[Bug]
[Model Eval]
[Review]
[Security]
```

Repository-specific subtype prefixes may be added after the standard prefix where useful, for example:

```text
[Foundation][Task] Configuration schema
[Architecture][Epic] Control plane
```
