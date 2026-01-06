# LLARS - LLM Assisted Research System

**Eine Forschungsplattform zur KI-gestützten Analyse und Evaluation von Online-Beratungskommunikation**

---

## 1. Was ist LLARS?

LLARS (LLM Assisted Research System) ist eine webbasierte Forschungsplattform, die speziell für die wissenschaftliche Analyse und Evaluation von E-Mail-Beratungskommunikation entwickelt wurde. Das System kombiniert moderne Large Language Models (LLMs) mit kollaborativen Bewertungswerkzeugen und automatisierten Analysemethoden.

### Kernziele

- **Standardisierte Evaluation** von Beratungsqualität durch strukturierte Bewertungsverfahren
- **LLM-gestützte Analyse** von Kommunikationsmustern in Beratungsgesprächen
- **Kollaborative Forschung** durch Multi-User-Unterstützung mit Echtzeit-Synchronisation
- **Reproduzierbare Forschung** durch systematische Datenerfassung und -verwaltung

---

## 2. Hauptfunktionen

### 2.1 E-Mail-Rating System

Das Kernsystem ermöglicht die strukturierte Bewertung von E-Mail-Threads aus Beratungskontexten:

| Funktion | Beschreibung |
|----------|--------------|
| **Mail Rating** | Bewertung einzelner E-Mails nach definierten Kriterien |
| **Szenario-Management** | Organisation von E-Mails in Bewertungsszenarien |
| **Ranking-System** | Vergleichende Einordnung von Beratungsqualität |
| **Multi-Rater Support** | Mehrere Bewerter können parallel arbeiten |

### 2.2 LLM-as-Judge System

Automatisierte paarweise Vergleiche von E-Mail-Konversationen durch LLMs:

```
Säule A (z.B. Rollenspiel-Daten)  vs.  Säule B (z.B. echte Beratungen)
              ↓                                    ↓
         [LLM-Evaluation]
              ↓
    Winner: A/B + Konfidenz + Begründung
```

**Anwendungsfälle:**
- Vergleich verschiedener Beratungsansätze
- Evaluation von KI-generierten vs. menschlichen Antworten
- Qualitätsmessung über verschiedene Datenquellen hinweg

### 2.3 OnCoCo-Analyse (Online Counseling Conversations)

Tiefgreifende, satzbasierte Klassifikation von Beratungsgesprächen mit einem spezialisierten Transformer-Modell:

**Modell-Spezifikation:**
- Basis: XLM-RoBERTa Large (561M Parameter)
- 68 feingranulare Kategorien (40 Berater, 28 Klient)
- Bilinguale Unterstützung (Deutsch/Englisch)
- 80% Accuracy, Cohen's Kappa: 0.88 (Human-Level)

**Analyse-Output:**
- Label-Verteilungen pro Gespräch/Säule
- Transition-Matrizen (Übergänge zwischen Gesprächshandlungen)
- Sankey-Diagramme (Gesprächsfluss-Visualisierung)
- Säulen-Vergleiche mit statistischen Metriken

### 2.4 Kollaboratives Prompt Engineering

Echtzeit-kollaborative Entwicklung von LLM-Prompts für Bewertungs- und Analyseaufgaben:

- **Y.js CRDT-Synchronisation**: Konfliktfreie Zusammenarbeit
- **Cursor-Tracking**: Sehen, wo andere Nutzer arbeiten
- **Versionierung**: Automatische Speicherung aller Änderungen
- **Template-Management**: Wiederverwendbare Prompt-Vorlagen

Zusätzlich gibt es **Markdown Collab** für gemeinsames Schreiben von Markdown-Dokumenten mit Live-Preview und Git-Diff-Ansicht.

### 2.5 RAG-Pipeline (Retrieval-Augmented Generation)

Kontextbasierte Antwortgenerierung durch ChromaDB-Integration:

- **Dokumenten-Upload**: PDF, TXT, DOCX, PPTX, XLSX (und weitere)
- **Chunking & Embedding**: Automatische Verarbeitung
- **Kontextsuche**: Relevante Passagen für LLM-Anfragen
- **Admin-Interface**: Verwaltung der Wissensbasis

---

## 3. Datenquellen: KIA-Säulen-Modell

LLARS arbeitet mit dem strukturierten **KIA-Datenrepository** (git.informatik.fh-nuernberg.de):

| Säule | Name | Inhalt | Forschungsnutzen |
|-------|------|--------|------------------|
| **1** | Rollenspiele | Simulierte Beratungsgespräche | Trainings-Baseline, kontrollierte Szenarien |
| **2** | Feature aus Säule 1 | Extrahierte Merkmale | Quantitative Analyse |
| **3** | Anonymisierte Daten | Echte Beratungsgespräche | Ground Truth, Validierung |
| **4** | Synthetisch | KI-generierte Gespräche | Augmentation, Vergleichsstudien |
| **5** | Live-Testungen | Aktuelle Testdaten | Pilotierung, A/B-Tests |

---

## 4. Nutzung für die Dissertation

### 4.1 Forschungsfragen, die LLARS adressiert

LLARS eignet sich besonders für Forschungsarbeiten zu:

1. **Qualitätsmessung in der Online-Beratung**
   - Wie lässt sich Beratungsqualität objektiv messen?
   - Welche Gesprächsmuster korrelieren mit erfolgreichen Beratungen?

2. **KI in der Beratungsunterstützung**
   - Können LLMs Beratungsqualität zuverlässig bewerten?
   - Wie unterscheiden sich KI-generierte von menschlichen Antworten?

3. **Gesprächsanalyse und Dialog Acts**
   - Welche Gesprächshandlungen sind typisch für gute Beratung?
   - Wie entwickeln sich Gespräche über die Zeit?

4. **Inter-Rater-Reliabilität**
   - Wie konsistent bewerten verschiedene Rater?
   - Kann KI als "objektiver" Rater dienen?

### 4.2 Methoden-Unterstützung

| Methode | LLARS-Feature | Output |
|---------|---------------|--------|
| **Quantitative Inhaltsanalyse** | OnCoCo-Klassifikation | Label-Verteilungen, Häufigkeiten |
| **Sequenzanalyse** | Transition-Matrizen | Gesprächsmuster, Übergänge |
| **Vergleichsstudie** | LLM-as-Judge | Paarweise Bewertungen, Rankings |
| **Inter-Rater-Analyse** | Multi-User-Rating | Übereinstimmungsmaße |
| **Qualitative Exploration** | Prompt Engineering | Strukturierte LLM-Analyse |

### 4.3 Typischer Dissertations-Workflow

```
1. Daten-Import
   └── KIA-Säulen synchronisieren
   └── Szenarien definieren

2. Manuelle Bewertung (Ground Truth)
   └── Rater-Team einrichten
   └── Bewertungskriterien festlegen
   └── Collaborative Rating durchführen

3. Automatisierte Analyse
   └── OnCoCo-Klassifikation ausführen
   └── LLM-as-Judge Sessions erstellen
   └── Transition-Matrizen berechnen

4. Vergleich & Evaluation
   └── Human vs. LLM-Bewertungen
   └── Säulen-Vergleiche
   └── Statistische Tests

5. Export & Dokumentation
   └── CSV/JSON-Export
   └── Visualisierungen generieren
   └── Reproduzierbare Analyse-Pipeline
```

### 4.4 Konkrete Anwendungsbeispiele

**Beispiel 1: Evaluation von Beratungsqualität**
```
Forschungsfrage: "Unterscheidet sich die Beratungsqualität zwischen
                 Rollenspielen und echten Beratungen?"

LLARS-Ansatz:
1. Säule 1 (Rollenspiele) und Säule 3 (echte Daten) laden
2. LLM-as-Judge: Paarweise Vergleiche durchführen
3. OnCoCo: Label-Verteilungen vergleichen
4. Statistische Auswertung der Unterschiede
```

**Beispiel 2: Gesprächsdynamik-Analyse**
```
Forschungsfrage: "Welche Gesprächsmuster führen zu erfolgreichen
                 Beratungsabschlüssen?"

LLARS-Ansatz:
1. OnCoCo-Analyse aller Threads durchführen
2. Transition-Matrizen berechnen
3. Erfolgreiche vs. nicht-erfolgreiche Gespräche vergleichen
4. Signifikante Muster identifizieren
```

**Beispiel 3: LLM als Bewertungs-Tool**
```
Forschungsfrage: "Kann ein LLM menschliche Bewertungen
                 zuverlässig replizieren?"

LLARS-Ansatz:
1. Menschliche Rater bewerten Stichprobe
2. LLM-as-Judge bewertet dieselbe Stichprobe
3. Inter-Rater-Reliabilität berechnen (Cohen's Kappa)
4. Diskrepanz-Analyse durchführen
```

---

## 5. Technische Übersicht

### 5.1 Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                         NGINX                                │
│                    (Reverse Proxy)                           │
└────────┬──────────────┬──────────────┬──────────────┬───────┘
         │              │              │              │
    ┌────▼────┐   ┌─────▼─────┐  ┌─────▼─────┐  ┌────▼────┐
    │   Vue   │   │   Flask   │  │    YJS    │  │ Authentik│
    │Frontend │   │  Backend  │  │WebSocket  │  │   Auth   │
    └────┬────┘   └─────┬─────┘  └─────┬─────┘  └─────────┘
         │              │              │
         │        ┌─────┴─────────────┐│
         │        │     MariaDB       ││
         │        └───────────────────┘│
         │                             │
    ┌────┴─────────────────────────────┴────┐
    │              Externe APIs              │
    │  (LiteLLM/OpenAI, GitLab, ChromaDB)   │
    └────────────────────────────────────────┘
```

### 5.2 Tech-Stack

| Komponente | Technologie | Zweck |
|------------|-------------|-------|
| Frontend | Vue 3 + Vuetify | User Interface |
| Backend | Flask 3.0 | REST API, Business Logic |
| Auth | Authentik | Benutzerverwaltung |
| Collaboration | Y.js + Socket.IO | Echtzeit-Sync |
| Database | MariaDB | Persistenz |
| LLM | LiteLLM (Mistral) + OpenAI | KI-Bewertungen |
| RAG | ChromaDB | Vektordatenbank |
| NLP | XLM-RoBERTa | OnCoCo-Klassifikation |

### 5.3 Berechtigungssystem

Granulares RBAC mit 40 Permissions:

| Rolle | Rechte | Typischer Nutzer |
|-------|--------|------------------|
| **Admin** | Vollzugriff (40 Permissions) | Projektleiter |
| **Researcher** | Evaluierung + Prompt Engineering + Markdown Collab + Anonymisierung + KAIMO (19) | Wissenschaftler |
| **Chatbot Manager** | Chatbots + RAG + Prompt Engineering + Markdown Collab (14) | Content Owner |
| **Evaluator** | Lesezugriff + ausgewählte Edit-Rechte (13) | Externe Reviewer |

---

## 6. Wissenschaftliche Grundlagen

### 6.1 OnCoCo-Kategoriesystem

Das Kategoriesystem basiert auf etablierter Beratungsforschung:

**Berater-Kategorien (CO):**
- Formalities (Begrüßung, Abschluss)
- Information Gathering (Fakten, Emotionen, Ziele)
- Motivation (MI-Techniken, Ermutigung)
- Resource Activation (sozial, professionell)
- Problem Solving (Ratschläge, Erklärungen)

**Klient-Kategorien (CL):**
- Problem Clarification (Darstellung, Definition)
- Objectives (Ziele, Aufträge)
- Feedback (positiv/negativ)
- Resource Consideration

### 6.2 Methodische Grundlagen

- **Motivational Interviewing (MI)**: Spezifische Labels für MI-Techniken
- **Dialog Act Classification**: Hierarchisches Kategoriesystem
- **Process Mining**: Transition-Matrizen, Sankey-Diagramme
- **Human-AI Collaboration**: LLM-as-Judge Paradigma

---

## 7. Output-Formate für die Dissertation

### 7.1 Quantitative Daten

```csv
# Beispiel: Label-Verteilung
pillar,label,count,percentage
1,CO-IF-AC-RF,245,18.3%
1,CO-IF-Mot,189,14.1%
3,CO-IF-AC-RF,312,21.7%
...
```

### 7.2 Visualisierungen

- **Transition-Matrix Heatmaps**: PNG/SVG-Export
- **Sankey-Diagramme**: Interaktiv (Plotly) oder statisch
- **Radar-Charts**: Säulen-Vergleiche
- **Timeline-Visualisierungen**: Gesprächsverläufe

### 7.3 Statistische Auswertungen

- Label-Häufigkeiten und -Verteilungen
- KL-Divergenz zwischen Säulen
- Chi-Quadrat-Tests für Signifikanz
- Cohen's Kappa für Inter-Rater-Reliabilität
- ELO-Scores aus LLM-as-Judge

---

## 8. Vorteile für die Forschung

### Reproduzierbarkeit
- Alle Analysen sind dokumentiert und wiederholbar
- Export-Funktionen für alle Rohdaten
- Versionierung von Prompts und Konfigurationen

### Skalierbarkeit
- Automatisierte Analyse großer Datensätze
- Background-Worker für Batch-Verarbeitung
- API-basiert für Integration mit anderen Tools

### Kollaboration
- Multi-User-Support mit Rollen
- Echtzeit-Synchronisation
- Audit-Trail für Nachvollziehbarkeit

### Flexibilität
- Modulare Architektur
- Erweiterbar durch neue Analyse-Module
- Open-Source-Stack

---

## 9. Zusammenfassung

LLARS ist eine spezialisierte Forschungsplattform, die drei zentrale Funktionen für die wissenschaftliche Analyse von Online-Beratung vereint:

1. **Strukturierte Bewertung**: Multi-Rater-System für manuelle Evaluation
2. **Automatisierte Analyse**: OnCoCo-Klassifikation und LLM-as-Judge
3. **Visualisierung & Export**: Publikationsreife Outputs

Für Dissertationen im Bereich E-Beratung, KI-gestützte Kommunikationsanalyse oder Human-AI-Collaboration bietet LLARS:

- Standardisierte Methoden zur Qualitätsmessung
- Reproduzierbare Analyse-Pipelines
- Vergleichsmöglichkeiten zwischen verschiedenen Datenquellen
- Integration von manueller und automatisierter Bewertung

---

**Entwickler:** Philipp Steigerwald
**Version:** 2.6
**Stand:** November 2025
**Repository:** LLARS (LLM Assisted Research System)
