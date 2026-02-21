# LLARS - LLM Assisted Research System

**A research platform for AI-supported analysis and evaluation of online counseling communication**

---

## 1. What is LLARS?

LLARS (LLM Assisted Research System) is a web-based research platform designed specifically for scientific analysis and evaluation of email counseling communication. The system combines modern Large Language Models (LLMs) with collaborative rating tools and automated analysis methods.

### Core Goals

- **Standardized evaluation** of counseling quality through structured rating procedures
- **LLM-assisted analysis** of communication patterns in counseling conversations
- **Collaborative research** through multi-user support with real-time synchronization
- **Reproducible research** through systematic data collection and management

---

## 2. Core Features

### 2.1 Email Rating System

The core system enables structured evaluation of email threads from counseling contexts:

| Function | Description |
|----------|-------------|
| **Mail Rating** | Rate individual emails based on defined criteria |
| **Scenario Management** | Organize emails into evaluation scenarios |
| **Ranking System** | Comparative assessment of counseling quality |
| **Multi-Rater Support** | Multiple raters can work in parallel |

### 2.2 LLM Evaluator System

Automated pairwise comparisons of email conversations by LLMs:

```
Pillar A (e.g., role-play data)  vs.  Pillar B (e.g., real counseling)
              ↓                               ↓
         [LLM Evaluation]
              ↓
    Winner: A/B + confidence + rationale
```

**Use cases:**
- Comparing different counseling approaches
- Evaluating AI-generated vs. human responses
- Measuring quality across multiple data sources

### 2.3 OnCoCo Analysis (Online Counseling Conversations)

In-depth, sentence-level classification of counseling conversations with a specialized transformer model:

**Model specification:**
- Base: XLM-RoBERTa Large (561M parameters)
- 68 fine-grained categories (40 counselor, 28 client)
- Bilingual support (German/English)
- 80% accuracy, Cohen's Kappa: 0.88 (human-level)

**Analysis output:**
- Label distributions per conversation/pillar
- Transition matrices (changes between dialog acts)
- Sankey diagrams (conversation flow visualization)
- Pillar comparisons with statistical metrics

### 2.4 Collaborative Prompt Engineering

Real-time collaborative development of LLM prompts for evaluation and analysis tasks:

- **Y.js CRDT synchronization**: Conflict-free collaboration
- **Cursor tracking**: See where other users are working
- **Versioning**: Automatic saving of all changes
- **Template management**: Reusable prompt templates

Additionally, **Markdown Collab** enables collaborative writing of Markdown documents with live preview and Git-style diff view.

### 2.5 RAG Pipeline (Retrieval-Augmented Generation)

Context-aware answer generation through ChromaDB integration:

- **Document upload**: PDF, TXT, DOCX, PPTX, XLSX (and more)
- **Chunking & embedding**: Automated processing
- **Context search**: Relevant passages for LLM queries
- **Admin interface**: Knowledge base management

---

## 3. Data Sources: KIA Pillar Model

LLARS works with the structured **KIA data repository** (git.informatik.fh-nuernberg.de):

| Pillar | Name | Content | Research Value |
|--------|------|---------|----------------|
| **1** | Role plays | Simulated counseling conversations | Training baseline, controlled scenarios |
| **2** | Features from pillar 1 | Extracted features | Quantitative analysis |
| **3** | Anonymized data | Real counseling conversations | Ground truth, validation |
| **4** | Synthetic | AI-generated conversations | Augmentation, comparison studies |
| **5** | Live tests | Current test data | Pilot studies, A/B tests |

---

## 4. Usage for Dissertation Work

### 4.1 Research Questions Addressed by LLARS

LLARS is particularly well-suited for research on:

1. **Quality measurement in online counseling**
   - How can counseling quality be measured objectively?
   - Which conversation patterns correlate with successful counseling?

2. **AI in counseling support**
   - Can LLMs reliably evaluate counseling quality?
   - How do AI-generated and human responses differ?

3. **Conversation analysis and dialog acts**
   - Which dialog acts are typical for high-quality counseling?
   - How do conversations evolve over time?

4. **Inter-rater reliability**
   - How consistent are different raters?
   - Can AI serve as an "objective" rater?

### 4.2 Method Support

| Method | LLARS Feature | Output |
|--------|---------------|--------|
| **Quantitative content analysis** | OnCoCo classification | Label distributions, frequencies |
| **Sequence analysis** | Transition matrices | Conversation patterns, transitions |
| **Comparative study** | LLM Evaluator | Pairwise ratings, rankings |
| **Inter-rater analysis** | Multi-user rating | Agreement metrics |
| **Qualitative exploration** | Prompt Engineering | Structured LLM analysis |

### 4.3 Typical Dissertation Workflow

```
1. Data import
   └── Synchronize KIA pillars
   └── Define scenarios

2. Manual evaluation (ground truth)
   └── Set up rater team
   └── Define rating criteria
   └── Run collaborative rating

3. Automated analysis
   └── Run OnCoCo classification
   └── Create LLM Evaluator sessions
   └── Compute transition matrices

4. Comparison & evaluation
   └── Human vs. LLM ratings
   └── Pillar comparisons
   └── Statistical tests

5. Export & documentation
   └── CSV/JSON export
   └── Generate visualizations
   └── Reproducible analysis pipeline
```

### 4.4 Concrete Example Use Cases

**Example 1: Evaluating counseling quality**
```
Research question: "Does counseling quality differ between
                   role plays and real counseling?"

LLARS approach:
1. Load pillar 1 (role plays) and pillar 3 (real data)
2. LLM Evaluator: run pairwise comparisons
3. OnCoCo: compare label distributions
4. Statistical analysis of differences
```

**Example 2: Conversation dynamics analysis**
```
Research question: "Which conversation patterns lead to successful
                   counseling outcomes?"

LLARS approach:
1. Run OnCoCo analysis on all threads
2. Compute transition matrices
3. Compare successful vs. unsuccessful conversations
4. Identify significant patterns
```

**Example 3: LLM as a rating tool**
```
Research question: "Can an LLM reliably replicate
                   human ratings?"

LLARS approach:
1. Human raters evaluate a sample
2. LLM Evaluator rates the same sample
3. Calculate inter-rater reliability (Cohen's Kappa)
4. Analyze discrepancies
```

---
