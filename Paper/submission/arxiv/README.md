# arXiv Submission — LLARS Demo Paper

Camera-ready submission bundle for the IJCAI–ECAI 2026 demonstrations-track paper.

---

## 1. What's in this folder

| File | Purpose |
|---|---|
| `arxiv-ijcai26.tar.gz` | **Upload this to arXiv** (322 KB) — contains everything below |
| `ijcai26.tex` | Paper source |
| `ijcai26.sty` | IJCAI 2026 style file |
| `named.bst` | BibTeX style |
| `llars.bib` | Bibliography source |
| `ijcai26.bbl` | Pre-built bibliography (arXiv won't run bibtex; this is required) |
| `figures/img.png` | Figure 1 — prompt editor screenshot |
| `figures/provenance-analysis.png` | Figure 2 — provenance dashboard |

---

## 2. Submission flow

1. Log in at <https://arxiv.org/user>.
   *Endorsement: if this is your first submission in `cs.HC`, request endorsement from a co-author who already has an arXiv paper there. (Mara, Eric, Jens — anyone of you can endorse Philipp).*
2. Start a new submission at <https://arxiv.org/submit>.
3. Upload **`arxiv-ijcai26.tar.gz`**.
   *Do not upload the compiled PDF — arXiv builds it from source.*
4. arXiv runs `pdflatex × 2` automatically; verify the preview PDF matches the IJCAI version (4 pages).
5. Fill in the metadata (see Section 3 below).
6. Submit.

After submission, arXiv assigns an ID (e.g. `2605.XXXXX`) and the paper appears within 24 h.

---

## 3. Metadata to fill in (copy-paste ready)

### License

```
arXiv.org perpetual, non-exclusive license to distribute this article
```

(default — keeps copyright with author, IJCAI compatible)

### Title

```
LLARS: Enabling Domain Expert & Developer Collaboration for LLM Prompting, Generation and Evaluation
```

*Plain text only — arXiv does not render LaTeX (`\textsc{Llars}`) in titles.*

### Authors

```
Philipp Steigerwald, Mara Stieler, Jennifer Burghardt, Eric Rudolph, Jens Albrecht
```

Affiliation (use for each):

```
Technische Hochschule Nürnberg Georg Simon Ohm
```

### Abstract (plain text — no LaTeX commands)

```
We demonstrate LLARS (LLM Assisted Research System), an open-source platform that bridges the gap between domain experts and developers for building LLM-based systems. It integrates three tightly connected modules into an end-to-end pipeline: Collaborative Prompt Engineering for real-time co-authoring with version control and instant LLM testing, Batch Generation for configurable output production across user-selected prompts $\times$ models $\times$ data with cost control, and Hybrid Evaluation where human and LLM evaluators jointly assess outputs through diverse assessment methods, with live agreement metrics and provenance analysis to identify the best model-prompt combination for a given use case. New prompts and models are automatically available for batch generation and completed batches can be turned into evaluation scenarios with a single click. Interviews with six domain experts and three developers in online counselling confirmed that LLARS feels intuitive, saves considerable time by keeping everything in one place and makes interdisciplinary collaboration seamless.
```

### Comments

```
Accepted at IJCAI-ECAI 2026 Demonstrations Track. 4 pages, 2 figures. Demo video: https://youtu.be/3QaKouwr4gU
```

### Subject classification

| Slot | Code | Name |
|---|---|---|
| **Primary** | `cs.HC` | Human-Computer Interaction |
| **Cross-list** | `cs.CL` | Computation and Language |
| **Cross-list (optional)** | `cs.SE` | Software Engineering |

### MSC / ACM class *(both optional, can leave blank)*

```
ACM Class: H.5.3; I.2.7
```

### DOI

Leave empty — no DOI yet (IJCAI proceedings DOI is assigned later).

### Journal-ref

```
Proceedings of the Thirty-Fifth International Joint Conference on Artificial Intelligence, IJCAI-ECAI 2026, Demonstrations Track
```

*(Optional — can also be added later once IJCAI proceedings citation is finalised.)*

---

## 4. Do NOT upload

- The compiled PDF `ijcai26.pdf` — arXiv only takes source.
- `out/` directory or any LaTeX build artefacts (`.aux`, `.log`, `.toc`).
- The full project repo.
- The video file (`llars.mp4`) — too big anyway; link to the YouTube URL in Comments.

---

## 5. Sanity check before submitting

- [ ] Preview PDF on arXiv shows 4 pages
- [ ] All citations resolve (no `[?]` markers)
- [ ] No `??` or `???` references in the PDF
- [ ] Author list matches IJCAI submission exactly
- [ ] Abstract fits in the form (max ~1900 characters; ours is ~1700)
- [ ] YouTube link in Comments resolves (https://youtu.be/3QaKouwr4gU)
- [ ] Primary category is `cs.HC`

---

## 6. After arXiv assigns an ID

1. Update the IJCAI camera-ready PDF *(optional)* with `\cite{arxiv:2605.XXXXX}` or footnote `arXiv:2605.XXXXX`.
2. Add the arXiv link to:
   - the GitHub README (`https://arxiv.org/abs/2605.XXXXX`)
   - the YouTube description
3. Once IJCAI publishes, add the DOI/proceedings URL back to the arXiv version via "Replace" submission (arXiv allows v2, v3 …).

---

## 7. Rebuilding the bundle (if source changes)

```bash
cd /Users/philippsteigerwald/PycharmProjects/llars/Paper

# Rebuild the PDF + .bbl
bash build.sh

# Refresh the arXiv bundle
rm -rf arxiv/figures
mkdir -p arxiv/figures
cp ijcai26.tex ijcai26.sty named.bst llars.bib out/ijcai26.bbl arxiv/
cp figures/img.png figures/provenance-analysis.png arxiv/figures/
cd arxiv && tar czf arxiv-ijcai26.tar.gz \
    ijcai26.tex ijcai26.sty named.bst llars.bib ijcai26.bbl figures/*.png
```
