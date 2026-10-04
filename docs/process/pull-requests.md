<!-- Managed by harkers/repo-standards at revision d65d8d54. Use .repo-standards.yml overrides instead of editing this header away. -->

# Pull Request Standard

## Draft-first lifecycle

Create a draft PR after the first verified implementation commit when practical. Subsequent atomic commits should update the same PR so CI and review can run continuously.

```text
first verified commit
  → push branch
  → create draft PR from repository/default template
  → continue bounded tasks
  → atomic commit + push per validated task
  → independent testing
  → local review
  → conditional cloud/specialist review
  → evidence verification
  → completion packet
  → PR_READY
```

## Required PR content

A PR records:

- linked issue;
- specification and implementation plan;
- bounded change summary;
- commands/tests and results;
- risk tier;
- review findings and verification disposition;
- evidence references;
- cloud-review boundary where used;
- known risks/limitations;
- completion packet status;
- scope check.

## Readiness gate

A PR may become ready only when:

- configured CI checks pass;
- required independent testing completed;
- required review routes completed;
- material completion/reviewer claims passed evidence verification;
- supported blocking findings are resolved or accepted under explicit repository policy;
- specialist review is complete where triggered;
- completion packet exists;
- scope audit confirms no unrelated changes.

## Merge boundary

`PR_READY` is permission to request/perform final merge according to repository policy; it is not itself a merge instruction. Delivery agents must not infer merge permission solely from a passing review.

## Cloud review

Cloud review receives the minimum necessary evidence. Do not send whole repositories, secrets, credentials, `.env` data, private keys or unrelated source by default.
