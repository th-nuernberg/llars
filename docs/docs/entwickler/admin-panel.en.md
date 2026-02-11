# Admin Panel Guide

This guide documents the features of the LLARS admin panel.

!!! info "Access"
    The admin panel is available at `/admin` and requires the `admin` role.

---

## Overview

The admin panel provides the following areas:

| Area | Description | Permission |
|------|-------------|------------|
| **Dashboard** | System overview and statistics | `admin:dashboard:view` |
| **Users** | User management | `admin:users:view` |
| **Chatbots** | Chatbot activity | `admin:chatbots:view` |
| **RAG** | Document management | `admin:rag:view` |
| **Docker Monitor** | Container monitoring | `admin:docker:view` |
| **Database** | DB explorer | `admin:database:view` |
| **Analytics** | Matomo settings | `admin:analytics:view` |
| **System** | System settings | `admin:settings:view` |

---

## Docker Monitor

The Docker monitor shows real-time information about all LLARS containers.

### Features

#### Container list

Shows all containers with:

- **Status**: Running/Stopped/Restarting
- **CPU usage**: Percentage CPU usage
- **RAM usage**: Memory usage in MB/GB
- **Network**: Incoming/Outgoing traffic

#### Performance charts

Real-time charts for:

- CPU history (last 5 minutes)
- Memory history (last 5 minutes)
- Network traffic

#### Container logs

Live streaming of container logs with:

- Auto scroll
- Log level filtering
- Download as text file

### Usage

1. Navigate to **Admin → Docker Monitor**
2. Select a container from the list
3. Logs stream automatically
4. Charts update in real time

### Technical details

```javascript
// WebSocket connection for Docker Monitor
socket.emit('docker:subscribe')

// Events
socket.on('docker:stats', (data) => {
  // data = { containers: [...], summary: {...} }
})

socket.on('docker:logs', (data) => {
  // data = { container_id, logs: [...] }
})
```

!!! warning "Security note"
    The Docker monitor requires access to `/var/run/docker.sock`.
    This grants potential host Docker control.
    **Only enable for trusted admins.**

---

## Database Explorer

The DB explorer provides read-only access to LLARS tables.

### Features

- **Table browser**: List all tables
- **Data viewer**: Display table contents
- **Filtering**: Column-based filters
- **Sorting**: Column-based sorting
- **Pagination**: Page through large tables
- **Export**: CSV download

### Usage

1. Navigate to **Admin → Database**
2. Select a table from the sidebar
3. Use filters and sorting options
4. Export as CSV if needed

### Technical details

```javascript
// WebSocket events for DB Explorer
socket.emit('db:list_tables')
socket.on('db:tables', (tables) => { ... })

socket.emit('db:query', {
  table: 'users',
  limit: 50,
  offset: 0,
  order_by: 'created_at',
  order_dir: 'desc'
})
socket.on('db:result', (data) => { ... })
```

!!! note "Read-only"
    The DB explorer is **read-only**. Data changes are
    not possible through this interface.

---

## Analytics Settings

Configuration of the Matomo integration.

### Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `tracking_enabled` | Enable tracking | `true` |
| `track_user_id` | Track user ID | `false` |
| `track_search` | Track search terms | `true` |
| `cookie_consent_required` | Require cookie consent | `true` |

### API

```http
GET /api/admin/analytics/settings
```

```json
{
  "success": true,
  "settings": {
    "tracking_enabled": true,
    "track_user_id": false,
    "track_search": true,
    "cookie_consent_required": true,
    "matomo_site_id": 1
  }
}
```

```http
PATCH /api/admin/analytics/settings
Content-Type: application/json

{
  "tracking_enabled": false
}
```

---

## User Management

### User list

Shows all users with:

- Username and email
- Roles
- Last login
- Actions (edit, deactivate)

### Edit permissions

1. Click **Edit** for a user
2. Select roles from the list
3. Add/remove individual permissions
4. Save

### Bulk actions

- Select multiple users
- Assign role
- Deactivate

---

## Chatbot Activity

### Overview

- Number of active chatbots
- Total conversations
- Messages per day (chart)

### Per-chatbot details

- Conversation statistics
- Most common questions
- Average response time
- Error rate

### Export

- Export conversations as JSON/CSV
- Select time range
- Filter by chatbot

---

## RAG Management

### Collections overview

| Column | Description |
|--------|-------------|
| Name | Collection name |
| Documents | Number of documents |
| Chunks | Number of chunks |
| Size | Total size |
| Status | Indexing status |

### Document queue

Shows all documents in the processing queue:

- **Pending**: Waiting for processing
- **Processing**: Currently processing
- **Indexed**: Finished
- **Failed**: Error during processing
