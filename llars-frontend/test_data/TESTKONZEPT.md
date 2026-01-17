# Testkonzept: Evaluationstypen in LLARS

## Ziel

Systematisches Testen aller Evaluationstypen mit LLM-Evaluatoren, um zu verifizieren:
1. Korrekte Datenerfassung und -anzeige
2. Funktionierendes LLM-Evaluation
3. Richtige Ergebnis-Visualisierung pro Typ

---

## Evaluationstypen-Übersicht

| ID | Typ | Beschreibung | Besondere Ergebnisse |
|----|-----|--------------|---------------------|
| 1 | `ranking` | Items in Kategorien sortieren (Gut/Mittel/Schlecht) | Bucket-Verteilung, Krippendorff's Alpha |
| 2 | `rating` | Features/Items mit Sternen bewerten (1-5) | Durchschnittswerte, Verteilung |
| 3 | `mail_rating` | E-Mail-Konversation insgesamt bewerten | Qualitäts-Scores |
| 5 | `authenticity` | Fake/Echt-Erkennung | **Confusion Matrix**, Accuracy, Precision, Recall, F1 |

---

## Testdaten

### Verzeichnisstruktur

```
llars-frontend/test_data/
├── authenticity/           # Fake/Echt Test
│   ├── human_email_1.json  # 3x echte E-Mails
│   ├── human_email_2.json
│   ├── human_email_3.json
│   ├── gpt4_email_1.json   # 2x GPT-4 generiert
│   ├── gpt4_email_2.json
│   ├── claude_email_1.json # 2x Claude generiert
│   └── claude_email_2.json
│
├── ranking/                # Ranking Test
│   ├── good_response_1.json    # 2x gute Qualität
│   ├── good_response_2.json
│   ├── medium_response_1.json  # 2x mittlere Qualität
│   ├── medium_response_2.json
│   ├── poor_response_1.json    # 2x schlechte Qualität
│   └── poor_response_2.json
│
└── rating/                 # Rating Test
    ├── conversation_1.json # 4 Konversationen
    ├── conversation_2.json # verschiedener Qualität
    ├── conversation_3.json
    └── conversation_4.json
```

### Datenformat (OpenAI/ChatML)

```json
{
  "messages": [
    {"role": "system", "content": "Kontext"},
    {"role": "user", "content": "Nachricht vom Klienten"},
    {"role": "assistant", "content": "Antwort vom Berater"}
  ],
  "metadata": {
    "source": "Human" | "gpt-4" | "claude-3",
    "subject": "Betreff",
    "id": "eindeutige_id"
  }
}
```

**Wichtig für Authenticity:** Das `source`-Feld bestimmt den Ground-Truth!
- `"Human"` → Thread ist echt
- Alles andere → Thread ist fake/KI-generiert

---

## Testdurchführung

### Test 1: Authenticity (Fake/Echt-Erkennung)

#### Schritt 1: Szenario erstellen

1. **Szenario Manager** öffnen (http://localhost:55080/scenario-manager)
2. **Neues Szenario** → Wizard starten
3. Dateien hochladen: Alle 7 Dateien aus `test_data/authenticity/`
4. Typ auswählen: **Authenticity / Labeling**
5. Konfiguration prüfen:
   - Labels: `fake`, `echt` (oder `AI-generated`, `Human`)
6. Zeitraum: Heute bis +7 Tage
7. Szenario erstellen

#### Schritt 2: LLM-Evaluator hinzufügen

1. Szenario öffnen → Tab "Evaluierung"
2. Sektion "LLM Evaluatoren"
3. **LLM hinzufügen** klicken
4. Modell auswählen (z.B. `gpt-4o-mini` oder `claude-3-haiku`)
5. Evaluation starten

#### Schritt 3: Ergebnisse prüfen

**Erwartete Anzeige:**
- [ ] Confusion Matrix mit 4 Feldern (TP, FP, TN, FN)
- [ ] Metriken: Accuracy, Precision, Recall, F1
- [ ] Progress-Anzeige pro LLM
- [ ] Agreement-Metriken (wenn mehrere Evaluatoren)

**Ground Truth:**
- human_email_1.json → echt (source: Human)
- human_email_2.json → echt
- human_email_3.json → echt
- gpt4_email_1.json → fake (source: gpt-4)
- gpt4_email_2.json → fake
- claude_email_1.json → fake (source: claude-3)
- claude_email_2.json → fake

---

### Test 2: Ranking

#### Schritt 1: Szenario erstellen

1. **Neues Szenario** → Wizard
2. Dateien hochladen: Alle 6 Dateien aus `test_data/ranking/`
3. Typ: **Ranking**
4. Buckets konfigurieren:
   - `Gut` (grün)
   - `Mittel` (gelb)
   - `Schlecht` (rot)
5. Szenario erstellen

#### Schritt 2: LLM-Evaluator hinzufügen

1. LLM hinzufügen (z.B. `gpt-4o`)
2. Evaluation starten

#### Schritt 3: Ergebnisse prüfen

**Erwartete Anzeige:**
- [ ] Bucket-Verteilungs-Chart
- [ ] Progress pro Evaluator
- [ ] Krippendorff's Alpha (Agreement)
- [ ] Keine Confusion Matrix (nur für authenticity)

**Erwartete Zuordnung:**
- good_response_* → Bucket "Gut"
- medium_response_* → Bucket "Mittel"
- poor_response_* → Bucket "Schlecht"

---

### Test 3: Rating / Mail Rating

#### Schritt 1: Szenario erstellen

1. **Neues Szenario** → Wizard
2. Dateien hochladen: Alle 4 Dateien aus `test_data/rating/`
3. Typ: **Rating** oder **Mail Rating**
4. Skala konfigurieren: 1-5 Sterne
5. Szenario erstellen

#### Schritt 2: LLM-Evaluator hinzufügen

1. LLM hinzufügen
2. Evaluation starten

#### Schritt 3: Ergebnisse prüfen

**Erwartete Anzeige:**
- [ ] Durchschnittswerte pro Evaluator
- [ ] Bewertungsverteilung (Histogramm)
- [ ] Keine Confusion Matrix
- [ ] Keine Bucket-Verteilung

---

## Checkliste pro Evaluationstyp

### Authenticity
- [ ] Confusion Matrix wird angezeigt
- [ ] TP/FP/TN/FN Werte sind korrekt
- [ ] Metriken werden berechnet (Accuracy, Precision, Recall, F1)
- [ ] Heatmap-Farben funktionieren
- [ ] Toggle Counts/Percentages funktioniert
- [ ] Legende wird angezeigt

### Ranking
- [ ] Bucket-Verteilung wird angezeigt
- [ ] Alle Buckets sind sichtbar
- [ ] Progress-Bars funktionieren
- [ ] Keine Confusion Matrix sichtbar

### Rating
- [ ] Durchschnittswerte werden angezeigt
- [ ] Verteilungs-Chart funktioniert
- [ ] Keine Confusion Matrix sichtbar
- [ ] Keine Bucket-Verteilung sichtbar

---

## Troubleshooting

### Problem: LLM-Evaluation startet nicht
- [ ] Provider konfiguriert? (Settings → LLM Provider)
- [ ] API-Key gültig?
- [ ] Modell hat Zugriff? (Admin → Model Access)

### Problem: Confusion Matrix zeigt nur Nullen
- [ ] `source`/`generated_by` Feld in Testdaten korrekt?
- [ ] Ground-Truth wird erkannt?
- [ ] useScenarioStats liefert `fake_correct`, `fake_incorrect` etc.?

### Problem: Keine Ergebnisse sichtbar
- [ ] Evaluator hat alle Threads bewertet?
- [ ] Socket-Verbindung aktiv?
- [ ] Stats-API gibt Daten zurück?

---

## API-Debugging

```bash
# Stats abrufen
curl -H "Authorization: Bearer <TOKEN>" \
  http://localhost:55080/api/scenarios/<ID>/stats

# Erwartete Felder:
# - rater_stats[]
# - evaluator_stats[]
# - agreement_metrics
# - function_type
```

---

## Nächste Schritte nach Tests

1. [ ] Screenshots der Ergebnisse dokumentieren
2. [ ] Bugs in Issues erfassen
3. [ ] UI-Verbesserungen identifizieren
4. [ ] Export-Funktion testen (CSV/JSON)
