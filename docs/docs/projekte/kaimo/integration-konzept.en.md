# KAIMo Integration in LLARS - Effort Analysis

## Initial Situation

**KAIMo** (AI assistance in child protection) is a demonstrator/training tool for professionals dealing with child welfare risk. The current prototype is a static Next.js app with a hard-coded case vignette ("Malaika").

**Goal:** KAIMo should evolve into a training tool for education and professional development, with the ability to create additional case vignettes.

**Integration:** KAIMo is integrated as a **tile in LLARS** - similar to existing features like mail rating, LLM-as-Judge, RAG pipeline, etc.

!!! success "Status (2026-02)"
    Variant B (LLARS integration) has been implemented. Admin and user panels are production-ready.
    The following variant sections remain as a historical effort assessment.

---

## KAIMo Scope (prototype)

The demonstrator consists of three core functions:

1. **Case file/documents** - display of notes and documents
2. **Hint assignment** - assign hints to categories:
   - Basic care of the child
   - Developmental situation
   - Family situation
   - Parents/guardians
3. **Case assessment** - risk/resource/unclear + final verdict

**AI functions (planned in prototype, but static):**
- Hint summary
- Consequence assessment
- Plausibility check

---

## Case 1: Manual HTML workflow

### Description
Instructors create vignettes and texts (summary, consequences, plausibility) in a Word template. A technical staff member inserts them into the demonstrator HTML.

### Tasks

| Task | Description | Effort |
|------|-------------|--------|
| Start page extension | New Vue component with case selection tiles | 4-8h |
| LLARS integration | New route `/kaimo`, navigation, permission `feature:kaimo:view` | 2-4h |
| Document structure | Define JSON schema for vignettes | 2-4h |
| Static hosting | Store JSON files in frontend | 1-2h |
| Case loader | Component to load and render JSON | 4-8h |
| Styling | Integrate KAIMo design into LLARS theme | 4-8h |
| **Documentation** | Word template for instructors | 2-4h |

### Total effort (Case 1)
**19-38 hours (approx. 2.5-5 days)**

### Pros
- Fastest implementation
- No backend changes
- Works immediately

### Cons
- Technical know-how needed for HTML/JSON
- Error-prone manual maintenance
- No central management
- No versioning of cases

---

## Case 2: LLARS-based case management

### Description
Instructors manage cases and all texts via a LLARS admin UI. Data is stored in MariaDB and shown automatically in KAIMo.

### Tasks

| Task | Description | Effort |
|------|-------------|--------|
| **Backend** | | |
| DB schema | Tables: `kaimo_cases`, `kaimo_documents`, `kaimo_hints`, `kaimo_categories` | 4-8h |
| API routes | CRUD for cases, documents, hints | 8-16h |
| Permission integration | `feature:kaimo:view`, `feature:kaimo:edit`, `admin:kaimo:manage` | 2-4h |
| | | |
| **Frontend - Admin** | | |
| Case editor | Create/edit cases | 8-16h |
| Document editor | Rich-text editor for notes | 8-12h |
| Hint editor | Categorize and assign hints | 6-10h |
| AI text editor | Fields for summary/consequences/plausibility | 4-8h |
| | | |
| **Frontend - Application** | | |
| KAIMo start page | Case selection with preview | 4-8h |
| Case view | Dynamic rendering from DB data | 8-12h |
| Hint interaction | Drag&drop, categorization, rating | 8-16h |
| Result storage | Store user assessments in DB | 4-8h |
| | | |
| **Integration** | | |
| LLARS navigation | Tile on home dashboard | 2-4h |
| Styling/Theming | Dark/light mode compatibility | 4-8h |
| Testing | Unit + integration tests | 8-12h |

### Total effort (Case 2)
**78-142 hours (approx. 10-18 days)**

### Pros
- Central case management
- No technical knowledge needed for instructors
- Versioning possible
- User tracking (who assessed which case)
- Consistent UX with LLARS

### Cons
- Higher implementation effort
- AI texts still manual

---

## Case 3: LLARS + AI-generated content

### Description
Like Case 2, but AI generates the texts (summary, consequences, plausibility) and experts can edit them.

### Additional tasks (on top of Case 2)

| Task | Description | Effort |
|------|-------------|--------|
| **AI integration** | | |
| Prompt engineering | Prompts for summary/consequences/plausibility | 8-16h |
| LLM service | Integration via LiteLLM/Mistral (already in LLARS) | 4-8h |
| Generation API | Endpoint `/api/kaimo/generate/{type}` | 4-8h |
| Streaming support | Live output via Socket.IO | 4-8h |
| | | |
| **Frontend - AI** | | |
| Generation UI | "Generate with AI" button + loading | 4-6h |
| Streaming UI | Live text rendering | 4-6h |
| Edit workflow | Review and save generated texts | 4-8h |
| Regenerate | Re-generate text | 2-4h |
| | | |
| **Quality** | | |
| Prompt optimization | Iterative improvement | 8-16h |
| Validation | Domain review of AI texts | External |
| Fallback handling | LLM errors | 2-4h |

### Total effort (Case 3)
**Case 2 + 44-84 hours = 122-226 hours (approx. 15-28 days)**

### Pros
- Maximum automation
- Consistent text quality
- Fast case creation
- Reuse of LLARS LLM infrastructure

### Cons
- Highest implementation effort
- AI text quality must be validated
- Dependency on LLM availability
- Ethical considerations in child protection context

---

## LLARS Architecture for KAIMo (as of 2026-02)

### Current integration

```
LLARS Home Dashboard
└── KAIMo
    ├── /kaimo            - Hub / entry
    ├── /kaimo/panel      - Case overview
    ├── /kaimo/new        - New case (Admin)
    ├── /kaimo/edit/:id   - Edit case (Admin)
    └── /kaimo/:id        - Case work (Evaluator)
```

### Technical integration (current)

**Backend (Flask):**
```
app/routes/kaimo/
├── kaimo_admin_routes.py     # Admin API
├── kaimo_user_routes.py      # User API
└── __init__.py

app/services/kaimo/
├── kaimo_case_service.py
├── kaimo_document_service.py
├── kaimo_hint_service.py
├── kaimo_category_service.py
└── kaimo_export_service.py
```

**Frontend (Vue 3):**
```
llars-frontend/src/components/Kaimo/
├── KaimoHub.vue
├── KaimoPanel.vue
├── KaimoNewCase.vue
├── KaimoCaseEditor.vue
├── KaimoCase.vue
├── KaimoAssessmentView.vue
└── KaimoDocumentsView.vue
```

**Database (MariaDB):**
```sql
kaimo_cases
kaimo_documents
kaimo_hints
kaimo_categories
kaimo_subcategories
kaimo_case_categories
kaimo_user_assessments
kaimo_hint_assignments
kaimo_case_shares
kaimo_ai_content
```

**Permissions:**
```
feature:kaimo:view       -- View cases
feature:kaimo:edit       -- Submit assessments
admin:kaimo:manage       -- Create/edit cases
admin:kaimo:results      -- View results
```

---

## Recommendation

| Scenario | Recommended case | Reason |
|----------|------------------|--------|
| **Quick prototype** | Case 1 | Minimal effort, fast demo |
| **Production use** | Case 2 | Good balance of effort and benefit |
| **Long-term vision** | Case 3 | Maximum automation |
