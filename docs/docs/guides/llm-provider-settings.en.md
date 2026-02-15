# LLM Provider (Settings)

**Version:** 1.0 | **Date:** February 2026

Under **Settings → LLM-Provider**, all users can add their own LLM API keys, test connections, and share providers with other users or roles. Configured providers are then available system-wide in the model selection (`LlmModelSelect`).

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Settings → LLM Provider                                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  My Providers                                    [+ Add]       │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │  🤖 OpenAI             GPT-5, GPT-5-mini   ✓  ⋮ (Menu)       │   │
│  │  🧠 Anthropic          api.anthropic.com    ✓  ⋮ (Menu)       │   │
│  │  ⚡ LiteLLM            litellm.example.com  ✓  ⋮ (Menu)       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Shared With Me                                                 │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │  🖥 Ollama  (from admin)      llama3, mistral                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

The page is divided into two sections:

- **My Providers** — Self-created providers with API key, test, and sharing features
- **Shared With Me** — Providers shared by other users (read-only)

---

## Quick Start

!!! tip "5 Steps to Your First Provider"
    1. Open **Settings** (gear icon in the top bar)
    2. Select the **LLM-Provider** tab
    3. Click **+ Add**
    4. Choose a provider type, enter your API key, select models
    5. Click **Create** → done! The provider appears in the model selection.

---

## Provider Types

| Type | Description | API Key | Base URL | Notes |
|------|------------|---------|----------|-------|
| **OpenAI** | GPT-5, GPT-4.1, o3/o4 | Yes | Optional | Model selection via dropdown |
| **Anthropic** | Claude models | Yes | Optional | — |
| **Google Gemini** | Gemini Pro, Ultra | Yes | No | — |
| **Azure OpenAI** | Azure-hosted OpenAI | Yes | Yes | Deployment name required |
| **Ollama** | Local installation | No | Yes | Default: `http://localhost:11434` |
| **LiteLLM** | Multi-provider proxy | Yes | Yes | — |
| **Custom** | OpenAI-compatible endpoint | Yes | Yes | For any OpenAI-compatible API |

!!! info "Which Type to Choose?"
    - **Own OpenAI account** → Type `OpenAI`
    - **Own Anthropic account** → Type `Anthropic`
    - **Local model (Ollama, vLLM)** → Type `Ollama` or `Custom`
    - **University/company proxy** → Type `LiteLLM` or `Custom`

---

## Adding a Provider

Click **+ Add** to open the dialog:

```
┌─────────────────────────────────────────────────────┐
│  Add Provider                                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Type:       [OpenAI              ▾]                │
│                                                     │
│  API Key:    [sk-...                  👁]           │
│                                                     │
│  Models:     [GPT-5] [GPT-5 Mini] [GPT-4.1]  ×    │
│              Select models that should be            │
│              available                               │
│                                                     │
│  ☐ Set as default                                   │
│                                                     │
│                          [Cancel]  [Create]         │
└─────────────────────────────────────────────────────┘
```

### Field Details

| Field | Description |
|-------|------------|
| **Type** | Provider kind (OpenAI, Anthropic, etc.) — cannot be changed after creation |
| **Name** | Display name (auto-set for OpenAI) |
| **API Key** | The provider's API key — stored encrypted on the server |
| **Models** | OpenAI only: dropdown with available models (multi-select) |
| **Base URL** | Only for providers with custom URLs (Ollama, LiteLLM, Custom, etc.) |
| **Set as default** | This provider is used preferentially |

!!! warning "API Key Security"
    The API key is encrypted server-side. It cannot be retrieved in plain text after saving. When editing, leave it empty to keep the existing key.

### OpenAI: Model Selection

For OpenAI, you can select exactly which models should be available:

| Model | Context | Output | Vision | Reasoning |
|-------|---------|--------|--------|-----------|
| GPT-5.2 | 400K | 128K | Yes | Yes |
| GPT-5.1 | 400K | 128K | Yes | Yes |
| GPT-5 | 400K | 128K | Yes | Yes |
| GPT-5 Mini | 400K | 128K | Yes | No |
| GPT-5 Nano | 400K | 128K | No | No |
| GPT-4.1 | 1M | 32K | Yes | No |
| GPT-4.1 Mini | 1M | 32K | Yes | No |
| GPT-4.1 Nano | 1M | 32K | Yes | No |
| GPT-4o | 128K | 16K | Yes | No |
| o3 | 200K | 100K | Yes | Yes |
| o4 Mini | 200K | 100K | Yes | Yes |

---

## Testing the Connection

To verify that your API key is valid:

1. Click the **⋮ menu** on the provider
2. Select **Test Connection**
3. LLARS sends a test request to the provider
4. Result: success message or error description

!!! tip "Test Fails?"
    - **401/403** → API key invalid or expired
    - **Timeout** → Base URL not reachable (firewall, VPN?)
    - **Model not found** → Check the selected models

---

## Sharing a Provider

You can share your providers with individual users, entire roles, or all users.

### Opening the Share Dialog

1. Click **⋮ menu** → **Share**
2. The share dialog opens:

```
┌─────────────────────────────────────────────────────┐
│  Share "OpenAI"                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Current shares:                                    │
│  [👤 evaluator ×] [👥 researcher ×]                │
│                                                     │
│  ☐ Share with all users                             │
│  ─────────────────────────────────                  │
│  Add share:                                         │
│  [User | Role]                                      │
│                                                     │
│  [Search user...                   ] [Share]        │
│                                                     │
│                                          [Close]    │
└─────────────────────────────────────────────────────┘
```

### Sharing Options

| Option | Description |
|--------|------------|
| **Share with user** | Autocomplete user search → individual share |
| **Share with role** | Enter role name (e.g. `researcher`) → all users with that role |
| **Share with all** | Toggle switch → provider is visible to everyone |

### Removing a Share

Click the **×** on a share chip to revoke the share.

!!! info "What Can Recipients Do?"
    Recipients can only **use** the shared provider (select models), but **cannot** edit, delete, or re-share it. The API key remains invisible.

---

## Using Shared Providers

Providers shared with you appear in the **Shared With Me** section:

- Displayed: provider name, type, available models, and **who** shared it
- The models automatically appear in the **model selection** (`LlmModelSelect`) across all areas (generation, prompt engineering, chatbot, etc.)
- Model ID format for shared providers: `user-provider:{id}:{username}:{model}`

---

## Managing Providers

The **⋮ menu** on each provider offers the following actions:

| Action | Description |
|--------|------------|
| **Test Connection** | Send a test request to the provider |
| **Edit** | Change name, API key, base URL, or models |
| **Share** | Open the share dialog |
| **Set as Default** | Set this provider as the preferred default |
| **Delete** | Permanently remove the provider (including all shares) |

### Usage Statistics

The following information is displayed for each provider:

- **Requests** — Total number of API calls
- **Last used** — Date of last usage
- **API Key Status** — Green checkmark (set) or warning (missing)

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|------------|
| GET | `/api/user/providers` | List own providers |
| GET | `/api/user/providers/available` | Own + shared providers |
| GET | `/api/user/providers/types` | Available provider types |
| POST | `/api/user/providers` | Create a provider |
| GET | `/api/user/providers/<id>` | Provider details |
| PUT | `/api/user/providers/<id>` | Update a provider |
| DELETE | `/api/user/providers/<id>` | Delete a provider |
| POST | `/api/user/providers/<id>/test` | Test connection |
| POST | `/api/user/providers/models` | Fetch models for a provider |
| GET | `/api/user/providers/<id>/shares` | List shares |
| POST | `/api/user/providers/<id>/shares` | Create a share |
| DELETE | `/api/user/providers/<id>/shares/<share_id>` | Remove a share |
| POST | `/api/user/providers/<id>/share-all` | Toggle share with all |

---

## Permissions

Any authenticated user can create their own providers — no special permission is required.

| Action | Requirement |
|--------|------------|
| Create/edit/delete providers | Logged in (any role) |
| Test providers | Logged in (any role) |
| Share providers | Logged in (own provider) |
| View all providers (admin) | `admin:system:configure` |

---

## See Also

- [Admin Dashboard](admin-dashboard.md) — Manage LLM providers and models centrally (admin)
- [Batch Generation](batch-generation.md) — Select models for batch processing
- [Prompt Engineering](prompt-engineering.md) — Test prompts with different models
- [Permission System](permission-system.md) — Roles and permissions
