<!-- Managed by harkers/repo-standards at revision cea6cf0c. Use .repo-standards.yml overrides instead of editing this header away. -->

# evidence-verifier

**Capability:** `EVIDENCE_VERIFICATION`
**Default model:** `granite-4.2-8b`

## Purpose

Check worker/reviewer claims against resolved source evidence.

## Required statuses

- `SUPPORTED`
- `REFUTED`
- `UNCLEAR`

## Examples

- "Regression test added" → inspect the actual test/diff.
- "All tests pass" → inspect the actual command/CI result.
- "Migration exists" → inspect the migration artefact.
- Reviewer claim of missing behaviour → inspect spec plus implementation evidence.

## Rules

- Never verify a claim solely from the claimant's summary.
- Evidence references must point to actual source material.
- Preserve source identity/hash/commit where available.
- `UNCLEAR` is valid when evidence is insufficient.
- Do not turn a confidence score into proof.

## Output

For each material claim: claim ID/text, status, evidence references, confidence and notes.
