<!-- Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away. -->

# Commit Standard

## Atomic commits

A commit should represent one coherent validated change. Prefer one commit per bounded task or repair unit rather than accumulating a large mixed delta.

## Before committing

Delivery Ops must inspect:

```bash
git status --short
git diff --check
git diff --stat
git diff
```

It must confirm:

- changed files belong to the active issue/task;
- targeted validation for the task passed;
- no credentials, `.env` material, private keys or unrelated generated artefacts are staged;
- the working tree does not contain unexplained modifications from another task.

## Commit messages

Use conventional-commit style where practical:

```text
feat: add task transition engine
fix: reject invalid state regression
test: add blocked-state coverage
docs: record evidence resolver decision
chore: sync repository standards
refactor: isolate event normalization
```

Issue references may be added to the commit body or PR rather than making the subject unreadable.

## Automation rule

A builder may propose a commit message, but Delivery Ops owns the mechanical commit step. A commit must not be created solely because the builder declares completion; required task validation must have evidence first.

## Pushing

After an atomic commit:

1. push the issue branch;
2. create the draft PR if none exists and this is the first verified implementation commit;
3. otherwise update the existing PR lifecycle/evidence record;
4. never force-push a shared review branch unless repository policy explicitly permits it and the consequences are understood.
