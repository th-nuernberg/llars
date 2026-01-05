#!/bin/bash
# =============================================================================
# Build script for ACL LaTeX paper
# =============================================================================

set -e

cd "$(dirname "$0")"

echo "Building ACL paper..."

# Clean old aux files
rm -f acl_latex.aux acl_latex.bbl acl_latex.blg acl_latex.log acl_latex.out 2>/dev/null || true

# First pass
echo "  [1/4] pdflatex (1st pass)..."
pdflatex -interaction=nonstopmode acl_latex.tex > /dev/null 2>&1

# Bibliography
echo "  [2/4] bibtex..."
bibtex acl_latex > /dev/null 2>&1 || true

# Second pass
echo "  [3/4] pdflatex (2nd pass)..."
pdflatex -interaction=nonstopmode acl_latex.tex > /dev/null 2>&1

# Third pass
echo "  [4/4] pdflatex (3rd pass)..."
pdflatex -interaction=nonstopmode acl_latex.tex > /dev/null 2>&1

# Clean up
rm -f acl_latex.aux acl_latex.bbl acl_latex.blg acl_latex.log acl_latex.out 2>/dev/null || true

echo ""
echo "Done! Output: acl_latex.pdf"

# Copy to project root
cp acl_latex.pdf ../acl_latex.pdf
ls -lh ../acl_latex.pdf

echo "PDF saved to project root: acl_latex.pdf"

# Open PDF on macOS
if command -v open &> /dev/null; then
    open ../acl_latex.pdf
fi
