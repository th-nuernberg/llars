# KAIMO - Panel Concept with Role Separation

!!! warning "Status: Concept"
    This project is in the **concept phase**.
    The design is being developed.

**Created:** 2025-11-29
**Author:** Claude Code
**Version:** 1.2 (based on KAIMo_Final prototype)

---

## Objective

KAIMO (AI-assisted Analysis and Modeling) is integrated into LLARS as an interactive learning tool. The system distinguishes between **Researcher (Admin Panel)** and **Evaluator (User Panel)**, where Researchers can create and manage new cases, while Evaluators work through and assess them.

!!! info "AI Integration: Prepared, not implemented"
    The database and API are prepared for future AI integration (table `kaimo_ai_content`, API endpoints).
    **Phases 1-5 will be implemented without AI functionality.** The AI texts (summary, impact assessment, plausibility check) will be entered manually by Researchers.

**Core idea:**
```
Researcher: Create case -> Define documents/hints -> Assign specialists
Evaluator:  Select case -> Assign hints -> Submit assessment -> View result
```

---

## Roles and Permissions

### Role Model

| Role | Panel | Description |
|------|-------|-------------|
| **Researcher** | KAIMO Admin Panel | Can create, edit, delete cases and analyze results |
| **Evaluator** | KAIMO Panel | Can work through assigned cases and submit assessments |

### Permission System

| Permission | Description | Researcher | Evaluator |
|------------|-------------|:----------:|:------:|
| `feature:kaimo:view` | View KAIMO section, work through cases | ✓ | ✓ |
| `feature:kaimo:edit` | Submit own assessments | ✓ | ✓ |
| `admin:kaimo:manage` | Create/edit/delete cases, view results | ✓ | ✗ |
| `admin:kaimo:results` | View aggregated results and statistics | ✓ | ✗ |

### Role Mapping

```python
# In app/db/db.py - extend role definition

KAIMO_PERMISSIONS = {
    'admin': [
        'feature:kaimo:view',
        'feature:kaimo:edit',
        'admin:kaimo:manage',
        'admin:kaimo:results'
    ],
    'researcher': [
        'feature:kaimo:view',
        'feature:kaimo:edit',
        'admin:kaimo:manage',
        'admin:kaimo:results'
    ],
    'evaluator': [
        'feature:kaimo:view',
        'feature:kaimo:edit'
    ]
}
```

---

## Requirements

### Functional Requirements

| ID | Requirement | Priority | Panel |
|----|-------------|----------|-------|
| F01 | Researcher can create a new case (case vignette) | High | Admin |
| F02 | Researcher can add documents/case notes to a case | High | Admin |
| F03 | Researcher can define hints and assign categories | High | Admin |
| F04 | Researcher can manually enter texts (summary, impact assessment) | High | Admin |
| F05 | Researcher can share a case with specific users/groups | Medium | Admin |
| F06 | Evaluator sees a list of shared cases | High | User |
| F07 | Evaluator can assign hints to categories (drag & drop) | High | User |
| F08 | Evaluator can rate hints as risk/resource/unclear | High | User |
| F09 | Evaluator submits final case verdict | High | User |
| F10 | Researcher sees aggregated results of all assessments | Medium | Admin |
| F11 | Researcher can provide a model solution and analyze deviations | Low | Admin |

### Non-functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NF01 | Performance: Smooth drag & drop interaction | High |
| NF02 | Usability: Intuitive user guidance for specialists without IT knowledge | High |
| NF03 | Security: Strict role separation, no access to other users' assessments | High |
| NF04 | Responsiveness: Mobile-optimized view for the Evaluator panel | Medium |

---

## Database Design

### New Tables

#### `kaimo_cases` (Case Vignettes)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INT (PK) | No | Auto-increment primary key |
| name | VARCHAR(100) | No | Internal name (URL-safe) |
| display_name | VARCHAR(255) | No | Display name (e.g., "Case Malaika") |
| description | TEXT | Yes | Short description of the case |
| status | ENUM | No | 'draft', 'published', 'archived' |
| icon | VARCHAR(10) | Yes | Emoji for display |
| color | VARCHAR(20) | Yes | Accent color (hex) |
| created_by | VARCHAR(255) | No | Username of the creator |
| created_at | DATETIME | No | Creation timestamp |
| updated_at | DATETIME | Yes | Last modification |
| published_at | DATETIME | Yes | Publication timestamp |

#### `kaimo_documents` (Case Notes/Documents)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INT (PK) | No | Auto-increment primary key |
| case_id | INT (FK) | No | Reference to kaimo_cases |
| title | VARCHAR(255) | No | Document title |
| content | TEXT | No | Content (Markdown/HTML) |
| document_type | ENUM | No | 'aktenvermerk', 'bericht', 'protokoll', 'sonstiges' |
| document_date | DATE | Yes | Date of the document (fictitious) |
| sort_order | INT | No | Display order |
| created_at | DATETIME | No | Creation timestamp |

#### `kaimo_categories` (Assessment Categories)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INT (PK) | No | Auto-increment primary key |
| name | VARCHAR(100) | No | Internal name |
| display_name | VARCHAR(255) | No | Display name |
| description | TEXT | Yes | Category description |
| icon | VARCHAR(10) | Yes | Category icon |
| color | VARCHAR(20) | Yes | Accent color |
| sort_order | INT | No | Order |
| is_default | BOOLEAN | No | Default categories for new cases |

**Default categories (from KAIMo prototype):**

1. **Basic care of the young person**
   - Physical health of the child
   - Mental health of the child
   - Medication and substance use of the child
   - Supervision / care situation of the child

2. **Developmental situation of the young person**
   - Biography of the child (incl. youth welfare measures)
   - Social behavior / social contacts of the child
   - Sexual development of the child
   - Education and performance area of the child

3. **Family situation**
   - Living situation
   - Economic situation (incl. employment)
   - Family relationships (incl. domestic violence)

4. **Parents / Legal guardians**
   - Biography of the legal guardians
   - Health of the legal guardians
   - Well-being of the legal guardians
   - Social behavior / social contacts of the legal guardians

#### `kaimo_subcategories` (Subcategories for Assessment Matrix)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INT (PK) | No | Auto-increment primary key |
| category_id | INT (FK) | No | Reference to kaimo_categories |
| name | VARCHAR(100) | No | Internal name |
| display_name | VARCHAR(255) | No | Display name |
| description | TEXT | Yes | Description |
| sort_order | INT | No | Order within the category |
| is_default | BOOLEAN | No | Default subcategories |

#### `kaimo_hints` (Hints from Documents)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INT (PK) | No | Auto-increment primary key |
| case_id | INT (FK) | No | Reference to kaimo_cases |
| document_id | INT (FK) | Yes | Reference to kaimo_documents (source) |
| content | TEXT | No | Hint text |
| expected_category_id | INT (FK) | Yes | Expected main category (model solution) |
| expected_subcategory_id | INT (FK) | Yes | Expected subcategory (model solution) |
| expected_rating | ENUM | Yes | 'risk', 'resource', 'unclear' (model solution) |
| sort_order | INT | No | Order |
| created_at | DATETIME | No | Creation timestamp |

#### `kaimo_case_categories` (n:m Case <-> Categories)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INT (PK) | No | Auto-increment primary key |
| case_id | INT (FK) | No | Reference to kaimo_cases |
| category_id | INT (FK) | No | Reference to kaimo_categories |
| sort_order | INT | No | Order within the case |

#### `kaimo_ai_content` (Texts - AI Preparation)

!!! note "AI Preparation"
    This table is prepared for future AI integration. In phases 1-5, all content is entered manually (`is_generated = false`).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INT (PK) | No | Auto-increment primary key |
| case_id | INT (FK) | No | Reference to kaimo_cases |
| content_type | ENUM | No | 'summary', 'consequences', 'plausibility' |
| content | TEXT | No | Content |
| is_generated | BOOLEAN | No | Manual (false) or AI-generated (true, for later) |
| generated_at | DATETIME | Yes | Generation timestamp (for AI, later) |
| created_at | DATETIME | No | Creation timestamp |
| updated_at | DATETIME | Yes | Last edit |

#### `kaimo_user_assessments` (User Assessments)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INT (PK) | No | Auto-increment primary key |
| case_id | INT (FK) | No | Reference to kaimo_cases |
| user_id | VARCHAR(255) | No | Authentik user ID |
| username | VARCHAR(255) | No | Username for display |
| status | ENUM | No | 'in_progress', 'completed' |
| final_verdict | ENUM | Yes | 'inconclusive', 'not_endangered', 'endangered' |
| final_comment | TEXT | Yes | Reasoning for the assessment |
| started_at | DATETIME | No | Start of processing |
| completed_at | DATETIME | Yes | Completion of processing |
| duration_seconds | INT | Yes | Processing duration |

**Final verdict options (as in the prototype):**

- `inconclusive` = "A conclusive assessment is not possible"
- `not_endangered` = "The welfare of [child] is not endangered"
- `endangered` = "The welfare of [child] is endangered"

#### `kaimo_hint_assignments` (Hint Assignments by Users)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INT (PK) | No | Auto-increment primary key |
| assessment_id | INT (FK) | No | Reference to kaimo_user_assessments |
| hint_id | INT (FK) | No | Reference to kaimo_hints |
| assigned_category_id | INT (FK) | Yes | Assigned main category |
| assigned_subcategory_id | INT (FK) | Yes | Assigned subcategory |
| rating | ENUM | Yes | 'risk', 'resource', 'unclear' |
| assigned_at | DATETIME | No | Timestamp of assignment |

#### `kaimo_case_permissions` (Case Permissions)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INT (PK) | No | Auto-increment primary key |
| case_id | INT (FK) | No | Reference to kaimo_cases |
| user_id | VARCHAR(255) | Yes | Individual user (or NULL for group) |
| group_name | VARCHAR(100) | Yes | Group name (or NULL for individual user) |
| granted_by | VARCHAR(255) | No | Who granted access |
| granted_at | DATETIME | No | Timestamp of grant |

### Relationship Diagram

```
                    ┌─────────────────────┐
                    │    kaimo_cases      │
                    │  (Case Vignettes)   │
                    └─────────┬───────────┘
                              │
    ┌───────────┬─────────────┼─────────────┬──────────────┬──────────────┐
    │           │             │             │              │              │
    ▼           ▼             ▼             ▼              ▼              ▼
┌────────┐ ┌────────┐ ┌──────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐
│kaimo_  │ │kaimo_  │ │kaimo_case_   │ │kaimo_ai_   │ │kaimo_case_ │ │kaimo_    │
│docs    │ │hints   │ │categories    │ │content     │ │permissions │ │user_     │
│        │ │        │ │(n:m)         │ │(AI-ready)  │ │            │ │assess-   │
└────────┘ └───┬────┘ └──────┬───────┘ └────────────┘ └────────────┘ │ments     │
               │             │                                       └─────┬────┘
               │             ▼                                             │
               │    ┌─────────────────┐                                    │
               │    │kaimo_categories │                                    │
               │    └────────┬────────┘                                    │
               │             │                                             │
               │             ▼                                             │
               │    ┌─────────────────┐                                    │
               │    │kaimo_           │                                    │
               │    │subcategories    │◄───────────────────────────────────┤
               │    └─────────────────┘                                    │
               │                                                           │
               └───────────────────────────────────────────────────────────┤
                                                                           │
                                                              ┌────────────┴───────────┐
                                                              │ kaimo_hint_assignments │
                                                              │ (User Assignments)     │
                                                              └────────────────────────┘
```

---

## API Design

### KAIMO Admin Panel API

#### `GET /api/kaimo/admin/cases`

**Description:** List of all cases for Researchers

**Permission:** `admin:kaimo:manage`

**Response:**
```json
{
  "success": true,
  "cases": [
    {
      "id": 1,
      "name": "fall-malaika",
      "display_name": "Case Malaika",
      "description": "Child endangerment involving a girl (8 years old)",
      "status": "published",
      "icon": "👧",
      "color": "#e91e63",
      "document_count": 5,
      "hint_count": 12,
      "assessment_count": 8,
      "created_by": "researcher1",
      "created_at": "2025-11-29T10:00:00Z",
      "published_at": "2025-11-29T12:00:00Z"
    }
  ],
  "total": 1
}
```

---

#### `POST /api/kaimo/admin/cases`

**Description:** Create a new case

**Permission:** `admin:kaimo:manage`

**Request:**
```json
{
  "name": "fall-malaika",
  "display_name": "Case Malaika",
  "description": "Child endangerment involving a girl (8 years old)",
  "icon": "👧",
  "color": "#e91e63",
  "categories": [1, 2, 3, 4]
}
```

**Response:**
```json
{
  "success": true,
  "case": {
    "id": 1,
    "name": "fall-malaika",
    "display_name": "Case Malaika",
    "status": "draft"
  }
}
```

---

#### `PUT /api/kaimo/admin/cases/<id>`

**Description:** Edit a case

**Permission:** `admin:kaimo:manage`

---

#### `DELETE /api/kaimo/admin/cases/<id>`

**Description:** Delete a case (only if no assessments exist or force=true)

**Permission:** `admin:kaimo:manage`

---

#### `POST /api/kaimo/admin/cases/<id>/publish`

**Description:** Publish a case

**Permission:** `admin:kaimo:manage`

---

#### `POST /api/kaimo/admin/cases/<id>/documents`

**Description:** Add a document to a case

**Permission:** `admin:kaimo:manage`

**Request:**
```json
{
  "title": "Case note from 15.03.2024",
  "content": "**Home visit at the M. family**\n\nPresent were...",
  "document_type": "aktenvermerk",
  "document_date": "2024-03-15"
}
```

---

#### `POST /api/kaimo/admin/cases/<id>/hints`

**Description:** Add a hint to a case

**Permission:** `admin:kaimo:manage`

**Request:**
```json
{
  "content": "Child shows signs of malnutrition",
  "document_id": 1,
  "expected_category_id": 1,
  "expected_rating": "risk"
}
```

---

#### `POST /api/kaimo/admin/cases/<id>/content`

**Description:** Manually set text content (summary, impact assessment, plausibility)

**Permission:** `admin:kaimo:manage`

**Request:**
```json
{
  "content_type": "summary",
  "content": "The case shows multiple signs of..."
}
```

!!! note "AI Preparation"
    The API endpoint is prepared for future AI generation. A `generate: true` parameter can be added later.

---

#### `GET /api/kaimo/admin/cases/<id>/results`

**Description:** Aggregated results of a case

**Permission:** `admin:kaimo:results`

**Response:**
```json
{
  "success": true,
  "case_id": 1,
  "total_assessments": 8,
  "completed_assessments": 6,
  "average_duration_seconds": 1250,
  "final_ratings": {
    "risk": 4,
    "resource": 1,
    "unclear": 1
  },
  "hint_accuracy": {
    "correct_category": 0.78,
    "correct_rating": 0.65
  },
  "per_hint_results": [
    {
      "hint_id": 1,
      "hint_content": "Child shows signs of...",
      "expected_category": "Basic care",
      "expected_rating": "risk",
      "assignments": {
        "Basic care": 5,
        "Developmental situation": 1
      },
      "ratings": {
        "risk": 5,
        "unclear": 1
      }
    }
  ]
}
```

---

### KAIMO User Panel API

#### `GET /api/kaimo/cases`

**Description:** List of cases shared with the user

**Permission:** `feature:kaimo:view`

**Response:**
```json
{
  "success": true,
  "cases": [
    {
      "id": 1,
      "display_name": "Case Malaika",
      "description": "Child endangerment involving a girl (8 years old)",
      "icon": "👧",
      "color": "#e91e63",
      "document_count": 5,
      "hint_count": 12,
      "my_status": "not_started",
      "estimated_duration_minutes": 30
    }
  ]
}
```

---

#### `GET /api/kaimo/cases/<id>`

**Description:** Case details for processing

**Permission:** `feature:kaimo:view`

**Response:**
```json
{
  "success": true,
  "case": {
    "id": 1,
    "display_name": "Case Malaika",
    "description": "...",
    "documents": [
      {
        "id": 1,
        "title": "Case note from 15.03.2024",
        "content": "...",
        "document_type": "aktenvermerk",
        "document_date": "2024-03-15"
      }
    ],
    "categories": [
      {
        "id": 1,
        "display_name": "Basic care",
        "icon": "🍎",
        "color": "#4caf50"
      }
    ],
    "hints": [
      {
        "id": 1,
        "content": "Child shows signs of malnutrition",
        "source_document_id": 1
      }
    ]
  },
  "my_assessment": {
    "id": 1,
    "status": "in_progress",
    "hint_assignments": [
      {
        "hint_id": 1,
        "assigned_category_id": 1,
        "rating": "risk"
      }
    ]
  }
}
```

---

#### `POST /api/kaimo/cases/<id>/start`

**Description:** Start processing a case

**Permission:** `feature:kaimo:edit`

**Response:**
```json
{
  "success": true,
  "assessment_id": 1,
  "started_at": "2025-11-29T14:00:00Z"
}
```

---

#### `PUT /api/kaimo/assessments/<id>/hints/<hint_id>`

**Description:** Save hint assignment

**Permission:** `feature:kaimo:edit`

**Request:**
```json
{
  "assigned_category_id": 1,
  "rating": "risk"
}
```

---

#### `POST /api/kaimo/assessments/<id>/complete`

**Description:** Complete assessment

**Permission:** `feature:kaimo:edit`

**Request:**
```json
{
  "final_rating": "risk",
  "final_comment": "Based on the multiple indications of..."
}
```

---

## Frontend Design

### Component Structure

```
llars-frontend/src/components/KAIMo/
├── KAIMoOverview.vue              # Case overview (tiles)
├── KAIMoCase.vue                  # Main container with 3 sections
│
├── case/                          # 3 main sections (like prototype)
│   ├── KAIMoDocuments.vue         # Section 1: Case file/documents
│   ├── KAIMoDiagram.vue           # Section 2: Hint assignment (diagram)
│   ├── KAIMoAssessment.vue        # Section 3: Case verdict (matrix + verdict)
│   ├── KAIMoSidebar.vue           # Left sidebar with 3 icons
│   └── KAIMoHintAssignment.vue    # Dialog for hint assignment
│
├── documents/
│   ├── KAIMoDocumentList.vue      # Document list (left)
│   ├── KAIMoDocumentViewer.vue    # Document content (right)
│   └── KAIMoDocumentSearch.vue    # Search + filter
│
├── assessment/
│   ├── KAIMoMatrix.vue            # Assessment matrix (categories x subcategories)
│   ├── KAIMoMatrixRow.vue         # A single row in the matrix
│   ├── KAIMoFinalVerdict.vue      # Final verdict (3 options)
│   └── KAIMoResults.vue           # Results display (after completion)
│
├── admin/
│   ├── KAIMoAdminOverview.vue     # Admin dashboard
│   ├── KAIMoCaseEditor.vue        # Create/edit case
│   ├── KAIMoDocumentEditor.vue    # Manage documents
│   ├── KAIMoHintEditor.vue        # Define hints
│   ├── KAIMoContentEditor.vue     # Manage texts (AI-ready)
│   ├── KAIMoCasePermissions.vue   # Manage permissions
│   └── KAIMoCaseResults.vue       # Aggregated results
│
└── shared/
    ├── KAIMoCategoryCard.vue      # Category card (in diagram)
    ├── KAIMoHintCard.vue          # Hint card (draggable)
    ├── KAIMoRatingButtons.vue     # Risk/Resource/Unclear buttons
    └── KAIMoProgressBar.vue       # Progress bar
```

---

### User Panel - Case Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  KAIMO - Case Vignettes                                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Available Cases                                                     │
│                                                                      │
│  ┌──────────────────────┐  ┌──────────────────────┐                 │
│  │ 👧 Case Malaika       │  │ 👦 Case Tim           │                 │
│  │                      │  │                      │                 │
│  │ Child endangerment   │  │ Neglect in the       │                 │
│  │ involving girl (8 y.)│  │ domestic environment  │                 │
│  │                      │  │                      │                 │
│  │ 📄 5 Documents        │  │ 📄 3 Documents        │                 │
│  │ 💡 22 Hints           │  │ 💡 15 Hints           │                 │
│  │ ⏱️ approx. 30 min.    │  │ ⏱️ approx. 20 min.    │                 │
│  │                      │  │                      │                 │
│  │ Status: Not started  │  │ Status: In progress  │                 │
│  │                      │  │ ████████░░ 80%       │                 │
│  │                      │  │                      │                 │
│  │ [Start case]         │  │ [Continue]           │                 │
│  └──────────────────────┘  └──────────────────────┘                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

### User Panel - 3 Main Sections (like KAIMo Prototype)

Case processing takes place in **3 main sections**, accessible via the left sidebar:

#### Section 1: Case File/Documents

```
┌────┬──────────────────────────────────────────────────────────────────┐
│    │  🔍 Text search        [Features ▼] [Actors ▼]                   │
│ 📄 ├──────────────────────────────────────────────────────────────────┤
│    │                                                                  │
│ 📊 │  ┌────────────────┐  ┌────────────────────────────────────────┐ │
│    │  │ DOCUMENTS      │  │ Report of a possible                   │ │
│ ⚖️ │  │                │  │ child endangerment                     │ │
│    │  │ ▶ Report       │  │                        Fri, 03.02.2023 │ │
│    │  │   03.02.2023   │  │                                        │ │
│    │  │                │  │ Type of report:                        │ │
│    │  │ ○ Phone call   │  │ Call to youth welfare office            │ │
│    │  │   Teacher      │  │                                        │ │
│    │  │   06.02.2023   │  │ Information about the child:           │ │
│    │  │                │  │ Malaika Boukari, 8 years old,          │ │
│    │  │ ○ Home visit   │  │ residing: Regenbogenstraße 7...        │ │
│    │  │   07.02.2023   │  │                                        │ │
│    │  │                │  │ Information about the mother:          │ │
│    │  │ ○ Meeting      │  │ Inaya Boukari, 43 years old...         │ │
│    │  │   Office       │  │                                        │ │
│    │  │   16.02.2023   │  │ Information about the situation:       │ │
│    │  │                │  │ The daughter of the caller and          │ │
│    │  │                │  │ Malaika would together...              │ │
│    │  └────────────────┘  └────────────────────────────────────────┘ │
│    │                                                                  │
└────┴──────────────────────────────────────────────────────────────────┘
```

#### Section 2: Hint Assignment (Diagram View)

```
┌────┬──────────────────────────────────────────────────────────────────┐
│    │                                                                  │
│ 📄 │     ┌─────────────────────┐         ┌─────────────────────┐     │
│    │     │ Basic care          │         │ Family situation    │     │
│ 📊 │     │ 8 Open hints        │         │ 6 Open hints        │     │
│    │     │ 🔴 0  🟢 0  ⚪ 0    │         │ 🔴 0  🟢 0  ⚪ 0    │     │
│ ⚖️ │     └─────────────────────┘         └─────────────────────┘     │
│    │                                                                  │
│    │                      ┌─────────┐                                │
│    │                      │ Malaika │                                │
│    │                      └─────────┘                                │
│    │                                                                  │
│    │     ┌─────────────────────┐         ┌─────────────────────┐     │
│    │     │ Development         │         │ Parents             │     │
│    │     │ 5 Open hints        │         │ 3 Open hints        │     │
│    │     │ 🔴 0  🟢 0  ⚪ 0    │         │ 🔴 0  🟢 0  ⚪ 0    │     │
│    │     └─────────────────────┘         └─────────────────────┘     │
│    │                                                                  │
└────┴──────────────────────────────────────────────────────────────────┘
```

Clicking on a category opens the detail view with hints to assign.

#### Section 3: Case Verdict (Matrix + Verdict)

```
┌────┬──────────────────────────────────────────────────────────────────┐
│    │  Final Case Verdict                               [📂 File]    │
│ 📄 ├──────────────────────────────────────────────────────────────────┤
│    │                                                                  │
│ 📊 │  ┌─────────────────────────────────────┐  ┌──────────────────┐  │
│    │  │ ASSESSMENT MATRIX                   │  │ VERDICT          │  │
│ ⚖️ │  │                                     │  │                  │  │
│    │  │           │ Risk   │ Resource  │ ?  │  │ Select your      │  │
│    │  │ ──────────┼────────┼───────────┼────│  │ verdict:         │  │
│    │  │ BASIC CARE                          │  │                  │  │
│    │  │ Physical  │   ●    │           │    │  │ ○ Assessment     │  │
│    │  │ Health    │        │           │    │  │   not possible   │  │
│    │  │ Mental    │        │     ●     │    │  │                  │  │
│    │  │ Health    │        │           │    │  │ ○ Welfare not    │  │
│    │  │ Supervis. │        │           │  ● │  │   endangered     │  │
│    │  │ ──────────┼────────┼───────────┼────│  │                  │  │
│    │  │ DEVELOPMENT                         │  │ ○ Welfare        │  │
│    │  │ Biography │   ●    │           │    │  │   endangered     │  │
│    │  │ Social b. │        │     ●     │    │  │                  │  │
│    │  │ ...       │        │           │    │  │                  │  │
│    │  │                                     │  │ [Complete]       │  │
│    │  └─────────────────────────────────────┘  └──────────────────┘  │
│    │                                                                  │
└────┴──────────────────────────────────────────────────────────────────┘
```

---

### Admin Panel - Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  KAIMO Admin                                      [+ New Case]       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐        │
│  │ 3          │ │ 2          │ │ 1          │ │ 15         │        │
│  │ Total      │ │ Published  │ │ Draft      │ │ Completed  │        │
│  │ Cases      │ │            │ │            │ │ Assessments│        │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘        │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Name          │ Status      │ Documents │ Assessments │ Actions │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │ 👧 Malaika     │ ✓ Published │ 5         │ 8/10 (80%)  │ ⚙️ 📊 🗑️ │ │
│  │ 👦 Tim         │ ✓ Published │ 3         │ 3/10 (30%)  │ ⚙️ 📊 🗑️ │ │
│  │ 👶 Leon        │ 📝 Draft    │ 2         │ -           │ ⚙️ 🗑️    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  Legend: ⚙️ Edit  📊 Results  🗑️ Delete                               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Admin Panel - Case Editor

```
┌─────────────────────────────────────────────────────────────────────┐
│  ← Back                          Edit Case: Malaika                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ General │ Documents │ Hints │ Texts │ Permissions │ Results      ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  GENERAL DATA                                                        │
│                                                                      │
│  Name (internal):                       Icon:                        │
│  ┌────────────────────────────────┐      ┌──────┐                   │
│  │ fall-malaika                   │      │ 👧   │                   │
│  └────────────────────────────────┘      └──────┘                   │
│                                                                      │
│  Display name:                          Color:                       │
│  ┌────────────────────────────────┐      ┌──────┐                   │
│  │ Case Malaika                   │      │██████│ #e91e63           │
│  └────────────────────────────────┘      └──────┘                   │
│                                                                      │
│  Description:                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Child endangerment involving an 8-year-old girl.               ││
│  │ The case covers aspects of neglect and...                      ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  Categories for this case:                                           │
│  ☑ Basic care  ☑ Development  ☑ Family  ☑ Parents                   │
│                                                                      │
│  Status: 📝 Draft                                                    │
│                                                                      │
│                    [Save]          [Publish]                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Routing

### User Panel Routes

| Route | Component | Permission |
|-------|-----------|------------|
| `/kaimo` | KAIMoOverview | `feature:kaimo:view` |
| `/kaimo/:id` | KAIMoCase | `feature:kaimo:view` |
| `/kaimo/:id/results` | KAIMoResults | `feature:kaimo:view` |

### Admin Panel Routes

| Route | Component | Permission |
|-------|-----------|------------|
| `/admin/kaimo` | KAIMoAdminOverview | `admin:kaimo:manage` |
| `/admin/kaimo/new` | KAIMoCaseEditor | `admin:kaimo:manage` |
| `/admin/kaimo/:id/edit` | KAIMoCaseEditor | `admin:kaimo:manage` |
| `/admin/kaimo/:id/results` | KAIMoCaseResults | `admin:kaimo:results` |

---

## Implementation Plan

### Phase 1: Database & Base API (Priority: High)

- [ ] Create database tables (migration)
- [ ] Define SQLAlchemy models
- [ ] Seed default categories
- [ ] Insert permission keys into DB
- [ ] Base CRUD API for cases

**Effort:** 8-12h

### Phase 2: Admin Panel - Case Management (Priority: High)

- [ ] KAIMoAdminOverview.vue
- [ ] KAIMoCaseEditor.vue (general data)
- [ ] KAIMoDocumentEditor.vue
- [ ] KAIMoHintEditor.vue
- [ ] API endpoints for documents and hints

**Effort:** 16-24h

### Phase 3: User Panel - Case Processing (Priority: High)

- [ ] KAIMoOverview.vue (case overview)
- [ ] KAIMoCase.vue (main view)
- [ ] KAIMoHintBoard.vue (drag & drop)
- [ ] KAIMoDocumentViewer.vue
- [ ] API for assessments and assignments

**Effort:** 20-30h

### Phase 4: Assessment & Completion (Priority: High)

- [ ] KAIMoRatingPanel.vue
- [ ] KAIMoFinalAssessment.vue
- [ ] KAIMoResults.vue
- [ ] API for finalization

**Effort:** 10-16h

### Phase 5: Admin - Results, Texts & Permissions (Priority: Medium)

- [ ] KAIMoCaseResults.vue (aggregation)
- [ ] KAIMoContentEditor.vue (manual text input, AI-ready)
- [ ] KAIMoCasePermissions.vue
- [ ] Export functions (CSV/Excel)

**Effort:** 14-20h

---

## Total Effort

| Phase | Effort (Hours) |
|-------|----------------|
| Phase 1: DB & Base API | 8-12h |
| Phase 2: Admin Panel | 16-24h |
| Phase 3: User Panel | 20-30h |
| Phase 4: Assessment | 10-16h |
| Phase 5: Results & Texts | 14-20h |
| **Total** | **68-102h** |

---

## AI Integration (Future)

!!! info "Prepared for future implementation"
    The following components are prepared in the database schema and API but will only be implemented in a later phase.

**Prepared infrastructure:**

- Table `kaimo_ai_content` with `is_generated` and `generated_at` fields
- API endpoint `/api/kaimo/admin/cases/<id>/content` extensible with `generate: true`
- `KAIMoContentEditor.vue` can later be extended with an "Generate with AI" button

**Future AI features (Phase 6+):**

- [ ] LLM integration for summaries
- [ ] AI-generated impact assessment
- [ ] Automatic plausibility check
- [ ] Streaming support for LLM responses

**Estimated additional effort:** 16-24h

---

## Open Questions

- [ ] Should Evaluators be able to compare their own completed results with the model solution?
- [ ] How granular should permissions be? (Individual users vs. groups vs. all)
- [ ] Should there be a time limit for case processing?

---

## Approval

| Reviewer | Date | Status |
|----------|------|--------|
| Philipp Steigerwald | 2025-11-29 | Pending |
