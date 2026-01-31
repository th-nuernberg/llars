# Plan: MkDocs Dokumentation Update

## Übersicht

Update der Dokumentation für drei Kernbereiche:
1. **Scenario Wizard** - Assistent zur Szenario-Erstellung
2. **Scenario Manager** - Verwaltung und Workspace
3. **Evaluation** - Durchführung von Bewertungen

---

## 1. Scenario Wizard (`docs/docs/guides/scenario-wizard.md`)

### Aktuelle Lücken
- Keine Dokumentation im offiziellen MkDocs
- Concept-File in `/docs/concepts/` ist veraltet
- Fehlt: Structure-based Detection (neu!)
- Fehlt: Long-Format Daten-Support (neu!)
- Fehlt: AI Field Mapping (neu!)

### Zu dokumentieren
1. **Wizard-Übersicht**
   - 5 Schritte erklärt
   - Screenshots/Diagramme

2. **Daten-Upload**
   - Unterstützte Formate (CSV, JSON, JSONL)
   - Wide vs. Long Format (NEU!)
   - Beispieldateien

3. **Automatische Typ-Erkennung**
   - SchemaDetector (deterministisch)
   - AI-Fallback
   - Erkannte Feldmuster

4. **Long-Format Transformation (NEU!)**
   - Was ist Long-Format?
   - Automatisches Field Mapping
   - Transformation zu LLARS-Format

5. **Evaluationstypen**
   - Die 6 Typen erklärt
   - Wann welcher Typ?
   - Presets

6. **Team-Zusammenstellung**
   - Menschliche Evaluatoren
   - LLM-Modelle als Evaluatoren

---

## 2. Scenario Manager (`docs/docs/guides/scenario-manager.md`)

### Aktuelle Lücken
- Nur Redesign-Konzept existiert
- Keine Benutzer-Dokumentation
- Fehlt: Workspace-Tabs Erklärung
- Fehlt: Live-Statistiken

### Zu dokumentieren
1. **Manager-Übersicht**
   - "Meine Szenarien" Tab
   - "Einladungen" Tab
   - Szenario-Karten

2. **Workspace**
   - Übersicht Tab
   - Evaluation Tab (Live-Stats)
   - Team Tab
   - Einstellungen Tab
   - Ergebnisse Tab

3. **Live-Statistiken**
   - Fortschrittsbalken
   - Inter-Rater Agreement Heatmap
   - Dimensionen-Verteilung
   - Evaluator-Übersicht

4. **Szenario-Aktionen**
   - Bearbeiten
   - Duplizieren
   - Archivieren
   - Löschen
   - LLM-Evaluation starten

---

## 3. Evaluation (`docs/docs/guides/evaluation.md`)

### Aktuelle Lücken
- Nur technische Datenformate-Doku
- Keine Benutzer-Anleitung
- Fehlt: Wie bewerte ich?
- Fehlt: UI-Erklärung pro Typ

### Zu dokumentieren
1. **Evaluation starten**
   - Als Eingeladener
   - Als Owner

2. **Evaluations-Interface**
   - Layout erklärt
   - Navigation zwischen Items
   - Fortschrittsanzeige

3. **Bewertung pro Typ**
   - Rating: Likert-Skalen, Dimensionen
   - Ranking: Drag & Drop in Buckets
   - Labeling: Kategorien auswählen
   - Comparison: A vs B wählen
   - Authenticity: Echt/Fake
   - Mail Rating: E-Mail-Verlauf bewerten

4. **Tipps & Best Practices**
   - Konsistenz
   - Pausieren/Fortsetzen
   - Tastaturkürzel

---

## Dateistruktur (Ziel)

```
docs/docs/guides/
├── index.md (aktualisieren - Links hinzufügen)
├── scenario-wizard.md (NEU)
├── scenario-manager.md (NEU)
├── evaluation.md (NEU)
└── ... (bestehende Dateien)
```

## mkdocs.yml Navigation (Ziel)

```yaml
nav:
  - Anleitungen:
      - Übersicht: guides/index.md
      - Szenario Wizard: guides/scenario-wizard.md      # NEU
      - Szenario Manager: guides/scenario-manager.md    # NEU
      - Evaluation: guides/evaluation.md                # NEU
      - Schnellstart: guides/quick-start.md
      - ...
```

---

## Implementierungsreihenfolge

1. Scenario Wizard (grundlegend, Start-Punkt)
2. Scenario Manager (Verwaltung)
3. Evaluation (Durchführung)
4. mkdocs.yml aktualisieren
5. guides/index.md aktualisieren
