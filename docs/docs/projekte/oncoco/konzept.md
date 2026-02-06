# OnCoCo-Analyse für KIA-Daten: Implementierung & Konzept

**Version:** 2.0
**Stand:** 2026-02-05
**Autor:** LLARS Development Team

---

## 1. Zusammenfassung

OnCoCo ist in LLARS **vollständig implementiert**. Das System analysiert KIA‑E‑Mail‑Beratungen
satzbasiert und liefert Live‑Fortschritt, Label‑Verteilungen, Transition‑Heatmaps sowie
statistische Säulenvergleiche. Die Analyse läuft im Backend mit Socket.IO‑Updates und ist
im UI über die OnCoCo‑Pages verfügbar.

---

## 2. Modell & Labels

### 2.1 Modell‑Spezifikation

| Eigenschaft | Wert |
|-------------|------|
| **Basis‑Modell** | XLM‑RoBERTa Large (OnCoCo DE/EN) |
| **Kategorien** | 68 (40 Berater, 28 Klient) |
| **Sprachen** | Deutsch & Englisch |
| **Performance** | ~80% Accuracy, F1 Macro ~0.78 |
| **Pfad** | `ONCOCO_MODEL_PATH` (Env, siehe Backend) |

**Backend‑Pfad/Config:** `app/services/oncoco/oncoco_service.py`

### 2.2 Label‑Hierarchie

Die Labels sind hierarchisch aufgebaut (Role → Level‑1 → Level‑2 → …). Die **vollständige
Label‑Definition** liegt in `app/services/oncoco/oncoco_labels.py`.

Beispiel‑Pfad:
```
CO-IF-AC-RF-RLS-SR
```

---

## 3. Datenquellen: KIA‑Säulen

Daten werden über den KIA GitLab Sync geladen (`KIASyncService`).

| Säule | Name | GitLab‑Pfad |
|-------|------|-------------|
| 1 | Rollenspiele | `data/saeule_1/common/json` |
| 2 | Feature aus Säule 1 | `data/saeule_2/common/json` |
| 3 | Anonymisierte Daten | `data/saeule_3/common/json` |
| 4 | Synthetisch generiert | `data/saeule_4/common/json` |
| 5 | Live‑Testungen | `data/saeule_5/common/json` |

**Repository:** `git.informatik.fh-nuernberg.de/e-beratung/kia/kia-data`

---

## 4. Workflow (aktuelle Implementierung)

```
KIA GitLab Sync → OnCoCo Analyse (Satz‑Level) → Ergebnisse & Visualisierung
```

1. **Sync:** Pillar‑Daten werden aus GitLab geladen (`/api/oncoco/pillars/sync`).
2. **Analyse:** OnCoCo klassifiziert jede Nachricht satzweise.
3. **Progress:** Live‑Updates via Socket.IO (`oncoco:progress`).
4. **Ergebnisse:** Verteilungen, Transitionen und Metriken im UI.

**Resume:** Analysen können bei „stuck“ Zustand mit `force=true` neu gestartet werden.

---

## 5. Analyse‑Logik (Backend)

- **Satz‑Segmentierung:** NLTK `punkt` (Fallback: Regex Split)
- **Role‑Detection:** sender/role Feld + Heuristik (Berater/Klient)
- **Label‑Masking:** Modell gibt nur CO‑Labels für Counselor, CL‑Labels für Client aus
- **Top‑3 Scores:** werden pro Satz gespeichert (für Detailansichten)

**Service:** `app/services/oncoco/oncoco_service.py`

---

## 6. Ergebnisse & Metriken

### 6.1 Pro Säule

- `total_threads`, `total_messages`, `total_sentences`
- `counselor_sentences`, `client_sentences`
- `impact_factor_ratio`
- `resource_activation_score`
- `mi_score`
- `avg_confidence`

### 6.2 Transition‑Matrizen

- **Level:** `full` (Level‑0) oder `level2` (aggregiert)
- **Ausgabe:** Matrix oder Listen‑Format (für Sankey‑Konzept)

### 6.3 Säulen‑Vergleich (Matrix Comparison)

Endpunkt: `/api/oncoco/analyses/{id}/matrix-comparison`

Metriken:
- Frobenius Distance
- Jensen‑Shannon Divergence
- Chi‑Square Test
- Permutation Test
- Effect Size

---

## 7. UI‑Oberfläche

### 7.1 Überblick (`/oncoco`)

- Analysen‑Tabelle mit Status/Progress
- KIA Sync Panel (Pillar‑Status + Sync)
- Modell‑Info & Label‑Statistik

### 7.2 Konfiguration (`/oncoco/config`)

- Analyse‑Name
- Säulen‑Auswahl
- Advanced: `use_level2`, `batch_size`
- „Create“ oder „Create & Start“

### 7.3 Ergebnisse (`/oncoco/results/:id`)

Tabs:
- **Overview:** Metriken pro Säule
- **Distribution:** Label‑Verteilungen (Filter nach Säule/Level/Rolle)
- **Transitions:** Heatmaps + Top‑Transitions + Matrix‑Comparison
- **Sentences:** Satzliste mit Filtern

Live‑Panel zeigt Hardware‑Infos, Performance, ETA und letzte Klassifikation.

### 7.4 Info (`/oncoco/info`)

- Label‑System, Beispiele, Ressourcen und Modell‑Details

---

## 8. API‑Endpoints (aktuell)

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| GET | `/api/oncoco/info` | Modell‑ und Label‑Info |
| GET | `/api/oncoco/labels` | Labels + Hierarchie |
| GET | `/api/oncoco/pillars` | Pillar‑Status |
| POST | `/api/oncoco/pillars/sync` | KIA‑Sync |
| GET | `/api/oncoco/analyses` | Analysen‑Liste |
| POST | `/api/oncoco/analyses` | Analyse erstellen |
| GET | `/api/oncoco/analyses/{id}` | Analyse‑Details |
| POST | `/api/oncoco/analyses/{id}/start` | Analyse starten/resume (`force=true`) |
| DELETE | `/api/oncoco/analyses/{id}` | Analyse löschen |
| GET | `/api/oncoco/analyses/{id}/sentences` | Satz‑Labels |
| GET | `/api/oncoco/analyses/{id}/distribution` | Label‑Verteilung |
| GET | `/api/oncoco/analyses/{id}/transition-matrix` | Transitionen (Matrix/List) |
| GET | `/api/oncoco/analyses/{id}/comparison` | Säulen‑Vergleich |
| GET | `/api/oncoco/analyses/{id}/matrix-comparison` | Statistische Matrix‑Metriken |

---

## 9. Berechtigungen

Die OnCoCo‑Routen sind über **`feature:comparison:view|edit`** geschützt.

---

## 10. Geplante Erweiterungen

- Sankey‑Visualisierung (Endpoint liefert bereits Listen‑Format)
- Export/Reporting (CSV/JSON)
- Zusätzliche UI‑Filter und Benchmarks
