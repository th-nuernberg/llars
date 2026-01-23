#!/bin/bash
# =============================================================================
# Build script for IJCAI-ECAI 2026 Demo Paper (LLARS)
# =============================================================================

set -e

cd "$(dirname "$0")"

PAPER_NAME="ijcai26"
OUT_DIR="out"

echo "Building IJCAI-ECAI 2026 Demo Paper: ${PAPER_NAME}.tex"
echo ""

# Create output directory
mkdir -p "${OUT_DIR}"

# Clean old aux files
rm -f "${OUT_DIR}/${PAPER_NAME}".{aux,bbl,blg,log,out,toc,lof,lot} 2>/dev/null || true

# First pass
echo "  [1/4] pdflatex (1st pass)..."
pdflatex -interaction=nonstopmode -output-directory="${OUT_DIR}" "${PAPER_NAME}.tex" > /dev/null 2>&1

# Bibliography
echo "  [2/4] bibtex..."
cp *.bib "${OUT_DIR}/" 2>/dev/null || true
cp *.bst "${OUT_DIR}/" 2>/dev/null || true
cd "${OUT_DIR}"
bibtex "${PAPER_NAME}" > /dev/null 2>&1 || true
cd ..

# Second pass
echo "  [3/4] pdflatex (2nd pass)..."
pdflatex -interaction=nonstopmode -output-directory="${OUT_DIR}" "${PAPER_NAME}.tex" > /dev/null 2>&1

# Third pass
echo "  [4/4] pdflatex (3rd pass)..."
pdflatex -interaction=nonstopmode -output-directory="${OUT_DIR}" "${PAPER_NAME}.tex" > /dev/null 2>&1

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
