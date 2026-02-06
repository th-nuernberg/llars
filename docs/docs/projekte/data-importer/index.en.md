# LLARS Data Importer

!!! info "AI by Design"
    The Data Importer uses AI assistance to import arbitrary data formats into LLARS.

## Overview

The LLARS Data Importer is a universal import wizard that guides users through the entire process:

**Upload → AI Analysis → Transformation → Scenario → Users → Evaluation**

## Documentation

| Document | Description |
|----------|-------------|
| [Concept](konzept.md) | Full project concept with requirements, architecture, and work checklist |

## Quick Facts

| Aspect | Details |
|--------|---------|
| **Status** | Implemented (active) |
| **Priority** | High |
| **Key Feature** | AI-assisted data transformation |
| **Target Group** | Researchers without technical background |

## Supported Formats

- LLARS native format
- OpenAI/ChatML (messages array)
- LMSYS pairwise comparison
- JSONL/NDJSON
- CSV/TSV
- Generic JSON lists (fallback)
- Custom (via AI transformation)

## Evaluation Types

- Rating (star rating)
- Ranking (drag & drop sorting)
- Mail Rating (conversation rating)
- Comparison (A vs B)
- Authenticity (fake/real)
- Labeling (classification)
