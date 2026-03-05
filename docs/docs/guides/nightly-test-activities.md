# Nightly Test Activities

Diese Seite beschreibt die konkreten Aktivitäten, die im Nightly-Lauf automatisiert geprüft werden.

## Ziel

Vor jedem produktiven Umschalten der Blue-Green-Deploymentfarbe wird geprüft, dass zentrale Nutzerinteraktionen weiterhin funktionieren.

## Kernaktivitäten

| Aktivität | Beschreibung | Ergebnis |
|---|---|---|
| Home Tile Open | Jede sichtbare Kachel pro Rolle wird geöffnet | Navigation, kein Login-Redirect, kein 404 |
| Safe Button Sweep | Nicht-destruktive Buttons auf Zielseite werden geklickt | UI bleibt stabil, keine 5xx |
| Prompt Export/Import/Test | Prompt Engineering Kernaktionen | Download/Import/Test-Aktion vorhanden und klickbar |
| Batch -> Szenario Wizard | Übergang aus Batch Generation | Wizard/Scenario-Handoff erreichbar |
| Scenario Role Assignment | Evaluator/Viewer/Role-Zuweisung | Assignment-Controls sichtbar |
| LaTeX Resizer Drag | Split-Pane-Resize im Workspace | Divider bewegt sich messbar |
| Conference Access Request | Zugangsanfrage zur Forschungsgruppe | Request-UI vorhanden |

## Rollenabdeckung

Reihenfolge im Nightly-Lauf:

1. `test_evaluator`
2. `test_researcher`
3. `test_chatbot_manager`
4. `test_admin`

`ijcai_reviewer` ist explizit aus diesem Nightly-Lauf ausgeschlossen.

## Source of Truth

1. `llars-frontend/src/config/home_tiles.contract.json`
2. `llars-frontend/e2e/nightly/nightly_workflows.contract.json`
3. `docs/testing/nightly/NIGHTLY_TILE_MATRIX.md`

## CI-Gate

`python3 scripts/testing/validate_nightly_coverage.py`

Der Check schlägt fehl, wenn:

1. Home-Routen und Tile-Contract nicht übereinstimmen.
2. Ein Kachelname keinen gleichnamigen Testtitel hat.
3. Ein Workflowname keinen gleichnamigen Testtitel hat.
4. `Home.vue` oder der Tile-Contract geändert wurde, aber Tests/Doku nicht mitgezogen wurden.

## Änderungsvorgehen

Wenn eine Kachel oder Nutzerinteraktion geändert wird:

1. Contract aktualisieren.
2. E2E-Testtitel unverändert am Kachelnamen ausrichten.
3. Activity-Eintrag in der Matrix ergänzen.
4. CI-Check lokal ausführen.
