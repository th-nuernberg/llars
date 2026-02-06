# OnCoCo Analysis for KIA Data: Implementation & Concept

**Version:** 2.0
**Date:** 2026-02-05
**Author:** LLARS Development Team

---

## 1. Summary

OnCoCo is **fully implemented** in LLARS. The system analyzes KIA email counseling data at sentence level
and provides live progress, label distributions, transition heatmaps, and statistical pillar comparisons.
Analysis runs in the backend with Socket.IO updates and is available in the UI via the OnCoCo pages.

---

## 2. Model & Labels

### 2.1 Model Specification

| Property | Value |
|-------------|------|
| **Base model** | XLM‑RoBERTa Large (OnCoCo DE/EN) |
| **Categories** | 68 (40 counselor, 28 client) |
| **Languages** | German & English |
| **Performance** | ~80% accuracy, F1 macro ~0.78 |
| **Path** | `ONCOCO_MODEL_PATH` (env, see backend) |

**Backend path/config:** `app/services/oncoco/oncoco_service.py`

### 2.2 Label Hierarchy

Labels are hierarchical (role → level‑1 → level‑2 → …). The **complete label definition** lives in
`app/services/oncoco/oncoco_labels.py`.

Example path:
```
CO-IF-AC-RF-RLS-SR
```

---

## 3. Data Sources: KIA Pillars

Data is synced via the KIA GitLab service (`KIASyncService`).

| Pillar | Name | GitLab path |
|-------|------|-------------|
| 1 | Roleplays | `data/saeule_1/common/json` |
| 2 | Features from Pillar 1 | `data/saeule_2/common/json` |
| 3 | Anonymized data | `data/saeule_3/common/json` |
| 4 | Synthetically generated | `data/saeule_4/common/json` |
| 5 | Live testing | `data/saeule_5/common/json` |

**Repository:** `git.informatik.fh-nuernberg.de/e-beratung/kia/kia-data`

---

## 4. Workflow (current implementation)

```
KIA GitLab Sync → OnCoCo Analysis (sentence-level) → Results & Visualization
```

1. **Sync:** Pillar data is loaded from GitLab (`/api/oncoco/pillars/sync`).
2. **Analysis:** OnCoCo classifies each message sentence by sentence.
3. **Progress:** Live updates via Socket.IO (`oncoco:progress`).
4. **Results:** Distributions, transitions, and metrics in the UI.

**Resume:** Analyses can be restarted with `force=true` when stuck.

---

## 5. Analysis Logic (backend)

- **Sentence segmentation:** NLTK `punkt` (fallback: regex split)
- **Role detection:** sender/role fields + heuristic (counselor/client)
- **Label masking:** model outputs only CO labels for counselor and CL labels for client
- **Top‑3 scores:** stored per sentence (for detail views)

**Service:** `app/services/oncoco/oncoco_service.py`

---

## 6. Results & Metrics

### 6.1 Per Pillar

- `total_threads`, `total_messages`, `total_sentences`
- `counselor_sentences`, `client_sentences`
- `impact_factor_ratio`
- `resource_activation_score`
- `mi_score`
- `avg_confidence`

### 6.2 Transition Matrices

- **Level:** `full` (level‑0) or `level2` (aggregated)
- **Output:** matrix or list format (for Sankey concept)

### 6.3 Pillar Comparison (matrix comparison)

Endpoint: `/api/oncoco/analyses/{id}/matrix-comparison`

Metrics:
- Frobenius distance
- Jensen‑Shannon divergence
- Chi‑square test
- Permutation test
- Effect size

---

## 7. UI

### 7.1 Overview (`/oncoco`)

- Analyses table with status/progress
- KIA sync panel (pillar status + sync)
- Model info & label statistics

### 7.2 Configuration (`/oncoco/config`)

- Analysis name
- Pillar selection
- Advanced: `use_level2`, `batch_size`
- “Create” or “Create & Start”

### 7.3 Results (`/oncoco/results/:id`)

Tabs:
- **Overview:** metrics per pillar
- **Distribution:** label distributions (filter by pillar/level/role)
- **Transitions:** heatmaps + top transitions + matrix comparison
- **Sentences:** sentence list with filters

Live panel shows hardware info, performance, ETA, and last classification.

### 7.4 Info (`/oncoco/info`)

- Label system, examples, resources, and model details

---

## 8. API Endpoints (current)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/oncoco/info` | Model and label info |
| GET | `/api/oncoco/labels` | Labels + hierarchy |
| GET | `/api/oncoco/pillars` | Pillar status |
| POST | `/api/oncoco/pillars/sync` | KIA sync |
| GET | `/api/oncoco/analyses` | List analyses |
| POST | `/api/oncoco/analyses` | Create analysis |
| GET | `/api/oncoco/analyses/{id}` | Analysis details |
| POST | `/api/oncoco/analyses/{id}/start` | Start/resume analysis (`force=true`) |
| DELETE | `/api/oncoco/analyses/{id}` | Delete analysis |
| GET | `/api/oncoco/analyses/{id}/sentences` | Sentence labels |
| GET | `/api/oncoco/analyses/{id}/distribution` | Label distribution |
| GET | `/api/oncoco/analyses/{id}/transition-matrix` | Transitions (matrix/list) |
| GET | `/api/oncoco/analyses/{id}/comparison` | Pillar comparison |
| GET | `/api/oncoco/analyses/{id}/matrix-comparison` | Statistical matrix metrics |

---

## 9. Permissions

OnCoCo routes are protected by **`feature:comparison:view|edit`**.

---

## 10. Planned Extensions

- Sankey visualization (endpoint already returns list format)
- Export/reporting (CSV/JSON)
- Additional UI filters and benchmarks
