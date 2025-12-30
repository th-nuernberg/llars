# LLARS Testkonzept

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Inhaltsverzeichnis

1. [Einführung & Teststrategie](#1-einführung--teststrategie)
2. [Testing-Pyramide](#2-testing-pyramide)
3. [Tool-Stack & Setup](#3-tool-stack--setup)
4. [Unit Tests](#4-unit-tests)
5. [Integration Tests](#5-integration-tests)
6. [End-to-End Tests](#6-end-to-end-tests)
7. [Spezial-Tests](#7-spezial-tests)
8. [CI/CD Integration](#8-cicd-integration)
9. [Implementierungs-Roadmap](#9-implementierungs-roadmap)

---

## 1. Einführung & Teststrategie

### 1.1 Ziele

- **Stabilität**: Regression verhindern bei Änderungen
- **Vertrauen**: Schnelles Deployment ohne manuelle Tests
- **Dokumentation**: Tests als lebende Spezifikation
- **Qualität**: Bugs früh im Entwicklungszyklus finden

### 1.2 Architektur-Übersicht (Test-relevant)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         LLARS Architektur                           │
├─────────────────────────────────────────────────────────────────────┤
│  Frontend (Vue 3)          │  Backend (Flask 3.0)                   │
│  ├── Components (25+)      │  ├── Routes (38 Blueprints)            │
│  ├── Composables (15+)     │  ├── Services (40+ Module)             │
│  ├── Services (6+)         │  ├── Models (20+ DB-Modelle)           │
│  └── Socket.IO Client      │  └── Socket.IO Server (12 Namespaces)  │
├─────────────────────────────────────────────────────────────────────┤
│  External Services                                                  │
│  ├── MariaDB 11.2 (Hauptdatenbank)                                  │
│  ├── ChromaDB (Vector Store)                                        │
│  ├── Redis 7 (Session Storage)                                      │
│  ├── Authentik (OIDC Auth)                                          │
│  ├── YJS Server (Collaborative Editing)                             │
│  └── LiteLLM Proxy (LLM Gateway)                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 Kritische Pfade

| Priorität | Feature | Risiko | Test-Fokus |
|-----------|---------|--------|------------|
| 🔴 P0 | Authentication | Login/Logout bricht System | Unit + Integration |
| 🔴 P0 | Permission System | Unbefugter Zugriff | Unit + Integration |
| 🔴 P0 | RAG Pipeline | Daten-Inkonsistenz | Integration + E2E |
| 🟠 P1 | LLM-as-Judge | Evaluation-Ergebnisse falsch | Integration |
| 🟠 P1 | Chatbot Builder | Wizard-State verloren | Integration |
| 🟠 P1 | Rating/Ranking | Bewertungen inkonsistent | Unit + E2E |
| 🟡 P2 | Collaborative Editing | Sync-Konflikte | Spezial (CRDT) |
| 🟡 P2 | Socket.IO Events | Real-time Updates fehlen | Integration |

---

## 2. Testing-Pyramide

```
                    ┌───────────────┐
                   │    E2E Tests   │  ← 10-15% (langsam, teuer)
                   │   (Playwright)  │     Kritische User Journeys
                  ├─────────────────┤
                 │ Integration Tests │  ← 25-30% (mittel)
                │    (Pytest + DB)    │     API, DB, Services
               ├──────────────────────┤
              │      Unit Tests        │  ← 55-65% (schnell, günstig)
             │   (Pytest + Vitest)      │     Funktionen, Komponenten
            └────────────────────────────┘
```

### 2.1 Verteilung nach Bereichen

| Bereich | Unit | Integration | E2E |
|---------|------|-------------|-----|
| Backend Auth | 15 | 8 | 2 |
| Backend Services | 50 | 20 | - |
| Backend Routes | 30 | 40 | - |
| Database Models | 25 | 10 | - |
| Frontend Components | 40 | - | - |
| Frontend Composables | 20 | - | - |
| Socket.IO | 10 | 15 | 5 |
| User Journeys | - | - | 20 |
| **Gesamt** | **190** | **93** | **27** |

---

## 3. Tool-Stack & Setup

### 3.1 Backend Testing

```bash
# Installation
pip install pytest pytest-flask pytest-cov pytest-asyncio pytest-mock factory-boy

# Zusätzlich für spezielle Tests
pip install pytest-socket    # Socket-Isolation
pip install pytest-xdist     # Parallel Tests
pip install pytest-timeout   # Timeout für hängende Tests
pip install freezegun        # Time Mocking
pip install responses        # HTTP Mocking
```

**requirements-test.txt**:
```
pytest==8.3.4
pytest-flask==1.3.0
pytest-cov==6.0.0
pytest-asyncio==0.24.0
pytest-mock==3.14.0
pytest-socket==0.7.0
pytest-xdist==3.5.0
pytest-timeout==2.3.1
factory-boy==3.3.1
freezegun==1.4.0
responses==0.25.3
flask-testing==0.8.1
```

### 3.2 Frontend Testing

```bash
cd llars-frontend

# Installation
npm install -D vitest @vitest/coverage-v8 @vue/test-utils happy-dom
npm install -D @testing-library/vue @testing-library/user-event
npm install -D msw  # API Mocking

# Optional für Browser Mode (empfohlen für 2025)
npm install -D @vitest/browser playwright vitest-browser-vue
```

**vitest.config.js**:
```javascript
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'url'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'happy-dom',
    include: ['src/**/*.{test,spec}.{js,ts,vue}'],
    exclude: ['node_modules', 'dist'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/**/*.{js,ts,vue}'],
      exclude: ['src/**/*.test.{js,ts}', 'src/**/*.spec.{js,ts}']
    },
    setupFiles: ['./src/test/setup.js']
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
})
```

### 3.3 E2E Testing

```bash
# Playwright (empfohlen für LLARS)
npm install -D @playwright/test
npx playwright install

# Alternativ: Cypress
npm install -D cypress
```

**playwright.config.ts**:
```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 60000,
  retries: 2,
  workers: process.env.CI ? 2 : 4,
  reporter: [['html'], ['json', { outputFile: 'test-results.json' }]],

  use: {
    baseURL: 'http://localhost:55080',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } }
  ],

  // LLARS via Docker Compose starten
  webServer: {
    command: 'docker compose up -d && sleep 30',
    url: 'http://localhost:55080',
    reuseExistingServer: !process.env.CI,
    timeout: 120000
  }
})
```

### 3.4 Verzeichnisstruktur

```
llars/
├── tests/                          # Backend Tests
│   ├── conftest.py                 # Gemeinsame Fixtures
│   ├── unit/                       # Unit Tests
│   │   ├── auth/
│   │   │   ├── test_decorators.py
│   │   │   └── test_token_validation.py
│   │   ├── services/
│   │   │   ├── test_permission_service.py
│   │   │   ├── test_ranking_service.py
│   │   │   └── test_embedding_model_service.py
│   │   ├── models/
│   │   │   ├── test_user.py
│   │   │   ├── test_rag_document.py
│   │   │   └── test_judge_session.py
│   │   └── workers/
│   │       ├── test_embedding_worker.py
│   │       └── test_judge_worker_pool.py
│   ├── integration/                # Integration Tests
│   │   ├── test_auth_flow.py
│   │   ├── test_rag_pipeline.py
│   │   ├── test_chatbot_wizard.py
│   │   ├── test_judge_system.py
│   │   └── test_socket_events.py
│   └── fixtures/                   # Test-Daten
│       ├── users.json
│       ├── documents/
│       └── scenarios.json
│
├── llars-frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── __tests__/          # Component Tests
│   │   ├── composables/
│   │   │   └── __tests__/          # Composable Tests
│   │   └── test/
│   │       ├── setup.js            # Test Setup
│   │       └── mocks/              # API Mocks
│   └── vitest.config.js
│
├── e2e/                            # E2E Tests (Playwright)
│   ├── auth.spec.ts
│   ├── rating-workflow.spec.ts
│   ├── chatbot-creation.spec.ts
│   ├── judge-session.spec.ts
│   └── fixtures/
│       └── test-users.ts
│
└── docker-compose.test.yml         # Test-Umgebung
```

---

## 4. Unit Tests

### 4.1 Backend Unit Tests

#### 4.1.1 Fixture-Konfiguration (conftest.py)

```python
# tests/conftest.py
import pytest
from flask import Flask
from app.main import create_app
from app.db.db import db as _db
from app.db.models import User, Role, Permission
from unittest.mock import MagicMock, patch
import os

@pytest.fixture(scope='session')
def app():
    """Test-Flask-App mit SQLite in-memory"""
    os.environ['TESTING'] = 'true'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

    app = create_app(testing=True)
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'AUTHENTIK_DISABLED': True,  # Auth für Unit Tests deaktivieren
    })

    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()

@pytest.fixture(scope='function')
def db(app):
    """Frische DB pro Test"""
    with app.app_context():
        _db.session.begin_nested()
        yield _db
        _db.session.rollback()

@pytest.fixture
def client(app):
    """Test-Client"""
    return app.test_client()

@pytest.fixture
def auth_headers():
    """Mock-Auth-Header für authentifizierte Requests"""
    return {'Authorization': 'Bearer mock-token-for-testing'}

@pytest.fixture
def mock_authentik_user(db):
    """Gemockter Authentik User"""
    user = User(
        username='test_user',
        email='test@llars.local',
        is_active=True
    )
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def admin_user(db):
    """Admin User für Tests"""
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin', description='Administrator')
        db.session.add(admin_role)

    user = User(username='admin_test', email='admin@llars.local', is_active=True)
    user.roles.append(admin_role)
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def researcher_user(db):
    """Researcher User für Tests"""
    researcher_role = Role.query.filter_by(name='researcher').first()
    if not researcher_role:
        researcher_role = Role(name='researcher', description='Researcher')
        db.session.add(researcher_role)

    user = User(username='researcher_test', email='researcher@llars.local', is_active=True)
    user.roles.append(researcher_role)
    db.session.add(user)
    db.session.commit()
    return user
```

#### 4.1.2 Auth Decorator Tests

```python
# tests/unit/auth/test_decorators.py
import pytest
from unittest.mock import patch, MagicMock
from flask import g
from app.auth.decorators import authentik_required, get_or_create_user

class TestAuthentikRequired:
    """Tests für @authentik_required Decorator"""

    def test_missing_auth_header_returns_401(self, client):
        """Request ohne Auth-Header wird abgelehnt"""
        response = client.get('/api/users/me')
        assert response.status_code == 401
        assert 'error' in response.json

    def test_invalid_token_returns_401(self, client):
        """Ungültiger Token wird abgelehnt"""
        response = client.get(
            '/api/users/me',
            headers={'Authorization': 'Bearer invalid-token'}
        )
        assert response.status_code == 401

    @patch('app.auth.decorators.validate_token')
    def test_valid_token_sets_g_user(self, mock_validate, client, mock_authentik_user):
        """Gültiger Token setzt g.authentik_user"""
        mock_validate.return_value = {
            'sub': mock_authentik_user.username,
            'email': mock_authentik_user.email
        }

        with client.session_transaction():
            response = client.get(
                '/api/users/me',
                headers={'Authorization': 'Bearer valid-token'}
            )

        assert response.status_code == 200

    @patch('app.auth.decorators.validate_token')
    def test_expired_token_returns_401(self, mock_validate, client):
        """Abgelaufener Token wird abgelehnt"""
        mock_validate.side_effect = Exception("Token expired")

        response = client.get(
            '/api/users/me',
            headers={'Authorization': 'Bearer expired-token'}
        )
        assert response.status_code == 401


class TestGetOrCreateUser:
    """Tests für get_or_create_user Funktion"""

    def test_creates_new_user_on_first_login(self, app, db):
        """Neuer User wird bei erstem Login erstellt"""
        with app.app_context():
            token_data = {
                'sub': 'new_user_123',
                'email': 'new@llars.local',
                'preferred_username': 'new_user',
                'name': 'New User'
            }

            user = get_or_create_user(token_data)

            assert user is not None
            assert user.username == 'new_user'
            assert user.email == 'new@llars.local'

    def test_returns_existing_user(self, app, db, mock_authentik_user):
        """Existierender User wird zurückgegeben"""
        with app.app_context():
            token_data = {
                'sub': mock_authentik_user.username,
                'email': mock_authentik_user.email,
                'preferred_username': mock_authentik_user.username
            }

            user = get_or_create_user(token_data)

            assert user.id == mock_authentik_user.id

    def test_new_user_gets_viewer_role(self, app, db):
        """Neuer User bekommt automatisch Viewer-Rolle"""
        with app.app_context():
            token_data = {
                'sub': 'viewer_user',
                'email': 'viewer@llars.local',
                'preferred_username': 'viewer_user'
            }

            user = get_or_create_user(token_data)
            role_names = [r.name for r in user.roles]

            assert 'viewer' in role_names

    def test_locked_user_returns_none(self, app, db, mock_authentik_user):
        """Gesperrter User wird nicht zurückgegeben"""
        with app.app_context():
            mock_authentik_user.account_status = 'locked'
            db.session.commit()

            token_data = {
                'sub': mock_authentik_user.username,
                'email': mock_authentik_user.email
            }

            # Sollte Exception werfen oder None zurückgeben
            with pytest.raises(Exception):
                get_or_create_user(token_data)
```

#### 4.1.3 Permission Service Tests

```python
# tests/unit/services/test_permission_service.py
import pytest
from app.services.permission_service import PermissionService
from app.db.models import User, Role, Permission, UserPermission, RolePermission

class TestPermissionService:
    """Tests für PermissionService"""

    @pytest.fixture
    def permission_service(self, app):
        with app.app_context():
            return PermissionService()

    def test_admin_has_all_permissions(self, permission_service, admin_user):
        """Admin hat alle Permissions"""
        assert permission_service.check_permission(admin_user, 'feature:any:action') is True
        assert permission_service.check_permission(admin_user, 'admin:users:delete') is True

    def test_viewer_has_limited_permissions(self, permission_service, db):
        """Viewer hat nur Lese-Permissions"""
        viewer = User(username='viewer', email='viewer@test.local', is_active=True)
        viewer_role = Role(name='viewer')
        viewer.roles.append(viewer_role)
        db.session.add(viewer)
        db.session.commit()

        assert permission_service.check_permission(viewer, 'feature:ranking:view') is True
        assert permission_service.check_permission(viewer, 'feature:ranking:edit') is False

    def test_deny_overrides_grant(self, permission_service, db, researcher_user):
        """Deny schlägt Grant (auch von Rolle)"""
        # Researcher-Rolle hat 'feature:ranking:edit' = granted
        # User bekommt direktes Deny
        deny_perm = UserPermission(
            user_id=researcher_user.id,
            permission='feature:ranking:edit',
            granted=False  # DENY
        )
        db.session.add(deny_perm)
        db.session.commit()

        assert permission_service.check_permission(researcher_user, 'feature:ranking:edit') is False

    def test_user_permission_overrides_role(self, permission_service, db, researcher_user):
        """User-Permission überschreibt Rollen-Permission"""
        # User bekommt direktes Grant für etwas, das die Rolle nicht hat
        grant_perm = UserPermission(
            user_id=researcher_user.id,
            permission='admin:special:action',
            granted=True
        )
        db.session.add(grant_perm)
        db.session.commit()

        assert permission_service.check_permission(researcher_user, 'admin:special:action') is True

    def test_deny_by_default(self, permission_service, db):
        """Ohne explizite Permission wird denied"""
        user = User(username='noperm', email='noperm@test.local', is_active=True)
        db.session.add(user)
        db.session.commit()

        assert permission_service.check_permission(user, 'feature:unknown:action') is False

    def test_locked_user_always_denied(self, permission_service, db, admin_user):
        """Gesperrter User hat keine Permissions"""
        admin_user.account_status = 'locked'
        db.session.commit()

        assert permission_service.check_permission(admin_user, 'feature:any:action') is False
```

#### 4.1.4 Embedding Model Service Tests

```python
# tests/unit/services/test_embedding_model_service.py
import pytest
from unittest.mock import patch, MagicMock
from app.services.rag.embedding_model_service import (
    get_available_embedding_models,
    get_best_embedding_for_collection,
    check_model_availability
)
from app.db.models import LLMModel, RAGCollection, CollectionEmbedding

class TestEmbeddingModelService:
    """Tests für Embedding Model Service"""

    @pytest.fixture
    def mock_collection(self, db):
        """Test-Collection"""
        collection = RAGCollection(
            name='Test Collection',
            description='For testing',
            source_type='upload'
        )
        db.session.add(collection)
        db.session.commit()
        return collection

    @pytest.fixture
    def mock_embedding_model(self, db):
        """Test Embedding Model"""
        model = LLMModel(
            model_id='test-embedding-model',
            display_name='Test Embedder',
            model_type='embedding',
            is_default=True,
            embedding_dimensions=384
        )
        db.session.add(model)
        db.session.commit()
        return model

    def test_get_available_models_returns_list(self, app, mock_embedding_model):
        """get_available_embedding_models gibt Liste zurück"""
        with app.app_context():
            models = get_available_embedding_models()

            assert isinstance(models, list)
            assert len(models) >= 1

    @patch('app.services.rag.embedding_model_service.litellm_client')
    def test_model_availability_check_litellm(self, mock_litellm, app, mock_embedding_model):
        """Prüft LiteLLM Model Verfügbarkeit"""
        mock_litellm.embedding.return_value = MagicMock(data=[MagicMock(embedding=[0.1] * 384)])

        with app.app_context():
            available = check_model_availability(mock_embedding_model.model_id, 'litellm')

            assert available is True

    @patch('app.services.rag.embedding_model_service.HuggingFaceEmbeddings')
    def test_model_availability_check_local(self, mock_hf, app, mock_embedding_model):
        """Prüft Local Model Verfügbarkeit"""
        mock_hf.return_value.embed_query.return_value = [0.1] * 384

        with app.app_context():
            available = check_model_availability(mock_embedding_model.model_id, 'local')

            assert available is True

    def test_fallback_chain_on_model_failure(self, app, db, mock_collection, mock_embedding_model):
        """Fallback auf alternatives Model bei Fehler"""
        # Füge Fallback-Model hinzu
        fallback = LLMModel(
            model_id='fallback-model',
            display_name='Fallback',
            model_type='embedding',
            is_default=False,
            embedding_dimensions=384
        )
        db.session.add(fallback)
        db.session.commit()

        with app.app_context():
            with patch('app.services.rag.embedding_model_service.check_model_availability') as mock_check:
                # Primary fails, fallback works
                mock_check.side_effect = [False, True]

                embeddings, model_id, _, dims = get_best_embedding_for_collection(mock_collection.id)

                assert model_id == 'fallback-model'
```

#### 4.1.5 Database Model Tests

```python
# tests/unit/models/test_user.py
import pytest
from app.db.models import User, Role, UserPermission
from sqlalchemy.exc import IntegrityError

class TestUserModel:
    """Tests für User Model"""

    def test_user_creation(self, db):
        """User kann erstellt werden"""
        user = User(
            username='test_create',
            email='create@test.local',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.created_at is not None

    def test_username_unique_constraint(self, db, mock_authentik_user):
        """Username muss eindeutig sein"""
        duplicate = User(
            username=mock_authentik_user.username,  # Duplikat!
            email='other@test.local'
        )
        db.session.add(duplicate)

        with pytest.raises(IntegrityError):
            db.session.commit()

    def test_user_role_relationship(self, db):
        """User kann Rollen haben"""
        user = User(username='role_test', email='role@test.local')
        role = Role(name='test_role')
        user.roles.append(role)

        db.session.add(user)
        db.session.commit()

        assert len(user.roles) == 1
        assert user.roles[0].name == 'test_role'

    def test_user_to_dict(self, db):
        """to_dict() gibt korrektes Dictionary zurück"""
        user = User(
            username='dict_test',
            email='dict@test.local',
            collab_color='#FF0000'
        )
        db.session.add(user)
        db.session.commit()

        user_dict = user.to_dict()

        assert user_dict['username'] == 'dict_test'
        assert user_dict['email'] == 'dict@test.local'
        assert user_dict['collab_color'] == '#FF0000'
        assert 'password_hash' not in user_dict  # Sensible Daten ausgeschlossen

    def test_account_status_enum(self, db):
        """Account-Status wird korrekt gesetzt"""
        user = User(username='status_test', email='status@test.local')

        user.account_status = 'active'
        assert user.account_status == 'active'

        user.account_status = 'locked'
        assert user.account_status == 'locked'


# tests/unit/models/test_rag_document.py
class TestRAGDocumentModel:
    """Tests für RAGDocument Model"""

    @pytest.fixture
    def collection(self, db):
        from app.db.models import RAGCollection
        coll = RAGCollection(name='Test', source_type='upload')
        db.session.add(coll)
        db.session.commit()
        return coll

    def test_document_creation(self, db, collection):
        from app.db.models import RAGDocument

        doc = RAGDocument(
            collection_id=collection.id,
            title='Test Document',
            content='Test content here',
            source_type='upload'
        )
        db.session.add(doc)
        db.session.commit()

        assert doc.id is not None
        assert doc.collection_id == collection.id

    def test_cascade_delete_chunks(self, db, collection):
        """Chunks werden bei Document-Löschung mitgelöscht"""
        from app.db.models import RAGDocument, RAGDocumentChunk

        doc = RAGDocument(
            collection_id=collection.id,
            title='Cascade Test',
            content='Content'
        )
        db.session.add(doc)
        db.session.commit()

        chunk = RAGDocumentChunk(
            document_id=doc.id,
            chunk_index=0,
            content='Chunk content'
        )
        db.session.add(chunk)
        db.session.commit()

        chunk_id = chunk.id
        db.session.delete(doc)
        db.session.commit()

        assert RAGDocumentChunk.query.get(chunk_id) is None


# tests/unit/models/test_judge_session.py
class TestJudgeSessionModel:
    """Tests für JudgeSession Model"""

    def test_session_status_transitions(self, db):
        from app.db.models import JudgeSession

        session = JudgeSession(
            name='Test Session',
            status='draft'
        )
        db.session.add(session)
        db.session.commit()

        # Draft → Queued
        session.status = 'queued'
        db.session.commit()
        assert session.status == 'queued'

        # Queued → Running
        session.status = 'running'
        db.session.commit()
        assert session.status == 'running'

    def test_session_config_json(self, db):
        """config_json wird korrekt gespeichert"""
        from app.db.models import JudgeSession

        config = {
            'pillar_ids': [1, 2, 3],
            'workers': 4,
            'model': 'gpt-4'
        }

        session = JudgeSession(
            name='Config Test',
            status='draft',
            config_json=config
        )
        db.session.add(session)
        db.session.commit()

        loaded = JudgeSession.query.get(session.id)
        assert loaded.config_json['pillar_ids'] == [1, 2, 3]
        assert loaded.config_json['workers'] == 4
```

### 4.2 Frontend Unit Tests

#### 4.2.1 Test Setup

```javascript
// llars-frontend/src/test/setup.js
import { config } from '@vue/test-utils'
import { vi } from 'vitest'

// Globale Mocks
vi.mock('@/services/socketService', () => ({
  default: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    emit: vi.fn(),
    on: vi.fn(),
    off: vi.fn()
  }
}))

// Vuetify Mock
config.global.stubs = {
  'v-btn': true,
  'v-card': true,
  'v-icon': true,
  'v-tooltip': true,
  // ... weitere Vuetify Komponenten
}

// Router Mock
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn()
  }),
  useRoute: () => ({
    params: {},
    query: {}
  })
}))

// LocalStorage Mock
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}
vi.stubGlobal('localStorage', localStorageMock)
```

#### 4.2.2 Composable Tests

```javascript
// llars-frontend/src/composables/__tests__/useAuth.test.js
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useAuth } from '@/composables/useAuth'
import { setActivePinia, createPinia } from 'pinia'

describe('useAuth', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('isAuthenticated', () => {
    it('returns false when no token exists', () => {
      localStorage.getItem.mockReturnValue(null)

      const { isAuthenticated } = useAuth()

      expect(isAuthenticated.value).toBe(false)
    })

    it('returns true when valid token exists', () => {
      const validToken = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjk5OTk5OTk5OTl9.sig'
      localStorage.getItem.mockReturnValue(validToken)

      const { isAuthenticated } = useAuth()

      expect(isAuthenticated.value).toBe(true)
    })

    it('returns false for expired token', () => {
      // Token mit exp in der Vergangenheit
      const expiredToken = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2MDAwMDAwMDB9.sig'
      localStorage.getItem.mockReturnValue(expiredToken)

      const { isAuthenticated } = useAuth()

      expect(isAuthenticated.value).toBe(false)
    })
  })

  describe('logout', () => {
    it('clears token from localStorage', () => {
      const { logout } = useAuth()

      logout()

      expect(localStorage.removeItem).toHaveBeenCalledWith('access_token')
    })

    it('redirects to login page', async () => {
      const mockPush = vi.fn()
      vi.mock('vue-router', () => ({
        useRouter: () => ({ push: mockPush })
      }))

      const { logout } = useAuth()
      await logout()

      expect(mockPush).toHaveBeenCalledWith('/login')
    })
  })

  describe('getUserInfo', () => {
    it('decodes user info from token', () => {
      const tokenPayload = {
        sub: 'user123',
        preferred_username: 'testuser',
        email: 'test@llars.local',
        groups: ['researcher']
      }
      const token = createMockToken(tokenPayload)
      localStorage.getItem.mockReturnValue(token)

      const { getUserInfo } = useAuth()
      const userInfo = getUserInfo()

      expect(userInfo.username).toBe('testuser')
      expect(userInfo.email).toBe('test@llars.local')
      expect(userInfo.groups).toContain('researcher')
    })
  })
})

// Helper
function createMockToken(payload) {
  const header = btoa(JSON.stringify({ alg: 'RS256', typ: 'JWT' }))
  const body = btoa(JSON.stringify({ ...payload, exp: 9999999999 }))
  return `${header}.${body}.signature`
}
```

```javascript
// llars-frontend/src/composables/__tests__/usePermissions.test.js
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { usePermissions } from '@/composables/usePermissions'
import { useAuth } from '@/composables/useAuth'

vi.mock('@/composables/useAuth')

describe('usePermissions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('hasPermission', () => {
    it('returns true for admin user on any permission', () => {
      useAuth.mockReturnValue({
        getUserInfo: () => ({ groups: ['admin'] }),
        isAuthenticated: { value: true }
      })

      const { hasPermission } = usePermissions()

      expect(hasPermission('feature:anything:do')).toBe(true)
      expect(hasPermission('admin:users:delete')).toBe(true)
    })

    it('returns true for researcher on allowed permissions', () => {
      useAuth.mockReturnValue({
        getUserInfo: () => ({ groups: ['researcher'] }),
        isAuthenticated: { value: true }
      })

      const { hasPermission } = usePermissions()

      expect(hasPermission('feature:ranking:view')).toBe(true)
      expect(hasPermission('feature:ranking:edit')).toBe(true)
    })

    it('returns false for viewer on edit permissions', () => {
      useAuth.mockReturnValue({
        getUserInfo: () => ({ groups: ['viewer'] }),
        isAuthenticated: { value: true }
      })

      const { hasPermission } = usePermissions()

      expect(hasPermission('feature:ranking:view')).toBe(true)
      expect(hasPermission('feature:ranking:edit')).toBe(false)
    })

    it('returns false when not authenticated', () => {
      useAuth.mockReturnValue({
        getUserInfo: () => null,
        isAuthenticated: { value: false }
      })

      const { hasPermission } = usePermissions()

      expect(hasPermission('feature:public:view')).toBe(false)
    })
  })

  describe('hasAnyPermission', () => {
    it('returns true if user has at least one permission', () => {
      useAuth.mockReturnValue({
        getUserInfo: () => ({ groups: ['researcher'] }),
        isAuthenticated: { value: true }
      })

      const { hasAnyPermission } = usePermissions()

      expect(hasAnyPermission([
        'admin:users:delete',  // doesn't have
        'feature:ranking:view' // has
      ])).toBe(true)
    })
  })
})
```

#### 4.2.3 Component Tests

```javascript
// llars-frontend/src/components/common/__tests__/LBtn.test.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LBtn from '@/components/common/LBtn.vue'

describe('LBtn', () => {
  it('renders with correct variant class', () => {
    const wrapper = mount(LBtn, {
      props: { variant: 'primary' }
    })

    expect(wrapper.classes()).toContain('l-btn--primary')
  })

  it('renders slot content', () => {
    const wrapper = mount(LBtn, {
      slots: { default: 'Click me' }
    })

    expect(wrapper.text()).toContain('Click me')
  })

  it('emits click event when clicked', async () => {
    const wrapper = mount(LBtn)

    await wrapper.trigger('click')

    expect(wrapper.emitted('click')).toBeTruthy()
    expect(wrapper.emitted('click')).toHaveLength(1)
  })

  it('is disabled when loading', async () => {
    const wrapper = mount(LBtn, {
      props: { loading: true }
    })

    await wrapper.trigger('click')

    expect(wrapper.emitted('click')).toBeFalsy()
  })

  it('shows prepend icon when provided', () => {
    const wrapper = mount(LBtn, {
      props: { prependIcon: 'mdi-plus' }
    })

    expect(wrapper.find('.v-icon').exists()).toBe(true)
  })

  it('applies danger variant styles', () => {
    const wrapper = mount(LBtn, {
      props: { variant: 'danger' }
    })

    expect(wrapper.classes()).toContain('l-btn--danger')
  })
})


// llars-frontend/src/components/common/__tests__/LTag.test.js
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import LTag from '@/components/common/LTag.vue'

describe('LTag', () => {
  it('renders with correct variant', () => {
    const wrapper = mount(LTag, {
      props: { variant: 'success' }
    })

    expect(wrapper.classes()).toContain('l-tag--success')
  })

  it('shows close button when closable', () => {
    const wrapper = mount(LTag, {
      props: { closable: true }
    })

    expect(wrapper.find('.l-tag__close').exists()).toBe(true)
  })

  it('emits close event when close button clicked', async () => {
    const wrapper = mount(LTag, {
      props: { closable: true }
    })

    await wrapper.find('.l-tag__close').trigger('click')

    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('renders slot content', () => {
    const wrapper = mount(LTag, {
      slots: { default: 'Status' }
    })

    expect(wrapper.text()).toContain('Status')
  })
})


// llars-frontend/src/components/common/__tests__/LSlider.test.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LSlider from '@/components/common/LSlider.vue'

describe('LSlider', () => {
  it('renders with initial value', () => {
    const wrapper = mount(LSlider, {
      props: { modelValue: 50, min: 0, max: 100 }
    })

    expect(wrapper.find('input[type="range"]').element.value).toBe('50')
  })

  it('emits update:modelValue on change', async () => {
    const wrapper = mount(LSlider, {
      props: { modelValue: 50, min: 0, max: 100 }
    })

    await wrapper.find('input').setValue(75)

    expect(wrapper.emitted('update:modelValue')[0]).toEqual([75])
  })

  it('shows gradient color based on value', async () => {
    const wrapper = mount(LSlider, {
      props: { modelValue: 0, min: 0, max: 100, startActive: true }
    })

    // Low value = red
    expect(wrapper.find('.slider-track').attributes('style')).toContain('rgb')
  })

  it('starts gray when startActive is false', () => {
    const wrapper = mount(LSlider, {
      props: { modelValue: 50, min: 0, max: 100, startActive: false }
    })

    expect(wrapper.classes()).toContain('l-slider--inactive')
  })
})
```

---

## 5. Integration Tests

### 5.1 Backend Integration Tests

#### 5.1.1 Auth Flow Integration

```python
# tests/integration/test_auth_flow.py
import pytest
from unittest.mock import patch, MagicMock
from app.db.models import User, Role

class TestAuthFlowIntegration:
    """Vollständiger Auth-Flow Integration Test"""

    @pytest.fixture
    def authentik_mock(self):
        """Mock für Authentik OIDC"""
        with patch('app.auth.decorators.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {
                'active': True,
                'sub': 'new_test_user',
                'preferred_username': 'integration_user',
                'email': 'integration@llars.local',
                'groups': ['researcher']
            }
            yield mock_get

    def test_first_login_creates_user_with_role(self, client, db, authentik_mock):
        """Erster Login erstellt User mit korrekter Rolle"""
        response = client.get(
            '/api/users/me',
            headers={'Authorization': 'Bearer mock-valid-token'}
        )

        assert response.status_code == 200

        # User wurde erstellt
        user = User.query.filter_by(username='integration_user').first()
        assert user is not None
        assert user.email == 'integration@llars.local'

        # Hat Viewer-Rolle (Default)
        role_names = [r.name for r in user.roles]
        assert 'viewer' in role_names

    def test_subsequent_login_returns_existing_user(self, client, db, authentik_mock):
        """Folgende Logins geben existierenden User zurück"""
        # Erster Login
        response1 = client.get('/api/users/me', headers={'Authorization': 'Bearer token1'})
        user_id_1 = response1.json['user']['id']

        # Zweiter Login
        response2 = client.get('/api/users/me', headers={'Authorization': 'Bearer token2'})
        user_id_2 = response2.json['user']['id']

        assert user_id_1 == user_id_2

    def test_locked_account_denied_access(self, client, db, authentik_mock, mock_authentik_user):
        """Gesperrter Account bekommt keinen Zugang"""
        mock_authentik_user.account_status = 'locked'
        db.session.commit()

        authentik_mock.return_value.json.return_value['sub'] = mock_authentik_user.username

        response = client.get(
            '/api/users/me',
            headers={'Authorization': 'Bearer token'}
        )

        assert response.status_code == 403
        assert 'locked' in response.json.get('error', '').lower()
```

#### 5.1.2 RAG Pipeline Integration

```python
# tests/integration/test_rag_pipeline.py
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
from app.db.models import RAGCollection, RAGDocument, RAGDocumentChunk, RAGProcessingQueue

class TestRAGPipelineIntegration:
    """RAG Pipeline Integration Tests"""

    @pytest.fixture
    def auth_user(self, client, db, mock_authentik_user):
        """Authentifizierter User für Tests"""
        with patch('app.auth.decorators.validate_token') as mock:
            mock.return_value = {'sub': mock_authentik_user.username}
            yield mock_authentik_user

    @pytest.fixture
    def collection(self, db, auth_user):
        """Test-Collection"""
        coll = RAGCollection(
            name='Integration Test Collection',
            owner_id=auth_user.id,
            source_type='upload'
        )
        db.session.add(coll)
        db.session.commit()
        return coll

    def test_document_upload_creates_queue_entry(self, client, db, collection, auth_user):
        """Dokument-Upload erstellt Queue-Eintrag"""
        data = {
            'file': (BytesIO(b'Test document content for RAG'), 'test.txt')
        }

        response = client.post(
            f'/api/rag/collections/{collection.id}/documents',
            data=data,
            content_type='multipart/form-data',
            headers={'Authorization': 'Bearer token'}
        )

        assert response.status_code == 201

        # Document erstellt
        doc = RAGDocument.query.filter_by(collection_id=collection.id).first()
        assert doc is not None

        # Queue-Eintrag erstellt
        queue = RAGProcessingQueue.query.filter_by(document_id=doc.id).first()
        assert queue is not None
        assert queue.status == 'pending'

    @patch('app.services.rag.collection_embedding_service.get_embeddings')
    @patch('app.services.rag.collection_embedding_service.chroma_client')
    def test_embedding_process_creates_chunks(
        self, mock_chroma, mock_embeddings, client, db, collection, auth_user
    ):
        """Embedding-Prozess erstellt Chunks mit Vektoren"""
        mock_embeddings.return_value = [[0.1] * 384]  # Mock Embeddings
        mock_chroma.get_or_create_collection.return_value = MagicMock()

        # Dokument erstellen
        doc = RAGDocument(
            collection_id=collection.id,
            title='Embedding Test',
            content='This is test content that will be chunked and embedded.',
            source_type='upload'
        )
        db.session.add(doc)
        db.session.commit()

        # Embedding Worker simulieren
        from app.workers.embedding_worker import process_document
        process_document(doc.id)

        # Chunks wurden erstellt
        chunks = RAGDocumentChunk.query.filter_by(document_id=doc.id).all()
        assert len(chunks) > 0

        # Status aktualisiert
        doc = RAGDocument.query.get(doc.id)
        assert doc.embedding_status == 'completed'

    @patch('app.services.rag.collection_embedding_service.chroma_client')
    def test_semantic_search_returns_results(self, mock_chroma, client, db, collection, auth_user):
        """Semantische Suche gibt relevante Ergebnisse zurück"""
        # Mock ChromaDB query results
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            'ids': [['chunk_1', 'chunk_2']],
            'documents': [['Result 1', 'Result 2']],
            'metadatas': [[{'source': 'doc1'}, {'source': 'doc2'}]],
            'distances': [[0.1, 0.3]]
        }
        mock_chroma.get_collection.return_value = mock_collection

        response = client.post(
            f'/api/rag/collections/{collection.id}/search',
            json={'query': 'test search query', 'top_k': 5},
            headers={'Authorization': 'Bearer token'}
        )

        assert response.status_code == 200
        assert len(response.json['results']) > 0

    def test_multi_model_embedding_fallback(self, client, db, collection, auth_user):
        """Fallback auf alternatives Embedding Model bei Fehler"""
        with patch('app.services.rag.embedding_model_service.check_model_availability') as mock_check:
            # Primary model fails
            mock_check.side_effect = [False, True]

            from app.services.rag.embedding_model_service import get_best_embedding_for_collection
            result = get_best_embedding_for_collection(collection.id)

            # Fallback model verwendet
            assert result is not None
```

#### 5.1.3 Chatbot Wizard Integration

```python
# tests/integration/test_chatbot_wizard.py
import pytest
from unittest.mock import patch, MagicMock
from app.db.models import Chatbot, RAGCollection

class TestChatbotWizardIntegration:
    """Chatbot Builder Wizard Integration Tests"""

    @pytest.fixture
    def wizard_session(self, client, db, mock_authentik_user):
        """Wizard Session initialisieren"""
        with patch('app.auth.decorators.validate_token') as mock:
            mock.return_value = {'sub': mock_authentik_user.username}

            response = client.post(
                '/api/chatbot/wizard/start',
                json={'name': 'Test Bot'},
                headers={'Authorization': 'Bearer token'}
            )

            return response.json['session_id']

    def test_wizard_step_1_crawler_config(self, client, wizard_session):
        """Step 1: Crawler-Konfiguration"""
        response = client.post(
            f'/api/chatbot/wizard/{wizard_session}/step/1',
            json={
                'crawler_config': {
                    'url': 'https://example.com',
                    'max_pages': 10,
                    'max_depth': 2
                }
            },
            headers={'Authorization': 'Bearer token'}
        )

        assert response.status_code == 200
        assert response.json['current_step'] == 2

    def test_wizard_step_2_embedding_config(self, client, wizard_session):
        """Step 2: Embedding-Konfiguration"""
        # Erst Step 1 abschließen
        client.post(
            f'/api/chatbot/wizard/{wizard_session}/step/1',
            json={'crawler_config': {'url': 'https://example.com'}},
            headers={'Authorization': 'Bearer token'}
        )

        response = client.post(
            f'/api/chatbot/wizard/{wizard_session}/step/2',
            json={
                'embedding_config': {
                    'model': 'test-embedding-model',
                    'chunk_size': 500
                }
            },
            headers={'Authorization': 'Bearer token'}
        )

        assert response.status_code == 200
        assert response.json['current_step'] == 3

    def test_wizard_step_validation_prevents_skip(self, client, wizard_session):
        """Steps können nicht übersprungen werden"""
        # Versuche direkt zu Step 3 zu springen
        response = client.post(
            f'/api/chatbot/wizard/{wizard_session}/step/3',
            json={'config': {}},
            headers={'Authorization': 'Bearer token'}
        )

        assert response.status_code == 400
        assert 'step' in response.json['error'].lower()

    def test_wizard_cancel_cleans_up(self, client, db, wizard_session):
        """Wizard-Abbruch räumt auf"""
        response = client.delete(
            f'/api/chatbot/wizard/{wizard_session}',
            headers={'Authorization': 'Bearer token'}
        )

        assert response.status_code == 200

        # Session gelöscht (Redis)
        # Keine Chatbot-Reste in DB
        assert Chatbot.query.filter_by(build_status='draft').count() == 0
```

#### 5.1.4 Judge System Integration

```python
# tests/integration/test_judge_system.py
import pytest
from unittest.mock import patch, MagicMock
from app.db.models import JudgeSession, JudgeComparison, PillarThread

class TestJudgeSystemIntegration:
    """LLM-as-Judge System Integration Tests"""

    @pytest.fixture
    def judge_session(self, db, mock_authentik_user):
        """Judge Session für Tests"""
        session = JudgeSession(
            name='Integration Test Session',
            creator_id=mock_authentik_user.id,
            status='draft',
            config_json={
                'pillar_ids': [1, 2],
                'model': 'gpt-4',
                'workers': 2
            }
        )
        db.session.add(session)
        db.session.commit()
        return session

    @pytest.fixture
    def pillar_threads(self, db):
        """Test Pillar Threads"""
        threads = []
        for i in range(5):
            thread = PillarThread(
                pillar_id=1,
                content=f'Test thread {i} content',
                metadata={'source': 'test'}
            )
            db.session.add(thread)
            threads.append(thread)
        db.session.commit()
        return threads

    def test_session_start_generates_comparisons(
        self, client, db, judge_session, pillar_threads
    ):
        """Session-Start generiert Comparisons"""
        response = client.post(
            f'/api/judge/sessions/{judge_session.id}/start',
            headers={'Authorization': 'Bearer token'}
        )

        assert response.status_code == 200

        # Comparisons erstellt
        comparisons = JudgeComparison.query.filter_by(session_id=judge_session.id).all()
        assert len(comparisons) > 0

        # Status aktualisiert
        session = JudgeSession.query.get(judge_session.id)
        assert session.status == 'running'

    @patch('app.workers.judge_worker_pool.call_llm_judge')
    def test_comparison_execution(
        self, mock_llm, client, db, judge_session, pillar_threads
    ):
        """Comparison-Ausführung mit LLM"""
        mock_llm.return_value = {
            'winner': 'thread_a',
            'reasoning': 'Thread A is more relevant',
            'confidence': 0.85
        }

        # Session starten
        client.post(f'/api/judge/sessions/{judge_session.id}/start',
                   headers={'Authorization': 'Bearer token'})

        # Worker ausführen
        from app.workers.judge_worker_pool import execute_pending_comparisons
        execute_pending_comparisons(judge_session.id)

        # Evaluations erstellt
        from app.db.models import JudgeEvaluation
        evaluations = JudgeEvaluation.query.join(JudgeComparison).filter(
            JudgeComparison.session_id == judge_session.id
        ).all()

        assert len(evaluations) > 0
        assert all(e.winner is not None for e in evaluations)

    def test_stale_job_detection(self, db, judge_session):
        """Stale Jobs werden erkannt"""
        from datetime import datetime, timedelta
        from app.services.judge.stale_job_detection import detect_stale_jobs

        # Comparison die >30min läuft
        comparison = JudgeComparison(
            session_id=judge_session.id,
            thread_a_id=1,
            thread_b_id=2,
            status='running',
            started_at=datetime.utcnow() - timedelta(minutes=35)
        )
        db.session.add(comparison)
        db.session.commit()

        stale = detect_stale_jobs()

        assert len(stale) > 0
        assert comparison.id in [s.id for s in stale]

    def test_session_pause_and_resume(self, client, db, judge_session, pillar_threads):
        """Session kann pausiert und fortgesetzt werden"""
        # Start
        client.post(f'/api/judge/sessions/{judge_session.id}/start',
                   headers={'Authorization': 'Bearer token'})

        # Pause
        response = client.post(
            f'/api/judge/sessions/{judge_session.id}/pause',
            headers={'Authorization': 'Bearer token'}
        )
        assert response.status_code == 200

        session = JudgeSession.query.get(judge_session.id)
        assert session.status == 'paused'

        # Resume
        response = client.post(
            f'/api/judge/sessions/{judge_session.id}/resume',
            headers={'Authorization': 'Bearer token'}
        )
        assert response.status_code == 200

        session = JudgeSession.query.get(judge_session.id)
        assert session.status == 'running'
```

### 5.2 Socket.IO Integration Tests

```python
# tests/integration/test_socket_events.py
import pytest
from flask_socketio import SocketIOTestClient
from unittest.mock import patch, MagicMock

class TestSocketIOIntegration:
    """Socket.IO Event Integration Tests"""

    @pytest.fixture
    def socketio_client(self, app):
        """Socket.IO Test Client"""
        from app.main import socketio
        return SocketIOTestClient(app, socketio)

    def test_connection_requires_auth(self, socketio_client):
        """Verbindung erfordert Authentifizierung"""
        # Ohne Auth-Token
        socketio_client.connect()

        received = socketio_client.get_received()
        assert any('error' in str(r) or 'unauthorized' in str(r).lower()
                   for r in received)

    @patch('app.socketio_handlers.events_connection.validate_token')
    def test_authenticated_connection(self, mock_validate, socketio_client):
        """Authentifizierte Verbindung funktioniert"""
        mock_validate.return_value = {'sub': 'test_user'}

        socketio_client.connect(headers={'Authorization': 'Bearer valid-token'})

        assert socketio_client.is_connected()

    @patch('app.socketio_handlers.events_rag.get_queue_status')
    def test_rag_queue_subscription(self, mock_status, socketio_client):
        """RAG Queue Subscription"""
        mock_status.return_value = [{'id': 1, 'status': 'processing', 'progress': 50}]

        socketio_client.emit('rag:subscribe_queue', {'collection_id': 1})

        received = socketio_client.get_received()
        assert any('queue_update' in str(r) for r in received)

    def test_judge_session_updates(self, socketio_client, db, judge_session):
        """Judge Session Updates werden empfangen"""
        socketio_client.emit('judge:join_session', {'session_id': judge_session.id})

        # Simuliere Update
        from app.main import socketio
        socketio.emit('judge:status_update',
                     {'session_id': judge_session.id, 'status': 'running'},
                     namespace='/judge')

        received = socketio_client.get_received()
        assert any('status_update' in str(r) for r in received)

    def test_chat_streaming(self, socketio_client):
        """Chat Streaming funktioniert"""
        with patch('app.socketio_handlers.events_chat.stream_llm_response') as mock_stream:
            mock_stream.return_value = iter(['Hello', ' World', '!'])

            socketio_client.emit('chat_stream', {
                'message': 'Hi',
                'chatbot_id': 1
            })

            received = socketio_client.get_received()
            # Sollte mehrere chunk-Events empfangen haben
            chunks = [r for r in received if 'chunk' in str(r)]
            assert len(chunks) >= 1
```

---

## 6. End-to-End Tests

### 6.1 Playwright Setup

```typescript
// e2e/fixtures/auth.ts
import { test as base, expect } from '@playwright/test'

// Test-User Credentials
export const testUsers = {
  admin: { username: 'admin', password: 'admin123' },
  researcher: { username: 'researcher', password: 'admin123' },
  viewer: { username: 'viewer', password: 'admin123' }
}

// Erweiterte Test-Fixture mit Auth
export const test = base.extend<{
  authenticatedPage: Page
  adminPage: Page
  researcherPage: Page
}>({
  authenticatedPage: async ({ page }, use) => {
    await login(page, testUsers.researcher)
    await use(page)
  },
  adminPage: async ({ page }, use) => {
    await login(page, testUsers.admin)
    await use(page)
  },
  researcherPage: async ({ page }, use) => {
    await login(page, testUsers.researcher)
    await use(page)
  }
})

async function login(page: Page, user: { username: string, password: string }) {
  await page.goto('/login')

  // Authentik Login Flow
  await page.fill('input[name="username"]', user.username)
  await page.fill('input[name="password"]', user.password)
  await page.click('button[type="submit"]')

  // Warte auf Redirect zu LLARS
  await page.waitForURL('**/Home')

  // Prüfe Auth Token
  const token = await page.evaluate(() => localStorage.getItem('access_token'))
  expect(token).toBeTruthy()
}

export { expect }
```

### 6.2 Auth E2E Tests

```typescript
// e2e/auth.spec.ts
import { test, expect, testUsers } from './fixtures/auth'

test.describe('Authentication', () => {
  test('successful login redirects to Home', async ({ page }) => {
    await page.goto('/login')

    await page.fill('input[name="username"]', testUsers.researcher.username)
    await page.fill('input[name="password"]', testUsers.researcher.password)
    await page.click('button[type="submit"]')

    await expect(page).toHaveURL(/.*Home/)
    await expect(page.locator('.user-menu')).toBeVisible()
  })

  test('invalid credentials show error', async ({ page }) => {
    await page.goto('/login')

    await page.fill('input[name="username"]', 'wrong')
    await page.fill('input[name="password"]', 'credentials')
    await page.click('button[type="submit"]')

    await expect(page.locator('.error-message')).toBeVisible()
  })

  test('logout clears session', async ({ authenticatedPage }) => {
    await authenticatedPage.click('.user-menu')
    await authenticatedPage.click('text=Logout')

    await expect(authenticatedPage).toHaveURL(/.*login/)

    const token = await authenticatedPage.evaluate(
      () => localStorage.getItem('access_token')
    )
    expect(token).toBeNull()
  })

  test('protected routes redirect to login', async ({ page }) => {
    await page.goto('/Ranker')

    await expect(page).toHaveURL(/.*login/)
  })
})
```

### 6.3 Rating Workflow E2E

```typescript
// e2e/rating-workflow.spec.ts
import { test, expect } from './fixtures/auth'

test.describe('Rating Workflow', () => {
  test('complete rating flow for researcher', async ({ researcherPage }) => {
    // 1. Navigiere zu Rater
    await researcherPage.goto('/Rater')
    await expect(researcherPage.locator('h1')).toContainText('Rating')

    // 2. Wähle ersten Thread
    const firstThread = researcherPage.locator('.thread-list .thread-item').first()
    await firstThread.click()

    // 3. Warte auf Features
    await expect(researcherPage.locator('.feature-list')).toBeVisible()

    // 4. Bewerte erstes Feature
    const slider = researcherPage.locator('.l-slider').first()
    await slider.click()
    await slider.fill('75')

    // 5. Speichere Bewertung
    await researcherPage.click('button:has-text("Speichern")')

    // 6. Prüfe Erfolg
    await expect(researcherPage.locator('.v-snackbar')).toContainText('gespeichert')

    // 7. Prüfe Progress-Update
    const progressBar = researcherPage.locator('.progress-bar')
    await expect(progressBar).toHaveAttribute('aria-valuenow', /[1-9]/)
  })

  test('ranking drag and drop works', async ({ researcherPage }) => {
    await researcherPage.goto('/Ranker')

    // Wähle Thread
    await researcherPage.locator('.thread-item').first().click()

    // Drag & Drop
    const items = researcherPage.locator('.ranking-item')
    const firstItem = items.first()
    const secondItem = items.nth(1)

    await firstItem.dragTo(secondItem)

    // Prüfe neue Reihenfolge
    const newOrder = await items.allTextContents()
    expect(newOrder[0]).not.toEqual(newOrder[1])

    // Speichere
    await researcherPage.click('button:has-text("Ranking speichern")')
    await expect(researcherPage.locator('.v-snackbar')).toContainText('gespeichert')
  })
})
```

### 6.4 Chatbot Creation E2E

```typescript
// e2e/chatbot-creation.spec.ts
import { test, expect } from './fixtures/auth'

test.describe('Chatbot Creation Wizard', () => {
  test.beforeEach(async ({ adminPage }) => {
    await adminPage.goto('/Admin/AdminChatbots')
  })

  test('create chatbot via wizard', async ({ adminPage }) => {
    // 1. Wizard starten
    await adminPage.click('button:has-text("Neuer Chatbot")')
    await expect(adminPage.locator('.wizard-dialog')).toBeVisible()

    // 2. Step 1: Name & Beschreibung
    await adminPage.fill('input[name="name"]', 'E2E Test Bot')
    await adminPage.fill('textarea[name="description"]', 'Created by E2E test')
    await adminPage.click('button:has-text("Weiter")')

    // 3. Step 2: Datenquelle (Upload)
    await adminPage.setInputFiles('input[type="file"]', './e2e/fixtures/test-doc.pdf')
    await expect(adminPage.locator('.upload-progress')).toBeVisible()
    await expect(adminPage.locator('.upload-success')).toBeVisible({ timeout: 30000 })
    await adminPage.click('button:has-text("Weiter")')

    // 4. Step 3: Embedding (warte auf Abschluss)
    await expect(adminPage.locator('.embedding-progress')).toBeVisible()
    await expect(adminPage.locator('.embedding-complete')).toBeVisible({ timeout: 120000 })
    await adminPage.click('button:has-text("Weiter")')

    // 5. Step 4: Konfiguration
    await adminPage.selectOption('select[name="model"]', 'gpt-4')
    await adminPage.fill('input[name="temperature"]', '0.7')
    await adminPage.click('button:has-text("Fertigstellen")')

    // 6. Prüfe Erstellung
    await expect(adminPage.locator('.v-snackbar')).toContainText('erfolgreich')
    await expect(adminPage.locator('.chatbot-list')).toContainText('E2E Test Bot')
  })

  test('chatbot chat works after creation', async ({ adminPage }) => {
    // Navigiere zu Chat
    await adminPage.goto('/ChatWithBots')

    // Wähle erstellten Bot
    await adminPage.click('.chatbot-selector')
    await adminPage.click('text=E2E Test Bot')

    // Sende Nachricht
    await adminPage.fill('.chat-input', 'Was steht im Dokument?')
    await adminPage.click('button:has-text("Senden")')

    // Warte auf Antwort (Streaming)
    await expect(adminPage.locator('.chat-message.assistant')).toBeVisible({ timeout: 60000 })
    await expect(adminPage.locator('.chat-message.assistant')).not.toBeEmpty()
  })
})
```

### 6.5 Judge Session E2E

```typescript
// e2e/judge-session.spec.ts
import { test, expect } from './fixtures/auth'

test.describe('LLM-as-Judge Session', () => {
  test('complete judge session workflow', async ({ researcherPage }) => {
    // 1. Navigiere zu Judge
    await researcherPage.goto('/Judge')

    // 2. Neue Session erstellen
    await researcherPage.click('button:has-text("Neue Session")')
    await researcherPage.fill('input[name="name"]', 'E2E Judge Session')

    // 3. Pillars auswählen
    await researcherPage.click('.pillar-selector')
    await researcherPage.click('text=Pillar 1')
    await researcherPage.click('text=Pillar 2')
    await researcherPage.keyboard.press('Escape')

    // 4. Konfiguration
    await researcherPage.selectOption('select[name="model"]', 'gpt-4')
    await researcherPage.fill('input[name="workers"]', '2')

    // 5. Session starten
    await researcherPage.click('button:has-text("Session starten")')

    // 6. Warte auf Status-Update
    await expect(researcherPage.locator('.session-status')).toContainText('Running')

    // 7. Fortschritt beobachten
    const progressBar = researcherPage.locator('.comparison-progress')
    await expect(progressBar).toBeVisible()

    // 8. Warte auf Abschluss (mit Timeout für langsame LLM-Calls)
    await expect(researcherPage.locator('.session-status')).toContainText('Completed', {
      timeout: 300000 // 5 Minuten für LLM-Verarbeitung
    })

    // 9. Ergebnisse prüfen
    await researcherPage.click('button:has-text("Ergebnisse anzeigen")')
    await expect(researcherPage.locator('.results-table')).toBeVisible()
    await expect(researcherPage.locator('.results-table tbody tr')).toHaveCount.greaterThan(0)
  })

  test('pause and resume session', async ({ researcherPage }) => {
    // Session in Running-Status finden
    await researcherPage.goto('/Judge')
    await researcherPage.click('.session-row:has-text("Running")')

    // Pausieren
    await researcherPage.click('button:has-text("Pausieren")')
    await expect(researcherPage.locator('.session-status')).toContainText('Paused')

    // Fortsetzen
    await researcherPage.click('button:has-text("Fortsetzen")')
    await expect(researcherPage.locator('.session-status')).toContainText('Running')
  })
})
```

### 6.6 Collaborative Editing E2E

```typescript
// e2e/collab-editing.spec.ts
import { test, expect } from './fixtures/auth'

test.describe('Collaborative Markdown Editing', () => {
  test('real-time sync between two users', async ({ browser }) => {
    // Zwei Browser-Kontexte für zwei User
    const context1 = await browser.newContext()
    const context2 = await browser.newContext()

    const page1 = await context1.newPage()
    const page2 = await context2.newPage()

    // Beide einloggen
    await login(page1, testUsers.researcher)
    await login(page2, testUsers.admin)

    // Workspace erstellen (User 1)
    await page1.goto('/MarkdownCollabHome')
    await page1.click('button:has-text("Neuer Workspace")')
    await page1.fill('input[name="name"]', 'Collab Test')
    await page1.click('button:has-text("Erstellen")')

    const workspaceUrl = page1.url()

    // User 2 öffnet gleichen Workspace
    await page2.goto(workspaceUrl)

    // Warte auf Sync
    await expect(page2.locator('.workspace-title')).toContainText('Collab Test')

    // User 1 tippt
    const editor1 = page1.locator('.markdown-editor .ProseMirror')
    await editor1.click()
    await editor1.type('Hello from User 1!')

    // User 2 sieht Update (Real-time)
    const editor2 = page2.locator('.markdown-editor .ProseMirror')
    await expect(editor2).toContainText('Hello from User 1!', { timeout: 5000 })

    // User 2 tippt zurück
    await editor2.click()
    await editor2.type('\nHello from User 2!')

    // User 1 sieht Update
    await expect(editor1).toContainText('Hello from User 2!', { timeout: 5000 })

    // Cleanup
    await context1.close()
    await context2.close()
  })

  test('presence indicators show active users', async ({ browser }) => {
    const context1 = await browser.newContext()
    const context2 = await browser.newContext()

    const page1 = await context1.newPage()
    const page2 = await context2.newPage()

    await login(page1, testUsers.researcher)
    await login(page2, testUsers.admin)

    await page1.goto('/MarkdownCollabWorkspace/1')
    await page2.goto('/MarkdownCollabWorkspace/1')

    // Presence Avatars prüfen
    await expect(page1.locator('.presence-avatars')).toContainText('2 online')
    await expect(page2.locator('.presence-avatars')).toContainText('2 online')

    // User 2 verlässt
    await context2.close()

    // User 1 sieht Update
    await expect(page1.locator('.presence-avatars')).toContainText('1 online', { timeout: 10000 })

    await context1.close()
  })
})
```

---

## 7. Spezial-Tests

### 7.1 YJS/CRDT Sync Tests

```javascript
// e2e/yjs-sync.spec.ts
import { test, expect } from '@playwright/test'
import * as Y from 'yjs'
import { WebsocketProvider } from 'y-websocket'

test.describe('YJS Synchronization', () => {
  test('CRDT conflict resolution', async () => {
    // Zwei YJS Dokumente
    const doc1 = new Y.Doc()
    const doc2 = new Y.Doc()

    // Simuliere WebSocket-Sync
    const provider1 = new WebsocketProvider('ws://localhost:55082', 'test-room', doc1)
    const provider2 = new WebsocketProvider('ws://localhost:55082', 'test-room', doc2)

    await new Promise(r => setTimeout(r, 1000)) // Warte auf Sync

    // Gleichzeitige Edits
    const text1 = doc1.getText('content')
    const text2 = doc2.getText('content')

    text1.insert(0, 'Hello ')
    text2.insert(0, 'World ')

    await new Promise(r => setTimeout(r, 1000)) // Sync

    // Beide sollten gleichen Content haben (CRDT merged)
    expect(text1.toString()).toEqual(text2.toString())

    provider1.destroy()
    provider2.destroy()
  })

  test('offline edit sync on reconnect', async () => {
    const doc = new Y.Doc()
    const provider = new WebsocketProvider('ws://localhost:55082', 'offline-test', doc)

    // Online edit
    const text = doc.getText('content')
    text.insert(0, 'Online edit. ')

    await new Promise(r => setTimeout(r, 500))

    // Disconnect
    provider.disconnect()

    // Offline edit
    text.insert(text.length, 'Offline edit.')

    // Reconnect
    provider.connect()

    await new Promise(r => setTimeout(r, 1000))

    // Server sollte alle Edits haben
    expect(provider.synced).toBe(true)

    provider.destroy()
  })
})
```

### 7.2 WebSocket Reconnection Tests

```typescript
// e2e/websocket-reconnection.spec.ts
import { test, expect } from './fixtures/auth'

test.describe('WebSocket Reconnection', () => {
  test('auto-reconnect on connection loss', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/ChatWithBots')

    // Initiale Verbindung prüfen
    await expect(authenticatedPage.locator('.connection-status')).toContainText('Connected')

    // Netzwerk unterbrechen
    await authenticatedPage.context().setOffline(true)
    await expect(authenticatedPage.locator('.connection-status')).toContainText('Disconnected')

    // Netzwerk wiederherstellen
    await authenticatedPage.context().setOffline(false)

    // Auto-Reconnect (mit Backoff)
    await expect(authenticatedPage.locator('.connection-status')).toContainText('Connected', {
      timeout: 30000
    })

    // Pending Messages wurden gesendet
    await authenticatedPage.fill('.chat-input', 'Test nach Reconnect')
    await authenticatedPage.click('button:has-text("Senden")')
    await expect(authenticatedPage.locator('.chat-message.assistant')).toBeVisible()
  })

  test('session recovery after page reload', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/Judge')

    // Session joinen
    await authenticatedPage.click('.session-row:first-child')
    await expect(authenticatedPage.locator('.session-details')).toBeVisible()

    // Session ID merken
    const sessionId = await authenticatedPage.locator('.session-id').textContent()

    // Page reload
    await authenticatedPage.reload()

    // Session sollte wiederhergestellt sein
    await expect(authenticatedPage.locator('.session-id')).toContainText(sessionId)
    await expect(authenticatedPage.locator('.session-details')).toBeVisible()
  })
})
```

### 7.3 Performance Tests

```python
# tests/performance/test_rag_performance.py
import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class TestRAGPerformance:
    """Performance Tests für RAG Pipeline"""

    @pytest.fixture
    def large_documents(self, db, collection):
        """100 Dokumente mit je 10KB Content"""
        from app.db.models import RAGDocument

        docs = []
        for i in range(100):
            doc = RAGDocument(
                collection_id=collection.id,
                title=f'Large Doc {i}',
                content='Lorem ipsum ' * 1000,  # ~10KB
                source_type='upload'
            )
            db.session.add(doc)
            docs.append(doc)
        db.session.commit()
        return docs

    def test_embedding_throughput(self, app, db, large_documents):
        """Embedding-Durchsatz: min 10 Docs/Minute"""
        from app.workers.embedding_worker import process_document

        start = time.time()

        for doc in large_documents[:10]:
            process_document(doc.id)

        duration = time.time() - start
        throughput = 10 / (duration / 60)  # Docs pro Minute

        assert throughput >= 10, f'Throughput {throughput:.1f} docs/min < 10'

    def test_search_latency(self, client, collection):
        """Search Latency: max 500ms p95"""
        latencies = []

        for _ in range(100):
            start = time.time()

            client.post(
                f'/api/rag/collections/{collection.id}/search',
                json={'query': 'test query', 'top_k': 10},
                headers={'Authorization': 'Bearer token'}
            )

            latencies.append((time.time() - start) * 1000)

        p95 = sorted(latencies)[94]
        assert p95 < 500, f'p95 Latency {p95:.0f}ms > 500ms'

    def test_concurrent_searches(self, client, collection):
        """10 parallele Suchen ohne Timeout"""
        def search():
            return client.post(
                f'/api/rag/collections/{collection.id}/search',
                json={'query': 'concurrent test', 'top_k': 5},
                headers={'Authorization': 'Bearer token'}
            )

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(search) for _ in range(10)]
            results = [f.result() for f in as_completed(futures)]

        assert all(r.status_code == 200 for r in results)


# tests/performance/test_concurrent_users.py
class TestConcurrentUsers:
    """Concurrent User Load Tests"""

    def test_50_concurrent_logins(self, client):
        """50 gleichzeitige Logins"""
        from concurrent.futures import ThreadPoolExecutor

        def login():
            return client.post('/api/auth/login', json={
                'username': f'user_{time.time_ns()}',
                'password': 'test'
            })

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(login) for _ in range(50)]
            results = [f.result() for f in futures]

        # Alle sollten antworten (auch wenn 401)
        assert all(r.status_code in [200, 401] for r in results)

    def test_concurrent_socket_connections(self, app):
        """100 gleichzeitige Socket.IO Verbindungen"""
        from flask_socketio import SocketIOTestClient
        from app.main import socketio

        clients = []
        for _ in range(100):
            client = SocketIOTestClient(app, socketio)
            client.connect()
            clients.append(client)

        # Alle verbunden
        assert all(c.is_connected() for c in clients)

        # Cleanup
        for c in clients:
            c.disconnect()
```

### 7.4 Database Integrity Tests

```python
# tests/integration/test_database_integrity.py
import pytest
from sqlalchemy import text

class TestDatabaseIntegrity:
    """Database Integrity & Constraint Tests"""

    def test_foreign_key_constraints_enforced(self, db):
        """Foreign Key Constraints werden enforced"""
        from app.db.models import RAGDocument

        # Dokument mit nicht-existierender Collection
        doc = RAGDocument(
            collection_id=99999,  # Existiert nicht
            title='Invalid',
            content='Test'
        )
        db.session.add(doc)

        with pytest.raises(Exception):  # IntegrityError
            db.session.commit()

    def test_cascade_delete_works(self, db, collection):
        """CASCADE DELETE funktioniert"""
        from app.db.models import RAGDocument, RAGDocumentChunk

        doc = RAGDocument(collection_id=collection.id, title='Test', content='')
        db.session.add(doc)
        db.session.commit()

        chunk = RAGDocumentChunk(document_id=doc.id, chunk_index=0, content='Chunk')
        db.session.add(chunk)
        db.session.commit()

        chunk_id = chunk.id

        # Lösche Collection (sollte alles löschen)
        db.session.delete(collection)
        db.session.commit()

        assert RAGDocumentChunk.query.get(chunk_id) is None

    def test_unique_constraints(self, db):
        """Unique Constraints werden enforced"""
        from app.db.models import User

        user1 = User(username='unique_test', email='unique@test.local')
        db.session.add(user1)
        db.session.commit()

        user2 = User(username='unique_test', email='other@test.local')  # Gleicher Username
        db.session.add(user2)

        with pytest.raises(Exception):
            db.session.commit()

    def test_transaction_rollback(self, db):
        """Transaktionen werden bei Fehler zurückgerollt"""
        from app.db.models import User

        initial_count = User.query.count()

        try:
            user = User(username='rollback_test', email='rollback@test.local')
            db.session.add(user)

            # Force error
            db.session.execute(text('SELECT * FROM non_existent_table'))
            db.session.commit()
        except:
            db.session.rollback()

        assert User.query.count() == initial_count

    def test_no_orphaned_chunks(self, db):
        """Keine verwaisten Chunks ohne Dokument"""
        result = db.session.execute(text('''
            SELECT c.id FROM rag_document_chunks c
            LEFT JOIN rag_documents d ON c.document_id = d.id
            WHERE d.id IS NULL
        ''')).fetchall()

        assert len(result) == 0, f'{len(result)} orphaned chunks found'

    def test_no_orphaned_sessions(self, db):
        """Keine verwaisten Judge Sessions ohne Creator"""
        result = db.session.execute(text('''
            SELECT s.id FROM judge_sessions s
            LEFT JOIN users u ON s.creator_id = u.id
            WHERE u.id IS NULL
        ''')).fetchall()

        assert len(result) == 0, f'{len(result)} orphaned sessions found'
```

---

## 8. CI/CD Integration

### 8.1 GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: LLARS Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '20'

jobs:
  # Unit Tests (schnell, parallel)
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-group: [auth, services, models, workers]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run Unit Tests (${{ matrix.test-group }})
        run: |
          pytest tests/unit/${{ matrix.test-group }}/ \
            --cov=app \
            --cov-report=xml \
            -v --tb=short

      - name: Upload Coverage
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
          flags: unit-${{ matrix.test-group }}

  # Frontend Unit Tests
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: llars-frontend/package-lock.json

      - name: Install dependencies
        working-directory: llars-frontend
        run: npm ci

      - name: Run Vitest
        working-directory: llars-frontend
        run: npm run test:coverage

      - name: Upload Coverage
        uses: codecov/codecov-action@v4
        with:
          file: llars-frontend/coverage/coverage-final.json
          flags: frontend

  # Integration Tests (braucht DB)
  integration-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests]
    services:
      mariadb:
        image: mariadb:11.2
        env:
          MYSQL_ROOT_PASSWORD: test
          MYSQL_DATABASE: llars_test
          MYSQL_USER: test
          MYSQL_PASSWORD: test
        ports:
          - 3306:3306
        options: --health-cmd="healthcheck.sh --connect" --health-interval=10s --health-timeout=5s --health-retries=3

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run Integration Tests
        env:
          DATABASE_URL: mysql://test:test@localhost:3306/llars_test
          REDIS_URL: redis://localhost:6379
        run: |
          pytest tests/integration/ \
            --cov=app \
            --cov-report=xml \
            -v --tb=short \
            -x  # Stop on first failure

      - name: Upload Coverage
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
          flags: integration

  # E2E Tests (braucht volle Umgebung)
  e2e-tests:
    runs-on: ubuntu-latest
    needs: [integration-tests, frontend-tests]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}

      - name: Install Playwright
        run: |
          npm install -D @playwright/test
          npx playwright install --with-deps chromium

      - name: Start LLARS (Docker Compose)
        run: |
          cp .env.template.test .env
          docker compose -f docker-compose.test.yml up -d
          ./scripts/wait-for-healthy.sh

      - name: Run E2E Tests
        run: npx playwright test --project=chromium

      - name: Upload Playwright Report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: playwright-report/

      - name: Stop LLARS
        if: always()
        run: docker compose -f docker-compose.test.yml down -v

  # Coverage Gate
  coverage-check:
    runs-on: ubuntu-latest
    needs: [unit-tests, frontend-tests, integration-tests]
    steps:
      - name: Check Coverage Threshold
        uses: codecov/codecov-action@v4
        with:
          fail_ci_if_error: true
          threshold: 70%  # Mindest-Coverage
```

### 8.2 Docker Compose Test Environment

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  # Datenbank
  db:
    image: mariadb:11.2
    environment:
      MYSQL_ROOT_PASSWORD: test
      MYSQL_DATABASE: llars_test
      MYSQL_USER: test
      MYSQL_PASSWORD: test
    healthcheck:
      test: ["CMD", "healthcheck.sh", "--connect"]
      interval: 5s
      timeout: 5s
      retries: 10

  # Redis
  redis:
    image: redis:7
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  # ChromaDB
  chromadb:
    image: chromadb/chroma:0.5.20
    environment:
      ANONYMIZED_TELEMETRY: "false"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 5s
      timeout: 5s
      retries: 10

  # YJS Server
  yjs-server:
    build:
      context: ./yjs-server
    healthcheck:
      test: ["CMD", "node", "-e", "require('net').connect(8082).on('connect', () => process.exit(0))"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Backend
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - TESTING=true
      - DATABASE_URL=mysql://test:test@db:3306/llars_test
      - REDIS_URL=redis://redis:6379
      - CHROMA_URL=http://chromadb:8000
      - YJS_URL=ws://yjs-server:8082
      - AUTHENTIK_DISABLED=true  # Mock Auth für Tests
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      chromadb:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8081/api/health"]
      interval: 10s
      timeout: 5s
      retries: 10

  # Frontend
  frontend:
    build:
      context: ./llars-frontend
      args:
        - VITE_API_URL=http://backend:8081
    depends_on:
      backend:
        condition: service_healthy

  # Nginx
  nginx:
    image: nginx:alpine
    ports:
      - "55080:80"
    volumes:
      - ./nginx/test.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
      - frontend
```

### 8.3 Coverage Requirements

```ini
# .coveragerc
[run]
source = app
omit =
    app/migrations/*
    app/db/seeders/*
    app/__pycache__/*
    */tests/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:

fail_under = 70

[html]
directory = coverage_html
```

---

## 9. Implementierungs-Roadmap

### Phase 1: Foundation (Woche 1-2)

| Task | Priorität | Aufwand |
|------|-----------|---------|
| Test-Infrastruktur aufsetzen (pytest, Vitest) | 🔴 P0 | 2h |
| conftest.py mit Basis-Fixtures | 🔴 P0 | 4h |
| CI/CD Pipeline (GitHub Actions) | 🔴 P0 | 4h |
| Docker Compose Test-Umgebung | 🔴 P0 | 3h |
| Vitest Konfiguration (Frontend) | 🟠 P1 | 2h |
| Playwright Setup | 🟠 P1 | 2h |

**Deliverables:**
- `tests/conftest.py` mit allen Fixtures
- `llars-frontend/vitest.config.js`
- `.github/workflows/test.yml`
- `docker-compose.test.yml`

### Phase 2: Critical Path Tests (Woche 3-4)

| Task | Priorität | Aufwand |
|------|-----------|---------|
| Auth Decorator Tests | 🔴 P0 | 8h |
| Permission Service Tests | 🔴 P0 | 6h |
| User Model Tests | 🔴 P0 | 4h |
| Auth Flow Integration Test | 🔴 P0 | 6h |
| useAuth.js Tests (Frontend) | 🟠 P1 | 4h |
| usePermissions.js Tests | 🟠 P1 | 4h |
| Login E2E Test | 🟠 P1 | 4h |

**Deliverables:**
- 15+ Auth Unit Tests
- 5+ Auth Integration Tests
- 2 Auth E2E Tests
- Coverage: Auth >80%

### Phase 3: RAG Pipeline Tests (Woche 5-6)

| Task | Priorität | Aufwand |
|------|-----------|---------|
| Embedding Model Service Tests | 🔴 P0 | 8h |
| Document Model Tests | 🔴 P0 | 4h |
| Collection Service Tests | 🟠 P1 | 6h |
| RAG Pipeline Integration | 🟠 P1 | 10h |
| Embedding Worker Tests | 🟠 P1 | 6h |
| Search E2E Test | 🟡 P2 | 4h |

**Deliverables:**
- 25+ RAG Unit Tests
- 10+ RAG Integration Tests
- Coverage: RAG >75%

### Phase 4: Judge & Chatbot Tests (Woche 7-8)

| Task | Priorität | Aufwand |
|------|-----------|---------|
| Judge Service Tests | 🟠 P1 | 8h |
| Judge Session Model Tests | 🟠 P1 | 4h |
| Chatbot Service Tests | 🟠 P1 | 8h |
| Wizard Flow Integration | 🟠 P1 | 8h |
| Judge E2E Test | 🟡 P2 | 6h |
| Chatbot E2E Test | 🟡 P2 | 6h |

**Deliverables:**
- 20+ Judge Unit Tests
- 20+ Chatbot Unit Tests
- 10+ Integration Tests
- 4 E2E Tests

### Phase 5: Frontend & Socket.IO (Woche 9-10)

| Task | Priorität | Aufwand |
|------|-----------|---------|
| LBtn, LTag, LSlider Tests | 🟠 P1 | 6h |
| LCard, LTabs, LActionGroup Tests | 🟡 P2 | 6h |
| Composable Tests (Auth, Permissions) | 🟠 P1 | 8h |
| Socket.IO Event Tests | 🟠 P1 | 10h |
| WebSocket Reconnection Test | 🟡 P2 | 4h |

**Deliverables:**
- 30+ Frontend Unit Tests
- 15+ Socket.IO Tests
- Coverage: Frontend >60%

### Phase 6: Collab & Performance (Woche 11-12)

| Task | Priorität | Aufwand |
|------|-----------|---------|
| YJS Sync Tests | 🟡 P2 | 8h |
| Collab E2E Test | 🟡 P2 | 6h |
| Performance Tests (RAG) | 🟡 P2 | 6h |
| Load Tests (Concurrent Users) | 🟡 P2 | 6h |
| Database Integrity Tests | 🟡 P2 | 4h |

**Deliverables:**
- 10+ Collab Tests
- Performance Baseline
- Load Test Report

---

## Anhang: Quellen & Referenzen

### Backend Testing
- [Flask Testing Documentation](https://flask.palletsprojects.com/en/stable/testing/)
- [Testing Flask Applications with Pytest](https://testdriven.io/blog/flask-pytest/)
- [pytest-flask GitHub](https://github.com/pytest-dev/pytest-flask)
- [Advanced Integration Testing for Python 2025](https://moldstud.com/articles/p-advanced-integration-testing-techniques-for-python-developers-expert-guide-2025)
- [Introduction to Testing in Python Flask](https://blog.appsignal.com/2025/04/02/an-introduction-to-testing-in-python-flask.html)

### Frontend Testing
- [Vue.js Testing Guide](https://vuejs.org/guide/scaling-up/testing)
- [Unit Testing Vue 3 with Vitest](https://medium.com/@vasanthancomrads/unit-testing-vue-3-components-with-vitest-and-testing-library-part-1-554d86aa1797)
- [Testing Vue Composables with Lifecycle Hooks](https://dylanbritz.dev/writing/testing-vue-composables-lifecycle/)
- [Vue 3 Testing Pyramid with Vitest Browser Mode](https://alexop.dev/posts/vue3_testing_pyramid_vitest_browser_mode/)
- [Vitest Tips and Tricks](https://patrickstuart.com/2025/09/16/unit-testing-vue-components-with-vitest-tips-and-tricks/)

### E2E Testing
- [Playwright vs Cypress 2025](https://www.frugaltesting.com/blog/playwright-vs-cypress-the-ultimate-2025-e2e-testing-showdown)
- [Docker + Cypress E2E Setup](https://dev.to/cypress/docker-cypress-in-2025-how-ive-perfected-my-e2e-testing-setup-4f7j)
- [Playwright Docker Tutorial](https://www.browserstack.com/guide/playwright-docker)
- [Dockerized E2E Tests with GitHub Actions](https://lachiejames.com/elevate-your-ci-cd-dockerized-e2e-tests-with-github-actions/)

### YJS & Collaborative Editing
- [YJS Documentation](https://docs.yjs.dev/)
- [y-websocket Provider](https://docs.yjs.dev/ecosystem/connection-provider/y-websocket)
- [Real-Time Collaborative Editing with Yjs](https://dev.to/hexshift/mastering-real-time-collaborative-editing-with-yjs-and-websockets-12n)
- [YJS Sync & Awareness](https://medium.com/dovetail-engineering/yjs-fundamentals-part-2-sync-awareness-73b8fabc2233)

---

**Erstellt:** 30. Dezember 2025
**Autor:** Claude Code (automatisch generiert)
**Review:** Ausstehend
