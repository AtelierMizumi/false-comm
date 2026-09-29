#!/usr/bin/env bash
# ==============================================================================
# false-comm Universal Installer
# Compatible with Linux (all distros), macOS, and WSL
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/AtelierMizumi/false-comm/main/install.sh | bash
# Or with options:
#   curl -fsSL ... | bash -s -- --dir ~/.local/bin
# ==============================================================================
set -euo pipefail

REPO="AtelierMizumi/false-comm"
INSTALL_DIR="${HOME}/.local/bin"
BIN_NAME="false-comm"
ALIAS_NAME="fc"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info() {
    printf "${CYAN}==>${NC} %s\n" "$1"
}

success() {
    printf "${GREEN}✔${NC} %s\n" "$1"
}

warn() {
    printf "${YELLOW}⚠${NC} %s\n" "$1"
}

error() {
    printf "${RED}✘ Error:${NC} %s\n" "$1" >&2
    exit 1
}

# Parse command line flags
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --help|-h)
            echo "false-comm Universal Installer"
            echo "Usage: install.sh [--dir <install_path>]"
            exit 0
            ;;
        *)
            warn "Unknown option: $1"
            shift
            ;;
    esac
done

info "Detecting platform and system dependencies..."
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "$ARCH" in
    x86_64|amd64) ARCH="x86_64" ;;
    aarch64|arm64) ARCH="aarch64" ;;
    *) error "Unsupported architecture: $ARCH" ;;
esac

mkdir -p "$INSTALL_DIR"

# Preferred installation method 1: uv (fastest, standalone, isolated)
if command -v uv >/dev/null 2>&1; then
    info "Found 'uv' package manager. Installing false-comm in isolated tool environment..."
    uv tool install --force git+https://github.com/${REPO}.git
    success "Successfully installed false-comm via uv tool!"

# Preferred installation method 2: pipx (standard Python CLI isolator)
elif command -v pipx >/dev/null 2>&1; then
    info "Found 'pipx'. Installing false-comm in isolated environment..."
    pipx install --force git+https://github.com/${REPO}.git
    success "Successfully installed false-comm via pipx!"

# Method 3: Download standalone GitHub Release binary if available
else
    info "Neither uv nor pipx detected. Attempting to fetch standalone binary from GitHub Releases..."
    LATEST_TAG=$(curl -s "https://api.github.com/repos/${REPO}/releases/latest" 2>/dev/null | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/' || echo "")
    
    BINARY_URL=""
    if [ -n "$LATEST_TAG" ]; then
        BINARY_NAME="false-comm-${OS}-${ARCH}"
        BINARY_URL="https://github.com/${REPO}/releases/download/${LATEST_TAG}/${BINARY_NAME}"
    fi

    DOWNLOAD_SUCCESS=false
    if [ -n "$BINARY_URL" ]; then
        info "Downloading standalone executable: $BINARY_NAME..."
        TEMP_BIN="$(mktemp)"
        if curl -fsSL "$BINARY_URL" -o "$TEMP_BIN" 2>/dev/null; then
            chmod +x "$TEMP_BIN"
            mv "$TEMP_BIN" "${INSTALL_DIR}/${BIN_NAME}"
            ln -sf "${INSTALL_DIR}/${BIN_NAME}" "${INSTALL_DIR}/${ALIAS_NAME}"
            DOWNLOAD_SUCCESS=true
            success "Installed standalone binary to ${INSTALL_DIR}/${BIN_NAME} (alias: ${ALIAS_NAME})"
        else
            rm -f "$TEMP_BIN"
        fi
    fi

    # Fallback to python3 venv standalone setup in ~/.local/share/false-comm
    if [ "$DOWNLOAD_SUCCESS" = false ]; then
        info "Falling back to self-contained virtual environment via python3..."
        command -v python3 >/dev/null 2>&1 || error "python3 is required. Please install python3 or uv."
        command -v git >/dev/null 2>&1 || error "git is required. Please install git."

        VENV_DIR="${HOME}/.local/share/false-comm/venv"
        mkdir -p "$(dirname "$VENV_DIR")"
        python3 -m venv "$VENV_DIR"
        "$VENV_DIR/bin/pip" install --upgrade pip
        "$VENV_DIR/bin/pip" install git+https://github.com/${REPO}.git

        ln -sf "$VENV_DIR/bin/false-comm" "${INSTALL_DIR}/${BIN_NAME}"
        ln -sf "$VENV_DIR/bin/fc" "${INSTALL_DIR}/${ALIAS_NAME}"
        success "Installed self-contained false-comm into ${VENV_DIR}"
    fi
fi

# PATH Check
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    warn "${INSTALL_DIR} is not in your PATH."
    echo "Add it by appending the following to your ~/.bashrc, ~/.zshrc, or shell profile:"
    echo ""
    echo "  export PATH=\"\$PATH:${INSTALL_DIR}\""
    echo ""
fi

echo ""
info "Verifying installation..."
if command -v false-comm >/dev/null 2>&1; then
    false-comm --version || true
elif [ -x "${INSTALL_DIR}/${BIN_NAME}" ]; then
    "${INSTALL_DIR}/${BIN_NAME}" --version || true
fi

echo ""
success "false-comm is ready to use!"
echo "Run 'false-comm' (or shorthand 'fc') to launch Mission Control!"
