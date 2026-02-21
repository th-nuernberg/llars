# KAIMo Integration

!!! success "Status: Implementiert (Beta, Stand Februar 2026)"
    KAIMo ist in LLARS integriert und produktiv nutzbar. Admin- und User-Panel sind verfügbar.

## Übersicht

KAIMo (KI-gestützte Analyse und Modellierung) ist ein Lerntool zur Schulung von Fachkräften in der Kindeswohlgefährdung. Das System ist in LLARS mit zwei Panels umgesetzt:

- **KAIMO Admin Panel** (für Researcher): Fälle anlegen, Dokumente/Hinweise verwalten, Ergebnisse auswerten
- **KAIMO Panel** (für Evaluator): Fälle durcharbeiten, Hinweise zuordnen, Bewertungen abgeben

## Dokumentation

| Dokument | Beschreibung | Status |
|----------|--------------|--------|
| [Panel-Konzept](konzept.md) | Detailliertes Konzept mit Admin/Evaluator-Trennung | Referenz |
| [Anfrage-Einschätzung](anfrage-einschaetzung.md) | Historische Bewertung der Varianten | Archiv |
| [Integration Konzept](integration-konzept.md) | Technische Analyse + Architektur | Aktualisiert |

## Rollen und Berechtigungen

| Rolle | Panel | Berechtigungen |
|-------|-------|----------------|
| **Researcher** | Admin Panel | Fälle anlegen/bearbeiten, Ergebnisse einsehen |
| **Evaluator** | User Panel | Fälle durcharbeiten, Bewertungen abgeben |

### Permissions

```
feature:kaimo:view       # KAIMO-Bereich sehen
feature:kaimo:edit       # Bewertungen abgeben
admin:kaimo:manage       # Fälle verwalten (Admin)
admin:kaimo:results      # Ergebnisse einsehen (Admin)
```

## Kernfunktionen (aktuell)

### Admin Panel (Researcher)

1. **Fälle anlegen** - Neue Fallvignetten erstellen (Draft/Published)
2. **Dokumente verwalten** - Aktenvermerke, Berichte, Protokolle
3. **Hinweise definieren** - Hinweise + erwartete Kategorie/Rating
4. **Kategorien verwalten** - Standard-Kategorien + Subkategorien
5. **Ergebnisse analysieren** - Aggregierte Bewertungen & Exporte
6. **Teilen/Import/Export** - Fälle teilen und als JSON exportieren/importieren

### User Panel (Evaluator)

1. **Fälle durcharbeiten** - Dokumente lesen, Hinweise analysieren
2. **Hinweise zuordnen** - Kategorien + Rating (Risiko/Ressource/Unklar)
3. **Fallbeurteilung** - Finale Einschätzung mit Begründung
4. **Fortschritt** - Status und Überblick pro Fall

## Umsetzung (Stand Februar 2026)

- Backend: `/api/kaimo` Admin- und User‑Routes, Services, Modelle, Seeder
- Frontend: `/kaimo` Hub, Panel, Case‑Editor, Assessment‑View
- Berechtigungen: `feature:kaimo:*`, `admin:kaimo:*` (siehe Permissions)

## Historische Aufwandsschätzung

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

## Historische nächste Schritte (Konzeptphase)

1. Konzept-Review durch Philipp Steigerwald
2. Implementierung Phase 1 (Datenbank & Basis-API)
3. Phase 2-5 ohne KI-Integration
4. Optional später: KI-Features nachrüsten
