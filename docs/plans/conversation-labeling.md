# Umsetzungsplan: Szenariotyp „Konversationslabeling"

> Stand 2026-07-30 · Repo `llars` · Auftraggeber: VRM-Korpus-Projekt
> Spezifikation: `vrm-corpus/docs/konzept-llars-konversationslabeling.md`
> Briefing: `vrm-corpus/docs/handoff-llars-konversationslabeling.md`
> Fachlicher Hintergrund: `vrm-corpus/docs/gemco-phase4-design.md`

**Kern in einem Satz:** Ein Item ist ein ganzes Beratungsgespräch, gelabelt
werden die einzelnen Berater-**Spans** darin — der Reihenfolge nach, mit dem
Gesprächsverlauf sichtbar darüber.

Mengengerüst der ersten Studie: 86 Gespräche · 342 Berater-Nachrichten ·
**8.307 Spans** · 2 Annotator:innen · Median 92 Spans pro Gespräch.

---

## 0. Vorabprüfung (erledigt)

- [x] Spezifikation, Handoff, Phase-4-Design, Daten-README und offene
      Entscheidungen gelesen
- [x] Alle Code-Behauptungen des Handoffs gegen das Repo verifiziert —
      stimmen punktgenau
- [x] **§6-Invarianten live gegen prod geprüft:** Szenario 758 / part p1 →
      `item_count 100 · rater_count 2 · cohens_kappa 0.6628 · fleiss_kappa
      0.6616 · krippendorff_alpha 0.6633 · percent_agreement 76.0` — exakt die
      Sollwerte. Das ist die Baseline, gegen die nach der Migration erneut
      gemessen wird.
- [x] Geklärt, dass `/api/v1/scenarios/<id>/metrics` über
      `AgreementMetricsService.calculate_all_metrics` läuft und **nicht** über
      `get_progress_stats` — der Pfad ist von jüngeren Stats-Änderungen
      unberührt.
- [x] `function_type_id` 6 ist eine zurückgezogene Alt-ID (ehemals „judge"),
      keine Datenzeile nutzt sie mehr (prod geprüft)

---

## 1. Designentscheidungen

Begründet festgehalten, damit später nachvollziehbar ist, warum es so aussieht.

### D1 — Eigener `function_type_id 9`, nicht Variante von 7

`EvaluationSession.vue` wählt das Interface **szenarioweit** über den
Function-Type-Namen, nicht pro Item. Ein Gespräch-Item innerhalb eines
Typ-7-Szenarios bekäme das klassische `LabelingInterface`. Mischbetrieb müsste
man erst bauen — und würde ausgerechnet an Szenario 758 schrauben, dessen
p1-Votes, Zeiten und Kontrollsubset-Salt laut Invariante unangetastet bleiben.

Präzedenzfall im Repo: `communication_comparison` bekam eine eigene ID (8),
obwohl es `ComparisonInterface` mit einer Mode-Prop wiederverwendet. Genau
dieses Muster wird hier übernommen: **eigener Typ, maximale Wiederverwendung
der Labeling-Codepfade darunter.**

Nicht die freie Lücke 6 nehmen — die ist historisch als „judge" vergeben und
taucht so in alten Backups und Kommentaren auf. Anhängen ist billiger als
Verwechslungsgefahr.

### D2 — Name: technisch `conversation_labeling`, UI „Konversationslabeling"

Der Content-Typ heißt in der Spezifikation `conversation_labeling`; das ist der
API-Vertrag mit `vrm-corpus`. Function-Type und Content-Typ gleich zu benennen
hält eine Sache bei einem Namen.

Bewusst **nicht** „Kommunikationslabeling" analog zu „Kommunikationsvergleich":
`communication_comparison` heißt so, weil dort der *Beratungskontext* das
Unterscheidungsmerkmal ist (A/B mit „was würdest du senden"). Hier ist das
Unterscheidungsmerkmal die *Konversationsstruktur* (Item = Verlauf, Vote =
Span) — das trifft „Konversation" genauer und deckt sich mit dem Vertrag.

### D3 — `span_id` als Spalte auf **drei** Tabellen

Das Handoff nennt zwei; es sind drei:

| Tabelle | Constraint heute |
|---|---|
| `item_labeling_evaluations` | `uix_user_item_scenario_labeling` |
| `labeling_copilot_logs` | `uix_user_item_scenario_copilot_log` |
| **`evaluation_item_timings`** | **`uix_user_item_scenario_timing`** |

Ohne die dritte scheitert „Zeit pro Span": der erste Span schreibt die Zeile,
die weiteren ~91 prallen am Duplikatschutz ab — und die Amortisationsrechnung
(≈14 s/Span) wäre nicht messbar.

Form überall gleich: `span_id VARCHAR(64) NOT NULL DEFAULT ''`, Leerstring =
„ganzes Item" (klassischer Typ). MariaDB behandelt `NULL` in Unique-Keys als
verschieden — ein nullable Feld würde den Duplikatschutz für die bestehenden
Typen aufheben. Migration rein additiv, **kein Backfill**.

### D4 — `span_id` = globale `span_uid` aus dem Import

Empfehlung an `vrm-corpus`: `gemco_A/1/m2/s003` statt item-lokal `m2-s003`.
Bei ~17.000 Zeilen (8.307 × 2 Rater) kostet der längere Key nichts und kauft:
Exporte sind direkt auf `gemco-vrm-spans-v1.jsonl` joinbar, ohne Umweg über
LLARS-`item_id`, und die IDs überleben unterschiedliche ID-Vergaben zwischen
dev/staging/prod. `VARCHAR(64)` reicht; der zusammengesetzte Unique-Key bleibt
weit unter dem InnoDB-Limit.

LLARS erzwingt das Format **nicht** — jeder stabile String ≤ 64 Zeichen geht.

### D5 — Text einmal, Spans als Offsets

`messages[].content` speichert den Text; `spans[]` referenziert
`start`/`end`. Bei 8.307 Spans über 86 Gespräche ist das der Unterschied
zwischen ~1 MB und ~100 MB. `text` im Span bleibt optional erlaubt (Import darf
es mitliefern), ist aber redundant und wird serverseitig gegen die Offsets
validiert.

### D6 — Fortschritt zählt Spans

Item-Status `done`, wenn **alle** Spans des Gesprächs gelabelt sind.
Assessor-Fortschritt, Parts-Fortschritt und die Items-Übersicht zählen Spans,
nicht Items. `parts.size` zählt weiterhin **Items** — was hier Gespräche sind,
also genau das Gewünschte; kein Codeeingriff nötig.

### D7 — Co-Pilot: Schlüsselung `(user, item, span)`

Kontrollsubset-Zuweisung über `(salt, user, item, span_id)`. Der `salt` des
Szenarios bleibt unangetastet. `{context}` wird **serverseitig** aus dem Verlauf
gebaut (bis einschließlich Zielspan) statt aus `metadata.context` — damit sehen
Mensch und Modell garantiert dasselbe Fenster.

### D8 — Migration nach Repo-Muster, Index-Tausch in EINEM Statement

Das Repo hat kein Alembic, sondern idempotente Module unter
`app/db/migrations/`, beim Start aus `app/main.py` aufgerufen und über
`INFORMATION_SCHEMA` gegen Doppelausführung geschützt (Vorbild:
`migrate_evaluation_items_metadata.py`). Dasselbe Muster hier.

Ein Detail, das über „additiv" hinausgeht: der Unique-Key muss **erweitert**
werden, nicht nur eine Spalte dazu. Drop und Add gehören deshalb in **ein**
`ALTER TABLE` — sonst gibt es ein Fenster ohne Duplikatschutz:

```sql
ALTER TABLE item_labeling_evaluations
  ADD COLUMN IF NOT EXISTS span_id VARCHAR(64) NOT NULL DEFAULT '',
  DROP INDEX uix_user_item_scenario_labeling,
  ADD UNIQUE KEY uix_user_item_scenario_span_labeling
      (user_id, item_id, scenario_id, span_id);
```

Bestehende Zeilen bekommen `''` und bleiben damit exakt so geschützt wie
vorher. Kein Backfill, kein Umschreiben.

### D10 — Span-Struktur in `EvaluationItem.metadata_json`, Text in `messages`

`Message` hat keine Metadatenspalte (`message_id, item_id, sender, content,
timestamp, generated_by`) — die Spans können also nicht an der Nachricht hängen.

Gewählt: Nachrichten wandern wie gewohnt in `messages`-Zeilen (Text genau
einmal, D5 bleibt gewahrt), die Span-Struktur landet unter einem reservierten
Schlüssel in `EvaluationItem.metadata_json`:

```jsonc
{
  "…": "vorhandene Forschungs-Metadaten bleiben unangetastet",
  "conversation_labeling": {
    "spans": [
      {"span_id": "gemco_A/1/m2/s001", "message_index": 1, "message_id": 2,
       "span_index": 0, "start": 0, "end": 26}
    ]
  }
}
```

Begründung gegen eine eigene Tabelle: Spans sind unveränderliche
Import-Artefakte (Invariante 5 — Unitizing eingefroren, in der UI nicht
editierbar). Es gibt keine Schreibpfade, keine Beziehungen, keine Abfragen
gegen einzelne Spans außer „alle eines Items" — dafür ist ein JSON-Array
billiger als ein Join, und es spart eine zweite Migration. Mengengerüst: ~92
Spans à ~80 Byte = ~7 KB je Item, 86 Items ≈ 600 KB.

`message_index` (Position im Array) ist der Verbindungsschlüssel zur
gerenderten Nachrichtenliste; die `message_id` des Imports wird zusätzlich
mitgeführt, weil der Export sie laut Spezifikation ausweisen muss.

Der reservierte Schlüssel ist bewusst namensgeräumt — Forschungs-Metadaten der
Studie dürfen nicht überschrieben werden.

### D11 — Eine gemeinsame Typ-Familie statt `or` an jedem Branch

`services/evaluation/labeling_types.py` definiert `is_labeling_type()` und
`is_span_labeling()`. Die ~20 Stellen, die heute auf `'labeling'` prüfen,
fragen die Familie ab statt zu vergleichen.

Grund ist die Erfahrung mit Typ 8: dort wurde an jeder Stelle einzeln ein
Vergleich angehängt — und ein Dutzend Dispatcher wurde übersehen, bis heute.
Eine dritte Labeling-Variante später heißt: diese Datei ändern, nicht Branches
suchen. Spiegelt das vorhandene `COMPARISON_FUNCTION_TYPE_IDS = (4, 8)`-Idiom.

### D9 — Rückwärtskompatibilität ist ein Testgate, keine Absicht

Vor und nach der Migration werden die drei §6-Abfragen gefahren. Weicht κ ab,
ist die Migration falsch — nicht die Metrik.

---

## 2. Offene Rückfragen an `vrm-corpus`

Blockieren den Import auf deren Seite, nicht den Bau hier.

- [ ] **Q1 `span_id`-Format** — Empfehlung D4 (globale `span_uid`)
- [ ] **Q2 Item-Schema** liefern, damit `analysis/gemco_phase4.py` gebaut werden kann
- [ ] **Q3 Parts** — beantwortet: `size` zählt Items = Gespräche, keine
      expliziten `item_ids` nötig
- [ ] **Q4 758 oder eigenes Szenario** — beantwortet: eigenes Szenario (D1)

Antworten nach `vrm-corpus/docs/offene-entscheidungen.md` (Zeilen 2c/2d).

---

## 3. Touchpoints

### 3.1 Fallen, die aus der Repo-Analyse kamen

- **`app/db/seeders/schema_patches.py:1397–1427`** legt `item_labeling_evaluations`
  per `_ensure_table` inklusive Unique-Key an. Wird das nicht mitgezogen,
  bekommt jede **frische** DB den alten Key — die Migration repariert nur
  bestehende Instanzen. Beide Stellen müssen dasselbe sagen.
- **„Done" wird an vier Stellen unabhängig berechnet**, alle vier brauchen den
  Begriff „alle Spans gelabelt":
  `session_service.py:355` (Batch) · `session_service.py:650` (Einzelitem) ·
  `scenario_stats_service.py:635–638` · `scenario_parts_service.py:611`
- **Config-Unwrap-Reihenfolge unterscheidet sich** zwischen Backend
  (`locate_inner_config`: `eval_config.config` → `config.config` → …) und
  Frontend (`LabelingInterface.vue:420`: `config.config` →
  `config.eval_config.config` → …). Beim neuen Interface die Backend-Reihenfolge
  übernehmen, nicht die alte Frontend-Variante kopieren.
- **Keys sind gemischt snake_case/camelCase in freier Wildbahn** (`labels` vs.
  `categories`, `allowUnsure`, `minLabels`). Jeder Leser toleriert beides — der
  neue Code muss das auch.
- **Der Co-Pilot-Cache ist pro Item geschlüsselt**
  (`LLMTaskResult(scenario_id, item_id, model_id, task_type)`); für Vorschläge
  pro Span braucht es eine Span-Dimension.
- **`LabelingInterface.vue` hat keinerlei Tastaturbedienung** — die Tastatur ist
  komplett neu zu bauen, nicht zu übernehmen.
- **Export:** `feature_id`/`dimension_id` sind bei Labeling ungenutzt. Trotzdem
  **nicht** zweckentfremden — die Spezifikation verlangt echte Spalten
  `span_id`/`message_id`/`span_index`. Diese **hinten anhängen**, damit
  bestehende Konsumenten die Spaltenreihenfolge behalten;
  `APIV1_RES_001` prüft genau diese Reihenfolge und wird mitgezogen.

### 3.2 Was bei Typ 8 **vergessen** wurde — hier nicht wiederholen

Die wertvollste Erkenntnis der Analyse: `communication_comparison` ist bis heute
an über 20 Stellen nicht registriert. Zwei davon sind echte Bugs im Feld:

- `api_v1/scenarios_routes.py:53–60` — `_FUNCTION_ID_TO_TYPE` ohne `8`, der
  v1-Serializer fällt still auf `RATING` zurück (steht als „Serializer-Eigenheit"
  in der Studien-Doku, ist aber schlicht ein fehlender Map-Eintrag)
- `llm_ai_task_runner.py:493–521` — kein Branch, LLM-Evaluatoren werden
  eingereiht und laufen nie

Beide Muster (Vorwärts-Map ohne Rückwärts-Map, Dispatcher ohne Branch) sind
genau die, die man beim Hinzufügen eines Typs übersieht. **Deshalb wird für den
neuen Typ jeder Dispatcher paarweise geprüft.**

### 3.3 Registrierungspunkte — Reihenfolge nach „was zuerst bricht"

**A. Fundament**
- [x] `app/db/seeders/feature_types.py` — `(9, 'conversation_labeling')` + Begründungskommentar
- [x] `app/db/seeders/schema_patches.py:1397–1427` — Unique-Key der
      `_ensure_table`-Definition mitziehen (sonst falscher Key auf frischer DB)
- [x] `tests/unit/routes/conftest.py:477–493` — `seed_function_types`-Fixture

**B. Pydantic-Schicht**
- [x] `EvaluationType.CONVERSATION_LABELING` + `from/to_function_type_id`
- [x] `ConversationLabelingConfig`, `ConversationLabelingContent`, `Span`
- [x] `EvaluationConfig`-Union + `api_v1/scenario_api.py` `EvalConfig`-Union
      (**Subklasse vor Elternklasse**, sonst schluckt der Parent)
- [x] `_config_matches_type`-Validator-Map
- [x] `NativeItem.content`-Union um den neuen Content-Typ erweitern

**C. Beide Richtungen der Typ-Maps**
- [x] `api_v1_scenario_service._TYPE_TO_FUNCTION_ID`
- [x] `api_v1/scenarios_routes._FUNCTION_ID_TO_TYPE` ← die vergessene Richtung
- [x] `schema_export_service.EVALUATION_TYPE_INFO` (**testerzwungen**: jeder
      Enum-Member braucht Eintrag, ≥2 Detection-Hints, ≥1 Use-Case)

**D. Namens-Dispatcher im Backend**
- [x] `session_service` — `_batch_status_for_threads`, `_get_thread_evaluation_status`,
      `_batch_get_saved_evaluations` (Span-Votes!)
- [x] `scenario_stats_service` — Progression, Distribution-Gate, Pairwise-Gate,
      Distribution-Branch, Assessor-Nenner
- [x] `results_export_service` — `_FUNCTION_TYPE_NAME`, Collector-Dispatch, LLM-Extraktion
- [x] `agreement_metrics_service` — Dispatch, `_collect_human_evaluations`, `_extract_value`
- [x] `HelperFunctions` — `PROGRESSION_HANDLERS`, Distribution-Mode
- [ ] `scenario_manager_api` — Data-Tab-Status, Item-Detail, Eval-Tab-Export
- [x] `llm_ai_task_runner` — Dispatch-Branch (bei Typ 8 vergessen)
- [x] `schema_transformer_service` — Dispatch-Branch (bei Typ 8 vergessen)
- [x] `scenario_resources.FUNCTION_TYPE_UI_META`, `scenario_schema_api` types-Liste,
      `wizard_routes.eval_types`

**E. Frontend-Kern**
- [x] `evaluationSchemas.js` — `EvaluationType`, `FUNCTION_TYPE_MAP`, `EVALUATION_TYPE_TO_ID`
- [x] `EvaluationSession.vue` — Interface-Map → `ConversationLabelingInterface.vue`
- [x] `useEvaluationSession.js` `FUNCTION_TYPE_MAP` (bei Typ 8 vergessen)
- [x] `EvaluationScenario.vue` `TYPE_CONFIG` inkl. `itemRoute` (bei Typ 8 vergessen)

**F. Die sieben `typeConfig`-Maps** (Icon/Farbe/Label)
- [x] `EvaluationHub.vue` · `EvaluationItemsOverview.vue` · `ScenarioWorkspace.vue`
      · `ScenarioCard.vue` · `ScenarioInviteCard.vue` · `ScenarioOwnerCard.vue`
      · `ScenarioOverviewTab.vue`

**G. Wizard, Presets, Admin, Landing**
- [x] `evaluationPresets.js` — `PRESETS_BY_TYPE`, `DEFAULT_CONFIG_BY_TYPE`,
      `TYPE_INFO`, `BASE_TYPE_MAP`, `isLlarsType`, Kategorie-Funktionen
- [x] `ScenarioWizard.vue` — `getTypeVariant`, `getTaskType`, AI-Detection-Map
- [x] `EvaluationConfigEditor.vue` Prop-Validator + Konfig-Editor
- [x] `AdminScenariosSection.vue` — fünf Maps
- [x] `EvalTypesSection.vue` + `TechSection.vue`-Zähler hochsetzen
- [ ] `DataFormatGuide.vue` — Beispielblock

**H. i18n (beide Locales, zwei Konventionen)**
- [x] `scenarioManager.types.conversationLabeling` (camelCase)
- [x] `evaluation.types.conversation_labeling` (snake_case)
- [x] `landing.evalTypes.types.conversation_labeling.{title,desc}`
- [x] `evaluation.conversationLabeling.*` fürs Interface

**I. Harte Zählwerte in Tests**
- [x] `evaluationSchemas.spec.js` „exactly 7 types"
- [x] `evaluationPresets.spec.js` „exactly 7 types", `getLlarsTypes`-Array
- [ ] `test_schema_export_service.py` Typ→ID-Tabelle
- [ ] `api_v1_results` Spaltenreihenfolge (neue Export-Spalten)

**J. Doku**
- [ ] `docs/docs/entwickler/evaluation-datenformate.{md,en.md}` — Tabellenzeile + Abschnitt
- [ ] `docs/docs/guides/conversation-labeling.{md,en.md}` + `mkdocs.yml`-Nav
- [ ] `CLAUDE.md` function_type-Tabelle
- [ ] `CHANGELOG.md` + `docs/docs/changelog.md` (beide!)

---

## 4. Phasen

### Phase 1 — Datenmodell, Schema, Import

**Migrationsnachweis (lokal, echte MariaDB, 44 Bestands-Votes):**

| Prüfung | Ergebnis |
|---|---|
| Spalte auf allen drei Tabellen | `varchar(64) NOT NULL DEFAULT ''` |
| Unique-Keys | alle drei auf `(user_id, item_id, scenario_id, span_id)` |
| Bestandszeilen | 44 vorher → 44 nachher, alle `span_id = ''` |
| Idempotenz | zweiter Lauf `changed = False`, alle drei `already_current` |
| Duplikatschutz Altdaten | zweiter Insert mit `span_id=''` → `Duplicate entry` ✔ |
| Mehrere Spans je Item | `m2-s001` + `m2-s002` nebeneinander akzeptiert ✔ |

Die letzten beiden Zeilen sind der eigentliche Punkt: hätte man `span_id`
nullable gemacht, wäre der vorletzte Insert **durchgegangen** — MariaDB
behandelt NULL in Unique-Keys als verschieden. Der Leerstring hält den Schutz.

Die Migration lief unbeaufsichtigt beim Neuladen des Dev-Servers durch, also
genau auf dem Weg, den sie in Produktion nehmen wird.
- [x] `span_id` auf die drei Tabellen, Unique-Keys erweitert, additive Migration
- [x] `ConversationLabelingContent` + `Span`/`LabelableMessage` in
      `evaluation_data_schemas.py`
- [x] `ConversationLabelingConfig` (erbt `LabelingConfig` + `context_window`,
      `future_spans`, `no_future_messages`)
- [x] `EvaluationType.CONVERSATION_LABELING`, Typ→Config-Validator, Typ→ID-Map
- [x] Function-Type 9 im Seeder
- [x] v1-Importer: Content-Typ akzeptieren, Spans persistieren, Offsets validieren
- [ ] **Regressionsgate:** §6-Abfragen gegen lokale Kopie vor/nach Migration

### Phase 2 — Bewertungsoberfläche
- [x] `ConversationLabelingInterface.vue`: Verlauf links, Fokus-Span rechts
- [x] Gelabelte Spans zeigen ihr Label inline
- [x] Tastatur: 1–9 Modus, Enter speichern+weiter, Backspace zurück
- [x] Wiedereinstieg springt zum ersten unbeschrifteten Span
- [x] Auto-Save bei Auswahl (Pflicht — eingebettete Interfaces haben keinen
      Speichern-Button)
- [x] Registrierung in `EvaluationSession.vue`

### Phase 3 — Fortschritt und Status auf Span-Ebene
- [x] Session-Payload trägt gespeicherte Votes pro Span
- [x] Save-Endpoint nimmt `span_id`
- [x] Fortschritt in Session, Parts und Items-Übersicht zählt Spans
- [x] Zeit pro Span, first-write-only; erster Span einer Nachricht erkennbar

### Phase 4 — Co-Pilot auf Span-Ebene
- [x] Schlüsselung `(user, item, span)`, Kontrollsubset span-weise gesalzen
- [ ] `{context}` serverseitig aus dem Verlauf
- [ ] Batch-Generierung: Mengengerüst 8.307 Calls, Fortschritt nach Spans

### Phase 5 — Export und Metriken
- [ ] Export-Zeilen tragen `span_id`, `message_id`, `span_index`;
      bestehende Spalten unverändert
- [ ] Agreement-Zellen `(span, rater)`; `?part=` und `?copilot=` funktionieren weiter

### Phase 6 — Szenario-Manager, Wizard, Rundum
- [ ] Icon + Farbe + i18n-Label im Evaluierungs-Hub
- [ ] Szenario-Manager-Tabs, Wizard, Presets, DataFormatGuide
- [ ] Demo-Seeder
- [ ] Doku DE+EN unter `docs/docs/guides/`, in `mkdocs.yml` registriert
- [ ] CHANGELOG-Eintrag

### Phase 7 — Test und Abnahme
- [ ] Backend-Unit-Tests, Frontend-Unit-Tests
- [ ] Lokal durchspielen: Szenario per v1-API anlegen, zu zweit labeln,
      exportieren, Metriken prüfen
- [ ] Chrome-Durchlauf der Oberfläche
- [ ] Nightly-Tile-Contract prüfen (falls Kachel betroffen)

---

## 5. Invarianten (nicht aufweichen)

1. Co-Pilot-Vorschläge **nie vorausgewählt** — Übernahme braucht eine bewusste
   Aktion. Im Sequenzmodus kritischer als bisher: bei 24 Spans hintereinander
   entsteht sonst ein Bestätigungsrhythmus.
2. Verdecktes Kontrollsubset **nur serverseitig**, ununterscheidbar von „kein
   Vorschlag". Salt und Ratio von 758 nie nachträglich ändern.
3. Prompt-Versionierung: jede Prompt-/Codebook-/`top_k`-Änderung bumpt die
   Version; Item→Version bleibt Audit-Trail.
4. Zeit = **first-write only**. Revisits überschreiben nicht.
5. Unitizing ist eingefroren — Spans kommen aus dem Import und sind in der UI
   **nicht editierbar**. Falsche Grenzen werden über eine Label-Karte gemeldet.
6. `oncoco_*` ist Analyse-Metadatum und wird Annotator:innen **nie** angezeigt.
7. Beratungstexte nur über den KIZ-LiteLLM-Proxy, nie an öffentliche APIs.
8. Bestehender Labeling-Typ verhält sich **bitgenau unverändert**
   (Szenarien 758 und 873 sind der Testfall).
