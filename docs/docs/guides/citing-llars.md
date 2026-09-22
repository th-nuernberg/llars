# LLARS zitieren

**Version:** 1.0 | **Stand:** August 2026

Wenn Sie LLARS in Forschung, Lehre oder einer Abschlussarbeit einsetzen, zitieren
Sie bitte das LLARS-Paper. Für akademische Arbeiten ist die Zitation **keine
Bitte, sondern eine Lizenzbedingung** (siehe [Lizenz](#lizenz)).

---

## Warum zitieren?

LLARS wird an der Technischen Hochschule Nürnberg Georg Simon Ohm entwickelt und
über Forschungsmittel finanziert. Zitationen sind die Währung, mit der solche
Projekte weiterfinanziert und weiterentwickelt werden — und sie machen Ihre
eigenen Ergebnisse reproduzierbar, weil Leserinnen und Leser nachvollziehen
können, mit welchem Werkzeug Bewertungen, Metriken und Exporte entstanden sind.

Zitieren Sie LLARS, wenn Sie

- Bewertungs- oder Labeling-Studien mit LLARS durchgeführt haben,
- mit LLARS erzeugte Daten (Exporte, Metriken wie Krippendorff's Alpha)
  auswerten oder veröffentlichen,
- die Plattform selbst hosten, erweitern oder in einem Paper beschreiben.

---

## Wie zitieren?

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

### Fließtext

> Steigerwald, P., Stieler, M., Burghardt, J., Rudolph, E., & Albrecht, J. (2026).
> *LLARS: Enabling Domain Expert & Developer Collaboration for LLM Prompting,
> Generation and Evaluation.* In *Proceedings of the Thirty-Fifth International
> Joint Conference on Artificial Intelligence (IJCAI-26), Demo Track* (S. 8526–8529).
> <https://doi.org/10.24963/ijcai.2026/995>

---

## Wo Sie die Zitation im Produkt finden

| Ort | Beschreibung |
|-----|--------------|
| App-Footer | Link **„LLARS zitieren"** öffnet einen Dialog mit BibTeX und Kopier-Button |
| Landing Page (Footer) | Derselbe Dialog + Lizenzhinweis |
| JSON-Exporte | Jeder JSON-Export (v1-API und GUI) enthält einen `citation`-Block |
| Repository | [`CITATION.cff`](https://github.com/th-nuernberg/llars/blob/main/CITATION.cff) — GitHubs Button *„Cite this repository"* liest diese Datei |

### `citation`-Block in Exporten

JSON-Exporte tragen die Referenz direkt im Envelope, damit sie auch dann
verfügbar ist, wenn nur die Exportdatei weitergegeben wird:

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

!!! note "Nur im JSON-Envelope"
    CSV- und JSONL-Exporte enthalten den Block **nicht**. Eine Kommentar- oder
    Präambel-Zeile würde strikte Parser (`pandas.read_csv`, R `read.csv`,
    zeilenweise JSONL-Leser) brechen.

---

## `CITATION.cff`

Im Repository-Root liegt eine [Citation File Format](https://citation-file-format.github.io/)-Datei.
GitHub rendert daraus den Button *„Cite this repository"*, und Werkzeuge wie
Zotero oder `cffconvert` können daraus APA, BibTeX oder RIS erzeugen:

```bash
pip install cffconvert
cffconvert -f bibtex -i CITATION.cff
```

!!! info "Preprint vs. Proceedings"
    Zitieren Sie die **Proceedings-Version** (IJCAI-26 Demo Track,
    doi:10.24963/ijcai.2026/995). Der arXiv-Preprint desselben Papers
    ([arXiv:2605.10593](https://arxiv.org/abs/2605.10593)) bleibt erreichbar und
    steht in `CITATION.cff` als zusätzlicher Identifier, ist aber nicht die
    Referenz, die in eine Literaturliste gehört.

---

## Lizenz

LLARS steht unter der
**[PolyForm Noncommercial License 1.0.0](https://github.com/th-nuernberg/llars/blob/main/LICENSE)**
mit einer zusätzlichen Zitationsklausel.

| | |
|---|---|
| **Forschung, Lehre, private Nutzung** | Kostenlos — der Quellcode ist einsehbar, nutzbar, veränderbar und weitergebbar |
| **Öffentliche Einrichtungen & Non-Profits** | Kostenlos (Hochschulen, Behörden, gemeinnützige Organisationen — unabhängig von der Finanzierungsquelle) |
| **Akademische Arbeiten** | Kostenlos, **mit Zitationspflicht** — die Zitation ist Bedingung der Lizenzgewährung |
| **Kommerzielle Nutzung** | Erfordert eine separate kommerzielle Lizenz |

**Kommerzielle Anfragen:** [steigerwaldph@ki-zentrum.bayern](mailto:steigerwaldph@ki-zentrum.bayern)

!!! warning "Nicht OSI-approved"
    „Quelloffen" heißt hier *source-available*: Der Code ist einsehbar und für
    nicht-kommerzielle Zwecke frei nutzbar, die PolyForm Noncommercial License
    ist aber keine von der Open Source Initiative anerkannte Open-Source-Lizenz.
    Ältere LLARS-Versionen, die vor der Einführung dieser Lizenz veröffentlicht
    wurden, hatten keine Lizenzdatei und unterliegen weiterhin den Bedingungen
    (falls vorhanden), unter denen sie bezogen wurden.

---

## Siehe auch

- [Projektstatus](project-state.md)
- [v1 Scenario API](api-v1-scenarios.md) — Exporte inkl. `citation`-Block
- [Evaluation](evaluation.md)
