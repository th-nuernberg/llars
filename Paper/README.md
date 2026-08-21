# LLARS Demo Paper — IJCAI-ECAI 2026

**Paper #DM234** · Demonstrations Track · Bremen, August 2026

Title: *LLARS: Enabling Domain Expert & Developer Collaboration for LLM Prompting, Generation and Evaluation*

Authors: Philipp Steigerwald, Mara Stieler, Jennifer Burghardt, Eric Rudolph, Jens Albrecht

YouTube demo video: <https://youtu.be/3QaKouwr4gU>

---

## Folder layout

```
Paper/
├── README.md                       ← this file
├── build.sh                        ← compile pdf via pdflatex + bibtex
│
├── ijcai26.tex                     ← MAIN paper source
├── ijcai26.sty                     ← IJCAI 2026 style file
├── named.bst                       ← BibTeX style
├── llars.bib                       ← bibliography
├── ijcai26.pdf                     ← latest compiled PDF
├── figures/                        ← figures (img.png + provenance-analysis.png used in paper)
│
├── submission/                     ← READY-TO-UPLOAD artefacts
│   ├── ijcai26.pdf                 ← camera-ready PDF (= the one above)
│   ├── ijcai26-source.zip          ← IJCAI source ZIP for proceedings.ijcai.org
│   ├── copyright-signed.pdf        ← signed IJCAI Copyright Transfer Agreement
│   └── arxiv/                      ← arXiv source bundle + README
│       ├── README.md               ← step-by-step arXiv submission guide
│       ├── arxiv-ijcai26.tar.gz    ← THE upload to arxiv.org
│       ├── ijcai26.tex/sty/bbl     ← (also inside the tar.gz)
│       ├── llars.bib, named.bst
│       └── figures/
│
├── demo-video/                     ← demo video assets
│   ├── README.md                   ← video production notes
│   ├── KONZEPT.md                  ← script concept
│   ├── SCRIPT.json                 ← step-by-step recording script
│   ├── metadata.md                 ← YouTube upload metadata
│   ├── run.py                      ← Selenium + ffmpeg recorder
│   ├── prepare_demo_data.py        ← demo-data seeding
│   ├── setup_demo_data.sh
│   ├── requirements.txt
│   ├── assets/                     ← recording bg, fonts
│   ├── audio/                      ← TTS-generated narrations
│   ├── data/                       ← counselling case JSON
│   ├── src/                        ← helper modules
│   ├── voices/                     ← TTS reference voices
│   └── output/
│       ├── llars.mp4               ← FINAL 16:9 video (1.1× sped up, +30% volume)
│       └── thumbnails/thumbnail.png ← YouTube thumbnail
│
├── interviews/                     ← user-study interview material
│   ├── interview-leitfaden.md      ← interview guide (master)
│   ├── interview-leitfaden-counsellor.md
│   ├── interview-leitfaden-developer.md
│   └── LLars Interview Zusammenfassung *.md  ← per-participant summaries (9)
│
├── literature/                     ← background reading (PDFs)
│
└── archive/                        ← historic / unused files
    ├── ijcai26_V0.pdf              ← first draft (Jan 2026)
    ├── ijcai26_V1.pdf              ← pre-submission draft (Jan 2026)
    ├── ijcai26-template.tex        ← original IJCAI template
    ├── ijcai26.bib                 ← obsolete bib (use llars.bib)
    ├── figure-comparison.{pdf,tex} ← unused standalone comparison figure
    ├── CAMERA_READY_CHECKLIST.md   ← superseded by submission/README files
    └── PAPER_NOTES.md              ← internal drafting notes
```

---

## Quick commands

### Compile the PDF

```bash
cd Paper
bash build.sh
```

Outputs `ijcai26.pdf` (4 pages). Intermediate artefacts go to `out/` (auto-deleted between builds, not tracked).

### Rebuild submission ZIP

```bash
cd Paper
bash build.sh                        # produces fresh out/ijcai26.bbl

rm -rf submission/_zip_tmp
mkdir -p submission/_zip_tmp/figures
cp ijcai26.tex ijcai26.sty named.bst llars.bib out/ijcai26.bbl submission/_zip_tmp/
cp figures/img.png figures/provenance-analysis.png submission/_zip_tmp/figures/
rm -f submission/ijcai26-source.zip
cd submission/_zip_tmp && zip -r ../ijcai26-source.zip . && cd ..
rm -rf _zip_tmp

# For arXiv (.tar.gz)
cd Paper
cp -f ijcai26.tex ijcai26.sty named.bst llars.bib out/ijcai26.bbl submission/arxiv/
cp -f figures/img.png figures/provenance-analysis.png submission/arxiv/figures/
cd submission/arxiv && rm -f arxiv-ijcai26.tar.gz && \
  tar czf arxiv-ijcai26.tar.gz ijcai26.tex ijcai26.sty named.bst llars.bib ijcai26.bbl figures/*.png
```

---

## Submission status

| Track | Deadline | Status |
|---|---|---|
| **IJCAI Camera-Ready** | 29 May 2026, 23:59 UTC-12 | ⏳ ready to upload (`submission/ijcai26.pdf` + `submission/ijcai26-source.zip` + `submission/copyright-signed.pdf`) |
| **arXiv** | — (when ready) | ⏳ ready to upload (`submission/arxiv/arxiv-ijcai26.tar.gz`); see `submission/arxiv/README.md` |

### What you still have to do

1. Upload `submission/ijcai26.pdf` + `submission/ijcai26-source.zip` + `submission/copyright-signed.pdf` to <https://proceedings.ijcai.org> (login: `philipp.steigerwald@th-nuernberg.de`).
2. Enter ORCID IDs for all 5 co-authors in the IJCAI CMT (required 2026).
3. Register at least one author for the conference (Bremen, 17–21 Aug 2026).
4. Upload `submission/arxiv/arxiv-ijcai26.tar.gz` to <https://arxiv.org/submit>. Metadata is in `submission/arxiv/README.md`.
