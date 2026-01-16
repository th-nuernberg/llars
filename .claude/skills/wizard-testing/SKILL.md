---
name: wizard-testing
description: Test LLARS wizards (Scenario Wizard, Chatbot Wizard). Use when testing wizard functionality, validating AI-powered data analysis, checking evaluation type detection, or when user mentions wizard issues.
---

# Wizard Testing for LLARS

## Overview

LLARS has two AI-powered wizards:

1. **Scenario Wizard** - Creates evaluation scenarios with AI-powered data analysis
2. **Chatbot Wizard** - Creates RAG-enabled chatbots with collection configuration

## Scenario Wizard Testing

### Test Data Infrastructure

The Scenario Wizard includes AI-powered analysis of uploaded data. To test this properly, we have test data infrastructure:

```bash
# Location of test data files
ls -la /app/scripts/

# Test scripts
scripts/
├── test_scenario_wizard.py       # External HTTP test (requires auth)
└── test_wizard_internal.py       # Internal Flask test (recommended)
```

### Quick Test (Internal)

```bash
# Run inside Flask container
docker exec -it llars_flask_service python -c "
from main import app
with app.app_context():
    exec(open('/app/scripts/test_wizard_internal.py').read())
    main()
"
```

### Manual API Test

```bash
# Get auth token
TOKEN=$(docker logs llars_flask_service 2>&1 | grep -o 'token=eyJ[^&]*' | tail -1 | cut -d= -f2)

# Test AI analysis endpoint
curl -s -X POST "http://localhost:55080/api/ai-assist/analyze-scenario-data" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"text": "Great product!", "rating": 5},
      {"text": "Bad quality", "rating": 1},
      {"text": "Okay", "rating": 3}
    ],
    "filename": "reviews.json"
  }' | python3 -m json.tool
```

### Evaluation Type Detection

The AI should correctly identify these types:

| Data Pattern | Expected Type | Confidence |
|--------------|---------------|------------|
| Numeric ratings (1-5, 1-10) | `rating` | > 0.8 |
| Star ratings, scores | `rating` | > 0.8 |
| Category labels | `labeling` | > 0.8 |
| Binary (spam/not spam) | `labeling` | > 0.8 |
| Pairs with preferred choice | `comparison` | > 0.8 |
| Quality buckets (Good/Bad) | `ranking` | > 0.7 |
| E-Mail conversations | `mail_rating` | > 0.7 |
| Fake/Real detection | `authenticity` | > 0.7 |

### Test Datasets

Popular datasets for testing (from HuggingFace):

| Dataset | Type | Test For |
|---------|------|----------|
| IMDb Reviews | rating | Sentiment/star detection |
| AG News | labeling | Multi-class classification |
| Amazon Reviews | rating | Star rating detection |
| Anthropic HH-RLHF | comparison | Preference data detection |
| TruthfulQA | labeling | Binary authenticity |

### Test Dataset Download

```python
# In Flask container
from routes.test_data.test_data_routes import download_dataset, transform_dataset

# Download IMDb dataset
result = download_dataset('imdb', max_samples=100)
print(f"Downloaded: {result}")

# Transform for Scenario Wizard
transformed = transform_dataset('imdb', result, max_items=50)
```

### Evaluation Types Reference

| Type ID | Type Key | Base Type | Description |
|---------|----------|-----------|-------------|
| 1 | ranking | - | Sort items into buckets |
| 2 | rating | - | Rate on a scale |
| 3 | mail_rating | rating | Email quality (LLARS-specific) |
| 4 | comparison | - | A vs B preference |
| 5 | authenticity | labeling | Fake/real detection (LLARS-specific) |
| 7 | labeling | - | Categorization |

### Key Files

| File | Purpose |
|------|---------|
| `app/routes/ai_assist/scenario_analysis_routes.py` | AI analysis endpoint |
| `app/services/ai_assist/scenario_data_analyzer.py` | Data analysis service |
| `llars-frontend/src/views/ScenarioManager/components/ScenarioWizard.vue` | Wizard UI |
| `llars-frontend/src/views/ScenarioManager/config/evaluationPresets.js` | Type configs |

### Database Check

```sql
-- Check created scenarios
SELECT id, scenario_name, function_type_id, created_at, config_json
FROM rating_scenarios
ORDER BY id DESC LIMIT 5;

-- Check scenario config
SELECT id, scenario_name,
       JSON_EXTRACT(config_json, '$.eval_type') as eval_type,
       JSON_EXTRACT(config_json, '$.eval_config.presetId') as preset
FROM rating_scenarios WHERE id = {ID};
```

---

## Chatbot Wizard Testing

### Quick Test

```bash
# Check existing chatbots
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:55080/api/chatbots" | python3 -c "
import sys, json
bots = json.load(sys.stdin).get('chatbots', [])
for b in bots:
    print(f'{b[\"id\"]}: {b[\"name\"]} - {b[\"build_status\"]}')"

# Create test chatbot
curl -s -X POST "http://localhost:55080/api/chatbots" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-wizard-bot",
    "display_name": "Test Bot",
    "model_name": "gpt-4o-mini",
    "rag_enabled": false,
    "is_public": true
  }' | python3 -m json.tool
```

### RAG Configuration Test

```bash
# Check available collections
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:55080/api/rag/collections" | python3 -c "
import sys, json
cols = json.load(sys.stdin).get('collections', [])
for c in cols:
    print(f'{c[\"id\"]}: {c[\"name\"]} ({c.get(\"document_count\", 0)} docs)')"

# Assign collection to chatbot
curl -s -X POST "http://localhost:55080/api/chatbots/{BOT_ID}/collections" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": 1, "is_primary": true}'
```

### Key Files

| File | Purpose |
|------|---------|
| `app/routes/chatbot/chatbot_routes.py` | CRUD endpoints |
| `app/routes/chatbot/chatbot_collection_routes.py` | Collection assignment |
| `llars-frontend/src/components/Chatbot/ChatbotEditor.vue` | Chatbot wizard UI |
| `llars-frontend/src/views/ChatWithBots/CreateChatbotDialog.vue` | Creation dialog |

---

## Common Issues

### Issue 1: AI Analysis Returns Wrong Type

**Debug:**
```bash
docker logs llars_flask_service 2>&1 | grep -i "scenario.*analysis\|eval_type"
```

**Check LLM Model:**
```sql
SELECT key_name, value_str FROM system_settings WHERE key_name = 'scenario_analysis_model';
```

**Check Prompt Template:**
```sql
SELECT id, template_key, prompt_text FROM prompt_templates WHERE template_key = 'scenario.analysis';
```

### Issue 2: Wizard File Upload Fails

**Check:**
- File size limits (default 50MB)
- Supported formats: JSON, CSV, XLSX

**Debug:**
```bash
docker logs llars_flask_service 2>&1 | grep -i "upload\|file"
```

### Issue 3: Chatbot Creation Fails

**Check LLM Provider:**
```sql
SELECT id, name, api_type, is_active FROM llm_providers WHERE is_active = 1;
SELECT model_name, provider_id, is_active FROM llm_models WHERE model_name = '{MODEL}';
```

**Check Logs:**
```bash
docker logs llars_flask_service 2>&1 | grep -i "chatbot.*create\|chatbot.*error"
```

---

## Test Checklist

### Scenario Wizard

- [ ] Upload JSON file -> AI analyzes correctly
- [ ] Upload CSV file -> AI analyzes correctly
- [ ] Upload multiple files -> Merged analysis
- [ ] Rating data -> Suggests `rating` type
- [ ] Classification data -> Suggests `labeling` type
- [ ] Preference pairs -> Suggests `comparison` type
- [ ] E-Mail data -> Suggests `mail_rating` (LLARS)
- [ ] Fake/real labels -> Suggests `authenticity` (LLARS)
- [ ] AI suggests scenario name
- [ ] AI suggests description
- [ ] Presets load correctly
- [ ] Team selection works
- [ ] Scenario creates successfully
- [ ] Stats update after creation

### Chatbot Wizard

- [ ] Basic chatbot creates successfully
- [ ] Model selection shows available models
- [ ] RAG toggle enables collection selection
- [ ] Collection assignment works
- [ ] Chatbot is accessible after creation
- [ ] Test message works

---

## Test Results Documentation

Test results are documented in:
- `docs/concepts/scenario-wizard-tests.md`

Latest test run: All 16 tests passing (100% accuracy)
- 8 main dataset tests
- 8 edge case tests
