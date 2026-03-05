# LLARS Nightly Tile Matrix

**Version:** 1.0  
**Stand:** 5. März 2026

Diese Datei ist die operative Referenz für die Nightly-Kacheltests.

## Pflichtregeln

1. Jede Home-Kachel muss in `llars-frontend/src/config/home_tiles.contract.json` definiert sein.
2. Für jede Kachel muss ein gleichnamiger Playwright-Test existieren in `llars-frontend/e2e/nightly/tile-regression.spec.js`.
3. Workflow-übergreifende Tests müssen in `llars-frontend/e2e/nightly/workflows.spec.js` stehen und mit `llars-frontend/e2e/nightly/nightly_workflows.contract.json` synchron sein.
4. Wenn `Home.vue` oder `home_tiles.contract.json` geändert wird, müssen Tests und Doku mitgeändert werden, sonst schlägt CI fehl (`scripts/testing/validate_nightly_coverage.py`).

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
| Szenario Wizard | Übergang aus Batch Generation Richtung Szenariofluss | Ja |
| Prompt Engineering Collaboration | Prompt-Testen, Import/Export, Sharing-Sichtbarkeit | Ja |
| Latex Collab Resizer | Drag-Resize der Pane-Aufteilung | Ja |
| Scenario Manager Role Assignment | Rollen-/Einladungslogik in Szenarien | Ja |
| Conference Manager Access Request | Access-Request-Fluss für Forschungsgruppen | Nein |

## Activity-Katalog (Auszug)

| Activity ID | Aktion | Erwartung |
|---|---|---|
| PE-EXPORT-001 | Export-Button im Prompt Engineering klicken | Datei wird zum Download angeboten |
| PE-TEST-001 | Test-Button im Prompt Engineering klicken | Antwort/Resultat wird angezeigt |
| BG-WIZ-001 | Szenario-Wizard aus Batch-Kontext aufrufen | Wizard-Flow ist erreichbar |
| SCN-ASSIGN-001 | Evaluator/Viewer zu Szenario hinzufügen | Zuweisung wird angezeigt |
| LTX-RESIZE-001 | Divider im LaTeX-Workspace ziehen | Pane-Verhältnis ändert sich |
| CONF-REQ-001 | Zugang zu Forschungsgruppe anfragen | Request-UI ist verfügbar |

## Änderungsvorgehen bei neuer/angepasster Kachel

1. Kachel in `Home.vue` ändern.
2. `home_tiles.contract.json` synchron ändern.
3. Passenden gleichnamigen Test in `tile-regression.spec.js` ergänzen/anpassen.
4. Falls Cross-Feature-Betroffenheit vorliegt, `nightly_workflows.contract.json` und `workflows.spec.js` ergänzen.
5. Diese Datei (`NIGHTLY_TILE_MATRIX.md`) aktualisieren.
6. `CLAUDE.md` und ggf. `docs/testing/CICD_SETUP.md` aktualisieren.
7. Lokal prüfen: `python3 scripts/testing/validate_nightly_coverage.py`.
