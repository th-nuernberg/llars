# Error Handling Migration Guide

**Status:** ✅ Error handler extended with custom exception classes
**Date:** 2025-12-07
**Target:** Standardize all LLARS backend routes to use `@handle_api_errors` decorator

## Overview

The LLARS backend now has a standardized error handling system using the `@handle_api_errors` decorator and custom exception classes. This guide shows how to migrate existing routes.

## Available Exception Classes

Located in `/app/decorators/error_handler.py`:

```python
from decorators.error_handler import (
    handle_api_errors,
    APIError,           # Base: Custom status code
    NotFoundError,      # 404
    ValidationError,    # 400
    UnauthorizedError,  # 401
    ForbiddenError,     # 403
    ConflictError       # 409
)
```

## Migration Pattern

### Pattern 1: Simple 404 Check

**BEFORE:**
```python
@bp.route('/items/<int:id>')
@require_permission('feature:items:view')
def get_item(id):
    item = Item.query.get(id)
    if not item:
        return jsonify({'success': False, 'error': 'Item not found'}), 404
    return jsonify({'success': True, 'item': item.to_dict()})
```

**AFTER:**
```python
@bp.route('/items/<int:id>')
@require_permission('feature:items:view')
@handle_api_errors(logger_name='items')
def get_item(id):
    item = Item.query.get(id)
    if not item:
        raise NotFoundError(f'Item {id} not found')
    return jsonify({'success': True, 'item': item.to_dict()})
```

### Pattern 2: Validation Errors

**BEFORE:**
```python
@bp.route('/items', methods=['POST'])
@require_permission('feature:items:edit')
def create_item():
    data = request.get_json() or {}
    name = data.get('name')

    if not name:
        return jsonify({'success': False, 'error': 'name is required'}), 400

    item = Item(name=name)
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'item': item.to_dict()}), 201
```

**AFTER:**
```python
@bp.route('/items', methods=['POST'])
@require_permission('feature:items:edit')
@handle_api_errors(logger_name='items')
def create_item():
    data = request.get_json() or {}
    name = data.get('name')

    if not name:
        raise ValidationError('name is required')

    item = Item(name=name)
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'item': item.to_dict()}), 201
```

### Pattern 3: Conflict (Duplicate) Errors

**BEFORE:**
```python
@bp.route('/cases', methods=['POST'])
def create_case():
    data = request.get_json() or {}
    name = data.get('name')

    existing = Case.query.filter_by(name=name).first()
    if existing:
        return jsonify({'success': False, 'error': 'Case with this name already exists'}), 400

    # ... create case
```

**AFTER:**
```python
@bp.route('/cases', methods=['POST'])
@handle_api_errors(logger_name='cases')
def create_case():
    data = request.get_json() or {}
    name = data.get('name')

    existing = Case.query.filter_by(name=name).first()
    if existing:
        raise ConflictError('Case with this name already exists')

    # ... create case
```

### Pattern 4: Try/Except Blocks

**BEFORE:**
```python
@bp.route('/documents/upload', methods=['POST'])
@require_permission('feature:rag:edit')
def upload_document():
    try:
        file = request.files['file']
        # ... processing logic
        return jsonify({'success': True}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error uploading: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
```

**AFTER:**
```python
@bp.route('/documents/upload', methods=['POST'])
@require_permission('feature:rag:edit')
@handle_api_errors(logger_name='documents')
def upload_document():
    file = request.files.get('file')
    if not file:
        raise ValidationError('No file provided')

    # ... processing logic
    # Decorator handles exceptions automatically
    return jsonify({'success': True}), 201
```

### Pattern 5: Multiple Error Types

**BEFORE:**
```python
@bp.route('/sessions/<int:id>/start', methods=['POST'])
def start_session(id):
    try:
        session = Session.query.get(id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404

        if session.status != 'created':
            return jsonify({'error': 'Invalid session status'}), 400

        # ... start logic
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**AFTER:**
```python
@bp.route('/sessions/<int:id>/start', methods=['POST'])
@handle_api_errors(logger_name='sessions')
def start_session(id):
    session = Session.query.get(id)
    if not session:
        raise NotFoundError(f'Session {id} not found')

    if session.status != 'created':
        raise ValidationError(f'Cannot start session with status {session.status}')

    # ... start logic (decorator handles unexpected errors)
    return jsonify({'success': True})
```

## Response Format

All errors now return a consistent format:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_type": "not_found|validation_error|unauthorized|forbidden|conflict|internal_error",
  "details": {  // Optional, if provided
    "field": "email",
    "expected": "valid email format"
  }
}
```

## Migration Checklist

For each route file:

1. ✅ Add imports:
   ```python
   from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError, ConflictError
   ```

2. ✅ Add decorator to each route:
   ```python
   @handle_api_errors(logger_name='module_name')
   ```

3. ✅ Replace error returns with exceptions:
   - `return jsonify({..., 'error': ...}), 404` → `raise NotFoundError(...)`
   - `return jsonify({..., 'error': ...}), 400` → `raise ValidationError(...)`
   - `return jsonify({..., 'error': ...}), 409` → `raise ConflictError(...)`

4. ✅ Remove try/except blocks (unless specific handling needed):
   - Keep business logic clean
   - Let decorator handle logging and responses

5. ✅ Test the endpoint to ensure:
   - Error responses have correct status codes
   - Error messages are clear
   - Logs are generated properly

## Files to Migrate (Priority Order)

### High Priority (Most Error Handling)
- [x] `/app/decorators/error_handler.py` - Extended with custom exceptions
- [ ] `/app/routes/kaimo/kaimo_admin_routes.py` - 19 endpoints, many validations
- [ ] `/app/routes/rag/document_routes.py` - 10 endpoints, file handling
- [ ] `/app/routes/crawler/crawler_routes.py` - 8 endpoints, complex logic
- [ ] `/app/routes/judge/session_routes.py` - Session management

### Medium Priority
- [ ] `/app/routes/rag/collection_routes.py` - 8 try/except blocks
- [ ] `/app/routes/rag/admin_routes.py` - 2 try/except blocks
- [ ] `/app/routes/rag/search_routes.py` - 4 try/except blocks
- [ ] `/app/routes/judge/kia_sync_routes.py` - 4 try/except blocks
- [ ] `/app/routes/scenarios/*.py` - Multiple scenario routes

### Already Done ✅
- `/app/routes/chatbot/chatbot_routes.py` - Already uses `@handle_errors`

## Benefits

1. **Consistency**: All errors follow same format
2. **Less Boilerplate**: No repetitive try/except blocks
3. **Better Logging**: Automatic error logging with context
4. **Type Safety**: Clear exception hierarchy
5. **Debugging**: Stack traces in logs for 500 errors
6. **Frontend**: Predictable error structure for UI

## Example: Complete Migration

**File:** `/app/routes/kaimo/kaimo_admin_routes.py`

```python
# Add imports
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError, ConflictError

# Migrate endpoint
@kaimo_admin_bp.route('/cases/<int:case_id>', methods=['DELETE'])
@require_permission('admin:kaimo:manage')
@handle_api_errors(logger_name='kaimo_admin')
def delete_case(case_id: int):
    """Delete a KAIMO case."""
    case = KaimoCase.query.get(case_id)
    if not case:
        raise NotFoundError("Case not found")

    force = request.args.get('force', 'false').lower() == 'true'
    assessment_count = KaimoUserAssessment.query.filter_by(case_id=case_id).count()

    if assessment_count > 0 and not force:
        raise ValidationError(
            f"Case has {assessment_count} assessments. Use force=true to delete anyway."
        )

    db.session.delete(case)
    db.session.commit()

    return jsonify({"success": True, "case_id": case_id}), 200
```

## Notes

- Keep `@require_permission` decorator BEFORE `@handle_api_errors`
- Decorator order matters: Permission check happens first
- Use `raise ValueError(...)` for simple validation (auto-converted to 400)
- Use `raise KeyError(...)` for missing fields (auto-converted to 400)
- Custom exceptions are preferred for clarity

## Testing

After migration, test each endpoint:

```bash
# Test 404
curl -X GET http://localhost:55080/api/cases/99999 \
  -H "Authorization: Bearer $TOKEN"

# Test 400 validation
curl -X POST http://localhost:55080/api/cases \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'

# Test 409 conflict
curl -X POST http://localhost:55080/api/cases \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "existing-case"}'
```

Expected response format:
```json
{
  "success": false,
  "error": "Clear error message",
  "error_type": "not_found"
}
```
