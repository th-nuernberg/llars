---
name: code-review
description: Perform comprehensive code review on staged changes or specific files. Use when reviewing code quality, checking for bugs, ensuring best practices, or before committing changes.
---

# Code Review for LLARS

Perform a thorough code review following LLARS standards and best practices.

## Review Scope

Determine what to review:

1. **Staged changes** (default): `git diff --cached`
2. **Unstaged changes**: `git diff`
3. **Specific files**: User-provided file paths
4. **Branch comparison**: `git diff main...HEAD`

## Review Process

### Step 1: Gather Changes

```bash
# Get staged changes
git diff --cached --name-only

# Get full diff for review
git diff --cached
```

### Step 2: Apply Review Checklist

For each changed file, check:

#### Code Quality
- [ ] **Readability**: Is the code easy to understand?
- [ ] **Naming**: Are variables/functions named descriptively?
- [ ] **Complexity**: Can any logic be simplified?
- [ ] **DRY**: Is there code duplication that should be extracted?
- [ ] **Single Responsibility**: Does each function/class do one thing?

#### LLARS-Specific Standards
- [ ] **Backend Routes**: Use `@handle_api_errors`, `@authentik_required`, `@require_permission`
- [ ] **Frontend Components**: Use LLARS Design System (LBtn, LCard, LTag, etc.)
- [ ] **i18n**: All user-facing strings in `de.json` and `en.json`
- [ ] **No Over-Engineering**: Only implement what's needed
- [ ] **Delete Unused Code**: No commented-out code, no unused imports

#### Bug Detection
- [ ] **Edge Cases**: Are null/undefined/empty cases handled?
- [ ] **Error Handling**: Are errors caught and handled appropriately?
- [ ] **Type Safety**: Are types consistent and correct?
- [ ] **Race Conditions**: Any async issues?
- [ ] **Memory Leaks**: Event listeners cleaned up? Subscriptions unsubscribed?

#### Performance
- [ ] **N+1 Queries**: Database queries in loops?
- [ ] **Unnecessary Re-renders**: Missing useMemo/useCallback in Vue computed?
- [ ] **Large Payloads**: Fetching more data than needed?

#### Testing
- [ ] **Test Coverage**: Are new functions/components tested?
- [ ] **Test Quality**: Do tests cover edge cases?
- [ ] **Test Naming**: Clear test IDs following conventions (AUTH_, PERM_, etc.)

### Step 3: Generate Report

Format findings as:

```markdown
## Code Review Summary

### Files Reviewed
- `path/to/file1.py`
- `path/to/file2.vue`

### Issues Found

#### Critical (Must Fix)
1. **[file:line]** Description of critical issue
   - Why it's critical
   - Suggested fix

#### Warnings (Should Fix)
1. **[file:line]** Description of warning
   - Suggested improvement

#### Suggestions (Nice to Have)
1. **[file:line]** Description of suggestion

### What Looks Good
- Positive observation 1
- Positive observation 2

### Checklist Summary
- [x] Error handling: OK
- [ ] i18n: Missing translations in de.json
- [x] Tests: Coverage adequate
```

## File-Type Specific Checks

### Python (Backend)

```python
# Check for these patterns:

# Good: Proper error handling
@handle_api_errors(logger_name='my_module')
def my_route():
    if not item:
        raise NotFoundError(f'Item {id} not found')

# Bad: Generic exception, no logging
def my_route():
    try:
        ...
    except:
        return {'error': 'something went wrong'}, 500
```

**Check for:**
- `@handle_api_errors` on all routes
- Proper exception types (NotFoundError, ValidationError, etc.)
- No bare `except:` clauses
- f-strings over `.format()` or `%`
- Type hints on public functions

### Vue (Frontend)

```vue
<!-- Good: Using LLARS components -->
<LBtn variant="primary" @click="save">
  {{ $t('common.save') }}
</LBtn>

<!-- Bad: Raw Vuetify + hardcoded string -->
<v-btn color="primary" @click="save">
  Save
</v-btn>
```

**Check for:**
- LLARS components (LBtn, LCard, LTag) instead of raw Vuetify
- `$t()` for all user-facing text
- `usePermissions` for feature gating
- `ref`/`computed` usage (not reactive where not needed)
- Event cleanup in `onUnmounted`

### JavaScript/TypeScript

**Check for:**
- `async/await` over `.then()` chains
- Proper error handling in async functions
- No console.log in production code
- Optional chaining (`?.`) for nested access

## Quick Commands

```bash
# Review staged changes
git diff --cached

# Review changes on current branch vs main
git diff main...HEAD

# Show changed files only
git diff --cached --name-only

# Review specific file
git diff --cached -- path/to/file.py
```

## Output Format

After review, provide:

1. **Summary**: Overall assessment (Approved / Changes Requested / Needs Discussion)
2. **Issues**: Categorized by severity
3. **Action Items**: Clear next steps

---

## Integration with Commit

After a successful review with no critical issues:

```bash
# Stage any fixes made during review
git add -A

# Commit with review confirmation
git commit -m "$(cat <<'EOF'
<type>(<scope>): <description>

Reviewed-By: Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```
