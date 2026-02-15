#!/usr/bin/env bash
# =============================================================================
# Build script for IJCAI-ECAI 2026 Demo Paper (LLARS)
# =============================================================================

# If started with another shell (e.g., /bin/zsh script.sh), re-exec with bash.
if [ -z "${BASH_VERSION:-}" ]; then
    exec /usr/bin/env bash "$0" "$@"
fi

set -euo pipefail

SCRIPT_PATH="${BASH_SOURCE[0]}"
SCRIPT_DIR="${SCRIPT_PATH%/*}"
if [ "${SCRIPT_DIR}" = "${SCRIPT_PATH}" ]; then
    SCRIPT_DIR="."
fi
SCRIPT_DIR="$(cd "${SCRIPT_DIR}" && pwd)"
cd "${SCRIPT_DIR}"

PAPER_NAME="ijcai26"
PAPER_TEX="${SCRIPT_DIR}/${PAPER_NAME}.tex"
OUT_DIR="${SCRIPT_DIR}/out"

echo "Building IJCAI-ECAI 2026 Demo Paper: ${PAPER_NAME}.tex"
echo "Main source: ${PAPER_TEX}"
echo ""

if [ ! -f "${PAPER_TEX}" ]; then
    echo "Error: Missing source file ${PAPER_TEX}" >&2
    exit 1
fi

# Create output directory
mkdir -p "${OUT_DIR}"

# Clean old aux files
rm -f "${OUT_DIR}/${PAPER_NAME}".{aux,bbl,blg,log,out,toc,lof,lot} 2>/dev/null || true
# Remove potential shadow copies in out/ to avoid compiling stale sources.
rm -f "${OUT_DIR}/${PAPER_NAME}.tex" "${OUT_DIR}/${PAPER_NAME}.sty" 2>/dev/null || true
# Keep Paper/ root clean from generated artifacts.
rm -f "${SCRIPT_DIR}/${PAPER_NAME}".{aux,bbl,blg,log,out,toc,lof,lot} 2>/dev/null || true

# First pass
echo "  [1/4] pdflatex (1st pass)..."
pdflatex -interaction=nonstopmode -output-directory="${OUT_DIR}" "${PAPER_TEX}" > /dev/null 2>&1

# Bibliography
echo "  [2/4] bibtex..."
cp -f ./*.bib "${OUT_DIR}/" 2>/dev/null || true
cp -f ./*.bst "${OUT_DIR}/" 2>/dev/null || true
cd "${OUT_DIR}"
bibtex "${PAPER_NAME}" > /dev/null 2>&1 || true
cd ..

# Second pass
echo "  [3/4] pdflatex (2nd pass)..."
pdflatex -interaction=nonstopmode -output-directory="${OUT_DIR}" "${PAPER_TEX}" > /dev/null 2>&1

# Third pass
echo "  [4/4] pdflatex (3rd pass)..."
pdflatex -interaction=nonstopmode -output-directory="${OUT_DIR}" "${PAPER_TEX}" > /dev/null 2>&1

# Copy final PDF to Paper folder
cp "${OUT_DIR}/${PAPER_NAME}.pdf" "./${PAPER_NAME}.pdf"

echo ""
echo "Done!"
echo ""
ls -lh "./${PAPER_NAME}.pdf"
echo ""
echo "Output: Paper/${PAPER_NAME}.pdf"

# Open PDF on macOS
if command -v open &> /dev/null; then
    open "./${PAPER_NAME}.pdf"
fi
