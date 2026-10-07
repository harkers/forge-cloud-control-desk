#!/usr/bin/env python3
# Managed by harkers/repo-standards at revision d5afae46. Use .repo-standards.yml overrides instead of editing this header away.
"""Canonical producer registry: which command satisfies which control.

A *producer* is the command that runs a control and writes its raw report. This
module is the single place that answers the two questions the gate previously
left open (harkers/repo-standards#77):

- for a control a profile requires, which command produces its result?
- if there is no shipped command, what must a consumer do to supply one?

`SHIPPED_PRODUCERS` maps a control name to a command template. The assembler
substitutes `{artifact}` (where the raw report MUST be written) and `{results}`
(the results directory). The assembler then parses the report into normalized
findings.

`CONSUMER_SUPPLIED` names every control for which no universal command exists,
with the remediation a consumer receives when their profile requires it and
they have not declared a producer. These are roles where the command is
repository-specific by nature:

- `tests`, `lint`, `markdown_lint`, `link_check` depend on the repository's own
  toolchain;
- `policy_validation` validates that repository's policy artifacts, which no
  central command can know;
- `container_scan` needs an image reference the repository must name.

Adding a control to a profile without adding it here, or to
`SHIPPED_PRODUCERS`, is the defect the registry exists to prevent, and
`tests/test_producers.py` fails on it.
"""

from __future__ import annotations

#: control name -> command template. `{artifact}` is the path the command MUST
#: write its raw report to; `{results}` is the results directory.
SHIPPED_PRODUCERS: dict[str, str] = {
    "secret_detection": (
        "gitleaks detect --source . --redact --report-format json "
        '--report-path "{artifact}"'
    ),
    "sast": 'semgrep ci --config auto --sarif --output "{artifact}"',
    "sbom": 'syft dir:. -o cyclonedx-json="{artifact}"',
    "vulnerability_scan": 'grype dir:. -o json --file "{artifact}"',
    "infrastructure_scan": 'trivy config --format json --output "{artifact}" .',
}

#: control name -> remediation shown when a profile requires the control and no
#: producer is configured.
CONSUMER_SUPPLIED: dict[str, str] = {
    "tests": (
        "declare assurance.producers.tests in .repo-standards.yml, e.g. "
        '"pytest tests -q"'
    ),
    "lint": (
        'declare assurance.producers.lint in .repo-standards.yml, e.g. "ruff check ."'
    ),
    "markdown_lint": (
        "declare assurance.producers.markdown_lint in .repo-standards.yml, e.g. "
        "\"markdownlint-cli2 '**/*.md'\""
    ),
    "link_check": (
        "declare assurance.producers.link_check in .repo-standards.yml, e.g. "
        '"lychee --no-progress ."'
    ),
    "policy_validation": (
        "declare assurance.producers.policy_validation in .repo-standards.yml "
        "with the command that validates this repository's policy artifacts, "
        'e.g. "python3 tools/validate_todo.py"'
    ),
    "container_scan": (
        "declare assurance.producers.container_scan in .repo-standards.yml with "
        "the command that scans the repository image, e.g. "
        '"trivy image --format json --output \\"{artifact}\\" <image:tag>"'
    ),
}


def producer_for(
    control: str,
    shipped: dict[str, str] | None = None,
    repo_declared: dict[str, str] | None = None,
    overrides: dict[str, str] | None = None,
) -> str | None:
    """Resolve a producer command, most specific source first.

    Precedence: an explicit run-time override, then the repository's own
    declaration, then the shipped default. `None` means no producer is known,
    which the assembler records as BLOCKED with the remediation from
    `CONSUMER_SUPPLIED` rather than silently omitting the control.
    """
    for source in (overrides, repo_declared, shipped or SHIPPED_PRODUCERS):
        if source and control in source:
            command = source[control]
            if command:
                return command
    return None


#: control -> binary a shipped producer needs. Derived so the registry stays the
#: single source: the first token of the shipped command is the executable.
SHIPPED_TOOLS: dict[str, str] = {
    control: command.split()[0] for control, command in SHIPPED_PRODUCERS.items()
}


def tool_for(control: str) -> str | None:
    """The binary a shipped producer for `control` runs, if any."""
    return SHIPPED_TOOLS.get(control)


def remediation_for(control: str) -> str:
    """How to unblock `control`.

    A missing *producer* and a missing *tool* need different actions, and the
    standard requires the packet to distinguish them:

    - a control with a shipped producer is blocked because the binary is absent,
      so the remediation is to install it;
    - a consumer-supplied control is blocked because nothing was declared, so the
      remediation is the configuration key to add;
    - an unmapped control is a defect in the standard itself.

    Returning one generic message for all three told a consumer to "add a shipped
    producer" for a control that already had one (found while adopting rs#77).
    """
    tool = SHIPPED_TOOLS.get(control)
    if tool is not None:
        return (
            f"install {tool!r}, the shipped producer for {control!r} "
            f"(command: {SHIPPED_PRODUCERS[control]})"
        )
    declared = CONSUMER_SUPPLIED.get(control)
    if declared is not None:
        return declared
    return (
        "add a shipped producer for this control in tools/producers.py, or "
        "declare assurance.producers.<control> in .repo-standards.yml"
    )
