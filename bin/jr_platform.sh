#!/bin/bash
#
# jr_platform.sh
# Sourced by jrrun, jr_versions, and admin scripts to provide
# cross-platform (macOS / Windows Git Bash) helper functions.
#
# Usage:
#   source "$(dirname "$0")/jr_platform.sh"   # from bin/
#   source "$SCRIPT_DIR/../bin/jr_platform.sh" # from admin/
#

# --- Detect OS
# Returns: "macos" | "windows" | "linux"
jr_os() {
  case "$OSTYPE" in
    darwin*)                     echo "macos"   ;;
    msys*|cygwin*|win32*)        echo "windows" ;;
    *)                           echo "linux"   ;;
  esac
}

# --- Python virtualenv binary path
# Usage: jr_venv_python "/path/to/venv"
jr_venv_python() {
  local venv="$1"
  if [[ "$(jr_os)" == "windows" ]]; then
    echo "$venv/Scripts/python.exe"
  else
    echo "$venv/bin/python"
  fi
}

# --- Python virtualenv pip path
# Usage: jr_venv_pip "/path/to/venv"
jr_venv_pip() {
  local venv="$1"
  if [[ "$(jr_os)" == "windows" ]]; then
    echo "$venv/Scripts/pip.exe"
  else
    echo "$venv/bin/pip"
  fi
}

# --- Python virtualenv pytest path
# Usage: jr_venv_pytest "/path/to/venv"
jr_venv_pytest() {
  local venv="$1"
  if [[ "$(jr_os)" == "windows" ]]; then
    echo "$venv/Scripts/pytest.exe"
  else
    echo "$venv/bin/pytest"
  fi
}

# --- R platform string for renv library paths
# Returns the platform component used by renv, e.g. "macos" or "windows"
jr_r_platform_dir() {
  if [[ "$(jr_os)" == "windows" ]]; then
    echo "windows"
  else
    echo "macos"
  fi
}

# --- Cross-platform sed in-place edit
# Usage: jr_sed_inplace 's/foo/bar/g' "/path/to/file"
# Handles the macOS 'sed -i ""' vs GNU 'sed -i' difference.
jr_sed_inplace() {
  local expr="$1"
  local file="$2"
  if [[ "$(jr_os)" == "macos" ]]; then
    sed -i '' "$expr" "$file"
  else
    sed -i "$expr" "$file"
  fi
}

# --- Shell RC file for PATH setup
# Returns the file that setup_jr_path.sh should append to.
jr_shell_rc() {
  if [[ "$(jr_os)" == "windows" ]]; then
    echo "$HOME/.bash_profile"
  else
    echo "$HOME/.zprofile"
  fi
}

# --- macOS version (stub gracefully on non-macOS)
jr_os_version() {
  if command -v sw_vers >/dev/null 2>&1; then
    sw_vers -productVersion
  else
    local ver
    ver=$(uname -r 2>/dev/null || echo "unknown")
    echo "$ver"
  fi
}
