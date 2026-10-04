<!-- Managed by harkers/repo-standards at revision 5371ef03. Use .repo-standards.yml overrides instead of editing this header away. -->

# Issue Standard

Structured issues are the entry point for engineering work.

## Issue types

- **Epic** — large capability; never a direct implementation instruction.
- **Feature Request** — desired capability/outcome; may require decomposition.
- **Implementation Task** — bounded unit of work with spec, plan, branch/worktree and measurable acceptance criteria.
- **Investigation** — evidence-first analysis before a decision or implementation.
- **Spike / Research** — time-bounded experiment ending in an explicit decision gate.
- **Architecture Decision / ADR** — significant decision, alternatives, evidence, consequences and revisit trigger.
- **Bug / Incident** — defect/failure with reproduction, diagnostics, severity and evidence.
- **Model Evaluation** — reproducible capability/routing experiment.
- **Review Finding** — falsifiable independent-review claim with verification state.
- **Security Finding** — structured security/trust-boundary claim with evidence and mitigation.

## Mandatory defect tracking

Agents discover defects while doing other work. `docs/process/behavioral-policy.md` makes raising a
GitHub issue for each **material** defect mandatory, and this document defines how.

### Form selection

1. Inspect the repository's issue forms (`config.yml` contacts plus the canonical forms inherited
   from `harkers/.github`).
2. Choose the form whose nature matches the finding: `bug-incident.yml` for defects,
   `security-finding.yml` for vulnerabilities and dependency/supply-chain risk,
   `investigation.yml` for an unresolved unknown, `architecture-decision.yml` for a decision,
   `review-finding.yml` for a falsifiable review claim.
3. File through that form with every relevant required field populated.
4. A generic free-form issue is a defect in itself when a matching form exists.

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

### Issue quality contract

Agent-raised issues carry: title, classification, observed behaviour, expected behaviour, evidence,
reproduction, impact, root cause (or explicitly `UNKNOWN`), recommended resolution, acceptance
criteria and related work. See `docs/process/behavioral-policy.md` for the full contract.

### Reporting a finding

```text
Issue: / Evidence: / Impact: / Resolution: / GitHub issue: / Next action:
```

`GitHub issue:` is never omitted. If an issue could not be raised, the field reads
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
9. Every material defect is raised as an issue; terminal output, chat history, TODO comments and handover notes are not the record.
10. Every agent-raised issue uses the appropriate issue form, with all relevant required fields populated.
11. Every agent-raised issue carries the issue quality contract, including `Root cause: UNKNOWN` when the cause is not yet established.
12. Every material finding reported to another agent carries a `GitHub issue:` field.
13. Duplicate root causes are updated in place, not re-filed.
14. A known blocking defect prevents `DONE`; the work is `BLOCKED`, `FAILED` or `REQUIRES_REMEDIATION` until it is remediated and re-verified.

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
