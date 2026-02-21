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
3. **Einladung annehmen**
4. Danach auf **"Zur Evaluation"** klicken

```
┌────────────────────────────────────────┐
│  [↕️] LLM-Vergleich Benchmark           │
│  Ranking · Eingeladen von admin         │
│                                         │
│  Dein Fortschritt: 0/20 (0%)            │
│  ░░░░░░░░░░░░░░░░░░░░                   │
│                                         │
│  [Ablehnen] [Annehmen]                  │
│  (nach Annahme: [Zur Evaluation])       │
└────────────────────────────────────────┘
```

!!! info "Eingeschränkte Rechte"
    Als eingeladener Evaluator sehen Sie nur Ihren eigenen Fortschritt, nicht den anderer Evaluatoren oder Gesamtergebnisse.

### Als Owner (Szenario-Ersteller)

1. Öffnen Sie **Evaluation** (Evaluation Hub) im Hauptmenü
2. Wählen Sie das gewünschte Szenario
3. Öffnen Sie die **Item-Übersicht** und starten Sie die Bewertung

!!! tip "Testen vor dem Einladen"
    Als Owner können Sie das Szenario selbst durcharbeiten, bevor Sie andere Evaluatoren einladen. Ihre Bewertungen werden ebenfalls gespeichert.

---

## Evaluation-Übersicht (Items)

Nach dem Öffnen gelangen Sie zuerst zur **Item-Übersicht**. Dort sehen Sie alle Items als Karten, inklusive Status und Filter (Ausstehend, In Bearbeitung, Abgeschlossen). Ein Klick auf ein Item öffnet die Evaluations-Session.

```
┌────────────────────────────────────────┐
│  Filter: Alle | Ausstehend | In Arbeit │
│                                         │
│  [Item-Karte]  [Item-Karte]  [Item...]  │
│  Status-Badge  Status-Badge  Status...  │
└────────────────────────────────────────┘
```

---

## Evaluations-Interface

Die Evaluations-Session öffnet sich nach Klick auf ein Item in der Übersicht.

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

Standard-Dimensionen für LLM Evaluator:

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

!!! info "Optionen konfigurierbar"
    Die Auswahloptionen (z.B. Mensch/KI oder Echt/Fake) werden pro Szenario festgelegt.

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

| Status | Bedeutung |
|--------|-----------|
| **Ausstehend** | Noch nicht bewertet |
| **In Bearbeitung** | Bewertung läuft oder teilweise abgeschlossen |
| **Abgeschlossen** | Vollständig bewertet |
| **Speichern** | Bewertung wird gerade gespeichert |

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

Das hängt von Ihrer Rolle und der Verteilung ab:
- **EVALUATOR:** Items gemäß Verteilung (z.B. alle, zufällig, sequenziell)
- **VIEWER:** Keine Bewertungen (read-only)

---

## LLM-Evaluation

Zusätzlich zu menschlichen Evaluatoren können **LLM-Modelle** als automatische Bewerter eingesetzt werden:

### Verfügbare Modelle

- **System-Modelle** (admin-konfiguriert)
- **Eigene/geteilte Provider** (vom Nutzer oder Team bereitgestellt)

### LLM-Evaluation konfigurieren

1. Im **Szenario Wizard** (Schritt „Team“) LLMs auswählen
2. **LLM-Evaluation aktivieren**

!!! info "Automatische Bewertung"
    Wenn LLM-Evaluation aktiviert ist, bewerten die ausgewählten Modelle automatisch alle Items basierend auf den konfigurierten Dimensionen. Die Ergebnisse erscheinen im Evaluation-Tab.

---

## API-Endpunkte

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/scenarios/:scenarioId` | GET | Szenario-Details (für Übersicht) |
| `/api/evaluation/session/:scenarioId` | GET | Session-Daten abrufen |
| `/api/evaluation/session/:scenarioId/items/:itemId/evaluate` | POST | Bewertung speichern |
| `/api/evaluation/llm/:scenarioId/start` | POST | LLM-Evaluation starten |
| `/api/evaluation/llm/:scenarioId/stop` | POST | LLM-Evaluation stoppen |

---

## Siehe auch

- [Szenario Wizard](scenario-wizard.md) - Szenarien erstellen
- [Szenario Manager](scenario-manager.md) - Szenarien verwalten
- [Berechtigungssystem](permission-system.md) - Zugriffsrechte
