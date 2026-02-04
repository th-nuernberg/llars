# Evaluation

**Version:** 2.0 | **Date:** January 2026

This guide explains how to perform evaluations in LLARS. The interface and method depend on the evaluation type.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  Evaluation Interface                                               │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐  │
│  │                             │  │                             │  │
│  │    Content Area             │  │    Rating Panel             │  │
│  │    (Text, Conversation)     │  │    (Scales, Buttons)        │  │
│  │                             │  │                             │  │
│  └─────────────────────────────┘  └─────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│  [◀ Back]            Item 3 of 25             [Next ▶]              │
│  ████████████░░░░░░░░░░░░░░░░░░░░░░  12%                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Start Evaluation

### As an Invited Evaluator

1. Open the **Scenario Manager**
2. Go to the **"Invitations"** tab
3. **Accept the invitation**
4. Click **"Go to Evaluation"**

```
┌────────────────────────────────────────┐
│  [↕️] LLM Comparison Benchmark          │
│  Ranking · Invited by admin             │
│                                         │
│  Your progress: 0/20 (0%)               │
│  ░░░░░░░░░░░░░░░░░░░░                   │
│                                         │
│  [Reject] [Accept]                      │
│  (after accepting: [Go to Evaluation]) │
└────────────────────────────────────────┘
```

!!! info "Limited permissions"
    As an invited evaluator, you only see your own progress, not other evaluators or overall results.

### As Owner (Scenario Creator)

1. Open **Evaluation** (Evaluation Hub) from the main menu
2. Select the desired scenario
3. Open the **items overview** and start evaluating

!!! tip "Test before inviting"
    As the owner, you can work through the scenario yourself before inviting others. Your ratings are saved as well.

---

## Items Overview

After opening, you first see the **items overview**. It shows all items as cards with status badges and filters (Pending, In Progress, Done). Clicking an item opens the evaluation session.

```
┌────────────────────────────────────────┐
│  Filter: All | Pending | In Progress   │
│                                         │
│  [Item Card]  [Item Card]  [Item...]    │
│  Status Badge  Status Badge  Status...  │
└────────────────────────────────────────┘
```

---

## Evaluation Interface

The evaluation session opens after clicking an item in the overview.

### Layout

The interface is divided into three main areas:

| Area | Description |
|------|-------------|
| **Header** | Scenario name, progress, navigation |
| **Content** | The item to be rated (text, conversation, variants) |
| **Rating** | Input controls depending on evaluation type |

### Navigation

| Element | Function |
|---------|----------|
| **◀ Back** | Previous item |
| **Next ▶** | Next item |
| **Progress bar** | Shows current progress |
| **Item X of Y** | Current position |

---

## Evaluation Types

### Rating (Multi-Dimensional)

**Use cases:** text quality, summaries, LLM outputs

```
┌─────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐  │
│  │  Question:                  │  │  Coherence                  │  │
│  │  What is the capital        │  │  ○ 1  ○ 2  ● 3  ○ 4  ○ 5     │  │
│  │  of France?                 │  ├─────────────────────────────┤  │
│  │                             │  │  Fluency                    │  │
│  │  Answer:                    │  │  ○ 1  ○ 2  ○ 3  ● 4  ○ 5     │  │
│  │  The capital of France      │  ├─────────────────────────────┤  │
│  │  is Paris.                  │  │  Relevance                  │  │
│  │                             │  │  ○ 1  ○ 2  ○ 3  ○ 4  ● 5     │  │
│  │                             │  ├─────────────────────────────┤  │
│  │                             │  │  Consistency                │  │
│  │                             │  │  ○ 1  ○ 2  ○ 3  ● 4  ○ 5     │  │
│  └─────────────────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

#### Dimensions

Standard dimensions for the LLM evaluator:

| Dimension | Description | Scale |
|-----------|-------------|-------|
| **Coherence** | Logical flow | 1-5 |
| **Fluency** | Language quality | 1-5 |
| **Relevance** | Relevance to the question | 1-5 |
| **Consistency** | Factual consistency | 1-5 |

#### Rating Tips

- Rate **each dimension individually**
- Do **not** compare across items
- Follow the **scale descriptions**

---

### Ranking (Bucket Sorting)

**Use cases:** summary quality, LLM comparisons, prioritization

```
┌─────────────────────────────────────────────────────────────────────┐
│  Reference: Original article about climate change...                │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │    GOOD      │  │   MEDIUM     │  │   POOR       │              │
│  │   (green)    │  │   (yellow)   │  │   (red)      │              │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤              │
│  │              │  │              │  │              │              │
│  │  [Summary A] │  │              │  │              │              │
│  │              │  │              │  │              │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                     │
│  Unsorted:                                                         │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐                         │
│  │ Summary B │ │ Summary C │ │ Summary D │                         │
│  └───────────┘ └───────────┘ └───────────┘                         │
└─────────────────────────────────────────────────────────────────────┘
```

#### How it Works

1. **Read the reference** (original text) at the top
2. **Read each variant** (Summary A, B, C...)
3. **Drag & drop** each variant into the appropriate bucket
4. **Ties are allowed** - multiple items can be in the same bucket

#### Bucket Types

| Bucket | Color | Meaning |
|--------|-------|---------|
| **Good** | Green | High quality |
| **Medium** | Yellow | Acceptable quality |
| **Poor** | Red | Low quality |

!!! tip "Compare to the reference"
    Always evaluate relative to the original text, not by comparing summaries to each other.

---

### Labeling (Categorization)

**Use cases:** topic classification, sentiment analysis

```
┌─────────────────────────────────────────────────────────────────────┐
│  Text:                                                              │
│  "The product is fantastic! Shipping was fast                       │
│   and customer service was very helpful."                           │
├─────────────────────────────────────────────────────────────────────┤
│  Select category:                                                   │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Positive   │  │   Neutral    │  │   Negative   │              │
│  │      ✓       │  │              │  │              │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

#### Category Types

| Mode | Description |
|------|-------------|
| **Single-label** | Exactly one category |
| **Multi-label** | Multiple categories allowed |

#### Rating Tips

- Choose the **most fitting** category
- For multi-label: select **only relevant** categories
- If unsure: use the optional "Unsure" category

---

### Comparison (Pairwise Comparison)

**Use cases:** model comparisons, preference studies

```
┌─────────────────────────────────────────────────────────────────────┐
│  Prompt: "Explain quantum computing simply."                       │
├────────────────────────────┬────────────────────────────────────────┤
│  Answer A                  │  Answer B                              │
│                            │                                        │
│  "Quantum computers use    │  "A quantum computer is like a         │
│  qubits instead of bits.   │  normal computer, but it can do        │
│  They can..."              │  many computations at once..."         │
│                            │                                        │
├────────────────────────────┴────────────────────────────────────────┤
│                                                                     │
│  Which answer is better?                                           │
│                                                                     │
│  [ A is better ]  [ Tie ]  [ B is better ]                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### Options

| Option | Description |
|--------|-------------|
| **A is better** | Prefer answer A |
| **B is better** | Prefer answer B |
| **Tie** | Both are equally good (if allowed) |

#### Rating Tips

- Read **both answers completely**
- Focus on the **quality criteria** of the scenario
- Choose tie only if **no preference** exists

---

### Authenticity (Human vs AI)

**Use cases:** detect AI-generated texts

```
┌─────────────────────────────────────────────────────────────────────┐
│  Text:                                                              │
│                                                                     │
│  "Dear client, thank you for your message.                          │
│   Your situation sounds challenging. It is important                │
│   that you seek professional help..."                               │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  Was this text written by a human or an AI?                          │
│                                                                     │
│  ┌─────────────────────┐    ┌─────────────────────┐                │
│  │   👤 HUMAN          │    │   🤖 AI             │                │
│  │                     │    │                     │                │
│  └─────────────────────┘    └─────────────────────┘                │
│                                                                     │
│  Optional: How confident are you?                                   │
│  [ Very unsure ] ─────●───── [ Very sure ]                          │
└─────────────────────────────────────────────────────────────────────┘
```

#### Detection Hints

| Feature | More Human | More AI |
|---------|------------|---------|
| **Language** | Colloquial, errors | Formal, error-free |
| **Structure** | Variable | Uniform |
| **Emotions** | Authentic, individual | Generic, distant |
| **Details** | Specific, personal | Generic |

!!! warning "No guarantee"
    These are tendencies, not reliable indicators. Modern LLMs can sound very human.

!!! info "Configurable options"
    The available options (e.g., Human/AI or Real/Fake) are defined per scenario.

---

### Mail Rating (Email Thread Evaluation)

**Use cases:** counseling quality, response quality in email threads

```
┌─────────────────────────────────────────────────────────────────────┐
│  Email thread                                                      │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 👤 Client (2026-01-10, 14:30)                                │   │
│  │ Subject: Problems at work                                    │   │
│  │                                                              │
│  │ Hi, I have been having issues with my manager for weeks...   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 💬 Counselor (2026-01-11, 09:15)                             │   │
│  │                                                              │
│  │ Thank you for your message. I understand that the situation  │
│  │ is stressful for you...                                      │
│  └─────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────┤
│  Rate the counselor response:                                       │
│                                                                     │
│  Empathy:         ○ 1  ○ 2  ○ 3  ● 4  ○ 5                          │
│  Professionalism: ○ 1  ○ 2  ○ 3  ○ 4  ● 5                          │
│  Helpfulness:     ○ 1  ○ 2  ○ 3  ● 4  ○ 5                          │
└─────────────────────────────────────────────────────────────────────┘
```

#### Special Notes

- **Conversation view:** The full email thread is displayed
- **Context matters:** Rate the response in context of the request
- **Roles:** Client messages vs. counselor responses

---

## Progress & Status

### Progress Indicator

```
████████████░░░░░░░░░░░░░░░░░░░░░░  35%
14 of 40 items rated
```

### Item Status

| Status | Meaning |
|--------|---------|
| **Pending** | Not rated yet |
| **In progress** | Rating started or partially complete |
| **Done** | Fully rated |
| **Saving** | Rating is being saved |

---

## Tips & Best Practices

### Consistency

- **Calibrate yourself:** Rate the first 3-5 items especially carefully
- **Plan breaks:** After 20-30 items, take a short break
- **Take notes:** Leave comments if a feedback field is enabled

### Pause & Resume

- **Auto-save:** Your ratings are saved automatically
- **Pause anytime:** Just close the window
- **Resume:** Open the evaluation again - you continue at the last item

### Quality Assurance

!!! warning "Important notes"
    - Rate **impartially** - ignore which model produced the text
    - **Take your time** - quality over speed

---

## FAQ

### Can I change a rating?

Yes. Simply navigate back to the item. Your new rating overwrites the old one.

### What happens if I stop?

All previous ratings are saved. You can continue at any time.

### Can I see results?

- **As evaluator:** No, you only see your own progress
- **As owner:** Yes, in the Scenario Manager under the "Evaluation" tab

### How many items do I need to rate?

It depends on your role and distribution:
- **EVALUATOR:** Items according to distribution (e.g., all, random, sequential)
- **VIEWER:** No ratings (read-only)

---

## LLM Evaluation

In addition to human evaluators, **LLM models** can be used as automatic evaluators.

### Available Models

- **System models** (admin-configured)
- **Own/shared providers** (provided by the user or team)

### Configure LLM Evaluation

1. In the **Scenario Wizard** (step "Team"), select LLMs
2. **Enable LLM evaluation**

!!! info "Automatic rating"
    When LLM evaluation is enabled, the selected models automatically rate all items based on the configured dimensions. Results appear in the Evaluation tab.

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scenarios/:scenarioId` | GET | Scenario details (for overview) |
| `/api/evaluation/session/:scenarioId` | GET | Fetch session data |
| `/api/evaluation/session/:scenarioId/items/:itemId/evaluate` | POST | Save a rating |
| `/api/evaluation/llm/:scenarioId/start` | POST | Start LLM evaluation |
| `/api/evaluation/llm/:scenarioId/stop` | POST | Stop LLM evaluation |

---

## See Also

- [Scenario Wizard](scenario-wizard.md) - Create scenarios
- [Scenario Manager](scenario-manager.md) - Manage scenarios
- [Permission System](permission-system.md) - Access rights
