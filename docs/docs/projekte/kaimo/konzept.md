# KAIMO - Panel-Konzept mit Rollentrennung

!!! warning "Status: Konzept"
    Dieses Projekt befindet sich in der **Konzeptphase**.
    Das Design wird erarbeitet.

**Erstellt:** 2025-11-29
**Autor:** Claude Code
**Version:** 1.2 (basierend auf KAIMo_Final Prototyp)

---

## Ziel

KAIMO (KI-gestützte Analyse und Modellierung) wird in LLARS als interaktives Lerntool integriert. Das System unterscheidet zwischen **Researcher (Admin Panel)** und **Evaluator (User Panel)**, wobei Researcher neue Fälle anlegen und verwalten können, während Evaluator diese durcharbeiten und bewerten.

!!! info "KI-Integration: Vorbereitet, nicht implementiert"
    Die Datenbank und API sind für spätere KI-Integration vorbereitet (Tabelle `kaimo_ai_content`, API-Endpoints).
    **Phase 1-5 werden ohne KI-Funktionalität umgesetzt.** Die KI-Texte (Zusammenfassung, Folgenabschätzung, Plausibilitätsprüfung) werden manuell durch Researcher eingegeben.

**Kernidee:**
```
Researcher: Fall anlegen → Dokumente/Hinweise definieren → Fachkräfte zuweisen
Evaluator:     Fall auswählen → Hinweise zuordnen → Bewertung abgeben → Ergebnis sehen
```

---

## Rollen und Berechtigungen

### Rollenmodell

| Rolle | Panel | Beschreibung |
|-------|-------|--------------|
| **Researcher** | KAIMO Admin Panel | Kann Fälle anlegen, bearbeiten, löschen und Ergebnisse auswerten |
| **Evaluator** | KAIMO Panel | Kann zugewiesene Fälle durcharbeiten und Bewertungen abgeben |

### Permission-System

| Permission | Beschreibung | Researcher | Evaluator |
|------------|--------------|:----------:|:------:|
| `feature:kaimo:view` | KAIMO-Bereich sehen, Fälle durcharbeiten | ✓ | ✓ |
| `feature:kaimo:edit` | Eigene Bewertungen abgeben | ✓ | ✓ |
| `admin:kaimo:manage` | Fälle anlegen/bearbeiten/löschen, Ergebnisse einsehen | ✓ | ✗ |
| `admin:kaimo:results` | Aggregierte Ergebnisse und Statistiken einsehen | ✓ | ✗ |

### Rollen-Mapping

```python
# In app/db/db.py - Rollendefinition erweitern

KAIMO_PERMISSIONS = {
    'admin': [
        'feature:kaimo:view',
        'feature:kaimo:edit',
        'admin:kaimo:manage',
        'admin:kaimo:results'
    ],
    'researcher': [
        'feature:kaimo:view',
        'feature:kaimo:edit',
        'admin:kaimo:manage',
        'admin:kaimo:results'
    ],
    'evaluator': [
        'feature:kaimo:view',
        'feature:kaimo:edit'
    ]
}
```

---

## Anforderungen

### Funktionale Anforderungen

| ID | Anforderung | Priorität | Panel |
|----|-------------|-----------|-------|
| F01 | Researcher kann neuen Fall (Fallvignette) anlegen | Hoch | Admin |
| F02 | Researcher kann Dokumente/Aktenvermerke zum Fall hinzufügen | Hoch | Admin |
| F03 | Researcher kann Hinweise definieren und Kategorien zuordnen | Hoch | Admin |
| F04 | Researcher kann Texte (Zusammenfassung, Folgenabschätzung) manuell eingeben | Hoch | Admin |
| F05 | Researcher kann Fall für bestimmte Benutzer/Gruppen freigeben | Mittel | Admin |
| F06 | Evaluator sieht Liste der freigegebenen Fälle | Hoch | User |
| F07 | Evaluator kann Hinweise in Kategorien zuordnen (Drag & Drop) | Hoch | User |
| F08 | Evaluator kann Hinweise als Risiko/Ressource/Unklar bewerten | Hoch | User |
| F09 | Evaluator gibt finale Fallbeurteilung ab | Hoch | User |
| F10 | Researcher sieht aggregierte Ergebnisse aller Bewertungen | Mittel | Admin |
| F11 | Researcher kann Musterlösung hinterlegen und Abweichungen analysieren | Niedrig | Admin |

### Nicht-funktionale Anforderungen

| ID | Anforderung | Priorität |
|----|-------------|-----------|
| NF01 | Performance: Flüssige Drag & Drop Interaktion | Hoch |
| NF02 | Usability: Intuitive Benutzerführung für Fachkräfte ohne IT-Kenntnisse | Hoch |
| NF03 | Sicherheit: Strikte Rollentrennung, keine Einsicht in fremde Bewertungen | Hoch |
| NF04 | Responsivität: Mobile-optimierte Ansicht für Evaluator-Panel | Mittel |

---

## Datenbank-Design

### Neue Tabellen

#### `kaimo_cases` (Fallvignetten)

| Spalte | Typ | Nullable | Beschreibung |
|--------|-----|----------|--------------|
| id | INT (PK) | Nein | Auto-Increment Primary Key |
| name | VARCHAR(100) | Nein | Interner Name (URL-safe) |
| display_name | VARCHAR(255) | Nein | Anzeigename (z.B. "Fall Malaika") |
| description | TEXT | Ja | Kurzbeschreibung des Falls |
| status | ENUM | Nein | 'draft', 'published', 'archived' |
| icon | VARCHAR(10) | Ja | Emoji für Anzeige |
| color | VARCHAR(20) | Ja | Akzentfarbe (Hex) |
| created_by | VARCHAR(255) | Nein | Username des Erstellers |
| created_at | DATETIME | Nein | Erstellungszeitpunkt |
| updated_at | DATETIME | Ja | Letzte Änderung |
| published_at | DATETIME | Ja | Veröffentlichungszeitpunkt |

#### `kaimo_documents` (Aktenvermerke/Dokumente)

| Spalte | Typ | Nullable | Beschreibung |
|--------|-----|----------|--------------|
| id | INT (PK) | Nein | Auto-Increment Primary Key |
| case_id | INT (FK) | Nein | Referenz auf kaimo_cases |
| title | VARCHAR(255) | Nein | Dokumenttitel |
| content | TEXT | Nein | Inhalt (Markdown/HTML) |
| document_type | ENUM | Nein | 'aktenvermerk', 'bericht', 'protokoll', 'sonstiges' |
| document_date | DATE | Ja | Datum des Dokuments (fiktiv) |
| sort_order | INT | Nein | Reihenfolge der Anzeige |
| created_at | DATETIME | Nein | Erstellungszeitpunkt |

#### `kaimo_categories` (Bewertungskategorien)

| Spalte | Typ | Nullable | Beschreibung |
|--------|-----|----------|--------------|
| id | INT (PK) | Nein | Auto-Increment Primary Key |
| name | VARCHAR(100) | Nein | Interner Name |
| display_name | VARCHAR(255) | Nein | Anzeigename |
| description | TEXT | Ja | Beschreibung der Kategorie |
| icon | VARCHAR(10) | Ja | Kategorie-Icon |
| color | VARCHAR(20) | Ja | Akzentfarbe |
| sort_order | INT | Nein | Reihenfolge |
| is_default | BOOLEAN | Nein | Standard-Kategorien für neue Fälle |

**Standard-Kategorien (aus KAIMo-Prototyp):**

1. **Grundversorgung des jungen Menschen**
   - Körperliche Gesundheit des Kindes
   - Psychische Gesundheit des Kindes
   - Medikamenten- und Substanzkonsum des Kindes
   - Aufsicht / Betreuungssituation des Kindes

2. **Entwicklungssituation des jungen Menschen**
   - Biografie des Kindes (inkl. Maßnahmen der Jugendhilfe)
   - Sozialverhalten / Sozialkontakte des Kindes
   - Sexualentwicklung des Kindes
   - Bildung- und Leistungsbereich des Kindes

3. **Familiensituation**
   - Wohnsituation
   - Wirtschaftliche Situation (inkl. Erwerbstätigkeit)
   - Familiäre Beziehungen (inkl. Häusliche Gewalt)

4. **Eltern / Erziehungsberechtigte**
   - Biografie der Erziehungsberechtigten
   - Gesundheit der Erziehungsberechtigten
   - Wohlbefinden der Erziehungsberechtigten
   - Sozialverhalten / Sozialkontakte der Erziehungsberechtigten

#### `kaimo_subcategories` (Unterkategorien für Bewertungsmatrix)

| Spalte | Typ | Nullable | Beschreibung |
|--------|-----|----------|--------------|
| id | INT (PK) | Nein | Auto-Increment Primary Key |
| category_id | INT (FK) | Nein | Referenz auf kaimo_categories |
| name | VARCHAR(100) | Nein | Interner Name |
| display_name | VARCHAR(255) | Nein | Anzeigename |
| description | TEXT | Ja | Beschreibung |
| sort_order | INT | Nein | Reihenfolge innerhalb der Kategorie |
| is_default | BOOLEAN | Nein | Standard-Unterkategorien |

#### `kaimo_hints` (Hinweise aus Dokumenten)

| Spalte | Typ | Nullable | Beschreibung |
|--------|-----|----------|--------------|
| id | INT (PK) | Nein | Auto-Increment Primary Key |
| case_id | INT (FK) | Nein | Referenz auf kaimo_cases |
| document_id | INT (FK) | Ja | Referenz auf kaimo_documents (Quelle) |
| content | TEXT | Nein | Hinweistext |
| expected_category_id | INT (FK) | Ja | Erwartete Hauptkategorie (Musterlösung) |
| expected_subcategory_id | INT (FK) | Ja | Erwartete Unterkategorie (Musterlösung) |
| expected_rating | ENUM | Ja | 'risk', 'resource', 'unclear' (Musterlösung) |
| sort_order | INT | Nein | Reihenfolge |
| created_at | DATETIME | Nein | Erstellungszeitpunkt |

#### `kaimo_case_categories` (n:m Fall ↔ Kategorien)

| Spalte | Typ | Nullable | Beschreibung |
|--------|-----|----------|--------------|
| id | INT (PK) | Nein | Auto-Increment Primary Key |
| case_id | INT (FK) | Nein | Referenz auf kaimo_cases |
| category_id | INT (FK) | Nein | Referenz auf kaimo_categories |
| sort_order | INT | Nein | Reihenfolge im Fall |

#### `kaimo_ai_content` (Texte - KI-Vorbereitung)

!!! note "KI-Vorbereitung"
    Diese Tabelle ist für spätere KI-Integration vorbereitet. In Phase 1-5 werden alle Inhalte manuell eingegeben (`is_generated = false`).

| Spalte | Typ | Nullable | Beschreibung |
|--------|-----|----------|--------------|
| id | INT (PK) | Nein | Auto-Increment Primary Key |
| case_id | INT (FK) | Nein | Referenz auf kaimo_cases |
| content_type | ENUM | Nein | 'summary', 'consequences', 'plausibility' |
| content | TEXT | Nein | Inhalt |
| is_generated | BOOLEAN | Nein | Manuell (false) oder KI-generiert (true, für später) |
| generated_at | DATETIME | Ja | Generierungszeitpunkt (für KI, später) |
| created_at | DATETIME | Nein | Erstellungszeitpunkt |
| updated_at | DATETIME | Ja | Letzte Bearbeitung |

#### `kaimo_user_assessments` (Benutzer-Bewertungen)

| Spalte | Typ | Nullable | Beschreibung |
|--------|-----|----------|--------------|
| id | INT (PK) | Nein | Auto-Increment Primary Key |
| case_id | INT (FK) | Nein | Referenz auf kaimo_cases |
| user_id | VARCHAR(255) | Nein | Authentik User-ID |
| username | VARCHAR(255) | Nein | Username für Anzeige |
| status | ENUM | Nein | 'in_progress', 'completed' |
| final_verdict | ENUM | Ja | 'inconclusive', 'not_endangered', 'endangered' |
| final_comment | TEXT | Ja | Begründung der Bewertung |
| started_at | DATETIME | Nein | Beginn der Bearbeitung |
| completed_at | DATETIME | Ja | Abschluss der Bearbeitung |
| duration_seconds | INT | Ja | Bearbeitungsdauer |

**Finale Urteilsoptionen (wie im Prototyp):**

- `inconclusive` = "Eine abschließende Bewertung ist nicht möglich"
- `not_endangered` = "Das Wohl von [Kind] ist nicht gefährdet"
- `endangered` = "Das Wohl von [Kind] ist gefährdet"

#### `kaimo_hint_assignments` (Hinweiszuordnungen durch User)

| Spalte | Typ | Nullable | Beschreibung |
|--------|-----|----------|--------------|
| id | INT (PK) | Nein | Auto-Increment Primary Key |
| assessment_id | INT (FK) | Nein | Referenz auf kaimo_user_assessments |
| hint_id | INT (FK) | Nein | Referenz auf kaimo_hints |
| assigned_category_id | INT (FK) | Ja | Zugewiesene Hauptkategorie |
| assigned_subcategory_id | INT (FK) | Ja | Zugewiesene Unterkategorie |
| rating | ENUM | Ja | 'risk', 'resource', 'unclear' |
| assigned_at | DATETIME | Nein | Zeitpunkt der Zuordnung |

#### `kaimo_case_permissions` (Fallfreigaben)

| Spalte | Typ | Nullable | Beschreibung |
|--------|-----|----------|--------------|
| id | INT (PK) | Nein | Auto-Increment Primary Key |
| case_id | INT (FK) | Nein | Referenz auf kaimo_cases |
| user_id | VARCHAR(255) | Ja | Einzelner Benutzer (oder NULL für Gruppe) |
| group_name | VARCHAR(100) | Ja | Gruppenname (oder NULL für Einzeluser) |
| granted_by | VARCHAR(255) | Nein | Wer hat freigegeben |
| granted_at | DATETIME | Nein | Freigabezeitpunkt |

### Relationen-Diagramm

```
                    ┌─────────────────────┐
                    │    kaimo_cases      │
                    │  (Fallvignetten)    │
                    └─────────┬───────────┘
                              │
    ┌───────────┬─────────────┼─────────────┬──────────────┬──────────────┐
    │           │             │             │              │              │
    ▼           ▼             ▼             ▼              ▼              ▼
┌────────┐ ┌────────┐ ┌──────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐
│kaimo_  │ │kaimo_  │ │kaimo_case_   │ │kaimo_ai_   │ │kaimo_case_ │ │kaimo_    │
│docs    │ │hints   │ │categories    │ │content     │ │permissions │ │user_     │
│        │ │        │ │(n:m)         │ │(KI-ready)  │ │            │ │assess-   │
└────────┘ └───┬────┘ └──────┬───────┘ └────────────┘ └────────────┘ │ments     │
               │             │                                       └─────┬────┘
               │             ▼                                             │
               │    ┌─────────────────┐                                    │
               │    │kaimo_categories │                                    │
               │    └────────┬────────┘                                    │
               │             │                                             │
               │             ▼                                             │
               │    ┌─────────────────┐                                    │
               │    │kaimo_           │                                    │
               │    │subcategories    │◄───────────────────────────────────┤
               │    └─────────────────┘                                    │
               │                                                           │
               └───────────────────────────────────────────────────────────┤
                                                                           │
                                                              ┌────────────┴───────────┐
                                                              │ kaimo_hint_assignments │
                                                              │ (User-Zuordnungen)     │
                                                              └────────────────────────┘
```

---

## API-Design

### KAIMO Admin Panel API

#### `GET /api/kaimo/admin/cases`

**Beschreibung:** Liste aller Fälle für Researcher

**Permission:** `admin:kaimo:manage`

**Response:**
```json
{
  "success": true,
  "cases": [
    {
      "id": 1,
      "name": "fall-malaika",
      "display_name": "Fall Malaika",
      "description": "Kindeswohlgefährdung bei Mädchen (8 Jahre)",
      "status": "published",
      "icon": "👧",
      "color": "#e91e63",
      "document_count": 5,
      "hint_count": 12,
      "assessment_count": 8,
      "created_by": "researcher1",
      "created_at": "2025-11-29T10:00:00Z",
      "published_at": "2025-11-29T12:00:00Z"
    }
  ],
  "total": 1
}
```

---

#### `POST /api/kaimo/admin/cases`

**Beschreibung:** Neuen Fall anlegen

**Permission:** `admin:kaimo:manage`

**Request:**
```json
{
  "name": "fall-malaika",
  "display_name": "Fall Malaika",
  "description": "Kindeswohlgefährdung bei Mädchen (8 Jahre)",
  "icon": "👧",
  "color": "#e91e63",
  "categories": [1, 2, 3, 4]
}
```

**Response:**
```json
{
  "success": true,
  "case": {
    "id": 1,
    "name": "fall-malaika",
    "display_name": "Fall Malaika",
    "status": "draft"
  }
}
```

---

#### `PUT /api/kaimo/admin/cases/<id>`

**Beschreibung:** Fall bearbeiten

**Permission:** `admin:kaimo:manage`

---

#### `DELETE /api/kaimo/admin/cases/<id>`

**Beschreibung:** Fall löschen (nur wenn keine Assessments vorhanden oder force=true)

**Permission:** `admin:kaimo:manage`

---

#### `POST /api/kaimo/admin/cases/<id>/publish`

**Beschreibung:** Fall veröffentlichen

**Permission:** `admin:kaimo:manage`

---

#### `POST /api/kaimo/admin/cases/<id>/documents`

**Beschreibung:** Dokument zum Fall hinzufügen

**Permission:** `admin:kaimo:manage`

**Request:**
```json
{
  "title": "Aktenvermerk vom 15.03.2024",
  "content": "**Hausbesuch bei Familie M.**\n\nAnwesend waren...",
  "document_type": "aktenvermerk",
  "document_date": "2024-03-15"
}
```

---

#### `POST /api/kaimo/admin/cases/<id>/hints`

**Beschreibung:** Hinweis zum Fall hinzufügen

**Permission:** `admin:kaimo:manage`

**Request:**
```json
{
  "content": "Kind zeigt Anzeichen von Unterernährung",
  "document_id": 1,
  "expected_category_id": 1,
  "expected_rating": "risk"
}
```

---

#### `POST /api/kaimo/admin/cases/<id>/content`

**Beschreibung:** Textinhalt (Zusammenfassung, Folgenabschätzung, Plausibilität) manuell setzen

**Permission:** `admin:kaimo:manage`

**Request:**
```json
{
  "content_type": "summary",
  "content": "Der Fall zeigt mehrere Anzeichen von..."
}
```

!!! note "KI-Vorbereitung"
    Der API-Endpoint ist für spätere KI-Generierung vorbereitet. Ein `generate: true` Parameter kann später hinzugefügt werden.

---

#### `GET /api/kaimo/admin/cases/<id>/results`

**Beschreibung:** Aggregierte Ergebnisse eines Falls

**Permission:** `admin:kaimo:results`

**Response:**
```json
{
  "success": true,
  "case_id": 1,
  "total_assessments": 8,
  "completed_assessments": 6,
  "average_duration_seconds": 1250,
  "final_ratings": {
    "risk": 4,
    "resource": 1,
    "unclear": 1
  },
  "hint_accuracy": {
    "correct_category": 0.78,
    "correct_rating": 0.65
  },
  "per_hint_results": [
    {
      "hint_id": 1,
      "hint_content": "Kind zeigt Anzeichen...",
      "expected_category": "Grundversorgung",
      "expected_rating": "risk",
      "assignments": {
        "Grundversorgung": 5,
        "Entwicklungssituation": 1
      },
      "ratings": {
        "risk": 5,
        "unclear": 1
      }
    }
  ]
}
```

---

### KAIMO User Panel API

#### `GET /api/kaimo/cases`

**Beschreibung:** Liste der für den User freigegebenen Fälle

**Permission:** `feature:kaimo:view`

**Response:**
```json
{
  "success": true,
  "cases": [
    {
      "id": 1,
      "display_name": "Fall Malaika",
      "description": "Kindeswohlgefährdung bei Mädchen (8 Jahre)",
      "icon": "👧",
      "color": "#e91e63",
      "document_count": 5,
      "hint_count": 12,
      "my_status": "not_started",
      "estimated_duration_minutes": 30
    }
  ]
}
```

---

#### `GET /api/kaimo/cases/<id>`

**Beschreibung:** Fall-Details für Bearbeitung

**Permission:** `feature:kaimo:view`

**Response:**
```json
{
  "success": true,
  "case": {
    "id": 1,
    "display_name": "Fall Malaika",
    "description": "...",
    "documents": [
      {
        "id": 1,
        "title": "Aktenvermerk vom 15.03.2024",
        "content": "...",
        "document_type": "aktenvermerk",
        "document_date": "2024-03-15"
      }
    ],
    "categories": [
      {
        "id": 1,
        "display_name": "Grundversorgung",
        "icon": "🍎",
        "color": "#4caf50"
      }
    ],
    "hints": [
      {
        "id": 1,
        "content": "Kind zeigt Anzeichen von Unterernährung",
        "source_document_id": 1
      }
    ]
  },
  "my_assessment": {
    "id": 1,
    "status": "in_progress",
    "hint_assignments": [
      {
        "hint_id": 1,
        "assigned_category_id": 1,
        "rating": "risk"
      }
    ]
  }
}
```

---

#### `POST /api/kaimo/cases/<id>/start`

**Beschreibung:** Bearbeitung eines Falls starten

**Permission:** `feature:kaimo:edit`

**Response:**
```json
{
  "success": true,
  "assessment_id": 1,
  "started_at": "2025-11-29T14:00:00Z"
}
```

---

#### `PUT /api/kaimo/assessments/<id>/hints/<hint_id>`

**Beschreibung:** Hinweis-Zuordnung speichern

**Permission:** `feature:kaimo:edit`

**Request:**
```json
{
  "assigned_category_id": 1,
  "rating": "risk"
}
```

---

#### `POST /api/kaimo/assessments/<id>/complete`

**Beschreibung:** Bewertung abschließen

**Permission:** `feature:kaimo:edit`

**Request:**
```json
{
  "final_rating": "risk",
  "final_comment": "Aufgrund der mehrfachen Hinweise auf..."
}
```

---

## Frontend-Design

### Komponenten-Struktur

```
llars-frontend/src/components/KAIMo/
├── KAIMoOverview.vue              # Fallübersicht (Kacheln)
├── KAIMoCase.vue                  # Haupt-Container mit 3 Bereichen
│
├── case/                          # 3 Hauptbereiche (wie Prototyp)
│   ├── KAIMoDocuments.vue         # Bereich 1: Fallakte/Dokumente
│   ├── KAIMoDiagram.vue           # Bereich 2: Hinweiszuordnung (Diagramm)
│   ├── KAIMoAssessment.vue        # Bereich 3: Fallbeurteilung (Matrix + Urteil)
│   ├── KAIMoSidebar.vue           # Linke Sidebar mit 3 Icons
│   └── KAIMoHintAssignment.vue    # Dialog für Hinweis-Zuordnung
│
├── documents/
│   ├── KAIMoDocumentList.vue      # Dokumentenliste (links)
│   ├── KAIMoDocumentViewer.vue    # Dokumenteninhalt (rechts)
│   └── KAIMoDocumentSearch.vue    # Suche + Filter
│
├── assessment/
│   ├── KAIMoMatrix.vue            # Bewertungsmatrix (Kategorien × Unterkategorien)
│   ├── KAIMoMatrixRow.vue         # Eine Zeile in der Matrix
│   ├── KAIMoFinalVerdict.vue      # Finales Urteil (3 Optionen)
│   └── KAIMoResults.vue           # Ergebnis-Anzeige (nach Abschluss)
│
├── admin/
│   ├── KAIMoAdminOverview.vue     # Admin Dashboard
│   ├── KAIMoCaseEditor.vue        # Fall erstellen/bearbeiten
│   ├── KAIMoDocumentEditor.vue    # Dokumente verwalten
│   ├── KAIMoHintEditor.vue        # Hinweise definieren
│   ├── KAIMoContentEditor.vue     # Texte verwalten (KI-ready)
│   ├── KAIMoCasePermissions.vue   # Freigaben verwalten
│   └── KAIMoCaseResults.vue       # Aggregierte Ergebnisse
│
└── shared/
    ├── KAIMoCategoryCard.vue      # Kategorie-Karte (im Diagramm)
    ├── KAIMoHintCard.vue          # Hinweis-Karte (draggable)
    ├── KAIMoRatingButtons.vue     # Risiko/Ressource/Unklar Buttons
    └── KAIMoProgressBar.vue       # Fortschrittsanzeige
```

---

### User Panel - Fallübersicht

```
┌─────────────────────────────────────────────────────────────────────┐
│  KAIMO - Fallvignetten                                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Verfügbare Fälle                                                   │
│                                                                      │
│  ┌──────────────────────┐  ┌──────────────────────┐                 │
│  │ 👧 Fall Malaika       │  │ 👦 Fall Tim           │                 │
│  │                      │  │                      │                 │
│  │ Kindeswohlgefährdung │  │ Vernachlässigung im  │                 │
│  │ bei Mädchen (8 J.)   │  │ häuslichen Umfeld    │                 │
│  │                      │  │                      │                 │
│  │ 📄 5 Dokumente        │  │ 📄 3 Dokumente        │                 │
│  │ 💡 22 Hinweise        │  │ 💡 15 Hinweise        │                 │
│  │ ⏱️ ca. 30 Min.        │  │ ⏱️ ca. 20 Min.        │                 │
│  │                      │  │                      │                 │
│  │ Status: Nicht begonnen│ │ Status: In Bearbeitung│                │
│  │                      │  │ ████████░░ 80%       │                 │
│  │                      │  │                      │                 │
│  │ [Fall starten]       │  │ [Fortsetzen]         │                 │
│  └──────────────────────┘  └──────────────────────┘                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

### User Panel - 3 Hauptbereiche (wie KAIMo Prototyp)

Die Fall-Bearbeitung erfolgt in **3 Hauptbereichen**, erreichbar über die linke Sidebar:

#### Bereich 1: Fallakte/Dokumente

```
┌────┬──────────────────────────────────────────────────────────────────┐
│    │  🔍 Textsuche        [Merkmale ▼] [Akteure ▼]                   │
│ 📄 ├──────────────────────────────────────────────────────────────────┤
│    │                                                                  │
│ 📊 │  ┌────────────────┐  ┌────────────────────────────────────────┐ │
│    │  │ DOKUMENTE      │  │ Mitteilung über eine mögliche          │ │
│ ⚖️ │  │                │  │ Kindeswohlgefährdung                   │ │
│    │  │ ▶ Mitteilung   │  │                        Fr, 03.02.2023  │ │
│    │  │   03.02.2023   │  │                                        │ │
│    │  │                │  │ Art der Meldung:                       │ │
│    │  │ ○ Telefonat    │  │ Anruf im Jugendamt                     │ │
│    │  │   Lehrerin     │  │                                        │ │
│    │  │   06.02.2023   │  │ Angaben zum Kind:                      │ │
│    │  │                │  │ Malaika Boukari, 8 Jahre alt,          │ │
│    │  │ ○ Hausbesuch   │  │ wohnhaft: Regenbogenstraße 7...        │ │
│    │  │   07.02.2023   │  │                                        │ │
│    │  │                │  │ Angaben zur Mutter:                    │ │
│    │  │ ○ Gespräch     │  │ Inaya Boukari, 43 Jahre alt...         │ │
│    │  │   Dienststelle │  │                                        │ │
│    │  │   16.02.2023   │  │ Angaben zum Sachverhalt:               │ │
│    │  │                │  │ Die Tochter der Anruferin und          │ │
│    │  │                │  │ Malaika würden gemeinsam...            │ │
│    │  └────────────────┘  └────────────────────────────────────────┘ │
│    │                                                                  │
└────┴──────────────────────────────────────────────────────────────────┘
```

#### Bereich 2: Hinweiszuordnung (Diagramm-Ansicht)

```
┌────┬──────────────────────────────────────────────────────────────────┐
│    │                                                                  │
│ 📄 │     ┌─────────────────────┐         ┌─────────────────────┐     │
│    │     │ Grundversorgung     │         │ Familiensituation   │     │
│ 📊 │     │ 8 Offene Hinweise   │         │ 6 Offene Hinweise   │     │
│    │     │ 🔴 0  🟢 0  ⚪ 0    │         │ 🔴 0  🟢 0  ⚪ 0    │     │
│ ⚖️ │     └─────────────────────┘         └─────────────────────┘     │
│    │                                                                  │
│    │                      ┌─────────┐                                │
│    │                      │ Malaika │                                │
│    │                      └─────────┘                                │
│    │                                                                  │
│    │     ┌─────────────────────┐         ┌─────────────────────┐     │
│    │     │ Entwicklung         │         │ Eltern              │     │
│    │     │ 5 Offene Hinweise   │         │ 3 Offene Hinweise   │     │
│    │     │ 🔴 0  🟢 0  ⚪ 0    │         │ 🔴 0  🟢 0  ⚪ 0    │     │
│    │     └─────────────────────┘         └─────────────────────┘     │
│    │                                                                  │
└────┴──────────────────────────────────────────────────────────────────┘
```

Klick auf Kategorie öffnet Detail-Ansicht mit Hinweisen zum Zuordnen.

#### Bereich 3: Fallbeurteilung (Matrix + Urteil)

```
┌────┬──────────────────────────────────────────────────────────────────┐
│    │  Abschließende Fallbeurteilung                     [📂 Akte]    │
│ 📄 ├──────────────────────────────────────────────────────────────────┤
│    │                                                                  │
│ 📊 │  ┌─────────────────────────────────────┐  ┌──────────────────┐  │
│    │  │ BEWERTUNGSMATRIX                    │  │ URTEIL           │  │
│ ⚖️ │  │                                     │  │                  │  │
│    │  │           │ Risiko │ Ressource │ ?  │  │ Wählen Sie Ihr   │  │
│    │  │ ──────────┼────────┼───────────┼────│  │ Urteil:          │  │
│    │  │ GRUNDVERSORGUNG                     │  │                  │  │
│    │  │ Körperl.  │   ●    │           │    │  │ ○ Bewertung      │  │
│    │  │ Gesundh.  │        │           │    │  │   nicht möglich  │  │
│    │  │ Psych.    │        │     ●     │    │  │                  │  │
│    │  │ Gesundh.  │        │           │    │  │ ○ Wohl nicht     │  │
│    │  │ Aufsicht  │        │           │  ● │  │   gefährdet      │  │
│    │  │ ──────────┼────────┼───────────┼────│  │                  │  │
│    │  │ ENTWICKLUNG                         │  │ ○ Wohl           │  │
│    │  │ Biografie │   ●    │           │    │  │   gefährdet      │  │
│    │  │ Sozialv.  │        │     ●     │    │  │                  │  │
│    │  │ ...       │        │           │    │  │                  │  │
│    │  │                                     │  │ [Abschließen]    │  │
│    │  └─────────────────────────────────────┘  └──────────────────┘  │
│    │                                                                  │
└────┴──────────────────────────────────────────────────────────────────┘
```

---

### Admin Panel - Übersicht

```
┌─────────────────────────────────────────────────────────────────────┐
│  KAIMO Admin                                      [+ Neuer Fall]    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐        │
│  │ 3          │ │ 2          │ │ 1          │ │ 15         │        │
│  │ Fälle      │ │ Veröffent- │ │ Entwurf    │ │ Abgeschl.  │        │
│  │ gesamt     │ │ licht      │ │            │ │ Bewertungen│        │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘        │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Name          │ Status      │ Dokumente │ Bewertungen │ Aktionen│ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │ 👧 Malaika     │ ✓ Published │ 5         │ 8/10 (80%)  │ ⚙️ 📊 🗑️ │ │
│  │ 👦 Tim         │ ✓ Published │ 3         │ 3/10 (30%)  │ ⚙️ 📊 🗑️ │ │
│  │ 👶 Leon        │ 📝 Draft    │ 2         │ -           │ ⚙️ 🗑️    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  Legende: ⚙️ Bearbeiten  📊 Ergebnisse  🗑️ Löschen                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Admin Panel - Fall-Editor

```
┌─────────────────────────────────────────────────────────────────────┐
│  ← Zurück                     Fall bearbeiten: Malaika              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Grunddaten │ Dokumente │ Hinweise │ Texte │ Freigaben │ Ergebnisse ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  GRUNDDATEN                                                          │
│                                                                      │
│  Name (intern):                          Icon:                      │
│  ┌────────────────────────────────┐      ┌──────┐                   │
│  │ fall-malaika                   │      │ 👧   │                   │
│  └────────────────────────────────┘      └──────┘                   │
│                                                                      │
│  Anzeigename:                            Farbe:                     │
│  ┌────────────────────────────────┐      ┌──────┐                   │
│  │ Fall Malaika                   │      │██████│ #e91e63           │
│  └────────────────────────────────┘      └──────┘                   │
│                                                                      │
│  Beschreibung:                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Kindeswohlgefährdung bei einem 8-jährigen Mädchen.             ││
│  │ Der Fall umfasst Aspekte von Vernachlässigung und...           ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  Kategorien für diesen Fall:                                         │
│  ☑ Grundversorgung  ☑ Entwicklung  ☑ Familie  ☑ Eltern             │
│                                                                      │
│  Status: 📝 Entwurf                                                  │
│                                                                      │
│                    [Speichern]     [Veröffentlichen]                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Routing

### User Panel Routes

| Route | Komponente | Permission |
|-------|------------|------------|
| `/kaimo` | KAIMoOverview | `feature:kaimo:view` |
| `/kaimo/:id` | KAIMoCase | `feature:kaimo:view` |
| `/kaimo/:id/results` | KAIMoResults | `feature:kaimo:view` |

### Admin Panel Routes

| Route | Komponente | Permission |
|-------|------------|------------|
| `/admin/kaimo` | KAIMoAdminOverview | `admin:kaimo:manage` |
| `/admin/kaimo/new` | KAIMoCaseEditor | `admin:kaimo:manage` |
| `/admin/kaimo/:id/edit` | KAIMoCaseEditor | `admin:kaimo:manage` |
| `/admin/kaimo/:id/results` | KAIMoCaseResults | `admin:kaimo:results` |

---

## Implementierungsplan

### Phase 1: Datenbank & Basis-API (Priorität: Hoch)

- [ ] Datenbank-Tabellen erstellen (Migration)
- [ ] SQLAlchemy-Models definieren
- [ ] Standard-Kategorien initial befüllen
- [ ] Permission-Keys in DB einfügen
- [ ] Basis-CRUD API für Cases

**Aufwand:** 8-12h

### Phase 2: Admin Panel - Fall-Verwaltung (Priorität: Hoch)

- [ ] KAIMoAdminOverview.vue
- [ ] KAIMoCaseEditor.vue (Grunddaten)
- [ ] KAIMoDocumentEditor.vue
- [ ] KAIMoHintEditor.vue
- [ ] API-Endpoints für Dokumente und Hinweise

**Aufwand:** 16-24h

### Phase 3: User Panel - Fall-Bearbeitung (Priorität: Hoch)

- [ ] KAIMoOverview.vue (Fallübersicht)
- [ ] KAIMoCase.vue (Hauptansicht)
- [ ] KAIMoHintBoard.vue (Drag & Drop)
- [ ] KAIMoDocumentViewer.vue
- [ ] API für Assessments und Zuordnungen

**Aufwand:** 20-30h

### Phase 4: Bewertung & Abschluss (Priorität: Hoch)

- [ ] KAIMoRatingPanel.vue
- [ ] KAIMoFinalAssessment.vue
- [ ] KAIMoResults.vue
- [ ] API für Finalisierung

**Aufwand:** 10-16h

### Phase 5: Admin - Ergebnisse, Texte & Freigaben (Priorität: Mittel)

- [ ] KAIMoCaseResults.vue (Aggregation)
- [ ] KAIMoContentEditor.vue (manuelle Texteingabe, KI-ready)
- [ ] KAIMoCasePermissions.vue
- [ ] Export-Funktionen (CSV/Excel)

**Aufwand:** 14-20h

---

## Gesamtaufwand

| Phase | Aufwand (Stunden) |
|-------|-------------------|
| Phase 1: DB & Basis-API | 8-12h |
| Phase 2: Admin Panel | 16-24h |
| Phase 3: User Panel | 20-30h |
| Phase 4: Bewertung | 10-16h |
| Phase 5: Ergebnisse & Texte | 14-20h |
| **Gesamt** | **68-102h** |

---

## KI-Integration (Zukunft)

!!! info "Für spätere Implementierung vorbereitet"
    Die folgenden Komponenten sind im Datenbank-Schema und der API vorbereitet, werden aber erst in einer späteren Phase implementiert.

**Vorbereitete Infrastruktur:**

- Tabelle `kaimo_ai_content` mit `is_generated` und `generated_at` Feldern
- API-Endpoint `/api/kaimo/admin/cases/<id>/content` erweiterbar um `generate: true`
- `KAIMoContentEditor.vue` kann später um "KI generieren" Button erweitert werden

**Spätere KI-Features (Phase 6+):**

- [ ] LLM-Integration für Zusammenfassungen
- [ ] KI-generierte Folgenabschätzung
- [ ] Automatische Plausibilitätsprüfung
- [ ] Streaming-Support für LLM-Antworten

**Geschätzter Zusatzaufwand:** 16-24h

---

## Offene Fragen

- [ ] Sollen Evaluator ihre eigenen abgeschlossenen Ergebnisse mit der Musterlösung vergleichen können?
- [ ] Wie granular soll die Freigabe sein? (Einzelnutzer vs. Gruppen vs. Alle)
- [ ] Soll es eine Zeitbegrenzung für die Fallbearbeitung geben?

---

## Abnahme

| Reviewer | Datum | Status |
|----------|-------|--------|
| Philipp Steigerwald | 2025-11-29 | Ausstehend |
