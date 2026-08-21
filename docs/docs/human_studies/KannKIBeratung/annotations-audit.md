# Kann KI Beratung? — Annotations-Audit

Die **fachlichen Anmerkungen aus den Sozialwissenschaften** definieren die
Studienanforderungen für „Kann KI Beratung?". Diese Seite auditiert, was davon
in LLARS umgesetzt ist und was fehlt — mit Status und `file:line`-Belegen.

Status-Legende: **Implementiert** · **Teilweise** · **Fehlt** ·
**Implementiert (Merge ausstehend)**.

> Hinweis zu Branch-Ständen: Die meisten Funktionen sind auf `main` (Produktion)
> implementiert. Die einmalige „Herzlichen Dank"-Bestätigung liegt auf einem
> separaten Branch (Commit `78130f9f`) und ist noch nicht nach `main` gemerged
> → **implementiert (Merge ausstehend)**. Pfade unten beziehen sich auf den
> jeweils belegenden Branch.

## Überblick

| # | Anforderung (aus den Sozialwissenschaften) | Status |
|---|--------------------------------------------|--------|
| 1 | Startseiten-Aufgabentext (Aufgabe 1) | **Implementiert** |
| 2 | Pro-Fall-Aufgabentext (Aufgabe 2) | **Implementiert** |
| 3 | 3 demografische Fragen bei/nach der Registrierung | **Implementiert** |
| 4 | Auswertungs-Popup nach je 5 Fällen (bevorzugt Mensch / trainierte KI / Standard-KI; schaltet 5 weitere frei) | **Implementiert** |
| 5 | Einmalige „Herzlichen Dank … klicken Sie auf Weiter"-Bestätigung nach dem ersten gespeicherten Vergleich | **Implementiert (Merge ausstehend)** |
| 6 | Bearbeitungsstatus pro Fall-Kachel (Ausstehend / Abgeschlossen) | **Implementiert** |

---

## 1 · Startseiten-Aufgabentext (Aufgabe 1) — Implementiert

**Anforderung (Wortlaut):** „Herzliche Dank für Ihre Bereitschaft an unserer
Testung mitzuwirken! Wir haben Ihnen zu Beginn 5 Fallvignetten bereitgestellt …
Bearbeitungsstatus (z. B. Ausstehend oder Abgeschlossen). Nach jeweils 5
abgeschlossenen Fällen erhalten Sie eine Auswertung … weitere 5 Fälle … Starten
Sie die Testung, indem Sie den 1. Fall durch Anklicken der Kachel auswählen."

**Umsetzung:**

- Der Text ist als `welcome_markdown` (DE/EN) in der Studien-Eval-Config
  hinterlegt: `EMNLP2026/data/human_study/v15/eval_config.json` (Schlüssel
  `eval_config.config.welcome_markdown`, Wortlaut deckt sich mit der
  Anforderung).
- Gerendert wird er als **Briefing-Banner** über den Item-Kacheln:
  - `llars-frontend/src/views/Evaluation/EvaluationItemsOverview.vue:48`
    (Briefing-Banner-Block).
  - `llars-frontend/src/views/Evaluation/EvaluationItemsOverview.vue:59-60`
    (`taskMarkdown` → `<LMarkdownContent>`).
  - `llars-frontend/src/views/Evaluation/EvaluationItemsOverview.vue:335`
    (`taskMarkdown` computed; löst Briefing-/Welcome-Markdown auf und
    substituiert Variablen wie `{{channel_label}}`).
  - `llars-frontend/src/views/Evaluation/EvaluationItemsOverview.vue:345`
    (`hasBriefing`).

**Befund:** Anforderung erfüllt — Text steuerbar über die Eval-Config,
Rendering vorhanden.

---

## 2 · Pro-Fall-Aufgabentext (Aufgabe 2) — Implementiert

**Anforderung (Wortlaut):** „Worum geht's? … Lesen Sie den Verlauf; lesen Sie
die zwei Antwortmöglichkeiten; entscheiden Sie; wählen Sie „Option A/B wählen";
„Weiter"/„Zurück". Hinweis: auch wenn beide ungeeignet erscheinen, bitte dennoch
entscheiden."

**Umsetzung:**

- Text als `task_description_markdown` (DE/EN) in
  `EMNLP2026/data/human_study/v15/eval_config.json`
  (`eval_config.config.task_description_markdown`) — enthält die 5
  nummerierten Schritte und den „dennoch entscheiden"-Hinweis wortgleich.
- Auflösung + Rendering im Comparison-Interface:
  - `llars-frontend/src/views/Evaluation/interfaces/ComparisonInterface.vue:492`
    (`_readTaskDescriptionMarkdown`, liest `taskDescriptionMarkdown` /
    `task_description_markdown` aus der Config).
  - `llars-frontend/src/views/Evaluation/interfaces/ComparisonInterface.vue:562`
    (Fallback auf die Frage, wenn kein Aufgabentext gesetzt ist).
- Bewerter-Aktionen, auf die der Text verweist, sind vorhanden:
  „Option A/B wählen" (`selectA`/`selectB`-Buttons), „Weiter"/„Zurück"
  (Navigations-Footer) — im Comparison-Interface.

**Befund:** Anforderung erfüllt — inkl. der zwei Antwort-Optionen, der A/B-
Auswahl und der Weiter/Zurück-Navigation.

---

## 3 · Drei demografische Fragen — Implementiert

**Anforderung:** 3 demografische Fragen bei/nach der Registrierung.

**Umsetzung:**

- Datenmodell `UserDemographics` (1:1 zu User), einmaliger Survey:
  - `app/db/models/user_demographics.py:23` (Klasse).
  - Felder: `gender` (`:45`), `age_range` (`:48`), `education` (`:51`) — die
    **drei Pflicht-/Kernfragen** —, plus optionales Freitext-Feld `profession`
    (`:54`); `completed_at` (`:67`) markiert „einmalig erledigt".
- Backend-Routen:
  - `app/routes/user_settings/user_demographics_routes.py:45` (`GET` — liefert
    `completed: true`, sodass das Frontend den Survey unterdrückt).
  - `app/routes/user_settings/user_demographics_routes.py:81` (`POST`) mit
    Validierung von `gender`/`age_range`/`education` (`:94-96`) und optionaler
    `profession` (`:98`).
- Frontend-Survey-Dialog (3 Sektionen Gender / Age / Education + optional
  Profession):
  - `llars-frontend/src/components/Onboarding/DemographicSurveyDialog.vue:28`
    (Gender), `:43` (Age), `:58` (Education).
- Auslösung (einmalig, primär für Referral-Signups):
  - `llars-frontend/src/App.vue:130-133` (`<DemographicSurveyDialog>`),
    `:310` (`checkDemographicSurvey()`).

**Befund:** Anforderung erfüllt — drei kontrollierte Fragen (Geschlecht,
Altersgruppe, Bildung) plus optionales Berufsfeld; einmalig, alle Felder
optional beantwortbar, Wiederanzeige unterdrückt.

---

## 4 · Auswertungs-Popup nach je 5 Fällen — Implementiert

**Anforderung:** Nach 5 abgeschlossenen Fällen ein Auswertungs-Popup
(bevorzugt Mensch / trainierte KI / Standard-KI) → schaltet die nächsten 5 frei.

**Umsetzung:**

- Config: `gamification_first_milestone:5`,
  `gamification_recurring_milestone:5`, `progressive_reveal:true`
  (`EMNLP2026/data/human_study/v15/eval_config.json`).
- Milestone-Logik:
  - `llars-frontend/src/composables/useComparisonEvaluation.js:82`
    (`milestoneEvent = { count, isFirst }`).
  - `:104-114` (liest `gamification_first_milestone` /
    `gamification_recurring_milestone`, Default 5).
  - `:121-130` (`itemsUntilNextMilestone` — Countdown).
  - `:368-374` (feuert das Milestone-Event genau einmal, wenn die abgeschlossene
    Anzahl die Schwelle erreicht — `isFirst` bzw. recurring).
- Popup-UI + Präferenz-Anteile:
  - `llars-frontend/src/views/Evaluation/interfaces/ComparisonRewardDialog.vue:41`
    (`reward-stats`), `:153-176` (Achsen `human_vs_llm` → „Mensch", und
    `trained_vs_base` → „trainiert vs. Standard").
- Aggregation der Präferenzen (Backend):
  - `app/services/evaluation/comparison_preference_stats_service.py`
    (Endpoint `GET /api/evaluation/session/:scenarioId/comparison/preferences`,
    referenziert in `ComparisonRewardDialog.vue:91`).
- Progressives Freischalten weiterer Fälle: über `progressive_reveal` /
  Milestone-Mechanik gekoppelt.

**Befund:** Anforderung erfüllt — Popup nach je 5 Fällen mit den geforderten
Präferenz-Achsen (Mensch / trainierte KI / Standard-KI) und Freischalt-Logik.

---

## 5 · Einmalige „Herzlichen Dank … klicken Sie auf Weiter" — Implementiert (Merge ausstehend)

**Anforderung:** Einmalig, nach dem **ersten** gespeicherten Vergleich, eine
Bestätigung „Herzlichen Dank! … klicken Sie auf Weiter".

**Umsetzung (Branch — Commit `78130f9f`, noch nicht auf `main`):**

- Composable mit Einmal-Gate (Backend-Flag + localStorage-Fast-Path):
  - `llars-frontend/src/composables/useFirstComparisonNotice.js`
    (`maybeShowAfterFirstSave()`; persistiert
    `preferences.firstComparisonNoticeSeen` via `GET/PUT /api/user/settings`,
    zusätzlich per-User localStorage).
- Einbindung im Interface (feuert **nach** erfolgreichem Speichern):
  - `llars-frontend/src/views/Evaluation/interfaces/ComparisonInterface.vue:152`
    (Dialog `v-model="firstNotice.noticeVisible.value"`),
    `:247` (`useFirstComparisonNotice()`),
    `:271` (`firstNotice.maybeShowAfterFirstSave()` nach dem Save).
- i18n (DE): `llars-frontend/src/locales/de.json` —
  Titel „Herzlichen Dank!", „Ihre Bewertung wurde gespeichert." (+ EN-Pendant).
- Tests: `llars-frontend/src/composables/useFirstComparisonNotice.spec.js`
  (12 Fälle).

**Befund:** Vollständig implementiert inkl. Tests, aber auf einem separaten
Branch — **Merge nach `main` ausstehend**. Auf dem aktuellen `dev`-Stand (und im
Doku-Worktree) ist die ältere `ComparisonInterface.vue` ohne diese Notice aktiv.

---

## 6 · Bearbeitungsstatus pro Fall-Kachel (Ausstehend / Abgeschlossen) — Implementiert

**Anforderung:** Pro Fall-Kachel oben der Bearbeitungsstatus (Ausstehend /
Abgeschlossen).

**Umsetzung:**

- Status-Badge je Kachel:
  - `llars-frontend/src/views/Evaluation/EvaluationItemsOverview.vue:207-210`
    (`<LEvaluationStatus :status="getItemStatus(item)">`).
  - `:481` (`getItemStatus(item)` — liefert `pending` / `in_progress` / `done`).
  - `:296-298` (Zählwerte `completedCount` / `inProgressCount` /
    `pendingCount`).
  - Filter-Chips „Ausstehend / In Bearbeitung / Abgeschlossen": `:80-98`.
- Anzeige-Komponente: `LEvaluationStatus` (Design-System, Mapping
  `done|in_progress|pending` → Labels „Abgeschlossen / In Bearbeitung /
  Ausstehend" via i18n `evaluation.status.*`).

**Befund:** Anforderung erfüllt — Status pro Kachel sichtbar, zusätzlich als
Filter nutzbar.

---

## Fehlende / offene Punkte (Zusammenfassung)

- **Nichts fachlich Fehlendes identifiziert** unter den auditierten sechs
  Anforderungen — alle sind implementiert.
- **Einzige offene Aktion:** Punkt 5 („Herzlichen Dank"-Bestätigung) ist
  implementiert, aber der **Merge des Branches `78130f9f` nach `main`** steht
  noch aus. Bis dahin ist die Funktion auf der Produktion nicht aktiv.
