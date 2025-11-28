# KAIMo Integration

!!! warning "📋 Status: Konzept"
    Dieses Projekt befindet sich in der **Planungsphase**.
    Entscheidung über Implementierungsvariante steht aus.

## Übersicht

KAIMo (KI-gestützte Analyse und Modellierung) ist ein externes Tool zur Analyse von Beratungsgesprächen. Diese Dokumentation beschreibt mögliche Integrationsvarianten in LLARS.

## Dokumentation

| Dokument | Beschreibung | Status |
|----------|--------------|--------|
| [Anfrage-Einschätzung](anfrage-einschaetzung.md) | Strategische Bewertung der 3 Varianten | 📋 Entscheidung offen |
| [Integration Konzept](integration-konzept.md) | Technische Analyse mit Aufwandsschätzung | 📋 Fertig |

## Implementierungs-Varianten

| Variante | Aufwand | Beschreibung |
|----------|---------|--------------|
| A: Einfach | 19-33h | Manuelle CSV-Eingabe ohne LLARS-Integration |
| B: LLARS | 73-119h | Volle Integration mit DB und UI |
| C: KI-unterstützt | 145-226h | Volle Integration + KI-Analyse |

## Empfehlung

- **Für Studien-Demo:** Variante A (schnell umsetzbar)
- **Für nachhaltige Nutzung:** Variante B (LLARS-Integration)
