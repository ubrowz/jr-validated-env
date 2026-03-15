# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

JR Validated Environment — a framework for running validated R and Python analysis scripts in a controlled, reproducible environment for FDA medical device development (21 CFR 820.70(i), ISO 13485). Package versions are pinned and installed from a local repository (never the internet at runtime). Every run is integrity-checked and logged.

## Common Commands

```zsh
# Run any script in the validated environment
jrrun jrc_ss_discrete.R 0.90 0.95

# Per-script help
jrrun jrc_ss_discrete.R --help

# Show installed R, Python, and package versions
jr_versions

# Admin: set up / rebuild environments (requires Dropbox repo)
./admin/admin_install_R
./admin/admin_install_R --rebuild
./admin/admin_install_R --add pkgname==1.2.3

./admin/admin_install_Python
./admin/admin_install_Python --rebuild

# Admin: regenerate project integrity file (required after adding/changing scripts)
./admin/admin_create_hash

# Admin: generate IQ validation evidence
./admin/admin_validate

# Scaffold a new community script
./admin/admin_scaffold_R jrc_my_script       # creates R/jrc_my_script.R, wrapper/jrc_my_script, help/jrc_my_script.txt
./admin/admin_scaffold_Python jrc_my_script  # creates Python/jrc_my_script.py, wrapper/jrc_my_script, help/jrc_my_script.txt

# Lint all zsh scripts (no native zsh mode — use bash as proxy)
find . -maxdepth 2 -type f -perm -111 ! -name "*.R" ! -name "*.py" | xargs shellcheck -s bash
```

## Architecture

**Execution flow:** `wrapper/jrc_*` → `bin/jrrun` → integrity check → rebuild env if needed → run script → log to `~/.jrscript/<PROJECT_ID>/run.log`

**`bin/jrrun`** is the central dispatcher. It:
1. Resolves the script path (bare filename → `R/` or `Python/` subfolder)
2. Verifies `admin/project_integrity.sha256` via SHA256
3. For `.R`: sets `RENV_PATHS_ROOT`, rebuilds renv library at `~/.renv/<PROJECT_ID>/` if `renv.lock` hash changed
4. For `.py`: sets venv at `~/.venvs/<PROJECT_ID>/`, rebuilds if `python_requirements.txt` hash changed
5. Runs the script, logs exit code

**Bypass protection:** Every R script checks `RENV_PATHS_ROOT` at startup and `stop()`s if it is not set — this prevents scripts from running outside `jrrun`.

**Package control:**
- R: pinned in `admin/R_requirements.txt`, locked in `admin/renv.lock`, stored in `R_repo/my-cran-repo/` (miniCRAN, shared via Dropbox, not in Git)
- Python: pinned in `admin/python_requirements.txt`, stored in `Python_repo/my-repo/` (pip wheels, shared via Dropbox, not in Git)
- `python_requirements.txt` is currently empty — the two Python scripts use only stdlib

**Data convention:** All scripts that consume data expect a two-column CSV with headers `id` and `value`.

## Adding a New Community Script

1. Run `admin/admin_scaffold_R <name>` (or `admin_scaffold_Python`)
2. Fill in the script, help file. The wrapper needs no editing.
3. If new R packages are needed, add to `admin/R_requirements.txt` and run `admin/admin_install_R --add pkg==ver`. This triggers revalidation.
4. Run `admin/admin_create_hash` to regenerate the integrity file.
5. Update `SCRIPT_IDEAS.md` and `CHANGELOG.md`.

## Validation

- IQ evidence: `./admin/admin_validate` → `~/.jrscript/<PROJECT_ID>/validation/`
- OQ Validation Plan: `docs/oq_validation_plan.docx` (JR-VP-002 v1.0) — 122 test cases across all 24 community scripts
- OQ generator: `docs/generate_oq_plan.py` (python-docx)
- Any change to scripts, wrappers, or requirements files requires re-running `admin_create_hash` and potentially revalidation

## Commit and Branch Conventions

Commit format: `<type>: <summary under 72 chars>` — types: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`

Branch prefixes: `feature/`, `fix/`, `docs/`, `refactor/`, `test/`, `release/`

Do not push without explicit instruction — validation artefacts must be complete first.
