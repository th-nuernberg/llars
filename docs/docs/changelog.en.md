# 📜 LLARS Changelog

![Version](https://img.shields.io/badge/version-1.24.0-b0ca97?style=flat-square)
![Released](https://img.shields.io/badge/released-2026--09--15-88c4c8?style=flat-square)
![Releases](https://img.shields.io/badge/releases-31-D1BC8A?style=flat-square)
![Format](https://img.shields.io/badge/format-Keep%20a%20Changelog-98d4bb?style=flat-square)

All notable changes to **LLARS** (LLM Assisted Research System) — **newest first**.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

**Legend:**  ✨ Added · 🔁 Changed · 🗑️ Removed · 🐛 Fixed · 🔒 Security · ⚡ Performance · 📚 Docs

> **Versioning** — LLARS uses **tag-based semantic versioning** via
> `git describe --tags --match "v*" --first-parent`. A tag `vMAJOR.MINOR.PATCH`
> yields `MAJOR.MINOR.(PATCH + N)`, where `N` is the number of commits since the
> tag; at the tagged commit itself `N = 0` and the version equals the tag exactly.
> Releases are tagged on `main` after every `dev`→`main` merge (currently **v1.0.0 … v1.24.0**).

---

## [Unreleased]

### 🐛 Fixed

- **Labeling: partial answers count as "in progress"** — With question-first labeling a row in `item_labeling_evaluations` can hold answers, a second choice or a comment but no label yet. It used to show as "pending" everywhere. There is now one three-way rule in one place (`labeling_types.labeling_row_status`: label or "unsure" = `done`, otherwise any input = `in_progress`, otherwise `pending`) shared by the session status, single-item status, progression, scenario stats, span progress (type 9) and the manager's item list. The save endpoint returns that status instead of the old `completed`. Partial rows are **not votes**: export and IRR skip them, and per-case timing plus the co-pilot log are written on the first complete label, not the first click. `LABEL_STATUS_001–026`.
- **Labeling persists every selection immediately** — each answered question, lean slider, second choice, direct label, "unsure" and the comment is saved on click (POST with `category_id: null` + `answers_json` while no label can be derived yet). The item shows as **"In progress"** until the label is complete (item list, session footer and the status tag in the labeling panel, including a "Saving…" indicator); in-flight saves are awaited before navigating (next/previous, session navigation included) and on leaving the interface. Previously a rater who answered two of three questions and clicked on lost that work (prod scenario 758). A label is still never pre-selected.

## [1.24.0] - 2026-09-15

### ✨ Added

- **Question-first labeling (labeling types 7/9):** A labeling scenario can put decision questions in front of the label (`questions` in the labeling config: `items` with two answer options each, `mapping` answer key → label, optional `sliders` as supplementary "rather A … rather B" info, `direct_selection`). Annotators answer the questions at the top with buttons, the label is derived from the answer key and never pre-selected; the direct choice stays available in an expandable section and sets the answers backwards via the mapping. Answers are stored in `item_labeling_evaluations.answers_json` (new column, startup migration `migrate_labeling_second_choice_answers.py`), in the session prefill and as export column `answers_json`. Model: the VRM cheat sheet (Stiles 1992) – topic / presumption / frame of reference, each S/G. `LabelingInterface.vue`, `DecisionQuestionsConfig`, `LABEL_009–013`.
- **Second choice ("rank 2") in labeling:** `second_choice: true` shows chips for a second label after the first choice – not a multi-label, the study label stays `category_id`; the second choice is stored in `second_choice_id` and exported as column `second_choice`. "Both defensible" cases are no longer thrown away. `LABEL_011`, `LABEL_SVC_026`.
- **Co-pilot answers the decision questions first:** If the scenario has `questions`, the format block of every suggestion requires `answers` (one option per question) first and then the explicit `label_id`; the parser carries `answers`, `derived_label_id` (from the mapping) and `consistent` through, the explicit label stays authoritative. Changes to the questions bump `prompt_version` like `top_k`. The answers appear in the suggestion panel. `_validate_copilot_answers`, `COPILOT_Q_001–006`.
- **v1 API `PUT /api/v1/scenarios/{id}/labeling-config`:** toggles `questions` and `second_choice` headlessly via API key (owner/admin, `scenario:write`) – the generic scenario PUT is session-only and the v1 PATCH refuses `eval_config`, so study scripts had no path to these settings. Validated against `DecisionQuestionsConfig`, mapping targets must be label ids, the `config.config` mirror stays in sync. `LABEL_SET_001–007`.

### 🐛 Fixed

- **Labeling feedback was lost when moving on:** The comment was saved with an 800 ms delay; navigating to the next item cleared the timer and emptied the field before the POST. A pending comment is now saved before `goNext`/`goPrev`, on leaving the field and on unmount, and a failed save shows a snackbar instead of only `console.error`. `LABEL_012`.

## [1.23.0] - 2026-08-23

### 🔁 Changed
- **Sign-in links from emails are now multi-use** — The passwordless sign-in link in the post-QR-scan welcome mail and in the returning-participant mail (`/auto-login/<token>`) used to be **single-use**: it died on the first click, so anyone reopening the email later was locked out. The link now works **as often as you like within its validity window** — participants scan the QR code once, get the email, and sign in with it again and again for up to **7 days**. The bounds are unchanged: a strict **168-hour TTL**, only the SHA-256 hash is stored in the database, and a newly sent sign-in link **retires the previous one**. The mail copy (DE/EN) now says so too ("valid for 7 days and reusable as often as you like") instead of "single-use".
- **Friendly page for an expired sign-in link** — Opening an expired link no longer lands on "Sign-in failed" but on **"This sign-in link has expired"**, with an explanation (sign-in links are valid for 7 days for security reasons) and a clear next step: via **"Forgot password"** (the button leads straight to `/forgot-password`) participants can set a password of their own at any time — entering their email address is enough. "Go to login" remains as the secondary action. Bilingual (DE/EN).

### 🔒 Security
- **`purpose` column separates reset links from sign-in links** — Both kinds of link used to sit indistinguishably in the same `password_reset_tokens` table. That allowed a **sign-in token to be posted to `/auth/password-reset/reset` and change the account password** — a privilege a sign-in link was never meant to carry, least of all now that it is a reusable 7-day link. The new `purpose` column (`'reset'` | `'magic'`) closes this in both directions: `/auth/password-reset/reset` accepts `'reset'` only (NULL/legacy rows count as `'reset'`), `/auth/magic-login` accepts `'magic'` only. The two flows also stop invalidating each other: a fresh sign-in link no longer kills a pending password-reset link, and vice versa (this included the 2-minute anti-mail-flooding cooldown, which would otherwise have swallowed the reset mail requested right after a QR scan). The migration `migrate_add_password_reset_purpose.py` runs **idempotently at server startup** — no manual SQL.

## [1.22.0] - 2026-08-21

### ✨ Added
- **New license: PolyForm Noncommercial 1.0.0 with a citation clause** — LLARS moves from "MIT/open source" to the **[PolyForm Noncommercial License 1.0.0](https://github.com/th-nuernberg/llars/blob/main/LICENSE)** with additional terms: **free for research, teaching and any other noncommercial use** (universities, government bodies and charitable organizations explicitly included, regardless of funding source), while **commercial use requires a separate license** (contact: steigerwaldph@ki-zentrum.bayern). New is the condition that **academic work using LLARS — or data produced with it — must cite the LLARS paper**: the citation is a condition of the license grant, not a request. A new `LICENSE` file sits in the repository root (verbatim PolyForm text plus `Required Notice:` lines and Additional Terms); `README.md` and `CITATION.cff` were updated accordingly. Versions published **before** this switch shipped without a license file and remain governed by the terms under which they were obtained.
- **In-app citation hint** — Both footers (app footer and landing-page footer) now carry a discreet **"Cite LLARS"** link that opens a small dialog: the ask, the full BibTeX entry in a monospace box, and a **copy** button (with a "Copied!" confirmation). One reusable component (`LCitationDialog.vue`) serves both places; the BibTeX block is deliberately a code literal rather than a locale string so translations cannot break the LaTeX escaping (`\&`). All surrounding text is bilingual (DE/EN). The landing footer additionally states the license model in one sentence and links to `LICENSE`.
- **`citation` block in JSON exports** — Every JSON export (v1 API `GET /api/v1/scenarios/<id>/results` **and** the GUI export `GET /api/scenarios/<id>/export`) now carries a `citation` block in its envelope with `message`, `paper` (short reference including the arXiv ID) and `bibtex_url` (pointing at `CITATION.cff`). Anyone who only ever receives the export file still has the citation at hand. **Deliberately not in CSV/JSONL:** a comment or preamble line would break strict parsers (`pandas.read_csv`, R `read.csv`, line-by-line JSONL readers). The literal lives in exactly **one** place (`results_export_service.CITATION_BLOCK` / `citation_block()`) and is imported by both routes — guarding the same regression class that dropped `timing_metrics` from the v1 envelope in 1.21.0. (Tests EXPORT_CITE_001–006.)
- **"Citing LLARS" docs page** (`guides/citing-llars.md`, DE + EN) — why and how to cite (BibTeX, plain text, `CITATION.cff` + `cffconvert`), where the citation surfaces in the product, plus a license section breaking down research / non-profit / academic / commercial use. Notes that the reference currently points at the arXiv preprint and will be switched to the IJCAI-ECAI 2026 proceedings version once it appears.

### 🔁 Changed
- **App copy: "open source" → "source-available / free for research"** — Everywhere LLARS described its **own** license or nature, the wording now matches the new model: landing hero badge and subtitle, tech and research sections (including "MIT license — permanently free" → "PolyForm Noncommercial 1.0.0 — permanently free for research and teaching, commercial use on request"), landing navigation, docs hero tag, and **§ 5 of the Terms of Use** (now "Source-available & license", including the citation requirement and the pointer to a separate commercial license). Also updated: the static SEO metadata and the JSON-LD `SoftwareApplication` in `index.html`, whose `license` pointed at `opensource.org/licenses/MIT` and was simply wrong. **Left untouched:** mentions of open-source *third-party* software (Matomo, Authentik in the privacy policy), third-party model licenses (OnCoCo, CC BY-SA 4.0), and the paper reference "TextGrad … (MIT, 2024)", where "MIT" means the university. The landing anchor `#open-source` is kept so existing deep links keep working.

### 🐛 Fixed
- **`CITATION.cff` declared two licenses** — The file contained a duplicate `license:` key; on YAML parse the second (`MIT`) overrode the first (`PolyForm-Noncommercial-1.0.0`), so GitHub and `cffconvert` would still have reported MIT. Duplicate removed.

### 🗑️ Removed
- **DB price agent removed entirely** — The admin-only alpha tile "DB Preisagent" and its dashboard (`/db-agent`) are gone without replacement. The tool had nothing to do with what LLARS is for: it scraped the bahn.de fare search for **one single hardcoded route** (Dortmund Hbf ↔ Nürnberg Hbf, BahnCard 25, second class), collected journey prices in its own background scheduler and had an LLM derive travel recommendations from them. The scanner had been running into nothing for months — the public bahn.de endpoint answered `403 Forbidden`, which is why the scheduler thread was already switched off via `DB_AGENT_SCHEDULER_ENABLED=false`. Removed: the tile with its route and the `feature:db_agent:view` permission, all `/api/db-agent/*` endpoints (status, scan, scheduler control, statistics, deals, calendar, price history, volatility, weekday/timing analysis, LLM analysis, trip search), the scanner/analyzer/scheduler service including its startup thread in `main.py`, the three tables `db_price_scans`, `db_price_entries` and `db_trip_searches`, the four icons used only here (`train`, `train-outbound`, `train-return`, `deal`) along with their hover animations, plus 97 i18n keys in DE and EN. Existing databases are cleaned up by `migrations/20260821_remove_db_agent.sql` (tables child-before-parent, then the permission including its role/user assignments).

## [1.21.0] - 2026-08-21


### ✨ Added
- **Merging spans (conversation labeling)** — The counterpart to splitting, under the same rules: allowed only for **directly adjacent spans of the same message with nothing but whitespace between them** (any text in between would otherwise slip into a judged unit unnoticed). The new id is derived, and undoing a split is the common case — `x+a` + `x+b` gives back plain `x`, so a study carries exactly the ids it started with. **Both** votes are deleted for every rater, along with the co-pilot log row and timing: two decisions about two units are not one decision about their union. Spans are marked with **ctrl/cmd-click** (dashed outline, counter on the button); "Merge spans" stays greyed out until the marking forms an unbroken run within one message. Only **whitespace** may sit between them — in a real segmentation sentence spans are one space apart, so demanding exact contiguity would have left the button dead in every genuine conversation. When two neighbours carry the same label, a prompt pre-marks them — deliberately marking only and **not** merging automatically: the segmentation is shared by every rater, so changing it based on one person's labels would shift the units under everyone else and delete their votes. Two dedicated LLARS icons (`span-split`, `span-merge`) in the icon registry; both tools sit quietly at the bottom of the panel above the note field. (`span_progress_service.merge_spans`, `POST /api/evaluation/session/<sid>/items/<iid>/spans/merge`; tests SPANMERGE_001–008, CONVLAB_028–030.) See [Conversation Labeling](guides/conversation-labeling.md).
- **New scenario type: conversation labeling (`function_type_id = 9`)** — Labels sense units ("spans") **inside** a conversation rather than the message as a whole. One item is a whole thread and holds many decisions (~92 in the VRM study); the **unit of analysis is therefore the span, not the item**. That runs through everything: Krippendorff's alpha is computed over span cells, time on task is measured per span, and a conversation only counts as done once *every* span is decided ("40 of 92" is a normal middle state that classic labeling does not have). The segmentation arrives finished from the import and is frozen — if everyone segmented for themselves, the rows of the rater matrix would no longer be the same units and an agreement coefficient across them would not be interpretable. Interface: the conversation on the left as speech bubbles, unfolding **turn by turn** (later messages stay hidden — raters should not know how it ends), auto-advance on by default (at ~92 decisions, clicking back into the text is otherwise the single largest cost), keyboard `1`–`9`/`Enter`/`Backspace`, auto-save on every selection. The co-pilot works span by span, is never pre-selected, and uses a server-side hidden control subset with identical visibility for human and model. Exports carry `span_id`/`message_id`/`span_index` (at the end of the column list so position-indexed analyses keep working). New `span_id` column on `item_labeling_evaluations`, `labeling_copilot_logs` and `evaluation_item_timings`, with an idempotent startup migration. (`ConversationLabelingInterface.vue`, `span_progress_service.py`, `labeling_types.py`; tests CONVLAB_001–027, APIV1_RES_014–019, TIMING_020.)
- **Splitting a span (deliberately understated)** — When a span plainly carries two speech acts, it can be cut at a character boundary through a quiet link below the target span. The cut must fall strictly inside (at the edge it would create a zero-length unit), new ids are derived (`x` → `x+a`/`x+b`) rather than renumbered (so an older export still joins), and the vote on the old span is deleted **for every rater** — together with its co-pilot log row and timing, because those describe a unit that no longer exists. Placed unobtrusively so that re-cutting stays the exception.
- **Add/remove an LLM as an assessor — like a human** — The "Add LLM" dialog in the Assessors tab now actually works (it used to be a TODO stub with a hardcoded model list that saved nothing). You pick a genuinely available model (`/api/llm/models/available`, filtered to `model_type='llm'`), and on adding it is persisted to `config_json.llm_evaluators` **and the managed runner starts automatically** — labelling/annotating every item with all existing safeguards (lock per (scenario, model), cooldowns, circuit breaker, permanent-failure and total-failure caps). Removing deletes the model plus its stored results (out of IRR and exports). New endpoints `POST/DELETE /api/scenarios/<id>/llm-evaluators[/<model_id>]` (owner/admin; Bearer **or** X-API-Key). (`scenario_crud.py`, `ScenarioTeamTab.vue`; tests ADDLLM_001–011.)
- **"Demo Video" opens the internal LLARS video page (YouTube is now only a backup)** — The "Demo Video" button in the landing hero (and the footer "Demo" link) now lead to the self-hosted video page `/video` (playing `/videos/llars_demo.mp4`) instead of straight to YouTube. The YouTube link is **only** linked as a backup on the video page (in case the file does not play). `/video` is public for this (`requiresAuth: false`) so visitors who are not logged in can see the demo (`HeroSection.vue`, `LandingFooter.vue`, `DemoVideoPage.vue`, `router.js`).
- **Unlock a phase directly in the Overview tab** — For labeling scenarios with phases (parts/calibration phases), every phase row in the **Overview** tab now has an **Unlock/Lock** button (previously read-only with a pointer to the Settings tab). Owners/managers unlock the next phase where they see the progress. Uses the same management-gated endpoint `PUT /api/scenarios/<id>/parts/<part_id>` (`ScenarioOverviewTab.vue`).

### 🗑️ Removed
- **LaTeX collaboration removed entirely, including the AI writing assistant and the Zotero integration** — The LaTeX workspace (`/LatexCollab`, `/LatexCollabAI`) with its real-time editor, PDF compilation (pdflatex/biber/SyncTeX), workspace git panel and template picker is gone without replacement; **Markdown Collab is unaffected** and remains the collaborative editor in LLARS. Removed along with it: the tightly coupled **AI Writing Assistant (LatexCollabAI)** — ghost text, `@`-commands, selection menu (rephrase/expand/shorten), AI sidebar chat and citation/DOI search — and the fully dependent **Zotero integration** (OAuth connection, library import, BibTeX generation) including its encrypted credentials. This drops the `latex_collab:*` Socket.IO events, the `/api/latex-collab/*`, AI-writing and Zotero endpoints, the `latex_*` tables, the permissions `feature:latex_collab:view/edit/share/ai` and the `ZOTERO_*` configuration variables. On the infrastructure side the `texlive-full` layer (~5 GB) leaves the Flask image. **Not affected:** the external `overleaf_url` link on conference papers (plain web link) and the Markdown collab permissions `feature:markdown_collab:*`.
- **Voice/video calls with live transcription (LiveKit) removed entirely** — The messaging module now offers text chat only (incl. E2E encryption, reactions, link previews and AI summaries). Removed: the phone/camera buttons in the chat header with the call and transcription panels, the Socket.IO events `messaging:call_initiate/accept/decline/end`, the endpoints `POST /api/messaging/calls/transcript-chunk` and `GET /api/messaging/calls/<id>/summary`, `CallService` + `CallTranscriptionService`, the (already orphaned) STT provider package, the tables `messaging_calls`/`messaging_call_participants`, the message type `call_event` and the permissions `feature:communication:voice`, `:video` and `:transcription`. On the infrastructure side the containers `livekit-service` + `livekit-agents-service`, the nginx upstream `/livekit/` and all `LIVEKIT_*`/`STT_*` variables are gone. **Not affected:** the messaging master switch `system_settings.communication_enabled`, the permissions `feature:communication:access/chat/ai` and the public demo-video page `/video`. Existing databases are cleaned up via `migrations/20260821_remove_call_feature.sql` (existing `call_event` messages are rewritten to `system` before the ENUM is narrowed).

### 🐛 Fixed
- **Conversation labeling: IRR described one arbitrary span per conversation** — `_collect_human_evaluations` wrote all ~92 span rows of a conversation into the same cell `data[item][rater]`; the last one written won. The alpha looked perfectly normal and meant nothing. The unit of analysis is now the span (`item::span`, the same pattern as dimensional pooling).
- **Conversation labeling: the model dropped silently out of every comparison** — The LLM predictions live span by span under `task_type = "copilot_labeling"`, not under `"conversation_labeling"`. The query matched nothing. The cache row is now fanned out; the model's vote is its primary suggestion — exactly the one a human would have been shown.
- **Conversation labeling: co-pilot data was duplicated across spans** — The export join was keyed by `(user, item)` and collapsed ~92 log rows into one, so every span of a conversation carried the same suggestion, the same acceptance and the same `helpful` flag — fabricated study data that looked plausible in the CSV. Same pattern for the timings (`timings_for_scenario` now returns 3-tuples).
- **Add-LLM-assessor UI was inconsistent** — After adding an LLM assessor the row showed "0/0" plus a **Start** button, although the runner had already been started **automatically** server-side (the live stats arrive with a delay). Clicking "Start" was then a no-op (runner lock) → "nothing happens". Fix: models just added or started are shown as **"Running" immediately** (no misleading Start button) until the real stats take over. The dead **"Template: Standard/Detailed" dropdown** was also removed from the dialog (a decoy with no backend effect), and the DELETE endpoint resets `enable_llm_evaluation` when the last model is removed. The add/remove endpoints now check `check_scenario_management_access` (owner/manager/admin) instead of owner-only — consistent with the `canManage` UI gating and the `/start` endpoint, so an editor no longer sees a button that throws 403. (`ScenarioTeamTab.vue`, `scenario_crud.py`.)
- **The LLM labeler was given the wrong task** — For (wizard-typical) labeling scenarios the runner sent the model the **raw category ids** (`cat_1782…`) instead of the names (`include`/`exclude`) and **left out the task description and inclusion criteria entirely** (they were read from the wrong, top-level config path; in the wizard they sit under `eval_config.config.*Markdown`). The result would have been guesswork or nothing but errors. `_run_text_classification` now passes the label names as meaning (the model still answers with the id → aligning with the human `category_id` in IRR), fetches task and criteria through the correct resolver, and mirrors the `unsure` option. Label extraction was additionally made **robust across all config shapes** (`_extract_labels_from_config`): `categories` **and** `labels` lists, dict entries with a `name` **or** `label` key (localized), strings, `classification_labels`, top-level and nested — before this, scenario 629 (labels as dicts under `config.labels`) fell back to the default labels `positive/negative/neutral`. (`llm_ai_task_runner.py`; tests LABELTASK_001–009.)
- **Google Maps on the contact page was blocked (CSP)** — The consent-gated Google Maps embed (`Kontakt.vue`, iframe `maps.google.com/…&output=embed`) was blocked by the CSP `frame-src 'self' blob:` (`Framing 'https://maps.google.com/' violates … frame-src`). Added `https://maps.google.com https://www.google.com` to `frame-src` in both production nginx configs (`nginx.prod.conf`, `nginx.prod-no-ssl.conf` — port 80 and 443 blocks). The map loads after consent.
- **Demo video (`/videos/llars_demo.mp4`) returned 404** — Not a code bug: the 85 MB file is deliberately gitignored/dockerignored and served through the host mount `./static/videos → /srv/llars-static/videos` (the nginx `location /videos/` already existed), but it was not present on the production host. The file was placed in `/var/llars/static/videos/` → it is now served (with range streaming). **Ops note:** on a fresh host setup the video has to be placed there manually.
- **`timing_metrics` was missing from the v1 JSON export** — The v1 route builds its JSON envelope from selected keys; the new aggregate block (`timing_metrics`) from `collect_results` was not passed through (the CSV had the per-case columns, but the JSON lacked the per-rater figures). Key added (`scenario_results_routes.py`; test APIV1_RES_013). The GUI export was unaffected.

## [1.20.0] - 2026-07-15


### ✨ Added
- **Time per case in every export** — Every evaluation export (v1 API `GET /api/v1/scenarios/<id>/results` **and** the GUI export `GET /api/scenarios/<id>/export`, for **all** types: rating, mail rating, ranking, comparison, communication comparison, authenticity, labeling) now contains two time columns per judgement: **`time_on_item_ms`** (client-measured time from displaying the item to the first save) and **`time_since_prev_ms`** (a derived fallback: the gap between the `created_at` timestamps of a rater's consecutive cases — so **older studies** without real capture get an approximation too; the first case per rater and ranking rows stay empty). Real capture: a new central table `evaluation_item_timings` (one row per rater/item/scenario, first-write-only), fed by a `Date.now()` timer in all evaluation interfaces and wired into the 4 submit endpoints. Labeling additionally continues to use `labeling_copilot_logs.time_on_item_ms`. The JSON envelope (v1 API and GUI export) also contains a `timing_metrics` block with **aggregated figures per rater** (n, mean, median, min, max, standard deviation, total, plus captured/derived provenance) and an overall block — correctly deduplicated per case (rating has several rows per case). (`EvaluationItemTiming`, `ItemTimingService`, `results_export_service`, `scenario_manager_api`; tests TIMING_001–019, CMP_TIME_001/002).

### 🐛 Fixed
- **Matomo custom logo and absolute URLs (missing `/analytics/` base path)** — The publicly active port 80 nginx block (the gateway forwards there over HTTP) did not pass `X-Forwarded-Uri /analytics` through, so Matomo (`proxy_uri_header=1`) did not know its base path and built absolute URLs — including the LLARS custom logo — **without** the `/analytics/` prefix → 404 / broken image. Added `X-Forwarded-Uri` (plus `-Host`/`-Port`) to the port 80 and no-ssl blocks (the 443 block already had them). Completes the branding and mixed-content fix from 1.19.0.

---

## [1.19.0] - 2026-07-13


### ✨ Added
- **Matomo in LLARS branding** — The analytics dashboard (`/analytics/`) now shows the LLARS logo (login and header) instead of the Matomo default. Implemented via a custom logo in `misc/user/` plus `branding_use_custom_logo=1` through `docker/matomo/init-matomo.sh` and `configure-branding.php` (best effort, never aborts the Matomo init).
- **MkDocs documentation in the LLARS design** — The documentation (`/mkdocs/`) now carries the LLARS colour palette (green header `#b0ca97`, teal links/accents), the LLARS logo in the header and as favicon, and the asymmetric border-radius signature (code blocks, admonitions, tables, search). Implemented through `extra_css` (`docs/docs/stylesheets/llars.css`) rather than a theme rewrite; covers both light and dark schemes.
- **Space bar = "next" in evaluations (opt-in)** — A new **Preferences** settings tab (`/settings`) with a "space bar jumps to the next item" switch. **Off** by default; every user enables it for themselves. When on, the space bar advances to the next item in every evaluation (all scenario types) — unless the focus is in a text field (where it types a normal space). The preference is stored **per user** in the backend (`user.settings_json`, across devices). The tab is laid out as a home for future preferences (`PreferencesTab.vue`, `useUserPreferences.js`, `EvaluationSession.vue`).
- **Changelog by clicking the version number** — The version number in the footer (and the version tag in the app bar in dev mode) is now a link to the changelog (`/mkdocs/changelog/`, language-aware), so you can read what changed between releases (`App.vue`, i18n `footer.changelog`).

### 🐛 Fixed
- **The Matomo dashboard was broken (CSP `unsafe-eval`)** — Matomo's Vue UI uses `new Function()`; the globally hardened CSP (`script-src` without `unsafe-eval`, pentest M11) blocked it → the dashboard broke while mounting (jQuery/EvalError). Fix: a path-dependent CSP via an nginx `map` — only `/analytics/` gets `unsafe-eval` (Matomo is additionally auth-protected), the rest of the app stays strict. Verified locally in Chrome: `/` without, `/analytics/` with `unsafe-eval`; the dashboard mounts.
- **Matomo mixed-content warnings** — Behind the SSL-terminating FH gateway (HTTP to the app nginx), Matomo generated absolute `http://` URLs → mixed content on the HTTPS page. Fix: `assume_secure_protocol = 1` in Matomo's `config.ini.php` (production only, via `init-matomo.sh`).
- **Changelog badges did not load in MkDocs** — The shields.io badges in the changelog header (version/released/…) were blocked by the content security policy (`img-src` did not allow `img.shields.io`). Added `img.shields.io` to the CSP `img-src` (`nginx.prod.conf`, `nginx.prod-no-ssl.conf`).
- **Labeling: item status in the footer (wrongly "in progress")** — In the evaluate view the status tag at the bottom showed the **overall progress** instead of the status of the **current** item. As a result a fresh, untouched item wrongly read "in progress" (because other items were already done), and navigating back to an already **completed** item also read "in progress" instead of "completed". Fix: `LabelingInterface` now emits the status of the item currently displayed (`done` | `pending`) instead of the aggregate (`LabelingInterface.vue`, tests LABEL_007/008).
- **E2E deploy gate unblocked (consent banner)** — After the consent buttons were renamed (`Accept all` / `Only necessary`), the E2E helper `dismissConsentBanner` clicked the first button in the banner — which is the **privacy link**, navigating to `/Datenschutz` and thereby leaving the login flow. As a result 33 nightly E2E tests ran into a 30 s login-form timeout and the production deploy gate stayed blocked (production was stuck on 1.17.2). Fix: stable `data-testid`s (`consent-accept` / `consent-decline` / `consent-privacy`) on the banner, and the helper clicks `consent-accept` specifically and stays on the page (`e2e/helpers.js`, `e2e/auth.setup.js`, `e2e/login.spec.js`).
- **Documentation link (footer) → MkDocs instead of 404** — Public traffic runs through the SSL-terminating FH gateway, which forwards over **HTTP** to the **port 80 server** of the production nginx. That block did have the `location = /mkdocs` redirect but **no `/mkdocs/` proxy** (only the 443 block had one) → `/mkdocs/` fell into the SPA catch-all and showed the Vue 404 ("document not found"). Fix: added the `/mkdocs/` proxy block to the port 80 server as well (`docker/nginx/nginx.prod.conf`).
- **Progress on labeling scenarios (0/0 despite labels)** — In `get_progress_stats` a labeling assessor without active parts counted against the (empty) `ScenarioThreadDistribution` table and showed 0 done / 0 pending, although the session hands **every** assessor **all** items (no per-user distribution). Fix: labeling assessors without parts now count against all items — consistent with `session_service._get_items_for_scenario` and `get_user_progress_counts` (bug in scenario 758; `app/services/scenario_stats_service.py`, test STATS-113).

---

## [1.18.0] - 2026-07-11


### ✨ Added
- **Landing page as the public root** — `https://llars.e-beratungsinstitut.de/` now natively shows the landing page instead of redirecting to `/login` (`/landing` remains as an alias; logged-in users still land on `/Home` or in the single-scenario shortcut). New navigation with section anchors (smooth scroll), **login and register buttons**, GitHub link (nav, hero, open-source section, footer → `github.com/th-nuernberg/llars`).
- **Interactive labeling demo with co-pilot** — A DOM-built app window on the landing page: three clickable example items with a co-pilot suggestion (rationale, confidence, highlighted textual evidence), an "accept" button, autosave check mark and progress bar; 3D tilt and cursor glow, `cursor: pointer` only on genuinely clickable elements. Plus a co-pilot explanation (never pre-selected, hidden control subset, study logging) and a new feature card in the bento grid.
- **Akteon-style animations** — Hero background blobs fly in staggered on page load (then drift endlessly), a `PaintStrokesReveal` component (scroll-triggered blob entry, CTA finale and open-source section), a `v-glow` directive (cursor-following sheen on cards), a scroll hint arrow, bear bobbing — all with `prefers-reduced-motion` fallbacks.
- **Open-source section "By researchers, for researchers"** — Photo (locally hosted Unsplash image, `assets/landing/ATTRIBUTION.md`), MIT/self-hosting/reproducibility points, GitHub and documentation CTA.
- **New itshover icons** — `GithubIcon` (brand mark) and `CursorClickIcon`; resolver tokens `github` and `cursor/click/tap/gesture/pointer`.

### 🔁 Changed
- **Landing copy sharpened for researchers** — Hero subtitle, CTA and a new open-source message address research teams (free to use, self-hostable, stays MIT); a second hero badge "100 % open source · MIT"; the hero CTA leads to `/register`.

### 🐛 Fixed
- **Duplicate footer and hero overflow on `/landing-preview`** — Hiding the app bar and footer is now meta-based (`hideAppChrome`) instead of bound to the route name `LandingPage`; this removes the doubly rendered small app footer and the 100vh hero overflow by the app bar height (plus `100svh` for mobile browser UI).
- **"Seven evaluation types" grid** — Cards now wrap symmetrically as 4+3 (previously a lopsided 5+2); long titles ("communication comparison") are kept inside the card by hyphenation.
- **CI deploys blocked by the rate limit** — The nightly E2E suite (`test:e2e:nightly:tiles`) and `smoke:staging` test the staging instance from a single internal IP against `localhost:55080` and blew past the strict per-IP limit (500/h in production mode) → `429` plus a 45-minute job timeout, which caused `deploy:production` to be skipped (the nightly did not deploy either). Fix: internal/private test traffic is now exempt from the rate limit (`exempt_internal_ips`, spoofing-safe — real users on public IPs stay limited at 500/h); the E2E job timeout went from `45m` to `75m` as a buffer.
- **Progress on parts/phase scenarios** — In labeling scenarios with active parts (phases), the evaluator progress display showed `0/0` for assessors although labelling was happening. Cause: with active parts, items are delivered through the parts mechanism (open parts), not through `scenario_item_distribution` — but the progress calculation (`get_progress_stats`/`get_user_progress_counts`) still counted against the (empty) distribution table. Both functions are now parts-aware (an assessor's item set = the items of the open parts, mirroring delivery); non-parts scenarios are unchanged.

### 🔒 Privacy
- **Two-click Google Maps solution on the contact page** — The Maps `iframe` (which opens a connection to Google including IP transfer and cookies) is only loaded after explicit consent; before that there is only a local placeholder with a note and a privacy link, and no request goes out to `maps.google.com`. Consent is remembered per browser (`localStorage`). This matters because the contact page is reachable from the new public landing page. (Fonts are already fully self-hosted; the Matomo/analytics consent banner also appears on the landing page.)
- **Official LLARS contact address** — The contact page now shows `llars@e-beratungsinstitut.de` (identical to `MAIL_REPLY_TO` in the backend) as a clickable `mailto` link instead of the old `info@` address.
- **Privacy policy fully revised** (as of 07/2026, `/Datenschutz`) — Instead of 6 thin sections there are now 13: server log files, cookies and local storage, reach measurement (Matomo, cookie-free and consent-gated), Google Maps, account/Authentik, email dispatch, recipients, retention, data protection measures, plus the full data subject rights including the **right to complain (BayLfD)** and legal bases (Art. 6/9 GDPR, BayDSG).
- **Terms of use page** (`/Nutzungsbedingungen`, DE/EN, 9 sections) added — scope, account, permitted use, research data/data donation, open source, availability, liability, termination, final provisions. Linked in the footer (landing and app).
- **Registration consent** — A mandatory checkbox "I accept the terms of use and the privacy policy" for **every** registration (the button is disabled without the check, hard-gated in `handleRegister`), separate from the study consent (which applies additionally for study links). Plus a transparency note on research use/data donation (legal basis: public research task, Art. 6(1)(e) GDPR, no coupled consent).
- **Cookie banner to EU standard** — "Accept all" / "Only necessary" instead of "Agree/Decline", with clearer wording on necessary versus optional (Matomo) cookies.
- **SEO essentials** — `index.html` with a meaningful title, meta description, keywords, Open Graph and Twitter card tags, `canonical`, `robots: index,follow`, and JSON-LD structured data (`SoftwareApplication` + `Organization`, free/MIT). New: `robots.txt` (allows indexing, points to the sitemap, blocks api/auth/reset/join) and `sitemap.xml` (public pages). The manifest gained a description and categories. Per-route document titles (`meta.seoTitle` + `router.afterEach`) for tab titles and JS-rendering crawlers. Target keywords include "LLM evaluation software", "label software", "inter-rater reliability".
- **`<noscript>` content block** in `index.html` — real textual content (heading, core description, features, keywords, links) for crawlers and users without JavaScript, without SSR/prerendering risk.

### ⚡ Performance
- **Code splitting** (`vite.config` `manualChunks`) — the large, lazily loaded leaf libraries (Vuetify, pdfjs-dist, jsPDF/html2canvas, Leaflet) are separated into their own, long-term cacheable chunks. The main bundle went from ~6.8 MB to ~5.9 MB; the framework core stays in the main bundle (separate `vue`/`realtime` chunks created circular dependencies). Improves load time and Core Web Vitals — verified in the built preview without console errors.

### 🔁 Changed
- **App bar logo click** — logged-in users land on `/Home`, users who are not logged in (e.g. on `/login`) land on the public landing page `/`.
- **MkDocs language coupling** — Documentation links in LLARS now open the version matching the UI language (DE → `/mkdocs/`, EN → `/mkdocs/en/`, via `utils/docsUrl.js`; app footer, landing footer, research section, documentation overview, `/docs` redirects). nginx no longer **forces English** — the complete German documentation (the default language) is reachable under `/mkdocs/` again, English under `/mkdocs/en/`, and MkDocs' own language switcher works again (correct `/mkdocs/` base path via `site_url`). Dev (`mkdocs serve`, no strip) and production (static build, strip) are distinguished accordingly in the nginx configs. **Note:** on production the public documentation remains separately blocked by the FH gateway cache (stale SPA) until that cache is cleared.

---

## [1.17.0] - 2026-07-11


### ✨ Added
- **Scenario parts (phases) for labeling** — Labeling scenarios can optionally be divided into ordered parts (wizard section "Parts / Phases" plus v1 API), the study gate for calibration designs (e.g. P1 calibration → IRR/alignment meeting → unlock P2 → main phase with co-pilot): per part an **order** (`sequential` = identical for all raters / `random` = deterministic per-user shuffle), **co-pilot on/off** (the runner only generates for co-pilot parts; the hidden control subset works unchanged within them), and **lock/unlock** (owner UI in the Settings tab plus `PUT /api/v1/scenarios/<id>/parts/<part_id>`). For raters the division is **invisible** (parts/co-pilot sections are stripped server-side from session, list and stats responses; item totals are scaled to the open parts). For analysis: a `part` column in the results export, a `?part=` filter on the agreement metrics (IRR per phase, combinable with `?copilot=`), and `copilot_metrics.per_part`. Loading further items requires `part_id` when parts are active (partition invariant: every item belongs to exactly one part). Without `parts` in the config nothing changes (opt-in).

### 🔒 Security
- **Co-pilot internals no longer in the assessor payload** — `hidden_control_salt`/`ratio` used to be part of the session/list config, which made the hidden control subset computable client-side. The `copilot` section is now removed server-side for non-managers (the evaluator UI does not read it).

---

## [1.16.0] - 2026-07-05


### ✨ Added
- **Labeling co-pilot (LLM pre-annotation)** — Can be enabled per labeling scenario (scenario wizard plus v1 API), modelled on the DMRS co-pilot from PsyDefConv: a freely editable prompt template (`{item}`/`{context}`/`{labels}`/`{codebook}`) with **per-scenario prompt versioning**, batch pre-generation through the LLM runner queue (cached per item × prompt version × model), **top-1/top-2 suggestions** with rationale, an evidence quote and confidence in the labeling interface (clearly marked, never pre-selected), a helpfulness thumbs vote, time-per-item measurement, a **hidden control subset** for anchoring analyses, `copilot_*` columns plus acceptance/helpfulness/time metrics in the results export, and a **"with/without co-pilot" filter** for the agreement metrics.
- **Voter provenance in the results export** — `voter_origin`/`voter_source` (referral link vs. existing account) on all human rows.

### 🐛 Fixed
- **Schema patches are boot-race safe** — Containers booting in parallel (flask/worker/supervisor) could crash each other with "duplicate column" on the first start after an update (a TOCTOU between the existence check and the ALTER).
- **Labeling evaluations fully wired up** — Auto-save in the embedded interface, progress counting from `ItemLabelingEvaluation`, display in the Data tab.
- **Labeling task type detection in the analysis tab** for scenarios created through the v1 API (`function_type_name` fallback).

---

## [1.15.0 – 1.15.2] - 2026-06


### ✨ Added
- **Complete, published changelog** — this file is now complete (all releases 1.0.0–1.14.0, newest first, badges plus emoji sections) and linked as a MkDocs page under `/mkdocs/changelog/` (DE/EN).
- **Seventh evaluation type on the landing page** — `communication_comparison` added (types section plus the tech counter "seven evaluation types").

### 🔁 Changed
- **The landing page** links the new IJCAI demo video; the chatbot builder tile got a fitting icon.
- **Chatbot grounding is prompt-driven** — cite only genuinely relevant sources, answer general questions from the model's own knowledge, and admit honestly when there is "no reliable information" about LLARS (calibration showed that bi-encoder relevance does not separate on-topic from off-topic reliably).

### 📚 Docs
- English translations for `nightly-test-activities`, `mail-service`, `human_studies/index` and `playbook`; a detail section for communication comparison (type 8); the MariaDB version corrected to 11.2.6.

---

## [1.14.0] - 2026-06-13


### ✨ Added
- **User provenance in the scenario manager** — Coloured "origin" pills show for each evaluator where they came from (referral link vs. existing user) and how they joined the scenario (owner / auto-enrol / invited by … / themselves). Visible in **Assessors, Settings, Overview and Evaluation**. Every referral link gets an **LLARS-wide consistent colour** (assigned deterministically, overridable in the admin panel) plus a collapsible legend.
- **General LLARS demo** — DE/EN invitation plus welcome mail and demo accounts with a one-week expiry; a nightly `maintenance:demo-cleanup` job clears expired demos.
- **IJCAI welcome mail** made visible in the admin mail centre.

### 🔁 Changed
- **The chatbot answers generic questions without sources** — the answer is decoupled from the obligation to cite: general-knowledge questions are answered freely, relevant LLARS sources are still cited.

### 🔒 Security
- **Pentest hardening (comprehensive)** — the `docker.sock` mount was replaced by a read-only socket proxy (C3); container memory limits against DoS (M3); nginx hardening (CSP `unsafe-eval` removed, real IP, PHP hidden); mkdocs/authentik moved to loopback, hashed reset tokens, npm audit; dual-key secret decryption plus a loopback-only DB port; `test_prompt_stream` gated plus rate limiting on the socket LLM paths; IDOR/SSRF closed, CSV/XSS/crypto/session gaps hardened.

### 🐛 Fixed
- **DOMPurify works again** — the npm-audit-fix lockfile bump was rolled back (it had broken DOMPurify).

---

## [1.13.0] - 2026-06-08


### ✨ Added
- **Comparison analysis: individual vote matrix plus author analysis** — For pairwise scenarios (comparison / communication_comparison) the scenario analysis tab now shows who (which evaluator) chose what (A/B/tie) per comparison, including an author chip (human vs. a specific LLM), voter exclusion (hide test accounts) and Krippendorff's α. The author analysis ranks the systems by win rate (Wilson 95 % CI) plus Bradley-Terry strength and shows head-to-head rates.
- **Mail centre: quick send** — Admins can send a selected mail template straight to an address they type in (Templates tab), gated behind `feature:admin:mail`.

### 🔁 Changed
- **A more compact, modern layout for "individual votes" and "author analysis"** — consistent icon headers with metric chips, cleanly padded card bodies, smaller tags/chips/bars, muted win-rate bars with an accent gradient for the rank-1 entry, and a subtle accent bar for the human reference row.

### 🐛 Fixed
- **Author classification of the comparison options corrected** — the human/LLM hint in the results export (the basis of the author analysis) now follows the canonical `_categorize`: a "human:" prefix and "…/human" tails (e.g. "human:counsellor") are correctly recognised as human; the ineffective glob entries "klient*in"/"berater*in" were replaced by the real forms.
- **Deterministic feature order** — the A/B options in the rater view are now explicitly sorted by `feature_id` (like the export), so that the author attribution of the votes is guaranteed to match what the raters saw.
- **Performance of the vote matrix** — O(1) lookup instead of a per-cell `items.find` (previously O(items² × voters)).

---

## [1.12.0] - 2026-06-08


### ✨ Added
- **Admin mail centre, major expansion** — Template gallery with preview (iframe plus fullscreen), click/open tracking, bundled branded invitations (faf/kiz/org), the workflow "pick a referral link → edit the matching invitation → send", long invitations with a side-by-side live preview, and a clickable log link opening the mail popup.
- **Referral system expanded** — a configurable `signup_mode` (full | email | instant), a per-link default language plus passwordless magic auto-login, the IJCAI demo (multi-scenario enrol plus viewer role), joining for existing accounts through a link plus welcome mail, and code redemption after login with an enrolment confirmation popup.
- **Demographics in the settings** — Users can view and edit their demographics and see the stored email address; consent to storing the email is opt-in/revocable.

### 🔁 Changed
- **Responsive/mobile pass (audit-driven)** across all evaluation interfaces **and** the entire scenario manager — mobile comparison (A/B fullscreen reading mode, thin tappable footers, task popup, fullscreen history), a mobile chat overhaul in the Claude/ChatGPT style, and slim data-tab tables without horizontal swiping.
- **Chat sources only when cited** — the source panel opens on click only; the auth token now travels over the chat socket (fixing streaming instead of the REST fallback); "new chat" works on the empty `/chat` page.
- **Chatbot grounding sharpened** — `standard_admin` only uses the `llars-documentation` collection; the RAG citation prompt was hardened (cite only on genuine relevance, do not invent links).
- **App bar** without the "Platform" suffix, its own evaluations icon, and comparison votes in the detail dialog.

### 🐛 Fixed
- Exports including `communication_comparison` plus IRR metrics; full DE/EN i18n parity for the evaluationAssistant; numerous evaluation, consent and mobile layout fixes (per-scenario task popup, footer/bar polish, panel overlaps).

### 🔒 Security
- Audit findings closed (authz/IDOR plus hardening of the referral signup); the Brevo webhook marked as a token-guarded `@public_endpoint`.

---

## [1.11.0] - 2026-06-03


### ✨ Added
- **privacy-filter as a 4th anonymisation engine** — `openai/privacy-filter` (HF token classification) is selectable alongside offline/llm/hybrid. It maps the 8 native PII labels onto the LLARS taxonomy, merges fragmented BIOES spans and trims whitespace offsets; a new `SECRET` label (always masked). Benchmarked against Flair on the KIZ cluster (`scripts/anonymize/`): for German counselling text Flair remains the better default (LOC/AGE support, higher person recall), privacy-filter is English-centric → opt-in.
- **NER offload into the worker container** (phase 1) — the heavy Flair/privacy-filter inference now runs once and warm in the `llars_worker` container instead of per gevent web worker. The web tier calls it through Redis request/reply (gevent-friendly), with a local fallback when no worker is reachable. This removes the ~35 s cold load per web worker and the RAM multiplication of the 2.2 GB model. (`services/anonymize/ner_remote.py`)

### 🔁 Changed
- **Transactional mails are German-only** — the welcome and password reset mails lost their English second part (the study is German-language). The welcome mail now closes with the study lead signature, the reset mail with "— Das Team des KI-Zentrums Bayern".

---

## [1.10.0] - 2026-06-02


### ✨ Added
- **Self-service password reset** — the complete flow with an optional email, a consent redesign, a branded reset mail and new app icons.
- **Mistral-Medium-3.5-128B** registered, including env-gated default promotion.

### 🔒 Security
- **Password reset, SSRF, RCE, IDOR and rate limit gaps closed.**

### 🐛 Fixed
- `create_user` now sets the password by a known primary key (restoring the correct test sequence).

---

## [1.9.2] - 2026-05-18


### 🐛 Fixed
- **The referral landing scenario now survives logout/login** — the single-scenario auto-redirect used to hang purely on a `count === 1` heuristic. As soon as an admin added the rater to a second scenario (e.g. for testing), the shortcut broke permanently for that user. The backend (`authentik_routes._enrich_token_with_roles`) now returns a new `referral_target_scenario_id` field in the login response whenever the user originally arrived through a referral link with a bound scenario. The router prefers that hint over the count logic. It is cleared on logout so that shared workstations leak nothing to the next user.

---

## [1.9.1] - 2026-05-18


### ✨ Added
- **Vertical resize handle in the stacked layout** — only side-by-side had a drag divider so far. Stacked now gets the same: a 6 px horizontal bar between "history" and the options, dragging shifts the height ratio (20 %/75 % min/max), and the position persists separately from the horizontal variant. `usePanelResize` now supports `axis: 'vertical'`.

### 🔁 Changed
- **The task briefing collapses automatically on the first "next"** — on the transition from item 0 to item 1 the briefing closes once. As soon as the rater has toggled it manually (open or closed), their choice is the source of truth and auto-collapse never fires again.
- **The notes section is even slimmer** — chevron 16→12 px, font 0.78→0.72 rem, top padding removed, textarea 2→1 rows. Collapsed, the section now takes only ~16 px of vertical space.

---

## [1.9.0] - 2026-05-18


### ✨ Added
- **Reward button on the item overview** — a new trophy button on the right of the filter row (`/scenarios/<id>/evaluate`) opens the aggregated preference popup (human vs. trained AI vs. standard AI) on demand rather than only after a milestone. It pulses when a milestone has just been reached.

### 🔁 Changed
- **`communication_comparison` type routing completed** — the backend (`session_service`, `scenario_stats_service`, `results_export_service`, the `comparison/preferences` endpoint) and the frontend (EvaluationItemsOverview gamification gate, EvaluationHub type label, ScenarioWizard variant map, ScenarioDetailsDialog model panel) now accept `function_type_id` in `(4, 8)` everywhere. Previously communication-comparison items passed through as "pending", gamification was off on the overview, and the reward popup showed "not enough data".
- **Locale-driven type labels** — EvaluationHub now renders the type chip via `$t('evaluation.types.<key>')` instead of a hardcoded string. The DE and EN locales gain `communication_comparison` plus the missing `mail_rating` entry.
- **The progress denominator respects the unlock window** — with `progressive_reveal=true` the overview now counts against `unlockedCount` instead of `items.length` (e.g. `0/3` instead of `0/5` with `first_milestone=3`).

### 🐛 Fixed
- **Demo seeder conversations** now end with a client opening; the previous counsellor turn as the second message in the history made the A/B candidates replies to the counsellor rather than to the client.
- **Demo seeder timezone bug** — `datetime.now()` (local time) → `datetime.utcnow()`. Previously freshly seeded scenarios ended up in `status='draft'` and were hidden by the EvaluationHub filter.

### 📚 Docs
- `docs/docs/entwickler/evaluation-datenformate.{md,en.md}` updated: "6 → 7 types" plus a communication comparison row in the overview table.

---

## [1.8.4] - 2026-05-18


### 🐛 Fixed
- **Evaluator shortcut strictly only on `count === 1`** — the previous code also redirected to `/evaluation` as a fallback on `count === 0` (or > 1). As a result `test_evaluator` (a fresh CI fixture with 0 scenarios) also landed on `/evaluation` instead of `/Home`, which meant the tile regression specs could not find their `.feature-card` tiles and ran into a timeout. Now strictly: 1 scenario → auto-redirect, otherwise the default landing. This also matches the original request, "when only one scenario is assigned".

---

## [1.8.3] - 2026-05-18


### 🐛 Fixed
- **The evaluator shortcut hardens itself against race conditions** — the `roles.length > 0` guard is back (v1.8.1 had removed it), so that CI fixtures and fresh referral registrations with a not-yet-hydrated auth bundle do not run into the shortcut path. Plus a 3-second timeout on the `/api/scenarios` lookup in the router guard — if staging gunicorn recycles a worker mid-request or a 502 comes back, the guard falls through transparently to `/evaluation` instead of blocking indefinitely.

---

## [1.8.2] - 2026-05-17


### 🐛 Fixed
- **E2E `authenticate as evaluator` hung after v1.8.1** — the setup fixture waited stubbornly for `/Home`, but the broader role check in v1.8.1 redirects evaluator-only users straight to `/evaluation` or `/scenarios/<id>/evaluate`. `auth.setup.js` now accepts all three landing paths. Power-role fixtures (admin/researcher/chatbot_manager) still land on `/Home`.

---

## [1.8.1] - 2026-05-17


### 🐛 Fixed
- **Evaluator auto-redirect without strict role equality** — quick access used to fire only on `roles.every(r === 'evaluator')`. Now: every authenticated user without a power role (`admin` / `researcher` / `chatbot_manager`) who has exactly one assigned scenario lands directly in its tile view. This also catches fresh registrations through a referral link, where `llars_roles` is initially empty and the JWT `groups` fallback applies.

---

## [1.8.0] - 2026-05-17


### ✨ Added
- **Communication comparison evaluation type** (`function_type_id=8`) — a specialisation of `comparison` for A/B comparisons in a counselling context. The same data structure as comparison; the UI frames the choice as "send response" with a fly-out animation, an optional response prompt and a rater notes textarea. Fully wired: Pydantic schemas, frontend schemas, feature type seeder, demo scenario, preset registry, EvalConfigEnvelope discriminator.
- **Evaluator quick access**: users with the `evaluator` role and exactly one assigned scenario are automatically taken from `/Home`/`/evaluation` straight into that scenario's tile view (skipping the welcome and tool list). Cached per session, falling through transparently to `/evaluation` on 0 or more than 1 scenarios.

### 🔁 Changed
- **Comparison UI wording** adjusted following feedback from the social sciences (2026-05-15): "choose option A" / "choose option B" now in both modes (classic and communication comparison) instead of the mode-dependent "send response A/B" variant.

---

## [1.7.0] - 2026-05-08


### ✨ Added
- **Public v1 chatbot API plus wizard quickbuild** — programmatic chatbot access with scope-gated keys.
- **Comparison: progressive reveal** — cards are unlocked in chunks per milestone.
- **Study gamification made visible** plus auto-login, drawer privacy and a confirmation email.

### 🔒 Security
- **v1 chatbot API hardened** — SSRF and cross-tenant RAG attach blocked; several production blockers and defects from three agent review passes fixed (including an MVCC snapshot and a DNS timeout race).

### 🐛 Fixed
- `axios` raised to `^1.16.0` (release gate vulnerability).

---

## [1.6.0] - 2026-05-07


### ✨ Added
- **Public v1 scenario API** — scope-gated API keys plus security hardening.
- **Public landing page** with scroll reveal, a bento grid and paint strokes, plus an admin-only landing preview tile.
- **Turing test / comparison** — reward system, deterministic import, tie opt-in, layout polish; a pairwise comparison demo for IJCAI reviewers.
- **Referral: auto-enrol on join** plus a dedicated EMNLP study link.

### 🐛 Fixed
- **Krippendorff's alpha corrected** (coincidence matrix plus ordinal metric) along with the IRR calculation and the entire results pipeline; the rater filter is respected in the agreement metrics; the crawler persists crawl sessions across workers; `pygments==2.19.1` pinned (fixing a mkdocs crash).

---

## [1.5.0] - 2026-04-02


### 🔒 Security
- **API keys hashed with argon2id** — plaintext keys are migrated automatically at startup. New keys are only ever stored as a hash. Backward compatible during migration.
- **Docker base images pinned** — all Dockerfiles now use specific versions (python:3.10.20-slim, nginx:1.28.3-alpine, node:23.11.1-slim/alpine, mariadb:11.2.6) instead of floating tags. Supply chain protection.
- **The security scan blocks the pipeline** — `allow_failure: true` removed from `security:scan`. Vulnerabilities must be fixed or explicitly ignored.
- **CVE-2026-22815 (aiohttp)** fixed — upgrade from 3.13.3 to 3.13.4.
- **lodash-es prototype pollution** fixed (GHSA-f23m, GHSA-r5fr).
- **picomatch ReDoS and method injection** fixed (GHSA-3v7f, GHSA-c2c7).
- **Rollback error handling** — no more silent `|| true`; an explicit error message when both rollback mechanisms fail.

### ⚡ Performance
- **Agreement computation 241× faster** — Krippendorff's alpha, Fleiss' kappa and the heatmaps now use NumPy vectorisation instead of Python loops. A ProcessPoolExecutor distributes independent computations across all CPU cores.
- **Gunicorn workers auto-scaled** — `cpu_count + 1` (13 on production) instead of a hardcoded 4. Gevent-optimised.
- **Stats/LLM workers auto-scaled** — `cpu_count // 2` (6 each on production) instead of a hardcoded 2.
- **CI backend tests 3.7× faster** — pytest-xdist distributes 3110 tests across 12 cores (18 min to 5 min).
- **Flask RAM −50 %** — from 11.17 GB to 5.5 GB through the correct worker count for gevent.

### 🐛 Fixed
- **Flaky TestPromptDialog in CI** — timeout raised to 15 s, and a proper Vue unmount in `afterEach` prevents socket listener leaks.
- **Dead code removed** — the old `_stats_cache` functions (replaced by the 2-tier cache service).
- **Healthcheck `start_period`** reduced from 30 min to 2 min.

---

## [1.4.0] - 2026-03-18


### 🔁 Changed
- **Two-axis scenario role model** — refactored to `manager_role` + `evaluation_role` (replacing the simple `role` column).

### ✨ Added
- Improved timeline layout plus sorting of the conference list.

### 🐛 Fixed
- Viewer scenarios appear in "my scenarios"; `from_job` chains are resolved instead of rejected; a session flush in the distribution helpers (preventing SQLite state corruption); non-UTF-8 bytes in the `latexmk` output are caught; several flaky CI tests stabilised.

---

## [1.3.0] - 2026-03-16


### ✨ Added
- **A single source of truth for LLM model colours** (backend plus frontend).
- **Role-aware item distribution**, agreement metric filtering and a diff cache.

### 🔁 Changed
- `black`/`isort` removed from linting (never enforced, 499 files non-compliant).

### 🐛 Fixed
- LLM evaluations are included in provenance and agreement metrics; stats cache invalidation wrapped in `try/except`.

### ⚡ Performance
- CI pipeline accelerated (parallel tests, E2E workers, centralised builds).

---

## [1.2.0] - 2026-03-15


### 🐛 Fixed
- **CRITICAL: the frontend healthcheck used `wget` (not installed in nginx:alpine)** — this caused 9 h 17 min of production downtime after a server reboot. An `unattended-upgrades` kernel update triggered the reboot → the frontend healthcheck failed → nginx blocked. Fix: the healthcheck was switched to `curl`.

### ✨ Added
- **Systemd reboot resilience** — automatic recovery after server reboots via `llars.service` with 5-retry logic and exponential backoff. Blue-green aware: a two-step start (infrastructure via compose, app containers via docker start). A healthcheck timer (3 min) and a cleanup timer (daily at 03:30).
- **A two-axis permission model for scenarios** — replaces the simple `role` column with `access_level` (OWNER/MANAGER/MEMBER) plus capability flags (`is_viewer`, `is_assessor`), enabling fine-grained control.
- **A new Settings tab in the scenario manager** — replaces the settings popup dialog. Contains all scenario settings plus a team overview with tag-based role management.

---

## [1.1.0] - 2026-03-13


Changes since v1.0.0 (2026-03-09).

### 2026-03-13

#### 🐛 Fixed
- **MariaDB updated from 11.2.2 to 11.2.6** — fixes a SEGFAULT crash in the database
- **pypdf updated from 6.7.5 to 6.8.0** — fixes CVE-2026-31826 (security vulnerability)
- **The bucket column widened to VARCHAR(255)** for custom labels in ranking scenarios
- Owners automatically receive VIEWER permission; team visibility in the scenario manager corrected
- Nginx DNS auto-heal after container restarts
- A syntax error in the GenerationJobDetail socket handler fixed
- Numerous E2E test fixes: user search, share dialog, rate limit avoidance, workflow robustness

### 2026-03-12

#### ✨ Added
- **Generation job sharing** — jobs can be shared with other users (read-only)
- E2E tests for the dev branch run automatically with the same suite as main

#### 🐛 Fixed
- Consistent avatars in all user lists (backend plus frontend)
- The missing `ItemComparisonEvaluation` model class added
- E2E workflow tests stabilised with SYSTEM_ADMIN_API_KEY

#### 🔁 Changed
- `build_avatar_url()` is now used everywhere instead of manual URL construction

### 2026-03-11

#### 🐛 Fixed
- E2E tile regression: `requiresAdmin` for the pipeline routes, redirect detection
- E2E fixes for staging 429 rate limits
- Bootstrap variables added for the e2e:dev job

#### ⚡ Performance
- CI pipeline: venv/node_modules caching with file-hash keys introduced

### 2026-03-10

#### ✨ Added
- **Tag-based versioning system** with an `/api/version` endpoint
- **117 new LLM tests** plus smoke tests and an E2E LLM stream test
- An LLM prompt response smoke test and handler integration tests

#### 🐛 Fixed
- **Flask==3.0.3 and Werkzeug==3.0.6 pinned** — fixes the Socket.IO session error (critical)
- **LLM evaluator anti-DDoS**: a lock plus permanent failure detection prevent server overload
- Docker Hub TLS timeouts: `syntax=docker/dockerfile:1` directives removed
- Flask-SocketIO updated to 5.4.1, the encryption key fallback corrected
- NameError crashes in the LLM ranking runner fixed
- Socket.IO xhr-post errors in prompt engineering and chat eliminated
- LLM auto-start and Socket.IO connectivity restored
- Smart CACHE_BUST instead of --no-cache for docker builds (preventing a full disk)

#### 📚 Documentation
- The LLM evaluator anti-DDoS architecture documented; a code documentation policy introduced

### 2026-03-09

#### ✨ Added
- **Markdown scenario briefings** end to end (judge scenarios with markdown descriptions)
- **Admin research groups** redesigned with a new master-detail layout
- **Semantic version management** with branch-aware auto-increment
- The branch and commit hash are shown next to the version in the app bar

#### 🐛 Fixed
- A segfault in the route test teardown fixed
- E2E tile regression failures corrected
- The git version passed as a build arg to the docker frontend builds
- The SQLite connection pool is properly disposed before dropping tables
- A langchain dependency conflict and seeder constraint errors fixed
- The dependency audit pipeline restored

---

## [1.0.0] - 2026-03-09


The first tagged release. Covers the entire development of the project since March 2024.

### 🌟 Highlights

- A complete evaluation framework with 6 assessment types (ranking, rating, mail rating, comparison, authenticity, labeling)
- A multi-dimensional rating system with presets (SummEval, LLM judge standard, etc.)
- LLM-as-judge with automatic evaluation and anti-DDoS protection layers
- Collaborative prompt engineering with YJS WebSocket sync
- A RAG pipeline with ChromaDB, embedding models and reranking
- A scenario wizard with AI-assisted data analysis and type detection
- Blue-green deployment with automatic rollback
- An RBAC permission system with Authentik integration

### March 2026 (before the tag)

#### ✨ Added
- **Deutsche Bahn price agent** — DB price monitoring as a new tool
- **A dev branch CI/CD pipeline** for the llars-dev server with its own blue-green deployment
- Mobile views for the DB agent and LaTeX collaboration
- A conference manager with a PDF viewer
- LaTeX collab PDF downloads

#### 🐛 Fixed
- Blue-green deployment: the switch job, smoke tests against the staging nginx
- Aggressive disk cleanup in CI for `/var` storage problems
- Stabilisation of the nightly tile tests and privacy recovery
- Relative production URLs for the frontend

### February 2026

#### ✨ Added
- **Conference manager** — managing conferences and papers
- **A manager role** for scenarios; evaluator renamed to assessor
- **User LLM providers** — users can create and share their own LLM providers
- **An automated pipeline** feature (admin-only) for automated evaluation pipelines
- **IONOS AI Model Hub** catalogue with cost tracking and token accounting
- **A referral system** with live slug validation and improved UX
- **Provenance analysis** — origin analysis for conversation partners and prompts
- **A demo video framework** for IJCAI 2026 with two-speaker TTS and an overlay system
- openai_compatible and vLLM provider support
- Provider prefix routing for LLM models (Global/{manufacturer}/{model})
- Server-side generation-to-scenario import with format detection
- Per-dimension agreement metrics for rating and mail rating
- Skeleton loading plus fade transitions for the scenario evaluation tab
- Batch generation with grouped, colour-coded output lists
- i18n translations for RAG, DataImporter and the admin sections
- Automatic MkDocs language switching based on the LLARS locale

#### 🐛 Fixed
- N+1 queries in evaluation session loading and scenario stats eliminated
- The legacy `llms` table removed, model_id strings used throughout
- Bucket distribution and provenance made fully dynamic
- Generation stream reconnect and pre-request latency optimised
- An i18n SyntaxError caused by unescaped @ characters in locale messages fixed
- A 502 Bad Gateway after `--update` fixed by an nginx restart

#### 🔒 Security
- SSRF protection and access control enforcement strengthened

### January 2026

#### ✨ Added
- **Gunicorn + gevent** for production WebSocket support (instead of the Flask dev server)
- **User API key management** — users can manage their own API keys
- **An AI writing assistant** for LaTeX collaboration with streaming
- **A floating git panel** / version control panel for prompt engineering
- **MkDocs documentation** as a RAG knowledge base for the chatbot
- **KaiMo case sharing** with per-user ownership and auto-save
- AI analysis for the scenario wizard improved (file format detection)
- An LFloatingWindow component
- The scenario invite flow improved

#### 🐛 Fixed
- Chatbot: PROJECT_URL placeholders replaced in the RAG context and LLM answers
- Socket.IO background thread app context and LLM client initialisation
- The AI comment context raised to 1000 characters, the nginx timeout adjusted

### December 2025

#### ✨ Added
- **A CI/CD pipeline** fully configured with a GitLab shell runner
- **Zotero OAuth integration** for LaTeX collaboration
- **A System Settings** admin section with runtime config
- **An AI writing assistant** for LaTeX collaboration
- Markdown collaboration with YJS sync improved
- A system settings database table for runtime configuration
- Pytest configuration and test structure established
- Comprehensive unit and integration tests (frontend plus backend)

#### 🐛 Fixed
- A ChromaDB `page_content=None` bug (defensive handling)
- PDF.js worker: MIME types, CSP, auto-copy on build
- The frontend healthcheck timeout adjusted to a 60 s `start_period`
- Collection embedding service and seeder improvements

### November 2025

#### 🔁 Changed
- **Large refactoring** (16 major refactorings completed):
  - ChatWithBots.vue (3299 to 774 lines), JudgeSession.vue (2174 to 579)
  - ChatbotEditor.vue (1967 to 507), chat_service.py (1657 to 590)
  - crawler_service.py (1415 to 666), anonymize_service.py (1275 to 445)
  - Composable extraction for all large Vue components
  - Backend routes split into modular files (judge, oncoco, RAG, statistics, sessions)
  - `tables.py` split into modular model files (phase 1)
  - The web crawler split into modular components

### September – October 2024

#### ✨ Added
- Authentik OAuth2 integration with RBAC
- Core ranking and rating functionality
- LLM integration (OpenAI, LiteLLM)
- A chatbot builder with RAG integration
- A web crawler for knowledge bases

### March – August 2024

#### ✨ Added
- **Project start** — Vue 3 + Flask backend initialised
- Basic ranker/rater dashboards
- A drag-and-drop ranking interface
- Email thread management and the basic scenario structure
- MariaDB integration with the first tables
- A docker-compose setup with hot reloading
- Authentik user management basics

---

## Links

- Repository: git.informatik.fh-nuernberg.de/kiz-nlp/llars/llars
- Production: 141.75.150.128
- Dev: 141.75.150.86
