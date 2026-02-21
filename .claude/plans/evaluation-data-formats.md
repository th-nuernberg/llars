# Einheitliche Datenformate für Evaluationstypen

## Übersicht

Dieses Dokument definiert die einheitlichen Datenformate für alle Evaluationstypen in LLARS.
Die Formate gelten sowohl für den Batch Generator als auch für den Szenario Manager.

---

## 1. Gemeinsame Basis-Struktur

### EvaluationItem (Tabelle: evaluation_items)

```python
{
    "item_id": int,              # Primary Key
    "chat_id": int,              # Unique identifier (legacy, für Kompatibilität)
    "subject": str,              # Titel/Betreff des Items
    "sender": str,               # Ersteller/Quelle (Model-Name bei generierten Items)
    "function_type_id": int,     # 1=ranking, 2=rating, 3=mail_rating, etc.
    "ground_truth_label": str,   # Optional: Ground Truth für supervised evaluation
    "metadata_json": dict,       # NEU: Strukturierte Metadaten (siehe unten)
}
```

### Message (Tabelle: messages)

```python
{
    "message_id": int,
    "item_id": int,              # FK zu evaluation_items
    "sender": str,               # "Ratsuchende" | "Beratende" | "System" | Model-Name
    "content": str,              # Nachrichteninhalt
    "timestamp": datetime,
    "generated_by": str,         # "Human" | Job-Name | Model-Name
}
```

---

## 2. Format pro Evaluationstyp

### 2.1 Rating (function_type_id = 2)

**Anwendungsfall:** Generische Texte bewerten (Zusammenfassungen, Antworten, etc.)

**EvaluationItem:**
```python
{
    "subject": "Summary of Article X",
    "sender": "gpt-4-turbo",
    "function_type_id": 2,
    "metadata_json": {
        "source_type": "generated",          # "generated" | "imported" | "manual"
        "source_job_id": 123,                # Optional: Batch Job ID
        "source_item_id": 456,               # Optional: Original-Item ID
        "llm_model": "gpt-4-turbo",
        "prompt_template_id": 1,
        "prompt_variant": "default",
    }
}
```

**Messages:**
```python
[
    {
        "sender": "Source",                  # Quelltext
        "content": "Der Originaltext...",
        "generated_by": "Human"
    },
    {
        "sender": "gpt-4-turbo",             # Generierte Antwort
        "content": "Zusammenfassung...",
        "generated_by": "Generation Job 123"
    }
]
```

**Scenario config_json:**
```python
{
    "evaluation": "rating",
    "type": "multi-dimensional",
    "min": 1,
    "max": 5,
    "step": 1,
    "dimensions": [
        {"id": "coherence", "name": {"de": "Kohärenz"}, "weight": 0.25},
        {"id": "fluency", "name": {"de": "Flüssigkeit"}, "weight": 0.25},
        # ...
    ],
    "labels": {
        "1": {"de": "Sehr schlecht"},
        "5": {"de": "Sehr gut"}
    },
    "showOverallScore": true,
    "allowFeedback": true,
}
```

---

### 2.2 Mail Rating (function_type_id = 3)

**Anwendungsfall:** E-Mail-Verläufe zwischen Ratsuchenden und Beratenden bewerten

**EvaluationItem:**
```python
{
    "subject": "Beratungsanfrage: Probleme am Arbeitsplatz",
    "sender": "Generation Job 123",          # Quelle des Items
    "function_type_id": 3,
    "metadata_json": {
        "source_type": "generated",
        "source_job_id": 123,
        "original_messages": [               # Original-Nachrichten vor Generation
            {"role": "Ratsuchende", "content": "..."}
        ],
        "llm_model": "gpt-4-turbo",
        "prompt_template_id": 1,
    }
}
```

**Messages:** (KRITISCH - muss korrekte Rollen haben!)
```python
[
    {
        "sender": "Ratsuchende",             # ← NICHT "Messages"!
        "content": "Guten Tag, ich wende mich an Sie...",
        "timestamp": "2025-01-15T14:23:00",
        "generated_by": "Human"              # Original-Nachricht
    },
    {
        "sender": "Beratende",               # ← NICHT "Content"!
        "content": "Liebe Sabine, vielen Dank...",
        "timestamp": "2025-01-15T15:30:00",
        "generated_by": "gpt-4-turbo"        # Generierte Antwort
    },
    {
        "sender": "Ratsuchende",
        "content": "Vielen Dank für Ihre Antwort...",
        "generated_by": "Human"
    }
]
```

**Scenario config_json:**
```python
{
    "eval_type": "mail_rating",
    "type": "multi-dimensional",
    "min": 1,
    "max": 5,
    "dimensions": [
        {
            "id": "client_coherence",
            "name": {"de": "Kohärenz ratsuchende Person"},
            "weight": 0.25
        },
        {
            "id": "counsellor_coherence",
            "name": {"de": "Kohärenz beratende Person"},
            "weight": 0.25
        },
        {
            "id": "quality",
            "name": {"de": "Beratungsqualität"},
            "weight": 0.25
        },
        {
            "id": "overall",
            "name": {"de": "Gesamtbewertung"},
            "weight": 0.25,
            "scale": {"type": "binary", "labels": {"1": "Ja", "2": "Nein"}}
        }
    ],
    "labels": {"1": "Sehr gut", "5": "Sehr schlecht"},
    "disableOnBadRating": true,
}
```

---

### 2.3 Ranking (function_type_id = 1)

**Anwendungsfall:** Items nach Qualität sortieren oder in Kategorien einteilen

**EvaluationItem:**
```python
{
    "subject": "Text A vs B",
    "function_type_id": 1,
    "metadata_json": {
        "source_type": "generated",
        "comparison_group": "summary_comparison_1",  # Items in gleicher Gruppe
    }
}
```

**Scenario config_json:**
```python
{
    "evaluation": "ranking",
    "mode": "sort",                          # "sort" | "bucket"
    "buckets": ["Gut", "Mittel", "Schlecht"], # nur bei mode=bucket
    "allowTies": false,
}
```

---

### 2.4 Labeling (function_type_id = 7)

**Anwendungsfall:** Kategorien zuweisen (Sentiment, Topic, etc.)

**EvaluationItem:**
```python
{
    "subject": "Customer Review #123",
    "function_type_id": 7,
    "ground_truth_label": "positive",        # Optional für supervised
    "metadata_json": {
        "source_type": "imported",
    }
}
```

**Scenario config_json:**
```python
{
    "evaluation": "labeling",
    "categories": [
        {"id": "positive", "name": "Positiv", "color": "#98d4bb"},
        {"id": "neutral", "name": "Neutral", "color": "#D1BC8A"},
        {"id": "negative", "name": "Negativ", "color": "#e8a087"}
    ],
    "multiLabel": false,                     # true = mehrere Labels erlaubt
    "allowUnsure": true,
}
```

---

### 2.5 Authenticity (function_type_id = 5)

**Anwendungsfall:** Fake vs. Echt Erkennung

**EvaluationItem:**
```python
{
    "subject": "Beratungsverlauf #456",
    "function_type_id": 5,
    "ground_truth_label": "fake",            # "fake" | "real"
    "metadata_json": {
        "source_type": "generated",
        "generation_model": "gpt-4",
    }
}
```

**Scenario config_json:**
```python
{
    "evaluation": "authenticity",
    "labels": {
        "real": {"de": "Echt", "en": "Real"},
        "fake": {"de": "Fake", "en": "Fake"}
    },
    "showConfidenceSlider": true,
}
```

---

### 2.6 Comparison (function_type_id = 4)

**Anwendungsfall:** Paarweiser Vergleich (A vs B)

**EvaluationItem:** (Ein Item pro Vergleichspaar)
```python
{
    "subject": "Comparison: GPT-4 vs Claude",
    "function_type_id": 4,
    "metadata_json": {
        "item_a_id": 123,
        "item_b_id": 124,
        "comparison_dimension": "quality",
    }
}
```

**Scenario config_json:**
```python
{
    "evaluation": "comparison",
    "comparisonMode": "pairwise",            # "pairwise" | "elo"
    "dimensions": ["quality", "helpfulness"],
    "allowTie": true,
}
```

---

## 3. Batch Generator → Scenario Konvertierung

### Notwendige Fixes im OutputExportService

```python
def _create_evaluation_items_from_outputs(outputs, function_type_id, job):
    """
    FIXED: Erstellt Items mit korrektem Format je nach function_type.
    """
    config = job.config_json or {}
    source_items = {item['id']: item for item in config.get('sources', {}).get('items', [])}

    for output in outputs:
        # 1. Erstelle EvaluationItem mit Metadaten
        item = EvaluationItem(
            subject=_get_subject(output, source_items),
            sender=output.llm_model_name,
            function_type_id=function_type_id,
            metadata_json={
                "source_type": "generated",
                "source_job_id": job.id,
                "source_item_id": output.source_item_id,  # ← Muss gesetzt sein!
                "llm_model": output.llm_model_name,
                "prompt_template_id": output.prompt_template_id,
            }
        )

        # 2. Erstelle Messages mit korrekten Rollen
        if function_type_id == 3:  # mail_rating
            _create_mail_rating_messages(item, output, source_items)
        else:
            _create_generic_messages(item, output)
```

### Fix für mail_rating Messages

```python
def _create_mail_rating_messages(item, output, source_items):
    """Erstellt Messages mit korrekten Rollen für mail_rating."""
    source_item = source_items.get(output.source_item_id, {})

    # 1. Original-Nachrichten mit korrekten Rollen
    for msg in source_item.get('messages', []):
        Message(
            item_id=item.item_id,
            sender=msg.get('role', 'Ratsuchende'),  # ← Korrekte Rolle!
            content=msg.get('content', ''),
            timestamp=parse_timestamp(msg.get('timestamp')),
            generated_by="Human"
        )

    # 2. Generierte Antwort als Beratende
    Message(
        item_id=item.item_id,
        sender="Beratende",                         # ← Korrekte Rolle!
        content=output.generated_content,
        timestamp=datetime.utcnow(),
        generated_by=output.llm_model_name
    )
```

---

## 4. Migration der bestehenden Daten

Für bereits erstellte Szenarien mit falschem Format:

```sql
-- Fix sender="Content" → "Beratende"
UPDATE messages
SET sender = 'Beratende'
WHERE sender = 'Content'
  AND generated_by LIKE 'Email Response Generator%';

-- Fix sender="Messages" → Parse JSON und erstelle echte Messages
-- (Benötigt Python-Migration-Script)
```

---

## 5. Validierung

### Schema-Validierung für config_json

```python
EVALUATION_CONFIG_SCHEMAS = {
    "rating": {
        "required": ["type", "dimensions"],
        "optional": ["min", "max", "labels", "showOverallScore"]
    },
    "mail_rating": {
        "required": ["type", "dimensions"],
        "optional": ["disableOnBadRating"]
    },
    "labeling": {
        "required": ["categories"],
        "optional": ["multiLabel", "allowUnsure"]
    },
    "authenticity": {
        "required": ["labels"],
        "optional": ["showConfidenceSlider"]
    },
    "ranking": {
        "required": ["mode"],
        "optional": ["buckets", "allowTies"]
    },
    "comparison": {
        "required": ["comparisonMode"],
        "optional": ["dimensions", "allowTie"]
    }
}
```
