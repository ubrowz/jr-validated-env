# Adding a New Module to JR Anchored

This document is a step-by-step recipe for adding a validated module to JR Anchored. It is based on the process used to build the Cap (Process Capability) and Corr (Correlation Analysis) modules, and should be followed in order.

---

## Naming conventions

Choose a short lowercase abbreviation for the module (e.g. `cap`, `corr`, `msa`). All artefacts use this abbreviation consistently:

| What | Pattern | Example |
|---|---|---|
| Module folder | `repos/<mod>/` | `repos/cap/` |
| Script names | `jrc_<mod>_<name>.R` | `jrc_cap_normal.R` |
| Validation plan doc number | `JR-VP-<MOD>-001` | `JR-VP-CAP-001` |
| Validation report doc number | `JR-VR-<MOD>-001` | `JR-VR-CAP-001` |
| OQ test case IDs | `TC-<MOD>-<X>-NNN` | `TC-CAP-N-001` |
| User requirement IDs | `UR-<MOD>-NNN` | `UR-CAP-001` |
| OQ runner script | `admin_<mod>_oq` | `admin_cap_oq` |

---

## Step 1 — Create the module folder structure

```
repos/<mod>/
  R/                        # R scripts
  wrapper/                  # thin bash launcher per script
  help/                     # plain-text --help files
  sample_data/              # 1-2 CSV files for users to try
  oq/
    conftest.py             # shared OQ helpers
    data/                   # OQ-specific CSV fixtures
    test_<mod>_<name>.py    # one test file per script
  docs/
    .gitkeep
    # PDFs go here after conversion (see Step 6)
  docs/ignore/              # gitignored — generators and source .docx files
    generate_<mod>_validation_plan.py
    generate_<mod>_validation_report.py
    generate_<mod>_user_manual.py
  admin_<mod>_oq            # OQ runner script
```

---

## Step 2 — Write the R scripts

Each script lives in `repos/<mod>/R/jrc_<mod>_<name>.R`.

**Every script must:**
- Check `RENV_PATHS_ROOT` at startup and call `stop()` if it is not set — this prevents running outside `jrrun`
- Accept a `--help` flag and print the help text then exit cleanly
- Write any PNG output to `~/Downloads/` with a timestamped filename: `<YYYYMMDD_HHMMSS>_jrc_<mod>_<name>.png`
- Print a clear, human-readable summary to stdout
- Exit with a non-zero code on all error conditions (file not found, bad column, n too small, invalid arguments, etc.)

---

## Step 3 — Write the wrapper scripts

One wrapper per script in `repos/<mod>/wrapper/jrc_<mod>_<name>` (no extension, executable):

```bash
#!/bin/bash
exec "$(dirname "$0")/../../../bin/jrrun" jrc_<mod>_<name>.R "$@"
```

Make all wrappers executable: `chmod +x repos/<mod>/wrapper/*`

---

## Step 4 — Write the help files

One plain-text file per script in `repos/<mod>/help/jrc_<mod>_<name>.txt`. Follow the layout used by existing help files: USAGE, DESCRIPTION, ARGUMENTS, OUTPUT, EXAMPLES sections.

---

## Step 5 — Write the OQ test suite

### `repos/<mod>/oq/conftest.py`

Shared helpers copied and adapted from an existing module (e.g. `repos/cap/oq/conftest.py`). Defines `PROJECT_ROOT`, `MODULE_ROOT`, `run()`, `combined()`, and `data()` helpers.

### `repos/<mod>/oq/data/`

Include at minimum:
- A valid "happy path" CSV
- A CSV that triggers a low-n error (fewer than the minimum required rows)
- A CSV with a non-numeric column

### `repos/<mod>/oq/test_<mod>_<name>.py` (one per script)

- Name test cases `TC-<MOD>-<X>-NNN` in the docstring at the top of the file
- Each test maps to a user requirement in the validation plan
- Standard tests to include for every script:
  - Valid input → exit 0, expected output in stdout
  - No arguments → non-zero exit, usage shown
  - File not found → non-zero exit
  - n too small → non-zero exit
  - Non-numeric column → non-zero exit
  - Direct `Rscript` call without `RENV_PATHS_ROOT` → non-zero exit
  - PNG saved to `~/Downloads/` with correct filename pattern

Run the suite to confirm all tests pass before continuing:
```bash
./repos/<mod>/admin_<mod>_oq
```

### `repos/<mod>/admin_<mod>_oq`

Copy `repos/cap/admin_cap_oq` and substitute `cap` → `<mod>` throughout. Make it executable.

---

## Step 6 — Create the validation documents

### Generators

Write three python-docx generator scripts in `repos/<mod>/docs/ignore/`:

- `generate_<mod>_validation_plan.py` — produces `<mod>_validation_plan.docx`
- `generate_<mod>_validation_report.py` — produces `<mod>_validation_report.docx`
- `generate_<mod>_user_manual.py` — produces `<mod>_user_manual.docx`

Use the generators in `repos/cap/docs/ignore/` or `repos/corr/docs/ignore/` as style templates. Key conventions:
- Document numbers: `JR-VP-<MOD>-001 v1.0` and `JR-VR-<MOD>-001 v1.0`
- Validation plan: list all user requirements (`UR-<MOD>-NNN`), then all test cases (`TC-<MOD>-…`), then a requirements traceability matrix
- Validation report: execution summary (N/N PASS, 0 deviations), environment details (R version, OS), per-test-case results table
- User manual: routing table for script selection, per-script argument tables, interpretation guidance

Run the generators:
```bash
cd repos/<mod>/docs/ignore
python3 generate_<mod>_validation_plan.py
python3 generate_<mod>_validation_report.py
python3 generate_<mod>_user_manual.py
```

### Convert to PDF

Open each `.docx` in Word and export as PDF. Save the three PDFs directly into `repos/<mod>/docs/`:
```
repos/<mod>/docs/<mod>_validation_plan.pdf
repos/<mod>/docs/<mod>_validation_report.pdf
repos/<mod>/docs/<mod>_user_manual.pdf
```

---

## Step 7 — Add sample data for users

Place one or two representative CSV files in `repos/<mod>/sample_data/`. These are the files a user would run to try the script for the first time. They should produce a clearly readable, non-trivial result.

---

## Step 8 — Update the GUI (`app/jr_app.py`)

1. Add a `<MOD>_DATA` path variable near the top alongside the other data path variables:
   ```python
   <MOD>_DATA = os.path.join(PROJECT_ROOT, "repos", "<mod>", "oq", "data")
   ```

2. Add a new section to the `CATALOGUE` dict (insert before or after an existing module section):
   ```python
   "<Module Display Name>": {
       "<Script Display Name>": {
           "script": "jrc_<mod>_<name>.R",
           "description": "...",
           "param_type": "<param_type>",   # e.g. "capability", "correlation"
           "sample_data_dir": <MOD>_DATA,
           "sample_prefix": "<mod>_<name>_",
           "png_pattern": "*_jrc_<mod>_<name>.png",
       },
       ...
   },
   ```

---

## Step 9 — Regenerate the project integrity hash

Any change to scripts or wrappers requires a new integrity file:

```bash
./admin/admin_create_hash
```

---

## Step 10 — Update infrastructure files

- **`CHANGELOG.md`** — add a `vX.Y.0` entry listing all new scripts and OQ test count
- **`SCRIPT_IDEAS.md`** — mark the new scripts as completed in the relevant section

---

## Step 11 — Add `repos/<mod>/docs/ignore/` to `.gitignore`

The `.docx` generator source files and output are not committed. Add the path to the root `.gitignore` alongside the other module ignore entries:

```
repos/<mod>/docs/ignore/
```

---

## Step 12 — Update the website

All web pages are in `web/` which is gitignored (local only, not committed).

### `web/index.html` — update in four places

1. `<meta name="description">` — update script and OQ test counts
2. Hero `<h2>` heading — update script and OQ test counts
3. `.stat-value` for validated scripts — update count
4. `.stat-value` for automated OQ tests — update count
5. Footer version span — bump to new version

### `web/modules.html`

1. **Nav grid** (top of page) — add a card:
   ```html
   <a href="#<mod>" class="module-nav-card">
     <div class="module-nav-name"><Mod></div>
     <div class="module-nav-count">N scripts</div>
   </a>
   ```

2. **Module section** (before `</main>`) — add a full `<div class="module-section" id="<mod>">` block with title row, description paragraph, one `module-group` div per script, and a `module-link-row` with links to `script_guide.html#cat-<mod>` and `references.html#<mod>`.

3. **Footer version** — bump to new version.

### `web/references.html`

1. Add an `id="<mod>"` anchor to the relevant `<p class="refs-category">` tag (or create a new `<div class="refs-section" id="<mod>">` section if the module warrants its own block).
2. Add all references cited by the new scripts (standards, papers, textbooks).
3. **Footer version** — bump to new version.

### `web/script_guide.html` — five edits

1. **`SCRIPTS` array** — add one object per script following the existing pattern. Include `id`, `name`, `description`, `when_to_use`, `syntax`, `example`, `image` (path to example PNG), and `tags`.

2. **`CATEGORIES` array** — add a new category object:
   ```js
   {
     label: "<Module Name> (<Mod>)",
     slug: "<mod>",
     ids: ["jrc_<mod>_<name1>", "jrc_<mod>_<name2>", ...]
   }
   ```
   The `slug` value becomes the `#cat-<mod>` anchor used by modules.html.

3. **`TREE`** — add a root-level choice and a `<mod>` node (and sub-nodes if needed). Also update any existing tree nodes that should route to the new module (e.g. the `analyse` node).

4. **`EXAMPLES` object** — add one entry per script with `title`, `image`, and `sections` (array of `{ heading, text }` interpretation blocks). The "See example output →" button only appears when an entry exists here.

5. **`GUI_NAMES` object** — add one entry per script mapping `jrc_<mod>_<name>` to its GUI display name string.

6. **`<meta name="description">`** — update script count and add the new module name.

7. **Footer version** — bump to new version.

### `web/downloads.html`

1. Add a module section (before `</main>`) with a heading, short description, and three download cards (user manual, validation plan, validation report). Link each to `docs/<mod>_<filename>.pdf`.
2. **`<meta name="description">`** — add the new module name.
3. **Footer version** — bump to new version.

### `web/about.html` and `web/pricing.html`

- **Footer version** — bump to new version on both pages.

---

## Step 13 — Generate example output PNGs

Run each new script against sample data to produce PNG output files for the Script Guide:

```bash
cd /path/to/jrscripts
bin/jrrun repos/<mod>/R/jrc_<mod>_<name>.R repos/<mod>/sample_data/<data>.csv <args>
```

PNGs land in `~/Downloads/` with a timestamp prefix. Rename and copy each to:
```
web/examples/jrc_<mod>_<name>.png
```

---

## Step 14 — Commit and push

### Commit order

Commit in two (or three) logical chunks:

1. **Module scripts + OQ** (the main `feat` commit):
   ```
   feat(<mod>): add <Module Name> module (vX.Y.0)

   N scripts: jrc_<mod>_<name1>, jrc_<mod>_<name2>, ...
   OQ: N/N tests passing (JR-VP-<MOD>-001 v1.0).
   ```

2. **Validation PDFs** (a separate `docs` commit):
   ```
   docs(<mod>): add validation plan, report, and user manual PDFs

   JR-VP-<MOD>-001 v1.0, JR-VR-<MOD>-001 v1.0, and <mod>_user_manual.pdf.
   ```

3. **.gitignore update** — can be bundled with the first commit if done at the same time.

Push only after all validation documents are committed and you are satisfied with the module:
```bash
git push origin main
```

---

## Checklist summary

```
Module folder structure
  [ ] repos/<mod>/R/           — R scripts
  [ ] repos/<mod>/wrapper/     — wrapper scripts (executable)
  [ ] repos/<mod>/help/        — help text files
  [ ] repos/<mod>/sample_data/ — 1-2 user-facing sample CSVs
  [ ] repos/<mod>/oq/          — conftest, test files, data fixtures
  [ ] repos/<mod>/docs/        — PDFs (after conversion)
  [ ] repos/<mod>/docs/ignore/ — generators and .docx files (gitignored)
  [ ] repos/<mod>/admin_<mod>_oq — OQ runner (executable)

Validation
  [ ] All OQ tests pass (N/N)
  [ ] Generators produce .docx files without errors
  [ ] PDFs converted and saved to repos/<mod>/docs/

Infrastructure
  [ ] admin/admin_create_hash re-run
  [ ] CHANGELOG.md updated
  [ ] SCRIPT_IDEAS.md updated
  [ ] app/jr_app.py CATALOGUE updated
  [ ] .gitignore: repos/<mod>/docs/ignore/ added

Web (local, gitignored)
  [ ] web/index.html  — 4× count updates + footer version
  [ ] web/modules.html — nav card + module section + footer version
  [ ] web/references.html — new references + id anchor + footer version
  [ ] web/script_guide.html — SCRIPTS + CATEGORIES + TREE + EXAMPLES + GUI_NAMES + meta + footer version
  [ ] web/downloads.html — 3 download cards + meta + footer version
  [ ] web/about.html — footer version
  [ ] web/pricing.html — footer version
  [ ] web/examples/jrc_<mod>_*.png — example output PNGs

Git
  [ ] feat commit: scripts + OQ + .gitignore
  [ ] docs commit: validation PDFs
  [ ] pushed to origin/main
```
