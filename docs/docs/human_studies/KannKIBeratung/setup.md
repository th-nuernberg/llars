# Kann KI Beratung? — Setup & Deployment

Wie die Studie als Comparison-Szenario in LLARS aufgesetzt und live gestellt
wurde. Folgt dem [Playbook](../playbook.md), Schritte 1–2 und 7.

## Evaluationstyp & Eval-Config

- **Typ:** `communication_comparison` (paarweiser A/B-Vergleich mit
  Konversations-Kontext). Im API-Serializer erscheint teils
  `evaluation_type:"rating"` — das ist eine Serializer-Eigenheit; mountet wird
  die Comparison-UI.
- **Bewertungsfrage:** „Welche Antwort würden Sie am ehesten verwenden?"
- **Kein Unentschieden:** `allow_tie:false`.
- **Verblindung:** `show_source:false` — die Quelle (Mensch / trainierte KI /
  Standard-KI) ist für Rater:innen nicht sichtbar (Dev-Quellenanzeige nur in
  lokalen Builds).
- **Item-Aufbau:** Konversations-Kontext + zwei Kandidaten-Antworten als
  Features. 100 Paare, mail-first geordnet (erste Items = Mailberatung), ergänzt
  um Chat- und Transkript-/Sprechstunden-Formate.
- **Aufgabentexte:** Startseiten-Briefing (`welcome_markdown`) und Pro-Fall-
  Aufgabe (`task_description_markdown`) zweisprachig (DE/EN). Wortlaut siehe
  [Annotations-Audit](annotations-audit.md).

Quelle der Konfiguration: `data/human_study/v15/eval_config.json` (EMNLP2026).

## Gamification / Auswertungs-Popup

- Nach je 5 abgeschlossenen Fällen erscheint ein **Auswertungs-Popup** mit den
  bisherigen Präferenz-Anteilen (Mensch vs. KI, trainierte vs. Standard-KI) und
  schaltet 5 weitere Fälle frei.
- Config: `gamification_first_milestone:5`, `gamification_recurring_milestone:5`,
  `progressive_reveal:true`.
- LLARS-Implementierung: siehe [Annotations-Audit](annotations-audit.md)
  (Abschnitt „Pro-5-Auswertungs-Popup").

## Deployment auf LLARS

- **Live-Host:** `https://llars.e-beratungsinstitut.de`, API `…/api/v1`
  (System-Admin-API-Key im `X-API-Key`-Header).
- **Szenario-Historie:** 489 → 490 → 491 → **492**. Bei jeder Text-/Konfig-
  Änderung wurde das Szenario **neu angelegt** (die `eval_config` ist nicht
  patchbar); der Referral-Slug zeigt automatisch auf das neue Szenario, sodass
  die Join-URLs stabil bleiben. Re-Deploy-Muster: erst neues Szenario anlegen,
  dann altes löschen.
- **Standard-Join-Flow:** anonym — `collect_email=false`,
  `collect_display_name=false` → Benutzername + Passwort; E-Mail optional;
  Consent beim Join.

Vollständiger Ablauf (Build → Payload → Push → Referral-Links → Verifikation):
`docs/HUMAN_STUDY_DEPLOY_RUNBOOK.md` (EMNLP2026).

## Verifikation

- Szenario abrufen: `GET /api/v1/scenarios/492` (System-Admin-API-Key).
- DB-Erwartung: erste Items = Mailberatung (mail-first-Reihenfolge).
- Referral-Slug prüfen: `GET /api/referral/validate/<slug>`.
