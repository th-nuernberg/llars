# Citing LLARS

**Version:** 1.0 | **Date:** August 2026

If you use LLARS in research, teaching or a thesis, please cite the LLARS paper.
For academic work this is **not a request but a license condition** (see
[License](#license)).

---

## Why cite?

LLARS is developed at Technische Hochschule Nürnberg Georg Simon Ohm and funded
through research grants. Citations are the currency that keeps such projects
funded and maintained — and they make your own results reproducible, because
readers can see which tool produced your judgments, metrics and exports.

Cite LLARS if you

- ran evaluation or labeling studies with LLARS,
- analyse or publish data produced with LLARS (exports, metrics such as
  Krippendorff's Alpha),
- self-host, extend or describe the platform in a paper.

---

## How to cite

### BibTeX

```bibtex
@inproceedings{steigerwald2026llars,
  title     = {LLARS: Enabling Domain Expert \& Developer Collaboration for LLM Prompting, Generation and Evaluation},
  author    = {Steigerwald, Philipp and Stieler, Mara and Burghardt, Jennifer and Rudolph, Eric and Albrecht, Jens},
  booktitle = {Proceedings of the Thirty-Fifth International Joint Conference on Artificial Intelligence, {IJCAI-26}},
  publisher = {International Joint Conferences on Artificial Intelligence Organization},
  editor    = {Diego Calvanese},
  pages     = {8526--8529},
  year      = {2026},
  month     = {8},
  note      = {Demo Track},
  doi       = {10.24963/ijcai.2026/995},
  url       = {https://doi.org/10.24963/ijcai.2026/995}
}
```

### Plain text

> Steigerwald, P., Stieler, M., Burghardt, J., Rudolph, E., & Albrecht, J. (2026).
> *LLARS: Enabling Domain Expert & Developer Collaboration for LLM Prompting,
> Generation and Evaluation.* In *Proceedings of the Thirty-Fifth International
> Joint Conference on Artificial Intelligence (IJCAI-26), Demo Track* (pp. 8526–8529).
> <https://doi.org/10.24963/ijcai.2026/995>

---

## Where to find the citation in the product

| Location | Description |
|----------|-------------|
| App footer | The **"Cite LLARS"** link opens a dialog with BibTeX and a copy button |
| Landing page (footer) | Same dialog plus a license note |
| JSON exports | Every JSON export (v1 API and GUI) carries a `citation` block |
| Repository | [`CITATION.cff`](https://github.com/th-nuernberg/llars/blob/main/CITATION.cff) — GitHub's *"Cite this repository"* button reads this file |

### `citation` block in exports

JSON exports carry the reference inside the envelope, so it stays available even
when only the export file is passed on:

```json
{
  "scenario_id": 42,
  "rows": [ ... ],
  "citation": {
    "message": "If you use data produced with LLARS in academic work, please cite the LLARS paper.",
    "paper": "Steigerwald et al. (2026). LLARS: Enabling Domain Expert & Developer Collaboration for LLM Prompting, Generation and Evaluation. In Proceedings of IJCAI-26 (Demo Track), pages 8526-8529. doi:10.24963/ijcai.2026/995",
    "doi": "10.24963/ijcai.2026/995",
    "url": "https://doi.org/10.24963/ijcai.2026/995",
    "bibtex_url": "https://github.com/th-nuernberg/llars/blob/main/CITATION.cff"
  }
}
```

!!! note "JSON envelope only"
    CSV and JSONL exports do **not** contain the block. A comment or preamble
    line would break strict parsers (`pandas.read_csv`, R `read.csv`,
    line-by-line JSONL readers).

---

## `CITATION.cff`

The repository root contains a [Citation File Format](https://citation-file-format.github.io/)
file. GitHub renders it as the *"Cite this repository"* button, and tools such as
Zotero or `cffconvert` can turn it into APA, BibTeX or RIS:

```bash
pip install cffconvert
cffconvert -f bibtex -i CITATION.cff
```

!!! info "Preprint vs. proceedings"
    Cite the **proceedings version** (IJCAI-26 Demo Track,
    doi:10.24963/ijcai.2026/995). The arXiv preprint of the same paper
    ([arXiv:2605.10593](https://arxiv.org/abs/2605.10593)) stays reachable and
    is kept in `CITATION.cff` as an additional identifier, but it is not the
    reference that belongs in a bibliography.

---

## License

LLARS is licensed under the
**[PolyForm Noncommercial License 1.0.0](https://github.com/th-nuernberg/llars/blob/main/LICENSE)**
with an additional citation clause.

| | |
|---|---|
| **Research, teaching, personal use** | Free — the source code may be read, used, modified and redistributed |
| **Public institutions & non-profits** | Free (universities, government bodies, charitable organizations — regardless of funding source) |
| **Academic work** | Free, **with a citation requirement** — the citation is a condition of the license grant |
| **Commercial use** | Requires a separate commercial license |

**Commercial enquiries:** [steigerwaldph@ki-zentrum.bayern](mailto:steigerwaldph@ki-zentrum.bayern)

!!! warning "Not OSI-approved"
    "Source-available" is the accurate term: the code can be read and used
    freely for noncommercial purposes, but the PolyForm Noncommercial License is
    not an Open Source Initiative approved open-source license. Older LLARS
    versions published before this license was introduced shipped without a
    license file and remain governed by the terms (if any) under which they were
    obtained.

---

## See also

- [Project State](project-state.md)
- [v1 Scenario API](api-v1-scenarios.md) — exports including the `citation` block
- [Evaluation](evaluation.md)
