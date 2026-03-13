# Contributing to JR Validated Environment

Thank you for your interest in contributing. This document explains how to
get started, what we expect from contributions, and what kinds of changes
are and are not accepted.

---

## Table of Contents

1. [Before You Start](#before-you-start)
2. [Setting Up a Development Environment](#setting-up-a-development-environment)
3. [Branch Naming Conventions](#branch-naming-conventions)
4. [Commit Message Format](#commit-message-format)
5. [Linting zsh Scripts](#linting-zsh-scripts)
6. [Pull Request Process](#pull-request-process)
7. [What We Will and Will Not Accept](#what-we-will-and-will-not-accept)

---

## Before You Start

Please open an **issue before submitting a pull request** so the proposed
change can be discussed. This avoids situations where significant work is
done on a change that turns out to be out of scope or in conflict with the
project's direction.

For small fixes (typos, documentation corrections, obvious bugs) you may
submit a pull request directly without an issue.

---

## Setting Up a Development Environment

**Requirements:**
- macOS 12 Ventura or later (Apple Silicon or Intel)
- Xcode Command Line Tools: `xcode-select --install`
- R — version specified in `admin/r_version.txt`
- Python — version specified in `admin/python_version.txt`
- Dropbox — for the local package repository
- shellcheck — for linting zsh scripts: `brew install shellcheck`
- Git

**Steps:**

1. Fork the repository on GitHub.

2. Clone your fork:
```zsh
git clone https://github.com/<your-username>/jr-validated-environment.git
cd jr-validated-environment
```

3. Add the upstream remote so you can pull future changes:
```zsh
git remote add upstream https://github.com/yourorg/jr-validated-environment.git
```

4. Set up your local package repository. Since `R_repo/` and `Python_repo/`
   are excluded from Git, you need to build them from scratch or obtain them
   from a team member:
```zsh
./admin/admin_install_R --rebuild
./admin/admin_install_Python --rebuild
```

5. Run `setup_jr_path.zsh` to add the project to your PATH:
```zsh
./setup_jr_path.zsh
```
   Then open a new Terminal window.

6. Verify everything is working:
```zsh
./admin/admin_validate
```

---

## Branch Naming Conventions

Branch names should be lowercase and use hyphens as separators.
Use one of the following prefixes:

| Prefix | Use for |
|---|---|
| `feature/` | New functionality |
| `fix/` | Bug fixes |
| `docs/` | Documentation changes only |
| `refactor/` | Code restructuring with no behaviour change |
| `test/` | Adding or improving tests |
| `release/` | Release preparation |

**Examples:**
```
feature/add-flag-admin-install
fix/renv-library-path-detection
docs/update-troubleshooting-guide
refactor/simplify-rebuild-block
```

---

## Commit Message Format

Use the following format for commit messages:

```
<type>: <short summary in present tense, max 72 characters>

<optional body — explain what and why, not how>
```

**Types:**

| Type | Use for |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code change with no behaviour change |
| `chore` | Maintenance, dependency updates |
| `test` | Adding or updating tests |

**Examples:**
```
feat: add --add flag to admin_install_R for single package updates

fix: capture CALL_DIR before cd in jrrun

docs: add troubleshooting entry for renv library empty after rebuild

refactor: simplify renv rebuild condition check
```

Keep the summary line under 72 characters. Use the body to explain the
reasoning behind the change if it is not obvious from the summary.

---

## Linting zsh Scripts

All zsh scripts must pass `shellcheck` before submission. Run it on any
script you have modified:

```zsh
shellcheck -s bash myscript
```

Note: shellcheck does not have a native zsh mode — using `-s bash` catches
the vast majority of issues that apply to zsh as well. Be aware that a small
number of zsh-specific constructs (such as 1-based array indexing) may not
be flagged correctly, so review these manually.

To lint all scripts in the project at once:

```zsh
find . -maxdepth 2 -type f -perm -111 ! -name "*.R" ! -name "*.py" \
  | xargs shellcheck -s bash
```

Pull requests that introduce shellcheck warnings will be asked to resolve
them before merging.

---

## Pull Request Process

1. Make sure your branch is up to date with upstream main before opening
   a pull request:
```zsh
git fetch upstream
git rebase upstream/main
```

2. Run shellcheck on all modified scripts.

3. If you modified any requirements files, re-run `admin_validate` to
   regenerate the validation scripts and confirm the environment is consistent:
```zsh
./admin/admin_validate
```

4. If you added or modified any scripts or wrappers, re-generate the
   integrity file:
```zsh
./admin/admin_create_hash
```
   Note: `admin/project_integrity.sha256` is excluded from Git — do not
   commit it. It is listed in `.gitignore` for this reason.

5. Open a pull request against the `main` branch with a clear description
   of what the change does and why. Reference the related issue number
   if one exists (e.g. `Closes #42`).

6. A maintainer will review the pull request. Please respond to review
   comments within a reasonable time. Pull requests with no activity for
   30 days may be closed.

---

## What We Will and Will Not Accept

### Will accept

- Bug fixes with a clear description of the problem and how the fix
  addresses it
- New functionality that is consistent with the validated environment
  philosophy — controlled package installation, integrity checking,
  clear audit trail
- Documentation improvements — clearer wording, missing steps, new
  troubleshooting entries
- Support for additional platforms (Windows, Linux) provided the macOS
  behaviour is not degraded
- Performance improvements to the admin or rebuild scripts
- New example R or Python scripts that demonstrate validated environment usage
- Community scripts submitted with a complete validation package (see
  [Contributing Community Scripts](#contributing-community-scripts))

### Will NOT accept

- Changes that weaken or bypass integrity checking
- Changes that allow packages to be installed from the internet during
  normal user script execution
- Changes that remove the controlled local repository requirement
- Changes that make the validation evidence less transparent or harder
  for a Quality Manager to review
- Breaking changes to the wrapper interface without a deprecation path
- Changes that introduce dependencies on tools not available via
  standard macOS + Xcode CLT + Homebrew

If you are unsure whether a proposed change falls into one of these
categories, open an issue and ask before investing time in the
implementation.

---

## Regulatory Note

This project is used in medical device development contexts where software
validation is a regulatory requirement. Contributors should be aware that
changes to core environment management logic — package installation,
integrity checking, library path enforcement — may have validation
implications for organisations using the tool. Such changes will be reviewed
carefully and will require clear justification and thorough testing before
acceptance.


