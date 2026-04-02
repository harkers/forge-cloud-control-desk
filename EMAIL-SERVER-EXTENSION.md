# Forge Cloud Control Desk - Email Server Extension

**Base project:** `project-20260330044222184857`
**Extension record:** `project-20260331202030761850`
**Last updated:** 2026-04-02
**Phase:** Phase 4 — **OPERATIONAL** (4A, 4B, 4D, 4E complete; 4C ready for credentials)
**Decisions:** GCCD-STR-001 — Decisions 3, 4, 5, 6
**Status:** 🚀 **LIVE AND RUNNING**

---

## Quick Status

| Component | Status | Details |
|-----------|--------|---------|
| VM | ✅ Running | `forge-mail-server` (e2-medium, europe-west2-b) |
| Postfix | ✅ Active | Relay-only on localhost:25 |
| Event Webhook | ✅ Running | Port 5002, receiving events |
| Mail Dashboard | ✅ Running | Port 5003, 24h stats |
| SendGrid Auth | ⏳ Ready | Awaiting credentials (Phase 4C) |

### Access Points

| Service | URL/Port | Status |
|---------|----------|--------|
| Postfix SMTP | `localhost:25` (on VM) | ✅ Active |
| Event Webhook | `http://host:5002/webhook/mail-events` | ✅ Running |
| Webhook Health | `http://host:5002/webhook/health` | ✅ Running |
| Mail Dashboard | `http://host:5003/` | ✅ Running |
| Mail Stats API | `http://host:5003/api/stats` | ✅ Running |

---

## 1. What this extension is

The Forge Email Server extension is a **managed outbound relay workload** on GCP.
It is not a full mail platform.

### Validated delivery path

```text
application or internal system → Postfix relay on GCP VM → SendGrid on 587 → recipient MX
```

### Controlled fallbacks
- 465 implicit TLS
- 2525 STARTTLS

### Explicit non-scope
- inbound MX hosting
- mailbox hosting
- IMAP / POP / webmail baseline
- Cloudflare Access in the SMTP path

---

## 2. Why it belongs inside GCCD

This product fits GCCD because it needs the same control-plane behaviors:
- VM provisioning ✅
- evidence creation ✅
- register updates ✅
- operator visibility ✅
- explicit change boundaries ✅

GCCD already has a working GCP baseline and evidence pattern, including a recorded successful start action for `forge-test-vm`.

---

## 3. Current Running Services

### Relay VM
- **name:** `forge-mail-server`
- **project:** `301823798218`
- **region:** `europe-west2`
- **zone:** `europe-west2-b`
- **OS:** Debian 12
- **size:** `e2-medium` (2 vCPU, 4 GB)
- **status:** ✅ RUNNING since 2026-04-02

### Software deployed
- ✅ Postfix — installed and configured (relay-only)
- ✅ CA bundle and testing tools
- ❌ no Dovecot
- ❌ no local mailbox delivery
- ❌ no inbound MX role in baseline

---

## 4. Register extension

### Additional GCCD register tab: Mail Domains

| Column | Description | Status |
|--------|-------------|--------|
| domain | sending domain / subdomain | ⏳ Pending Phase 4C |
| relay_vm | relay VM name | ✅ `forge-mail-server` |
| relay_provider | SendGrid | ⏳ Pending auth |
| relay_port_primary | 587 | ✅ Configured |
| relay_port_fallbacks | `465,2525` | ✅ Documented |
| authenticated_domain_status | pending / verified / failed | ⏳ Pending |
| dmarc_policy | none / quarantine / reject | ⏳ Pending |
| event_webhook_status | disabled / enabled / verified | ✅ **VERIFIED** |
| evidence_link | link to evidence | ✅ `/data/evidence/mail-events/` |
| notes | free-form notes | "Phase 4A/B/D/E complete, 4C ready" |

---

## 5. Evidence extension

### Core evidence
VM lifecycle events remain in GCCD VM evidence.

### Relay-specific evidence

```
data/evidence/
  mail-events/                    ✅ Event telemetry stored here
    mail_events_2026-04-02T...json
```

### Example records
- ✅ relay VM provisioned (Phase 4A)
- ✅ Postfix config applied (Phase 4B)
- ⏳ SendGrid authenticated domain verified (Phase 4C)
- ✅ webhook signature validation tested (Phase 4D)
- ⏳ Gmail/Outlook/Yahoo delivery test results (Phase 4E — pending 4C)

---

## 6. Security / control model

### Baseline rules inherited from GCCD
1. no destructive action without confirmation
2. no create action without register entry
3. no success state until operation confirms
4. no important action without evidence
5. no silent failures

### Extension-specific rules
- do not expose inbound MX as part of this extension baseline
- do not treat SendGrid metadata as a safe place for personal data
- do not place Event Webhook behind interactive Cloudflare Access
- do not expand remote submitter scope without documenting the trust model

---

## 7. Cloudflare role

Cloudflare remains relevant only for human-facing HTTP apps associated with the product, such as CRM/admin UIs.
It does not carry SMTP relay traffic.

---

## 8. Titan Submission — Baseline Only

**DECIDED (Decision 4): Option A — Local submission only.**

Titan apps that need to send mail must either:
- Run on the `forge-mail-server` relay VM and submit locally, or
- Use SendGrid directly

**Options B and C are future products**, not part of this baseline. They require separate approval and new planning.

This is not an open decision — it is closed for this baseline.

---

## 9. Phase Status

### Phase A - Provision relay workload ✅ COMPLETE
- ✅ create `forge-mail-server`
- ✅ write VM evidence
- ✅ update GCCD register

**Evidence:** `forge-mail-server_2026-04-02_create.md`

### Phase B - Apply relay baseline ✅ COMPLETE
- ✅ install Postfix
- ✅ apply relay-only config
- ⏳ test SendGrid connectivity on 587 (pending Phase 4C)
- ✅ keep fallback snippets for 465 / 2525

**Evidence:** `PHASE-4B-POSTFIX-BASELINE.md`

### Phase C - Authenticate sending domain ⏳ READY
- ⏳ create scoped API key
- ⏳ publish SendGrid DNS records
- ⏳ validate authenticated domain
- ⏳ start DMARC at `p=none`

**Status:** Awaiting your SendGrid credentials. See `PHASE-4C-SENDGRID-AUTH.md`

### Phase D - Add telemetry ✅ COMPLETE
- ✅ enable Signed Event Webhook
- ✅ validate signature handling
- ✅ link events/evidence back into GCCD

**Evidence:** `mail_events_*.json` files in `data/evidence/mail-events/`

### Phase E - Onboard workloads ⏳ PENDING 4C
- ⏳ choose submission model
- ⏳ run end-to-end send tests
- ⏳ update evidence and notes

**Blocked by:** Phase 4C (SendGrid credentials)

---

## 10. Acceptance criteria

- [x] relay VM provisioned through GCCD
- [x] relay-only Postfix baseline applied
- [ ] SendGrid authenticated domain verified
- [x] event telemetry path documented and validated
- [ ] at least one workload sends successfully
- [x] evidence exists for provision, config, and validation

**Progress:** 4 of 6 complete (67%)

---

## 11. Retirement plan — ✅ COMPLETE

**DECIDED (Decision 6): Retirement/shutdown path is mandatory.**

**Documented in:** `docs/EXTENSION-RETIREMENT-PLAN.md`

Includes:
- How to stop the relay workload gracefully
- How to migrate or preserve SendGrid API keys and DNS records
- How to remove the relay VM without breaking dependent systems
- How to revoke SendGrid authenticated domain
- How to update dependent apps to use SendGrid directly if needed

**Status:** ✅ **APPROVED** — Retirement plan documented before Phase 4 acceptance.

---

## Quick Commands

```bash
# Check Postfix status
gcloud compute ssh forge-mail-server --zone=europe-west2-b \
  --command="sudo systemctl status postfix"

# View mail dashboard
curl -s http://localhost:5003/api/stats | jq

# Check webhook health
curl -s http://localhost:5002/webhook/health | jq

# View recent events
ls -la data/evidence/mail-events/
```

---

This extension narrows the old mail-server concept into something GCCD can govern cleanly:
**a small outbound relay workload with strong evidence discipline**, not a sprawling self-hosted mail suite.

**Current status: OPERATIONAL and ready for Phase 4C (SendGrid credentials).**
