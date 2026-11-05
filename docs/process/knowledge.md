<!-- Managed by harkers/repo-standards at revision 13693659. Use .repo-standards.yml overrides instead of editing this header away. -->

# Knowledge Management Standard

Owner decision, 2026-11-02 (final): **Obsidian is the authoritative infrastructure and operational
knowledge repository for Harker Systems. Notion is permanently retired.** This file is the one
canonical knowledge policy; `AGENTS.md`, the global Claude instructions and the vault point here
rather than repeating it.

## Permanent rule

> Harker Systems uses Obsidian as its authoritative infrastructure and operational knowledge
> repository. Notion has been permanently retired. Before infrastructure work, consult relevant
> Obsidian documentation. Following substantive changes, update the affected Obsidian
> documentation. Use Forgejo for source code, version history and work tracking. Do not request,
> recommend, initialise or reconnect Notion. Never store credentials or secrets in Obsidian.

## Where knowledge lives

| System | Holds | Does not hold |
|---|---|---|
| **Harker Knowledge vault** (Obsidian; `/Users/stu/Harker-Knowledge` on the Mac, synced through `knowledge.harker.systems`) | Infrastructure and application documentation, architecture decisions, implementation records, troubleshooting, runbooks, system inventories, agent-generated knowledge | Source code, secrets, operational databases |
| **Forgejo** (`forge.harker.systems`) | Source code, history, issues, pull requests, CI, release records (for example zeus-infra `DECISIONS.md`) | A second knowledge base |
| **Repository docs** (`README.md`, `docs/`, runbooks next to code) | What is needed to build, develop, deploy or operate that repository | Duplicates of vault notes: link instead |
| **Infrastructure wiki** (`infra-wiki.harker.systems`, private) | A curated, reviewed, published subset | Anything published automatically from the vault |
| **Secrets** (Mac Keychain, Infisical, host-restricted files) | Credentials | — (notes name where a secret lives, never the value) |
| ~~Notion~~ | Retired 2026-11-02. Historical links are read-only references | Anything new |

Markdown with lightweight YAML properties is the format. One source per fact: link, do not copy.

## What agents do

1. **Before infrastructure or application work**, read the relevant notes: `00-Home/Dashboard.md`,
   `02-Infrastructure/`, `01-Projects/`, and the note whose `repo` property names the repository
   being changed. Compare documented and observed state; report discrepancies rather than trusting
   either blindly. Notes marked `verified: no` are unchecked.
2. **After a substantive, verified change** (an address, a deployment, a status, a decision),
   update the affected note in place: change the fact, bump `updated`, set `verified` and
   `sources`. Record a material architectural decision as a decision note. Document only what was
   verified; say what was not.
3. **Writes are small and deliberate:** read a note immediately before editing it, change only what
   is needed, never overwrite a note wholesale, and do not create empty or repetitive notes. If
   the vault is not reachable (another host, a CI runner), put the update in the PR description and
   append a capture to `00-Home/Inbox.md` when next on a host with the vault.
4. **Never write secrets** (passwords, tokens, private keys, recovery codes) into a note.
5. **Never request, recommend, initialise, reconnect or remind about Notion**, and do not add Notion
   steps, MCP connections, hooks or checklists to any workflow. A historical Notion link in an old
   document is left as an archived reference, not followed up.

## Linking model

Each application or component note carries, where they exist: `repo` (Forgejo URL), `url`
(published address), `host` (VM, container or machine). The note links to its runbooks and
decisions; the repository's `README.md` or `GUIDE.md` names the vault note (for example
"Knowledge: Harker Knowledge vault, note *Zeus*") rather than copying its content. The
infrastructure wiki and the planned dashboard read these properties; publishing is a deliberate,
reviewed step, never automatic, and private infrastructure detail is not published publicly.
