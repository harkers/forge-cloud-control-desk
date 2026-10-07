<!-- Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away. -->

# Build Assurance Standard

This standard defines which assurance controls must produce machine-verifiable evidence before a build may reach `PR_READY` or `DONE` in a managed repository, and it fixes the fail-closed behaviour for controls that cannot run. It does not mandate tooling: reference scanners and tools are replaceable defaults, and a repository may substitute an equivalent implementation without changing the required outcome or evidence.

## Control taxonomy

| Control ID | Name | Scope | Severity of failure |
| --- | --- | --- | --- |
| `RS-BUILD-001` | Canonical verification gate | Every implementation-capable repository | `BLOCKING` |
| `RS-BUILD-002` | Completion evidence | Every build reaching `PR_READY` / `DONE` | `BLOCKING` |
| `RS-SEC-001` | Secret detection | Every applicable source change | `BLOCKING` |
| `RS-SEC-002` | Software Bill of Materials | Every releasable software build | `BLOCKING` |
| `RS-SEC-003` | Vulnerability detection | Every applicable releasable build | `BLOCKING` |
| `RS-SEC-004` | Static application security testing | Applicable application source | `BLOCKING` |
| `RS-SEC-005` | Container / infrastructure assurance | Repositories producing containers or infrastructure definitions | `PROFILE_CONDITIONAL` |
| `RS-SEC-006` | Finding escalation and issue creation | Findings meeting the configured escalation threshold | `PROFILE_CONDITIONAL` |

A `BLOCKING` control prevents `PR_READY` / `DONE` while its status is `FAIL` or `BLOCKED`. A `PROFILE_CONDITIONAL` control is required only for the profiles that list it; outside those profiles it resolves to `NOT_APPLICABLE` with a recorded reason.

## RS-BUILD-001 — Canonical verification gate

Every implementation-capable repository SHOULD expose exactly one canonical verification entrypoint. The entrypoint MUST orchestrate, as applicable to the repository's profile:

- formatting checks;
- lint;
- type checking;
- unit tests;
- integration tests;
- secret detection;
- static application security testing (SAST);
- SBOM generation;
- vulnerability scanning;
- artifact validation.

`just verify` is the preferred interface. An equivalent repository-specific entrypoint MAY be used where justified, provided it is documented as the canonical gate. Agents SHOULD call that entrypoint instead of inventing their own sequence of checks.

## RS-BUILD-002 — Completion evidence

A build MUST NOT transition to `PR_READY` or `DONE` on prose alone. Every `REQUIRED` control MUST emit a `Verification Evidence Packet` conforming to `schemas/verification-evidence.schema.json`. Each control result carries exactly one status from the enum `PASS`, `WARN`, `FAIL`, `BLOCKED`, `NOT_APPLICABLE`, and blocking failures MUST be represented in the packet together with any tracked finding references.

If a required tool is unavailable, the resulting state MUST be `BLOCKED_TOOLING` and MUST record `missing_control` and `missing_tool`. If a blocking finding requires a durable issue and issue creation cannot be completed, the resulting state MUST be `BLOCKED_FINDING_TRACKING`. `tool unavailable` MUST never be translated to `PASS`.

Prohibited:

```text
"Grype was unavailable, but the dependency changes look safe, so this is DONE."
```

Expected:

```text
status = BLOCKED_TOOLING
missing_control = vulnerability_scan
missing_tool = grype
```

## Profile applicability

Controls MUST be selected by repository profile rather than blindly enabled everywhere. The baseline profiles and their required control lists are:

```yaml
profiles:
  library:
    requires:
      - tests
      - lint
      - secret_detection
      - sast
      - sbom
      - vulnerability_scan

  service:
    requires:
      - tests
      - lint
      - secret_detection
      - sast
      - sbom
      - vulnerability_scan
      - container_scan

  infrastructure:
    requires:
      - secret_detection
      - infrastructure_scan
      - policy_validation

  documentation:
    requires:
      - markdown_lint
      - link_check
      - secret_detection
```

A control omitted from a profile's required list resolves to `NOT_APPLICABLE` for that repository and MUST record the reason in the evidence packet. Profiles MAY be extended through `.repo-standards.yml` without silently weakening centrally required controls; any deliberate exclusion MUST be explicit and auditable.

## Producers

Every control that a profile REQUIRES must be satisfiable. A *producer* is the
command that runs a control and writes its raw report; the canonical registry is
`tools/producers.py`, and the gate resolves one producer per required control of
the selected profile before it runs anything.

Each control has exactly one of two natures:

1. **Shipped producer.** A reference command the standard provides. A consumer
   may override it with `assurance.producers.<control>` in `.repo-standards.yml`
   or with `--control <control>=<command>` for a single run.
2. **Consumer-supplied.** No universal command can exist because the operation
   is repository-specific (`tests`, `lint`, `markdown_lint`, `link_check`,
   `policy_validation`, `container_scan`). The repository declares its command in
   `.repo-standards.yml`:

   ```yaml
   assurance:
     producers:
       policy_validation: "python3 tools/validate_todo.py"
       tests: "pytest tests -q"
   ```

Rules:

1. A required control with no producer is recorded `BLOCKED` with the control
   name and the remediation, never omitted. Omission is indistinguishable from
   "never required", which is the ambiguity this section removes.
2. `BLOCKED` for a missing producer and `BLOCKED` for a missing tool are
   distinct: the first names the configuration to add, the second names the
   binary to install.
3. Adding a control to a profile without giving it a shipped producer or a
   documented remediation is a defect, and `tests/test_producers.py` fails on it
   for every profile.
4. A control that is satisfied by the gate itself rather than by a producer
   (`RS-BUILD-002` is validated by the gate's own `validate-evidence` step)
   records that reason explicitly, so it does not read as a missing tool.

The reference producer for `infrastructure_scan` is Trivy config scanning
(`trivy config`), covering IaC and configuration definitions. A repository that
produces containers instead of infrastructure definitions declares a
`container_scan` producer that names its image.

## Exceptions and waivers

An exception records a time-bounded, attributable acceptance of a specific control finding. The machine-readable waiver record referenced by the evidence schema is:

```yaml
exception:
  id: EXC-2026-014
  control: RS-SEC-003
  scope: "grype finding GHSA-xxxx in requirements.lock"
  justification: "not reachable from any entrypoint; tracked by harkers/workhub#123"
  approved_by: <issue-or-PR-url>
  expires: 2026-12-31
```

Rules:

1. Every exception MUST have an `id`, `justification`, `approved_by` and `expires`.
2. An expired exception is treated as if absent.
3. Exceptions are recorded in the Verification Evidence Packet, never in agent prose alone.

## Policy versus reference implementation

This standard defines outcomes and evidence requirements, not tools. Reference tooling is a replaceable default: a repository MAY substitute an equivalent implementation, provided the required outcome and the evidence it produces are unchanged.

Example:

- Policy: every releasable build MUST generate a machine-readable SBOM.
- Reference implementation: Syft producing CycloneDX JSON or SPDX JSON.

Swapping Syft for another SBOM generator does not change the control; dropping the machine-readable SBOM outcome does.

## Agent obligations

Builders MUST:

1. discover the repository profile and required assurance controls before implementation completion;
2. use the canonical verification entrypoint when available;
3. run all required controls;
4. preserve deterministic evidence;
5. never translate `tool unavailable` into `PASS`;
6. never mark a task complete while a blocking control is `FAIL` or `BLOCKED`;
7. expose findings to the reviewer rather than suppressing them;
8. automatically create or update the appropriate structured issue for findings meeting the configured escalation threshold;
9. deduplicate findings using a stable fingerprint rather than repeatedly opening equivalent issues;
10. link tracked findings back into the completion/verification evidence;
11. record any approved exception/waiver explicitly;
12. run `git diff --check` and inspect repository state before the completion claim;
13. include remote CI status when a draft PR exists.

### Local equivalence for the CI gate

Some repositories cannot run hosted CI: an Actions spending limit or quota, a policy decision not to
send a repository to a third-party runner, or an air-gapped environment. That absence MUST NOT be
treated as a pass, and MUST NOT be satisfied by deleting controls from the workflow.

A repository in that position MAY satisfy the gate by **running the same workflow steps locally**,
against the same tree, and recording that run as the CI evidence:

```bash
python3 tools/offline_ci.py --root .
```

`tools/offline_ci.py` extracts each step of `.github/workflows/validate.yml` and executes it
verbatim. It does not reimplement any control, so the local gate cannot silently drift from the
hosted one.

Conditions on accepting local equivalence as the gate:

- the **same workflow file** is executed, unmodified — editing a workflow to make it locally
  runnable is a gate bypass, not an optimisation;
- every step that executes MUST pass; a single failure blocks the gate, exactly as hosted;
- **skipped steps are declared, not assumed.** Steps using `uses:` and steps needing the network
  cannot run offline. The tool reports each skip and states they are not evidence. A skip is
  acceptable only when the repository records why that control is satisfied another way;
- the local run is recorded in the completion evidence with the command and its output, so the
  evidence shows *what was run*, not merely that something was;
- limitations are stated: hosted-runner specifics (OS image, package versions, services) are not
  reproduced, so a local pass is strong evidence rather than proof of a hosted pass.

`--fail-on-skip` makes any skip a failure, for repositories with no acceptable skips. A per-step
timeout is applied by default so a hanging control cannot hang the gate indefinitely.

Where remote CI *is* available it remains the primary gate; this is a declared substitute, not a
replacement. The rationale for not running remote CI — budget, quota or policy — belongs in
repository override configuration, recorded against a linked issue.

## Lifecycle integration

Target lifecycle:

```text
issue
  -> specification
  -> implementation plan
  -> READY
  -> implementation
  -> task validation
  -> unit/integration tests
  -> secret detection
  -> SAST
  -> SBOM generation
  -> vulnerability scan
  -> profile-specific assurance checks
  -> classify findings
  -> create/update deduplicated finding issues where required
  -> atomic commit
  -> draft PR
  -> CI
  -> independent review
  -> evidence verification
  -> fix/re-review loop if needed
  -> completion packet
  -> PR_READY
  -> DONE
```

Some checks may run earlier or in parallel; this describes required gates, not mandatory serial execution.

## Change log

| Version | Change | Date |
| --- | --- | --- |
| 1 | initial issue #2 implementation | 2026-10-04 |
