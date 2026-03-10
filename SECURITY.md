# Security Policy — JR Validated Environment

---

## Supported Versions

Security fixes are applied to the latest released version only.

| Version | Supported |
|---|---|
| Latest release | ✅ |
| Older releases | ❌ |

---

## Scope

This security policy covers vulnerabilities in the JR Validated Environment
project itself — specifically the zsh wrapper scripts, R scripts, Python
scripts, and the environment management logic.

**In scope:**

- Shell injection vulnerabilities in zsh wrapper scripts
- Path traversal issues in file handling
- Privilege escalation via admin scripts
- Integrity check bypass vulnerabilities
- Insecure handling of environment variables

**Out of scope:**

- Vulnerabilities in R, Python, or any third-party packages (report these
  to the respective upstream projects)
- Vulnerabilities in Dropbox, git, or other external tools
- Issues that require physical access to the machine
- Social engineering attacks

---

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it
responsibly rather than opening a public GitHub issue.

**Contact:** Open a private security advisory on GitHub via:

> Repository → Security → Advisories → New draft security advisory

Alternatively, email the maintainer directly. The email address is listed
in the repository's GitHub profile.

**Please include in your report:**

- A clear description of the vulnerability
- The affected script(s) or component(s)
- Steps to reproduce the issue
- The potential impact if exploited
- Your suggested fix, if you have one (optional but appreciated)

---

## Response Timeline

| Milestone | Target |
|---|---|
| Acknowledgement of report | Within 5 business days |
| Initial assessment | Within 10 business days |
| Fix or mitigation plan communicated | Within 30 days |
| Fix released | Dependent on severity — see below |

**Severity-based release timeline:**

| Severity | Target fix release |
|---|---|
| Critical (remote code execution, privilege escalation) | Within 7 days |
| High (integrity bypass, path traversal) | Within 14 days |
| Medium (information disclosure, minor bypass) | Within 30 days |
| Low (hardening improvements) | Next scheduled release |

---

## Disclosure Policy

This project follows **coordinated disclosure**:

1. Reporter submits vulnerability privately
2. Maintainer acknowledges and investigates
3. Fix is developed and tested
4. Fix is released
5. Reporter is credited in the release notes (unless they prefer anonymity)
6. Full public disclosure after the fix has been available for at least
   14 days, giving users time to update

We ask reporters to respect this timeline and not disclose the vulnerability
publicly until a fix has been released, or until 90 days have passed since
the initial report — whichever comes first.

---

## Regulatory Note

This project is used in medical device development contexts. Security
vulnerabilities that could compromise the integrity of the validated
environment — for example, allowing packages to be installed from
uncontrolled sources, or bypassing integrity checks — have potential
regulatory implications for organisations using the tool. Such
vulnerabilities will be treated with the highest priority.
