# LLARS Interviews – Finale Zusammenfassung

## Teilnehmer:innen

| # | Person | Rolle | Perspektive |
|---|--------|-------|-------------|
| 1 | Mark | Domain Expert (Sozialwissenschaftler) | Prompt Engineering, Evaluation |
| 2 | Jennifer | Domain Expert (Sozialwissenschaftlerin) | Kollaboration, Workflow |
| 3 | Maria | Beraterin | Evaluation (Ranking/Rating) |
| 4 | Dana | Beraterin | Evaluation, Prompt Engineering |
| 5 | Mara | Beraterin / Beratungsforscherin | Prompt Eng., Evaluation, Kollaboration |
| 6 | Nico | Entwickler | Prompt-Sync, E2E-Workflow |
| 7 | Eric | Entwickler | Prompt Engineering, Integrationen |

**Gesamt:** 5 Domain Expert:innen / Berater:innen, 2 Entwickler (aus 7 dokumentierten Interviews)

---

## Kernbefunde nach Themen

### 1. Bridging the Gap: Interdisziplinäre Zusammenarbeit

**Zentrales Ergebnis:** Der mit Abstand häufigste und stärkste Befund über alle Interviews hinweg ist, dass LLARS die Kluft zwischen Domain Expert:innen und Entwickler:innen überbrückt.

- **Jennifer:** Wegfall der „Dolmetscherarbeit" zwischen Sozialwissenschaft und Informatik – zuvor mussten Inhalte ständig zwischen Word-Dokumenten und technischen Formaten übersetzt werden. Bewertet als „Gamechanger".
- **Dana:** Vorher Anforderungen „in langen E-Mail-Ketten", oft mit Missverständnissen. In LLARS direktes Mitarbeiten am Prompt. Echtzeitkollaboration gibt das Gefühl, „wirklich zusammen an derselben Sache zu arbeiten".
- **Mara:** Bridging zwischen Entwickler:innen und Domain-Expert:innen als zentraler Mehrwert. Bessere Zusammenarbeit als mit Word, paralleles Arbeiten möglich.
- **Mark:** LLARS schließt die Lücke zwischen „Sozis" und Entwickler:innen.
- **Nico:** Gemeinsamer Ort für Prompt-Synchronisation schafft gegenseitiges Verständnis.

**Aggregiert:** 5 von 7 Befragten thematisieren explizit die verbesserte interdisziplinäre Zusammenarbeit. Domain Expert:innen bewerten vor allem den Wegfall von Übersetzungsarbeit, Entwickler:innen den gemeinsamen Zugriffspunkt.

### 2. Prompt Engineering

**Stärken (übergreifend):**
- Blockbasierte Struktur wird durchgängig positiv bewertet (Mark: „Blöcke sind super", Eric: „Blöcke werden sofort erkannt", Mara: Rolle/Kontext/Output-Struktur hilfreich)
- Domain Expert:innen können direkt am Prompt mitarbeiten, ohne technische Details verstehen zu müssen (Dana, Jennifer)
- Version Control sofort verständlich für Entwickler (Eric, Nico)

**Schwächen (übergreifend):**
- Variablen-UX noch nicht intuitiv genug – Mehrfach genannt (Mark, Eric, Dana)
- Technische Begriffe (Temperature, System Prompt) brauchen Erklärungen/Tooltips für Nicht-Techniker:innen (Dana, Mara)

### 3. Evaluation

**Stärken (übergreifend):**
- Evaluationstypen sofort verständlich: Fake/Echt „direkt klar" (Mark), Rating/Ranking intuitiver als Excel (Maria, Dana)
- Drag-and-Drop-Ranking wird als spielerisch und angenehm empfunden (Dana, Mara)
- Mehrdimensionales Rating passend für Beratungsforschung (Dana)
- Fortschrittsanzeige hilfreich bei verteilter Arbeit über mehrere Sitzungen (Jennifer, Dana)
- Vergleich menschliche vs. LLM-Bewertungen als „spannend und lehrreich" (Dana)

**Schwächen (übergreifend):**
- Bei sehr großen Textmengen wird Bewertung schwieriger (Mara)
- Wunsch nach Kommentarfunktion an Bewertungen (Dana)
- Loading-Animationen fehlen (Eric)

### 4. Gesamteindruck & Zeitersparnis

- **Zeitersparnis:** Explizit genannt von Mark, Jennifer, Eric. Jennifer: „stark beschleunigt" gegenüber Word-basiertem Workflow.
- **Intuitiv:** Maria (einfacher als Excel), Mara (sehr intuitiv), Mark (Lernkurve, wird mit Zeit angenehmer)
- **Gamification:** Jennifer hebt Spaßfaktor und Motivationssteigerung hervor
- **Produktreife:** Mark bewertet LLARS als „produktnah/produktreif"

### 5. Batch Generation

Wird in keinem Interview explizit kommentiert. Nico erwähnt den E2E-Workflow (Prompt → Generation → Evaluation) positiv, ohne auf Batch Generation im Detail einzugehen.

---

## Zentrale Verbesserungswünsche (priorisiert nach Häufigkeit)

| Wunsch | Genannt von | Häufigkeit |
|--------|-------------|:----------:|
| Variablen-UX verbessern / besser erklären | Mark, Eric, Dana | 3× |
| Tooltips für technische Begriffe | Dana, Mara, Jennifer | 3× |
| Mehr Tutorials / Self-Explanatory | Jennifer, Dana | 2× |
| REST/Webhook-Schnittstellen | Eric | 1× |
| No-Code-Baukasten für Evaluation | Jennifer, Eric | 2× |
| Kommentare an Bewertungen | Dana | 1× |
| SPSS/R-Export | Dana | 1× |

---

## Limitationen

- **Overfitting auf Testdaten** (Mara): Prompts wurden auf Testfälle optimiert und performten in realer Anwendung schlechter – relevante methodische Limitation
- **Synchronisierte Arbeitsweise kann verlangsamen** (Nico): Ob netto Zeit gespart wird, bleibt schwer messbar – der Mehrwert ist eher qualitativ

---

## Schlüsselzitate fürs Paper

| Zitat | Person | Thema |
|-------|--------|-------|
| Wegfall der „Dolmetscherarbeit" zwischen Disziplinen | Jennifer | Bridging the Gap |
| „Wirklich zusammen an derselben Sache arbeiten" | Dana | Kollaboration |
| „Blöcke sind super" | Mark | Prompt Engineering |
| „Direkt klar, was zu machen ist" | Mark | Evaluation |
| „Lohnt sich, dranzubleiben" | Maria | Gesamteindruck |
| LLARS als „genau das richtige Werkzeug" | Dana | Gesamteindruck |
| Bridging als zentraler Mehrwert | Mara | Kollaboration |
| LLM-Bewertungen neben eigenen: „spannend und lehrreich" | Dana | Evaluation |
