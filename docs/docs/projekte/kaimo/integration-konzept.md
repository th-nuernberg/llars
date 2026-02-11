# KAIMo Integration in LLARS - Aufwandsanalyse

## Ausgangssituation

**KAIMo** (KI-Assistenz im Kinderschutz) ist ein Demonstrator/Lerntool zur Schulung von Fachkraften in der Kindeswohlgefahrdung. Der aktuelle Prototyp ist eine statische Next.js-Anwendung mit einer fest einprogrammierten Fallvignette (Fall "Malaika").

**Ziel:** KAIMo soll zu einem Lerntool fur die Aus- und Weiterbildung weiterentwickelt werden, mit der Moglichkeit weitere Fallvignetten anzulegen.

**Integration:** KAIMo wird als **Kachel in LLARS** eingebaut - analog zu den bestehenden Features wie Mail-Rating, LLM-as-Judge, RAG-Pipeline etc.

!!! success "Status (2026-02)"
    Variante B (LLARS-Integration) ist umgesetzt. Admin- und User-Panel sind produktiv nutzbar.
    Die folgenden Varianten-Abschnitte bleiben als historische Aufwandseinschaetzung erhalten.

---

## KAIMo Funktionsumfang (aktueller Prototyp)

Der Demonstrator besteht aus drei Hauptfunktionen:

1. **Fallakte/Dokumente** - Anzeige von Aktenvermerken und Dokumenten zum Fall
2. **Hinweiszuordnung** - Zuordnung von Hinweisen zu Kategorien:
   - Grundversorgung des jungen Menschen
   - Entwicklungssituation des jungen Menschen
   - Familiensituation
   - Eltern/Erziehungsberechtigte
3. **Fallbeurteilung** - Bewertung als Risiko/Ressource/Unklar + Abschlussurteil

**KI-Funktionen (im Prototyp angedacht, aber statisch):**
- Hinweiszusammenfassung
- Folgenabschatzung
- Plausibilitatsprufung

---

## Fall 1: Manueller HTML-Workflow

### Beschreibung
Dozent\*innen erstellen Fallvignetten und Textinhalte (Hinweiszusammenfassung, Folgenabschatzung, Plausibilitatsprufung) manuell in einer Word-Vorlage. Diese werden dann manuell in die HTML-Datei des Demonstrators eingepflegt.

### Aufgaben

| Aufgabe | Beschreibung | Aufwand |
|---------|--------------|---------|
| Startseiten-Erweiterung | Neue Vue-Komponente mit Fallvignetten-Auswahl als Kacheln | 4-8h |
| LLARS-Integration | Neue Route `/kaimo`, Navigation, Permission `feature:kaimo:view` | 2-4h |
| Dokumentstruktur | JSON-Schema fur Fallvignetten definieren | 2-4h |
| Statisches Hosting | JSON-Dateien pro Fall im Frontend ablegen | 1-2h |
| Fall-Loader | Komponente die JSON ladt und rendert | 4-8h |
| Styling-Anpassung | KAIMo-Design in LLARS Dark/Light Mode integrieren | 4-8h |
| **Dokumentation** | Word-Vorlage fur Dozent\*innen erstellen | 2-4h |

### Gesamtaufwand Fall 1
**19-38 Arbeitsstunden (ca. 2.5-5 Tage)**

### Vorteile
- Schnellste Implementierung
- Keine Backend-Anderungen notig
- Funktioniert sofort

### Nachteile
- Technisches Know-how fur HTML/JSON erforderlich
- Fehleranfallig bei manueller Pflege
- Keine zentrale Verwaltung
- Kein Versionierung der Falle

---

## Fall 2: LLARS-basierte Fallverwaltung

### Beschreibung
Dozent\*innen pflegen Fallvignetten und alle Textinhalte uber eine LLARS-Oberflache (Admin-Bereich). Die Daten werden in der MariaDB gespeichert und automatisch in KAIMo angezeigt.

### Aufgaben

| Aufgabe | Beschreibung | Aufwand |
|---------|--------------|---------|
| **Backend** | | |
| Datenbank-Schema | Tabellen: `kaimo_cases`, `kaimo_documents`, `kaimo_hints`, `kaimo_categories` | 4-8h |
| API-Routen | CRUD fur Falle, Dokumente, Hinweise | 8-16h |
| Permission-Integration | `feature:kaimo:view`, `feature:kaimo:edit`, `admin:kaimo:manage` | 2-4h |
| | | |
| **Frontend - Admin** | | |
| Fall-Editor | Formular zum Anlegen/Bearbeiten von Fallen | 8-16h |
| Dokumenten-Editor | Rich-Text-Editor fur Aktenvermerke | 8-12h |
| Hinweis-Editor | Kategorisierung und Zuordnung von Hinweisen | 6-10h |
| KI-Text-Editor | Eingabefelder fur Zusammenfassung, Folgenabschatzung, Plausibilitat | 4-8h |
| | | |
| **Frontend - Anwendung** | | |
| KAIMo-Startseite | Fallauswahl mit Vorschau (Vue-Komponente) | 4-8h |
| Fall-Ansicht | Dynamische Darstellung aus DB-Daten | 8-12h |
| Hinweis-Interaktion | Drag&Drop, Kategorisierung, Bewertung | 8-16h |
| Ergebnis-Speicherung | User-Bewertungen in DB speichern | 4-8h |
| | | |
| **Integration** | | |
| LLARS-Navigation | Kachel im Home-Dashboard | 2-4h |
| Styling/Theming | Dark/Light Mode Kompatibilitat | 4-8h |
| Testing | Unit + Integration Tests | 8-12h |

### Gesamtaufwand Fall 2
**78-142 Arbeitsstunden (ca. 10-18 Tage)**

### Vorteile
- Zentrale Verwaltung aller Falle
- Keine technischen Kenntnisse fur Dozent\*innen notig
- Versionierung moglich
- User-Tracking (wer hat welchen Fall bearbeitet)
- Konsistente UX mit LLARS

### Nachteile
- Deutlich hoherer Implementierungsaufwand
- KI-Texte mussen weiterhin manuell erstellt werden

---

## Fall 3: LLARS + KI-generierte Inhalte

### Beschreibung
Wie Fall 2, aber zusatzlich werden die KI-Texte (Hinweiszusammenfassung, Folgenabschatzung, Plausibilitatsprufung) automatisch durch ein hinterlegtes LLM generiert. Optional konnen Fachkrafte diese editieren.

### Aufgaben (zusatzlich zu Fall 2)

| Aufgabe | Beschreibung | Aufwand |
|---------|--------------|---------|
| **KI-Integration** | | |
| Prompt Engineering | Prompts fur Zusammenfassung, Folgenabschatzung, Plausibilitat | 8-16h |
| LLM-Service | Integration mit LiteLLM/Mistral (existiert bereits in LLARS) | 4-8h |
| Generierungs-API | Endpoint `/api/kaimo/generate/{type}` | 4-8h |
| Streaming-Support | Live-Ausgabe der LLM-Antworten via Socket.IO | 4-8h |
| | | |
| **Frontend - KI** | | |
| Generierungs-UI | "KI generieren" Button mit Ladeanimation | 4-6h |
| Streaming-Anzeige | Live-Text-Rendering im Editor | 4-6h |
| Edit-Workflow | Generierte Texte uberarbeiten und speichern | 4-8h |
| Regenerate-Funktion | Texte neu generieren lassen | 2-4h |
| | | |
| **Qualitat** | | |
| Prompt-Optimierung | Iteratives Verbessern der Prompts | 8-16h |
| Validierung | Fachliche Prufung der generierten Texte | Extern |
| Fallback-Handling | Was passiert bei LLM-Fehlern? | 2-4h |

### Gesamtaufwand Fall 3
**Fall 2 + 44-84 Stunden = 122-226 Arbeitsstunden (ca. 15-28 Tage)**

### Vorteile
- Maximale Automatisierung
- Konsistente Textqualitat
- Schnelle Erstellung neuer Falle
- Nutzung der bestehenden LLARS LLM-Infrastruktur

### Nachteile
- Hochster Implementierungsaufwand
- Qualitat der KI-Texte muss validiert werden
- Abhangigkeit von LLM-Verfugbarkeit
- Ethische Uberlegungen bei KI im Kinderschutz-Kontext

---

## LLARS-Architektur fur KAIMo (Stand 2026-02)

### Aktuelle Einbindung

```
LLARS Home Dashboard
└── KAIMo
    ├── /kaimo            - Hub / Einstieg
    ├── /kaimo/panel      - Fallubersicht
    ├── /kaimo/new        - Neuer Fall (Admin)
    ├── /kaimo/edit/:id   - Fall bearbeiten (Admin)
    └── /kaimo/:id        - Fallbearbeitung (Evaluator)
```

### Technische Integration (aktuell)

**Backend (Flask):**
```
app/routes/kaimo/
├── kaimo_admin_routes.py     # Admin-API
├── kaimo_user_routes.py      # User-API
└── __init__.py

app/services/kaimo/
├── kaimo_case_service.py
├── kaimo_document_service.py
├── kaimo_hint_service.py
├── kaimo_category_service.py
└── kaimo_export_service.py
```

**Frontend (Vue 3):**
```
llars-frontend/src/components/Kaimo/
├── KaimoHub.vue
├── KaimoPanel.vue
├── KaimoNewCase.vue
├── KaimoCaseEditor.vue
├── KaimoCase.vue
├── KaimoAssessmentView.vue
└── KaimoDocumentsView.vue
```

**Datenbank (MariaDB):**
```sql
kaimo_cases
kaimo_documents
kaimo_hints
kaimo_categories
kaimo_subcategories
kaimo_case_categories
kaimo_user_assessments
kaimo_hint_assignments
kaimo_case_shares
kaimo_ai_content
```

**Permissions:**
```
feature:kaimo:view       -- Fall ansehen
feature:kaimo:edit       -- Bewertungen abgeben
admin:kaimo:manage       -- Falle anlegen/bearbeiten
admin:kaimo:results      -- Ergebnisse einsehen
```

---

## Empfehlung

| Szenario | Empfohlener Fall | Begrundung |
|----------|------------------|------------|
| **Schneller Prototyp** | Fall 1 | Minimaler Aufwand, schnelle Demo |
| **Produktiver Einsatz** | Fall 2 | Gute Balance Aufwand/Nutzen |
| **Langfristige Vision** | Fall 3 | Maximale Automatisierung |

**Vorgeschlagene Vorgehensweise:**
1. Mit **Fall 1** starten fur schnelle Demo
2. Parallel **Fall 2** Backend entwickeln
3. Spater **Fall 3** als Erweiterung

---

## Zusammenfassung Aufwande

| Fall | Aufwand (Stunden) | Aufwand (Tage) | Komplexitat |
|------|-------------------|----------------|-------------|
| Fall 1 | 19-38h | 2.5-5 Tage | Niedrig |
| Fall 2 | 78-142h | 10-18 Tage | Mittel |
| Fall 3 | 122-226h | 15-28 Tage | Hoch |

*Hinweis: Aufwande basieren auf einem erfahrenen Entwickler. Testing, Reviews und Deployment-Zeit sind teilweise inkludiert.*

---

**Erstellt:** 25. November 2025
**Autor:** Claude Code
**Projekt:** LLARS v2.2
