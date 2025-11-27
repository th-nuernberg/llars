# OnCoCo Model (xlm-roberta-large-OnCoCo-DE-EN)

## Übersicht

Dieses Verzeichnis enthält das OnCoCo (Online Counseling Conversations) Klassifikationsmodell für die Analyse von E-Mail-Konversationen.

**Basis-Modell:** XLM-RoBERTa Large  
**Feintuning:** Online-Beratungskonversationen (Deutsch/Englisch)  
**Aufgabe:** Klassifikation von Beratungsgesprächen

## Dateien

| Datei | Größe | Beschreibung | In Git? |
|-------|-------|--------------|---------|
| `config.json` | 5 KB | Modell-Konfiguration | ✅ Ja |
| `tokenizer.json` | 17 MB | Tokenizer-Vokabular | ✅ Ja |
| `tokenizer_config.json` | 2 KB | Tokenizer-Einstellungen | ✅ Ja |
| `special_tokens_map.json` | 1 KB | Spezielle Tokens | ✅ Ja |
| `model.safetensors` | 2.2 GB | Modell-Gewichte | ❌ Nein (.gitignore) |
| `training_args.bin` | 5 KB | Training-Parameter | ❌ Nein (.gitignore) |

## Model-Gewichte herunterladen

Die großen Modell-Dateien sind nicht in Git enthalten. Zum Herunterladen:

```bash
# Option 1: Von HuggingFace (falls verfügbar)
# huggingface-cli download <model-id> --local-dir app/models/oncoco/

# Option 2: Vom internen Server
# scp user@server:/path/to/model.safetensors app/models/oncoco/

# Option 3: Aus Backup wiederherstellen
# cp /backup/oncoco/model.safetensors app/models/oncoco/
```

## Verwendung

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification

model_path = "app/models/oncoco"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

# Klassifikation durchführen
inputs = tokenizer("Beispieltext", return_tensors="pt")
outputs = model(**inputs)
```

## Verknüpfung mit LLARS

Das OnCoCo-Modell wird verwendet in:
- `app/services/oncoco/` - OnCoCo Analyse-Service
- `llars-frontend/src/components/Judge/` - Integrierte Analyse-Ansicht
