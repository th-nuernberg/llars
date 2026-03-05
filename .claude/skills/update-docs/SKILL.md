---
name: update-docs
description: Audit and fix MkDocs documentation pages. Checks all pages for correctness, DE/EN consistency, broken links, and outdated content. Use when user mentions docs audit, documentation update, mkdocs check, or wants to verify documentation quality.
---

# Update Docs - MkDocs Documentation Audit & Fix

Systematically audit all MkDocs documentation pages and fix issues found.

## Scope

The LLARS docs live at `docs/docs/` with MkDocs Material theme and i18n plugin:
- **German** (default): `filename.md`
- **English**: `filename.en.md`
- **Config**: `docs/mkdocs.yml` (nav structure, i18n settings)

## Audit Process

### Phase 1: Inventory

1. Read `docs/mkdocs.yml` to get the full nav structure and page list
2. Count total pages and identify all sections

### Phase 2: Systematic Audit

For each page in the nav, check:

#### Content Correctness
- [ ] Factual accuracy against codebase (CLAUDE.md is the reference)
- [ ] Version numbers / dates are current
- [ ] Code examples match actual implementation
- [ ] API endpoints, permissions, and config values are correct
- [ ] No placeholder content (lorem ipsum, TODO, `github.com/your-repo`)

#### DE/EN Consistency
- [ ] Both `.md` and `.en.md` versions exist
- [ ] Both have matching structure (same sections, same tables)
- [ ] No significant content gaps (EN missing sections that DE has, or vice versa)
- [ ] Version numbers match between DE and EN

#### Links
- [ ] Internal links resolve to existing files
- [ ] Relative paths are correct (e.g., `../../entwickler/` not `../docs/entwickler/`)
- [ ] Links use `.md` extension (not `.en.md` - i18n plugin resolves language)
- [ ] Nav translations in mkdocs.yml cover all EN menu items

#### Formatting
- [ ] ASCII art tables are properly aligned
- [ ] Mermaid diagrams have valid syntax
- [ ] Code blocks have correct language annotations
- [ ] MkDocs admonitions use correct syntax (`!!! note`, `!!! warning`, etc.)

### Phase 3: Prioritize & Fix

Categorize findings by severity:

| Severity | Definition | Examples |
|----------|------------|---------|
| **Critical** | Wrong information, missing EN file, broken functionality | Incorrect API docs, missing translations, wrong version |
| **Medium** | Incomplete content, outdated info | Missing sections in EN, stale dates |
| **Low** | Cosmetic, minor inconsistencies | Link style, ASCII art alignment, missing cross-refs |

Fix order: Critical first, then Medium, then Low.

## Parallel Audit Strategy

Use subagents to audit sections in parallel. Recommended batching:

```
Agent 1: getting-started/ + guides/
Agent 2: entwickler/ (developer docs)
Agent 3: agentic-ai/ + projekte/
Agent 4: testing/ + archive/
```

Each agent should:
1. Read every page in its section (both DE and EN)
2. Cross-reference content against CLAUDE.md and actual code
3. Report issues with file path, line number, severity, and description

## Key References for Validation

| Topic | Reference |
|-------|-----------|
| Architecture | CLAUDE.md "Architektur" section |
| Test users | CLAUDE.md: admin, researcher, evaluator, chatbot_manager (all pw: admin123) |
| Permissions | CLAUDE.md "Permission System" section |
| Evaluation types | CLAUDE.md: ranking(1), rating(2), mail_rating(3), comparison(4), authenticity(5), labeling(7) |
| LLM models | CLAUDE.md "LLM Modelle" section |
| CI/CD | CLAUDE.md "GitLab CI/CD" section |
| Deployment | CLAUDE.md + scripts/ci/*.sh |
| Design System | CLAUDE.md "LLARS Design System" (35 L-components) |
| Frontend stack | Vue 3.4 + Vuetify 3.5 + Vite 5.1 + Socket.IO |
| Backend stack | Flask 3.0 + MariaDB 11.2 + ChromaDB |

## Common Issues Found in Previous Audits

| Issue | How to Fix |
|-------|-----------|
| EN version shorter than DE | Translate missing sections from DE |
| Wrong citation/author | Cross-check against actual paper DOI |
| Stale version/date in header | Update to current version from CLAUDE.md |
| Missing test user in setup docs | Add chatbot_manager (pw: admin123, role: chatbot_manager) |
| Links with `../docs/` prefix | Remove extra `docs/` - use `../../entwickler/` etc. |
| EN links with `.en.md` | Change to `.md` - i18n plugin auto-resolves |
| Missing "See Also" cross-refs | Add links to related pages in same section |
| Missing umlauts (encoding) | Rewrite file with proper UTF-8 characters |
| Missing nav_translations | Add English menu item in mkdocs.yml i18n section |
| Placeholder links | Replace `github.com/your-repo` with real reference |

## Output Format

After audit, produce a report:

```markdown
## Documentation Audit Report

**Pages audited:** X / Y
**Issues found:** Z (C critical, M medium, L low)

### Critical Issues
1. **[file.md:line]** Description - How to fix

### Medium Issues
1. **[file.md:line]** Description - How to fix

### Low Issues
1. **[file.md:line]** Description - How to fix
```

Then proceed to fix all issues, starting with critical.

## MkDocs i18n Plugin Notes

- Default language: `de` (German)
- English suffix: `.en.md`
- Nav translations go in `plugins > i18n > languages > en > nav_translations`
- Links between pages should always use `.md` (not `.en.md`)
- The plugin auto-resolves links to the correct language version
- If an EN page is missing, the DE version is shown as fallback

## File Encoding

All `.md` files must be UTF-8 with proper Unicode characters:
- German umlauts: ae=ä, oe=ö, ue=ü, ss=ß
- If a file has broken umlauts, rewrite the entire file with correct encoding
