# LLARS Smoke Test Checkliste

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Zweck

Diese Checkliste dient zur schnellen Überprüfung der Kernfunktionalitäten nach einem Deployment oder größeren Änderungen.

**Geschätzte Dauer:** 15-20 Minuten

---

## Voraussetzungen

- [ ] LLARS läuft (`docker compose up -d` erfolgreich)
- [ ] Alle Container healthy (`docker ps`)
- [ ] Test-User vorhanden (admin, researcher, viewer, chatbot_manager)

---

## 1. Authentifizierung (2 min)

### Login

- [ ] `/login` Seite lädt
- [ ] Login mit `admin` / `admin123` funktioniert
- [ ] Redirect zu `/Home` nach Login
- [ ] Token im localStorage vorhanden

### Logout

- [ ] User-Menu öffnet sich
- [ ] Logout-Button klickbar
- [ ] Redirect zu `/login` nach Logout
- [ ] Token gelöscht

---

## 2. Navigation & Home (3 min)

### Home Dashboard

- [ ] `/Home` lädt
- [ ] Kategorien-Sidebar sichtbar
- [ ] Feature-Kacheln sichtbar
- [ ] Alle Kacheln klickbar (als admin)

### Kachel-Navigation

- [ ] Ranking-Kachel → `/Ranker`
- [ ] Rating-Kachel → `/Rater`
- [ ] Chat-Kachel → `/chat`
- [ ] Admin-Kachel → `/admin`
- [ ] Markdown Collab → `/MarkdownCollab`
- [ ] LaTeX Collab → `/LatexCollab`

---

## 3. LLM Integration (3 min)

### Chat funktioniert

- [ ] `/chat` öffnen
- [ ] Chatbot auswählen
- [ ] Nachricht senden: "Hallo, antworte mit einem Satz."
- [ ] Bot antwortet (innerhalb 30s)
- [ ] Streaming funktioniert (Text erscheint Stück für Stück)

### LLM Models verfügbar

- [ ] Admin → Chatbot erstellen → LLM-Dropdown hat Modelle
- [ ] Mindestens ein Modell auswählbar

---

## 4. RAG Pipeline (3 min)

### Dokument-Upload

- [ ] Admin → RAG Tab öffnen
- [ ] Collection erstellen
- [ ] Dokument hochladen (z.B. test.txt)
- [ ] Upload erfolgreich

### Embedding

- [ ] Embedding startet automatisch oder manuell
- [ ] Fortschritt sichtbar
- [ ] Status wechselt zu "completed" (kann einige Minuten dauern)

### Suche

- [ ] Im Chat fragen: "Was steht in den Dokumenten?"
- [ ] Sources-Panel zeigt Chunks

---

## 5. Kollaborative Editoren (3 min)

### Markdown Collab

- [ ] `/MarkdownCollab` öffnen
- [ ] Workspace erstellen oder öffnen
- [ ] Text eingeben
- [ ] Preview aktualisiert sich

### LaTeX Collab

- [ ] `/LatexCollab` öffnen
- [ ] Workspace erstellen oder öffnen
- [ ] LaTeX eingeben: `\section{Test}`
- [ ] "Kompilieren" klicken
- [ ] PDF wird generiert (kann 30-60s dauern)

### Collab-Farbe

- [ ] User-Menu → Einstellungen
- [ ] Farbe ändern
- [ ] Speichern erfolgreich

---

## 6. Admin-Bereich (3 min)

### Dashboard

- [ ] `/admin` öffnen
- [ ] Alle Tabs sichtbar (als admin)

### Docker Monitor

- [ ] Docker Tab öffnen
- [ ] Container-Liste sichtbar
- [ ] CPU/Memory Charts laden

### DB Explorer

- [ ] DB Tab öffnen
- [ ] Tabellen-Liste sichtbar
- [ ] Tabelle auswählen → Daten laden

### User Management

- [ ] Users Tab öffnen
- [ ] User-Liste sichtbar
- [ ] User-Details klickbar

### Szenarien

- [ ] Scenarios Tab öffnen
- [ ] Szenarien-Liste (oder leer wenn keine)

---

## 7. Berechtigungen (2 min)

### Researcher Test

- [ ] Logout als admin
- [ ] Login als `researcher` / `admin123`
- [ ] Judge-Kachel NICHT sichtbar
- [ ] OnCoCo-Kachel NICHT sichtbar
- [ ] Admin-Kachel NICHT sichtbar
- [ ] `/admin` → Redirect oder 403

### Viewer Test

- [ ] Logout als researcher
- [ ] Login als `viewer` / `admin123`
- [ ] Ranking-Kachel sichtbar
- [ ] Keine Edit-Buttons (nur lesen)
- [ ] `/admin` → Redirect oder 403

---

## 8. Anonymisierung (1 min)

- [ ] `/Anonymize` öffnen
- [ ] Beispieltext laden oder eingeben
- [ ] "Pseudonymisieren" klicken
- [ ] Personennamen werden ersetzt

---

## Ergebnis

| Bereich | Status |
|---------|--------|
| Authentifizierung | ⬜ OK / ⬜ FAIL |
| Navigation | ⬜ OK / ⬜ FAIL |
| LLM Integration | ⬜ OK / ⬜ FAIL |
| RAG Pipeline | ⬜ OK / ⬜ FAIL |
| Collab Editoren | ⬜ OK / ⬜ FAIL |
| Admin-Bereich | ⬜ OK / ⬜ FAIL |
| Berechtigungen | ⬜ OK / ⬜ FAIL |
| Anonymisierung | ⬜ OK / ⬜ FAIL |

**Gesamtergebnis:** ⬜ PASSED / ⬜ FAILED

---

## Bei Fehlern

1. Container-Logs prüfen: `docker logs llars_flask_service`
2. Browser-Console prüfen (F12)
3. Netzwerk-Tab prüfen (API-Fehler)
4. Issue dokumentieren mit:
   - Betroffener Bereich
   - Erwartetes vs. tatsächliches Verhalten
   - Screenshots/Logs

---

## Notizen

| Datum | Tester | Ergebnis | Notizen |
|-------|--------|----------|---------|
| | | | |

---

**Letzte Aktualisierung:** 30. Dezember 2025
