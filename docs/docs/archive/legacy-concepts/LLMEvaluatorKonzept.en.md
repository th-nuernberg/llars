# LLM-as-Evaluator: Technical Concept (Legacy)

**Version:** 1.0 | **As of:** 2026-01-14  
**Focus:** Constrained decoding, transparency, configurable prompts

!!! note "Legacy document"
    This is a legacy concept. The German document contains the full detailed specification.
    This English page provides a concise summary of the main ideas and structures.

---

## Summary

The document proposes a structured, transparent LLM evaluator for LLARS that:

- Enforces **constrained output schemas** (Pydantic) per evaluation type
- Requires **reasoning + confidence** for every decision
- Supports multiple evaluation modes: rating, ranking, labeling, comparison, authenticity, mail rating
- Adds **auditability** (prompt/version metadata, timing)

---

## Evaluation Types (high level)

| Type | Human input | LLM output | Transparency |
|------|-------------|-----------|--------------|
| **Ranking** | Bucket sort | Bucket JSON + reasoning | Bucket + overall reasoning |
| **Rating** | 1‑5 per feature | Ratings JSON + reasoning | Per‑feature reasoning |
| **Authenticity** | Real/Fake | Vote + confidence | Vote + reasoning |
| **Mail rating** | Thread rating | Rating + reasoning | Full reasoning |
| **Comparison** | A/B/Tie | Winner + confidence | Criteria‑based reasoning |
| **Text classification** | Labels | Label + confidence | Label + reasoning |

---

## Schema Design (condensed)

Core schema elements:

- `reasoning`: required, length‑bounded
- `confidence`: 0.0–1.0
- `meta`: processing time, model version, prompt version

Examples described in the German spec:

- **Ranking schema** with bucket‑level reasoning + overall assessment
- **Rating schema** with per‑dimension reasoning
- **Comparison schema** with criteria‑based scoring

---

## Prompting & Decoding

Key ideas:

- Use **strict JSON prompts** with examples
- Leverage **constrained decoding** to enforce schema validity
- Track prompt versions for reproducibility

---

## UI/Workflow Integration (summary)

- LLM evaluator can run **in parallel with human ratings**
- Results are **stored with metadata** and can be compared to human labels
- UI should show **reasoning snippets** and confidence

---

## Status

This concept was drafted as a forward‑looking design and is archived here for reference. For the full technical specification (schemas, prompt templates, error handling, edge cases), see the German document.
