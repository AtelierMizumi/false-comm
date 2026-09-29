#!/usr/bin/env bash
# ==============================================================================
# Build standalone single binary for false-comm using PyInstaller
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"

echo "==> Building false-comm standalone binary..."
DIST_DIR="${REPO_ROOT}/dist/bin"
mkdir -p "${DIST_DIR}"

OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

OUTPUT_NAME="false-comm-${OS}-${ARCH}"

# Add data files (profiles, templates) using absolute path
DATA_ARG="${REPO_ROOT}/src/false_comm/data:false_comm/data"

uv run --with pyinstaller pyinstaller \
    --name "${OUTPUT_NAME}" \
    --onefile \
    --clean \
    --add-data "${DATA_ARG}" \
    --distpath "${DIST_DIR}" \
    --workpath "${REPO_ROOT}/build/pyinstaller" \
    --specpath "${REPO_ROOT}/build" \
    src/false_comm/cli/app.py

chmod +x "${DIST_DIR}/${OUTPUT_NAME}"
ln -sf "${DIST_DIR}/${OUTPUT_NAME}" "${DIST_DIR}/fc"
ln -sf "${DIST_DIR}/${OUTPUT_NAME}" "${DIST_DIR}/false-comm"

echo "✔ Binary built successfully: ${DIST_DIR}/${OUTPUT_NAME}"
"${DIST_DIR}/${OUTPUT_NAME}" --version
