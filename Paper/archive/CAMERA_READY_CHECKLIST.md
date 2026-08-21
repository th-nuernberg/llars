# LLARS — IJCAI-ECAI 2026 Demo Camera-Ready Checklist

**Conference:** IJCAI-ECAI 2026 (Bremen)
**Track:** Demonstrations
**Camera-Ready Deadline:** **15. Mai 2026, 23:59 AoE (UTC-12)**
**Source:** [Demo Track CFP](https://2026.ijcai.org/ijcai-ecai-2026-call-for-papers-demos/) · [Proceedings Info](https://proceedings.ijcai.org/info)

---

## 0. Stand zum Zeitpunkt der Annahme (30.04.2026)

| Check | Status |
|---|---|
| `\linenumbers` deaktiviert (Zeile 36 auskommentiert) | ✅ |
| Autoren + Affiliations + Emails gesetzt | ✅ |
| Template-Version `IJCAI.2026.0` im `\pdfinfo` | ✅ |
| Seitenanzahl: 4 (3 Inhalt + 1 Referenzen) — Limit 5 (3+2) | ✅ |
| `hidelinks` für Hyperref | ✅ |
| Bibliografie sauber (nur zitierte Refs) | ✅ |

---

## 1. Inhaltliche Änderungen am `.tex`

### 1.1 TODO-Kommentar entfernen (Zeile 80)

```tex
\noindent\textbf{Source code:} \url{github.com/th-nuernberg/llars} % TODO: Set up GitHub Pages demo site before submission
```

- [ ] Repo `github.com/th-nuernberg/llars` öffentlich + lauffähig sicherstellen
- [ ] `% TODO …`-Kommentar entfernen
- [ ] Optional: Demo-Site URL ergänzen (falls GitHub Pages aufgesetzt wird)

### 1.2 Demo-Video URL prüfen (Zeile 296)

Aktuell: `https://youtu.be/FdG1nJ7OqE0`

- [ ] Final-Video unter dieser URL veröffentlicht (nicht nur Privat-Link)
- [ ] Max. **10 Minuten** Laufzeit (Demo-Track-Vorgabe)
- [ ] Inhalt entspricht dem Paper-Stand (Pipeline: Prompt → Batch → Eval)
- [ ] URL klickbar im PDF (Hyperref aktiv)

### 1.3 Optionale Sektionen (auf Referenz-Seiten erlaubt)

- [ ] **Acknowledgements** — Förderer / Mittelgeber eintragen
  ```tex
  \section*{Acknowledgements}
  This work was supported by …
  ```
- [ ] **Contribution Statement** — Aufteilung der 5 Co-Autoren
  ```tex
  \section*{Contribution Statement}
  Steigerwald led the system design and implementation. …
  ```
- [ ] Ethical Statement — **nicht zwingend nötig** (keine User-Studie mit Vulnerable Population, Interviews waren mit Erwachsenen Mitarbeitern)

### 1.4 Final-Proof

- [ ] `figure-comparison.tex/.pdf` im Repo werden nicht eingebunden — checken ob Absicht
- [ ] `--` (en-dash) vs `---` (em-dash) Konsistenz
- [ ] Tippfehler-Pass durch alle Co-Autoren
- [ ] Alle Zitationen erscheinen im Bib + alle Bib-Einträge werden zitiert

---

## 2. Administrative Schritte (CMT / Submission-System)

### 2.1 Vor der Camera-Ready-Submission

- [ ] **ORCID** für alle 5 Autoren eingetragen (Pflicht 2026)
- [ ] **Author-Information-Form** ausgefüllt (Reihenfolge der Autoren kann hier noch geändert werden)
- [ ] **Keine neuen Co-Autoren** hinzufügen — nur die bei Submission Genannten

### 2.2 Camera-Ready-Submission

- [ ] PDF + Source als ZIP hochladen
- [ ] **Copyright-Form** unterschrieben einreichen (IJCAI behält Copyright, Open Access)
- [ ] Track-spezifische Metadaten verifizieren

### 2.3 Konferenz-Logistik

- [ ] **Mindestens ein Autor in Bremen anwesend** zur Präsentation (Pflicht für Demo-Track)
- [ ] Konferenz-Registrierung (Frühbucher-Frist beachten)
- [ ] Präsentations-Slot: 10 Minuten Demo-Talk vor Ort

---

## 3. Demo-Material

### 3.1 Demo-Video

- [ ] Neuaufnahme in **maximaler Qualität** (1080p+, hoher Bitrate)
- [ ] Max. **10 Minuten**
- [ ] YouTube hochladen (öffentlich / unlisted) und Link im Paper aktualisieren
- [ ] Untertitel/Closed Captions falls möglich

### 3.2 Repository

- [ ] `github.com/th-nuernberg/llars` öffentlich
- [ ] README mit Quick-Start
- [ ] Lizenz-File vorhanden
- [ ] Demo-Daten oder Seed-Skript dokumentiert

### 3.3 Live-Demo (Bremen)

- [ ] Lokal lauffähiger Stack zur Konferenz mitnehmen (Docker-Compose)
- [ ] Backup-Plan: Hosted Instance oder Video-Demo falls vor Ort kein Netz

---

## 4. Kritische Punkte vor dem 15. Mai

| Priorität | Aufgabe |
|---|---|
| 🔴 P0 | Camera-Ready PDF einreichen (Deadline 15.05.) |
| 🔴 P0 | Copyright-Form einreichen |
| 🔴 P0 | ORCID für alle Autoren |
| 🔴 P0 | Demo-Video final + öffentlich |
| 🟡 P1 | TODO-Kommentar entfernen |
| 🟡 P1 | Acknowledgements + Contribution Statement |
| 🟢 P2 | GitHub Pages Demo-Site |
| 🟢 P2 | Final-Proof durch Co-Autoren |

---

**Letztes Update:** 2026-05-01
