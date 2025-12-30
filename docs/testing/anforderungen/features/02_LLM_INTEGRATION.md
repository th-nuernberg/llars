# Feature Testanforderungen: LLM Integration

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Übersicht

Dieses Dokument beschreibt alle Tests für die LLM-Integration in LLARS.

**Komponenten:** LiteLLM Proxy | Model Management | Streaming | Agent Modes

---

## 1. LLM Model Management

**API:** `/api/llm/models`
**Tabelle:** `llm_models`

### Model Types

| Type | Beschreibung | Beispiele |
|------|--------------|-----------|
| `llm` | Chat/Completion Models | GPT-4o, Claude-3, Mistral |
| `embedding` | Embedding Models | VDR-2B, MiniLM |
| `reranker` | Reranking Models | Cross-Encoder |

### Model Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LLM-M01 | GET /api/llm/models | Liste aller Models | Integration |
| LLM-M02 | Filter by type | Nur type=llm | Integration |
| LLM-M03 | Default Model markiert | is_default=true | Integration |
| LLM-M04 | Vision Support Flag | supports_vision korrekt | Integration |
| LLM-M05 | Streaming Support | supports_streaming korrekt | Integration |
| LLM-M06 | Function Calling | supports_function_calling | Integration |
| LLM-M07 | Sync Models | LiteLLM Sync | Integration |

---

## 2. Chat Completion

**API:** `/api/chatbots/:id/chat`, Socket.IO `chatbot:stream`

### Basic Chat

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LLM-C01 | Simple Message | Response erhalten | Integration |
| LLM-C02 | Streaming Response | Token-by-Token | Integration |
| LLM-C03 | System Prompt | Befolgt System Prompt | Integration |
| LLM-C04 | Temperature 0 | Deterministische Antwort | Integration |
| LLM-C05 | Temperature 2 | Kreative Antwort | Integration |
| LLM-C06 | Max Tokens Limit | Antwort begrenzt | Integration |

### Conversation History

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LLM-H01 | Context Preserved | Referenz auf vorherige Msgs | Integration |
| LLM-H02 | Long Context | >10 Messages | Integration |
| LLM-H03 | Context Window | Truncation bei Limit | Integration |

### Error Handling

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LLM-E01 | Model nicht verfügbar | Fallback oder Error | Integration |
| LLM-E02 | Rate Limit | Retry mit Backoff | Integration |
| LLM-E03 | Timeout | Timeout-Error | Integration |
| LLM-E04 | Invalid Model ID | 404 Error | Integration |

---

## 3. Vision Models

**Capability:** `supports_vision=true`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LLM-V01 | Image Upload | Bild wird analysiert | Integration |
| LLM-V02 | Multiple Images | Alle verarbeitet | Integration |
| LLM-V03 | Image + Text | Kombinierte Query | Integration |
| LLM-V04 | Große Bilder | Resize/Compression | Integration |
| LLM-V05 | Non-Vision Model + Image | Error oder Ignoriert | Integration |

---

## 4. Agent Modes

**Modes:** Basic, ACT, ReAct, ReflAct

### Basic Mode

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LLM-AB01 | Direct Response | Keine Reasoning Steps | Integration |
| LLM-AB02 | Simple Query | Schnelle Antwort | Integration |

### ACT Mode

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LLM-AA01 | Action Selection | Action Events | Integration |
| LLM-AA02 | Tool Use | Tools korrekt aufgerufen | Integration |

### ReAct Mode

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LLM-AR01 | Thought Events | Reasoning sichtbar | Integration |
| LLM-AR02 | Action Events | Actions nach Thoughts | Integration |
| LLM-AR03 | Observation Events | Ergebnisse verarbeitet | Integration |
| LLM-AR04 | Loop Detection | Max Iterations | Integration |

### ReflAct Mode

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LLM-AF01 | Reflection Events | Selbst-Reflexion | Integration |
| LLM-AF02 | Quality Check | Antwort-Verbesserung | Integration |
| LLM-AF03 | Iteration Count | Max Reflections | Integration |

---

## 5. Prompt Engineering

**API:** `/api/prompts`

### Prompt Management

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| PRMT-01 | Create Prompt | Prompt erstellt | Integration |
| PRMT-02 | Update Prompt | Prompt aktualisiert | Integration |
| PRMT-03 | Delete Prompt | Prompt gelöscht | Integration |
| PRMT-04 | Share Prompt | Mit User geteilt | Integration |
| PRMT-05 | Revoke Share | Zugriff entfernt | Integration |

### Prompt Testing

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| PRMT-T01 | Test Prompt | Response erhalten | Integration |
| PRMT-T02 | Test mit Model | Spezifisches Model | Integration |
| PRMT-T03 | Test mit Params | Temperature etc. | Integration |
| PRMT-T04 | JSON Mode | JSON Response | Integration |
| PRMT-T05 | Schema Validation | Valides Schema | Integration |

### Prompt History

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| PRMT-H01 | Version erstellt | Bei Edit | Integration |
| PRMT-H02 | Version abrufen | History laden | Integration |
| PRMT-H03 | Version restore | Alte Version | Integration |

---

## 6. LLM-as-Judge

**API:** `/api/judge/sessions`

### Session Management

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| JUDGE-S01 | Create Session | Session erstellt | Integration |
| JUDGE-S02 | Start Session | Status: running | Integration |
| JUDGE-S03 | Pause Session | Status: paused | Integration |
| JUDGE-S04 | Resume Session | Fortgesetzt | Integration |
| JUDGE-S05 | Complete Session | Status: completed | Integration |

### Comparison Execution

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| JUDGE-C01 | Pairwise Compare | A vs B Bewertung | Integration |
| JUDGE-C02 | Pillar Evaluation | Pro Pillar | Integration |
| JUDGE-C03 | Winner Selection | winner: A/B/tie | Integration |
| JUDGE-C04 | Reasoning | Begründung vorhanden | Integration |
| JUDGE-C05 | Progress Update | Via WebSocket | Integration |

### Results

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| JUDGE-R01 | Get Results | Evaluations zurück | Integration |
| JUDGE-R02 | Export Results | CSV/JSON Export | Integration |
| JUDGE-R03 | Statistics | Aggregierte Stats | Integration |

---

## 7. Test-Code

```python
# tests/integration/llm/test_chat.py
import pytest


class TestLLMChat:
    """LLM Chat Tests"""

    def test_LLM_C01_simple_message(self, authenticated_client, test_chatbot):
        """Simple Message bekommt Response"""
        response = authenticated_client.post(
            f'/api/chatbots/{test_chatbot.id}/chat/test',
            json={'message': 'Say hello'}
        )
        assert response.status_code == 200
        assert 'response' in response.json
        assert len(response.json['response']) > 0

    def test_LLM_C02_streaming(self, socket_client, test_chatbot, auth_token):
        """Streaming Response funktioniert"""
        socket_client.emit('chatbot:join', {'session_id': 'test'})
        socket_client.emit('chatbot:stream', {
            'chatbot_id': test_chatbot.id,
            'message': 'Count to 5',
            'session_id': 'test',
            'token': auth_token
        })

        received = socket_client.get_received(timeout=30)
        response_events = [r for r in received if r['name'] == 'chatbot:response']
        complete_events = [r for r in received if r['name'] == 'chatbot:complete']

        assert len(response_events) > 1  # Multiple chunks
        assert len(complete_events) == 1

    def test_LLM_C04_temperature_0(self, authenticated_client, test_chatbot):
        """Temperature 0 gibt deterministische Antworten"""
        responses = []
        for _ in range(3):
            response = authenticated_client.post(
                f'/api/chatbots/{test_chatbot.id}/chat/test',
                json={'message': 'What is 2+2?', 'temperature': 0}
            )
            responses.append(response.json['response'])

        # Bei Temperature 0 sollten Antworten ähnlich sein
        assert responses[0] == responses[1] == responses[2]


class TestVisionModels:
    """Vision Model Tests"""

    def test_LLM_V01_image_analysis(self, authenticated_client, vision_chatbot, test_image):
        """Vision Model analysiert Bild"""
        with open(test_image, 'rb') as f:
            response = authenticated_client.post(
                f'/api/chatbots/{vision_chatbot.id}/chat/test',
                data={
                    'message': 'What is in this image?',
                    'image': (f, 'test.png')
                },
                content_type='multipart/form-data'
            )
        assert response.status_code == 200
        assert 'response' in response.json


class TestAgentModes:
    """Agent Mode Tests"""

    def test_LLM_AR01_react_thoughts(self, socket_client, react_chatbot, auth_token):
        """ReAct Mode sendet Thought Events"""
        socket_client.emit('chatbot:join', {'session_id': 'test'})
        socket_client.emit('chatbot:stream', {
            'chatbot_id': react_chatbot.id,
            'message': 'Search for information about Python',
            'session_id': 'test',
            'token': auth_token
        })

        received = socket_client.get_received(timeout=60)
        agent_events = [r for r in received if r['name'] == 'chatbot:agent_status']

        # ReAct sollte Thought-Events senden
        thought_events = [e for e in agent_events if 'thought' in str(e)]
        assert len(thought_events) > 0


class TestPromptEngineering:
    """Prompt Engineering Tests"""

    def test_PRMT_01_create_prompt(self, authenticated_client):
        """Prompt erstellen"""
        response = authenticated_client.post('/api/prompts', json={
            'name': 'Test Prompt',
            'content': 'You are a helpful assistant'
        })
        assert response.status_code == 201
        assert 'id' in response.json

    def test_PRMT_T04_json_mode(self, authenticated_client):
        """JSON Mode gibt valides JSON"""
        response = authenticated_client.post('/api/prompts/test', json={
            'prompt': 'Return a JSON with name and age',
            'model': 'gpt-4o-mini',
            'json_mode': True
        })
        assert response.status_code == 200
        # Response sollte JSON sein
        import json
        parsed = json.loads(response.json['response'])
        assert isinstance(parsed, dict)


class TestJudge:
    """LLM-as-Judge Tests"""

    def test_JUDGE_S01_create_session(self, authenticated_admin_client):
        """Judge Session erstellen"""
        response = authenticated_admin_client.post('/api/judge/sessions', json={
            'name': 'Test Session',
            'pillars': [1, 2, 3]
        })
        assert response.status_code == 201
        assert 'session_id' in response.json

    def test_JUDGE_C01_pairwise_compare(self, socket_client, judge_session):
        """Pairwise Comparison läuft"""
        socket_client.emit('judge:join_session', {'session_id': judge_session.id})
        socket_client.emit('judge:get_status', {'session_id': judge_session.id})

        received = socket_client.get_received(timeout=5)
        status_events = [r for r in received if r['name'] == 'judge:status']

        assert len(status_events) > 0
```

---

## 8. E2E Test-Code

```typescript
// e2e/llm/llm-integration.spec.ts
import { test, expect } from '../fixtures/auth'

test.describe('LLM Integration', () => {
  test('chat streaming works', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/chat')
    await authenticatedPage.click('.chatbot-item >> nth=0')

    await authenticatedPage.fill('.message-input', 'Say hello in one word')
    await authenticatedPage.click('button:has-text("Senden")')

    // Streaming indicator should appear
    await expect(authenticatedPage.locator('.streaming-indicator')).toBeVisible({
      timeout: 5000
    })

    // Response should appear
    await expect(authenticatedPage.locator('.message.bot')).toBeVisible({
      timeout: 30000
    })
  })

  test('prompt testing works', async ({ adminPage }) => {
    await adminPage.goto('/admin?tab=prompts')
    await adminPage.click('button:has-text("Test")')

    await adminPage.fill('.prompt-input', 'Say hi')
    await adminPage.click('button:has-text("Testen")')

    await expect(adminPage.locator('.test-response')).toBeVisible({
      timeout: 30000
    })
  })
})
```

---

## 9. Checkliste für manuelle Tests

### Chat
- [ ] Chatbot antwortet auf Nachrichten
- [ ] Streaming funktioniert flüssig
- [ ] Verschiedene Models funktionieren
- [ ] Conversation History bleibt erhalten
- [ ] Error Handling bei Timeout

### Vision
- [ ] Bild-Upload funktioniert
- [ ] Vision Model analysiert Bilder
- [ ] Nicht-Vision Model lehnt Bilder ab

### Agent Modes
- [ ] Basic Mode: Direkte Antworten
- [ ] ReAct Mode: Thought/Action/Observation
- [ ] ReflAct Mode: Selbst-Reflexion sichtbar

### Prompt Engineering
- [ ] Prompts erstellen/bearbeiten/löschen
- [ ] Prompts testen mit verschiedenen Models
- [ ] JSON Mode funktioniert
- [ ] Prompts teilen funktioniert

### LLM-as-Judge
- [ ] Sessions erstellen
- [ ] Comparisons laufen durch
- [ ] Progress wird angezeigt
- [ ] Ergebnisse exportierbar

---

## 10. Model-Verfügbarkeit

| Model | Type | Priorität | Fallback |
|-------|------|-----------|----------|
| GPT-4o | llm | 1 | GPT-4o-mini |
| GPT-4o-mini | llm | 2 | - |
| Claude-3.5-Sonnet | llm | 1 | Claude-3-Haiku |
| VDR-2B (LiteLLM) | embedding | 1 | VDR-2B (Local) |
| VDR-2B (Local) | embedding | 2 | MiniLM |
| MiniLM | embedding | 3 | - |

---

**Letzte Aktualisierung:** 30. Dezember 2025
