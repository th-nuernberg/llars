# [Projektname] - Umsetzung

!!! info "🔧 Status: In Umsetzung"
    Dieses Projekt wird aktuell **implementiert**.
    Siehe [Progress Template](progress-template.md) für Details.

**Konzept:** [Konzept Template](konzept-template.md)
**Erstellt:** YYYY-MM-DD
**Autor:** [Name]

---

## Übersicht

Diese Datei beschreibt die technische Umsetzung des Konzepts. Sie enthält konkreten Code und Anleitungen für die Implementierung.

### Implementierungs-Reihenfolge

1. [ ] Datenbank-Migrationen
2. [ ] Backend-Services
3. [ ] Backend-Routes
4. [ ] WebSocket-Events
5. [ ] Frontend-Komponenten
6. [ ] Integration & Testing

---

## Abhängigkeiten

### Python (Backend)

```bash
# Falls neue Packages benötigt werden
pip install package-name
```

Eintrag in `requirements.txt`:
```
package-name==1.0.0
```

### JavaScript (Frontend)

```bash
# Falls neue Packages benötigt werden
cd llars-frontend
npm install package-name
```

---

## Datenbank

### Neue Models

**Datei:** `app/db/tables.py`

```python
class ResourceName(db.Model):
    """
    Beschreibung der Ressource.
    """
    __tablename__ = 'resource_name'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    config = db.Column(db.JSON, nullable=True, default=dict)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow, nullable=True)

    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('resources', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'config': self.config,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_id': self.user_id
        }
```

### Migration

Nach dem Hinzufügen der Models:

```bash
docker compose exec backend-flask-service flask db migrate -m "Add ResourceName table"
docker compose exec backend-flask-service flask db upgrade
```

---

## Backend-Services

### Service-Klasse

**Datei:** `app/services/resource/resource_service.py`

```python
from app.db.db import db
from app.db.tables import ResourceName
from typing import Optional, List
from datetime import datetime


class ResourceService:
    """Service für ResourceName Operationen."""

    @staticmethod
    def get_all(user_id: Optional[int] = None) -> List[ResourceName]:
        """Alle Ressourcen abrufen, optional gefiltert nach User."""
        query = ResourceName.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        return query.order_by(ResourceName.created_at.desc()).all()

    @staticmethod
    def get_by_id(resource_id: int) -> Optional[ResourceName]:
        """Einzelne Ressource nach ID abrufen."""
        return ResourceName.query.get(resource_id)

    @staticmethod
    def create(name: str, user_id: int, description: str = None, config: dict = None) -> ResourceName:
        """Neue Ressource erstellen."""
        resource = ResourceName(
            name=name,
            description=description,
            config=config or {},
            user_id=user_id
        )
        db.session.add(resource)
        db.session.commit()
        return resource

    @staticmethod
    def update(resource_id: int, **kwargs) -> Optional[ResourceName]:
        """Ressource aktualisieren."""
        resource = ResourceName.query.get(resource_id)
        if not resource:
            return None

        for key, value in kwargs.items():
            if hasattr(resource, key):
                setattr(resource, key, value)

        resource.updated_at = datetime.utcnow()
        db.session.commit()
        return resource

    @staticmethod
    def delete(resource_id: int) -> bool:
        """Ressource löschen."""
        resource = ResourceName.query.get(resource_id)
        if not resource:
            return False

        db.session.delete(resource)
        db.session.commit()
        return True
```

---

## Backend-Routes

### Route-Blueprint

**Datei:** `app/routes/resource/resource_routes.py`

```python
from flask import Blueprint, request, jsonify, g
from app.services.resource.resource_service import ResourceService
from app.decorators.permission_decorator import require_permission
from app.auth.oidc_validator import get_token_from_request, validate_token

resource_blueprint = Blueprint('resource', __name__, url_prefix='/api/resource')


def get_current_user():
    """Aktuellen User aus Token extrahieren."""
    token = get_token_from_request()
    if token:
        payload = validate_token(token)
        if payload:
            return payload.get('preferred_username')
    return None


@resource_blueprint.route('', methods=['GET'])
@require_permission('feature:resource:view')
def get_all_resources():
    """Alle Ressourcen abrufen."""
    resources = ResourceService.get_all()
    return jsonify({
        'items': [r.to_dict() for r in resources],
        'total': len(resources)
    })


@resource_blueprint.route('/<int:resource_id>', methods=['GET'])
@require_permission('feature:resource:view')
def get_resource(resource_id):
    """Einzelne Ressource abrufen."""
    resource = ResourceService.get_by_id(resource_id)
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404
    return jsonify(resource.to_dict())


@resource_blueprint.route('', methods=['POST'])
@require_permission('feature:resource:edit')
def create_resource():
    """Neue Ressource erstellen."""
    data = request.get_json()

    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400

    # User ID aus Session/Token holen (anpassen je nach Auth-Setup)
    user_id = g.get('user_id', 1)  # Fallback für Development

    resource = ResourceService.create(
        name=data['name'],
        user_id=user_id,
        description=data.get('description'),
        config=data.get('config')
    )

    return jsonify(resource.to_dict()), 201


@resource_blueprint.route('/<int:resource_id>', methods=['PUT'])
@require_permission('feature:resource:edit')
def update_resource(resource_id):
    """Ressource aktualisieren."""
    data = request.get_json()

    resource = ResourceService.update(resource_id, **data)
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404

    return jsonify(resource.to_dict())


@resource_blueprint.route('/<int:resource_id>', methods=['DELETE'])
@require_permission('feature:resource:delete')
def delete_resource(resource_id):
    """Ressource löschen."""
    success = ResourceService.delete(resource_id)
    if not success:
        return jsonify({'error': 'Resource not found'}), 404

    return jsonify({'message': 'Resource deleted successfully'})
```

### Blueprint registrieren

**Datei:** `app/main.py`

```python
# Import hinzufügen
from app.routes.resource.resource_routes import resource_blueprint

# Blueprint registrieren (in create_app oder nach app-Initialisierung)
app.register_blueprint(resource_blueprint)
```

---

## WebSocket-Events

### Event-Handler

**Datei:** `app/socketio_handlers/events_resource.py`

```python
from flask_socketio import emit, join_room, leave_room
from app import socketio
from app.services.resource.resource_service import ResourceService


@socketio.on('resource:join')
def handle_join_resource(data):
    """Tritt einem Resource-Room bei."""
    resource_id = data.get('resource_id')
    if resource_id:
        room = f'resource-{resource_id}'
        join_room(room)
        emit('resource:joined', {'room': room, 'resource_id': resource_id})


@socketio.on('resource:leave')
def handle_leave_resource(data):
    """Verlässt einen Resource-Room."""
    resource_id = data.get('resource_id')
    if resource_id:
        room = f'resource-{resource_id}'
        leave_room(room)
        emit('resource:left', {'room': room, 'resource_id': resource_id})


def broadcast_resource_update(resource_id: int, event_type: str, data: dict):
    """Broadcast Update an alle Clients im Room."""
    room = f'resource-{resource_id}'
    socketio.emit('resource:update', {
        'resource_id': resource_id,
        'event_type': event_type,
        'data': data
    }, room=room)
```

### Events registrieren

**Datei:** `app/socketio_handlers/__init__.py`

```python
# Import hinzufügen
from app.socketio_handlers import events_resource
```

---

## Frontend-Komponenten

### API-Service

**Datei:** `llars-frontend/src/services/resourceService.js`

```javascript
import axios from 'axios'

const API_BASE = '/api/resource'

export const resourceService = {
  async getAll() {
    const response = await axios.get(API_BASE)
    return response.data
  },

  async getById(id) {
    const response = await axios.get(`${API_BASE}/${id}`)
    return response.data
  },

  async create(data) {
    const response = await axios.post(API_BASE, data)
    return response.data
  },

  async update(id, data) {
    const response = await axios.put(`${API_BASE}/${id}`, data)
    return response.data
  },

  async delete(id) {
    const response = await axios.delete(`${API_BASE}/${id}`)
    return response.data
  }
}
```

### Overview-Komponente

**Datei:** `llars-frontend/src/components/Resource/ResourceOverview.vue`

```vue
<template>
  <v-container>
    <!-- Header -->
    <v-row class="mb-4">
      <v-col>
        <h1 class="text-h4">Resources</h1>
      </v-col>
      <v-col cols="auto">
        <v-btn
          v-if="hasPermission('feature:resource:edit')"
          color="primary"
          @click="openCreateDialog"
        >
          <v-icon left>mdi-plus</v-icon>
          Neu erstellen
        </v-btn>
      </v-col>
    </v-row>

    <!-- Stats Cards -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" lg="3">
        <v-skeleton-loader v-if="isLoading('stats')" type="card" height="100" />
        <v-card v-else class="stat-card">
          <v-card-text>
            <div class="text-h4">{{ stats.total }}</div>
            <div class="text-caption">Gesamt</div>
          </v-card-text>
        </v-card>
      </v-col>
      <!-- Weitere Stats... -->
    </v-row>

    <!-- Datentabelle -->
    <v-skeleton-loader
      v-if="isLoading('table')"
      type="table-heading, table-thead, table-tbody"
    />
    <v-card v-else>
      <v-data-table
        :headers="headers"
        :items="resources"
        :loading="loading"
        @click:row="(event, { item }) => goToDetail(item.id)"
      >
        <template #item.created_at="{ item }">
          {{ formatDate(item.created_at) }}
        </template>
        <template #item.actions="{ item }">
          <v-btn
            v-if="hasPermission('feature:resource:delete')"
            icon
            size="small"
            @click.stop="confirmDelete(item)"
          >
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Create Dialog -->
    <v-dialog v-model="createDialog" max-width="500">
      <v-card>
        <v-card-title>Neue Resource</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="newResource.name"
            label="Name"
            required
          />
          <v-textarea
            v-model="newResource.description"
            label="Beschreibung"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="createDialog = false">Abbrechen</v-btn>
          <v-btn color="primary" @click="createResource">Erstellen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePermissions } from '@/composables/usePermissions'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { resourceService } from '@/services/resourceService'

const router = useRouter()
const { hasPermission } = usePermissions()
const { isLoading, setLoading } = useSkeletonLoading(['stats', 'table'])

const resources = ref([])
const stats = ref({ total: 0 })
const loading = ref(false)
const createDialog = ref(false)
const newResource = ref({ name: '', description: '' })

const headers = [
  { title: 'Name', key: 'name' },
  { title: 'Erstellt', key: 'created_at' },
  { title: 'Aktionen', key: 'actions', sortable: false }
]

onMounted(async () => {
  await loadData()
})

async function loadData() {
  setLoading('stats', true)
  setLoading('table', true)

  try {
    const data = await resourceService.getAll()
    resources.value = data.items
    stats.value.total = data.total
  } finally {
    setLoading('stats', false)
    setLoading('table', false)
  }
}

function goToDetail(id) {
  router.push(`/resource/${id}`)
}

function openCreateDialog() {
  newResource.value = { name: '', description: '' }
  createDialog.value = true
}

async function createResource() {
  try {
    await resourceService.create(newResource.value)
    createDialog.value = false
    await loadData()
  } catch (error) {
    console.error('Fehler beim Erstellen:', error)
  }
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('de-DE')
}
</script>
```

### Routing hinzufügen

**Datei:** `llars-frontend/src/router.js`

```javascript
// Import hinzufügen
import ResourceOverview from '@/components/Resource/ResourceOverview.vue'
import ResourceDetail from '@/components/Resource/ResourceDetail.vue'

// Routes hinzufügen
{
  path: '/resource',
  name: 'ResourceOverview',
  component: ResourceOverview,
  meta: { requiresAuth: true, permission: 'feature:resource:view' }
},
{
  path: '/resource/:id',
  name: 'ResourceDetail',
  component: ResourceDetail,
  meta: { requiresAuth: true, permission: 'feature:resource:view' }
}
```

---

## Testing

### Backend-Tests

```bash
# Service testen
docker compose exec backend-flask-service pytest app/tests/test_resource_service.py -v

# Routes testen
docker compose exec backend-flask-service pytest app/tests/test_resource_routes.py -v
```

### Frontend-Tests

```bash
cd llars-frontend
npm run test -- --grep "Resource"
```

### Manueller Test

1. Backend starten: `./start_llars.sh`
2. Browser öffnen: `http://localhost:55080/resource`
3. Prüfen:
   - [ ] Liste wird geladen
   - [ ] Skeleton Loading funktioniert
   - [ ] Erstellen funktioniert
   - [ ] Detail-Ansicht funktioniert
   - [ ] Löschen funktioniert
   - [ ] Permissions werden beachtet

---

## Rollback

Falls etwas schief geht:

```bash
# Datenbank-Migration rückgängig machen
docker compose exec backend-flask-service flask db downgrade

# Oder komplett neu starten
REMOVE_LLARS_VOLUMES=True ./start_llars.sh
```
