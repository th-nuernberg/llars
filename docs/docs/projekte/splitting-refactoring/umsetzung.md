# Splitting & Refactoring - Umsetzung

!!! info "🔧 Status: Bereit zur Umsetzung"
    Dieses Dokument enthält die konkreten Implementierungsschritte.
    Siehe [Progress](progress.md) für den aktuellen Stand.

**Konzept:** [Splitting & Refactoring Konzept](konzept.md)
**Erstellt:** 2025-11-28
**Autor:** Claude Code

---

## Übersicht

Dieses Dokument beschreibt die schrittweise Umsetzung des Splittings. Jede Phase enthält konkreten Code und Anleitungen.

### Implementierungs-Reihenfolge

1. [x] Phase 1: Backend Models (`tables.py`)
2. [ ] Phase 2: Backend Routes (`judge_routes.py`)
3. [ ] Phase 3: Frontend Judge (`JudgeSession.vue`)
4. [ ] Phase 4: Backend Routes (oncoco, RAG)
5. [ ] Phase 5: Frontend OnCoCo & Admin
6. [ ] Phase 6: Restliche Dateien

---

## Phase 1: Backend Models (tables.py)

### Ziel
`app/db/tables.py` (1.260 Zeilen) → 8 Model-Dateien (je ~150 Zeilen)

### Schritt 1.1: Ordnerstruktur erstellen

```bash
mkdir -p app/db/models
touch app/db/models/__init__.py
```

### Schritt 1.2: Base-Konfiguration

**Datei:** `app/db/models/__init__.py`

```python
"""
LLARS Database Models

Alle Models sind hier re-exportiert für Backwards Compatibility.
Import: from app.db.models import User, Permission, JudgeSession
"""

from app.db.models.user import User, UserGroup, UserRole
from app.db.models.permission import Permission, Role, RolePermission, UserPermission, PermissionAuditLog
from app.db.models.judge import JudgeSession, JudgeComparison, JudgeEvaluation
from app.db.models.rag import RAGCollection, RAGDocument, RAGDocumentChunk
from app.db.models.chatbot import Chatbot, ChatbotCollection, ChatbotConversation, ChatbotMessage
from app.db.models.oncoco import OnCoCoAnalysis, OnCoCoSentenceLabel
from app.db.models.pillar import PillarThread, PillarStatistics
from app.db.models.scenario import RatingScenario, MailRating, EmailThread, Message

__all__ = [
    # User
    'User', 'UserGroup', 'UserRole',
    # Permission
    'Permission', 'Role', 'RolePermission', 'UserPermission', 'PermissionAuditLog',
    # Judge
    'JudgeSession', 'JudgeComparison', 'JudgeEvaluation',
    # RAG
    'RAGCollection', 'RAGDocument', 'RAGDocumentChunk',
    # Chatbot
    'Chatbot', 'ChatbotCollection', 'ChatbotConversation', 'ChatbotMessage',
    # OnCoCo
    'OnCoCoAnalysis', 'OnCoCoSentenceLabel',
    # Pillar
    'PillarThread', 'PillarStatistics',
    # Scenario
    'RatingScenario', 'MailRating', 'EmailThread', 'Message',
]
```

### Schritt 1.3: User Models

**Datei:** `app/db/models/user.py`

```python
"""User-related database models."""

from datetime import datetime
from app.db.db import db


class User(db.Model):
    """User model for authentication and authorization."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True)
    display_name = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships
    groups = db.relationship('UserGroup', secondary='user_group_members', back_populates='users')
    roles = db.relationship('UserRole', back_populates='user')
    permissions = db.relationship('UserPermission', back_populates='user')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'display_name': self.display_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class UserGroup(db.Model):
    """Group model for organizing users."""
    __tablename__ = 'user_groups'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('User', secondary='user_group_members', back_populates='groups')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
        }


# Association table for User-Group many-to-many
user_group_members = db.Table(
    'user_group_members',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('user_groups.id'), primary_key=True),
)


class UserRole(db.Model):
    """Maps users to roles."""
    __tablename__ = 'user_roles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_by = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', back_populates='roles')
    role = db.relationship('Role', back_populates='user_roles')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'role_id': self.role_id,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
        }
```

### Schritt 1.4: Permission Models

**Datei:** `app/db/models/permission.py`

```python
"""Permission and Role database models."""

from datetime import datetime
from app.db.db import db


class Permission(db.Model):
    """Individual permission definition."""
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    key = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'name': self.name,
            'description': self.description,
            'category': self.category,
        }


class Role(db.Model):
    """Role definition with associated permissions."""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_system = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    permissions = db.relationship('RolePermission', back_populates='role')
    user_roles = db.relationship('UserRole', back_populates='role')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_system': self.is_system,
        }


class RolePermission(db.Model):
    """Maps roles to permissions."""
    __tablename__ = 'role_permissions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=False)

    role = db.relationship('Role', back_populates='permissions')
    permission = db.relationship('Permission')


class UserPermission(db.Model):
    """Direct user permission overrides."""
    __tablename__ = 'user_permissions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=False)
    granted = db.Column(db.Boolean, default=True)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_by = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', back_populates='permissions')
    permission = db.relationship('Permission')


class PermissionAuditLog(db.Model):
    """Audit trail for permission changes."""
    __tablename__ = 'permission_audit_log'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    actor = db.Column(db.String(255), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    target_user = db.Column(db.String(255), nullable=True)
    target_role = db.Column(db.String(255), nullable=True)
    permission_key = db.Column(db.String(255), nullable=True)
    details = db.Column(db.JSON, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'actor': self.actor,
            'action': self.action,
            'target_user': self.target_user,
            'target_role': self.target_role,
            'permission_key': self.permission_key,
            'details': self.details,
        }
```

### Schritt 1.5: Weitere Model-Dateien

Die weiteren Model-Dateien (`judge.py`, `rag.py`, `chatbot.py`, `oncoco.py`, `pillar.py`, `scenario.py`) folgen dem gleichen Muster. Jede Datei enthält die zugehörigen Models aus `tables.py`.

### Schritt 1.6: tables.py aktualisieren (Backwards Compatibility)

**Datei:** `app/db/tables.py`

```python
"""
DEPRECATED: Use app.db.models instead.

This file is kept for backwards compatibility.
All models are re-exported from app.db.models.
"""

import warnings

warnings.warn(
    "Importing from app.db.tables is deprecated. Use app.db.models instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all models for backwards compatibility
from app.db.models import *
```

### Schritt 1.7: Validierung

```bash
# Prüfen ob alle Imports funktionieren
docker compose exec backend-flask-service python -c "from app.db.models import User, Permission, JudgeSession; print('OK')"

# Prüfen ob alte Imports noch funktionieren
docker compose exec backend-flask-service python -c "from app.db.tables import User; print('OK')"

# Tests ausführen
docker compose exec backend-flask-service pytest app/tests/ -v
```

---

## Phase 2: Backend Routes (judge_routes.py)

### Ziel
`app/routes/judge/judge_routes.py` (2.596 Zeilen) → 6 Route-Dateien (je ~400 Zeilen)

### Schritt 2.1: Neue Dateien erstellen

```bash
touch app/routes/judge/session_routes.py
touch app/routes/judge/comparison_routes.py
touch app/routes/judge/evaluation_routes.py
touch app/routes/judge/kia_sync_routes.py
touch app/routes/judge/statistics_routes.py
touch app/routes/judge/stream_routes.py
```

### Schritt 2.2: Blueprint-Struktur

**Datei:** `app/routes/judge/__init__.py`

```python
"""
Judge Routes Module

Stellt alle Judge-bezogenen API-Endpoints bereit.
"""

from flask import Blueprint

# Haupt-Blueprint
judge_blueprint = Blueprint('judge', __name__, url_prefix='/api/judge')

# Sub-Blueprints importieren und registrieren
from app.routes.judge.session_routes import session_bp
from app.routes.judge.comparison_routes import comparison_bp
from app.routes.judge.evaluation_routes import evaluation_bp
from app.routes.judge.kia_sync_routes import kia_sync_bp
from app.routes.judge.statistics_routes import statistics_bp
from app.routes.judge.stream_routes import stream_bp

judge_blueprint.register_blueprint(session_bp)
judge_blueprint.register_blueprint(comparison_bp)
judge_blueprint.register_blueprint(evaluation_bp)
judge_blueprint.register_blueprint(kia_sync_bp)
judge_blueprint.register_blueprint(statistics_bp)
judge_blueprint.register_blueprint(stream_bp)

__all__ = ['judge_blueprint']
```

### Schritt 2.3: Session Routes

**Datei:** `app/routes/judge/session_routes.py`

```python
"""Session management routes for LLM-as-Judge."""

from flask import Blueprint, request, jsonify
from app.decorators.permission_decorator import require_permission

session_bp = Blueprint('judge_sessions', __name__)


@session_bp.route('/sessions', methods=['GET'])
@require_permission('feature:comparison:view')
def get_sessions():
    """List all judge sessions."""
    # Implementation aus judge_routes.py verschieben
    pass


@session_bp.route('/sessions', methods=['POST'])
@require_permission('feature:comparison:edit')
def create_session():
    """Create a new judge session."""
    pass


@session_bp.route('/sessions/<int:session_id>', methods=['GET'])
@require_permission('feature:comparison:view')
def get_session(session_id):
    """Get a specific session by ID."""
    pass


@session_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@require_permission('feature:comparison:edit')
def delete_session(session_id):
    """Delete a session."""
    pass


@session_bp.route('/sessions/<int:session_id>/start', methods=['POST'])
@require_permission('feature:comparison:edit')
def start_session(session_id):
    """Start a session."""
    pass


@session_bp.route('/sessions/<int:session_id>/pause', methods=['POST'])
@require_permission('feature:comparison:edit')
def pause_session(session_id):
    """Pause a running session."""
    pass
```

### Schritt 2.4-2.8: Weitere Route-Dateien

Analog zu `session_routes.py` werden die anderen Route-Dateien erstellt.

---

## Phase 3: Frontend Judge (JudgeSession.vue)

### Ziel
`JudgeSession.vue` (4.191 Zeilen) → 8+ Komponenten (je ~300 Zeilen)

### Schritt 3.1: Ordnerstruktur

```bash
mkdir -p llars-frontend/src/components/Judge/JudgeSession
mkdir -p llars-frontend/src/components/Judge/JudgeSession/composables
```

### Schritt 3.2: Composables extrahieren

**Datei:** `llars-frontend/src/components/Judge/JudgeSession/composables/useSessionSocket.js`

```javascript
/**
 * Socket.IO connection management for Judge Sessions
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { getSocket } from '@/services/socketService'

export function useSessionSocket(sessionId) {
  const socket = ref(null)
  const isConnected = ref(false)
  const connectionError = ref(null)

  const connect = () => {
    socket.value = getSocket()

    socket.value.on('connect', () => {
      isConnected.value = true
      socket.value.emit('judge:join_session', { session_id: sessionId.value })
    })

    socket.value.on('disconnect', () => {
      isConnected.value = false
    })

    socket.value.on('connect_error', (error) => {
      connectionError.value = error.message
    })
  }

  const disconnect = () => {
    if (socket.value) {
      socket.value.emit('judge:leave_session', { session_id: sessionId.value })
      socket.value.disconnect()
    }
  }

  onMounted(() => connect())
  onUnmounted(() => disconnect())

  return {
    socket,
    isConnected,
    connectionError,
    connect,
    disconnect,
  }
}
```

### Schritt 3.3: Sub-Komponenten erstellen

**Datei:** `llars-frontend/src/components/Judge/JudgeSession/SessionHeader.vue`

```vue
<template>
  <v-card class="mb-4">
    <v-card-title class="d-flex align-center">
      <v-icon class="mr-2">mdi-gavel</v-icon>
      <span>{{ session?.name || 'Judge Session' }}</span>
      <v-spacer />
      <v-chip :color="statusColor" class="ml-2">
        {{ session?.status }}
      </v-chip>
    </v-card-title>
    <v-card-text>
      <v-row>
        <v-col cols="3">
          <div class="text-h4">{{ progress.completed }}</div>
          <div class="text-caption">Abgeschlossen</div>
        </v-col>
        <v-col cols="3">
          <div class="text-h4">{{ progress.total }}</div>
          <div class="text-caption">Gesamt</div>
        </v-col>
        <v-col cols="3">
          <div class="text-h4">{{ progress.queued }}</div>
          <div class="text-caption">In Queue</div>
        </v-col>
        <v-col cols="3">
          <div class="text-h4">{{ activeWorkers }}</div>
          <div class="text-caption">Aktive Worker</div>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  session: Object,
  progress: Object,
  activeWorkers: Number,
})

const statusColor = computed(() => {
  const colors = {
    created: 'grey',
    running: 'success',
    paused: 'warning',
    completed: 'info',
    failed: 'error',
  }
  return colors[props.session?.status] || 'grey'
})
</script>
```

### Schritt 3.4: Haupt-Komponente refaktorieren

**Datei:** `llars-frontend/src/components/Judge/JudgeSession/JudgeSession.vue`

```vue
<template>
  <v-container fluid>
    <!-- Header -->
    <SessionHeader
      :session="session"
      :progress="progress"
      :active-workers="activeWorkers"
    />

    <!-- Controls -->
    <SessionControls
      :session="session"
      :is-running="isRunning"
      @start="startSession"
      @pause="pauseSession"
      @stop="stopSession"
    />

    <!-- Worker Grid -->
    <WorkerGrid
      :workers="workers"
      :comparisons="activeComparisons"
    />

    <!-- Queue -->
    <ComparisonQueue
      :queue="queue"
      :loading="loadingQueue"
    />
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useSessionSocket } from './composables/useSessionSocket'
import { useSessionState } from './composables/useSessionState'

import SessionHeader from './SessionHeader.vue'
import SessionControls from './SessionControls.vue'
import WorkerGrid from './WorkerGrid.vue'
import ComparisonQueue from './ComparisonQueue.vue'

const route = useRoute()
const sessionId = computed(() => route.params.id)

// Socket connection
const { socket, isConnected } = useSessionSocket(sessionId)

// Session state
const {
  session,
  workers,
  queue,
  progress,
  loadSession,
  startSession,
  pauseSession,
} = useSessionState(sessionId, socket)

// Computed
const isRunning = computed(() => session.value?.status === 'running')
const activeWorkers = computed(() => workers.value.filter(w => w.active).length)

onMounted(() => {
  loadSession()
})
</script>
```

---

## Validierung nach jeder Phase

### Checkliste

```bash
# 1. Syntax-Check
docker compose exec backend-flask-service python -m py_compile app/routes/judge/__init__.py

# 2. Import-Check
docker compose exec backend-flask-service python -c "from app.routes.judge import judge_blueprint; print('OK')"

# 3. Tests
docker compose exec backend-flask-service pytest app/tests/ -v --tb=short

# 4. Lint
docker compose exec backend-flask-service flake8 app/routes/judge/

# 5. Frontend Build
cd llars-frontend && npm run build

# 6. Anwendung starten und testen
./start_llars.sh
```

---

## Rollback-Strategie

Falls etwas schief geht:

```bash
# Git-Status prüfen
git status

# Änderungen verwerfen
git checkout -- app/routes/judge/

# Oder: Letzten Commit rückgängig
git revert HEAD
```

---

## Nächste Schritte nach Abschluss

1. Alte Dateien mit Deprecation-Warnings versehen
2. Dokumentation aktualisieren (CLAUDE.md)
3. Team über neue Struktur informieren
4. In 2-3 Monaten: Alte Re-Exports entfernen
