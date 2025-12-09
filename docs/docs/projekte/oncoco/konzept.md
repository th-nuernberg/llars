# OnCoCo-Analyse für KIA-Daten: Konzept

**Version:** 1.0
**Datum:** 25. November 2025
**Autor:** LLARS Development Team

---

## 1. Zusammenfassung

Dieses Konzept beschreibt die Integration des **OnCoCo-Klassifikators** (Online Counseling Conversations) in LLARS zur automatisierten Analyse von E-Mail-Beratungsverläufen aus dem KIA-Datenrepository. Das Ziel ist eine tiefgreifende, satzbasierte Analyse der Beratungsgespräche mit Visualisierungen wie Transition-Matrizen, Sankey-Diagrammen und Säulen-Vergleichen.

---

## 2. OnCoCo-Klassifikator Übersicht

### 2.1 Modell-Spezifikation

| Eigenschaft | Wert |
|-------------|------|
| **Basis-Modell** | FacebookAI/xlm-roberta-large |
| **Architektur** | XLMRobertaForSequenceClassification |
| **Parameter** | 561M |
| **Sprachen** | Deutsch & Englisch (bilingual) |
| **Accuracy** | 80% (@1), 89% (@2) |
| **F1 Macro** | 0.78 (@1), 0.87 (@2) |
| **Cohen's Kappa** | 0.88 (Human-Level Performance) |

### 2.2 Kategoriesystem (68 Klassen)

Das OnCoCo-Kategoriesystem ist hierarchisch strukturiert mit bis zu 5 Ebenen:

#### Berater-Kategorien (CO) - 40 Klassen

| Code | Kategorie (Level 5) | Beschreibung |
|------|---------------------|--------------|
| **CO-FA** | Formalities at Beginning | Begrüßung, Gesprächseröffnung |
| **CO-Mod** | Moderation | Gesprächsführung, Strukturierung |
| **CO-IF-AC-RF** | Analysis - Reflection (Fact) | Fragen zu Fakten, Lebensumständen |
| CO-IF-AC-RF-RPD | Request Personal Data | Frage nach persönlichen Daten |
| CO-IF-AC-RF-RPA | Request Previous Attempts | Frage nach bisherigen Lösungsversuchen |
| CO-IF-AC-RF-SRx | Simple Reflection | Einfache Spiegelung |
| CO-IF-AC-RF-RLS-SR | Request Living Situation - Social | Soziale Beziehungen |
| CO-IF-AC-RF-RLS-PS | Request Living Situation - Professional | Berufliche Situation |
| CO-IF-AC-RF-RLS-ES | Request Living Situation - Economic | Wirtschaftliche Situation |
| CO-IF-AC-RF-RLS-H | Request Living Situation - Health | Gesundheit (mental/physisch) |
| CO-IF-AC-RF-RLS-L | Request Living Situation - Leisure | Freizeit/Hobbies |
| CO-IF-AC-RF-RC | Request for Concerns | Frage nach Anliegen |
| CO-IF-AC-RF-RTP | Targeted, Precise Request | Gezielte, präzise Nachfrage |
| CO-IF-AC-RF-RCD | Request Change/Development | Frage nach Veränderung |
| **CO-IF-AC-RE** | Analysis - Reflection (Emotion) | Emotionale Reflexion |
| CO-IF-AC-RE-RCR | Complex Reflection | Komplexe Spiegelung |
| CO-IF-AC-RE-RES | Request Emotional State | Frage nach Gefühlszustand |
| **CO-IF-AO** | Analysis - Objectives | Zielklärung |
| CO-IF-AO-ROW | Request Objectives/Wishes | Frage nach Zielen/Wünschen |
| CO-IF-AO-ICO | Definition Counseling Objectives | Definition der Beratungsziele |
| **CO-IF-Mot** | Creating Motivation | Motivation schaffen |
| CO-IF-Mot-RFC | Eliciting Change-Talk (MI) | Change-Talk evozieren |
| CO-IF-Mot-IAC | Articulation Ability to Change | Wahrgenommene Veränderungsfähigkeit |
| CO-IF-Mot-ITA | Thanks and Appreciation | Dank und Wertschätzung |
| CO-IF-Mot-IEM | Encouragement, Motivation | Ermutigung, Motivation |
| CO-IF-Mot-RS | Question Support Resources | Frage nach Unterstützungsressourcen |
| **CO-IF-RA** | Resource Activation | Ressourcenaktivierung |
| CO-IF-RA-RP | Request Problem Statement | Anfrage zur Problemdarstellung |
| CO-IF-RA-RAP | Suggestion Professional Level | Vorschlag professionelle Ebene |
| CO-IF-RA-N-RAFa | Suggestion Family Level | Vorschlag Familienebene |
| CO-IF-RA-N-RAFr | Suggestion Friendship Level | Vorschlag Freundesebene |
| **CO-IF-HP** | Help, Problem Solving | Hilfe, Problemlösung |
| CO-IF-HP-ITFE | Technical/Factual Explanations | Fachliche Erklärungen |
| CO-IF-HP-IPFR | Professional Recommendation | Professionelle Empfehlung |
| CO-IF-HP-IF | Future Forecast | Zukunftsprognose |
| CO-IF-HP-IW | Warning | Warnung |
| CO-IF-HP-ICO | Calming | Beruhigung |
| CO-IF-HP-PP-IA | Advice | Ratschlag |
| CO-IF-HP-IEA | Evaluation, Interpretation | Bewertung, Interpretation |
| CO-IF-HP-PP-IW | Wish | Wunsch |
| **CO-FC** | Formalities Conclusion | Abschluss-Formalitäten |
| CO-FC-F | Farewell | Verabschiedung |
| CO-FC-OPR | Offer Professional Resources | Angebot professioneller Ressourcen |
| **CO-O** | Other | Sonstiges |
| CO-O-O | Other Statements | Andere Aussagen |
| CO-O-UCO | Inappropriate Remark | Unangemessene Bemerkung |

#### Klient-Kategorien (CL) - 28 Klassen

| Code | Kategorie (Level 5) | Beschreibung |
|------|---------------------|--------------|
| **CL-FB** | Formalities Beginning | Begrüßung |
| **CL-E** | Empathy | Empathie |
| CL-E-PT | Empathy Third Parties | Empathie für Dritte |
| CL-E-ECC | Compassion for Others | Mitgefühl für andere |
| CL-E-ECP | Concern for Another Person | Sorge um andere Person |
| **CL-IF-ACP** | Analysis - Clarification Problems | Problemklärung |
| CL-IF-ACP-PS | Problem Statement | Problemdarstellung |
| CL-IF-ACP-PD | Problem Definition | Problemdefinition |
| CL-IF-ACP-DPD | Disclosure Personal Data | Offenlegung persönlicher Daten |
| CL-IF-ACP-FPA | Feedback Previous Attempts | Feedback zu bisherigen Versuchen |
| CL-IF-ACP-OE | Own Emotional Expression | Eigener Gefühlsausdruck |
| CL-IF-ACP-Cons | Consent | Zustimmung |
| CL-IF-ACP-Rej | Rejection | Ablehnung |
| CL-IF-ACP-Req | General Request | Allgemeine Anfrage |
| **CL-IF-AO** | Analysis - Objectives | Zielklärung |
| CL-IF-AO-Obj | Objective Assignment | Ziel des Auftrags |
| CL-IF-AO-Ext | Extension Assignment | Erweiterung des Auftrags |
| **CL-IF-Mot** | Creating Motivation | Motivation |
| CL-IF-Mot-FC | Eliciting Change-Talk | Change-Talk |
| CL-IF-Mot-RC | Articulation Reasons for Change | Gründe für Veränderung |
| **CL-IF-RA** | Resource Activation | Ressourcenaktivierung |
| CL-IF-RA-RF | Considering Friends/Family | Ressourcen Freunde/Familie |
| CL-IF-RA-RP | Considering Professional Level | Ressourcen professionelle Ebene |
| **CL-IF-HP** | Help Coping with Problems | Problembewältigung |
| CL-IF-HP-PosF | General Positive Feedback | Allgemeines positives Feedback |
| CL-IF-HP-PosFR | Positive Feedback Recommendations | Positives Feedback zu Empfehlungen |
| CL-IF-HP-NegFR | Negative Feedback Recommendations | Negatives Feedback zu Empfehlungen |
| CL-IF-HP-RepRA | Report Implementation | Bericht zur Umsetzung |
| CL-IF-HP-Succ | Final Success | Finaler Erfolg |
| CL-IF-HP-Fail | Final Failure | Finales Scheitern |
| **CL-FC** | Formalities Conclusion | Abschluss |
| CL-FC-F | Farewell | Verabschiedung |
| CL-FC-UPR | Further Use Professional Resources | Weitere Nutzung prof. Ressourcen |
| **CL-O** | Other | Sonstiges |
| CL-O-O | Other Statements | Andere Aussagen |
| CL-O-UCO | Inappropriate Remark | Unangemessene Bemerkung |

---

## 3. Datenquellen: KIA-Säulen

Die KIA-Daten sind in 5 Säulen organisiert:

| Säule | Name | Beschreibung | GitLab-Pfad |
|-------|------|--------------|-------------|
| 1 | Rollenspiele | Simulierte Beratungsgespräche | `data/saeule_1/common/json` |
| 2 | Feature Säule 1 | Extrahierte Features | `data/saeule_2/common/json` |
| 3 | Anonymisierte Daten | Echte, anonymisierte Gespräche | `data/saeule_3/common/json` |
| 4 | Synthetisch generiert | KI-generierte Gespräche | `data/saeule_4/common/json` |
| 5 | Live-Testungen | Aktuelle Testdaten | `data/saeule_5/common/json` |

**Repository:** `git.informatik.fh-nuernberg.de/e-beratung/kia/kia-data`

---

## 4. Analyse-Konzept

### 4.1 Workflow

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   KIA GitLab     │────▶│   Satz-Level     │────▶│   OnCoCo         │
│   Data Sync      │     │   Segmentierung  │     │   Klassifikation │
└──────────────────┘     └──────────────────┘     └──────────────────┘
                                                           │
         ┌─────────────────────────────────────────────────┘
         ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Transition     │────▶│   Visualisierung │────▶│   Export &       │
│   Matrix         │     │   & Vergleich    │     │   Reporting      │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

### 4.2 Satz-Level Klassifikation

Jede Nachricht wird in Sätze segmentiert und einzeln klassifiziert:

```python
# Beispiel-Pipeline
message = "Ich verstehe, dass Sie sich Sorgen machen. Können Sie mir mehr über Ihre aktuelle Situation erzählen?"

sentences = segment_sentences(message)
# ["Ich verstehe, dass Sie sich Sorgen machen.",
#  "Können Sie mir mehr über Ihre aktuelle Situation erzählen?"]

labels = []
for sentence in sentences:
    label = oncoco_classifier.predict(f"Counselor: {sentence}")
    labels.append(label)
# ["CO-IF-AC-RF-SRx-*", "CO-IF-AC-RF-RC-*"]
```

### 4.3 Transition Matrix

Die **Transition Matrix** zeigt Übergänge zwischen Labels:

```
Von \ Nach     CO-FA   CO-IF-AC-RF   CO-IF-Mot   CL-IF-ACP   ...
CO-FA          0.02    0.65          0.08        0.00        ...
CO-IF-AC-RF    0.00    0.45          0.12        0.35        ...
CO-IF-Mot      0.00    0.30          0.15        0.40        ...
CL-IF-ACP      0.00    0.55          0.10        0.20        ...
```

**Berechnung:**
```python
import numpy as np
from collections import defaultdict

def compute_transition_matrix(label_sequences):
    """
    Berechnet die Transition Matrix aus Label-Sequenzen.

    Args:
        label_sequences: Liste von Listen mit Labels pro Gespräch

    Returns:
        transition_counts: Dict[label_from][label_to] -> count
        transition_probs: Normalisierte Wahrscheinlichkeiten
    """
    transition_counts = defaultdict(lambda: defaultdict(int))

    for sequence in label_sequences:
        for i in range(len(sequence) - 1):
            from_label = sequence[i]
            to_label = sequence[i + 1]
            transition_counts[from_label][to_label] += 1

    # Normalisierung zu Wahrscheinlichkeiten
    transition_probs = {}
    for from_label, to_labels in transition_counts.items():
        total = sum(to_labels.values())
        transition_probs[from_label] = {
            to_label: count / total
            for to_label, count in to_labels.items()
        }

    return transition_counts, transition_probs
```

### 4.4 Analyse-Metriken

#### Pro Säule:
1. **Label-Verteilung**: Häufigkeit jeder Kategorie
2. **Impact Factor Ratio**: Anteil der "Impact Factors" an Gesamtnachrichten
3. **Durchschnittliche Gesprächslänge**: Anzahl Nachrichten/Sätze
4. **Berater-Klient-Balance**: Verhältnis CO zu CL Labels
5. **Motivational Interviewing Score**: Häufigkeit von MI-Techniken
6. **Ressourcenaktivierung Score**: Häufigkeit von RA-Labels

#### Säulen-Vergleich:
1. **KL-Divergenz**: Unterschied der Label-Verteilungen
2. **Transition-Ähnlichkeit**: Cosinus-Ähnlichkeit der Transition-Vektoren
3. **Chi-Quadrat-Test**: Signifikanz der Verteilungsunterschiede
4. **Gespräch-Qualitätsindex**: Gewichteter Score basierend auf Impact Factors

---

## 5. Visualisierungen

### 5.1 Transition Matrix Heatmap

```
┌────────────────────────────────────────────┐
│         Transition Matrix - Säule 1        │
├────────────────────────────────────────────┤
│                                            │
│    FA  Mod IF-AC IF-AO IF-Mot IF-RA IF-HP │
│ FA  ▓   ░   ███   ░     ░      ░     ░    │
│ Mod ░   ░   ██    ░     ░      ░     ░    │
│IF-AC░   ░   ██    █     ░      ░     ░    │
│IF-AO░   ░   █     ░     ██     ░     ░    │
│IF-Mot░  ░   █     ░     █      █     ░    │
│IF-RA░   ░   █     ░     ░      █     ██   │
│IF-HP░   ░   ░     ░     ░      ░     █    │
│                                            │
│ ░ = 0-10%  █ = 10-30%  ██ = 30-50%  ███ = 50%+ │
└────────────────────────────────────────────┘
```

**Implementierung:** D3.js Heatmap oder Plotly

### 5.2 Sankey-Diagramm

Zeigt den "Fluss" durch ein typisches Beratungsgespräch:

```
Gesprächsbeginn           Mitte                    Ende
─────────────────────────────────────────────────────────
    ┌───────┐
    │ CO-FA │─────────┐
    └───────┘         │     ┌───────────┐
                      ├────▶│ CO-IF-AC  │──────┐
    ┌───────┐         │     └───────────┘      │
    │ CL-FB │─────────┘                        │
    └───────┘                                  │
                            ┌───────────┐      │    ┌───────┐
                      ┌────▶│ CO-IF-Mot │──────┼───▶│ CO-FC │
                      │     └───────────┘      │    └───────┘
    ┌───────────┐     │                        │
    │ CL-IF-ACP │─────┤                        │    ┌───────┐
    └───────────┘     │     ┌───────────┐      └───▶│ CL-FC │
                      └────▶│ CO-IF-HP  │──────────▶└───────┘
                            └───────────┘
```

**Implementierung:** Plotly Sankey oder D3-Sankey

### 5.3 Säulen-Vergleichs-Radar-Chart

```
                    Impact Factors
                         ▲
                    ████ │ ████
               ███      │      ███
          █            │            █
    Ressourcen ◀───────┼───────────▶ Motivation
          █            │            █
               ███      │      ███
                    ████ │ ████
                         ▼
                    Empathie

    ─── Säule 1    ─── Säule 3    ─── Säule 5
```

### 5.4 Gesprächsverlaufs-Timeline

```
Zeit →
┌────────────────────────────────────────────────────────────┐
│ CO: ██▓▓▓▓░░██▓▓▓▓░░░░██▓▓░░░░░░░░░░░░░██░░██░░░░░░░░░░██│
│     FA  AC       Mod    Mot      RA          HP        FC  │
├────────────────────────────────────────────────────────────┤
│ CL: ░░██▓▓██░░██▓▓▓▓██░░░░██▓▓▓▓░░░░██▓▓░░░░░░░░░░██░░░░│
│       FB  ACP      ACP     Mot    HP      HP          FC   │
└────────────────────────────────────────────────────────────┘
```

---

## 6. Frontend-Kachel: OnCoCo-Analyse

### 6.1 UI-Mockup

```
┌─────────────────────────────────────────────────────────────────────┐
│  OnCoCo-Analyse                                           [?] [×]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Datenquelle                                                  │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │  │
│  │  │ Säule 1 │ │ Säule 2 │ │ Säule 3 │ │ Säule 4 │ │ Säule 5 │ │  │
│  │  │  ✓ 42   │ │  ○ --   │ │  ✓ 156  │ │  ○ --   │ │  ✓ 28   │ │  │
│  │  │ Threads │ │ Threads │ │ Threads │ │ Threads │ │ Threads │ │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ │  │
│  │                                                               │  │
│  │  [🔄 KIA-Daten synchronisieren]  [📊 Analyse starten]        │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Analyse-Status                                                  ││
│  │ ████████████████████████░░░░░░░░░░  65% (142/218 Gespräche)   ││
│  │ Aktuelle Verarbeitung: Säule 3, Thread #47                     ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┐                │
│  │Overview │Transitions│ Sankey │ Vergleich│ Export │                │
│  └─────────┴─────────┴─────────┴─────────┴─────────┘                │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                                                                  ││
│  │              [Visualisierung / Ergebnisse]                      ││
│  │                                                                  ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Tab-Inhalte

#### Tab 1: Overview
- Label-Verteilung als Balkendiagramm (gruppiert nach Säule)
- Top 10 häufigste Labels
- Gesamtstatistiken (Gespräche, Sätze, Labels)

#### Tab 2: Transitions
- Interaktive Transition-Matrix-Heatmap
- Filter nach Säule, Level (aggregiert/detailliert)
- Hover: Zeigt Wahrscheinlichkeit und Beispielsätze

#### Tab 3: Sankey
- Sankey-Diagramm des typischen Gesprächsverlaufs
- Slider: Gesprächsphase (Anfang/Mitte/Ende)
- Vergleichsmodus: 2 Säulen nebeneinander

#### Tab 4: Vergleich
- Radar-Chart mit 6 Dimensionen pro Säule
- Tabelle: KL-Divergenz zwischen Säulen
- Signifikanz-Indikatoren

#### Tab 5: Export
- CSV-Export der Rohdaten
- PDF-Report mit allen Visualisierungen
- JSON-Export für weitere Analyse

---

## 7. Backend-Architektur

### 7.1 Neue API-Routen

```python
# app/routes/oncoco/oncoco_routes.py

@oncoco_bp.route('/api/oncoco/analyze', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
def start_analysis():
    """
    Startet OnCoCo-Analyse für ausgewählte Säulen.

    Body:
        pillars: List[int] - Säulen-IDs [1, 3, 5]
        granularity: str - "sentence" oder "message"

    Returns:
        analysis_id: int - ID der gestarteten Analyse
    """

@oncoco_bp.route('/api/oncoco/analyses/<int:analysis_id>', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_analysis_status(analysis_id: int):
    """Analyse-Status und Fortschritt abrufen."""

@oncoco_bp.route('/api/oncoco/analyses/<int:analysis_id>/results', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_analysis_results(analysis_id: int):
    """Vollständige Ergebnisse einer Analyse."""

@oncoco_bp.route('/api/oncoco/analyses/<int:analysis_id>/transitions', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_transition_matrix(analysis_id: int):
    """Transition Matrix für eine Analyse."""

@oncoco_bp.route('/api/oncoco/analyses/<int:analysis_id>/sankey', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_sankey_data(analysis_id: int):
    """Sankey-Diagramm-Daten."""

@oncoco_bp.route('/api/oncoco/compare', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:view')
def compare_pillars():
    """
    Vergleicht zwei oder mehr Säulen.

    Body:
        pillars: List[int] - Säulen-IDs zum Vergleich
        metrics: List[str] - Gewünschte Metriken
    """
```

### 7.2 Datenbank-Schema

```sql
-- Neue Tabellen für OnCoCo-Analyse

CREATE TABLE oncoco_analyses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
    config_json JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    completed_at DATETIME,
    error_message TEXT
);

CREATE TABLE oncoco_sentence_labels (
    id INT PRIMARY KEY AUTO_INCREMENT,
    analysis_id INT NOT NULL,
    thread_id INT NOT NULL,
    message_id INT NOT NULL,
    sentence_index INT NOT NULL,
    sentence_text TEXT NOT NULL,
    label VARCHAR(50) NOT NULL,
    confidence FLOAT,
    pillar_number INT NOT NULL,
    FOREIGN KEY (analysis_id) REFERENCES oncoco_analyses(id) ON DELETE CASCADE
);

CREATE TABLE oncoco_transition_matrices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    analysis_id INT NOT NULL,
    pillar_number INT,  -- NULL für aggregiert
    level INT DEFAULT 2,  -- Aggregations-Level (2-5)
    matrix_json JSON NOT NULL,
    FOREIGN KEY (analysis_id) REFERENCES oncoco_analyses(id) ON DELETE CASCADE
);

CREATE TABLE oncoco_pillar_statistics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    analysis_id INT NOT NULL,
    pillar_number INT NOT NULL,
    total_threads INT,
    total_messages INT,
    total_sentences INT,
    label_distribution_json JSON,
    impact_factor_ratio FLOAT,
    mi_score FLOAT,
    resource_activation_score FLOAT,
    FOREIGN KEY (analysis_id) REFERENCES oncoco_analyses(id) ON DELETE CASCADE
);
```

### 7.3 OnCoCo Service

```python
# app/services/oncoco/oncoco_service.py

class OnCoCoService:
    """Service für OnCoCo-Klassifikation und Analyse."""

    MODEL_PATH = "Ideen und Daten dazu/OnCoCo Analyse/xlm-roberta-large-OnCoCo-DE-EN"

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.label_mapping = None

    def load_model(self):
        """Lädt das OnCoCo-Modell (lazy loading)."""
        from transformers import AutoTokenizer, AutoModelForSequenceClassification

        if self.model is None:
            self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_PATH)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.MODEL_PATH)
            self.label_mapping = self.model.config.id2label

    def classify_sentence(self, text: str, role: str = "Counselor") -> dict:
        """
        Klassifiziert einen einzelnen Satz.

        Args:
            text: Der zu klassifizierende Satz
            role: "Counselor" oder "Client"

        Returns:
            dict mit 'label', 'confidence', 'top_3'
        """
        self.load_model()

        # Prefix für Rolle hinzufügen
        input_text = f"{role}: {text}"

        inputs = self.tokenizer(input_text, return_tensors="pt", truncation=True, max_length=512)
        outputs = self.model(**inputs)

        probs = torch.softmax(outputs.logits, dim=-1)[0]
        top_3_idx = torch.topk(probs, 3).indices

        # Rolle-basiertes Masking (CO-* für Counselor, CL-* für Client)
        prefix = "CO-" if role == "Counselor" else "CL-"

        # Finde bestes Label mit korrektem Prefix
        for idx in torch.argsort(probs, descending=True):
            label = self.label_mapping[str(idx.item())]
            if label.startswith(prefix):
                return {
                    'label': label,
                    'confidence': probs[idx].item(),
                    'top_3': [
                        {'label': self.label_mapping[str(i.item())], 'prob': probs[i].item()}
                        for i in top_3_idx if self.label_mapping[str(i.item())].startswith(prefix)
                    ]
                }

    def analyze_thread(self, thread_id: int, pillar_number: int) -> List[dict]:
        """Analysiert alle Nachrichten eines Threads."""
        from db.tables import Message
        import nltk

        messages = Message.query.filter_by(thread_id=thread_id).order_by(Message.timestamp).all()
        results = []

        for msg in messages:
            # Bestimme Rolle
            role = "Counselor" if 'berater' in (msg.sender or '').lower() else "Client"

            # Segmentiere in Sätze
            sentences = nltk.sent_tokenize(msg.content, language='german')

            for idx, sentence in enumerate(sentences):
                if len(sentence.strip()) > 10:  # Mindestlänge
                    result = self.classify_sentence(sentence, role)
                    results.append({
                        'message_id': msg.id,
                        'sentence_index': idx,
                        'sentence_text': sentence,
                        'role': role,
                        **result
                    })

        return results
```

### 7.4 Background Worker

```python
# app/workers/oncoco_worker.py

def run_oncoco_analysis(analysis_id: int):
    """
    Background-Worker für OnCoCo-Analyse.
    Sendet Socket.IO Events für Live-Updates.
    """
    from services.oncoco.oncoco_service import OnCoCoService
    from db.tables import OnCoCoAnalysis, OnCoCoSentenceLabel, PillarThread

    analysis = OnCoCoAnalysis.query.get(analysis_id)
    if not analysis:
        return

    analysis.status = 'running'
    analysis.started_at = datetime.now()
    db.session.commit()

    service = OnCoCoService()
    pillars = analysis.config_json.get('pillars', [1, 3, 5])

    total_threads = 0
    processed = 0

    for pillar in pillars:
        threads = PillarThread.query.filter_by(pillar_number=pillar).all()
        total_threads += len(threads)

    for pillar in pillars:
        threads = PillarThread.query.filter_by(pillar_number=pillar).all()

        for pt in threads:
            try:
                results = service.analyze_thread(pt.thread_id, pillar)

                for r in results:
                    label = OnCoCoSentenceLabel(
                        analysis_id=analysis_id,
                        thread_id=pt.thread_id,
                        message_id=r['message_id'],
                        sentence_index=r['sentence_index'],
                        sentence_text=r['sentence_text'],
                        label=r['label'],
                        confidence=r['confidence'],
                        pillar_number=pillar
                    )
                    db.session.add(label)

                processed += 1

                # Socket.IO Progress Update
                socketio.emit('oncoco:progress', {
                    'analysis_id': analysis_id,
                    'progress': processed / total_threads * 100,
                    'current_thread': pt.thread_id,
                    'pillar': pillar
                }, room=f'oncoco_{analysis_id}')

            except Exception as e:
                logger.error(f"Error analyzing thread {pt.thread_id}: {e}")

        db.session.commit()

    # Berechne Statistiken und Transition Matrices
    compute_analysis_statistics(analysis_id)
    compute_transition_matrices(analysis_id)

    analysis.status = 'completed'
    analysis.completed_at = datetime.now()
    db.session.commit()

    socketio.emit('oncoco:completed', {
        'analysis_id': analysis_id
    }, room=f'oncoco_{analysis_id}')
```

---

## 8. Erweiterte Analysen

### 8.1 Weitere Analyse-Möglichkeiten

| Analyse | Beschreibung | Nutzen |
|---------|--------------|--------|
| **N-Gram Sequenzen** | Häufigste 2er, 3er, 4er Label-Sequenzen | Typische Muster identifizieren |
| **Phasen-Erkennung** | Automatische Segmentierung in Gesprächsphasen | Struktur verstehen |
| **Anomalie-Detektion** | Ungewöhnliche Sequenzen finden | Qualitätssicherung |
| **Erfolgs-Korrelation** | Labels mit positivem Outcome korrelieren | Best Practices |
| **Berater-Profile** | Individuelle Stile klassifizieren | Training, Supervision |
| **Zeitreihen-Analyse** | Entwicklung über Zeit | Trends erkennen |
| **Cluster-Analyse** | Gespräche nach Muster gruppieren | Typisierung |
| **MI-Adherence Score** | Einhaltung von MI-Techniken messen | Methodentreue |

### 8.2 Empathie-Mapping

Basierend auf Labels kann ein "Empathie-Verlauf" berechnet werden:

```
Empathie-Score = w1 * CO-IF-AC-RE + w2 * CO-IF-Mot-ITA + w3 * CO-IF-AC-RF-SRx
```

### 8.3 Outcome-Prediction

Mit den Labels kann trainiert werden:
- Wird der Klient zurückkehren?
- Ist das Gespräch erfolgreich?
- Gibt es Risikosignale?

---

## 9. Implementierungs-Roadmap

### Phase 1: Grundlagen (2 Wochen)
- [ ] OnCoCo-Service implementieren
- [ ] Datenbank-Schema erweitern
- [ ] Basic API-Routes

### Phase 2: Analyse-Engine (2 Wochen)
- [ ] Satz-Segmentierung
- [ ] Batch-Klassifikation
- [ ] Transition Matrix Berechnung
- [ ] Background Worker

### Phase 3: Frontend (2 Wochen)
- [ ] OnCoCo-Kachel in Admin-Dashboard
- [ ] Tab: Overview mit Balkendiagrammen
- [ ] Tab: Transition Matrix Heatmap
- [ ] Tab: Sankey-Diagramm

### Phase 4: Erweiterungen (2 Wochen)
- [ ] Säulen-Vergleich
- [ ] Export-Funktionen
- [ ] Anomalie-Erkennung
- [ ] Performance-Optimierung

---

## 10. Technische Anforderungen

### Hardware (für GPU-Inferenz)
- CUDA-fähige GPU mit mindestens 8GB VRAM
- Alternativ: CPU-Inferenz (langsamer, ~1-2 Sek/Satz)

### Software
- Python 3.10+
- PyTorch 2.0+
- Transformers 4.49+
- NLTK (für Satz-Segmentierung)
- Plotly/D3.js (für Visualisierungen)

### Deployment
- Docker Container mit GPU-Support
- Oder: Inference-Service auf separatem GPU-Server

---

## 11. Quellen & Referenzen

### OnCoCo Paper
- Albrecht et al. (2025): "OnCoCo 1.0: A Public Dataset for Fine-Grained Message Classification in Online Counseling Conversations" - LREC 2026

### Conversation Analysis
- [Markov Chains in NLP - GeeksforGeeks](https://www.geeksforgeeks.org/nlp/markov-chains-in-nlp/)
- [Dialogue Act Classification - Papers with Code](https://paperswithcode.com/task/dialogue-act-classification)
- [Sentiment-Aware Dialogue Flow Discovery - ACL Anthology](https://aclanthology.org/2024.sigdial-1.24/)
- [Large-scale Analysis of Counseling Conversations - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC5361062/)
- [Speaker and Time-aware Joint Contextual Learning - ResearchGate](https://www.researchgate.net/publication/358624770_Speaker_and_Time-aware_Joint_Contextual_Learning_for_Dialogue-act_Classification_in_Counselling_Conversations)

### Visualisierung
- [Sankey Diagram in Python - Plotly](https://plotly.com/python/sankey-diagram/)
- [Process Mining with Sankey Diagrams - Medium](https://medium.com/@stephanhausberg/process-mining-with-sankey-diagrams-in-motion-3ab38cc250d0)

### Related Work
- Althoff et al. (2016): Large-scale Analysis of Counseling Conversations
- Malhotra et al. (2022): HOPE Dataset - Dialogue-act Classification in Counselling
- Wu et al. (2022, 2023): Anno-MI Dataset

---

## 12. Zusammenfassung

Dieses Konzept ermöglicht eine **tiefgreifende, automatisierte Analyse** von KIA-Beratungsgesprächen auf Satzebene mit dem OnCoCo-Klassifikator. Die Hauptfeatures sind:

1. **Satz-Level Klassifikation** mit 68 feingranularen Kategorien
2. **Transition Matrices** zur Visualisierung von Gesprächsdynamiken
3. **Sankey-Diagramme** für Gesprächsfluss-Analyse
4. **Säulen-Vergleiche** mit statistischen Metriken
5. **Export & Reporting** für weitere Forschung

Die Integration in LLARS erfolgt über eine neue **OnCoCo-Kachel** im Admin-Dashboard mit Live-Analyse-Updates via Socket.IO.
