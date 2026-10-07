<!-- Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away. -->

# `just verify` guidance (RS-BUILD-001)

Guidance document only — deliberately a `.md` so the managed templates ship no
executable `justfile`. A managed repository adopts the canonical entrypoint
into its own `justfile` following this template.

Standards: `standards/build-assurance.md` (RS-BUILD-001, RS-BUILD-002),
`standards/security-assurance.md` (RS-SEC-001…RS-SEC-004).

## Why `just verify` is the canonical entrypoint

RS-BUILD-001 requires every implementation-capable repository to expose
exactly one canonical verification entrypoint that orchestrates all controls
required by its profile. `just verify` is the preferred interface because:

- **One gate, one contract.** Agents call the entrypoint instead of inventing
  their own sequence of checks, so no control is silently skipped.
- **Fail-closed in one place.** The non-zero-exit rule for missing tools (below)
  is enforced by the recipes themselves; a missing tool can never be
  interpreted as a pass.
- **Evidence last.** The final step validates the Verification Evidence
  Packet, so a build that cannot prove its controls cannot claim completion
  (RS-BUILD-002).

An equivalent repository-specific entrypoint MAY be used where justified,
provided it is documented as the canonical gate.

## Sample justfile

```just
# Canonical verification gate. Fail-closed shell: any non-zero command
# (including a missing tool) fails the recipe — nothing is skipped.
set shell := ["bash", "-euo", "pipefail", "-c"]

# The ONLY entrypoint agents call. Dependencies run in listed order.
verify: format lint typecheck unit integration \
        secret-detection sast sbom vulnerability-scan validate-evidence

# --- build-quality controls (RS-BUILD-001) ---

format:
  ruff format --check .

lint:
  ruff check .

typecheck:
  mypy .

unit:
  pytest tests -q

integration:
  pytest tests/integration -q

# --- security controls (replaceable tools; defaults per standard) ---

secret-detection:
  gitleaks detect --source . --redact --report-format json \
    --report-path results/gitleaks.json

sast:
  semgrep ci --config auto --sarif --output results/semgrep.sarif

sbom:
  syft dir:. -o cyclonedx-json=results/sbom.cdx.json

vulnerability-scan:
  grype dir:. -o json --file results/grype.json

# --- completion evidence (RS-BUILD-002) ---

validate-evidence:
  python tools/validate_evidence.py evidence.json
```

### Missing tools MUST exit non-zero

A missing tool MUST fail the gate, never be skipped. `set shell :=
["bash", "-euo", "pipefail", "-c"]` already makes `command not found` a
non-zero exit. Where an explicit, attributable failure is preferred, guard the
recipe:

```just
require: *tool
  @command -v {{tool}} >/dev/null 2>&1 \
    || { echo "missing required assurance tool: {{tool}}" >&2; exit 1; }

secret-detection: require "gitleaks"
  gitleaks detect --source . --redact --report-format json \
    --report-path results/gitleaks.json
```

`tool unavailable` MUST be recorded as `BLOCKED_TOOLING` (with
`missing_control` and `missing_tool`) in the Verification Evidence Packet; it
MUST never be translated to `PASS`.

## Step → control mapping

| Recipe step | Control ID | Outcome |
| --- | --- | --- |
| `format` | RS-BUILD-001 | formatting checks |
| `lint` | RS-BUILD-001 | lint |
| `typecheck` | RS-BUILD-001 | type checking |
| `unit` | RS-BUILD-001 | unit tests |
| `integration` | RS-BUILD-001 | integration tests |
| `secret-detection` (gitleaks) | RS-SEC-001 | committed-secret scan |
| `sast` (semgrep) | RS-SEC-004 | static security analysis |
| `sbom` (syft) | RS-SEC-002 | machine-readable SBOM (CycloneDX JSON) |
| `vulnerability-scan` (grype) | RS-SEC-003 | dependency vulnerability scan |
| `validate-evidence` | RS-BUILD-002 | Verification Evidence Packet validation |

Tools are replaceable defaults: a repository MAY substitute an equivalent
implementation per control, provided the required outcome and the evidence it
produces are unchanged.
