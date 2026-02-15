# Fix: Model/Prompt-Metadaten im Evaluation-Export

## Context

Wenn ein Ranking/Rating-Szenario aus Batch-Generation erstellt wird, speichert die Import-Pipeline den Model-Namen auf `Feature.llm_id` (FK → `LLM.name`) und den Feature-Typ auf `Feature.type_id` (FK → `FeatureType.name`). Der Export-Endpoint (`GET /api/scenarios/<id>/export`) liest diese Joins aber **nicht** — exported werden nur `feature_content`, `ranking_value`, `bucket`.

**Ziel:** Im Export soll pro Feature/Item sichtbar sein, welches LLM und welcher Prompt-Typ den Text generiert hat. Damit kann man nach dem Download direkt auswerten, welches Modell am besten abgeschnitten hat.

## Datei

`app/routes/scenarios/scenario_manager_api.py`

## Änderungen

### 1. Import erweitern (Zeile 33)

`LLM` und `FeatureType` zum Import aus `db.tables` hinzufügen.

### 2. Ranking-Export: LLM-Lookup aufbauen (nach Zeile 2052)

Feature hat `feature.llm_id` (FK) und `feature.type_id` (FK). Die Relationship `feature.llm` und `feature.feature_type` existieren bereits am Model. SQLAlchemy lazy-loads diese, aber um N+1 Queries zu vermeiden: einmalig alle LLM- und FeatureType-IDs sammeln und per Bulk-Query laden.

```python
# Bulk-load LLM names and FeatureType names for features
llm_ids = {f.llm_id for f in features if f.llm_id}
llm_map = {l.llm_id: l.name for l in LLM.query.filter(LLM.llm_id.in_(llm_ids)).all()} if llm_ids else {}

type_ids = {f.type_id for f in features if f.type_id}
type_map = {t.type_id: t.name for t in FeatureType.query.filter(FeatureType.type_id.in_(type_ids)).all()} if type_ids else {}
```

### 3. Ranking-Export: Felder hinzufügen (Zeile 2063-2073)

Zwei neue Felder in das `results.append()` dict:

```python
'model_name': llm_map.get(feature.llm_id) if feature else None,
'feature_type': type_map.get(feature.type_id) if feature else None,
```

### 4. Rating-Export: Item→Feature→LLM Lookup (Zeile 2098-2119)

Für `dimensional_rating` gibt es keine Features, aber die Items haben Messages mit `generated_by` und ggf. Features zugeordnet. Bester Ansatz: Features pro Item laden und dort den LLM-Namen lesen.

```python
# Load features for rating items to get model attribution
rating_features = Feature.query.filter(Feature.thread_id.in_(scenario_thread_ids)).all()
item_feature_map = {}  # item_id → list of {model_name, feature_type}
llm_ids = {f.llm_id for f in rating_features if f.llm_id}
llm_map = {l.llm_id: l.name for l in LLM.query.filter(LLM.llm_id.in_(llm_ids)).all()} if llm_ids else {}
type_ids = {f.type_id for f in rating_features if f.type_id}
type_map = {t.type_id: t.name for t in FeatureType.query.filter(FeatureType.type_id.in_(type_ids)).all()} if type_ids else {}
for f in rating_features:
    item_feature_map.setdefault(f.item_id, []).append({
        'model_name': llm_map.get(f.llm_id),
        'feature_type': type_map.get(f.type_id),
    })
```

Dann beim Rating-Export:
```python
'item_models': item_feature_map.get(rating.item_id, []),
```

Dies gibt eine Liste der generierten Features pro Item — bei Rating-Items die aus Generation stammen hat man so die Model-Attribution.

### 5. Legacy Rating-Export (Zeile 2156-2175)

Gleicher LLM-Lookup wie beim Ranking — Features haben bereits `llm_id`. Felder `model_name` und `feature_type` ergänzen.

## Nicht geändert

- **Authenticity/Mail-Rating/Comparison**: Diese haben keine Generation-Features, kein Bedarf.
- **LLM-Evaluator Results** (`_llm` Typen): Haben bereits `model_id` im Export.

## Verifizierung

1. `pytest tests/ -x --ignore=tests/security -q -k "not (test_RANK_040 or test_RANK_041 or test_RANK_131)"`
2. Manuell: `GET /api/scenarios/{id}/export?format=json` → prüfen ob `model_name` und `feature_type` in Ranking-Results enthalten sind
3. CSV-Export: Neue Spalten `model_name`, `feature_type` sichtbar
