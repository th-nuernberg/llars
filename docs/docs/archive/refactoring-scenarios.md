# Code-Refactoring – ScenarioRoutes.py

**Datum:** 20.11.2025  
**Autor:** Claude Code (Automated Refactoring)  
**Commit:** `b4bd184`

---

## Zusammenfassung

Das monolithische `ScenarioRoutes.py` (729 Zeilen, 11 Routen) wurde in ein Paket mit vier klar getrennten Modulen umgebaut. Alle Endpunkte, Auth-Decorators und Datenbankzugriffe bleiben unverändert, die Wartbarkeit steigt deutlich.

---

## Neue Struktur

| Modul | Zweck | Wichtige Routen |
|-------|-------|-----------------|
| `scenario_crud.py` | Szenario-CRUD (Listen, Details, Anlegen, Bearbeiten, Löschen) | `/admin/scenarios`, `/admin/create_scenario`, `/admin/delete_scenario/<id>` |
| `scenario_management.py` | Thread-/Viewer-Verteilung (Round-Robin) | `/admin/add_threads_to_scenario`, `/admin/add_viewers_to_scenario` |
| `scenario_resources.py` | Referenzdaten für das UI | `/admin/get_function_types`, `/admin/get_users`, `/admin/get_threads_from_function_type/<id>` |
| `scenario_stats.py` | Fortschritts- und Statusberechnung | `/admin/scenario_progress_stats/<id>` |

`__init__.py` registriert die Module im Paket.

---

## Qualitätsgewinne

- **Single Responsibility:** CRUD, Management, Ressourcen und Stats sind getrennt.
- **Wartbarkeit:** Kleinere Dateien, klare Grenzen, leichteres Debugging.
- **Testbarkeit:** Module können separat geprüft werden (Syntax-Checks bestanden).
- **Dokumentation:** Modul- und Routen-Docstrings hinzugefügt.

---

## Änderungen im Repository

```diff
D  app/routes/ScenarioRoutes.py      # monolithisch (Backup separat)
A  app/routes/scenarios/__init__.py
A  app/routes/scenarios/scenario_crud.py
A  app/routes/scenarios/scenario_management.py
A  app/routes/scenarios/scenario_resources.py
A  app/routes/scenarios/scenario_stats.py
M  app/routes/__init__.py            # neue Imports
```

---

## Kompatibilität & Sicherheit

- Alle 11 Routen behalten URL, Methoden, Decorators (`@admin_required`) und Responses.
- Authentik-Auth (mit optionaler Legacy-Kompatibilität) unverändert, User-Kontext (`g.keycloak_user`) bleibt bestehen.
- Keine DB-Migration nötig, Query- und Transaktionslogik unverändert.

---

## Empfehlungen

- Ähnliche Aufteilung für weitere große Dateien (z. B. `routes_socketio.py`, `MailRatingRoutes.py`, `routes.py`, `UserPromptRoutes.py`).
- Unit-Tests je Modul ergänzen, um die Trennung langfristig abzusichern.
