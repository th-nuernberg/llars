# Evaluation

**Version:** 2.0 | **Stand:** Januar 2026

Diese Anleitung erklärt, wie Sie Bewertungen in LLARS durchführen. Je nach Evaluationstyp unterscheidet sich das Interface und die Bewertungsmethode.

---

## Übersicht

```
┌─────────────────────────────────────────────────────────────────────┐
│  Evaluation Interface                                               │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐  │
│  │                             │  │                             │  │
│  │    Content-Bereich          │  │    Bewertungs-Panel         │  │
│  │    (Text, Konversation)     │  │    (Skalen, Buttons)        │  │
│  │                             │  │                             │  │
│  └─────────────────────────────┘  └─────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│  [◀ Zurück]           Item 3 von 25            [Weiter ▶]           │
│  ████████████░░░░░░░░░░░░░░░░░░░░░░  12%                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Evaluation starten

### Als eingeladener Evaluator

1. Öffnen Sie den **Szenario Manager**
2. Wechseln Sie zum Tab **"Einladungen"**
3. Klicken Sie auf **"Zur Evaluation →"** bei der gewünschten Einladung

```
┌────────────────────────────────────────┐
│  [↕️] LLM-Vergleich Benchmark           │
│  Ranking · Eingeladen von admin         │
│                                         │
│  Dein Fortschritt: 0/20 (0%)            │
│  ░░░░░░░░░░░░░░░░░░░░                   │
│                                         │
│  [Zur Evaluation →]                     │
└────────────────────────────────────────┘
```

!!! info "Eingeschränkte Rechte"
    Als eingeladener Evaluator sehen Sie nur Ihren eigenen Fortschritt, nicht den anderer Evaluatoren oder Gesamtergebnisse.

### Als Owner (Szenario-Ersteller)

1. Öffnen Sie den **Szenario Manager**
2. Klicken Sie auf die **Szenario-Karte** unter "Meine Szenarien"
3. Im Workspace: Klicken Sie auf **"Zur Evaluation"** im Übersicht-Tab

!!! tip "Testen vor dem Einladen"
    Als Owner können Sie das Szenario selbst durcharbeiten, bevor Sie andere Evaluatoren einladen. Ihre Bewertungen werden ebenfalls gespeichert.

---

## Evaluations-Interface

### Layout

Das Interface ist in drei Hauptbereiche unterteilt:

| Bereich | Beschreibung |
|---------|--------------|
| **Header** | Szenario-Name, Fortschritt, Navigation |
| **Content** | Das zu bewertende Item (Text, Konversation, Varianten) |
| **Bewertung** | Eingabeelemente je nach Evaluationstyp |

### Navigation

| Element | Funktion |
|---------|----------|
| **◀ Zurück** | Vorheriges Item |
| **Weiter ▶** | Nächstes Item |
| **Fortschrittsbalken** | Zeigt aktuellen Stand |
| **Item X von Y** | Aktuelle Position |

---

## Evaluationstypen

### Rating (Multi-Dimensional)

**Anwendung:** Text-Qualität, Zusammenfassungen, LLM-Outputs

```
┌─────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐  │
│  │  Frage:                      │  │  Kohärenz                   │  │
│  │  Was ist die Hauptstadt      │  │  ○ 1  ○ 2  ● 3  ○ 4  ○ 5   │  │
│  │  von Frankreich?             │  ├─────────────────────────────┤  │
│  │                              │  │  Flüssigkeit                │  │
│  │  Antwort:                    │  │  ○ 1  ○ 2  ○ 3  ● 4  ○ 5   │  │
│  │  Die Hauptstadt von          │  ├─────────────────────────────┤  │
│  │  Frankreich ist Paris.       │  │  Relevanz                   │  │
│  │  Paris ist bekannt für...    │  │  ○ 1  ○ 2  ○ 3  ○ 4  ● 5   │  │
│  │                              │  ├─────────────────────────────┤  │
│  │                              │  │  Konsistenz                 │  │
│  │                              │  │  ○ 1  ○ 2  ○ 3  ● 4  ○ 5   │  │
│  └─────────────────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

#### Dimensionen

Standard-Dimensionen für LLM-as-Judge:

| Dimension | Beschreibung | Skala |
|-----------|--------------|-------|
| **Kohärenz** | Logischer Zusammenhang | 1-5 |
| **Flüssigkeit** | Sprachliche Qualität | 1-5 |
| **Relevanz** | Bezug zur Frage | 1-5 |
| **Konsistenz** | Widerspruchsfreiheit | 1-5 |

#### Bewertungstipps

- Bewerten Sie **jede Dimension einzeln**
- Vergleichen Sie **nicht** zwischen Items
- Orientieren Sie sich an den **Skalen-Beschreibungen**

---

### Ranking (Bucket-Sortierung)

**Anwendung:** Summary-Qualität, LLM-Vergleiche, Priorisierung

```
┌─────────────────────────────────────────────────────────────────────┐
│  Referenz: Original-Artikel über Klimawandel...                     │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │    GUT       │  │   MITTEL     │  │  SCHLECHT    │              │
│  │   (grün)     │  │   (gelb)     │  │    (rot)     │              │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤              │
│  │              │  │              │  │              │              │
│  │  [Summary A] │  │              │  │              │              │
│  │              │  │              │  │              │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                     │
│  Nicht sortiert:                                                    │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐                         │
│  │ Summary B │ │ Summary C │ │ Summary D │                         │
│  └───────────┘ └───────────┘ └───────────┘                         │
└─────────────────────────────────────────────────────────────────────┘
```

#### So funktioniert's

1. **Lesen Sie die Referenz** (Original-Text) oben
2. **Lesen Sie jede Variante** (Summary A, B, C...)
3. **Ziehen Sie per Drag & Drop** jede Variante in den passenden Bucket
4. **Ties sind erlaubt** - mehrere Items im gleichen Bucket

#### Bucket-Typen

| Bucket | Farbe | Bedeutung |
|--------|-------|-----------|
| **Gut** | Grün | Hohe Qualität |
| **Mittel** | Gelb | Akzeptable Qualität |
| **Schlecht** | Rot | Geringe Qualität |

!!! tip "Vergleichen Sie mit der Referenz"
    Bewerten Sie immer im Verhältnis zum Original-Text, nicht im Vergleich der Summaries untereinander.

---

### Labeling (Kategorisierung)

**Anwendung:** Themen-Klassifikation, Sentiment-Analyse

```
┌─────────────────────────────────────────────────────────────────────┐
│  Text:                                                              │
│  "Das Produkt ist fantastisch! Die Lieferung war schnell           │
│   und der Kundenservice sehr hilfsbereit."                         │
├─────────────────────────────────────────────────────────────────────┤
│  Kategorie auswählen:                                               │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Positiv    │  │   Neutral    │  │   Negativ    │              │
│  │      ✓       │  │              │  │              │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

#### Kategorien-Typen

| Modus | Beschreibung |
|-------|--------------|
| **Single-Label** | Genau eine Kategorie |
| **Multi-Label** | Mehrere Kategorien möglich |

#### Bewertungstipps

- Wählen Sie die **passendste** Kategorie
- Bei Multi-Label: Nur **relevante** Kategorien auswählen
- Bei Unsicherheit: Optional "Unsicher"-Kategorie nutzen

---

### Comparison (Paarweiser Vergleich)

**Anwendung:** Modell-Vergleiche, Präferenz-Studien

```
┌─────────────────────────────────────────────────────────────────────┐
│  Prompt: "Erkläre Quantencomputing einfach."                       │
├────────────────────────────┬────────────────────────────────────────┤
│  Antwort A                 │  Antwort B                             │
│                            │                                        │
│  "Quantencomputer nutzen   │  "Ein Quantencomputer ist wie ein     │
│  Qubits statt klassischer  │  normaler Computer, aber er kann      │
│  Bits. Diese können..."    │  mehrere Berechnungen..."             │
│                            │                                        │
├────────────────────────────┴────────────────────────────────────────┤
│                                                                     │
│  Welche Antwort ist besser?                                         │
│                                                                     │
│  [ A ist besser ]  [ Unentschieden ]  [ B ist besser ]              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### Auswahloptionen

| Option | Beschreibung |
|--------|--------------|
| **A ist besser** | Antwort A bevorzugt |
| **B ist besser** | Antwort B bevorzugt |
| **Unentschieden** | Beide gleichwertig (wenn erlaubt) |

#### Bewertungstipps

- Lesen Sie **beide Antworten vollständig**
- Fokussieren Sie auf die **Qualitätskriterien** des Szenarios
- Tie nur wählen, wenn wirklich **keine Präferenz**

---

### Authenticity (Echtheitsprüfung)

**Anwendung:** KI-generierte Texte erkennen

```
┌─────────────────────────────────────────────────────────────────────┐
│  Text:                                                              │
│                                                                     │
│  "Liebe Ratsuchende, vielen Dank für Ihre Nachricht.               │
│   Ihre Situation klingt belastend. Es ist wichtig,                  │
│   dass Sie sich professionelle Hilfe suchen..."                     │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  Ist dieser Text von einem Menschen oder einer KI geschrieben?      │
│                                                                     │
│  ┌─────────────────────┐    ┌─────────────────────┐                │
│  │   👤 MENSCH         │    │   🤖 KI             │                │
│  │                     │    │                     │                │
│  └─────────────────────┘    └─────────────────────┘                │
│                                                                     │
│  Optional: Wie sicher sind Sie?                                     │
│  [ Sehr unsicher ] ─────●───── [ Sehr sicher ]                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### Hinweise zur Erkennung

| Merkmal | Eher Mensch | Eher KI |
|---------|-------------|---------|
| **Sprache** | Umgangssprachlich, Fehler | Formell, fehlerlos |
| **Struktur** | Variabel | Gleichmäßig |
| **Emotionen** | Authentisch, individuell | Allgemein, distanziert |
| **Details** | Spezifisch, persönlich | Generisch |

!!! warning "Keine Garantie"
    Diese Merkmale sind Tendenzen, keine sicheren Indikatoren. Moderne LLMs können sehr menschlich klingen.

---

### Mail Rating (E-Mail-Bewertung)

**Anwendung:** Beratungsqualität, Antwortqualität in E-Mail-Verläufen

```
┌─────────────────────────────────────────────────────────────────────┐
│  E-Mail-Verlauf                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 👤 Klient (10.01.2026, 14:30)                                │   │
│  │ Betreff: Schwierigkeiten im Job                              │   │
│  │                                                              │   │
│  │ Hallo, ich habe seit Wochen Probleme mit meinem Chef...      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 💬 Berater (11.01.2026, 09:15)                               │   │
│  │                                                              │   │
│  │ Vielen Dank für Ihre Nachricht. Ich verstehe, dass die      │   │
│  │ Situation belastend für Sie ist...                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────┤
│  Bewertung der Berater-Antwort:                                     │
│                                                                     │
│  Empathie:        ○ 1  ○ 2  ○ 3  ● 4  ○ 5                          │
│  Professionalität: ○ 1  ○ 2  ○ 3  ○ 4  ● 5                          │
│  Hilfsbereitschaft: ○ 1  ○ 2  ○ 3  ● 4  ○ 5                         │
└─────────────────────────────────────────────────────────────────────┘
```

#### Besonderheiten

- **Konversationsansicht:** Der gesamte E-Mail-Verlauf wird angezeigt
- **Kontext wichtig:** Bewerten Sie die Antwort im Kontext der Anfrage
- **Rollen:** Klient-Nachrichten (links) vs. Berater-Antworten (rechts)

---

## Fortschritt & Status

### Fortschrittsanzeige

```
████████████░░░░░░░░░░░░░░░░░░░░░░  35%
14 von 40 Items bewertet
```

### Item-Status

| Symbol | Status | Bedeutung |
|--------|--------|-----------|
| ⚪ | Ausstehend | Noch nicht bewertet |
| 🟡 | Teilweise | Nicht alle Dimensionen bewertet |
| ✅ | Abgeschlossen | Vollständig bewertet |

---

## Tipps & Best Practices

### Konsistenz

- **Kalibrieren Sie sich:** Bewerten Sie die ersten 3-5 Items besonders sorgfältig
- **Pausen einplanen:** Nach 20-30 Items empfiehlt sich eine kurze Pause
- **Notizen machen:** Bei Unsicherheiten können Sie Kommentare hinterlassen (wenn aktiviert)

### Pausieren & Fortsetzen

- **Auto-Save:** Ihre Bewertungen werden automatisch gespeichert
- **Jederzeit pausieren:** Schließen Sie einfach das Fenster
- **Fortsetzen:** Öffnen Sie die Evaluation erneut - Sie starten beim letzten Item

### Qualitätssicherung

!!! warning "Wichtige Hinweise"
    - Bewerten Sie **unvoreingenommen** - ignorieren Sie, welches Modell den Text erzeugt hat
    - Bei **Long-Format Daten** sind die Varianten-Labels anonymisiert
    - **Nehmen Sie sich Zeit** - Qualität vor Geschwindigkeit

---

## Häufige Fragen

### Kann ich eine Bewertung ändern?

Ja, navigieren Sie einfach zum entsprechenden Item zurück. Ihre neue Bewertung überschreibt die alte.

### Was passiert bei Abbruch?

Alle bisherigen Bewertungen sind gespeichert. Sie können jederzeit fortsetzen.

### Sehe ich die Ergebnisse?

- **Als Evaluator:** Nein, Sie sehen nur Ihren eigenen Fortschritt
- **Als Owner:** Ja, im Workspace unter dem "Evaluation"-Tab

### Wie viele Items muss ich bewerten?

Das hängt von Ihrer Rolle ab:
- **EVALUATOR:** Alle Items des Szenarios
- **RATER:** Ein zugewiesener Teil (vom Owner konfiguriert)

---

## LLM-Evaluation

Zusätzlich zu menschlichen Evaluatoren können **LLM-Modelle** als automatische Bewerter eingesetzt werden:

### Verfügbare Modelle

- GPT-4, GPT-4o
- Claude 3 Opus, Claude 3.5 Sonnet
- Mistral, Llama 3
- Custom-Modelle (Admin-konfiguriert)

### LLM-Evaluation starten

1. Öffnen Sie den **Workspace** des Szenarios
2. Gehen Sie zum Tab **"Team"**
3. Klicken Sie auf **"+ Einladen"** → Tab **"LLM-Modelle"**
4. Wählen Sie die gewünschten Modelle
5. Klicken Sie auf **"LLM-Evaluation starten"**

!!! info "Automatische Bewertung"
    LLMs bewerten alle Items automatisch basierend auf den konfigurierten Dimensionen. Die Ergebnisse erscheinen in den Statistiken.

---

## API-Endpunkte

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/evaluation/session/:scenarioId` | GET | Session-Daten abrufen |
| `/api/evaluation/rating/:scenarioId/config` | GET | Rating-Konfiguration |
| `/api/evaluation/rating/:scenarioId/items` | GET | Items für Bewertung |
| `/api/evaluation/rating/:scenarioId/items/:itemId/rate` | POST | Bewertung speichern |
| `/api/evaluation/rating/:scenarioId/progress` | GET | Fortschritt abrufen |
| `/api/evaluation/:scenarioId/agreement-metrics` | GET | Agreement-Metriken |

---

## Siehe auch

- [Szenario Wizard](scenario-wizard.md) - Szenarien erstellen
- [Szenario Manager](scenario-manager.md) - Szenarien verwalten
- [Berechtigungssystem](permission-system.md) - Zugriffsrechte
