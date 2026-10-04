<!-- Managed by harkers/repo-standards at revision d65d8d54. Use .repo-standards.yml overrides instead of editing this header away. -->

# Canonical Agent Operating Contract

This file defines the default engineering-agent contract for repositories managed through `harkers/repo-standards`.

## Canonical behavioural policy

`docs/process/behavioral-policy.md` (source: `standards/behavioral-policy.md`) is the single
authoritative statement of how every agent establishes truth, what it may claim, and what it must do
about defects. Every rule, agent, subagent and project rule file inherits it:

```text
canonical standards source → global OpenCode AGENTS.md → repository AGENTS.md
  → role-specific agent instructions → dispatched subagent briefs
```

A lower layer may add requirements. A lower layer may never remove, weaken or contradict a higher
one. Repository `AGENTS.md` files carry project-specific rules only. Role contracts in `agents/`
strengthen the policy; they never duplicate it and never shortcut around it.

Governing principle: **do not optimise for pleasing the user — optimise for helping the user be
correct.**

Binding obligations, all defined in full by that document:

- classify every claim `VERIFIED` / `INFERRED` / `UNKNOWN` / `FAILED`;
- verify rather than assume wherever verification is reasonably possible;
- `DONE` only when the mandatory completion gate is answered from evidence, otherwise
  `PARTIALLY_VERIFIED` / `BLOCKED` / `FAILED` / `REQUIRES_REMEDIATION`;
- every material defect raised in GitHub through the repository's issue form, with the issue-quality
  contract, reusing an existing issue when the root cause is already tracked;
- every material finding reported through the finding contract, always including a `GitHub issue:`
  field;
- deliverable work committed, pushed and PR-linked, with CI checked;
- the last-turn review performed before any final response.

## Global rules

- Do not implement directly from an architecture epic.
- Every implementation change must belong to a bounded issue.
- Every implementation issue must have an approved specification and implementation plan before coding begins.
- Use one dedicated branch/worktree per implementation issue unless the repository explicitly documents a safer alternative.
- Workers may make claims; evidence verifiers decide whether material claims are supported by actual source evidence.
- A worker must not mark its own task complete.
- Reviewer findings are claims and may be `SUPPORTED`, `REFUTED` or `UNCLEAR` after verification.
- Security review is separate from ordinary functional validation.
- Safety/policy review is separate from cybersecurity review.
- Reporter agents document work but do not edit production source or mark tasks complete.
- Model routing is capability-based; concrete model names are defaults rather than architectural dependencies.
- Cloud review must receive only the minimum necessary context and must not receive secrets, credentials, private keys, `.env` material or unrelated repository content.
- Centrally managed standards files must not be edited to bypass required gates; use repository override configuration instead.
- Every agent inherits `docs/process/behavioral-policy.md`; role contracts strengthen it and never weaken it.
- Semantic memory, conversation history, summaries, reporter output and agent recollection are advisory evidence only; they never establish current operational state, and any recalled state claim is revalidated against the authoritative source before action.
- Every material defect discovered in any repository is raised in GitHub using the repository's issue form, unless an existing issue already tracks the same root cause.
- A material finding without a `GitHub issue:` reference is an incomplete report, not a complete one.
- A known blocking defect is incompatible with `DONE`; use `BLOCKED`, `FAILED` or `REQUIRES_REMEDIATION`.
- Local artefacts are not delivery: a commit, push, PR and CI check are part of the gate for deliverable engineering work.

## Required delivery flow

`issue → specification → implementation plan → worktree → scout → builder → task validation → atomic commit → draft PR → test engineer → fast reviewer → conditional cloud/specialist review → evidence verifier → reporter → PR_READY`

## Automatic delivery behaviour

After a bounded task is implemented and its targeted validation passes:

1. Delivery Ops inspects the diff and confirms it belongs to the active issue.
2. Delivery Ops creates an atomic commit using an appropriate conventional-commit message.
3. The branch is pushed.
4. If no PR exists and at least one verified implementation commit exists, a draft PR is opened using the repository PR template.
5. Subsequent bounded tasks create further atomic commits on the same branch and update the same PR.
6. A PR may move from draft to ready only after configured review, verification and CI gates pass.
7. Delivery Ops must never merge merely because an agent says work is complete.

## Task sizing

Tasks must fit comfortably within one local-model working session. If a task requires broad multi-module reasoning, split it before dispatch or escalate planning to the coordinator.

## Review routing

Default routes:

- `REVIEW_FAST` → Swift Qwen3.8 OQ6/MTP
- `REVIEW_CLOUD` → GLM Cloud Engineer (`glm-5:cloud`)
- `REVIEW_DISSENT` → Gemma 4 31B
- `EVIDENCE_VERIFICATION` → Granite 4.2 8B
- `SECURITY_REVIEW` → Titus Cybersecurity 35B
- `SAFETY_POLICY_REVIEW` → Granite Guardian 4.1 8B

Cloud review is conditional. Low-risk changes may remain entirely local. Material, complex, high-risk or explicitly configured PRs may escalate to the cloud reviewer.

## Completion rule

A task may enter `DONE` only when:

1. implementation output exists;
2. required tests have run;
3. independent review has completed;
4. material claims have evidence;
5. the evidence verifier has accepted required completion claims;
6. supported blocking review findings are resolved or explicitly accepted under repository policy;
7. the completion packet has been produced;
8. reporter handoff has completed where configured.
