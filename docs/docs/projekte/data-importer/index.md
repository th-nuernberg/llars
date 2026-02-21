# LLARS Data Importer

!!! info "AI by Design"
    Der Data Importer nutzt KI-Unterstützung um beliebige Datenformate in LLARS zu importieren.

## Übersicht

Der LLARS Data Importer ist ein universeller Import-Wizard, der Benutzer durch den gesamten Prozess führt:

**Upload → KI-Analyse → Transformation → Szenario → Benutzer → Evaluation**

## Dokumentation

| Dokument | Beschreibung |
|----------|--------------|
| [Konzept](konzept.md) | Vollständiges Projektkonzept mit Anforderungen, Architektur und Arbeitscheckliste |

## Quick Facts

| Aspekt | Details |
|--------|---------|
| **Status** | Implementiert (aktiv) |
| **Priorität** | Hoch |
| **Hauptfeature** | KI-gestützte Daten-Transformation |
| **Zielgruppe** | Forscher ohne technische Vorkenntnisse |

## Unterstützte Formate

- LLARS Native Format
- OpenAI/ChatML (messages Array)
- LMSYS Pairwise Comparison
- JSONL/NDJSON
- CSV/TSV
- Generische JSON-Listen (Fallback)
- Custom (via KI-Transformation)

## Evaluationstypen

- Rating (Sterne-Bewertung)
- Ranking (Drag & Drop Sortierung)
- Mail Rating (Konversations-Bewertung)
- Comparison (A vs B)
- Authenticity (Fake/Real)
- Labeling (Klassifikation)
