# KAIMo Integration

!!! success "Status: Implemented (Beta, as of February 2026)"
    KAIMo is integrated in LLARS and ready for use. Admin and user panels are available.

## Overview

KAIMo (AI‑assisted analysis and modeling) is a training tool for professionals dealing with child welfare risk. In LLARS it is implemented with two panels:

- **KAIMO Admin Panel** (for researchers): create cases, manage documents/hints, review results
- **KAIMO Panel** (for evaluators): work through cases, assign hints, submit assessments

## Documentation

| Document | Description | Status |
|----------|-------------|--------|
| [Panel Concept](konzept.md) | Detailed concept with admin/evaluator split | Reference |
| [Request Assessment](anfrage-einschaetzung.md) | Historic options assessment | Archive |
| [Integration Concept](integration-konzept.md) | Technical analysis + architecture | Updated |

## Roles and Permissions

| Role | Panel | Permissions |
|------|-------|-------------|
| **Researcher** | Admin Panel | Create/edit cases, view results |
| **Evaluator** | User Panel | Work cases, submit assessments |

### Permissions

```
feature:kaimo:view       # See KAIMO area
feature:kaimo:edit       # Submit assessments
admin:kaimo:manage       # Manage cases (Admin)
admin:kaimo:results      # View results (Admin)
```

## Core Features (current)

### Admin Panel (Researcher)

1. **Create cases** - New case vignettes (draft/published)
2. **Manage documents** - case notes, reports, protocols
3. **Define hints** - hints + expected category/rating
4. **Manage categories** - standard categories + subcategories
5. **Analyze results** - aggregated outcomes and exports
6. **Share/Import/Export** - share cases, JSON export/import

### User Panel (Evaluator)

1. **Work cases** - read documents, analyze hints
2. **Assign hints** - categories + rating (risk/resource/unclear)
3. **Final verdict** - overall assessment with reasoning
4. **Progress tracking** - status and overview per case

## Implementation (as of Feb 2026)

- Backend: `/api/kaimo` admin + user routes, services, models, seeders
- Frontend: `/kaimo` hub, panel, case editor, assessment view
- Permissions: `feature:kaimo:*`, `admin:kaimo:*`

## Historical Effort Estimate

| Component | Effort |
|-----------|--------|
| Database & API | 8-12h |
| Admin Panel | 16-24h |
| User Panel | 20-30h |
| Assessment & Results | 24-36h |
| **Total** | **68-102h** |

!!! info "AI integration (optional)"
    The infrastructure supports later AI integration. Estimated extra effort: 16-24h

## Historical Next Steps (concept phase)

1. Concept review
2. Phase 1 implementation (DB & base API)
3. Phase 2-5 without AI integration
4. Add AI features later (optional)
