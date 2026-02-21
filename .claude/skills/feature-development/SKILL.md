---
name: feature-development
description: Guide for developing new features in LLARS. Use when creating new components, adding features, or needing guidance on code standards, i18n, tests, design system, and project conventions.
---

# Feature Development Guide for LLARS

This guide covers everything you need to know when developing new features for LLARS.

## Quick Checklist

Before submitting a feature, ensure:

- [ ] **i18n**: All user-facing text in `de.json` and `en.json`
- [ ] **Tests**: Unit tests for new components/services
- [ ] **Design**: Using LLARS Design System components (LBtn, LCard, etc.)
- [ ] **Error Handling**: Backend uses `@handle_api_errors`, frontend handles errors gracefully
- [ ] **Permissions**: Routes protected with `@require_permission` decorator
- [ ] **No Over-Engineering**: Only implement what's requested

---

## 1. Internationalization (i18n)

### Pflicht / Required

ALL user-facing text MUST be translated. Never hardcode strings.

### Locale Files

```
llars-frontend/src/locales/
├── de.json    # German (primary)
└── en.json    # English
```

### Usage in Vue Components

```vue
<template>
  <!-- In templates -->
  <span>{{ $t('common.save') }}</span>
  <LBtn>{{ $t('promptEngineering.testPrompt.run') }}</LBtn>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// In script
const message = t('errors.notFound')
</script>
```

### Adding New Translations

1. **Find the correct section** in both `de.json` and `en.json`
2. **Use nested keys** for organization: `"feature.section.key"`
3. **Add to BOTH files** - missing translations cause errors

Example structure:
```json
{
  "myFeature": {
    "title": "Mein Feature",
    "actions": {
      "save": "Speichern",
      "delete": "Löschen"
    },
    "errors": {
      "notFound": "Nicht gefunden"
    }
  }
}
```

### Interpolation

```json
// de.json
"greeting": "Hallo {name}, du hast {count} Nachrichten"

// Usage
$t('greeting', { name: 'Max', count: 5 })
```

---

## 2. LLARS Design System

### Core Components

Always use LLARS components instead of raw Vuetify:

| Instead of | Use |
|------------|-----|
| `<v-btn>` | `<LBtn>` |
| `<v-card>` | `<LCard>` |
| `<v-chip>` | `<LTag>` |
| `<v-tabs>` | `<LTabs>` |
| Custom tooltips | `<LTooltip>` |
| Action buttons | `<LActionGroup>` |

### LBtn Variants

```vue
<LBtn variant="primary">Hauptaktion</LBtn>
<LBtn variant="secondary">Sekundär</LBtn>
<LBtn variant="accent">Hervorhebung</LBtn>
<LBtn variant="danger">Löschen</LBtn>
<LBtn variant="cancel">Abbrechen</LBtn>
<LBtn variant="text">Text-Button</LBtn>
```

### LCard Usage

```vue
<LCard title="Titel" icon="mdi-robot" color="#b0ca97">
  <template #header>
    <!-- Custom header content -->
  </template>

  <!-- Card body -->

  <template #actions>
    <LBtn variant="primary">OK</LBtn>
  </template>
</LCard>
```

### Color Palette

| Name | Hex | Usage |
|------|-----|-------|
| Primary | `#b0ca97` | Main actions, branding |
| Secondary | `#D1BC8A` | Secondary elements |
| Accent | `#88c4c8` | Highlights |
| Success | `#98d4bb` | Success states |
| Danger | `#e8a087` | Destructive actions |

### Signature Style: Asymmetric Border-Radius

```css
/* Buttons */
border-radius: 16px 4px 16px 4px;

/* Tags/Chips */
border-radius: 6px 2px 6px 2px;
```

### Viewport Layouts (Full-Screen Pages)

```css
.page-container {
  height: calc(100vh - 94px);  /* 64px AppBar + 30px Footer */
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-content {
  flex: 1;
  overflow-y: auto;  /* Only scroll here */
}
```

**Important**: Don't use `v-container` or `v-row` for viewport layouts!

---

## 3. Testing

### Requirement

Every new component/service MUST have tests.

### Backend Tests (pytest)

```bash
# Run all tests
pytest tests/

# With coverage
pytest --cov=app tests/

# Single file
pytest tests/unit/test_my_service.py -v
```

#### Test Structure

```python
import pytest
from app.services.my_service import MyService

class TestMyService:
    """Tests for MyService."""

    def test_create_item_success(self, db_session):
        """MYSERV_001: Successfully creates an item."""
        service = MyService(db_session)
        result = service.create_item(name="Test")

        assert result is not None
        assert result.name == "Test"

    def test_create_item_validation_error(self, db_session):
        """MYSERV_002: Raises ValidationError for empty name."""
        service = MyService(db_session)

        with pytest.raises(ValidationError):
            service.create_item(name="")
```

### Frontend Tests (Vitest)

```bash
cd llars-frontend

# Run tests
npm run test:run

# With coverage
npm run test:coverage

# Watch mode
npm run test
```

#### Test Structure

```javascript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import MyComponent from '@/components/MyComponent.vue'

describe('MyComponent', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  it('MYCOMP_001: renders title correctly', () => {
    const wrapper = mount(MyComponent, {
      props: { title: 'Test Title' }
    })

    expect(wrapper.text()).toContain('Test Title')
  })

  it('MYCOMP_002: emits event on button click', async () => {
    const wrapper = mount(MyComponent)

    await wrapper.find('button').trigger('click')

    expect(wrapper.emitted('submit')).toBeTruthy()
  })
})
```

### Test ID Conventions

| Prefix | Area |
|--------|------|
| `AUTH_` | Authentication |
| `PERM_` | Permissions |
| `COMP_BTN_` | Button components |
| `SVC_` | Services |
| `ROUTE_` | API routes |

### Common Mocks

```javascript
// Axios
vi.mock('axios', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() }
}))

// localStorage
vi.stubGlobal('localStorage', {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn()
})

// Vue Router
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  useRoute: () => ({ params: {}, query: {} })
}))

// i18n
vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key) => key })
}))
```

---

## 4. Backend Development

### Route Structure

```python
from flask import Blueprint, request, g
from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError

bp = Blueprint('my_feature', __name__, url_prefix='/api/my-feature')

@bp.route('/', methods=['GET'])
@authentik_required
@require_permission('feature:my_feature:view')
@handle_api_errors(logger_name='my_feature')
def list_items():
    """List all items."""
    user = g.authentik_user
    items = MyService.get_all(user_id=user.id)
    return jsonify([item.to_dict() for item in items])

@bp.route('/<int:item_id>', methods=['GET'])
@authentik_required
@require_permission('feature:my_feature:view')
@handle_api_errors(logger_name='my_feature')
def get_item(item_id):
    """Get single item."""
    item = MyService.get_by_id(item_id)
    if not item:
        raise NotFoundError(f'Item {item_id} not found')
    return jsonify(item.to_dict())

@bp.route('/', methods=['POST'])
@authentik_required
@require_permission('feature:my_feature:edit')
@handle_api_errors(logger_name='my_feature')
def create_item():
    """Create new item."""
    data = request.get_json()
    if not data.get('name'):
        raise ValidationError('Name is required')

    item = MyService.create(data, user_id=g.authentik_user.id)
    return jsonify(item.to_dict()), 201
```

### Error Handling

Always use `@handle_api_errors` decorator:

```python
from decorators.error_handler import (
    handle_api_errors,
    NotFoundError,      # 404
    ValidationError,    # 400
    ConflictError,      # 409
    ForbiddenError      # 403
)

@handle_api_errors(logger_name='my_module')
def my_route():
    if not found:
        raise NotFoundError('Resource not found')
    if invalid:
        raise ValidationError('Invalid input')
```

### Service Layer Pattern

```python
# app/services/my_service.py
from db import get_db_session

class MyService:
    """Service for my feature business logic."""

    @staticmethod
    def get_all(user_id: int) -> list:
        """Get all items for user."""
        session = get_db_session()
        return session.query(MyModel).filter_by(user_id=user_id).all()

    @staticmethod
    def create(data: dict, user_id: int) -> MyModel:
        """Create new item."""
        session = get_db_session()
        item = MyModel(
            name=data['name'],
            user_id=user_id
        )
        session.add(item)
        session.commit()
        return item
```

### Permissions

Permission format: `feature:<feature_name>:<action>`

Actions: `view`, `edit`, `delete`, `admin`

```python
@require_permission('feature:prompts:view')    # Read access
@require_permission('feature:prompts:edit')    # Write access
@require_permission('feature:prompts:admin')   # Admin access
```

---

## 5. Frontend Development

### Component Structure

```vue
<template>
  <div class="my-component">
    <!-- Template content -->
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { usePermissions } from '@/composables/usePermissions'

// Props
const props = defineProps({
  title: {
    type: String,
    required: true
  }
})

// Emits
const emit = defineEmits(['update', 'delete'])

// Composables
const { t } = useI18n()
const { hasPermission } = usePermissions()

// State
const isLoading = ref(false)
const items = ref([])

// Computed
const filteredItems = computed(() =>
  items.value.filter(item => item.active)
)

// Methods
const loadItems = async () => {
  isLoading.value = true
  try {
    const response = await axios.get('/api/items')
    items.value = response.data
  } catch (error) {
    console.error('Failed to load items:', error)
  } finally {
    isLoading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadItems()
})
</script>

<style scoped>
.my-component {
  /* Component styles */
}
</style>
```

### Permission Checks

```vue
<template>
  <!-- Conditional rendering -->
  <LBtn v-if="hasPermission('feature:items:edit')" @click="edit">
    {{ $t('common.edit') }}
  </LBtn>

  <!-- Disabled state -->
  <LBtn :disabled="!hasPermission('feature:items:delete')" @click="deleteItem">
    {{ $t('common.delete') }}
  </LBtn>
</template>

<script setup>
import { usePermissions } from '@/composables/usePermissions'

const { hasPermission } = usePermissions()
</script>
```

### API Calls

```javascript
import axios from 'axios'

// GET
const fetchItems = async () => {
  const response = await axios.get('/api/items')
  return response.data
}

// POST
const createItem = async (data) => {
  const response = await axios.post('/api/items', data)
  return response.data
}

// PUT
const updateItem = async (id, data) => {
  const response = await axios.put(`/api/items/${id}`, data)
  return response.data
}

// DELETE
const deleteItem = async (id) => {
  await axios.delete(`/api/items/${id}`)
}
```

### Composables Pattern

```javascript
// src/composables/useMyFeature.js
import { ref, computed } from 'vue'
import axios from 'axios'

export function useMyFeature() {
  const items = ref([])
  const isLoading = ref(false)
  const error = ref(null)

  const fetchItems = async () => {
    isLoading.value = true
    error.value = null
    try {
      const response = await axios.get('/api/my-feature')
      items.value = response.data
    } catch (e) {
      error.value = e.message
    } finally {
      isLoading.value = false
    }
  }

  const itemCount = computed(() => items.value.length)

  return {
    items,
    isLoading,
    error,
    fetchItems,
    itemCount
  }
}
```

---

## 6. Code Quality Rules

### Don't Over-Engineer

- Only implement what's requested
- No extra features, refactoring, or "improvements"
- Simple solutions over clever ones
- Three similar lines > premature abstraction

### Don't Add Unless Needed

- No docstrings/comments for obvious code
- No feature flags for simple changes
- No backwards-compatibility shims
- No error handling for impossible scenarios

### Delete Unused Code

- Remove unused imports
- Delete commented-out code
- Remove unused variables (no `_var` renaming)
- No `// removed` comments

---

## 7. File Locations

### Backend

```
app/
├── routes/              # API endpoints
│   └── my_feature/
│       ├── __init__.py
│       └── my_routes.py
├── services/            # Business logic
│   └── my_service.py
├── db/
│   └── models/          # SQLAlchemy models
│       └── my_model.py
└── tests/
    └── unit/
        └── test_my_service.py
```

### Frontend

```
llars-frontend/src/
├── components/
│   └── MyFeature/
│       ├── MyComponent.vue
│       └── composables/
│           └── useMyFeature.js
├── views/
│   └── MyFeature/
│       └── MyFeatureView.vue
├── locales/
│   ├── de.json
│   └── en.json
└── tests/
    └── components/
        └── MyComponent.spec.js
```

---

## 8. Git Commits

### Format

```bash
git commit -m "$(cat <<'EOF'
<type>(<scope>): <description>

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `test`: Adding tests
- `docs`: Documentation
- `chore`: Maintenance

### Scopes

- `frontend`, `backend`
- Feature names: `auth`, `judge`, `rag`, `prompts`, etc.

### Examples

```
feat(frontend): add dark mode toggle to settings
fix(backend): handle null values in ranking calculation
test(prompts): add unit tests for variable extraction
refactor(rag): simplify embedding service interface
```

---

## 9. Common Patterns

### Dialog Component

```vue
<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    max-width="600"
    persistent
  >
    <LCard>
      <template #header>
        <div class="d-flex align-center justify-space-between w-100">
          <span class="text-h6">{{ $t('myFeature.dialog.title') }}</span>
          <v-btn icon variant="text" @click="close">
            <LIcon>mdi-close</LIcon>
          </v-btn>
        </div>
      </template>

      <!-- Content -->

      <template #actions>
        <LBtn variant="cancel" @click="close">
          {{ $t('common.cancel') }}
        </LBtn>
        <LBtn variant="primary" @click="save" :loading="isSaving">
          {{ $t('common.save') }}
        </LBtn>
      </template>
    </LCard>
  </v-dialog>
</template>

<script setup>
const props = defineProps({
  modelValue: Boolean
})

const emit = defineEmits(['update:modelValue'])

const close = () => emit('update:modelValue', false)
</script>
```

### List with Actions

```vue
<template>
  <v-list>
    <v-list-item v-for="item in items" :key="item.id">
      <v-list-item-title>{{ item.name }}</v-list-item-title>

      <template #append>
        <LActionGroup
          :actions="['view', 'edit', 'delete']"
          @action="handleAction($event, item)"
        />
      </template>
    </v-list-item>
  </v-list>
</template>
```

---

## Summary

1. **i18n**: All text in locale files, both DE and EN
2. **Design**: Use LBtn, LCard, LTag, etc.
3. **Tests**: Required for all new code
4. **Backend**: Use decorators for auth, permissions, errors
5. **Frontend**: Use composables pattern, check permissions
6. **Quality**: Don't over-engineer, delete unused code
7. **Git**: Semantic commits with type and scope
