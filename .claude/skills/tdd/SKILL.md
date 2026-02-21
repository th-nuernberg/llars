---
name: tdd
description: Test-Driven Development workflow for LLARS. Use when implementing new features with tests first, improving test coverage, or following TDD methodology.
---

# Test-Driven Development (TDD) for LLARS

Follow the Red-Green-Refactor cycle for implementing features with tests first.

## TDD Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    TDD Cycle                                 │
│                                                              │
│   1. RED      →   2. GREEN    →   3. REFACTOR   →   REPEAT  │
│   Write       →   Make it     →   Improve       →           │
│   failing     →   pass        →   code          →           │
│   test        →   (minimal)   →   quality       →           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Phase 1: RED - Write Failing Test

Write the test FIRST, before any implementation code.

**Backend (pytest):**
```python
# tests/unit/services/test_my_service.py
import pytest
from app.services.my_service import MyService

class TestMyService:
    """Tests for MyService."""

    def test_create_item_success(self, db_session):
        """MYSVC_001: Successfully creates an item with valid data."""
        # Arrange
        service = MyService(db_session)

        # Act
        result = service.create_item(name="Test Item", value=42)

        # Assert
        assert result is not None
        assert result.name == "Test Item"
        assert result.value == 42
        assert result.id is not None

    def test_create_item_empty_name_raises_error(self, db_session):
        """MYSVC_002: Raises ValidationError for empty name."""
        service = MyService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            service.create_item(name="", value=42)

        assert "name is required" in str(exc_info.value).lower()
```

**Frontend (Vitest):**
```javascript
// tests/components/MyComponent.spec.js
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import MyComponent from '@/components/MyComponent.vue'

describe('MyComponent', () => {
  it('MYCOMP_001: renders title from props', () => {
    const wrapper = mount(MyComponent, {
      props: { title: 'Test Title' }
    })

    expect(wrapper.text()).toContain('Test Title')
  })

  it('MYCOMP_002: emits save event with form data on submit', async () => {
    const wrapper = mount(MyComponent)

    await wrapper.find('input[name="name"]').setValue('Test')
    await wrapper.find('form').trigger('submit')

    expect(wrapper.emitted('save')).toBeTruthy()
    expect(wrapper.emitted('save')[0][0]).toEqual({ name: 'Test' })
  })
})
```

**Run and verify test fails:**
```bash
# Backend
pytest tests/unit/services/test_my_service.py -v

# Frontend
cd llars-frontend && npm run test:run -- tests/components/MyComponent.spec.js
```

### Phase 2: GREEN - Make Test Pass

Write the MINIMUM code to make the test pass. Don't optimize yet.

**Backend:**
```python
# app/services/my_service.py
from decorators.error_handler import ValidationError

class MyService:
    def __init__(self, session):
        self.session = session

    def create_item(self, name: str, value: int):
        if not name:
            raise ValidationError("Name is required")

        item = MyModel(name=name, value=value)
        self.session.add(item)
        self.session.commit()
        return item
```

**Frontend:**
```vue
<!-- components/MyComponent.vue -->
<template>
  <div>
    <h1>{{ title }}</h1>
    <form @submit.prevent="handleSubmit">
      <input name="name" v-model="formData.name" />
      <button type="submit">Save</button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({ title: String })
const emit = defineEmits(['save'])

const formData = ref({ name: '' })

const handleSubmit = () => {
  emit('save', { ...formData.value })
}
</script>
```

**Run and verify test passes:**
```bash
# Backend
pytest tests/unit/services/test_my_service.py -v

# Frontend
cd llars-frontend && npm run test:run -- tests/components/MyComponent.spec.js
```

### Phase 3: REFACTOR - Improve Code Quality

Now improve the code while keeping tests green:

- Extract common logic
- Improve naming
- Add documentation
- Optimize performance
- Apply LLARS patterns

**After each refactor, run tests to ensure nothing broke.**

## LLARS Test Standards

### Test ID Conventions

| Prefix | Area | Example |
|--------|------|---------|
| `AUTH_` | Authentication | `AUTH_001: login with valid credentials` |
| `PERM_` | Permissions | `PERM_001: admin can access admin routes` |
| `SVC_` | Services | `SVC_USER_001: creates user successfully` |
| `ROUTE_` | API Routes | `ROUTE_API_001: returns 200 for valid request` |
| `COMP_` | Components | `COMP_BTN_001: renders with primary variant` |

### Test File Organization

```
tests/
├── unit/
│   ├── services/
│   │   └── test_my_service.py
│   └── routes/
│       └── test_my_routes.py
├── integration/
│   └── test_my_feature_integration.py
└── conftest.py  # Shared fixtures

llars-frontend/
├── tests/
│   ├── components/
│   │   └── MyComponent.spec.js
│   └── composables/
│       └── useMyFeature.spec.js
```

### Coverage Requirements

Current targets (from CLAUDE.md):
- **Backend**: 50% (currently 21%)
- **Frontend**: 40% (currently 14%)

```bash
# Check coverage
pytest --cov=app tests/
cd llars-frontend && npm run test:coverage
```

## TDD Session Workflow

### 1. Start Session

```bash
# Create feature branch
git checkout -b feature/my-feature

# Review requirements and plan tests
# - What behaviors need to be tested?
# - What edge cases exist?
# - What errors should be handled?
```

### 2. Write Test List

Before coding, list all tests needed:

```markdown
## Tests for UserRegistration Feature

### Happy Path
- [ ] USERREG_001: Creates user with valid email and password
- [ ] USERREG_002: Returns user ID and confirmation

### Validation
- [ ] USERREG_003: Rejects empty email
- [ ] USERREG_004: Rejects invalid email format
- [ ] USERREG_005: Rejects password under 8 chars
- [ ] USERREG_006: Rejects duplicate email

### Edge Cases
- [ ] USERREG_007: Handles unicode in name
- [ ] USERREG_008: Trims whitespace from email
```

### 3. Iterate Through Tests

For each test:
1. Write test (RED)
2. Run test, confirm failure
3. Write minimal code (GREEN)
4. Run test, confirm pass
5. Refactor if needed
6. Run test, confirm still passes
7. Commit

```bash
# After each test passes
git add -A
git commit -m "test(backend): add USERREG_001 - create user with valid data"
```

### 4. Complete Feature

```bash
# Run full test suite
pytest tests/
cd llars-frontend && npm run test:run

# Check coverage
pytest --cov=app --cov-report=term-missing tests/

# Commit final implementation
git add -A
git commit -m "feat(backend): implement user registration with full test coverage"
```

## Common Test Patterns

### Mocking in Python

```python
from unittest.mock import Mock, patch

def test_service_calls_external_api(self):
    """SVC_001: Service calls external API correctly."""
    with patch('app.services.my_service.requests.post') as mock_post:
        mock_post.return_value.json.return_value = {'status': 'ok'}

        result = MyService().call_api(data={'key': 'value'})

        mock_post.assert_called_once_with(
            'https://api.example.com',
            json={'key': 'value'}
        )
        assert result['status'] == 'ok'
```

### Mocking in JavaScript

```javascript
import { vi } from 'vitest'
import axios from 'axios'

vi.mock('axios')

it('COMP_001: fetches data on mount', async () => {
  axios.get.mockResolvedValue({ data: [{ id: 1, name: 'Test' }] })

  const wrapper = mount(MyComponent)
  await flushPromises()

  expect(axios.get).toHaveBeenCalledWith('/api/items')
  expect(wrapper.text()).toContain('Test')
})
```

### Testing Vue Components with i18n

```javascript
import { createI18n } from 'vue-i18n'

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: { common: { save: 'Save' } }
  }
})

const wrapper = mount(MyComponent, {
  global: {
    plugins: [i18n]
  }
})
```

### Testing API Routes

```python
import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app('testing')
    with app.test_client() as client:
        yield client

def test_get_items_returns_list(client, auth_headers):
    """ROUTE_001: GET /api/items returns list of items."""
    response = client.get('/api/items', headers=auth_headers)

    assert response.status_code == 200
    assert isinstance(response.json, list)
```

## Quick Commands

```bash
# Run single test file
pytest tests/unit/services/test_my_service.py -v

# Run tests matching pattern
pytest -k "test_create" -v

# Run with coverage for specific module
pytest --cov=app.services.my_service tests/unit/services/test_my_service.py

# Frontend: Run specific test
npm run test:run -- tests/components/MyComponent.spec.js

# Frontend: Run in watch mode
npm run test -- tests/components/MyComponent.spec.js

# Frontend: Update snapshots
npm run test:run -- -u
```

## TDD Benefits for LLARS

1. **Documentation**: Tests document expected behavior
2. **Confidence**: Refactor without fear of breaking things
3. **Design**: Forces thinking about API before implementation
4. **Coverage**: Naturally builds test coverage
5. **CI/CD**: Tests catch regressions in pipeline
