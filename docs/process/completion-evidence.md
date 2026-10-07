<!-- Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away. -->

# Completion Evidence Standard

This standard defines the Verification Evidence Packet: the machine-readable record a build produces for every assurance control it was required to run, and the contract consumers rely on instead of a prose completion claim. The machine contract is `schemas/verification-evidence.schema.json`; this document defines its meaning and the obligations of producers and consumers.

## Why

Prose claims are not evidence. "Tests passed", "the scan was clean" and "the scanner was unavailable but the change looks safe" are all unverifiable after the fact: they record no command, no commit, no tool version, no findings and no artefacts. A reviewer or a task-state machine reading a completion report cannot distinguish a passing build from a hopeful one.

The packet exists so that the question "did this build actually satisfy its required controls?" is answered by a file, bound to a specific commit, produced by the tools that actually ran. It is the input to `PR_READY` / `DONE` decisions; it is not a summary of them, and it never replaces the evidence it points at.

## Packet location and retention

A producer MAY write the packet into the repository at `.repo-standards/evidence/<commit-sha>.json`. A committed packet is convenient for local inspection, but it is not authoritative: it can be stale, and a commit can accumulate many packets as controls are re-run.

The CI artefact is authoritative. The packet MUST be uploaded as a build artefact named for the commit it describes, together with every artefact its control blocks reference — in particular the SBOM. Retention for both is governed by the producing repository's policy; a packet that outlives its referenced artefacts is not usable evidence.

Because the packet names its artefacts by path and digest, a consumer can prove that the SBOM it reads is the same artefact the SBOM control produced, rather than a file of unknown provenance that happened to be lying next to it.

## Required top-level fields

| Field | Meaning |
| --- | --- |
| `schema_version` | Version of this packet contract. A consumer that does not understand the version MUST refuse the packet rather than guess. |
| `repository` | `owner/repo` the evidence belongs to. Evidence is not transferable between repositories. |
| `commit` | The commit the evidence describes. See *Binding evidence to a build*. |
| `generated_at` | When the packet was assembled. Ordering and staleness only; never a substitute for `commit`. |
| `profile` | The assurance profile the producer resolved for this repository. |
| `controls` | One entry per assurance control, keyed by control ID. See *Control result block*. |
| `tracked_findings` | Every finding that is being tracked as work, with its fingerprint and issue reference. |
| `state` | The overall outcome: `PASS`, `FAIL`, `BLOCKED_TOOLING` or `BLOCKED_FINDING_TRACKING`. |

`controls` is an object keyed by control ID (`RS-SEC-001`, `RS-BUILD-001`, …) so that a consumer can look up a control by its canonical identifier without parsing prose or inferring identity from position.

## Control result block

Each entry in `controls` carries:

| Field | Meaning |
| --- | --- |
| `control_id` | The canonical control ID this block reports. |
| `requirement` | `REQUIRED`, `OPTIONAL` or `NOT_APPLICABLE` for this profile. |
| `tool` / `tool_version` | The tool that produced the result and the version it ran. A result without a version cannot be reproduced or reasoned about when the tool later changes behaviour. |
| `command` | The command executed, where recording it is safe. |
| `started_at` / `duration_seconds` | When the control ran and for how long. |
| `status` | Exactly one of `PASS`, `WARN`, `FAIL`, `BLOCKED`, `NOT_APPLICABLE`. |
| `missing_control` / `missing_tool` | Present when `status` is `BLOCKED`: which control could not be satisfied and which tool was absent. |
| `findings_by_severity` | Finding counts per severity. |
| `findings` | The findings themselves, with fingerprints. |
| `artifacts` | Produced files with path and `sha256` digest, and where each is retained. |
| `exception` | An approved waiver covering this control, if one applies. |
| `evidence_links` | References to supporting evidence. |

A `NOT_APPLICABLE` block MUST carry a `notes` entry giving the reason, so that a control silently dropped by configuration is distinguishable from one that was never required.

## Tracked findings

A tracked finding carries a `fingerprint`, a `severity`, a `status` (`OPEN`, `REOPENED`, `RESOLVED`, `WAIVED` or `NOT_APPLICABLE`) and an `issue` reference in `owner/repo#number` form, plus `id`, `component` and `fixed_version` where the scanner reports them.

The fingerprint is `rsf1:<32 hex>` and deliberately excludes severity — severity is re-scorable, and a re-score must not change the finding's identity. See `standards/security-assurance.md` for the normative definition and the deduplication rules.

Every finding at a severity that blocks completion MUST have an `issue` reference. A blocking finding with no durable issue is not an unrecorded detail; it is the `BLOCKED_FINDING_TRACKING` condition, and it prevents `PR_READY` / `DONE`. Reporting a blocking finding in the packet without tracking it anywhere is how findings become forgotten log lines.

`tracked_findings` is the packet-level index of work this build depends on. It exists so that a consumer can answer "what is outstanding?" from the packet alone, without re-running any scanner.

## Binding evidence to a build

A packet is valid only for the `commit` it names. Evidence produced against one commit says nothing about any other commit, however similar the two are. A consumer MUST verify that `commit` equals the commit under review before treating the packet as evidence for it, and MUST reject a packet whose `commit` does not match rather than treating it as stale-but-usable.

`repository` binds the evidence the same way. The same packet shape from another repository is a different claim about a different codebase.

The optional `build` field, where a producer records it, identifies the CI run or build that produced the packet; it supports traceability to logs and artefacts but does not replace `commit` as the binding identity.

## Producer obligations

1. Each producer writes the block for the control it ran, and only for that control. A producer MUST NOT write a block for a control it did not run.
2. A producer whose tool is unavailable MUST write a block with `status: BLOCKED` and the `missing_control` and `missing_tool` fields set. It MUST NOT omit its block. Omission is indistinguishable from a control that was never required, which is exactly the ambiguity this standard exists to remove.
3. A producer MUST NOT translate `tool unavailable` into `PASS`, and MUST NOT omit a failing control's findings to raise the overall state.
4. `tool` and `tool_version` MUST be recorded. A result that cannot name the tool that produced it is not evidence.
5. Artefacts MUST be recorded with a `sha256` digest so a consumer can bind a referenced file to the packet that claims it.
6. Any approved exception MUST be recorded in the control's `exception` field, with its `id`, `justification`, `approved_by` and `expires`. Exceptions are never asserted in prose alone.
7. The producer sets `state` from the controls, and MUST NOT set `PASS` while any `REQUIRED` control is `FAIL` or `BLOCKED`, or while a blocking finding is untracked.

## Consumer obligations

A consumer — the task-state machine, the evidence verifier, a reviewer, or any agent deciding whether work may reach `PR_READY` or `DONE`:

1. MUST read the packet and MUST NOT accept a prose completion claim in its place.
2. MUST verify `commit` matches the commit under claim before relying on the packet.
3. MUST refuse a packet whose `schema_version` it does not understand.
4. MUST treat `BLOCKED_TOOLING` and `BLOCKED_FINDING_TRACKING` as blocking. These are fail-closed states, not warnings.
5. MAY rely on `tracked_findings` to enumerate outstanding work rather than re-deriving it, but MUST NOT infer that a finding is resolved because it is absent from one packet. Resolution is recorded, never inferred from silence.
6. Where the packet and the repository disagree — the packet claims a control passed and the control's artefacts are missing, or a control the profile requires has no block at all — the disagreement is the finding, and it blocks.

## Change log

| Version | Change | Date |
| --- | --- | --- |
| 1 | initial issue #2 implementation | 2026-10-04 |
