# GCCD Strategic Decision Record

**Record:** GCCD-STR-001  
**Date:** 2026-03-31  
**Status:** DECIDED  
**Author:** Claw (Challenger Review + Human Approval)  
**Human:** Approved all six decisions, 2026-03-31 22:27  
**Applies to:** `projects/forge-cloud-control-desk/`

---

## Decision 1 — GCCD Identity: Product or Platform?

**DECIDED: Platform**

GCCD is a governance platform that others can extend. Extensions are welcome but require an ownership model, handover procedures, and per-extension runbook ownership. API/evidence/register contracts are intentional and stable.

---

## Decision 2 — Gmail: Aspirational or Baseline?

**DECIDED: Local notification is the baseline**

GCCD ships with local notification files as the default notification mechanism. Gmail becomes a Phase N+1 upgrade to be revisited when OAuth delegation is solved or an alternative email provider is adopted. Phase 1 deliverables do not depend on Gmail.

---

## Decision 3 — Email Extension Phase Position

**DECIDED: Email extension moves to Phase 4**

EMAIL-SERVER-EXTENSION is repositioned to Phase 4. Phase 3 becomes "Service Health + governance hardening." Email extension only begins after core cross-product governance is proven. All email extension deliverables in Phases A–E are marked TBD until Phase 4 gates open.

---

## Decision 4 — Titan Submission Model: Choose One Baseline

**DECIDED: Option A — Local submission only**

Baseline: Workloads run on the `forge-mail-server` relay VM and submit mail locally. No remote submitters accepted in the baseline security boundary.

Titan apps that need to send mail must either:
- Run on the relay VM and submit locally, or
- Use SendGrid directly

Option B (private network submission) and Option C (direct SendGrid) are documented as **future products** requiring new approval and new planning. They are not in scope for the current email extension baseline.

---

## Decision 5 — Extension Operator: Solo or Shared?

**DECIDED: Shared/team**

Extensions are operated by a named team. Each extension requires:
- Named on-call owner
- Handover procedure documented
- Runbook ownership assigned
- On-call rotation or coverage model

Extensions are not accepted unless the team operating model is defined.

---

## Decision 6 — Extension Retirement: Documented or Not?

**DECIDED: Retirement required before acceptance**

No extension is accepted into GCCD without a documented shutdown path including:
- How to stop the workload gracefully
- How to migrate or preserve data
- How to remove the VM without breaking dependent systems
- How to revoke access credentials associated with the extension

Extensions without a retirement plan are not approved.

---

## Decision Summary

| # | Decision | Choice | Status |
|---|----------|---------|--------|
| 1 | GCCD identity | Platform | ✅ DECIDED |
| 2 | Gmail baseline | Local notification | ✅ DECIDED |
| 3 | Email extension phase | Phase 4 | ✅ DECIDED |
| 4 | Titan submission | Option A (local only) | ✅ DECIDED |
| 5 | Extension operator | Shared/team | ✅ DECIDED |
| 6 | Extension retirement | Required before acceptance | ✅ DECIDED |

---

## Cascade Actions Required

The following documents must be updated to reflect these decisions:

| Document | Change required |
|----------|----------------|
| `ROADMAP.md` | Email extension → Phase 4. Gmail → Phase N+1. Add team ops note. |
| `PROJECT-SPEC.md` | Local notification as baseline. Team ops model. Retirement requirement. |
| `SOLO-OPS-BRIEF.md` | Rename from "Solo" to reflect team ops. Add extension gate criteria. |
| `EMAIL-SERVER-EXTENSION.md` | Phase A–E → Phase 4A–4E. Option B/C removed. Retirement plan required. |
| `PHASE-1-DESIGN.md` | Remove Gmail from Phase 1 scope. Local notification as baseline. |

---

*Human approved all six decisions, 2026-03-31 22:27. Document is closed for these six items. New decisions require a new record.*
