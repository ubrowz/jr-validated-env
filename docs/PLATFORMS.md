# Platform Support — JR Validated Environment

---

## Supported Platforms

| Platform | Status | Notes |
|---|---|---|
| macOS 12 Ventura (Apple Silicon) | ✅ Supported | Primary development platform |
| macOS 12 Ventura (Intel) | ✅ Supported | Tested |
| macOS 13 Sonoma | ✅ Supported | Tested |
| macOS 14 Sequoia | ✅ Supported | Tested |
| macOS 11 Big Sur | ⚠️ Not tested | May work but not validated |
| macOS 10.x or earlier | ❌ Not supported | Required tools unavailable |
| Windows | ❌ Not supported | See below |
| Linux | ❌ Not supported | See below |

---

## macOS-Specific Dependencies

The JR environment relies on the following macOS-specific components:

**Xcode Command Line Tools** — required by the administrator only, for git
and the compiler toolchain used by some R packages during repo building:
```zsh
xcode-select --install
```
End users do not need Xcode Command Line Tools — they install packages from
the pre-built local repository only.

**Dropbox** — required by all users to access the local package repositories
(`R_repo/` and `Python_repo/`). The repositories are distributed via
Dropbox to keep large binary files out of Git.

**R binary type** — the project currently uses `mac.binary.big-sur-arm64`
as the binary type for miniCRAN downloads. Intel Mac users may need the
admin to rebuild the local repo with `mac.binary` instead. This is
controlled by the `BINARY_TYPE` variable in `admin/R/admin_R_install.R`.

> ℹ️ A more elegant mechanism for configuring the binary type without
> editing R code directly is planned for v1.1.

**zsh** — all wrapper scripts are written for zsh, which is the default
shell on macOS since Catalina (10.15). If you are running bash, switch to
zsh or contact your administrator.

---

## Apple Silicon vs Intel

Both Apple Silicon (M1/M2/M3/M4) and Intel Macs are supported, but the
R binary packages in the local repo are architecture-specific. A repo built
on Apple Silicon cannot be used directly on Intel, and vice versa.

If your team uses a mix of Apple Silicon and Intel machines, the administrator
must maintain two separate local repos — one for each architecture — or use
source packages only (slower to install).

The architecture in use is determined by `BINARY_TYPE` in
`admin/R/admin_R_install.R`:

| Architecture | BINARY_TYPE |
|---|---|
| Apple Silicon (M1/M2/M3/M4) | `mac.binary.big-sur-arm64` |
| Intel | `mac.binary` |

---

## Windows — Not Supported

The JR environment is not supported on Windows. The core blockers are:

- All wrapper scripts are written in zsh, which is not available on Windows
- The renv library path structure assumes a Unix filesystem layout
- The `file://` URL scheme used for the local R repo behaves differently
  on Windows
- `pip download` and `pip install --no-index` path handling differs on Windows

**What would need to change for Windows support:**

- Rewrite all zsh wrappers as PowerShell scripts
- Replace `file://` repo URLs with a Windows-compatible path format
- Test the entire install chain on Windows with both R and Python
- Handle the different binary package types for R on Windows

Contributions adding Windows support are welcome provided they do not
degrade the macOS experience. See `CONTRIBUTING.md` for details.

---

## Linux — Not Supported

The JR environment is not supported on Linux. The core blockers are:

- The local R repo is built with macOS binary packages (`mac.binary.*`)
  which are not usable on Linux
- The renv library path includes a `macos` component that would need to
  change for Linux
- The Python `.pkg` installer distribution model is macOS-specific

**What would need to change for Linux support:**

- Rebuild the local R repo with Linux binary packages or source packages
- Update the renv library path detection to handle Linux platform strings
- Replace the Python `.pkg` distribution with a Linux-appropriate method
- Test on at least one major Linux distribution (Ubuntu LTS recommended)

Contributions adding Linux support are welcome provided they do not
degrade the macOS experience. See `CONTRIBUTING.md` for details.

---

## Docker

Docker is explicitly not a goal for this project. See [docs/COMPARISON.md](docs/COMPARISON.md)
for a detailed discussion of why a native validated environment is preferred
over Docker for medical device development contexts.
