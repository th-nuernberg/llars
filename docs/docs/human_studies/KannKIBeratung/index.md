# Kann KI Beratung? — erste Human Study in LLARS

„Kann KI Beratung?" ist die **erste Human Study, die in LLARS durchgeführt
wurde**. Sie diente zugleich als Vorlage, an der der generische
[Playbook](../playbook.md) entstanden ist. Weitere Studien folgen und werden im
[Human-Studies-Bereich](../index.md) ergänzt — diese Seite dokumentiert die
erste Instanz entlang des Playbooks.

> Tatsachenfeststellung, keine Plattform-Aussage: Wir haben diese Studie
> gefahren; sie war unser erster Durchlauf; der Ablauf ist im Playbook
> verallgemeinert.

## Studie auf einen Blick

| | |
|---|---|
| **Frage (a)** | Standard-KI vs. speziell trainierte KI |
| **Frage (b)** | KI vs. Mensch |
| **Aufgabe** | Pro Fall: bisheriger Beratungsverlauf + zwei mögliche Antworten (A/B) → die Antwort wählen, die man am ehesten verwenden würde (kein Unentschieden). |
| **Typ** | Pairwise Comparison (`communication_comparison`) |
| **Szenario** | **492** auf der Produktion (`https://llars.e-beratungsinstitut.de`) |
| **Rater:innen** | Beratungsfachkräfte der Onlineberatung |
| **Recruiting** | über Partner des Instituts für E-Beratung, **in Zusammenarbeit mit den Sozialwissenschaften** |

## Die drei Antwort-Quellen

Jeder Fall vergleicht zwei Antworten, die aus jeweils einer dieser drei Quellen
stammen (für Rater:innen **nicht** sichtbar — verblindet):

| Quelle | Bedeutung | Rolle im Vergleich |
|--------|-----------|--------------------|
| **Mensch** | Antwort einer professionellen Beratungsfachkraft (Onlineberatung) | Referenz „menschliche Qualität" |
| **Trainierte KI** | speziell auf Beratungsdaten trainiertes/feingetuntes KI-Modell | Kandidat „trainiert" |
| **Standard-KI** | untrainiertes, häufig genutztes Standard-KI-Modell | Kandidat „Basis" |

Im Auswertungs-Popup werden die Achsen u. a. als „Mensch vs. KI" und „trainierte
vs. Standard-KI" aggregiert.

## Unterseiten

| Seite | Inhalt |
|-------|--------|
| [Setup](setup.md) | Szenario 492, Eval-Config, Verblindung, Deploy auf LLARS. |
| [Recruiting](recruiting.md) | Pro-Org Referral-Links, Consent/Anonymität, Einladungsmail. |
| [Annotations-Audit](annotations-audit.md) | Fachliche Anmerkungen aus den Sozialwissenschaften vs. Implementierungsstand in LLARS. |

## Quell-Artefakte (EMNLP2026-Repo)

Die Studienartefakte (Build, Templates, Recruiting-Wortlaut, Runbooks) liegen
im Forschungs-Repo `EMNLP2026`. Diese Doku fasst zusammen und verlinkt, statt
zu duplizieren:

| Artefakt | Pfad (EMNLP2026) |
|----------|------------------|
| Studien-Übersicht | `docs/KANN_KI_BERATUNG_STUDY.md` |
| Studien-Konfig (Aufgabentexte DE/EN, Milestones) | `data/human_study/v15/eval_config.json` |
| Recruiting-Wortlaut + Quellen-Links | `data/human_study/v15/RECRUITMENT_jenny.md` |
| Einladungs-Templates (pro Org) | `data/human_study/v15/invitation_branded/*.html` |
| Deploy-Runbook (Szenario 492) | `docs/HUMAN_STUDY_DEPLOY_RUNBOOK.md` |
| Mail-Runbook (Brevo/SMTP) | `docs/MAIL_RUNBOOK.md` |
