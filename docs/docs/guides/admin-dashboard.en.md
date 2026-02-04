# Admin Dashboard

**Version:** 1.1 | **Date:** January 2026

The Admin Dashboard is the central management interface for LLARS. Administrators manage users, scenarios, chatbots, RAG data, LLM providers, system settings, and live monitoring.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Admin Dashboard                                                            │
├──────────────┬──────────────────────────────────────────────────────────────┤
│  Navigation  │  Overview                                                    │
│  ──────────  │  ─────────────────────────────────────────────────────────   │
│              │                                                              │
│  📊 Overview │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  📈 Analytics│  │ Users    │ │ Scenarios│ │RAG Docs  │ │Completion│       │
│  🫀 Health   │  │    42    │ │    15    │ │   234    │ │   78%    │       │
│  🖥 System   │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  👥 Users    │                                                              │
│  📋 Scenarios│  Recent Activity                                             │
│  🤖 Chatbots │  Quick Actions                                               │
│  📄 RAG      │  Active Scenarios                                            │
│  🔐 Permissions                                                         │
│  🔧 LLM      │  System Health                                               │
│  ⚙️ Settings │                                                              │
│  …           │  (more tabs: Presence, Chatbot Activity, Docker, DB, …)      │
└──────────────┴──────────────────────────────────────────────────────────────┘
```

---

## Quick Start

!!! tip "Most Important Admin Tasks"
    1. **Manage users** → assign roles, lock accounts
    2. **Monitor scenarios** → check progress, detect bottlenecks
    3. **LLM providers & models** → configure providers, review costs
    4. **System health** → watch CPU/RAM, events, errors
    5. **RAG & crawler** → keep collections and documents up to date

---

## Sections

### Overview

The Overview tab shows:

- **KPI cards** (users, active scenarios, RAG documents, completion rate)
- **System health bar** (quick status)
- **Recent activity** (with event detail dialog)
- **Quick actions** (e.g., open Matomo, create scenario)
- **Active scenarios** (progress table)

---

### Analytics (Matomo)

Configure Matomo tracking:

- Enable/disable tracking
- User ID, click/hover tracking, heartbeat
- Privacy options (e.g., no cookies)
- **Open Matomo** button

---

### Users

User management with search and role filter:

- Create, lock/unlock, delete users
- Assign/remove roles
- View effective permissions

**User Status**

| Status | Description |
|--------|-------------|
| **Active** | Normal account |
| **Locked** | Login disabled |
| **Deleted** | Soft delete (data retained) |

**Roles (Examples)**

| Role | Permissions |
|------|-------------|
| **Admin** | Full access |
| **Researcher** | Scenarios + prompt engineering |
| **Evaluator** | Participate in evaluations |
| **Chatbot Manager** | Manage chatbots and RAG |

---

### Scenarios

Admin overview of all scenarios:

- List with type, start date, status
- Detailed stats (progress, items, agreement)

---

### Chatbots

Central management for all chatbots:

- Start chatbot wizard
- Settings, collections, tests
- Access control by roles/users

---

### Chatbot Activity

Monitoring of chatbot-related events:

- Chats, wizard status, documents, collections
- Filters by time, user, type

---

### RAG

RAG admin with statistics and embedding info:

- **Stats**: documents, processed, collections, total size
- **Embedding model**: active model, dimensions, provider status
- **Tabs**: Documents, Collections, Upload

---

### Crawler

Web crawler for RAG ingestion:

- Add sources
- View crawl status and errors
- Defaults via System Settings (pages/depth/timeouts)

---

### Field Prompts (AI Assist)

Prompt templates for AI field assistance:

- Seed defaults
- Create, test, enable/disable prompts

---

### Permissions

Multi-tab interface:

- **Roles** (view/create)
- **Permissions** (grouped)
- **Chatbots** (access allowlist)
- **LLM Models** (access allowlist)
- **Audit Log** (change history)

---

### LLM Providers

Provider and model management:

- Quick connect (OpenAI, Anthropic, LiteLLM, Ollama)
- Test and sync providers
- Configure models (costs, context window, capabilities)

---

### Referrals

Referral system for invitations:

- Manage campaigns and links
- Review registrations
- Status: active, archived, deactivated

---

### Presence

Live user presence:

- Online/Active/Offline status
- Search and filters
- Last activity and last seen

---

### Docker Monitor

Live container monitoring:

- Status, health, CPU/RAM
- Network traffic (RX/TX)
- Container list with live updates

---

### DB Explorer

Direct read-only view of DB tables:

- Table list with search
- Limit/filter
- Data preview

---

### System Health

System status with metrics:

- Host metrics (CPU/RAM/Disk)
- API performance
- WebSocket status

---

### System Events

Live event stream with filtering:

- Severity filters (info/warn/error)
- Search by type/message/user
- Event detail dialog (entity, ID, JSON copy)

---

### System Settings

Global configuration:

- **Crawler timeouts** (crawl + embedding)
- **Crawler defaults** (max pages/depth)
- **RAG chunking** (chunk size/overlap)
- **LLM logging** (prompts/responses, tasks, max chars)
- **Referral system** (enable, self-registration, default role)
- **AI assistant** (enable, username, color)
- **Zotero OAuth** (env vs DB fallback)

---

## API Endpoints

### Users

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/users` | GET | List users |
| `/api/admin/users` | POST | Create user |
| `/api/admin/users/:username` | PATCH | Update user |
| `/api/admin/users/:username` | DELETE | Delete user |

### Scenarios

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/scenarios` | GET | List scenarios |
| `/api/admin/scenario_progress_stats/:id` | GET | Progress statistics |

### Permissions

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/permissions` | GET | All permissions |
| `/api/permissions/roles` | GET/POST | List/create roles |
| `/api/permissions/roles/:role/permissions` | PUT | Set role permissions |
| `/api/permissions/user/:username` | GET | User permissions + roles |
| `/api/permissions/grant` | POST | Grant permission |
| `/api/permissions/revoke` | POST | Revoke permission |
| `/api/permissions/assign-role` | POST | Assign role |
| `/api/permissions/unassign-role` | POST | Unassign role |
| `/api/permissions/audit-log` | GET | Audit log |

### LLM

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/llm/providers` | GET/POST | Manage providers |
| `/api/llm/providers/:id/test` | POST | Test connection |
| `/api/llm/providers/:id/sync-models` | POST | Sync models |
| `/api/llm/models` | GET/POST | Manage models |
| `/api/llm/models/:id/set-default` | POST | Set default |

### Analytics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/analytics/settings` | GET/PATCH | Matomo settings |

### System

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/system/settings` | GET/PATCH | System settings |
| `/api/admin/system/events` | GET | Event list (filters/limit) |
| `/api/admin/system/events/stream` | GET | Event stream (SSE) |

### Referrals

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/referral/admin/campaigns` | GET/POST | Manage campaigns |
| `/api/referral/admin/campaigns/:id` | GET/PUT/DELETE | Read/update/delete campaign |
| `/api/referral/admin/campaigns/:id/links` | GET/POST | Campaign links |
| `/api/referral/admin/links/:id` | GET/PUT/DELETE | Manage link |
| `/api/referral/admin/analytics/overview` | GET | Referral overview |
| `/api/referral/admin/registrations` | GET | Registrations |

---

## Permissions

| Permission | Description |
|------------|-------------|
| `admin:users:manage` | Manage users |
| `admin:system:configure` | Configure system |
| `admin:permissions:manage` | Manage permissions |
| `admin:roles:manage` | Manage roles |
| `admin:field_prompts:manage` | Manage AI prompts |
| `feature:llm:edit` | Edit LLM models |
| `feature:rag:edit` | Edit RAG collections |

---

## See Also

- [Permission System](permission-system.md) – Detailed permissions documentation
- [Chatbot Wizard](chatbot-wizard.md) – Create chatbots
- [Authentik Setup](authentik-setup.md) – Auth configuration
