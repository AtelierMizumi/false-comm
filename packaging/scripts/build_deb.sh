#!/usr/bin/env bash
# ==============================================================================
# Build Debian/Ubuntu .deb package for false-comm
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

VERSION="2.0.0"
ARCH="amd64"
PKG_NAME="false-comm"
DEB_DIR="${REPO_ROOT}/dist/deb/${PKG_NAME}_${VERSION}_${ARCH}"
DIST_DIR="${REPO_ROOT}/dist"

cd "${REPO_ROOT}"

echo "==> Preparing Debian package directory..."
rm -rf "${DEB_DIR}"
mkdir -p "${DEB_DIR}/DEBIAN"
mkdir -p "${DEB_DIR}/usr/bin"
mkdir -p "${DEB_DIR}/usr/share/man/man1"
mkdir -p "${DEB_DIR}/usr/share/doc/${PKG_NAME}"
mkdir -p "${DEB_DIR}/usr/share/bash-completion/completions"
mkdir -p "${DEB_DIR}/usr/share/zsh/site-functions"
mkdir -p "${DEB_DIR}/usr/share/fish/vendor_completions.d"

# Copy binary
BINARY_SRC="${REPO_ROOT}/dist/bin/false-comm-linux-x86_64"
if [ ! -f "${BINARY_SRC}" ]; then
    echo "Binary not found at ${BINARY_SRC}. Building binary first..."
    "${REPO_ROOT}/packaging/scripts/build_binary.sh"
fi

cp "${BINARY_SRC}" "${DEB_DIR}/usr/bin/false-comm"
chmod +x "${DEB_DIR}/usr/bin/false-comm"
ln -sf false-comm "${DEB_DIR}/usr/bin/fc"

# Copy man page
if [ -f "${REPO_ROOT}/packaging/man/false-comm.1" ]; then
    cp "${REPO_ROOT}/packaging/man/false-comm.1" "${DEB_DIR}/usr/share/man/man1/"
fi

# Copy shell completions
if [ -d "${REPO_ROOT}/packaging/completions" ]; then
    cp "${REPO_ROOT}/packaging/completions/bash" "${DEB_DIR}/usr/share/bash-completion/completions/false-comm"
    cp "${REPO_ROOT}/packaging/completions/bash" "${DEB_DIR}/usr/share/bash-completion/completions/fc"
    cp "${REPO_ROOT}/packaging/completions/zsh" "${DEB_DIR}/usr/share/zsh/site-functions/_false-comm"
    cp "${REPO_ROOT}/packaging/completions/zsh" "${DEB_DIR}/usr/share/zsh/site-functions/_fc"
    cp "${REPO_ROOT}/packaging/completions/fish" "${DEB_DIR}/usr/share/fish/vendor_completions.d/false-comm.fish"
    cp "${REPO_ROOT}/packaging/completions/fish" "${DEB_DIR}/usr/share/fish/vendor_completions.d/fc.fish"
fi

# Copy docs
cp "${REPO_ROOT}/README.md" "${DEB_DIR}/usr/share/doc/${PKG_NAME}/"
cp "${REPO_ROOT}/LICENSE" "${DEB_DIR}/usr/share/doc/${PKG_NAME}/copyright"

# Create DEBIAN/control
cat << EOF > "${DEB_DIR}/DEBIAN/control"
Package: ${PKG_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: false-comm contributors <thuanc177@gmail.com>
Depends: git
Description: Realistic, stealth Git commit history synthesizer for developers
 false-comm generates mathematically organic contribution heatmaps,
 meaningful semantic diffs, and natural developer work rhythms.
 Includes instant atomic rollback and multi-day commit replay.
EOF

OUTPUT_DEB="${DIST_DIR}/${PKG_NAME}_${VERSION}_${ARCH}.deb"
if command -v dpkg-deb >/dev/null 2>&1; then
    dpkg-deb --build --root-owner-group "${DEB_DIR}" "${OUTPUT_DEB}"
    echo "✔ Debian package created via dpkg-deb: ${OUTPUT_DEB}"
else
    python3 "${SCRIPT_DIR}/make_deb.py" "${DEB_DIR}" "${OUTPUT_DEB}"
fi
