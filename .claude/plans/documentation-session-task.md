# Dokumentations-Update Session

## Aufgabe

Aktualisiere die LLARS MkDocs-Dokumentation gemäß Master-Plan.

## Referenzen

- **Master-Plan:** `.claude/plans/documentation-master-plan.md`
- **MkDocs Config:** `docs/mkdocs.yml`
- **Aktuelle Docs:** `docs/docs/`

## Session-Ziele

### Phase 1: Aufräumen
- [ ] `docs/concepts/` → `docs/docs/archive/legacy-concepts/` verschieben
- [ ] `docs/konzepte/` → archivieren
- [ ] mkdocs.yml bereinigen

### Phase 2: Fehlende Guides erstellen (Priorität)

| Guide | Code-Referenz | Ziel-Pfad |
|-------|---------------|-----------|
| Prompt Engineering | `llars-frontend/src/views/PromptEngineering/` | `docs/docs/guides/prompt-engineering.md` |
| Batch Generation | `app/services/batch_generation/` | `docs/docs/guides/batch-generation.md` |
| Chatbot Wizard | `llars-frontend/src/components/Chatbot/ChatbotWizard.vue` | `docs/docs/guides/chatbot-wizard.md` |
| LaTeX Collab | `llars-frontend/src/views/LatexCollab/` | `docs/docs/guides/latex-collaboration.md` |
| Admin Dashboard | `llars-frontend/src/views/Admin/` | `docs/docs/guides/admin-dashboard.md` |

## Dokument-Schema (einheitlich)

```markdown
# Feature-Name

**Version:** X.Y | **Stand:** Monat Jahr

Kurze Einführung (2-3 Sätze).

---

## Übersicht

[ASCII-Diagramm]

---

## Funktionen

### Funktion A
...

---

## Siehe auch

- [Link 1](path.md)
- [Link 2](path.md)
```

## Vorgehen

1. Code-Komponente lesen (Frontend/Backend)
2. Funktionen verstehen
3. Guide nach Schema erstellen
4. In mkdocs.yml eintragen
5. Nächstes Feature

## Start-Befehl

```
Lies den Master-Plan und starte mit Phase 1 (Aufräumen), dann Phase 2 (Prompt Engineering Guide).
```
