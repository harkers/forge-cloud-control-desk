# Forge Cloud Control Desk - Email Server Extension

**Base project:** `project-20260330044222184857`
**Extension record:** `project-20260331202030761850`
**Last updated:** 2026-03-31
**Phase:** Phase 4 (after Phase 3 proves governance model)
**Decisions:** GCCD-STR-001 — Decisions 3, 4, 5, 6

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
- VM provisioning
- evidence creation
- register updates
- operator visibility
- explicit change boundaries

GCCD already has a working GCP baseline and evidence pattern, including a recorded successful start action for `forge-test-vm`.

---

## 3. Runtime model

### Relay VM
Recommended target:
- name: `forge-mail-server`
- project: `301823798218`
- region: `europe-west2`
- zone: `europe-west2-b`
- OS: Debian 12
- size: `e2-small` to start

### Software on the relay VM
- Postfix only
- CA bundle and testing tools
- no Dovecot
- no local mailbox delivery
- no inbound MX role in baseline

---

## 4. Register extension

### Additional GCCD register tab: Mail Domains

| Column | Description |
|--------|-------------|
| domain | sending domain / subdomain |
| relay_vm | relay VM name |
| relay_provider | SendGrid |
| relay_port_primary | 587 |
| relay_port_fallbacks | `465,2525` |
| authenticated_domain_status | pending / verified / failed |
| dmarc_policy | none / quarantine / reject |
| event_webhook_status | disabled / enabled / verified |
| evidence_link | link to evidence |
| notes | free-form notes |

---

## 5. Evidence extension

### Core evidence
VM lifecycle events remain in GCCD VM evidence.

### Relay-specific evidence
Use a separate mail evidence path such as:

```text
/mail-evidence/
  orderededge/
    relay-config/
    sendgrid-auth/
    webhook/
    validation/
```

Example records:
- relay VM provisioned
- Postfix config applied
- SendGrid authenticated domain verified
- webhook signature validation tested
- Gmail/Outlook/Yahoo delivery test results

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

## 9. Phase plan inside GCCD

### Phase A - Provision relay workload
- create `forge-mail-server`
- write VM evidence
- update GCCD register

### Phase B - Apply relay baseline
- install Postfix
- apply relay-only config
- test SendGrid connectivity on 587
- keep fallback snippets for 465 / 2525

### Phase C - Authenticate sending domain
- create scoped API key
- publish SendGrid DNS records
- validate authenticated domain
- start DMARC at `p=none`

### Phase D - Add telemetry
- enable Signed Event Webhook
- validate signature handling
- link events/evidence back into GCCD

### Phase E - Onboard workloads
- choose submission model
- run end-to-end send tests
- update evidence and notes

---

## 10. Acceptance criteria

- [ ] relay VM provisioned through GCCD
- [ ] relay-only Postfix baseline applied
- [ ] SendGrid authenticated domain verified
- [ ] event telemetry path documented and validated
- [ ] at least one workload sends successfully
- [ ] evidence exists for provision, config, and validation

## 11. Retirement plan — required

**DECIDED (Decision 6): Retirement/shutdown path is mandatory.**

Before Phase 4A begins, the following must be documented:
- How to stop the relay workload gracefully
- How to migrate or preserve SendGrid API keys and DNS records
- How to remove the relay VM without breaking dependent systems
- How to revoke SendGrid authenticated domain
- How to update dependent apps to use SendGrid directly if needed

Without a retirement plan, the extension is not accepted.

This extension narrows the old mail-server concept into something GCCD can govern cleanly:
**a small outbound relay workload with strong evidence discipline**, not a sprawling self-hosted mail suite.
