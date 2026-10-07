<!-- Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away. -->

# Branch and Worktree Standard

Mutating implementation work MUST be isolated from the live/default checkout in one dedicated, control-plane-assigned and verified worktree for the active bounded WorkItem/issue.

Read-only discovery, planning and review MAY run without a worktree when the control plane has verified and recorded the read-only scope of the task before dispatch. Recorded read-only scope satisfies this gate; runtime mechanical enforcement of read-only behaviour is deferred and is tracked as future work.

## Ownership invariant

For orchestrated work, the control plane owns worktree lifecycle. Agents consume the assigned worktree; they do not choose or create an alternative workspace.

One bounded implementation WorkItem/issue owns one dedicated worktree. Multiple agents may operate on that same issue worktree with role-appropriate permissions, but an unrelated WorkItem must receive a different worktree.

Before a mutating task may enter `READY` or `IN_PROGRESS`, the control plane MUST establish and record:

- WorkItem/issue identity;
- repository identity;
- worktree identity/path;
- issue branch;
- base revision;
- ownership/lease identity;
- successful verification evidence.

Failure to establish or verify any required identity MUST fail closed before model/worker mutation.

### Deferred: runtime mechanical enforcement

The ownership invariant above is enforced by control-plane verification and recorded evidence, not by
runtime sandboxing. Runtime mechanical enforcement of read-only behaviour, and of worktree identity at
the point of mutation, is not implemented by any consumer repository at present and is not required for
conformance to this standard today. Tracking: harkers/repo-standards#42.

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

For a new issue branch, create the branch and worktree from an explicit base:

```bash
git fetch origin
git worktree add -b feature/123-package-scaffold \
  ../<repo>-wt/issue-123-package-scaffold \
  origin/main
cd ../<repo>-wt/issue-123-package-scaffold
```

If the branch already exists remotely:

```bash
git fetch origin feature/123-package-scaffold
git worktree add --track -b feature/123-package-scaffold \
  ../<repo>-wt/issue-123-package-scaffold \
  origin/feature/123-package-scaffold
```

Agents MUST NOT create a second worktree for the same WorkItem merely because they are a different role or model.

## Verification

Verification is a control-plane gate, not a worker promise. Before every mutating dispatch/handoff, mechanically verify at least:

```bash
git rev-parse --show-toplevel
git branch --show-current
git status --short
pwd
```

The verifier MUST establish that:

- the path itself is the expected Git worktree top level, not merely a directory inside another checkout;
- the worktree belongs to the expected repository;
- the branch corresponds to the active issue;
- the worktree path/identity corresponds to the active WorkItem;
- the live/default checkout is not the mutation target;
- there are no unexplained modifications at a boundary that requires a clean handoff;
- the specification and plan belong to the same issue;
- allowed mutation scope resolves inside the assigned worktree.

Verification performed earlier in the workflow is not sufficient for a later mutating dispatch: the assigned worktree MUST be re-verified at the boundary where authority is handed to the next worker.

## Isolation rules

- MUST NOT use the live/default checkout for implementation, remediation, test authoring, commit creation or any other repository mutation.
- MUST NOT let one worktree serve multiple unrelated implementation issues.
- MUST NOT create, switch to, reuse or substitute a different worktree after assignment.
- MUST NOT switch the assigned worktree to an unrelated branch.
- MUST NOT mix review fixes from another PR into the active worktree.
- MUST NOT widen filesystem scope beyond the assigned worktree/allowed paths.

### Mechanical enforcement of commit creation

The rule that the live/default checkout is not a mutation target is checkable without a
control plane, so it ships with a guard rather than relying on prompt compliance alone.
`tools/guard_protected_commit.py` refuses a commit that carries staged content while the
current branch is a protected branch (`main` and `master` by default).

```bash
git config core.hooksPath .githooks      # once per clone
```

Scope is deliberately narrow. The guard does **not** verify that a worktree was assigned,
that the branch matches the active issue, or that any other isolation rule was followed;
those require the control plane. It catches only the failure that is cheap to detect and
easy to cause by accident — a mutating command run in the wrong directory, which stages work
into the canonical checkout while appearing to succeed.

A detached HEAD and a protected branch with nothing staged are both permitted: an
`--allow-empty` commit or an amend mutates nothing.

Deliberate repository maintenance opts out explicitly, and the opt-out is reported rather
than silent:

```bash
REPO_STANDARDS_ALLOW_PROTECTED_COMMIT=1 git commit -m "..."
```

Per the canonical policy, a deviation requires repository override configuration recorded
against a linked issue. Editing this standard is not a deviation path.
- MUST NOT delete a worktree until its branch/PR state is understood and any unpushed work is recovered.
- A missing, moved, wrong-branch, wrong-repository or otherwise unverifiable worktree blocks mutating dispatch.

## Handoff

Every mutating agent handoff should carry the stable worktree identity plus the currently verified path, branch and base/result revision. Downstream workers MUST consume that assignment rather than infer a workspace from ambient cwd or scope paths.

Read-only reviewer/verifier roles may inspect the same issue worktree with read-only permissions; a new worktree is not required merely to obtain reviewer independence.

## Overlap pre-flight

Worktree isolation stops two agents sharing a checkout; it does nothing about two agents editing
the same files. Before merging, an agent MUST re-check for overlapping work: another unmerged local
branch, or an open pull request, touching the same files. Checking once when work starts is not
enough — a check that was true twenty minutes ago is not true now.

```bash
python3 tools/merge_preflight.py --root . --check
```

## Cleanup

A worktree MUST be removed once its work is merged or closed and no unique work remains;
leaving it in place makes finished work look outstanding and has caused agents to re-open
already-merged work.

After merge/closure and after confirming no unique work remains:

```bash
git worktree remove ../<repo>-wt/issue-123-package-scaffold
git worktree prune

Cleanup is checkable rather than a matter of remembering:

```bash
python3 tools/worktree_audit.py --root .            # report
python3 tools/worktree_audit.py --root . --check    # non-zero if debris exists
python3 tools/worktree_audit.py --root . --prune    # remove landed worktrees
```

A worktree is removable only when it is **provably landed**: its branch has no
patches absent from the base ref and its tree is clean. Anything else — dirty,
unmerged, detached, or missing from disk — is reported with the reason and left
alone. The rule exists because a leftover worktree makes finished work look
outstanding: agents have re-opened already-merged work after finding one.
```

Branch deletion follows repository policy and must not occur while a needed PR, recovery path or evidence reference depends on it.
