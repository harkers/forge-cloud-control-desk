<!-- Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away. -->

# Security Assurance Standard

This standard defines the security assurance controls that must produce machine-verifiable evidence before a build may reach `PR_READY` or `DONE` in a managed repository: secret detection, software bill of materials, vulnerability detection, static application security testing, container/infrastructure assurance, and finding escalation. It fixes the fail-closed behaviour for security controls that cannot run and for qualifying findings that cannot be tracked. It does not mandate tooling: reference scanners are replaceable defaults, and a repository may substitute an equivalent implementation without changing the required outcome or evidence.

## RS-SEC-001 — Secret detection

### Normative

Every applicable source change MUST be scanned for committed credentials, tokens and secrets before completion. Minimum outcome:

- scanner executed;
- findings count recorded;
- blocking findings prevent completion;
- evidence retained in the verification packet.

### Reference implementation

- Gitleaks

### Evidence

The control MUST record in the Verification Evidence Packet: `tool`, `tool_version`, `status`, `findings` (count by result).

## RS-SEC-002 — Software Bill of Materials

### Normative

Every releasable software build MUST generate a machine-readable SBOM describing the resolved software components included in the build/release artifact. Accepted baseline formats:

- CycloneDX JSON
- SPDX JSON

The SBOM SHOULD be retained as a build artifact and SHOULD be addressable from the completion evidence packet.

### Reference implementation

- Syft

### Evidence

The control MUST record in the Verification Evidence Packet: `tool`, `tool_version`, `status`, `format`, `artifact` (path/digest of the generated SBOM).

## RS-SEC-003 — Vulnerability detection

### Normative

Every applicable releasable build MUST scan dependencies and/or produced artifacts against a recognised vulnerability database. The policy MUST support severity thresholds and explicit exceptions rather than assuming every finding blocks every build. Exceptions MUST be explicit, documented, time-bounded where practical, and attributable to an issue/decision. The default severity thresholds are given in [Vulnerability policy defaults](#vulnerability-policy-defaults).

### Reference implementation

- Grype

Complementary/reference implementations MAY include:

- Trivy
- OSV-Scanner
- ecosystem-native dependency scanners

### Evidence

The control MUST record in the Verification Evidence Packet: `tool`, `tool_version`, `status`, findings by severity, and linked issue references for findings that met the escalation threshold.

## RS-SEC-004 — Static application security testing

### Normative

Applicable application source MUST undergo static security analysis before completion.

### Reference implementation

- Semgrep

Language-specific complementary tooling MAY be used, for example:

- Bandit — Python
- govulncheck / staticcheck — Go
- ecosystem-native lint/security tooling

### Evidence

The control MUST record in the Verification Evidence Packet: `tool`, `tool_version`, `status`, `findings` (rule identifiers and locations).

## RS-SEC-005 — Container / infrastructure assurance

### Normative

Repositories producing containers or infrastructure definitions MUST run the appropriate additional controls. These checks MUST be profile/capability driven rather than universally imposed on documentation-only repositories.

### Reference implementation

- Trivy — container / filesystem / configuration scanning
- Hadolint — Dockerfiles
- Checkov — IaC
- Conftest / OPA — policy validation

### Evidence

The control MUST record in the Verification Evidence Packet, for each executed check: `tool`, `tool_version`, `status`, `findings`. Checks that do not apply to the repository profile resolve to `NOT_APPLICABLE` with a recorded reason.

## RS-SEC-006 — Finding escalation and issue creation

### Normative

Scanner findings MUST NOT exist only as ephemeral CI/log output when they meet the configured escalation threshold. Any finding meeting the repository/profile escalation policy MUST create or update a durable GitHub issue using the appropriate Repo Standards issue type/template. The issue created or updated MUST capture the full [finding record](#finding-record).

### Reference implementation

The Repo Standards finding issue templates, driven by the finding-escalation automation: classify, route per the [finding routing](#finding-routing) table, fingerprint, deduplicate, and update/reopen/link the existing issue where one matches. No third-party tool is mandated for this control.

### Evidence

The control MUST record in the Verification Evidence Packet: a `tracked_findings` entry per escalated finding carrying `fingerprint`, `severity`, `issue` reference and `status`.

Repo Standards additionally requires the packet to record the deduplication result (created, updated, reopened or linked). This is a Repo Standards extension: it is not part of the accepted specification's evidence requirements for this control, so a consumer implementing only the specification's requirements is not non-conformant for omitting it.

## Vulnerability policy defaults

```yaml
vulnerability_policy:
  block:
    - critical
  warn:
    - high
    - medium
```

Every deviation from these defaults is an explicit exception: it MUST be documented, time-bounded where practical, and attributable to an issue/decision, and it MUST be represented in the Verification Evidence Packet.

## Finding routing

Default routing for escalated findings:

| Finding class | Issue type |
| --- | --- |
| security vulnerability, exposed secret, insecure code pattern, vulnerable dependency, container/IaC security | Security Finding |
| build/test/tooling defect or scanner execution failure needing engineering remediation | Bug / Incident |
| bounded remediation derived from an accepted finding, where appropriate | Implementation Task |
| finding requiring evidence-first investigation before remediation | Investigation |

Tool and scanner execution failures are routed by the `blocking_tool_failure` threshold, so the
finding's own `blocking` flag is part of the routing condition, not merely metadata. A producer that
determines a failure does not block completion MUST set `blocking: false`; a non-blocking tool failure
then falls through to the severity check instead of escalating to `Bug / Incident`. An absent
`blocking` flag means the producer did not demote the failure and is treated as blocking, consistent
with the fail-closed convention that an absent `requirement` defaults to `REQUIRED` and an absent
control `status` defaults to `FAIL`. A demoted tool failure is never discarded outright: a
critical-severity finding still routes as `Security Finding`.

## Finding record

An issue created or updated for a finding MUST capture sufficient deterministic context to act on the finding, including where available:

- scanner/tool name and version;
- control ID;
- finding/rule/CVE/GHSA/advisory identifier;
- severity and configured escalation threshold;
- affected package/component/file/resource and version;
- fixed/patched version where known;
- repository, branch, commit SHA and originating PR/build;
- relevant scan command/configuration;
- concise evidence/excerpt or evidence artifact/link;
- remediation guidance supplied by the scanner or standard;
- first-seen and last-seen timestamps;
- current verification status;
- waiver/exception reference if applicable;
- deterministic deduplication/fingerprint key.

## Fingerprint and deduplication

The canonical finding fingerprint is normative; the finding-escalation automation implements it. It is defined as:

```text
fingerprint = "rsf1:" + sha256_hex(
  repository | control | scanner | rule_or_vuln_id | component_and_version_or_path
)[:32]
```

Severity is deliberately NOT part of the fingerprint: it is re-scorable (CVSS revisions and scanner upgrades re-score the same underlying finding), and including it would change the key and break deduplication. Severity is recorded as finding metadata instead.

Rules:

1. Automation MUST search for an existing open issue carrying the same `rsf1:` fingerprint before creating a new one.
2. On a match, the system SHOULD update/reopen/link the existing issue rather than create noise through duplicates.
3. A finding MUST NOT be closed merely because it is absent from one later scan; closure requires deterministic verification that the affected condition is remediated, removed, no longer applicable, or covered by an approved exception.

The fingerprint is part of the mandatory finding record and MUST be recorded both in the issue and in the Verification Evidence Packet, so that deduplication and regression handling remain deterministic across repeated scans.

## Fail-closed states

`BLOCKED_TOOLING`: a required scanner, test runner, or verification tool is unavailable. The result MUST be a blocked/failed verification state recording `missing_control` and `missing_tool`; `tool unavailable` MUST never be translated to `PASS`.

`BLOCKED_FINDING_TRACKING`: a blocking finding requires a durable issue and issue creation cannot be completed. This prevents a pipeline from saying "scan failed, issue creation also failed, continue anyway".

A blocking finding MUST:

1. be represented in the Verification Evidence Packet;
2. have an associated issue/finding record unless issue creation itself is unavailable;
3. prevent `PR_READY` / `DONE` until remediated or explicitly waived under the standard;
4. fail closed if automatic issue creation is required but cannot be completed (state `BLOCKED_FINDING_TRACKING`).

## Reference tool baseline

All tools in this section are defaults, replaceable: a repository MAY substitute an equivalent implementation without changing the required outcome or evidence.

### Universal build/security tooling (default, replaceable)

| Tool | Purpose |
| --- | --- |
| Gitleaks | secret detection |
| Syft | SBOM generation |
| Grype | vulnerability scanning |
| Semgrep | SAST |
| Trivy | complementary vulnerability/container/config scanning |
| ShellCheck | shell validation |

### Python profile (default, replaceable)

- uv
- pytest
- ruff
- mypy
- pip-audit
- Bandit where applicable

### Node / TypeScript profile (default, replaceable)

- Node.js / Corepack
- pnpm/npm
- ESLint
- TypeScript (`tsc`)
- Vitest or repository-selected test runner
- ecosystem-native audit tooling

### Go profile (default, replaceable)

- go test
- staticcheck
- govulncheck

### Container / infrastructure profile (default, replaceable)

- Trivy
- Hadolint
- Checkov
- Conftest / OPA where policy-as-code is required

Reference tools are defaults, not immutable architectural dependencies.

## Policy versus reference implementation

This standard defines outcomes and evidence requirements, not tools. Reference tooling is a replaceable default: a repository MAY substitute an equivalent implementation, provided the required outcome and the evidence it produces are unchanged.

Example:

- Policy: every releasable build MUST generate a machine-readable SBOM.
- Reference implementation: Syft producing CycloneDX JSON or SPDX JSON.

Swapping Syft for another SBOM generator does not change the control; dropping the machine-readable SBOM outcome does.

## Change log

| Version | Change | Date |
| --- | --- | --- |
| 1 | initial issue #2 implementation | 2026-10-04 |
