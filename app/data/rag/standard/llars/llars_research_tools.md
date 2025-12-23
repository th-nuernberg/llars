# LLARS Research Tools (Navigation + Workflows)

Ziel: Diese Notiz beschreibt die Research-Tools in LLARS (keine Admin-Tools),
wo man sie findet und wie man sie nutzt.

## Navigation Basics
- Einstieg: Home-Dashboard unter `/Home`.
- Kategorien: Links die Kategorie waehlen (Bewertung, Forschung, KI-Tools).
- Tool aufrufen: Rechts die Feature-Kachel anklicken.
- Sichtbarkeit: Kacheln erscheinen nur, wenn die Berechtigung vorhanden ist.

## Evaluierung (Hub)
- Pfad: `/evaluation` (Kachel "Evaluierung").
- Funktion: Zentrale Auswahl fuer Ranking, Rating, Verlaufsbewertung, Fake/Echt und Gegenueberstellung.
- Hinweis: Tools sind nur aktiv, wenn dir Szenarien/Threads zugewiesen sind.

### Ranking
- Pfad: `/Ranker`.
- Workflow:
  1) Thread oeffnen.
  2) Features in Buckets ziehen: Gut / Mittel / Schlecht / Neutral.
  3) Naechsten Thread auswaehlen, bis alles bewertet ist.

### Rating
- Pfad: `/Rater`.
- Workflow:
  1) Thread oeffnen.
  2) Feature anklicken.
  3) Bewertung abgeben (Skala) und speichern.

### Verlaufsbewertung (Mail Rating)
- Pfad: `/HistoryGeneration`.
- Workflow:
  1) Thread oeffnen.
  2) Kohaerenz, Qualitaet und Gesamtwirkung bewerten.
  3) Optional Kommentar/Hinweise erfassen.

### Fake/Echt (Authenticity)
- Pfad: `/authenticity`.
- Workflow:
  1) Thread oeffnen.
  2) Einstufen: echt oder fake.
  3) Bewertung speichern.

### Gegenueberstellung (Comparison)
- Pfad: `/comparison`.
- Workflow:
  1) Session starten.
  2) Zwei Modell-Ausgaben vergleichen.
  3) Gewinner waehlen und speichern.

## Prompt Engineering
- Pfad: `/PromptEngineering`.
- Zweck: Prompts kollaborativ erstellen, versionieren und testen.
- Workflow:
  1) Neues Prompt erstellen.
  2) Bloecke anlegen (z.B. System, Kontext, Aufgabenstellung).
  3) Inhalte bearbeiten, Bloecke sortieren.
  4) Optional: Teilen mit anderen und Testlauf starten.

## Markdown Collab
- Pfad: `/MarkdownCollab`.
- Zweck: Gemeinsames Schreiben von Markdown mit Live-Preview.
- Workflow:
  1) Workspace erstellen oder oeffnen.
  2) Dokument anlegen/oeffnen.
  3) Text bearbeiten, Live-Preview nutzen.
  4) Teammitglieder einladen (optional).

## KAIMO
- Pfad: `/kaimo`.
- Zweck: Fallvignetten bearbeiten und bewerten.
- Workflow (Panel):
  1) KAIMO Panel oeffnen.
  2) Fall auswaehlen.
  3) Hinweise den Kategorien zuordnen und Fall abschliessen.
- Workflow (Researcher):
  1) Neuen Fall anlegen (wenn freigeschaltet).
  2) Inhalte vorbereiten und veroeffentlichen.

## Anonymisierung
- Pfad: `/Anonymize`.
- Zweck: Offline-Pseudonymisierung fuer Texte, DOCX und PDF.
- Workflow:
  1) Text einfuegen oder Datei hochladen.
  2) Pseudonymisieren ausfuehren.
  3) Output kopieren oder Datei exportieren.

## LLM-as-Judge
- Pfad: `/judge`.
- Zweck: Automatisierte Vergleiche mit LLMs (Session-basiert).
- Workflow:
  1) Session anlegen.
  2) Vergleich starten (Start/Pause moeglich).
  3) Ergebnisse ansehen.

## OnCoCo Analyse
- Pfad: `/oncoco`.
- Zweck: Satzbasierte Klassifikation von Beratungsgespraechen.
- Workflow:
  1) Neue Analyse konfigurieren.
  2) Analyse starten und Fortschritt verfolgen.
  3) Ergebnisse und Visualisierungen ansehen.

## Chatbot
- Pfad: `/chat`.
- Zweck: Fragen zum System stellen, Hinweise zu Workflows erhalten.
- Workflow:
  1) Chat oeffnen.
  2) Bot auswaehlen (z.B. LLARS).
  3) Frage stellen und Quellen beachten.
