# 📜 LLARS Changelog

![Version](https://img.shields.io/badge/version-1.24.0-b0ca97?style=flat-square)
![Released](https://img.shields.io/badge/released-2026--09--15-88c4c8?style=flat-square)
![Releases](https://img.shields.io/badge/releases-31-D1BC8A?style=flat-square)
![Format](https://img.shields.io/badge/format-Keep%20a%20Changelog-98d4bb?style=flat-square)

Alle nennenswerten Änderungen am **LLARS** (LLM Assisted Research System) — **neueste zuerst**.
Das Format orientiert sich an [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

**Legende:**  ✨ Neu · 🔁 Geändert · 🗑️ Entfernt · 🐛 Behoben · 🔒 Security · ⚡ Performance · 📚 Docs

> **Versionierung** — LLARS nutzt **tag-basierte semantische Versionierung** via
> `git describe --tags --match "v*" --first-parent`. Aus einem Tag `vMAJOR.MINOR.PATCH`
> ergibt sich `MAJOR.MINOR.(PATCH + N)`, wobei `N` die Anzahl Commits seit dem Tag ist;
> am getaggten Commit selbst ist `N = 0` und die Version entspricht exakt dem Tag.
> Releases werden nach jedem `dev`→`main`-Merge auf `main` getaggt (aktuell **v1.0.0 … v1.24.0**).

---

## [Unreleased]

### 🐛 Fixed

- **Labeling: Teilantworten zählen als „in Bearbeitung"** — Beim Fragen-first-Labeling kann eine Zeile in `item_labeling_evaluations` mit Antworten, Zweitwahl oder Kommentar, aber ohne Label existieren. Bisher galt sie überall als „ausstehend". Jetzt gibt es eine Drei-Wege-Regel an genau einer Stelle (`labeling_types.labeling_row_status`: Label oder „unsicher" = `done`, sonst Eingaben = `in_progress`, sonst `pending`), die Session-Status, Einzel-Status, Progression, Szenario-Statistik, Span-Fortschritt (Typ 9) und die Items-Liste des Managers gemeinsam nutzen. Der Save-Endpoint antwortet mit diesem Status statt dem alten `completed`. Teilzeilen sind **keine Votes**: Export und IRR überspringen sie, und Bearbeitungszeit sowie Co-Pilot-Log werden erst beim ersten vollständigen Label geschrieben, nicht beim ersten Klick. `LABEL_STATUS_001–026`.
- **Labeling speichert jede Auswahl sofort** — jede beantwortete Frage, jeder Lean-Slider, die Zweitwahl, die Direktwahl, „unsicher" und der Kommentar werden beim Klick persistiert (POST mit `category_id: null` + `answers_json`, solange noch kein Label ableitbar ist). Das Item wird bis zum vollständigen Label als **„In Bearbeitung"** angezeigt (Item-Liste, Session-Footer und Statuskachel im Labeling-Panel, inkl. „Speichern…"-Indikator); laufende Speicherungen werden vor dem Blättern (Weiter/Zurück, auch über die Session-Navigation) und beim Verlassen abgewartet. Zuvor ging die Arbeit verloren, wer z. B. zwei von drei Fragen beantwortet und weitergeklickt hat (Prod-Szenario 758). Es wird dabei nie ein Label vorbelegt.

## [1.24.0] - 2026-09-15

### ✨ Added

- **Fragen-first-Labeling (Labeling-Typ 7/9):** Ein Labeling-Szenario kann dem Label Entscheidungsfragen vorschalten (`questions` in der Labeling-Config: `items` mit je zwei Antwort-Optionen, `mapping` Antwortschlüssel → Label, optional `sliders` als Zusatzinfo „eher A … eher B", `direct_selection`). Annotator:innen beantworten die Fragen oben mit Buttons, das Label wird aus dem Antwortschlüssel abgeleitet und nie vorausgewählt; die Direktwahl bleibt aufklappbar und setzt die Fragen rückwärts über das Mapping. Antworten landen in `item_labeling_evaluations.answers_json` (neue Spalte, Startup-Migration `migrate_labeling_second_choice_answers.py`), im Session-Prefill und als Export-Spalte `answers_json`. Vorbild: VRM-Cheatsheet (Stiles 1992) – Thema / Präsupposition / Bezugsrahmen, je S/G. `LabelingInterface.vue`, `DecisionQuestionsConfig`, `LABEL_009–013`.
- **Zweitwahl („Platz 2") beim Labeling:** `second_choice: true` blendet nach der ersten Wahl Chips für ein zweites Label ein – kein Multilabel, das Studienlabel bleibt `category_id`; die Zweitwahl wird in `second_choice_id` gespeichert und als Export-Spalte `second_choice` ausgegeben. So gehen „beides vertretbar"-Fälle nicht verloren. `LABEL_011`, `LABEL_SVC_026`.
- **Co-Pilot beantwortet Entscheidungsfragen zuerst:** Hat das Szenario `questions`, verlangt der Format-Block jedes Vorschlags zuerst `answers` (je Frage eine Option) und dann das explizite `label_id`; der Parser trägt `answers`, `derived_label_id` (aus dem Mapping) und `consistent` durch, das explizite Label bleibt maßgeblich. Änderungen an den Fragen bumpen `prompt_version` wie `top_k`. Die Antworten erscheinen im Vorschlags-Panel. `_validate_copilot_answers`, `COPILOT_Q_001–006`.
- **v1-API `PUT /api/v1/scenarios/{id}/labeling-config`:** schaltet `questions` und `second_choice` headless per API-Key (Owner/Admin, `scenario:write`) – der generische Szenario-PUT ist session-only und der v1-PATCH lehnt `eval_config` ab, Studien-Skripte hatten also keinen Weg zu diesen Einstellungen. Validiert gegen `DecisionQuestionsConfig`, Mapping-Ziele müssen Label-IDs sein, `config.config`-Spiegel bleibt synchron. `LABEL_SET_001–007`.

### 🐛 Fixed

- **Labeling-Feedback ging beim Weiterklicken verloren:** Der Kommentar wurde mit 800 ms Verzögerung gespeichert; Navigation zum nächsten Item löschte den Timer und leerte das Feld vor dem POST. Jetzt wird ein anstehender Kommentar vor `goNext`/`goPrev`, beim Verlassen des Feldes und beim Unmount gespeichert, und ein fehlgeschlagener Save zeigt einen Snackbar statt nur `console.error`. `LABEL_012`.

## [1.23.0] - 2026-08-23

### 🔁 Changed
- **Anmeldelinks aus E-Mails sind jetzt mehrfach nutzbar** — Der passwortlose Anmeldelink in der Willkommens-Mail nach dem QR-Scan und in der Mail für zurückkehrende Teilnehmende (`/auto-login/<token>`) war bisher **einmalig**: nach dem ersten Klick war er tot, und wer die Mail später erneut öffnete, kam nicht mehr hinein. Der Link funktioniert jetzt **innerhalb seines Gültigkeitsfensters beliebig oft** — Teilnehmende scannen den QR-Code einmal, bekommen die Mail und melden sich damit bis zu **7 Tage** lang immer wieder an. Die Grenzen bleiben unverändert: strikte **TTL von 168 Stunden**, nur der SHA-256-Hash liegt in der Datenbank, und ein neu versendeter Anmeldelink **entwertet den vorherigen**. Die Mail-Texte (DE/EN) sagen das jetzt auch so („7 Tage gültig und in dieser Zeit beliebig oft nutzbar“) statt „nur einmal nutzbar“.
- **Freundliche Seite bei abgelaufenem Anmeldelink** — Wer einen abgelaufenen Link öffnet, landet nicht mehr bei „Anmeldung fehlgeschlagen“, sondern bei **„Dieser Anmeldelink ist abgelaufen“** mit Erklärung (Anmeldelinks gelten aus Sicherheitsgründen 7 Tage) und einem klaren nächsten Schritt: Über **„Passwort vergessen“** (Button führt direkt auf `/forgot-password`) können sich Teilnehmende jederzeit selbst ein eigenes Passwort setzen — E-Mail-Adresse eingeben genügt. „Zur Anmeldung“ bleibt als zweite Aktion erhalten. Zweisprachig (DE/EN).

### 🔒 Security
- **`purpose`-Spalte trennt Reset- und Anmeldelinks** — Beide Link-Arten lagen bisher ununterscheidbar in derselben Tabelle `password_reset_tokens`. Dadurch liess sich ein **Anmelde-Token an `/auth/password-reset/reset` schicken und damit das Kontopasswort ändern** — eine Berechtigung, die ein Anmeldelink nie tragen sollte, erst recht nicht als jetzt mehrfach nutzbarer 7-Tage-Link. Die neue Spalte `purpose` (`'reset'` | `'magic'`) schliesst das in beide Richtungen: `/auth/password-reset/reset` akzeptiert ausschliesslich `'reset'` (NULL/Alt-Zeilen zählen als `'reset'`), `/auth/magic-login` ausschliesslich `'magic'`. Ausserdem entwerten sich die beiden Flows nicht mehr gegenseitig: ein frischer Anmeldelink löscht keinen offenen Passwort-Reset-Link mehr und umgekehrt (das galt auch für die 2-Minuten-Sperre gegen Mail-Flooding, die sonst die Reset-Mail direkt nach dem QR-Scan verschluckt hätte). Die Migration `migrate_add_password_reset_purpose.py` läuft **idempotent beim Serverstart** — kein manuelles SQL.

## [1.22.0] - 2026-08-21

### ✨ Added
- **Neue Lizenz: PolyForm Noncommercial 1.0.0 mit Zitationsklausel** — LLARS wechselt von „MIT/Open Source“ auf die **[PolyForm Noncommercial License 1.0.0](https://github.com/th-nuernberg/llars/blob/main/LICENSE)** mit zusätzlichen Bedingungen: **kostenlos für Forschung, Lehre und jede andere nicht-kommerzielle Nutzung** (Hochschulen, Behörden und gemeinnützige Organisationen ausdrücklich eingeschlossen, unabhängig von der Finanzierungsquelle), **kommerzielle Nutzung erfordert eine separate Lizenz** (Kontakt: steigerwaldph@ki-zentrum.bayern). Neu ist die Bedingung, dass **akademische Arbeiten, die LLARS oder damit erzeugte Daten verwenden, das LLARS-Paper zitieren müssen** — die Zitation ist Bedingung der Lizenzgewährung, keine Bitte. Neue `LICENSE`-Datei im Repository-Root (PolyForm-Text unverändert + `Required Notice:`-Zeilen + Additional Terms), `README.md` und `CITATION.cff` entsprechend aktualisiert. Versionen, die **vor** dieser Umstellung veröffentlicht wurden, hatten keine Lizenzdatei und unterliegen weiterhin den Bedingungen, unter denen sie bezogen wurden.
- **Zitationshinweis in der App** — Beide Footer (App-Footer und Landing-Page-Footer) tragen jetzt einen zurückhaltenden Link **„LLARS zitieren“**, der einen kleinen Dialog öffnet: Bitte um Zitation, der vollständige BibTeX-Eintrag in einer Monospace-Box und ein **Kopieren**-Knopf (mit „Kopiert!“-Rückmeldung). Eine wiederverwendbare Komponente (`LCitationDialog.vue`) für beide Stellen; der BibTeX-Block liegt bewusst als Code-Literal vor und nicht in den Locale-Dateien, damit die LaTeX-Escapes (`\&`) nicht durch Übersetzungen brechen. Alle übrigen Texte zweisprachig (DE/EN). Der Landing-Footer nennt zusätzlich in einem Satz das Lizenzmodell und verlinkt die `LICENSE`.
- **`citation`-Block in JSON-Exporten** — Jeder JSON-Export (v1-API `GET /api/v1/scenarios/<id>/results` **und** GUI-Export `GET /api/scenarios/<id>/export`) enthält im Envelope einen `citation`-Block mit `message`, `paper` (Kurzreferenz inkl. arXiv-ID) und `bibtex_url` (Link auf `CITATION.cff`). Damit hat auch jemand, der nur die Exportdatei in die Hände bekommt, die Zitation zur Hand. **Bewusst nicht in CSV/JSONL:** eine Kommentar- oder Präambel-Zeile würde strikte Parser (`pandas.read_csv`, R `read.csv`, zeilenweise JSONL-Leser) brechen. Das Literal liegt an genau **einer** Stelle (`results_export_service.CITATION_BLOCK` / `citation_block()`) und wird von beiden Routen importiert — dieselbe Regressionsklasse, die in 1.21.0 die `timing_metrics` aus dem v1-Envelope fallen ließ, ist damit auch für die Zitation abgesichert. (Tests EXPORT_CITE_001–006.)
- **Doku-Seite „LLARS zitieren“** (`guides/citing-llars.md`, DE + EN) — warum und wie zitiert wird (BibTeX, Fließtext, `CITATION.cff` + `cffconvert`), wo die Zitation im Produkt auftaucht, sowie ein Lizenzabschnitt mit der Aufteilung Forschung/Non-Profit/akademisch/kommerziell. Enthält den Hinweis, dass die Referenz derzeit auf den arXiv-Preprint zeigt und auf die IJCAI-ECAI-2026-Proceedings-Version umgestellt wird, sobald diese erscheint.

### 🔁 Changed
- **App-Texte: „Open Source“ → „quelloffen / kostenlos für Forschung“** — Überall dort, wo LLARS die **eigene** Lizenz oder Natur beschrieb, ist die Formulierung an das neue Modell angepasst: Landing-Hero-Badge und -Untertitel, Tech- und Research-Sektion (inkl. „MIT-Lizenz — dauerhaft frei“ → „PolyForm Noncommercial 1.0.0 — dauerhaft kostenlos für Forschung und Lehre, kommerzielle Nutzung auf Anfrage“), Landing-Navigation, Doku-Hero-Tag und **§ 5 der Nutzungsbedingungen** (jetzt „Quelloffenheit & Lizenz“, inkl. Zitationspflicht und Hinweis auf die separate kommerzielle Lizenz). Ebenfalls angepasst: statische SEO-Metadaten und das JSON-LD-`SoftwareApplication` in `index.html` — dessen `license` zeigte auf `opensource.org/licenses/MIT` und war damit schlicht falsch. **Nicht angefasst** wurden Erwähnungen von Open-Source-*Fremdsoftware* (Matomo, Authentik in der Datenschutzerklärung), Lizenzen von Drittmodellen (OnCoCo, CC BY-SA 4.0) und der Papierverweis „TextGrad … (MIT, 2024)“, wo „MIT“ die Hochschule meint. Der Landing-Anker `#open-source` bleibt bestehen, damit bestehende Deep-Links nicht brechen.

### 🐛 Fixed
- **`CITATION.cff` deklarierte zwei Lizenzen** — Die Datei enthielt einen doppelten `license:`-Schlüssel; der zweite (`MIT`) überschrieb beim YAML-Parsen den ersten (`PolyForm-Noncommercial-1.0.0`), sodass GitHub und `cffconvert` weiterhin MIT gemeldet hätten. Duplikat entfernt.

### 🗑️ Removed
- **DB Preisagent vollständig entfernt** — Die admin-only Alpha-Kachel „DB Preisagent" und ihr Dashboard (`/db-agent`) sind ersatzlos entfallen. Das Werkzeug hatte nichts mit dem Forschungszweck von LLARS zu tun: Es scrapte die bahn.de-Preissuche für **eine einzige hartkodierte Strecke** (Dortmund Hbf ↔ Nürnberg Hbf, BahnCard 25, 2. Klasse), sammelte Verbindungspreise in einem eigenen Hintergrund-Scheduler und ließ ein LLM Reise-Empfehlungen daraus ableiten. Der Scanner lief seit Monaten ins Leere — die öffentliche bahn.de-Schnittstelle antwortete mit `403 Forbidden`, weshalb der Scheduler-Thread bereits per `DB_AGENT_SCHEDULER_ENABLED=false` stillgelegt war. Entfernt wurden: die Kachel samt Route und `feature:db_agent:view`-Berechtigung, alle `/api/db-agent/*`-Endpunkte (Status, Scan, Scheduler-Steuerung, Statistiken, Deals, Kalender, Preisverlauf, Volatilität, Wochentags-/Timing-Analyse, LLM-Analyse, Reisesuche), der Scanner-/Analyzer-/Scheduler-Service samt Startup-Thread in `main.py`, die drei Tabellen `db_price_scans`, `db_price_entries` und `db_trip_searches`, die vier nur hier verwendeten Icons (`train`, `train-outbound`, `train-return`, `deal`) samt Hover-Animationen sowie 97 i18n-Keys in DE und EN. Bestandsdatenbanken werden per `migrations/20260821_remove_db_agent.sql` bereinigt (Tabellen Kind-vor-Eltern, danach die Permission inkl. Rollen-/User-Zuweisungen).

## [1.21.0] - 2026-08-21


### ✨ Added
- **Spans zusammenführen (Konversationslabeling)** — Gegenstück zum Trennen, mit denselben Regeln: erlaubt nur bei **direkt benachbarten, lückenlosen Spans derselben Nachricht** (Text dazwischen würde sonst stillschweigend in eine bewertete Einheit rutschen). Die neue ID wird abgeleitet, und das Rückgängigmachen eines Splits ist der Normalfall — `x+a` + `x+b` ergibt wieder `x`, eine Studie trägt danach exakt die IDs von vorher. **Beide** Votes werden für alle Bewertenden gelöscht, samt Co-Pilot-Log und Zeitmessung: zwei Entscheidungen über zwei Einheiten sind keine Entscheidung über deren Vereinigung. Die Spans werden per **⌘/Strg-Klick** markiert (gestrichelte Umrandung, Zähler am Knopf); „Span zusammenführen" bleibt ausgegraut, bis die Markierung eine ununterbrochene Folge in einer Nachricht bildet. Zwischen ihnen darf nur **Leerraum** stehen — in einer echten Segmentierung liegen Satz-Spans ein Leerzeichen auseinander, strikte Lückenlosigkeit hätte den Knopf in jedem realen Gespräch tot gelassen. Tragen zwei Nachbarn dasselbe Label, markiert ein Hinweis sie vor — bewusst nur markieren und **nicht** automatisch zusammenführen: die Segmentierung gehört allen Bewertenden gemeinsam, würde sie sich anhand der Labels einer Person ändern, verschöben sich die Einheiten unter allen anderen und deren Votes würden gelöscht. Zwei eigene LLARS-Icons (`span-split`, `span-merge`) im Icon-Register; beide Werkzeuge sitzen zurückhaltend am unteren Panelrand über dem Notizfeld. (`span_progress_service.merge_spans`, `POST /api/evaluation/session/<sid>/items/<iid>/spans/merge`; Tests SPANMERGE_001–008, CONVLAB_028–030.) Siehe [Konversationslabeling](guides/conversation-labeling.md).
- **Neuer Szenariotyp: Konversationslabeling (`function_type_id = 9`)** — Labelt Sinneinheiten („Spans") **innerhalb** eines Gesprächs statt der Nachricht als Ganzes. Ein Item ist ein ganzer Verlauf und enthält viele Entscheidungen (in der VRM-Studie ~92); die **Analyse-Einheit ist damit der Span, nicht das Item**. Das zieht sich durch: Krippendorffs Alpha rechnet über Span-Zellen, die Bearbeitungszeit wird pro Span gemessen, und ein Gespräch gilt erst als fertig, wenn *alle* seine Spans entschieden sind („40 von 92" ist ein normaler Zwischenstand, den klassisches Labeling nicht kennt). Die Segmentierung kommt fertig aus dem Import und ist eingefroren — würde jede Person selbst segmentieren, wären die Zeilen der Rater-Matrix nicht mehr dieselben Einheiten und ein Übereinstimmungsmaß über sie hinweg nicht interpretierbar. Oberfläche: Gespräch links als Sprechblasen, das sich **Turn für Turn** aufblättert (spätere Nachrichten bleiben verborgen — die Bewertenden sollen den Ausgang nicht kennen), Auto-Weiter standardmäßig an (bei ~92 Entscheidungen ist das Zurückklicken sonst der größte Einzelaufwand), Tastatur `1`–`9`/`Enter`/`Backspace`, Auto-Speichern bei jeder Auswahl. Co-Pilot arbeitet span-weise, nie vorausgewählt, mit serverseitig verdeckter Kontrollgruppe und identischer Sichtbarkeit für Mensch und Modell. Export trägt `span_id`/`message_id`/`span_index` (am Ende der Spaltenliste, damit positionsindizierende Auswertungen weiterlaufen). Neue Tabellen-Spalte `span_id` auf `item_labeling_evaluations`, `labeling_copilot_logs` und `evaluation_item_timings` inkl. idempotenter Startup-Migration. (`ConversationLabelingInterface.vue`, `span_progress_service.py`, `labeling_types.py`; Tests CONVLAB_001–027, APIV1_RES_014–019, TIMING_020.)
- **Span teilen (bewusst versteckt)** — Trägt ein Span erkennbar zwei Sprechakte, lässt er sich über einen leisen Link unter dem Zielspan zeichengenau auftrennen. Der Schnitt muss echt innerhalb liegen (an der Kante entstünde eine Einheit der Länge null), neue IDs werden abgeleitet (`x` → `x+a`/`x+b`) statt neu durchnummeriert (ein älterer Export joint dadurch weiterhin), und das Vote auf den alten Span wird **für alle Bewertenden** gelöscht — zusammen mit dessen Co-Pilot-Log und Zeitmessung, weil diese eine Einheit beschreiben, die es nicht mehr gibt. Unauffällig platziert, damit Nachschneiden die Ausnahme bleibt.
- **LLM als Assessor hinzufügen/entfernen — wie einen Menschen** — Der „LLM hinzufügen"-Dialog im Assessors-Tab funktioniert jetzt wirklich (vorher TODO-Stub mit hartkodierter Modell-Liste, der nichts speicherte). Man wählt ein echtes verfügbares Modell (`/api/llm/models/available`, gefiltert auf `model_type='llm'`), und beim Hinzufügen wird es in `config_json.llm_evaluators` persistiert **und der managed Runner startet automatisch** — labelt/annotiert jedes Item mit allen bestehenden Safeguards (Lock pro (Szenario,Modell), Cooldowns, Circuit-Breaker, Permanent-Failure- + Total-Failure-Cap). Entfernen löscht das Modell + seine gespeicherten Ergebnisse (raus aus IRR/Export). Neue Endpunkte `POST/DELETE /api/scenarios/<id>/llm-evaluators[/<model_id>]` (Owner/Admin; Bearer **oder** X-API-Key). (`scenario_crud.py`, `ScenarioTeamTab.vue`; Tests ADDLLM_001–011.)
- **„Demo Video" öffnet die interne LLARS-Video-Seite (YouTube nur noch Backup)** — Der „Demo Video"-Button im Landing-Hero (und der Footer-„Demo"-Link) führen jetzt auf die selbst gehostete Video-Seite `/video` (spielt `/videos/llars_demo.mp4`) statt direkt auf YouTube. Der YouTube-Link ist jetzt **nur** noch als Backup auf der Video-Seite verlinkt (falls die Datei nicht abspielt). `/video` ist dafür öffentlich (`requiresAuth: false`), damit auch nicht eingeloggte Besucher das Demo sehen (`HeroSection.vue`, `LandingFooter.vue`, `DemoVideoPage.vue`, `router.js`).
- **Phase freischalten direkt im Übersicht-Tab** — Bei Labeling-Szenarien mit Phasen (Teile/Kalibrierungsphasen) hat jede Phasen-Zeile im **Übersicht**-Tab jetzt einen **Freischalten/Sperren**-Button (vorher nur read-only mit Verweis auf den Einstellungen-Tab). Owner/Manager schalten die nächste Phase damit dort frei, wo sie den Fortschritt sehen. Nutzt denselben management-gated Endpoint `PUT /api/scenarios/<id>/parts/<part_id>` (`ScenarioOverviewTab.vue`).

### 🗑️ Removed
- **LaTeX-Kollaboration samt KI-Schreibassistent und Zotero-Anbindung vollständig entfernt** — Der LaTeX-Workspace (`/LatexCollab`, `/LatexCollabAI`) mit Echtzeit-Editor, PDF-Kompilierung (pdflatex/biber/SyncTeX), Workspace-Git-Panel und Template-Auswahl ist ersatzlos entfallen; **Markdown Collab bleibt unverändert bestehen** und ist weiterhin der kollaborative Editor in LLARS. Mit entfernt wurden der eng damit verzahnte **AI Writing Assistant (LatexCollabAI)** — Ghost Text, `@`-Kommandos, Selection-Menü (Umformulieren/Erweitern/Kürzen), AI-Sidebar-Chat und die Zitations-/DOI-Suche — sowie die vollständig daran gekoppelte **Zotero-Integration** (OAuth-Anbindung, Bibliotheks-Import, BibTeX-Erzeugung) inklusive ihrer verschlüsselten Zugangsdaten. Entfallen sind damit die `latex_collab:*`-Socket.IO-Events, die `/api/latex-collab/*`-, AI-Writing- und Zotero-Endpunkte, die `latex_*`-Tabellen, die Berechtigungen `feature:latex_collab:view/edit/share/ai` sowie die `ZOTERO_*`-Konfigurationsvariablen. Infrastrukturseitig fällt der `texlive-full`-Layer (~5 GB) aus dem Flask-Image weg. **Nicht betroffen:** der externe `overleaf_url`-Link an Konferenz-Papern (reiner Weblink) und die Markdown-Collab-Berechtigungen `feature:markdown_collab:*`.
- **Sprach-/Videoanrufe samt Live-Transkription (LiveKit) vollständig entfernt** — Das Messaging-Modul bietet nur noch Text-Chat (inkl. E2E-Verschlüsselung, Reaktionen, Link-Previews und KI-Zusammenfassungen). Entfernt wurden: die Telefon-/Kamera-Knöpfe im Chat-Header samt Call- und Transkriptions-Panels, die Socket.IO-Events `messaging:call_initiate/accept/decline/end`, die Endpunkte `POST /api/messaging/calls/transcript-chunk` und `GET /api/messaging/calls/<id>/summary`, `CallService` + `CallTranscriptionService`, das (bereits verwaiste) STT-Provider-Paket, die Tabellen `messaging_calls`/`messaging_call_participants`, der Nachrichtentyp `call_event` sowie die Berechtigungen `feature:communication:voice`, `:video` und `:transcription`. Infrastrukturseitig fallen die Container `livekit-service` + `livekit-agents-service`, der nginx-Upstream `/livekit/` und alle `LIVEKIT_*`/`STT_*`-Variablen weg. **Nicht betroffen:** der Messaging-Master-Schalter `system_settings.communication_enabled`, die Berechtigungen `feature:communication:access/chat/ai` und die öffentliche Demo-Video-Seite `/video`. Bestandsdatenbanken werden per `migrations/20260821_remove_call_feature.sql` bereinigt (vorhandene `call_event`-Nachrichten werden zu `system` umgeschrieben, bevor der ENUM verkleinert wird).

### 🐛 Fixed
- **Konversationslabeling: IRR beschrieb einen zufälligen Span pro Gespräch** — `_collect_human_evaluations` schrieb alle ~92 Span-Zeilen eines Gesprächs in dieselbe Zelle `data[item][rater]`; die zuletzt geschriebene gewann. Das Alpha sah völlig normal aus und bedeutete nichts. Die Analyse-Einheit ist jetzt der Span (`item::span`, dasselbe Muster wie beim Dimensions-Pooling).
- **Konversationslabeling: Modell fiel kommentarlos aus jedem Vergleich** — Die LLM-Vorhersagen liegen span-weise unter `task_type = "copilot_labeling"`, nicht unter `"conversation_labeling"`. Die Abfrage traf nichts. Jetzt wird die Cache-Zeile aufgefächert; der Vote des Modells ist sein primärer Vorschlag — genau der, den ein Mensch zu sehen bekommen hätte.
- **Konversationslabeling: Co-Pilot-Daten wurden über Spans hinweg vervielfältigt** — Der Export-Join war nach `(user, item)` indiziert und kollabierte ~92 Log-Zeilen auf eine, sodass jeder Span eines Gesprächs denselben Vorschlag, dieselbe Annahme und dasselbe `helpful` trug — erfundene Studiendaten, die im CSV plausibel aussahen. Gleiches Muster bei den Zeitmessungen (`timings_for_scenario` liefert jetzt 3-Tupel).
- **Add-LLM-Assessor-UI inkonsistent** — Nach dem Hinzufügen eines LLM-Assessors zeigte die Zeile „0/0" + einen **Start**-Button, obwohl der Runner serverseitig bereits **automatisch** gestartet war (die Live-Stats treffen erst mit Verzögerung ein). Klick auf „Start" war dann ein No-op (Runner-Lock) → „nichts passiert". Fix: gerade hinzugefügte/gestartete Modelle werden **sofort als „Running"** angezeigt (kein irreführender Start-Button), bis die echten Stats greifen. Zusätzlich der tote **„Template: Standard/Detailed"-Dropdown** aus dem Dialog entfernt (Attrappe ohne Backend-Wirkung), und der DELETE-Endpoint setzt `enable_llm_evaluation` beim Entfernen des letzten Modells zurück. Die Add/Remove-Endpunkte prüfen jetzt `check_scenario_management_access` (Owner/Manager/Admin) statt Owner-only — konsistent mit der `canManage`-UI-Gating und dem `/start`-Endpoint, sodass ein Editor keinen Button sieht, der 403 wirft. (`ScenarioTeamTab.vue`, `scenario_crud.py`.)
- **LLM-Labeler bekam die falsche Aufgabe** — Für (Wizard-typische) Labeling-Szenarien schickte der Runner dem Modell die **rohen Kategorie-IDs** (`cat_1782…`) statt der Namen (`include`/`exclude`) und ließ **Aufgabenbeschreibung + Einschlusskriterien komplett weg** (sie wurden aus dem falschen, top-level Config-Pfad gelesen; im Wizard liegen sie unter `eval_config.config.*Markdown`). Ergebnis wäre Rate-Müll oder lauter Fehler gewesen. `_run_text_classification` gibt jetzt die Label-Namen als Bedeutung mit (Modell antwortet weiter mit der ID → fluchtet mit menschlichem `category_id` im IRR), holt Aufgabe + Kriterien über den korrekten Resolver und spiegelt die `unsure`-Option. Die Label-Extraktion wurde zudem **robust über alle Config-Shapes** gemacht (`_extract_labels_from_config`): `categories`- **und** `labels`-Listen, Dict-Elemente mit `name`- **oder** `label`-Key (localized), Strings, `classification_labels`, top-level + nested — vorher fiel z.B. Szenario 629 (Labels als Dicts unter `config.labels`) auf die Default-Labels `positive/negative/neutral` zurück. (`llm_ai_task_runner.py`; Tests LABELTASK_001–009.)
- **Google-Maps-Karte auf der Kontakt-Seite geblockt (CSP)** — Die Consent-gegatete Google-Maps-Einbettung (`Kontakt.vue`, iframe `maps.google.com/…&output=embed`) wurde von der CSP `frame-src 'self' blob:` blockiert (`Framing 'https://maps.google.com/' violates … frame-src`). `https://maps.google.com https://www.google.com` zu `frame-src` in beiden Prod-nginx-Configs ergänzt (`nginx.prod.conf`, `nginx.prod-no-ssl.conf` — Port-80- und 443-Block). Karte lädt nach Zustimmung.
- **Demo-Video (`/videos/llars_demo.mp4`) 404** — Kein Code-Bug: die 85-MB-Datei ist bewusst gitignored/dockerignored und wird per Host-Mount `./static/videos → /srv/llars-static/videos` ausgeliefert (nginx `location /videos/` existierte bereits), lag aber nicht auf dem Prod-Host. Datei nach `/var/llars/static/videos/` gelegt → wird jetzt (mit Range-Streaming) ausgeliefert. **Ops-Hinweis:** bei frischem Host-Setup muss das Video dort manuell abgelegt werden.
- **`timing_metrics` fehlten im v1-JSON-Export** — Die v1-Route baut ihren JSON-Envelope aus ausgewählten Keys; der neue Aggregat-Block (`timing_metrics`) aus `collect_results` wurde nicht durchgereicht (CSV hatte die Pro-Fall-Spalten, das JSON aber nicht die Pro-Bewerter-Kennzahlen). Key ergänzt (`scenario_results_routes.py`; Test APIV1_RES_013). GUI-Export war nicht betroffen.

## [1.20.0] - 2026-07-15


### ✨ Added
- **Bearbeitungszeit pro Fall in jedem Export** — Jeder Evaluations-Export (v1-API `GET /api/v1/scenarios/<id>/results` **und** der GUI-Export `GET /api/scenarios/<id>/export`, für **alle** Typen: Rating, Mail-Rating, Ranking, Comparison, Communication-Comparison, Authenticity, Labeling) enthält jetzt zwei Zeit-Spalten pro Bewertung: **`time_on_item_ms`** (client-gemessene Zeit vom Anzeigen des Items bis zum ersten Speichern) und **`time_since_prev_ms`** (abgeleiteter Fallback: Abstand zwischen den `created_at`-Zeitstempeln aufeinanderfolgender Fälle desselben Bewerters — damit auch **Alt-Studien** ohne echte Erfassung eine Näherung bekommen; erster Fall pro Bewerter und Ranking-Zeilen bleiben leer). Echte Erfassung: neue zentrale Tabelle `evaluation_item_timings` (eine Zeile pro Bewerter/Item/Szenario, first-write-only), gespeist von einem `Date.now()`-Timer in allen Bewertungs-Interfaces; verdrahtet in die 4 Submit-Endpunkte. Labeling nutzt zusätzlich weiterhin `labeling_copilot_logs.time_on_item_ms`. Zusätzlich enthält der JSON-Envelope (v1-API + GUI-Export) einen `timing_metrics`-Block mit **aggregierten Kennzahlen pro Bewerter** (n, Mittelwert, Median, Min, Max, Standardabweichung, Summe + Herkunft echt/abgeleitet) sowie einem Overall-Block — korrekt pro Fall dedupliziert (Rating hat mehrere Zeilen pro Fall). (`EvaluationItemTiming`, `ItemTimingService`, `results_export_service`, `scenario_manager_api`; Tests TIMING_001–019, CMP_TIME_001/002).

### 🐛 Fixed
- **Matomo-Custom-Logo & absolute URLs (fehlender `/analytics/`-Basispfad)** — Der öffentlich aktive Port-80-nginx-Block (Gateway leitet per HTTP dorthin) reichte `X-Forwarded-Uri /analytics` nicht durch, sodass Matomo (`proxy_uri_header=1`) seinen Basispfad nicht kannte und absolute URLs — u.a. das LLARS-Custom-Logo — **ohne** `/analytics/`-Präfix baute → 404/kaputtes Bild. `X-Forwarded-Uri` (+ `-Host`/`-Port`) im Port-80- und no-ssl-Block ergänzt (der 443-Block hatte sie bereits). Ergänzt den Branding- und Mixed-Content-Fix aus 1.19.0.

---

## [1.19.0] - 2026-07-13


### ✨ Added
- **Matomo im LLARS-Branding** — Das Analytics-Dashboard (`/analytics/`) zeigt jetzt das LLARS-Logo (Login + Kopfzeile) statt des Matomo-Standardlogos. Umsetzung: Custom-Logo in `misc/user/` + `branding_use_custom_logo=1` via `docker/matomo/init-matomo.sh` + `configure-branding.php` (best-effort, bricht den Matomo-Init nie ab).
- **MkDocs-Doku im LLARS-Design** — Die Dokumentation (`/mkdocs/`) trägt jetzt die LLARS-Farbpalette (grüner Header `#b0ca97`, Teal-Links/Akzente), das LLARS-Logo im Header + als Favicon und die asymmetrische Border-Radius-Signatur (Code-Blöcke, Admonitions, Tabellen, Suche). Umsetzung über `extra_css` (`docs/docs/stylesheets/llars.css`) statt Theme-Umbau; Light- und Dark-Scheme abgedeckt.
- **Leertaste = „Weiter" in Evaluationen (opt-in)** — Neuer Settings-Tab **Präferenzen** (`/settings`) mit einem Schalter „Leertaste springt zum nächsten Item". Standardmäßig **aus**; jeder User aktiviert ihn selbst. Ist er an, blättert die Leertaste in jeder Evaluation (alle Szenario-Typen) zum nächsten Item — außer der Fokus liegt in einem Textfeld (dort tippt sie normal ein Leerzeichen). Die Präferenz wird **pro User** im Backend gespeichert (`user.settings_json`, geräteübergreifend). Der Tab ist als Sammelfläche für künftige Präferenzen angelegt (`PreferencesTab.vue`, `useUserPreferences.js`, `EvaluationSession.vue`).
- **Changelog per Klick auf die Versionsnummer** — Die Versionsnummer im Footer (bzw. das Versions-Tag in der App-Bar im Dev-Modus) ist jetzt ein Link auf den Changelog (`/mkdocs/changelog/`, sprachabhängig). So kann man direkt nachlesen, was sich zwischen den Releases geändert hat (`App.vue`, i18n `footer.changelog`).

### 🐛 Fixed
- **Matomo-Dashboard war kaputt (CSP `unsafe-eval`)** — Matomos Vue-UI nutzt `new Function()`; die global gehärtete CSP (`script-src` ohne `unsafe-eval`, Pentest M11) blockte das → das Dashboard brach beim Mounten (jQuery/EvalError). Fix: pfadabhängige CSP via nginx-`map` — nur `/analytics/` erhält `unsafe-eval` (Matomo ist zusätzlich Auth-geschützt), die restliche App bleibt strikt. Lokal in Chrome verifiziert: `/` ohne, `/analytics/` mit `unsafe-eval`; Dashboard mountet.
- **Matomo Mixed-Content-Warnungen** — Hinter dem SSL-terminierenden FH-Gateway (HTTP an die App-nginx) generierte Matomo absolute `http://`-URLs → Mixed-Content auf der HTTPS-Seite. Fix: `assume_secure_protocol = 1` in Matomos `config.ini.php` (nur Production, via `init-matomo.sh`).
- **Changelog-Badges im MkDocs luden nicht** — Die shields.io-Badges im Changelog-Header (Version/Released/…) wurden von der Content-Security-Policy geblockt (`img-src` erlaubte `img.shields.io` nicht). `img.shields.io` zur CSP-`img-src` ergänzt (`nginx.prod.conf`, `nginx.prod-no-ssl.conf`).
- **Labeling: Item-Status im Footer (falsch „In Bearbeitung")** — Im Evaluate-View zeigte der Status-Tag unten den **Gesamtfortschritt** statt des Status des **aktuellen** Items. Folge: ein frisches, unbearbeitetes Item stand fälschlich auf „In Bearbeitung" (weil andere Items schon erledigt waren), und beim Zurücknavigieren stand ein bereits **abgeschlossenes** Item ebenfalls auf „In Bearbeitung" statt „Abgeschlossen". Fix: `LabelingInterface` emittiert jetzt den Status des aktuell angezeigten Items (`done` | `pending`) statt des Aggregats (`LabelingInterface.vue`, Tests LABEL_007/008).
- **E2E-Deploy-Gate entblockt (Consent-Banner)** — Nach der Umbenennung der Consent-Buttons (`Alle akzeptieren` / `Nur notwendige`) klickte der E2E-Helper `dismissConsentBanner` den ersten Button im Banner — das ist der **Datenschutz-Link**, der auf `/Datenschutz` navigiert und so den Login-Flow verließ. Folge: 33 Nightly-E2E-Tests liefen 30 s in einen Login-Formular-Timeout, das Prod-Deploy-Gate blieb blockiert (Prod hing auf 1.17.2). Fix: stabile `data-testid`s (`consent-accept` / `consent-decline` / `consent-privacy`) am Banner + Helper klickt gezielt `consent-accept` und bleibt auf der Seite (`e2e/helpers.js`, `e2e/auth.setup.js`, `e2e/login.spec.js`).
- **Dokumentations-Link (Footer) → MkDocs statt 404** — Öffentlicher Traffic läuft über das SSL-terminierende FH-Gateway, das per **HTTP** an den **Port-80-Server** der Prod-nginx weiterleitet. Dieser Block hatte zwar den `location = /mkdocs`-Redirect, aber **keinen `/mkdocs/`-Proxy** (nur der 443-Block hatte ihn) → `/mkdocs/` fiel in den SPA-Catch-All und zeigte die Vue-404 („Dokument nicht gefunden"). Fix: `/mkdocs/`-Proxy-Block auch im Port-80-Server ergänzt (`docker/nginx/nginx.prod.conf`).
- **Fortschritt bei Labeling-Szenarien (0/0 trotz Labels)** — In `get_progress_stats` zählte ein Labeling-Assessor ohne aktive Teile über die (leere) `ScenarioThreadDistribution`-Tabelle und zeigte 0 Fertig / 0 Ausstehend, obwohl die Session **jedem** Assessor **alle** Items ausliefert (keine per-User-Distribution). Fix: Labeling-Assessoren ohne Teile zählen jetzt gegen alle Items — konsistent mit `session_service._get_items_for_scenario` und `get_user_progress_counts` (Bug Szenario 758; `app/services/scenario_stats_service.py`, Test STATS-113).

---

## [1.18.0] - 2026-07-11


### ✨ Added
- **Landing Page als öffentliche Root-Seite** — `https://llars.e-beratungsinstitut.de/` zeigt jetzt nativ die Landing Page statt auf `/login` umzuleiten (`/landing` bleibt als Alias, eingeloggte User landen weiter auf `/Home` bzw. im Single-Scenario-Shortcut). Neue Nav mit Sektions-Ankern (Smooth-Scroll), **Login- und Registrieren-Button**, GitHub-Link (Nav, Hero, Open-Source-Sektion, Footer → `github.com/th-nuernberg/llars`).
- **Interaktive Labeling-Demo mit Co-Pilot** — DOM-gebautes App-Fenster auf der Landing Page: drei durchklickbare Beispiel-Items mit Co-Pilot-Vorschlag (Begründung, Konfidenz, markiertem Textbeleg), „Übernehmen"-Button, Autosave-Häkchen und Fortschrittsbalken; 3D-Tilt + Cursor-Glow, `cursor: pointer` nur auf tatsächlich klickbaren Elementen. Dazu Co-Pilot-Erklärung (nie vorausgewählt, verdecktes Kontrollsubset, Studien-Logging) und neue Feature-Karte im Bento-Grid.
- **Akteon-Stil-Animationen** — Hero-Hintergrund-Blobs fliegen beim Seitenaufruf gestaffelt ein (danach Endlos-Drift), `PaintStrokesReveal`-Komponente (Scroll-getriggerter Blob-Einflug, CTA-Finale + Open-Source-Sektion), `v-glow`-Directive (cursor-folgender Glanz auf Karten), Scroll-Hinweis-Pfeil, Bären-Bobbing — alles mit `prefers-reduced-motion`-Fallbacks.
- **Open-Source-Sektion „Von Forschenden, für Forschende"** — Foto (lokal gehostetes Unsplash-Bild, `assets/landing/ATTRIBUTION.md`), MIT/Self-Hosting/Reproduzierbarkeits-Punkte, GitHub- und Doku-CTA.
- **Neue itshover-Icons** — `GithubIcon` (Brand-Mark) und `CursorClickIcon`; Resolver-Tokens `github` bzw. `cursor/click/tap/gesture/pointer`.

### 🔁 Changed
- **Landing-Texte für Forschende geschärft** — Hero-Subtitle, CTA und neue Open-Source-Botschaft adressieren Forschungsteams (frei nutzbar, selbst hostbar, bleibt MIT); zweites Hero-Badge „100 % Open Source · MIT"; Hero-CTA führt auf `/register`.

### 🐛 Fixed
- **Doppelter Footer + Hero-Überlauf auf `/landing-preview`** — AppBar/Footer-Hiding ist jetzt meta-basiert (`hideAppChrome`) statt an den Routennamen `LandingPage` gebunden; damit verschwinden der doppelt gerenderte kleine App-Footer und der 100vh-Hero-Überlauf um die AppBar-Höhe (zusätzlich `100svh` für mobile Browser-UI).
- **„Sieben Evaluationstypen"-Grid** — Karten brechen jetzt symmetrisch als 4+3 um (vorher schief wirkendes 5+2); lange Titel („Kommunikationsvergleich") werden per Silbentrennung in der Karte gehalten.
- **CI-Deploys durch Rate-Limit blockiert** — Die nächtliche E2E-Suite (`test:e2e:nightly:tiles`) und `smoke:staging` testen die Staging-Instanz von einer einzigen internen IP gegen `localhost:55080` und sprengten dabei das strikte Per-IP-Limit (500/h im Prod-Modus) → `429` + 45-Min-Job-Timeout, wodurch `deploy:production` übersprungen wurde (auch die Nightly deployte nicht). Fix: interner/privater Test-Traffic ist jetzt vom Rate-Limit ausgenommen (`exempt_internal_ips`, spoofing-sicher — echte Nutzer über öffentliche IPs bleiben bei 500/h limitiert); E2E-Job-Timeout `45m → 75m` als Puffer.
- **Fortschritt bei Parts/Phasen-Szenarien** — In Labeling-Szenarien mit aktiven Teilen (Parts/Phasen) zeigte die Evaluator-Fortschritts-Anzeige für Assessoren `0/0`, obwohl gelabelt wurde. Ursache: bei aktiven Teilen werden Items über den Parts-Mechanismus ausgeliefert (offene Teile), nicht über `scenario_item_distribution` — die Fortschritts-Berechnung (`get_progress_stats`/`get_user_progress_counts`) zählte aber weiter über die (leere) Distribution-Tabelle. Beide Funktionen sind jetzt Parts-bewusst (Assessor-Item-Menge = Items der offenen Teile, spiegelt die Auslieferung); Nicht-Parts-Szenarien bleiben unverändert.

### 🔒 Datenschutz
- **Google-Maps-Zwei-Klick-Lösung auf der Kontaktseite** — die Maps-`iframe` (Verbindungsaufbau zu Google inkl. IP-Übertragung/Cookies) wird erst nach expliziter Zustimmung geladen; vorher steht nur ein lokaler Platzhalter mit Hinweis + Datenschutz-Link, es geht kein Request an `maps.google.com` raus. Zustimmung wird pro Browser (`localStorage`) gemerkt. Wichtig, da die Kontaktseite über die neue öffentliche Landing Page erreichbar ist. (Fonts sind bereits vollständig self-hosted; der Matomo-/Analytics-Consent-Banner erscheint auch auf der Landing Page.)
- **Offizielle LLARS-Kontaktadresse** — Kontaktseite zeigt jetzt `llars@e-beratungsinstitut.de` (identisch zu `MAIL_REPLY_TO` im Backend) als klickbaren `mailto`-Link statt der alten `info@`-Adresse.
- **Datenschutzerklärung vollständig überarbeitet** (Stand 07/2026, `/Datenschutz`) — statt 6 dünner Abschnitte jetzt 13: Server-Logfiles, Cookies & lokale Speicherung, Reichweitenmessung (Matomo, cookiefrei/consent-gated), Google Maps, Konto/Authentik, E-Mail-Versand, Empfänger, Speicherdauer, Datenschutz-Maßnahmen sowie vollständige Betroffenenrechte inkl. **Beschwerderecht (BayLfD)** und Rechtsgrundlagen (Art. 6/9 DSGVO, BayDSG).
- **Nutzungsbedingungen-Seite** (`/Nutzungsbedingungen`, DE/EN, 9 Abschnitte) neu — Geltungsbereich, Konto, zulässige Nutzung, Forschungsdaten/Datenspende, Open Source, Verfügbarkeit, Haftung, Beendigung, Schlussbestimmungen. Im Footer verlinkt (Landing + App).
- **Registrierungs-Zustimmung** — verpflichtende Checkbox „Ich akzeptiere die Nutzungsbedingungen und die Datenschutzerklärung" für **jede** Registrierung (Button ohne Häkchen deaktiviert, Hard-Gate in `handleRegister`), getrennt vom Studien-Consent (der bei Studien-Links zusätzlich gilt). Plus Transparenz-Hinweis zur Forschungsnutzung/Datenspende (Rechtsgrundlage: öffentliche Forschungsaufgabe Art. 6 Abs. 1 lit. e DSGVO, keine gekoppelte Einwilligung).
- **Cookie-Banner auf EU-Standard** — „Alle akzeptieren" / „Nur notwendige" statt „Zustimmen/Ablehnen", klarer Text zu notwendigen vs. optionalen (Matomo) Cookies.
- **SEO-Grundausstattung** — `index.html` mit aussagekräftigem Titel, Meta-Description, Keywords, Open-Graph- und Twitter-Card-Tags, `canonical`, `robots: index,follow` sowie JSON-LD-Structured-Data (`SoftwareApplication` + `Organization`, kostenlos/MIT). Neu: `robots.txt` (erlaubt Indexierung, verweist auf Sitemap; sperrt api/auth/reset/join) und `sitemap.xml` (öffentliche Seiten). Manifest um Description/Kategorien ergänzt. Per-Route-Dokumenttitel (`meta.seoTitle` + `router.afterEach`) für Tab-Titel und JS-rendernde Crawler. Ziel-Keywords u.a. „LLM evaluation software", „label software", „Inter-Rater-Reliabilität".
- **`<noscript>`-Inhaltsblock** in `index.html` — echter Textinhalt (Überschrift, Kernbeschreibung, Funktionen, Keywords, Links) für Crawler und Nutzer ohne JavaScript, ohne SSR-/Prerendering-Risiko.

### ⚡ Performance
- **Code-Splitting** (`vite.config` `manualChunks`) — die großen, lazy-geladenen Leaf-Libraries (Vuetify, pdfjs-dist, jsPDF/html2canvas, Leaflet) werden in eigene, langfristig cachebare Chunks getrennt. Haupt-Bundle von ~6,8 MB auf ~5,9 MB reduziert; Framework-Kern bleibt im Haupt-Bundle (separate `vue`/`realtime`-Chunks erzeugten zirkuläre Abhängigkeiten). Verbessert Ladezeit/Core Web Vitals — im gebauten Build (Preview) ohne Konsolenfehler verifiziert.

### 🔁 Changed
- **App-Bar-Logo-Klick** — eingeloggte Nutzer landen auf `/Home`, nicht eingeloggte (z.B. auf `/login`) auf der öffentlichen Landing Page `/`.
- **MkDocs-Sprachkopplung** — Doku-Links in LLARS öffnen jetzt die zur UI-Sprache passende Version (DE → `/mkdocs/`, EN → `/mkdocs/en/`, via `utils/docsUrl.js`; App-Footer, Landing-Footer, Research-Sektion, Doku-Übersicht, `/docs`-Redirects). nginx erzwingt **kein Englisch mehr** — die vollständige deutsche Doku (Standardsprache) ist wieder unter `/mkdocs/` erreichbar, Englisch unter `/mkdocs/en/`, und der MkDocs-eigene Sprachumschalter funktioniert wieder (korrekter `/mkdocs/`-Basispfad via `site_url`). Dev (`mkdocs serve`, No-Strip) und Prod (Static-Build, Strip) sind in den nginx-Configs entsprechend unterschieden. **Hinweis:** Auf Prod bleibt die öffentliche Doku durch das FH-Gateway-Caching (stale SPA) separat blockiert, bis der Gateway-Cache geleert ist.

---

## [1.17.0] - 2026-07-11


### ✨ Added
- **Szenario-Teile („Parts"/Phasen) für Labeling** — Labeling-Szenarien lassen sich optional in geordnete Teile gliedern (Wizard-Sektion „Teile / Phasen" + v1-API), das Studien-Gate für Kalibrierungs-Designs (z.B. P1 Kalibrierung → IRR/Alignment-Meeting → P2 freischalten → Hauptphase mit Co-Pilot): pro Teil **Reihenfolge** (`sequential` = für alle Rater identisch / `random` = deterministischer Per-User-Shuffle), **Co-Pilot an/aus** (Runner generiert nur für Co-Pilot-Teile, verdecktes Kontrollsubset wirkt unverändert darin), **Sperren/Freischalten** (Owner-UI im Einstellungen-Tab + `PUT /api/v1/scenarios/<id>/parts/<part_id>`). Für Bewerter:innen ist die Teilung **unsichtbar** (parts-/copilot-Sektionen werden serverseitig aus Session-, Listen- und Stats-Antworten gestrippt; Item-Summen auf offene Teile skaliert). Auswertung: Spalte `part` im Results-Export, `?part=`-Filter an den Agreement-Metriken (IRR pro Phase, kombinierbar mit `?copilot=`), `copilot_metrics.per_part`. Item-Nachladen erfordert bei aktiven Teilen `part_id` (Partition-Invariante: jedes Item genau ein Teil). Ohne `parts` in der Config ändert sich nichts (Opt-in).

### 🔒 Security
- **Copilot-Interna nicht mehr im Assessor-Payload** — `hidden_control_salt`/`ratio` standen bisher in der Session-/Listen-Config; damit war das verdeckte Kontrollsubset klientseitig berechenbar. Die `copilot`-Sektion wird jetzt für Nicht-Manager serverseitig entfernt (das Evaluator-UI liest sie nicht).

---

## [1.16.0] - 2026-07-05


### ✨ Added
- **Labeling-Co-Pilot (LLM-Pre-Annotation)** — pro Labeling-Szenario zuschaltbar (Szenario-Wizard + v1-API), nach dem Vorbild des DMRS-Co-Pilots aus PsyDefConv: frei editierbares Prompt-Template (`{item}`/`{context}`/`{labels}`/`{codebook}`) mit **szenario-eigener Prompt-Versionierung**, Batch-Vorgenerierung über die LLM-Runner-Queue (Caching pro Item × Prompt-Version × Modell), **Top-1/Top-2-Vorschläge** mit Begründung, Evidenz-Zitat und Konfidenz im Labeling-Interface (klar markiert, nie vorausgewählt), Hilfreich-Daumen, Zeit-pro-Item-Messung, **verdecktes Kontrollsubset** für Anchoring-Analysen, `copilot_*`-Spalten + Akzeptanz-/Helpful-/Zeit-Metriken im Results-Export sowie **„Mit/Ohne Co-Pilot"-Filter** für die Agreement-Metriken.
- **Voter-Herkunft im Results-Export** — `voter_origin`/`voter_source` (Referral-Link vs. Bestandskonto) auf allen Human-Zeilen.

### 🐛 Fixed
- **Schema-Patches boot-race-sicher** — parallel bootende Container (flask/worker/supervisor) konnten sich beim ersten Start nach einem Update gegenseitig mit „Duplicate column" crashen (TOCTOU zwischen Existenz-Check und ALTER).
- **Labeling-Evaluationen vollständig angebunden** — Auto-Save im eingebetteten Interface, Fortschrittszählung aus `ItemLabelingEvaluation`, Anzeige im Daten-Tab.
- **Labeling-Task-Typ-Erkennung im Auswertungstab** für v1-erstellte Szenarien (`function_type_name`-Fallback).

---

## [1.15.0 – 1.15.2] - 2026-06


### ✨ Added
- **Vollständiger, veröffentlichter Changelog** — diese Datei ist jetzt komplett (alle Releases 1.0.0–1.14.0, neueste oben, Badges + Emoji-Sektionen) und als MkDocs-Seite unter `/mkdocs/changelog/` (DE/EN) verlinkt.
- **Siebter Evaluationstyp auf der Landing Page** — `communication_comparison` ergänzt (Typen-Sektion + Tech-Counter „Sieben Evaluationstypen").

### 🔁 Changed
- **Landing Page** verlinkt das neue IJCAI-Demo-Video; das Chatbot-Builder-Tile hat ein passendes Icon.
- **Chatbot-Grounding prompt-getrieben** — nur wirklich relevante Quellen zitieren, allgemeine Fragen aus Eigenwissen beantworten, bei LLARS-Lücken ehrlich „keine belastbare Info" (Kalibrierung zeigte: die Bi-Encoder-Relevanz trennt On-/Off-Topic nicht zuverlässig).

### 📚 Docs
- EN-Übersetzungen für `nightly-test-activities`, `mail-service`, `human_studies/index` und `playbook`; Detailabschnitt für Communication Comparison (Typ 8); MariaDB-Version auf 11.2.6 korrigiert.

---

## [1.14.0] - 2026-06-13


### ✨ Added
- **Nutzer-Herkunft im Scenario Manager** — farbige „Origin"-Pillen zeigen pro Evaluator, woher er kam (Referral-Link vs. Bestandsnutzer) und wie er ins Szenario kam (Owner / Auto-Enroll / eingeladen von … / selbst). Sichtbar in **Assessors, Settings, Overview und Evaluation**. Jeder Referral-Link bekommt eine **LLARS-weit konsistente Farbe** (deterministisch auto-vergeben, im Admin-Panel überschreibbar) plus eine einklappbare Legende.
- **Allgemeine LLARS-Demo** — de/en-Einladung + Willkommensmail + Demo-Accounts mit 1-Wochen-Ablauf; nächtlicher `maintenance:demo-cleanup`-Job räumt abgelaufene Demos auf.
- **IJCAI-Willkommensmail** im Admin Mail-Center sichtbar gemacht.

### 🔁 Changed
- **Chatbot beantwortet generische Fragen ohne Quellen** — Antwort vom Zwang zur Zitation entkoppelt: Allgemeinwissen-Fragen werden frei beantwortet, relevante LLARS-Quellen weiterhin zitiert.

### 🔒 Security
- **Pentest-Härtung (umfassend)** — `docker.sock`-Mount durch read-only Socket-Proxy ersetzt (C3); Container-Memory-Limits gegen DoS (M3); nginx-Härtung (CSP `unsafe-eval` raus, Real-IP, PHP versteckt); mkdocs/authentik auf Loopback, gehashte Reset-Tokens, npm-audit; Dual-Key-Secret-Decryption + DB-Port loopback-only; `test_prompt_stream` gegated + Rate-Limiting auf Socket-LLM-Pfaden; IDOR/SSRF geschlossen, CSV/XSS/Crypto/Session-Lücken gehärtet.

### 🐛 Fixed
- **DOMPurify wieder funktionsfähig** — der npm-audit-fix-Lockfile-Bump wurde zurückgerollt (hatte DOMPurify gebrochen).

---

## [1.13.0] - 2026-06-08


### ✨ Added
- **Vergleichs-Analyse: Einzelstimmen-Matrix + Autoren-Analyse** — der Szenario-Auswertungstab zeigt für paarweise Szenarien (comparison / communication_comparison) jetzt, wer (welcher Evaluator) was (A/B/Unentschieden) pro Vergleich gewählt hat, inkl. Autor-Chip (Mensch vs. konkretes LLM), Voter-Ausschluss (Testaccounts ausblenden) und Krippendorff-α. Die Autoren-Analyse rankt die Systeme per Win-Rate (Wilson-95%-CI) + Bradley-Terry-Stärke und zeigt Head-to-Head-Quoten.
- **Mail-Center: Quick-Send** — Admins können eine gewählte Mail-Vorlage direkt an eine eingegebene Adresse schicken (Templates-Tab), gegated über `feature:admin:mail`.

### 🔁 Changed
- **Kompakteres, modernes Layout für „Individual votes" + „Author analysis"** — konsistente Icon-Header mit Kennzahl-Chips, sauber gepolsterte Card-Bodies, kleinere Tags/Chips/Balken, gedämpfte Win-Rate-Balken mit Akzent-Gradient für den Rang-1-Eintrag und dezente Akzent-Leiste für die Mensch-Referenzzeile.

### 🐛 Fixed
- **Autor-Klassifikation der Vergleichs-Optionen korrigiert** — der Human/LLM-Hinweis im Ergebnis-Export (Basis der Autoren-Analyse) richtet sich jetzt nach dem kanonischen `_categorize`: „human:"-Präfix und „…/human"-Tails (z. B. „human:counsellor") werden korrekt als Mensch erkannt; die wirkungslosen Glob-Einträge „klient*in"/„berater*in" durch die realen Formen ersetzt.
- **Deterministische Feature-Reihenfolge** — die A/B-Optionen der Rater-Ansicht sind jetzt explizit nach `feature_id` sortiert (wie der Export), damit die Autoren-Zuordnung der Stimmen garantiert mit dem übereinstimmt, was die Rater gesehen haben.
- **Performance der Stimmen-Matrix** — O(1)-Lookup statt per-Zelle-`items.find` (vorher O(Items²×Voter)).

---

## [1.12.0] - 2026-06-08


### ✨ Added
- **Admin Mail-Center, großer Ausbau** — Template-Galerie mit Vorschau (iframe + Fullscreen), Klick-/Öffnen-Tracking, gebündelte branded Einladungen (faf/kiz/org), Workflow „Referral-Link wählen → passende Einladung bearbeiten → senden", Long-Invitation mit Side-by-Side-Live-Preview, anklickbarer Log-Link → Mail-Popup.
- **Referral-System ausgebaut** — konfigurierbarer `signup_mode` (full | email | instant), per-Link Default-Sprache + passwordless Magic-Auto-Login, IJCAI-Demo (Multi-Scenario-Enroll + Viewer-Rolle), Join für bestehende Accounts via Link + Willkommensmail, Code-Redeem nach Login mit Enrollment-Bestätigungs-Popup.
- **Demographics in den Settings** — Nutzer können ihre Demographics ansehen/bearbeiten und die gespeicherte E-Mail einsehen; Consent zur E-Mail-Speicherung als opt-in/revoke.

### 🔁 Changed
- **Responsive-/Mobile-Pass (audit-getrieben)** über alle Evaluation-Interfaces **und** den kompletten Scenario Manager — Mobile-Comparison (A/B-Fullscreen-Lesemodus, dünne tappbare Footer, Task-Popup, Verlauf-Fullscreen), mobiler Chat-Overhaul im Claude/ChatGPT-Stil, schlanke Daten-Tab-Tabellen ohne Horizontal-Swipe.
- **Chat-Quellen nur bei Zitat** — Source-Panel öffnet nur on-click; Auth-Token läuft jetzt über den Chat-Socket (fixt Streaming statt REST-Fallback); „New chat" funktioniert auf der leeren `/chat`-Seite.
- **Chatbot-Grounding geschärft** — `standard_admin` nutzt nur die `llars-documentation`-Collection; RAG-Zitier-Prompt gehärtet (nur bei echter Relevanz zitieren, keine Links erfinden).
- **App-Bar** ohne „Platform"-Zusatz, eigenes Bewertungen-Icon, Comparison-Votes im Detaildialog.

### 🐛 Fixed
- Export inkl. `communication_comparison` + IRR-Metriken; volle de/en-i18n-Parität für den evaluationAssistant; zahlreiche Eval-, Consent- und Mobile-Layout-Fixes (Task-Popup pro Szenario, Footer/Bars-Polish, Panel-Overlaps).

### 🔒 Security
- Audit-Findings geschlossen (authz/IDOR + Härtung des Referral-Signups); Brevo-Webhook als token-guarded `@public_endpoint` markiert.

---

## [1.11.0] - 2026-06-03


### ✨ Added
- **privacy-filter als 4. Anonymize-Engine** — `openai/privacy-filter` (HF token-classification) neben offline/llm/hybrid wählbar. Mappt die 8 nativen PII-Labels auf die LLARS-Taxonomie, führt fragmentierte BIOES-Spans zusammen und trimmt Whitespace-Offsets; neues `SECRET`-Label (immer maskiert). Benchmark vs. Flair auf dem KIZ-Cluster (`scripts/anonymize/`): für deutschen Beratungstext bleibt Flair der bessere Default (LOC/AGE-Support, höhere Personen-Recall), privacy-filter ist englisch-zentriert → opt-in.
- **NER-Offload in den Worker-Container** (Phase 1) — die heavy Flair/privacy-filter-Inferenz läuft jetzt einmalig & warm im `llars_worker`-Container statt pro gevent-Web-Worker. Web-Tier ruft per Redis Request/Reply ab (gevent-freundlich), mit lokalem Fallback wenn kein Worker erreichbar ist. Beseitigt den ~35 s Cold-Load pro Web-Worker und die RAM-Vervielfachung des 2,2-GB-Modells. (`services/anonymize/ner_remote.py`)

### 🔁 Changed
- **Transaktionsmails Deutsch-only** — Willkommens- und Passwort-Reset-Mail haben ihren englischen Zweitteil verloren (die Studie ist deutschsprachig). Die Willkommensmail schließt jetzt mit der Studienleitungs-Signatur („Mit kollegialen Grüßen / Philipp Steigerwald / KI-Zentrum Bayern"), die Reset-Mail mit „— Das Team des KI-Zentrums Bayern".

---

## [1.10.0] - 2026-06-02


### ✨ Added
- **Self-Service Passwort-Reset** — kompletter Flow mit optionaler E-Mail, Consent-Redesign, branded Reset-Mail und neuen App-Icons.
- **Mistral-Medium-3.5-128B** registriert, inkl. env-gegateter Default-Promotion.

### 🔒 Security
- **Passwort-Reset-, SSRF-, RCE-, IDOR- & Rate-Limit-Lücken geschlossen.**

### 🐛 Fixed
- `create_user` setzt das Passwort jetzt per bekanntem Primary Key (stellt die korrekte Test-Sequenz wieder her).

---

## [1.9.2] - 2026-05-18


### 🐛 Fixed
- **Referral-Landing-Scenario übersteht jetzt Logout/Login** — der Single-Scenario-Auto-Redirect hängte vorher rein an einer count===1-Heuristik. Sobald ein Admin den Rater zu einem zweiten Szenario hinzufügte (z. B. zum Testen), brach der Shortcut für den User dauerhaft. Jetzt liefert das Backend (`authentik_routes._enrich_token_with_roles`) im Login-Response ein neues `referral_target_scenario_id`-Feld, sobald der User ursprünglich über einen Referral-Link mit gebundenem Szenario kam. Der Router bevorzugt diesen Hint über die count-Logik. Auf Logout wird er gecleart, damit shared Workstations nichts an den nächsten User leaken.

---

## [1.9.1] - 2026-05-18


### ✨ Added
- **Vertikaler Resize-Handle im Stacked-Layout** — bisher nur Side-by-Side hatte einen Drag-Divider. Stacked bekommt jetzt das gleiche: 6 px Horizontal-Bar zwischen „Verlauf" und Options, drag verschiebt das Höhen-Verhältnis (20 %/75 % min/max), Position persistiert separat von der Horizontal-Variante. `usePanelResize` unterstützt jetzt `axis: 'vertical'`.

### 🔁 Changed
- **Aufgabe-Briefing klappt automatisch beim ersten „Weiter"** — beim Übergang Item 0 → Item 1 schließt sich das Briefing einmalig. Sobald der Rater es manuell getoggled hat (öffnen oder schließen), gilt seine Wahl als Source-of-Truth und Auto-Collapse feuert nie wieder.
- **Anmerkungen-Section noch schmaler** — Chevron 16→12 px, Font 0.78→0.72 rem, Top-Padding raus, Textarea 2→1 Zeilen. Kollabiert nimmt die Sektion jetzt nur noch ~16 px vertikal weg.

---

## [1.9.0] - 2026-05-18


### ✨ Added
- **Reward-Button auf der Item-Übersicht** — neuer Trophy-Button rechts in der Filter-Reihe (`/scenarios/<id>/evaluate`) öffnet das aggregierte Präferenz-Popup (Mensch vs trainierte KI vs Standard-KI) auf Knopfdruck statt nur nach Milestone. Pulsiert wenn gerade eine Etappe getroffen wurde.

### 🔁 Changed
- **`communication_comparison`-Type-Routing vollständig** — Backend (`session_service`, `scenario_stats_service`, `results_export_service`, `comparison/preferences`-Endpoint) und Frontend (EvaluationItemsOverview-Gamification-Gate, EvaluationHub-Type-Label, ScenarioWizard-Variant-Map, ScenarioDetailsDialog-Modell-Panel) akzeptieren jetzt überall `function_type_id` in `(4, 8)`. Vorher liefen Comm-Comparison-Items als „pending" durch, Gamification war auf der Übersicht aus, Reward-Popup zeigte „not enough data".
- **Locale-getriebene Type-Labels** — EvaluationHub rendert den Type-Chip jetzt via `$t('evaluation.types.<key>')` statt hardcodiertem String. DE+EN-Locales gewinnen `communication_comparison` + den fehlenden `mail_rating`-Eintrag.
- **Progress-Nenner respektiert Unlock-Fenster** — bei `progressive_reveal=true` zählt die Übersicht jetzt gegen `unlockedCount` statt `items.length` (z.B. `0/3` statt `0/5` bei `first_milestone=3`).

### 🐛 Fixed
- **Demo-Seeder Konversationen** enden jetzt mit einer `Klient*in`-Eröffnung; der vorherige Berater-Turn als 2. Nachricht im Verlauf machte die A/B-Kandidaten zu Antworten auf Berater statt auf Klient.
- **Demo-Seeder Timezone-Bug** — `datetime.now()` (lokale Zeit) → `datetime.utcnow()`. Vorher landeten frisch geseedete Szenarien in `status='draft'` und wurden vom EvaluationHub-Filter ausgeblendet.

### 📚 Docs
- `docs/docs/entwickler/evaluation-datenformate.{md,en.md}` aktualisiert: „6 → 7 Typen" + Communication-Comparison-Zeile in der Übersichts-Tabelle.

---

## [1.8.4] - 2026-05-18


### 🐛 Fixed
- **Evaluator-Shortcut strikt nur bei `count === 1`** — der bisherige Code redirectet auch bei `count === 0` (oder >1) per Fallback nach `/evaluation`. Damit landete `test_evaluator` (frische CI-Fixture, 0 Szenarien) ebenfalls auf `/evaluation` statt auf `/Home`, wodurch die Tile-Regression-Specs ihre `.feature-card`-Tiles nicht fanden und ins Timeout liefen. Jetzt strikt: 1 Szenario → Auto-Redirect, sonst Default-Landing. Entspricht auch dem ursprünglichen User-Wunsch „wenn nur einer Szenario zugeordnet".

---

## [1.8.3] - 2026-05-18


### 🐛 Fixed
- **Evaluator-Shortcut härtet sich gegen Race-Conditions** — `roles.length > 0`-Guard wieder rein (v1.8.1 hatte ihn entfernt), damit CI-Fixtures + Fresh-Referral-Registrierungen mit noch nicht hydratisiertem Auth-Bundle nicht in den Shortcut-Pfad laufen. Zusätzlich 3-Sekunden-Timeout auf den `/api/scenarios`-Lookup im Router-Guard — falls Staging-Gunicorn einen Worker mid-Request recycelt oder ein 502 zurückkommt, fällt der Guard transparent auf `/evaluation` zurück statt unendlich zu blockieren.

---

## [1.8.2] - 2026-05-17


### 🐛 Fixed
- **E2E `authenticate as evaluator` Hänger nach v1.8.1** — die Setup-Fixture wartete stur auf `/Home`, aber der breitere Role-Check in v1.8.1 leitet Evaluator-only-User direkt nach `/evaluation` oder `/scenarios/<id>/evaluate` um. `auth.setup.js` akzeptiert jetzt alle drei Landing-Pfade. Power-Role-Fixtures (admin/researcher/chatbot_manager) bleiben weiterhin auf `/Home`.

---

## [1.8.1] - 2026-05-17


### 🐛 Fixed
- **Evaluator-Auto-Redirect ohne strikte Role-Equality** — bisher feuerte der Quick-Access nur bei `roles.every(r === 'evaluator')`. Jetzt: jeder authentifizierte User ohne Power-Role (`admin` / `researcher` / `chatbot_manager`) mit genau einem zugewiesenen Szenario landet direkt in dessen Kachelansicht. Fängt auch Fresh-Registrierungen über den Referral-Link ab, bei denen `llars_roles` zunächst leer ist und der JWT-`groups`-Fallback greift.

---

## [1.8.0] - 2026-05-17


### ✨ Added
- **Communication-Comparison Evaluation-Typ** (`function_type_id=8`) — Spezialisierung von `comparison` für Beratungs-Kontext-A/B-Vergleiche. Gleiche Datenstruktur wie comparison; UI rahmt die Auswahl als „Antwort senden" mit Fly-Out-Animation, optionalem Response-Prompt + Rater-Notiz-Textarea. Komplett verkabelt: Pydantic-Schemas, Frontend-Schemas, Feature-Type-Seeder, Demo-Szenario, Preset-Registry, EvalConfigEnvelope-Diskriminator.
- **Evaluator Quick-Access**: User mit Rolle `evaluator` und exakt einem zugewiesenen Szenario werden automatisch von `/Home`/`/evaluation` direkt in die Kachelansicht des Szenarios geleitet (Welcome + Tool-Liste übersprungen). Cached pro Session, fällt bei 0 oder >1 Szenarien transparent auf `/evaluation` zurück.

### 🔁 Changed
- **Comparison-UI-Wording** angepasst an Sozialwissenschafts-Feedback (Burghardt, 2026-05-15): „Option A wählen" / „Option B wählen" jetzt in beiden Modi (klassisch + Communication-Comparison) statt der modal unterschiedlichen „Send response A/B"-Variante.

---

## [1.7.0] - 2026-05-08


### ✨ Added
- **Public v1 Chatbot API + Wizard-Quickbuild** — programmatischer Chatbot-Zugriff mit scope-gated Keys.
- **Comparison: Progressive Reveal** — Karten werden in Chunks pro Milestone freigeschaltet.
- **Studien-Gamification sichtbar** + Auto-Login + Drawer-Privacy + Bestätigungs-E-Mail.

### 🔒 Security
- **v1 Chatbot API gehärtet** — SSRF + cross-tenant RAG-Attach blockiert; mehrere Produktions-Blocker und Defekte aus drei Agent-Review-Pässen behoben (u. a. MVCC-Snapshot- und DNS-Timeout-Race).

### 🐛 Fixed
- `axios` auf `^1.16.0` angehoben (Release-Gate-Vulnerability).

---

## [1.6.0] - 2026-05-07


### ✨ Added
- **Public v1 Scenario API** — scope-gated API-Keys + Security-Härtung.
- **Öffentliche Landing Page** mit Scroll-Reveal, Bento-Grid und Paint-Strokes + admin-only Landing-Vorschau-Tile.
- **Turing-Test/Comparison** — Reward-System, deterministischer Import, Tie-opt-in, Layout-Politur; paarweises Comparison-Demo für IJCAI-Reviewer.
- **Referral: Auto-Enroll on Join** + dedizierter EMNLP-Study-Link.

### 🐛 Fixed
- **Krippendorff-Alpha korrigiert** (Coincidence-Matrix + ordinale Metrik) sowie IRR-Berechnung + komplette Results-Pipeline; Rater-Filter in Agreement-Metriken berücksichtigt; Crawler persistiert Crawl-Sessions über Worker hinweg; `pygments==2.19.1` gepinnt (behebt mkdocs-Crash).

---

## [1.5.0] - 2026-04-02


### 🔒 Security
- **API Keys mit argon2id gehasht** - Plaintext-Keys werden beim Startup automatisch migriert. Neue Keys werden nur noch als Hash gespeichert. Backward-kompatibel waehrend Migration.
- **Docker Base Images gepinnt** - Alle Dockerfiles nutzen jetzt spezifische Versionen (python:3.10.20-slim, nginx:1.28.3-alpine, node:23.11.1-slim/alpine, mariadb:11.2.6) statt floating Tags. Supply-Chain-Schutz.
- **Security-Scan blockiert Pipeline** - `allow_failure: true` entfernt von `security:scan`. Vulnerabilities muessen gefixt oder explizit ignoriert werden.
- **CVE-2026-22815 (aiohttp)** gefixt - Upgrade 3.13.3 auf 3.13.4
- **lodash-es Prototype Pollution** gefixt (GHSA-f23m, GHSA-r5fr)
- **picomatch ReDoS + Method Injection** gefixt (GHSA-3v7f, GHSA-c2c7)
- **Rollback Error-Handling** - Kein stilles `|| true` mehr; explizite Fehlermeldung wenn beide Rollback-Mechanismen scheitern

### ⚡ Performance
- **Agreement-Berechnung 241x schneller** - Krippendorffs Alpha, Fleiss Kappa, Heatmaps nutzen jetzt NumPy-Vektorisierung statt Python-Loops. ProcessPoolExecutor verteilt unabhaengige Berechnungen auf alle CPU-Kerne.
- **Gunicorn Workers auto-skaliert** - `cpu_count + 1` (13 auf Production) statt hardcoded 4. Gevent-optimiert.
- **Stats/LLM Workers auto-skaliert** - `cpu_count // 2` (6 je auf Production) statt hardcoded 2.
- **CI Backend-Tests 3.7x schneller** - pytest-xdist verteilt 3110 Tests auf 12 Kerne (18min auf 5min).
- **Flask RAM -50%** - Von 11.17GB auf 5.5GB durch korrekte Worker-Anzahl fuer gevent.

### 🐛 Fixed
- **Flaky TestPromptDialog in CI** - Timeout auf 15s erhoeht, proper Vue unmount im afterEach verhindert Socket-Listener-Leaks.
- **Dead Code entfernt** - Alte `_stats_cache` Funktionen (ersetzt durch 2-Tier Cache Service).
- **Healthcheck start_period** von 30min auf 2min reduziert.

---

## [1.4.0] - 2026-03-18


### 🔁 Changed
- **2-Achsen-Szenario-Rollenmodell** — Refactoring auf `manager_role` + `evaluation_role` (löst die einfache `role`-Spalte ab).

### ✨ Added
- Verbessertes Timeline-Layout + Sortierung der Conference-Liste.

### 🐛 Fixed
- Viewer-Szenarien erscheinen in „Meine Szenarien"; `from_job`-Chains werden aufgelöst statt abgelehnt; Session-Flush in den Distribution-Helpers (verhindert SQLite-State-Korruption); Non-UTF-8-Bytes im `latexmk`-Output abgefangen; mehrere flaky CI-Tests stabilisiert.

---

## [1.3.0] - 2026-03-16


### ✨ Added
- **Single Source of Truth für LLM-Modell-Farben** (Backend + Frontend).
- **Rollen-bewusste Item-Distribution**, Agreement-Metriken-Filtering und Diff-Cache.

### 🔁 Changed
- `black`/`isort` aus dem Lint entfernt (nie enforced, 499 Dateien non-compliant).

### 🐛 Fixed
- LLM-Evaluationen werden in Provenance + Agreement-Metriken einbezogen; Stats-Cache-Invalidation in `try/except` gewrappt.

### ⚡ Performance
- CI-Pipeline beschleunigt (parallele Tests, E2E-Workers, zentralisierte Builds).

---

## [1.2.0] - 2026-03-15


### 🐛 Fixed
- **KRITISCH: Frontend Healthcheck nutzte `wget` (nicht installiert in nginx:alpine)** - verursachte 9h17min Production-Downtime nach Server-Reboot. `unattended-upgrades` Kernel-Update loeste Reboot aus → Frontend-Healthcheck schlug fehl → nginx blockiert. Fix: Healthcheck auf `curl` umgestellt.

### ✨ Added
- **Systemd Reboot-Resilienz** - Automatische Wiederherstellung nach Server-Reboots via `llars.service` mit 5-Retry-Logik und Exponential-Backoff. Blue-Green-aware: Zwei-Schritt-Start (Infrastructure via compose, App-Container via docker start). Healthcheck-Timer (3min) und Cleanup-Timer (taeglich 03:30).
- **2-Achsen Berechtigungsmodell fuer Szenarien** - Ersetzt einfache `role`-Spalte durch `access_level` (OWNER/MANAGER/MEMBER) + Capability-Flags (`is_viewer`, `is_assessor`). Ermoeglicht feingranulare Kontrolle.
- **Neuer Settings-Tab im Scenario Manager** - Ersetzt Settings-Popup-Dialog. Enthaelt alle Szenario-Einstellungen + Team-Uebersicht mit Tag-basierter Rollenverwaltung.

---

## [1.1.0] - 2026-03-13


Changes since v1.0.0 (2026-03-09).

### 2026-03-13

#### 🐛 Fixed
- **MariaDB 11.2.2 auf 11.2.6 aktualisiert** - behebt SEGFAULT-Absturz in der Datenbank
- **pypdf 6.7.5 auf 6.8.0 aktualisiert** - behebt CVE-2026-31826 (Sicherheitsluecke)
- **Bucket-Spalte auf VARCHAR(255) erweitert** fuer benutzerdefinierte Labels in Ranking-Szenarien
- Owner erhaelt automatisch VIEWER-Berechtigung; Team-Sichtbarkeit im Scenario Manager korrigiert
- Nginx DNS Auto-Heal nach Container-Neustarts
- Syntax-Fehler im GenerationJobDetail Socket-Handler behoben
- Zahlreiche E2E-Test-Fixes: User-Suche, Share-Dialog, Rate-Limit-Vermeidung, Workflow-Robustheit

### 2026-03-12

#### ✨ Added
- **Generation Job Sharing** - Jobs koennen mit anderen Nutzern geteilt werden (read-only)
- E2E-Tests fuer Dev-Branch automatisch mit gleicher Suite wie Main

#### 🐛 Fixed
- Konsistente Avatare in allen User-Listen (Backend + Frontend)
- Fehlende `ItemComparisonEvaluation`-Model-Klasse ergaenzt
- E2E-Workflow-Tests mit SYSTEM_ADMIN_API_KEY stabilisiert

#### 🔁 Changed
- `build_avatar_url()` wird jetzt ueberall statt manueller URL-Konstruktion verwendet

### 2026-03-11

#### 🐛 Fixed
- E2E Tile-Regression: `requiresAdmin` fuer Pipeline-Routes, Redirect-Erkennung
- E2E-Fixes fuer Staging 429 Rate-Limits
- Bootstrap-Variablen fuer e2e:dev Job ergaenzt

#### ⚡ Performance
- CI-Pipeline: venv/node_modules Caching mit File-Hash-Keys eingefuehrt

### 2026-03-10

#### ✨ Added
- **Tag-basiertes Versionierungssystem** mit `/api/version` Endpoint
- **117 neue LLM-Tests** + Smoke-Tests + E2E LLM-Stream-Test
- LLM Prompt Response Smoke-Test und Handler-Integrationstests

#### 🐛 Fixed
- **Flask==3.0.3 und Werkzeug==3.0.6 gepinnt** - behebt Socket.IO Session-Fehler (kritisch)
- **LLM Evaluator Anti-DDoS**: Lock + Permanent-Failure-Detection verhindern Server-Ueberlastung
- Docker Hub TLS-Timeouts: `syntax=docker/dockerfile:1` Direktiven entfernt
- Flask-SocketIO auf 5.4.1 aktualisiert, Encryption-Key-Fallback korrigiert
- NameError-Crashes im LLM Ranking Runner behoben
- Socket.IO xhr-post-Fehler in Prompt Engineering und Chat beseitigt
- LLM Auto-Start und Socket.IO-Konnektivitaet wiederhergestellt
- Smart CACHE_BUST statt --no-cache fuer Docker Builds (verhindert Disk-Full)

#### 📚 Documentation
- LLM Evaluator Anti-DDoS Architektur dokumentiert; Code-Dokumentationsrichtlinie eingefuehrt

### 2026-03-09

#### ✨ Added
- **Markdown Scenario Briefings** end-to-end (Judge-Szenarien mit Markdown-Beschreibungen)
- **Admin Research Groups** mit neuem Master-Detail-Layout redesigned
- **Semantische Versionsverwaltung** mit Branch-aware Auto-Increment
- Branch und Commit-Hash werden neben der Version in der AppBar angezeigt

#### 🐛 Fixed
- Segfault im Route-Test-Teardown behoben
- E2E Tile-Regression-Failures korrigiert
- Git-Version als Build-Arg an Docker-Frontend-Builds uebergeben
- SQLite Connection Pool wird vor Table-Drop korrekt disposed
- Langchain Dependency-Konflikt und Seeder-Constraint-Fehler behoben
- Dependency-Audit-Pipeline wiederhergestellt

---

## [1.0.0] - 2026-03-09


Erster getaggter Release. Umfasst die gesamte Projektentwicklung seit Maerz 2024.

### 🌟 Highlights

- Vollstaendiges Evaluationsframework mit 6 Bewertungstypen (Ranking, Rating, Mail Rating, Comparison, Authenticity, Labeling)
- Multi-dimensionales Rating-System mit Presets (SummEval, LLM-Judge-Standard, etc.)
- LLM-as-Judge mit automatischer Evaluierung und Anti-DDoS-Schutzschichten
- Collaborative Prompt Engineering mit YJS-WebSocket-Sync
- RAG-Pipeline mit ChromaDB, Embedding-Models und Reranking
- Scenario Wizard mit AI-gestuetzter Datenanalyse und Typ-Erkennung
- Blue-Green Deployment mit automatischem Rollback
- RBAC-Berechtigungssystem mit Authentik-Integration

### Maerz 2026 (vor Tag)

#### ✨ Added
- **Deutsche Bahn Preisagent** - DB-Preismonitoring als neues Tool
- **Dev-Branch CI/CD Pipeline** fuer llars-dev Server mit eigenem Blue-Green Deployment
- Mobile Views fuer DB Agent und LaTeX Collaboration
- Conference Manager mit PDF-Viewer
- LaTeX Collab PDF-Downloads

#### 🐛 Fixed
- Blue-Green Deployment: Switch-Job, Smoke-Tests gegen Staging-Nginx
- Aggressive Disk-Cleanup in CI fuer /var-Speicherprobleme
- Stabilisierung der Nightly-Tile-Tests und Privacy-Recovery
- Relative Production-URLs fuer Frontend

### Februar 2026

#### ✨ Added
- **Conference Manager** - Verwaltung von Konferenzen und Papers
- **Manager-Rolle** fuer Szenarien; Evaluator in Assessor umbenannt
- **User LLM Providers** - Nutzer koennen eigene LLM-Provider anlegen und teilen
- **Automated Pipeline** Feature (admin-only) fuer automatisierte Evaluierungs-Pipelines
- **IONOS AI Model Hub** Katalog mit Kosten-Tracking und Token-Abrechnung
- **Referral-System** mit Live-Slug-Validation und verbesserter UX
- **Provenance-Analyse** - Herkunftsanalyse fuer Konversationspartner und Prompts
- **Demo-Video-Framework** fuer IJCAI 2026 mit Two-Speaker-TTS und Overlay-System
- openai_compatible und vLLM Provider-Unterstuetzung
- Provider-Prefix-Routing fuer LLM-Modelle (Global/{Hersteller}/{Modell})
- Server-side Generation-to-Scenario Import mit Format-Erkennung
- Per-Dimension Agreement-Metriken fuer Rating/Mail-Rating
- Skeleton Loading + Fade-Transitions fuer Scenario Evaluation Tab
- Batch Generation mit gruppierten, farbcodierten Output-Listen
- i18n-Uebersetzungen fuer RAG, DataImporter und Admin-Sections
- Automatische MkDocs-Sprachumschaltung basierend auf LLARS-Locale

#### 🐛 Fixed
- N+1-Queries in Evaluation-Session-Loading und Scenario-Stats eliminiert
- Legacy `llms`-Tabelle entfernt, durchgehend model_id Strings verwendet
- Bucket-Distribution und Provenance vollstaendig dynamisch gemacht
- Generation Stream Reconnect und Pre-Request-Latenz optimiert
- i18n SyntaxError durch unescapte @-Zeichen in Locale-Messages behoben
- 502 Bad Gateway nach --update durch Nginx-Restart behoben

#### 🔒 Security
- SSRF-Schutz und Access-Control-Enforcement verstaerkt

### Januar 2026

#### ✨ Added
- **Gunicorn + gevent** fuer Production WebSocket-Unterstuetzung (statt Flask Dev Server)
- **User API Key Management** - Nutzer koennen eigene API-Keys verwalten
- **AI Writing Assistant** fuer LaTeX Collaboration mit Streaming
- **Floating Git Panel** / Version Control Panel fuer Prompt Engineering
- **MkDocs Dokumentation** als RAG Knowledge Base fuer Chatbot
- **KaiMo Case Sharing** mit per-User-Ownership und Auto-Save
- AI-Analyse fuer Scenario Wizard verbessert (Dateiformaterkennung)
- LFloatingWindow Komponente
- Scenario-Invite-Flow verbessert

#### 🐛 Fixed
- Chatbot: PROJECT_URL-Platzhalter in RAG-Kontext und LLM-Antworten ersetzt
- Socket.IO Background-Thread App-Context und LLM-Client-Initialisierung
- AI-Comment-Kontext auf 1000 Zeichen erhoeht, Nginx-Timeout angepasst

### Dezember 2025

#### ✨ Added
- **CI/CD Pipeline** vollstaendig mit GitLab Shell Runner konfiguriert
- **Zotero OAuth Integration** fuer LaTeX Collaboration
- **System Settings** Admin-Section mit Runtime-Config
- **AI Writing Assistant** fuer LaTeX Collaboration
- Markdown Collaboration mit YJS-Sync verbessert
- System Settings Datenbank-Tabelle fuer Laufzeitkonfiguration
- Pytest-Konfiguration und Test-Struktur aufgebaut
- Comprehensive Unit- und Integrationstests (Frontend + Backend)

#### 🐛 Fixed
- ChromaDB page_content=None Bug (defensive Behandlung)
- PDF.js Worker: MIME-Types, CSP, auto-copy bei Build
- Frontend Healthcheck Timeout auf 60s start_period angepasst
- Collection Embedding Service und Seeder-Verbesserungen

### November 2025

#### 🔁 Changed
- **Grosses Refactoring** (16 Major-Refactorings abgeschlossen):
  - ChatWithBots.vue (3299 auf 774 Zeilen), JudgeSession.vue (2174 auf 579)
  - ChatbotEditor.vue (1967 auf 507), chat_service.py (1657 auf 590)
  - crawler_service.py (1415 auf 666), anonymize_service.py (1275 auf 445)
  - Composable-Extraktion fuer alle grossen Vue-Komponenten
  - Backend-Routes in modulare Dateien aufgeteilt (judge, oncoco, RAG, statistics, sessions)
  - `tables.py` in modulare Model-Dateien aufgeteilt (Phase 1)
  - Web-Crawler in modulare Komponenten gesplittet

### September - Oktober 2024

#### ✨ Added
- Authentik OAuth2 Integration mit RBAC
- Ranking- und Rating-System Grundfunktionen
- LLM Integration (OpenAI, LiteLLM)
- Chatbot-Builder mit RAG-Integration
- Web-Crawler fuer Wissensbasen

### Maerz - August 2024

#### ✨ Added
- **Projektstart** - Vue 3 + Flask Backend initialisiert
- Grundlegende Ranker/Rater Dashboards
- Drag-and-Drop Ranking-Interface
- E-Mail-Thread-Verwaltung und Szenario-Grundstruktur
- MariaDB-Integration mit ersten Tabellen
- Docker-Compose Setup mit Hot-Reloading
- Authentik User-Management Grundlagen

---

## Links

- Repository: git.informatik.fh-nuernberg.de/kiz-nlp/llars/llars
- Production: 141.75.150.128
- Dev: 141.75.150.86
