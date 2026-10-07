<!-- Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away. -->

# Canonical Planning Decomposition

This document defines how broad implementation work is decomposed into bounded, executable plans.
It operationalises the Decision contract in `docs/process/behavioral-policy.md`; it does not replace
or duplicate that policy. Routine decomposition is an engineering decision, not a user-choice point.

## Objective

Plans must remain executable, verifiable, reviewable and independently deliverable. An agent must
split work before plan quality degrades, rather than truncating detail or asking the user to approve
an obvious decomposition.

Plan length, repository precedent and token budget are **signals**, never success criteria. There is
no canonical maximum line count. An agent must not omit known work, use placeholders, weaken tests,
or compress acceptance criteria merely to keep a plan below an arbitrary size.

## When decomposition is required

An implementation plan MUST be decomposed when one or more of these conditions materially affect
quality or delivery:

- the active issue contains multiple independently executable outcomes;
- distinct priority classes (`P0`, `P1`, `P2`) can be delivered separately;
- a dependency boundary means one unit can complete and unblock another;
- materially different architectural subsystems can be changed and validated independently;
- validation, review or rollback requirements differ substantially between parts;
- one part can be merged safely without waiting for the remainder;
- the plan is becoming too large for reliable review, execution or handoff;
- keeping the work together would create an unreviewable PR or exceed a bounded worker session.

A single plan remains correct when splitting would create artificial coupling, unsafe intermediate
states, duplicated migrations, or children that cannot be delivered independently.

## Boundary selection

Dependency validity is a hard guard. A split is invalid if it schedules a child before work that the
child requires, or leaves the repository in an unsupported intermediate state.

Among dependency-valid splits, prefer boundaries in this order:

1. **Priority boundary** — `P0` / `P1` / `P2`, where the priorities can actually ship separately.
2. **Independently deliverable capability/outcome** — one observable capability per child.
3. **Architectural subsystem** — separate components with distinct change and validation surfaces.
4. **PR-sized implementation unit** — the smallest coherent unit that preserves behaviour and
   review quality.

Do not split by equal line counts, token counts, arbitrary file counts, or `part1` / `part2` solely
for cosmetic balance.

## Executable child-plan contract

Every executable child plan MUST contain:

- objective and observable outcome;
- in-scope and non-goal boundaries;
- owning bounded implementation issue / WorkItem;
- dependencies and prerequisite state;
- likely files/components/change surface;
- ordered implementation tasks;
- validation and regression checks;
- measurable acceptance criteria;
- evidence required to support completion claims;
- rollback or failure handling where material;
- intended delivery unit (branch/worktree and PR relationship).

Completing an executable child MUST leave the repository in a valid and supportable state. A child
that cannot meet this condition is not independently deliverable and must be recombined or have its
dependency structure corrected.

A document MAY be split purely for readability. Such a shard MUST be marked `executable: false` and
`deliverable: false`; it is documentation, not a schedulable WorkItem, branch or PR.

## Issue, worktree and PR mapping

A broad feature/epic remains a planning container. Execution occurs through bounded implementation
issues/WorkItems.

Default mapping:

```text
feature/specification
  -> plan-set index
     -> executable child plan
        -> bounded implementation issue / WorkItem
           -> dedicated branch/worktree
              -> draft PR after the first verified implementation commit
```

Each executable child MUST map to one bounded implementation issue. Existing canonical worktree,
commit and PR rules remain authoritative; this document does not create an exception to them.

Dependent children may be planned in advance, but only dependency-ready children are dispatched.
Later children do not block delivery of an earlier independently complete child unless the
specification explicitly requires atomic release.

## Naming

For a single plan, retain the repository's normal feature-oriented filename.

For a decomposed plan set, use a stable root index plus semantic child names. Preferred examples:

```text
docs/plans/2026-10-04-benchmark-runtime-observability.md
docs/plans/2026-10-04-benchmark-runtime-observability-p0.md
docs/plans/2026-10-04-benchmark-runtime-observability-p1.md
docs/plans/2026-10-04-benchmark-runtime-observability-p2.md
```

If more than one executable child exists at the same priority, add a short semantic suffix rather
than an arbitrary continuation number:

```text
...-p0-runtime.md
...-p0-runners.md
```

Avoid `part1`, `part2`, `continued`, or similar names when a meaningful capability name exists.

## Plan-set index and machine-readable graph

When a plan is decomposed, the root plan becomes a short plan-set index. It records the reason for
decomposition, the execution order and one `planning-decomposition/v1` YAML graph. Child plans hold
the implementation detail.

Canonical shape:

```yaml
schema_version: planning-decomposition/v1
feature: benchmark-runtime-observability
reason: "Multiple dependency-safe priority and delivery boundaries"
plans:
  - id: p0-core
    path: docs/plans/2026-10-04-benchmark-runtime-observability-p0.md
    priority: P0
    depends_on: []
    executable: true
    deliverable: true
    ready_when: []
  - id: p1-reporting
    path: docs/plans/2026-10-04-benchmark-runtime-observability-p1.md
    priority: P1
    depends_on: [p0-core]
    executable: true
    deliverable: true
    ready_when:
      - p0-core delivered
  - id: p2-trends
    path: docs/plans/2026-10-04-benchmark-runtime-observability-p2.md
    priority: P2
    depends_on: [p1-reporting]
    executable: true
    deliverable: true
    ready_when:
      - p1-reporting delivered
```

The graph is a deterministic projection for orchestration. Markdown remains authoritative for the
implementation detail. Agents MUST NOT infer a missing dependency merely to make the graph acyclic;
they must resolve the plan or report the dependency as `UNKNOWN`/blocked under the behavioural
policy.

## Autonomous forward-progress rule

When decomposition is clearly warranted, the planning agent SHALL:

1. identify the trigger and dependency constraints;
2. select the strongest valid boundary;
3. create/update the plan-set index and executable child plans;
4. record the dependency graph;
5. map executable children to bounded issues/WorkItems where execution is intended;
6. select the highest-priority dependency-ready child;
7. continue the normal delivery flow.

The agent MUST NOT ask the user whether to split a plan when the split is a routine, reversible
engineering decision inside approved scope.

Example of correct disposition:

```text
Decision: decomposed into dependency-safe P0, P1 and P2 execution units.
Next action: activate P0; P1 and P2 remain dependency-blocked child work.
```

Incorrect:

```text
This plan is getting large. Would you like me to split it into two plans?
```

## Human escalation

Human input is required only when the Decision contract in `docs/process/behavioral-policy.md`
requires it — for example because decomposition would materially change product/business direction,
requested scope/outcome, an irreversible architecture or security boundary, significant cost,
external production impact, legal/policy posture, credentials/authority, or genuine personal
preference.

Plan size, file naming, phase boundaries, dependency recording, routine PR partitioning and selection
of the next dependency-ready child are not by themselves escalation reasons.

## No-placeholder and fidelity rule

Decomposition preserves planning quality. An agent MUST NOT use the split to hide incomplete
planning. Known implementation work may not be replaced with:

- `TODO` placeholders for requirements that can already be specified;
- "implement similarly" in place of concrete change steps;
- omitted validation or rollback detail solely to reduce size;
- deferred acceptance criteria that can already be made measurable;
- unexplained ellipses or truncation.

If information is genuinely unavailable, classify it `UNKNOWN`, identify how it will be resolved,
and block only the child whose safe execution depends on it.

## `PLAN_READY` relationship

A bounded implementation WorkItem may enter `PLAN_READY` only when its executable child plan
satisfies this contract. The broad parent planning container is not dispatched as an implementation
unit merely because a plan-set index exists.

For decomposed work, `PLAN_READY` therefore means the active child is bounded, dependency-valid,
fully planned and independently verifiable. Dependent children may remain planned-but-not-ready
until their `ready_when` conditions are satisfied.

## Review checklist

Before declaring a decomposed plan set ready, self-review:

1. Does every executable child have an observable outcome?
2. Are dependency edges explicit and directionally correct?
3. Can each deliverable child merge without leaving an unsupported repository state?
4. Did priority labels influence sequencing without overriding dependencies?
5. Are documentation-only shards marked non-executable?
6. Are validation, evidence and acceptance criteria concrete for every child?
7. Is the plan-set graph consistent with the Markdown child plans?
8. Am I asking the user to decide anything the behavioural Decision contract delegates to me?
9. Is there exactly one highest-priority dependency-ready next execution unit?
10. Did I preserve full planning fidelity rather than optimising for document size?

If the answer to 8 is yes, decide and proceed unless a defined human-escalation condition applies.
