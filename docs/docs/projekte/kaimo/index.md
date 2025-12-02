# KAIMo Integration

!!! warning "Status: Konzept"
    Dieses Projekt befindet sich in der **Planungsphase**.
    Das Panel-Konzept mit Rollentrennung wurde erstellt.

## Übersicht

KAIMo (KI-gestützte Analyse und Modellierung) ist ein Lerntool zur Schulung von Fachkräften in der Kindeswohlgefährdung. Das System wird in LLARS mit zwei unterschiedlichen Panels integriert:

- **KAIMO Admin Panel** (für Researcher): Fälle anlegen, Dokumente/Hinweise verwalten, Ergebnisse auswerten
- **KAIMO Panel** (für Viewer): Fälle durcharbeiten, Hinweise zuordnen, Bewertungen abgeben

## Dokumentation

| Dokument | Beschreibung | Status |
|----------|--------------|--------|
| [Panel-Konzept](konzept.md) | **NEU:** Detailliertes Konzept mit Admin/Viewer-Trennung | In Review |
| [Anfrage-Einschätzung](anfrage-einschaetzung.md) | Strategische Bewertung der 3 Varianten | Entscheidung offen |
| [Integration Konzept](integration-konzept.md) | Technische Analyse mit Aufwandsschätzung | Fertig |

## Rollen und Berechtigungen

| Rolle | Panel | Berechtigungen |
|-------|-------|----------------|
| **Researcher** | Admin Panel | Fälle anlegen/bearbeiten, Ergebnisse einsehen |
| **Viewer** | User Panel | Fälle durcharbeiten, Bewertungen abgeben |

### Permissions

```
feature:kaimo:view       # KAIMO-Bereich sehen
feature:kaimo:edit       # Bewertungen abgeben
admin:kaimo:manage       # Fälle verwalten (Admin)
admin:kaimo:results      # Ergebnisse einsehen (Admin)
```

## Kernfunktionen

### Admin Panel (Researcher)

1. **Fälle anlegen** - Neue Fallvignetten erstellen
2. **Dokumente verwalten** - Aktenvermerke, Berichte, Protokolle
3. **Hinweise definieren** - Hinweise aus Dokumenten extrahieren und Kategorien zuordnen
4. **Musterlösung hinterlegen** - Erwartete Zuordnungen für Auswertung
5. **Ergebnisse analysieren** - Aggregierte Bewertungen aller Fachkräfte

### User Panel (Viewer)

1. **Fälle durcharbeiten** - Dokumente lesen, Hinweise analysieren
2. **Hinweise zuordnen** - Drag & Drop in Kategorien
3. **Bewertung abgeben** - Risiko/Ressource/Unklar für jeden Hinweis
4. **Fallbeurteilung** - Finale Einschätzung mit Begründung

## Geschätzter Aufwand

| Komponente | Aufwand |
|------------|---------|
| Datenbank & API | 8-12h |
| Admin Panel | 16-24h |
| User Panel | 20-30h |
| Bewertung & Ergebnisse | 24-36h |
| **Gesamt** | **68-102h** |

!!! info "KI-Integration vorbereitet"
    Die Infrastruktur (DB-Schema, API) ist für spätere KI-Integration vorbereitet.
    Zusatzaufwand bei Bedarf: 16-24h

## Nächste Schritte

1. Konzept-Review durch Philipp Steigerwald
2. Implementierung Phase 1 (Datenbank & Basis-API)
3. Phase 2-5 ohne KI-Integration
4. Optional später: KI-Features nachrüsten
