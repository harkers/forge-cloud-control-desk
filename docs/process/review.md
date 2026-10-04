<!-- Managed by harkers/repo-standards at revision 5371ef03. Use .repo-standards.yml overrides instead of editing this header away. -->

# Review and Verification Standard

Review is deliberately separated into multiple capabilities.

## Stage 1 — Fast local engineering review

Default capability: `REVIEW_FAST`.

Checks:

- implementation vs issue/spec/plan;
- correctness and edge cases;
- architecture consistency;
- test sufficiency;
- unnecessary complexity;
- regression and scope-creep risk.

The reviewer should produce falsifiable findings with file/line/test/spec references where possible.

## Stage 2 — Cloud engineering review

Default capability: `REVIEW_CLOUD`.

Use for normal/material changes when enabled by repository policy, and for complex or high-risk engineering review. Supply only minimum required diff/context.

Cloud review is not permitted to receive secrets, credentials, `.env` material or unrelated source by default.

## Stage 3 — Specialist review

Trigger specialists based on changed surface and risk:

- `SECURITY_REVIEW` for authentication, authorisation, credentials, filesystem/path handling, command execution, network exposure, supply-chain trust, logging/data leakage or write-capable control planes;
- `SAFETY_POLICY_REVIEW` for agent/tool policy, unsafe execution boundaries, hallucination-risk controls or other safety/policy concerns;
- `REVIEW_DISSENT` / Jury for high-risk architecture, material disagreement or deliberate model-family diversity;
- `VISION_REVIEW` for UI/screenshot/visual-regression evidence where relevant.

## Findings are claims

A review finding should be structured as:

```yaml
finding_id: REV-001
severity: medium
category: correctness
claim: Configuration accepts unknown top-level keys.
evidence:
  - src/config.py:80-110
  - tests/test_config.py
recommendation: Add fail-closed validation and regression coverage.
verification: PENDING
```

Do not instruct a builder to change code merely because a reviewer produced a confident statement.

## Evidence verification

`EVIDENCE_VERIFICATION` resolves each material claim against actual source evidence and returns:

- `SUPPORTED`
- `REFUTED`
- `UNCLEAR`

A verifier must not verify a finding solely from the reviewer's summary of the evidence.

## Fix loop

```text
review finding
  → evidence verification
  → SUPPORTED blocking finding
  → bounded repair task
  → targeted validation
  → atomic commit + push
  → re-review relevant delta
  → re-verify material claims
```

Refuted findings require no repair. `UNCLEAR` findings require better evidence or explicit risk handling rather than guessed remediation.
