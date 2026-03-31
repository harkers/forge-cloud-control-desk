# GCCD Strategic Decision Record

**Record:** GCCD-STR-001  
**Date:** 2026-03-31  
**Status:** DECISIONS REQUIRED  
**Author:** Claw (Challenger Review + Human Approval)  
**Applies to:** `projects/forge-cloud-control-desk/`

---

## Context

The GCCD challenger review (2026-03-31) identified five systemic risks in the current plans:

1. Solo/Extension operator model is undefined
2. Gmail OAuth contradiction in Phase 1 deliverables
3. Email extension documented before core notification is proven
4. Titan submission model left as three unspoken products
5. Extension acceptance criteria only covers existence, not lifecycle

This document forces **explicit yes/no decisions** on each. No decision means no progress.

---

## Decision 1 — GCCD Identity: Product or Platform?

**Current state:** Plans describe both without choosing.

**Options:**

| Choice | Implication |
|--------|-------------|
| **Product** (solo desk) | Extensions must be operable by one person. Any multi-operator extension is a new product. |
| **Platform** | GCCD becomes a governance layer others build on. Requires ownership model, API versioning, SLA. |

**Decision required by:** Before any Phase 3 work  
**Owner:** Human

---

## Decision 2 — Gmail: Aspirational or Baseline?

**Current state:** ROADMAP Phase 1 says "Gmail approval loop" but PROJECT-SPEC says OAuth delegation is required and unavailable.

**Options:**

| Choice | Implication |
|--------|-------------|
| **Local notification is the baseline** | Remove Gmail from Phase 1. Document GCCD as local-first. Gmail becomes Phase N+1 when OAuth is solved. |
| **Gmail is required for Phase 1** | Block until OAuth delegation is validated. Do not ship Phase 2 until Gmail works or a documented替代方案 exists. |

**Decision required by:** Before Phase 1 is marked complete  
**Owner:** Human

---

## Decision 3 — Email Extension Phase Position

**Current state:** EMAIL-SERVER-EXTENSION is Phase 3, before Service Health (Phase 4).

**Options:**

| Choice | Implication |
|--------|-------------|
| **Move email extension to Phase 4** | Phase 3 becomes "Service Health + governance hardening." Email only after core cross-product governance is proven. |
| **Keep email as Phase 3** | Accept that extension is speculative. Mark all email extension deliverables as TBD until Phase 2 proves the model. |

**Decision required by:** Before starting any Phase 3 work  
**Owner:** Human

---

## Decision 4 — Titan Submission Model: Choose One Baseline

**Current state:** Three options presented, none decided.

**Options:**

| Choice | Description | Implication |
|--------|-------------|-------------|
| **Option A — Local submission only** | Workloads on `forge-mail-server` submit mail locally. No remote submitters. Cleanest boundary. | Simplest security model. Titan apps must either run on the relay VM or use SendGrid directly. |
| **Option B — Private network submission** | Titan apps submit over a VPN-restricted path to the relay VM. | New firewall rules, new trust boundary, new failure modes. Requires explicit network design. |
| **Option C — Direct SendGrid** | Titan apps bypass the relay VM and send directly to SendGrid. | Relay VM becomes unnecessary for Titan workloads. Questions why `forge-mail-server` exists. |

**Required action:** Pick ONE as the documented baseline. The other two become **separate future products** requiring new approval and new planning.

**Decision required by:** Before Phase A of email extension  
**Owner:** Human

---

## Decision 5 — Extension Operator: Solo or Shared?

**Current state:** SOLO-OPS-BRIEF says "one operator." EMAIL-SERVER-EXTENSION implies the relay could serve multiple workloads from multiple sources.

**Options:**

| Choice | Implication |
|--------|-------------|
| **Solo only** | Extensions are personal tools. If you can't operate them solo, they need a separate ownership model. |
| **Shared/team** | Redefine GCCD governance to include team roles, handover procedures, and on-call ownership. |

**Decision required by:** Before accepting any extension beyond VM lifecycle  
**Owner:** Human

---

## Decision 6 — Extension Retirement: Documented or Not?

**Current state:** No retirement process documented for any extension.

**Options:**

| Choice | Implication |
|--------|-------------|
| **Retirement required before acceptance** | No extension accepted into GCCD without a documented shutdown path: how to stop the workload, migrate data, and remove the VM without breaking dependent systems. |
| **Retirement is future work** | Accept extensions without shutdown plans. Risk: accumulated technical debt with no exit path. |

**Decision required by:** Before Phase A of any extension  
**Owner:** Human

---

## Decision Summary

| # | Decision | Options | Deadline |
|---|----------|---------|----------|
| 1 | GCCD identity | Product vs Platform | Before Phase 3 |
| 2 | Gmail baseline | Local-first vs Gmail-required | Before Phase 1 close |
| 3 | Email extension phase | Phase 3 vs Phase 4 | Before Phase 3 start |
| 4 | Titan submission | Option A vs B vs C | Before Phase A |
| 5 | Extension operator | Solo vs Shared | Before Phase 3 |
| 6 | Extension retirement | Required vs Future | Before Phase A |

---

## What Happens If Decisions Are Not Made

| If not decided | Consequence |
|---------------|------------|
| Decision 1 | GCCD shipped as accidental platform with solo operator burning out |
| Decision 2 | Phase 1 claimed complete with broken Gmail, creating false confidence |
| Decision 3 | Email extension built on untested governance model |
| Decision 4 | Three different products shipped as one, with unclear security boundaries |
| Decision 5 | Extension fails when the solo operator is unavailable |
| Decision 6 | Extensions accumulate with no exit, creating lock-in |

---

## Required Output

Human must review this document and provide:
- A decision on each of the six items above
- Updated planning documents reflecting those decisions

Until decisions are recorded, **no Phase 3 work is authorized**.

---

*Generated by Claw challenger review, 2026-03-31. Requires human sign-off.*
