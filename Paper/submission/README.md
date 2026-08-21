# Camera-Ready Submission Bundle

Ready-to-upload artefacts for IJCAI–ECAI 2026 (Demonstrations Track, Paper #DM234).

**Deadline:** 29 May 2026, 23:59 UTC-12
**Portal:** <https://proceedings.ijcai.org>
**Login:** `philipp.steigerwald@th-nuernberg.de`

---

## Contents

| File | Purpose |
|---|---|
| `ijcai26.pdf` | Camera-ready paper PDF (4 pages, 405 KB) |
| `ijcai26-source.zip` | LaTeX source bundle for the IJCAI portal (323 KB) |
| `copyright-signed.pdf` | Signed IJCAI Copyright Transfer Agreement (341 KB) |
| `arxiv/` | Separate arXiv submission bundle — see `arxiv/README.md` |

---

## What to upload, where

| Field on proceedings.ijcai.org | File to upload |
|---|---|
| **Camera-ready PDF** | `ijcai26.pdf` |
| **Source files (LaTeX zip)** | `ijcai26-source.zip` |
| **Copyright form** | `copyright-signed.pdf` |
| **ORCID IDs** | enter manually for all 5 co-authors |
| **Author registration** | confirm at least one author registered for the Bremen conference |

---

## Source ZIP contents (`ijcai26-source.zip`)

| File | |
|---|---|
| `ijcai26.tex` | Main paper source |
| `ijcai26.sty` | IJCAI 2026 style |
| `named.bst` | BibTeX style |
| `llars.bib` | Bibliography source |
| `ijcai26.bbl` | Pre-built bibliography (in case the reviewer system doesn't run `bibtex`) |
| `figures/img.png` | Figure 1 — prompt editor screenshot |
| `figures/provenance-analysis.png` | Figure 2 — provenance dashboard |

Compiles standalone with `pdflatex × 2` (no internet, no extra packages).

---

## Verification before upload

- [ ] PDF opens, 4 pages, no `??` references
- [ ] Demo-video URL works: <https://youtu.be/3QaKouwr4gU>
- [ ] Copyright signature is clearly handwritten-looking
- [ ] ZIP file extracts cleanly (no `__MACOSX/` noise)
- [ ] ORCID IDs entered in CMT for all 5 authors

---

## Rebuilding

If the paper source changes:

```bash
cd Paper
bash build.sh                               # compile → ijcai26.pdf + out/ijcai26.bbl
cp ijcai26.pdf submission/                  # refresh submission PDF

# Rebuild source ZIP
rm -rf submission/_zip_tmp
mkdir -p submission/_zip_tmp/figures
cp ijcai26.tex ijcai26.sty named.bst llars.bib out/ijcai26.bbl submission/_zip_tmp/
cp figures/img.png figures/provenance-analysis.png submission/_zip_tmp/figures/
rm -f submission/ijcai26-source.zip
(cd submission/_zip_tmp && zip -r ../ijcai26-source.zip .)
rm -rf submission/_zip_tmp
```

If you need to re-sign the copyright (e.g. updated PDF):

1. Re-fill the form fields with `pypdf` if needed.
2. Overlay the signature image (`Unterschrift.png`) at PDF coords `(45, 95)` with size `80×39 pt`.
