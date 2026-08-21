# Human Studies in LLARS

Dieser Bereich bündelt die in LLARS durchgeführten **Human Studies** (Studien mit
menschlichen Bewerter:innen). LLARS wird hier nicht nur als Tool, sondern als
Plattform für wiederholbare Bewertungsstudien genutzt: Szenario anlegen,
Rater:innen über getrackte Einladungslinks rekrutieren, Bewertungen sammeln,
Feedback geben.

Der Bereich ist **erweiterbar angelegt** — jede Studie bekommt einen eigenen
Unterordner und folgt demselben generischen Ablauf, dem
[Playbook](playbook.md). Aktuell ist eine Studie dokumentiert; weitere kommen
hinzu und werden hier verlinkt.

## Aufbau dieses Bereichs

| Seite | Inhalt |
|-------|--------|
| [Playbook](playbook.md) | **Wiederverwendbarer Prozess** — wie wir eine Human Study in LLARS von Anfang bis Ende aufsetzen und betreiben (studienunabhängig). |
| [Kann KI Beratung?](KannKIBeratung/index.md) | Die **erste** in LLARS gelaufene Human Study, dokumentiert entlang des Playbooks. |
| [IJCAI 2026 Demo](ijcai-demo.md) | Konferenz-**Live-Demo**: ein QR-Code, sieben geteilte Demo-Szenarien (eines pro Evaluationstyp), Seeden & Beitreten. |

## Laufende / abgeschlossene Studien

| Studie | Typ | Status | Doku |
|--------|-----|--------|------|
| **Kann KI Beratung?** | Pairwise Comparison (KI/Mensch-Vergleich von Beratungsantworten) | Live (Produktion, Szenario 492) | [Übersicht](KannKIBeratung/index.md) · [Setup](KannKIBeratung/setup.md) · [Recruiting](KannKIBeratung/recruiting.md) · [Annotations-Audit](KannKIBeratung/annotations-audit.md) |

## Eine neue Studie hinzufügen

1. Neuen Unterordner `human_studies/<StudienName>/` anlegen.
2. Den [Playbook](playbook.md)-Ablauf durchgehen (Szenario, Referral-Links,
   Einladung, Consent/Anonymität, Feedback, Deploy, Tracking).
3. Eine `index.md` als Studien-Übersicht erstellen und — wo sinnvoll —
   `setup.md` / `recruiting.md` ergänzen.
4. Die Studie in der Tabelle oben sowie in der `mkdocs.yml`-Navigation eintragen.

> Die Studie „Kann KI Beratung?" dient als ausgearbeitetes Referenzbeispiel:
> sie zeigt, wie der generische Playbook-Ablauf konkret umgesetzt wurde.
