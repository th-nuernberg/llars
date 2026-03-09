# LLARS Nightly Tile Matrix

**Version:** 1.0  
**Stand:** 5. März 2026

Diese Datei ist die operative Referenz für die Nightly-Kacheltests.

## Pflichtregeln

1. Jede Home-Kachel muss in `llars-frontend/src/config/home_tiles.contract.json` definiert sein.
2. Für jede Kachel muss ein gleichnamiger Playwright-Test existieren in `llars-frontend/e2e/nightly/tile-regression.spec.js`.
3. Workflow-übergreifende Tests müssen in `llars-frontend/e2e/nightly/workflows.spec.js` stehen und mit `llars-frontend/e2e/nightly/nightly_workflows.contract.json` synchron sein.
4. Deep-Interaktionsaktivitäten müssen in `llars-frontend/e2e/nightly/nightly_activities.contract.json` gepflegt sein und als `[ACT:<ID>]` in den Nightly-Tests auftauchen.
5. Wenn `Home.vue` oder `home_tiles.contract.json` geändert wird, müssen Tests und Doku mitgeändert werden, sonst schlägt CI fehl (`scripts/testing/validate_nightly_coverage.py`).

## Rollenreihenfolge Nightly

`test_evaluator` -> `test_researcher` -> `test_chatbot_manager` -> `test_admin`

## Kachel-zu-Test-Matrix

| Kachelname (Testtitel) | Route | Rollen | Testtyp |
|---|---|---|---|
| Prompt Engineering | `/PromptEngineering` | evaluator, researcher, chatbot_manager, admin | Tile Regression + Workflow |
| Batch Generation | `/generation` | evaluator, researcher, chatbot_manager, admin | Tile Regression + Workflow |
| Evaluation | `/evaluation` | evaluator, researcher, admin | Tile Regression |
| Scenario Manager | `/scenarios` | evaluator, researcher, admin | Tile Regression + Workflow |
| Chatbot | `/chat` | evaluator, researcher, chatbot_manager, admin | Tile Regression |
| Video | `/video` | evaluator, researcher, admin | Tile Regression |
| Markdown Collab | `/MarkdownCollab` | evaluator, researcher, chatbot_manager, admin | Tile Regression |
| Latex Collab | `/LatexCollab` | evaluator, researcher, chatbot_manager, admin | Tile Regression + Workflow |
| Chatbot Arena | `/judge` | admin | Tile Regression |
| Anonymization | `/Anonymize` | evaluator, researcher, admin | Tile Regression |
| Anonymisierungs-Pipeline | `/anonymization` | researcher, admin | Tile Regression |
| KAIMO | `/kaimo` | evaluator, researcher, admin | Tile Regression |
| OnCoCo | `/oncoco` | admin | Tile Regression |
| Admin Dashboard | `/admin?tab=overview` | admin | Tile Regression |
| Chatbot Admin | `/chatbot-manager` | chatbot_manager, admin | Tile Regression |
| RAG Admin | `/chatbot-manager?tab=rag` | chatbot_manager, admin | Tile Regression |
| Conference Manager | `/conferences` | evaluator, researcher, admin | Tile Regression + Workflow |
| Pipeline | `/pipeline` | admin | Tile Regression |
| User Settings | `/settings` | evaluator, researcher, chatbot_manager, admin | Tile Regression |

## Workflow-Matrix

| Workflow-Testtitel | Zweck | Kritisch |
|---|---|---|
| Szenario Wizard | Uebergang aus Batch Generation Richtung Szenariofluss | Ja |
| Prompt Engineering Collaboration | Prompt-Testen, Import/Export, Sharing + Cross-User-Sichtbarkeit | Ja |
| Latex Collab Resizer | Drag-Resize der Pane-Aufteilung | Ja |
| Scenario Manager Role Assignment | Rollen-/Einladungslogik inkl. Evaluator-Annahme und Evaluation-Sprung | Ja |
| Conference Manager Access Request | Access-Request senden, sichtbar machen, genehmigen, Mitgliedschaft pruefen | Nein |
| Conference Manager Tab Navigation | Alle 5 Tabs durchklicken (Conferences, Papers, Calendar, Timeline, Kanban) | Ja |
| User Settings Navigation | Settings-Sidebar-Tabs durchklicken + Theme-Toggle | Ja |
| Anonymization Pipeline View | Pipeline-Manager oeffnen + View-Toggle (Cards/List) | Nein |
| Chatbot Manager Access | chatbot_manager-Rolle oeffnet dedizierte Seite + Tab-Navigation | Ja |
| Markdown Collab Navigation | Home oeffnen + Workspace oeffnen falls vorhanden | Nein |
| Infrastructure Health | MkDocs + Matomo erreichbar, MkDocs-Suche funktioniert | Ja |

## Cross-Tile Interaktionen (Nightly)

| Interaktion | Rollen | Nightly Workflow |
|---|---|---|
| Prompt teilen -> anderer User sieht Prompt | `test_researcher` -> `test_evaluator` | Prompt Engineering Collaboration |
| Szenario einladen -> Einladung annehmen -> Evaluation oeffnen | `test_admin` -> `test_evaluator` | Scenario Manager Role Assignment |
| Forschungsgruppe anfragen -> Request sichten -> genehmigen -> Mitglied pruefen | `test_researcher` -> `test_admin` | Conference Manager Access Request |
| Batch Generation -> Szenario Wizard Handoff | `test_researcher` | Szenario Wizard |
| Conference Manager alle Tabs navigieren | `test_researcher` | Conference Manager Tab Navigation |
| User Settings Sidebar-Tabs + Theme | `test_researcher` | User Settings Navigation |
| Anonymisierungs-Pipeline View-Toggle | `test_researcher` | Anonymization Pipeline View |
| Chatbot-Manager Tab-Navigation | `test_chatbot_manager` | Chatbot Manager Access |
| Markdown Collab Workspace oeffnen | `test_researcher` | Markdown Collab Navigation |

## Activity-Katalog (Pflicht-IDs)

| Activity ID | Aktion | Erwartung |
|---|---|---|
| PE-CREATE-001 | Prompt anlegen | Prompt erscheint und Detailseite ist erreichbar |
| PE-BLOCK-001 | Block anlegen + Text schreiben | Block sichtbar und Inhalt gespeichert |
| PE-EXPORT-001 | Export-Button im Prompt Engineering klicken | Datei wird zum Download angeboten |
| PE-TEST-001 | Test-Button im Prompt Engineering klicken | Antwort/Resultat wird angezeigt |
| PE-IMPORT-001 | Import aus JSON | Importierter Block ist sichtbar |
| PE-SHARE-001 / PE-SHARED-VISIBLE-001 / PE-UNSHARE-001 | User hinzufuegen / als anderer User sehen / entfernen | Share-Liste und Cross-User-Sichtbarkeit funktionieren |
| BG-WIZ-ENTRY-001 | Batch-Wizard oeffnen | Wizard-UI ist stabil erreichbar |
| BG-WIZ-HANDOFF-001 | Uebergang Richtung Szenario Wizard | Handoff-Aktion/Detailflow ist erreichbar |
| SCN-ASSIGN-INVITE-001 | Evaluator/Viewer zu Szenario hinzufuegen | Zuweisung wird angezeigt |
| SCN-ASSIGN-ROLE-001 | Rolle aendern | Rollenwechsel wird uebernommen |
| SCN-ASSIGN-VISIBLE-001 | Einladung als Evaluator sehen und annehmen | Invite-Card sichtbar und annehmbar |
| SCN-ASSIGN-EVAL-001 | Als Evaluator in Evaluation springen | Evaluation-relevante Route erreichbar |
| LTX-RESIZE-001 | Divider im LaTeX-Workspace ziehen | Pane-Verhaeltnis aendert sich |
| CONF-REQ-SUBMIT-001 | Zugang zu Forschungsgruppe anfragen | Anfrage wird als gesendet angezeigt |
| CONF-REQ-VISIBLE-001 | Anfrage bei Gruppenmitglied pruefen | Anfrage ist in Members sichtbar |
| CONF-REQ-APPROVE-001 | Anfrage genehmigen | Pending-Anfrage verschwindet |
| CONF-REQ-MEMBER-001 | Antragsteller als Mitglied pruefen | User ist in Mitgliederliste sichtbar |
| CONF-TABS-001 | Conference Manager Tabs navigieren | Alle 5 Tabs zeigen Content |
| SETTINGS-NAV-001 | Settings-Seite oeffnen | Sidebar sichtbar |
| SETTINGS-TABS-001 | Settings-Tabs durchklicken | Jeder Tab zeigt Content |
| SETTINGS-THEME-001 | Theme-Toggle pruefen | Toggle vorhanden und klickbar |
| ANON-VIEW-001 | Pipeline-Manager oeffnen | Seite laedt ohne Fehler |
| ANON-TOGGLE-001 | View-Toggle umschalten | Darstellung wechselt |
| CBM-ACCESS-001 | Chatbot-Manager Seite oeffnen | Seite sichtbar |
| CBM-TABS-001 | Chatbot-Manager Tabs durchklicken | Tab-Inhalte sichtbar |
| MD-NAV-001 | Markdown Collab Home oeffnen | Workspace-Liste oder Empty-State |
| MD-WORKSPACE-001 | Workspace oeffnen | Editor-Bereich sichtbar |
| INFRA-MKDOCS-001 | MkDocs Dokumentation oeffnen | HTTP 200, Content sichtbar |
| INFRA-MATOMO-001 | Matomo Analytics oeffnen | HTTP < 500, Login oder Dashboard |
| INFRA-MKDOCS-SEARCH-001 | MkDocs Suche testen | Suchergebnisse bei Eingabe |

## Änderungsvorgehen bei neuer/angepasster Kachel

1. Kachel in `Home.vue` ändern.
2. `home_tiles.contract.json` synchron ändern.
3. Passenden gleichnamigen Test in `tile-regression.spec.js` ergänzen/anpassen.
4. Falls Cross-Feature-Betroffenheit vorliegt, `nightly_workflows.contract.json` und `workflows.spec.js` ergänzen.
5. Diese Datei (`NIGHTLY_TILE_MATRIX.md`) aktualisieren.
6. `CLAUDE.md` und ggf. `docs/testing/CICD_SETUP.md` aktualisieren.
7. Lokal prüfen: `python3 scripts/testing/validate_nightly_coverage.py`.
