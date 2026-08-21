# Kann KI Beratung? — Recruiting & Einladungen

Wie Rater:innen rekrutiert und eingeladen wurden. Folgt dem
[Playbook](../playbook.md), Schritte 3–5. Das Recruiting lief über die Partner
des Instituts für E-Beratung, **in Zusammenarbeit mit den Sozialwissenschaften**.

## Pro-Organisation Referral-Links (Quellen-Tracking)

Jede Organisation erhielt einen **eigenen Slug** → jede Registrierung wird der
Quelle zugeordnet, über deren Link sie kam. Alle Links zeigen auf **Szenario
492**; E-Mail optional, anonym, mit Consent.

| Quelle | Slug | Join-Link |
|--------|------|-----------|
| DigiSucht | `kann-ki-beratung-digi-sucht` | `…/join/kann-ki-beratung-digi-sucht` |
| bke | `kann-ki-beratung-bke` | `…/join/kann-ki-beratung-bke` |
| BVkE | `kann-ki-beratung-bvke` | `…/join/kann-ki-beratung-bvke` |
| KI-Zentrum Bayern | `kann-ki-beratung-kiz` | `…/join/kann-ki-beratung-kiz` |
| Institut für E-Beratung | `kann-ki-beratung-ieb` | `…/join/kann-ki-beratung-ieb` |
| (Test) | `kann-ki-beratung-test` / `emnlp-v14-test` | `…/join/kann-ki-beratung-test` |

Basis-URL:
`https://llars.e-beratungsinstitut.de/join/kann-ki-beratung-{digi-sucht,bke,bvke,kiz,ieb,test}`

- Referral-Links werden idempotent per Slug über
  `POST /api/v1/scenarios/492/referral-link` angelegt/aktualisiert
  (`auto_enroll:true`, `role_name:"evaluator"`, `collect_email:false`,
  `collect_display_name:false`).
- Validierung: `GET /api/referral/validate/<slug>`.
- Weiterleiten **innerhalb** derselben Organisation ist ok; org-übergreifendes
  Weiterleiten vermischt die Quelle.

Quelle der Tabelle: Recruiting-Dokumentation im EMNLP2026-Repo (in
Zusammenarbeit mit den Sozialwissenschaften).

## Consent / Anonymität / optionale E-Mail

Der Join-Flow ist auf **anonyme** Teilnahme ausgelegt: Benutzername + Passwort
genügen, die E-Mail ist optional. Bei Studien-Links blendet das Register-
Formular einen **Consent-Block** (Datenschutz-/Studieneinwilligung) ein. Gibt
jemand keine E-Mail an, wird intern eine nicht zustellbare
`…@noemail.invalid`-Adresse gesetzt. Details:
[Playbook §4](../playbook.md#4-consent-anonymitat-optionale-e-mail).

## Einladungsmail

- **Versand:** **manuell** (kein App-Trigger), als gebrandetes HTML über die
  **Brevo-Transaktions-API vom Server** (IPv4). Absender
  `team@llars.e-beratungsinstitut.de`, Reply-To `llars@e-beratungsinstitut.de`,
  Betreff „Kann KI Beratung?".
- **Templates (eine Datei pro Quelle):**
  `data/human_study/v15/invitation_branded/<slug>.html` — identisch bis auf den
  „Jetzt mitmachen"-Link (Org-Slug) → Quellen-Tracking. **Nicht** die generierten
  HTMLs editieren, sondern:
  - **Generator:** `scripts/human_study/build_invitation_mails.py`
    (Text/Layout hier ändern → `python3 scripts/human_study/build_invitation_mails.py`).
  - **Wortlaut-Quelle:** `data/human_study/v15/RECRUITMENT.md`.
  - **Empfänger-Liste:** `data/human_study/v15/recruiting_recipients.csv`
    (echte Adressen = PII → **gitignored**, nicht committen).
- **Harte Versandregeln:** nur vom Server / IPv4, nur von der DKIM-
  authentifizierten Sende-Subdomain, From = reine Sende-Adresse, pro Org der
  richtige Link. Siehe [Mail-Service](../../entwickler/mail-service.md) und
  `docs/MAIL_RUNBOOK.md` (EMNLP2026).

## Begleitende App-Mails

Wer sich über einen Join-Link registriert **und** eine E-Mail angibt, erhält
automatisch die LLARS-**Willkommensmail** (Branding „Kann KI Beratung?");
Passwort-Reset analog. Diese App-Mails laufen über den LLARS-`email_service` →
Brevo-SMTP (siehe [Mail-Service](../../entwickler/mail-service.md)).

## Tracking auswerten

- **Quelle pro Registrierung:** Referral-Slug (`referral_registrations` ×
  `referral_links`).
- **Aktivität:** abgeschlossene Fälle (`item_comparison_evaluations`).
- **Demografie:** optionaler einmaliger Survey beim ersten Login
  (`UserDemographics`).
