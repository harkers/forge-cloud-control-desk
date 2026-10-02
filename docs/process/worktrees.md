<!-- Managed by harkers/repo-standards at revision cea6cf0c. Use .repo-standards.yml overrides instead of editing this header away. -->

# Branch and Worktree Standard

Implementation work should be isolated from the live/default checkout.

## Naming

For issue `123` with slug `package-scaffold`:

```text
branch:   feature/123-package-scaffold
worktree: ../<repo>-wt/issue-123-package-scaffold
```

Use a branch prefix that reflects the work type when useful:

```text
feature/<issue>-<slug>
fix/<issue>-<slug>
chore/<issue>-<slug>
docs/<issue>-<slug>
spike/<issue>-<slug>
```

## Creation

From the canonical local checkout:

```bash
git fetch origin
git worktree add ../<repo>-wt/issue-123-package-scaffold feature/123-package-scaffold
cd ../<repo>-wt/issue-123-package-scaffold
```

If the branch does not yet exist locally but exists remotely:

```bash
git fetch origin feature/123-package-scaffold
git worktree add --track -b feature/123-package-scaffold \
  ../<repo>-wt/issue-123-package-scaffold \
  origin/feature/123-package-scaffold
```

## Pre-edit verification

Every worker must confirm:

```bash
git branch --show-current
git status --short
pwd
```

Before changing files, verify:

- branch corresponds to the active issue;
- worktree path corresponds to the active issue;
- there are no unexplained modifications;
- the specification and plan being followed belong to the same issue.

## Isolation rules

- Do not use the live/default checkout for issue implementation.
- Do not let one worktree serve multiple unrelated implementation issues.
- Do not mix review fixes from another PR into the active worktree.
- Do not delete a worktree until its branch/PR state is understood and any unpushed work is recovered.

## Cleanup

After merge/closure and after confirming no unique work remains:

```bash
git worktree remove ../<repo>-wt/issue-123-package-scaffold
git worktree prune
```

Branch deletion follows repository policy and must not occur while a needed PR, recovery path or evidence reference depends on it.
