# Nightly Test Activities

This page describes the concrete activities that are checked automatically in the nightly run.

## Goal

Before each productive switch of the blue-green deployment color, it is verified that central user interactions as well as cross-role handoffs still work.

---

## Tile Activities (Tile-by-Tile)

### Prompt Engineering

| Activity-ID | Description | Expected Result |
|---|---|---|
| PE-CREATE-001 | Create a new prompt | Prompt card appears in the list |
| PE-BLOCK-001 | Create a block and edit text | Block with content visible |
| PE-TEST-001 | Start the test dialog | LLM response is displayed |
| PE-EXPORT-001 | Export prompt as JSON | File download starts |
| PE-IMPORT-001 | Import prompt blocks from JSON | Imported block in the list |
| PE-SHARE-001 | Share prompt with an evaluator | Evaluator visible in the shared list |
| PE-SHARED-VISIBLE-001 | Open the shared prompt as an evaluator | Prompt opens in the detail view |
| PE-UNSHARE-001 | Remove the share again | Evaluator disappears from the shared list |
| PE-CLEANUP-001 | Delete the test prompt | No test artifact remains |

### Batch Generation

| Activity-ID | Description | Expected Result |
|---|---|---|
| BG-WIZ-ENTRY-001 | Open the Generation Hub, check wizard entry | New-job button and wizard visible |
| BG-WIZ-HANDOFF-001 | Check the transition to the Scenario Wizard | Wizard/scenario handoff reachable |

### Scenario Manager

| Activity-ID | Description | Expected Result |
|---|---|---|
| SCN-ASSIGN-SETUP-001 | Create a nightly test scenario via API | Scenario ID returned |
| SCN-ASSIGN-INVITE-001 | Invite an evaluator via the UI | Evaluator visible in the member card |
| SCN-ASSIGN-ROLE-001 | Change role in the team tab | Role label updates |
| SCN-ASSIGN-VISIBLE-001 | See and accept the invitation as an evaluator | Invitation card with accept button |
| SCN-ASSIGN-EVAL-001 | Evaluator jumps into the evaluation | Evaluation route is reached |
| SCN-ASSIGN-CLEANUP-001 | Delete the nightly scenario | No test artifact remains |

### Conference Manager

| Activity-ID | Description | Expected Result |
|---|---|---|
| CONF-REQ-SETUP-001 | Create a nightly research group | Group ID returned |
| CONF-REQ-SUBMIT-001 | Send an access request as a researcher | Success message displayed |
| CONF-REQ-VISIBLE-001 | Request visible in the members area | Row with researcher username |
| CONF-REQ-APPROVE-001 | Approve the access request | Request disappears, member appears |
| CONF-REQ-MEMBER-001 | Researcher is a member | Member entry visible |
| CONF-REQ-CLEANUP-001 | Delete the nightly research group | No test artifact remains |
| CONF-TABS-001 | Click through all 5 tabs (Conferences, Papers, Calendar, Timeline, Kanban) | Each tab shows its own content |

### User Settings

| Activity-ID | Description | Expected Result |
|---|---|---|
| SETTINGS-NAV-001 | Open the settings page | Sidebar with tabs visible |
| SETTINGS-TABS-001 | Click through all sidebar tabs | Each tab shows matching content |
| SETTINGS-THEME-001 | Check the theme toggle | Toggle button present and clickable |

### Anonymization Pipeline

| Activity-ID | Description | Expected Result |
|---|---|---|
| ANON-VIEW-001 | Open the pipeline manager | Page loads without errors |
| ANON-TOGGLE-001 | Switch the view toggle (Cards/List) | Display changes |

### Chatbot Manager

| Activity-ID | Description | Expected Result |
|---|---|---|
| CBM-ACCESS-001 | chatbot_manager opens /chatbot-manager | Chatbot Manager page visible |
| CBM-TABS-001 | Click through tabs (Chatbots, RAG, Crawler) | Tab contents visible |

### Markdown Collab

| Activity-ID | Description | Expected Result |
|---|---|---|
| MD-NAV-001 | Open Markdown Collab home | Workspace list or empty state |
| MD-WORKSPACE-001 | Open a workspace (if present) | Editor area visible |

### Infrastructure (MkDocs + Matomo)

| Activity-ID | Description | Expected Result |
|---|---|---|
| INFRA-MKDOCS-001 | Open MkDocs documentation at /mkdocs/en/ | HTTP 200, navigation/content visible |
| INFRA-MATOMO-001 | Open Matomo Analytics at /analytics/ | HTTP < 500, login form or dashboard visible |
| INFRA-MKDOCS-SEARCH-001 | Test the MkDocs search function | Search results appear on input |

---

## Cross-Feature Interactions

### Share a prompt and view it as another user

**Flow:** Researcher creates a prompt -> shares it with an evaluator -> evaluator opens the shared prompt -> researcher removes the share

Tested in: `Prompt Engineering Collaboration`

### Scenario invitation and role change

**Flow:** Admin creates a scenario -> invites an evaluator -> evaluator sees the invitation -> accepts -> jumps into the evaluation

Tested in: `Scenario Manager Role Assignment`

### Batch Generation -> Scenario Wizard

**Flow:** Researcher opens Batch Generation -> starts the wizard -> transition to the Scenario Wizard

Tested in: `Szenario Wizard`

### Conference Manager access request

**Flow:** Admin creates a research group -> researcher submits an access request -> admin sees the request -> approves -> researcher is a member

Tested in: `Conference Manager Access Request`

### Conference Manager tab navigation

**Flow:** Researcher opens the Conference Manager -> navigates all 5 tabs (Conferences, Papers, Calendar, Timeline, Kanban)

Tested in: `Conference Manager Tab Navigation`

### User Settings navigation

**Flow:** User opens Settings -> navigates all sidebar tabs -> theme toggle checked

Tested in: `User Settings Navigation`

---

## Tile Regression (Automatic)

Each tile is checked per role:

| Check | Description |
|---|---|
| Visibility | Tile is visible for allowed roles, hidden for others |
| Navigation | Clicking the tile leads to the correct route |
| No login redirect | An authenticated user is not redirected to /login |
| No 404 | The target page does not show a NotFound |
| No 5xx | No backend API errors during navigation |
| Safe Button Sweep | Non-destructive buttons on the target page are clicked |

**Covered tiles:** Prompt Engineering, Batch Generation, Evaluation, Scenario Manager, Chatbot, Video, Markdown Collab, Chatbot Arena, Anonymization, Anonymization Pipeline, KAIMO, OnCoCo, Admin Dashboard, Chatbot Admin, RAG Admin, Conference Manager, Pipeline, User Settings

**Roles:** evaluator, researcher, chatbot_manager, admin

---

## Role Coverage

Order in the nightly run:

1. `test_evaluator`
2. `test_researcher`
3. `test_chatbot_manager`
4. `test_admin`

`ijcai_reviewer` is explicitly excluded from this nightly run.

---

## Source of Truth

1. `llars-frontend/src/config/home_tiles.contract.json`
2. `llars-frontend/e2e/nightly/nightly_workflows.contract.json`
3. `llars-frontend/e2e/nightly/nightly_activities.contract.json`
4. `docs/testing/nightly/NIGHTLY_TILE_MATRIX.md`

## CI Gate

`python3 scripts/testing/validate_nightly_coverage.py`

The check fails if:

1. Home routes and the tile contract do not match.
2. A tile name has no test title of the same name.
3. A workflow name has no test title of the same name.
4. A mandatory activity ID (`[ACT:<ID>]`) is missing from the nightly specs.
5. `Home.vue` or the tile contract was changed but tests/docs were not updated along with it.

## Nightly VM Housekeeping

After a successful production smoke, `maintenance:docker-cleanup` runs:

1. `docker image prune -af --filter "until=168h"`
2. `docker builder prune -af --filter "until=168h"`

This removes only unused artifacts older than 7 days, and the VM does not run into storage shortages.

## Change Procedure

When a tile or user interaction is changed:

1. Update the contract.
2. Align the E2E test title unchanged with the tile name.
3. Add an activity entry to the matrix.
4. Run the CI check locally.
