<!-- Managed by harkers/repo-standards at revision cea6cf0c. Use .repo-standards.yml overrides instead of editing this header away. -->

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

## Rules

1. Do not implement broad epics directly.
2. Implementation tasks require a specification and plan before coding.
3. Acceptance criteria must be measurable.
4. Scope and non-goals must both be explicit.
5. Investigation findings distinguish fact, inference, hypothesis and experiment result.
6. Review/security findings are claims; they are not automatically true because a reviewer produced them.
7. Model evaluations record build/quant, runtime, hardware, prompt/harness provenance, tasks, metrics and evidence.
8. Automatically raised incidents should include as much deterministic debugging context as safely available.

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
