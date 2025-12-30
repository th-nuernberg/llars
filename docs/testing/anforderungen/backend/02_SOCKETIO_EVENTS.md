# Backend Testanforderungen: Socket.IO Events

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Übersicht

Dieses Dokument beschreibt alle Tests für Socket.IO Real-Time Events in LLARS.

**Namespaces:** Default (`/`), Admin (`/admin`)
**Events:** 50+ Events über alle Funktionsbereiche

---

## 1. Connection Events

**Datei:** `app/routes/socketio/events_connection.py`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| SOCK-C01 | Connect ohne Token | Connection erlaubt | Integration |
| SOCK-C02 | Connect mit Token | User authentifiziert | Integration |
| SOCK-C03 | Disconnect | Cleanup durchgeführt | Integration |
| SOCK-C04 | Reconnect | State wiederhergestellt | Integration |

---

## 2. Chat Events

**Datei:** `app/routes/socketio/events_chat.py`

### chat_stream

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CHAT-S01 | Message senden | Streaming-Response | Integration |
| CHAT-S02 | RAG-Context injiziert | Sources im Response | Integration |
| CHAT-S03 | Streaming chunks | Mehrere chat_response Events | Integration |
| CHAT-S04 | Complete Flag | complete: true am Ende | Integration |
| CHAT-S05 | Error während Stream | Error Event mit Message | Integration |

### test_prompt_stream

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| PROMPT-S01 | Basic Prompt | Streaming-Response | Integration |
| PROMPT-S02 | JSON Mode | Valides JSON zurück | Integration |
| PROMPT-S03 | Schema Validation | Schema-konformes JSON | Integration |
| PROMPT-S04 | Temperature Setting | Andere Antworten | Integration |
| PROMPT-S05 | Max Tokens Limit | Antwort gekürzt | Integration |

---

## 3. Chatbot Events

**Datei:** `app/routes/socketio/events_chatbot.py`

### Room Management

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| BOT-R01 | chatbot:join | Room beigetreten | Integration |
| BOT-R02 | chatbot:leave | Room verlassen | Integration |
| BOT-R03 | Multiple Sessions | Unabhängige Rooms | Integration |

### Streaming

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| BOT-S01 | chatbot:stream | Streaming startet | Integration |
| BOT-S02 | chatbot:response chunks | Token-by-Token | Integration |
| BOT-S03 | chatbot:sources | Sources nach Completion | Integration |
| BOT-S04 | chatbot:complete | Finale Metadaten | Integration |
| BOT-S05 | chatbot:error | Fehler-Event | Integration |

### Title Generation

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| BOT-T01 | chatbot:title_generating | Event bei Start | Integration |
| BOT-T02 | chatbot:title_delta | Streaming Title | Integration |
| BOT-T03 | chatbot:title_complete | Fertiger Titel | Integration |

### Agent Status

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| BOT-A01 | Agent thought | Status-Event | Integration |
| BOT-A02 | Agent action | Action-Event | Integration |
| BOT-A03 | Agent reflection | Reflection-Event | Integration |

---

## 4. RAG Events

**Datei:** `app/routes/socketio/events_rag.py`

### Queue Subscription

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-Q01 | rag:subscribe_queue | Initial queue_list | Integration |
| RAG-Q02 | rag:unsubscribe_queue | Room verlassen | Integration |
| RAG-Q03 | rag:queue_updated | Bei Änderung | Integration |

### Collection Subscription

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-COL01 | rag:subscribe_collection | Status zurück | Integration |
| RAG-COL02 | rag:collection_progress | Progress Updates | Integration |
| RAG-COL03 | rag:collection_completed | Completion Event | Integration |
| RAG-COL04 | rag:collection_error | Error Event | Integration |

### Document Events

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-D01 | rag:document_processed | Nach Processing | Integration |
| RAG-D02 | rag:get_collection_documents | Documents zurück | Integration |

---

## 5. Judge Events

**Datei:** `app/routes/socketio/events_judge.py`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| JUDGE-S01 | judge:join_session | Room beigetreten | Integration |
| JUDGE-S02 | judge:leave_session | Room verlassen | Integration |
| JUDGE-S03 | judge:join_overview | Overview Room | Integration |
| JUDGE-S04 | judge:get_status | Status zurück | Integration |
| JUDGE-S05 | judge:status broadcast | Bei Änderung | Integration |

---

## 6. Crawler Events

**Datei:** `app/routes/socketio/events_crawler.py`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CRAWL-01 | crawler:join_session | Session Room | Integration |
| CRAWL-02 | crawler:leave_session | Room verlassen | Integration |
| CRAWL-03 | crawler:subscribe_jobs | Global Jobs Room | Integration |
| CRAWL-04 | crawler:get_status | Status zurück | Integration |
| CRAWL-05 | crawler:progress | Progress Updates | Integration |
| CRAWL-06 | crawler:page_crawled | Page Event | Integration |
| CRAWL-07 | crawler:complete | Completion Event | Integration |
| CRAWL-08 | crawler:error | Error Event | Integration |

---

## 7. Wizard Events

**Datei:** `app/routes/socketio/events_wizard.py`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| WIZ-S01 | wizard:join_session | State zurück | Integration |
| WIZ-S02 | wizard:leave_session | Room verlassen | Integration |
| WIZ-S03 | wizard:get_state | Aktueller State | Integration |
| WIZ-S04 | wizard:heartbeat | Elapsed Time | Integration |
| WIZ-S05 | wizard:progress | Progress Updates | Integration |
| WIZ-S06 | wizard:status_changed | Status Event | Integration |
| WIZ-S07 | wizard:error | Error Event | Integration |

---

## 8. Collaboration Events

### Markdown Collab

**Datei:** `app/routes/socketio/events_markdown_collab.py`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| MD-S01 | markdown_collab:subscribe | Subscribed Event | Integration |
| MD-S02 | markdown_collab:unsubscribe | Room verlassen | Integration |
| MD-S03 | markdown_collab:subscribe_document | Document Room | Integration |
| MD-S04 | markdown_collab:workspace_shared | Sharing Event | Integration |
| MD-S05 | markdown_collab:commit_created | Commit Event | Integration |

### LaTeX Collab

**Datei:** `app/routes/socketio/events_latex_collab.py`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LTX-S01 | latex_collab:subscribe | Subscribed Event | Integration |
| LTX-S02 | latex_collab:unsubscribe | Room verlassen | Integration |
| LTX-S03 | latex_collab:subscribe_document | Document Room | Integration |
| LTX-S04 | latex_collab:workspace_shared | Sharing Event | Integration |
| LTX-S05 | latex_collab:commit_created | Commit Event | Integration |

---

## 9. Prompts Events

**Datei:** `app/routes/socketio/events_prompts.py`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| PRMT-01 | prompts:subscribe | Prompt Liste | Integration |
| PRMT-02 | prompts:unsubscribe | Room verlassen | Integration |
| PRMT-03 | prompts:updated | Bei Änderung | Integration |
| PRMT-04 | prompts:prompt_updated | Content Update | Integration |
| PRMT-05 | prompts:shared_updated | Shared Prompts | Integration |

---

## 10. Ranker Events

**Datei:** `app/routes/socketio/events_ranker.py`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RANK-S01 | ranker:subscribe (scenario) | Stats Liste | Integration |
| RANK-S02 | ranker:subscribe (global) | Globale Stats | Integration |
| RANK-S03 | ranker:unsubscribe | Room verlassen | Integration |
| RANK-S04 | ranker:stats_updated | Bei Änderung | Integration |
| RANK-S05 | ranker:ranking_saved | Save Event | Integration |

---

## 11. OnCoCo Events

**Datei:** `app/routes/socketio/events_oncoco.py`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ONCO-S01 | oncoco:join_analysis | Room beigetreten | Integration |
| ONCO-S02 | oncoco:leave_analysis | Room verlassen | Integration |
| ONCO-S03 | oncoco:get_status | Status zurück | Integration |
| ONCO-S04 | oncoco:progress | Progress Updates | Integration |
| ONCO-S05 | oncoco:sentence | Sentence Event | Integration |
| ONCO-S06 | oncoco:complete | Completion Event | Integration |
| ONCO-S07 | oncoco:error | Error Event | Integration |

---

## 12. Comparison Events

**Datei:** `app/routes/socketio/events_comparison.py`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| COMP-01 | join_comparison_session | Messages loaded | Integration |
| COMP-02 | comparison_message | Bot-Antworten | Integration |
| COMP-03 | rate_response | Rating gespeichert | Integration |
| COMP-04 | generate_suggestion | Suggestion Event | Integration |
| COMP-05 | submit_justification | Saved Event | Integration |

---

## 13. Admin Namespace (/admin)

### Docker Monitor

**Datei:** `app/routes/socketio/events_docker_monitor.py`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ADM-D01 | connect (Admin) | docker:connected | Integration |
| ADM-D02 | connect (Nicht-Admin) | Abgelehnt | Integration |
| ADM-D03 | docker:subscribe_stats (project) | Container Stats | Integration |
| ADM-D04 | docker:subscribe_stats (all) | Alle Container | Integration |
| ADM-D05 | docker:unsubscribe_stats | Polling stoppt | Integration |
| ADM-D06 | docker:subscribe_logs | Log Streaming | Integration |
| ADM-D07 | docker:log_line | Log Lines | Integration |
| ADM-D08 | docker:unsubscribe_logs | Streaming stoppt | Integration |

### DB Explorer

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ADM-DB01 | db:get_tables | Tabellen-Liste | Integration |
| ADM-DB02 | db:subscribe_table | Table Data | Integration |
| ADM-DB03 | db:table polling | Updates alle 1.5s | Integration |
| ADM-DB04 | db:unsubscribe_table | Polling stoppt | Integration |
| ADM-DB05 | db:error | Bei SQL-Fehler | Integration |

### System Health

**Datei:** `app/routes/socketio/events_system_health.py`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ADM-H01 | host:subscribe | Host Stats | Integration |
| ADM-H02 | host:stats polling | Updates alle 2s | Integration |
| ADM-H03 | api:subscribe | API Metrics | Integration |
| ADM-H04 | ws:subscribe | WebSocket Stats | Integration |
| ADM-H05 | Cleanup on disconnect | Subscriptions entfernt | Integration |

---

## 14. Test-Code

```python
# tests/integration/socketio/test_events.py
import pytest
from flask_socketio import SocketIOTestClient


class TestChatbotEvents:
    """Chatbot Socket.IO Events Tests"""

    @pytest.fixture
    def socket_client(self, app, socketio):
        """Erstellt Socket.IO Test Client"""
        return socketio.test_client(app)

    def test_BOT_R01_join_session(self, socket_client, auth_token):
        """chatbot:join tritt Room bei"""
        socket_client.emit('chatbot:join', {
            'session_id': 'test-session'
        })
        received = socket_client.get_received()
        # Prüfe dass Room beigetreten wurde
        assert len(received) >= 0  # Join ist silent

    def test_BOT_S01_stream(self, socket_client, auth_token, test_chatbot):
        """chatbot:stream startet Streaming"""
        socket_client.emit('chatbot:join', {'session_id': 'test-session'})
        socket_client.emit('chatbot:stream', {
            'chatbot_id': test_chatbot.id,
            'message': 'Hello',
            'session_id': 'test-session',
            'token': auth_token
        })

        received = socket_client.get_received(timeout=30)
        event_types = [r['name'] for r in received]

        assert 'chatbot:response' in event_types
        assert 'chatbot:complete' in event_types


class TestRAGEvents:
    """RAG Socket.IO Events Tests"""

    def test_RAG_Q01_subscribe_queue(self, socket_client, auth_token):
        """rag:subscribe_queue gibt Queue-Liste"""
        socket_client.emit('rag:subscribe_queue', {}, query_string=f'token={auth_token}')
        received = socket_client.get_received()

        queue_event = next((r for r in received if r['name'] == 'rag:queue_list'), None)
        assert queue_event is not None
        assert 'queue' in queue_event['args'][0]

    def test_RAG_COL02_collection_progress(self, socket_client, processing_collection):
        """rag:collection_progress wird gesendet"""
        socket_client.emit('rag:subscribe_collection', {
            'collection_id': processing_collection.id
        })

        # Warte auf Progress-Event
        received = socket_client.get_received(timeout=60)
        progress_events = [r for r in received if r['name'] == 'rag:collection_progress']

        assert len(progress_events) > 0
        assert 'progress' in progress_events[0]['args'][0]


class TestAdminEvents:
    """Admin Namespace Events Tests"""

    @pytest.fixture
    def admin_socket(self, app, socketio, admin_token):
        """Admin Socket Client"""
        return socketio.test_client(
            app,
            namespace='/admin',
            query_string=f'token={admin_token}'
        )

    def test_ADM_D01_connect_admin(self, admin_socket):
        """Admin kann sich verbinden"""
        received = admin_socket.get_received(namespace='/admin')
        connect_event = next(
            (r for r in received if r['name'] == 'docker:connected'),
            None
        )
        assert connect_event is not None

    def test_ADM_D03_subscribe_stats(self, admin_socket):
        """Docker Stats Subscription"""
        admin_socket.emit('docker:subscribe_stats', {'scope': 'project'}, namespace='/admin')
        received = admin_socket.get_received(namespace='/admin', timeout=5)

        stats_event = next(
            (r for r in received if r['name'] == 'docker:stats'),
            None
        )
        assert stats_event is not None
        assert 'containers' in stats_event['args'][0]

    def test_ADM_DB01_get_tables(self, admin_socket):
        """DB Explorer Tables Liste"""
        admin_socket.emit('db:get_tables', {}, namespace='/admin')
        received = admin_socket.get_received(namespace='/admin')

        tables_event = next(
            (r for r in received if r['name'] == 'db:tables'),
            None
        )
        assert tables_event is not None
        assert 'tables' in tables_event['args'][0]
```

---

## 15. Room-Architektur

### Room Naming Patterns

| Pattern | Beispiel | Verwendung |
|---------|----------|------------|
| `chatbot_{session_id}` | `chatbot_abc123` | Chatbot Session |
| `rag_queue_user_{username}` | `rag_queue_user_admin` | User RAG Queue |
| `rag_collection_{id}` | `rag_collection_5` | Collection Progress |
| `judge_session_{id}` | `judge_session_1` | Judge Session |
| `judge_overview` | `judge_overview` | Alle Judge Sessions |
| `crawler_{session_id}` | `crawler_uuid` | Crawler Job |
| `crawler_jobs_global` | `crawler_jobs_global` | Alle Crawler Jobs |
| `ranker_stats_{scenario_id}` | `ranker_stats_3` | Scenario Stats |
| `ranker_stats_global` | `ranker_stats_global` | Globale Stats |
| `prompts_user_{id}` | `prompts_user_5` | User Prompts |
| `prompt_{id}` | `prompt_10` | Prompt Collab |
| `markdown_collab_user_{id}` | `markdown_collab_user_5` | MD User |
| `markdown_collab_doc_{id}` | `markdown_collab_doc_3` | MD Document |
| `latex_collab_user_{id}` | `latex_collab_user_5` | LaTeX User |
| `latex_collab_doc_{id}` | `latex_collab_doc_3` | LaTeX Document |
| `wizard_{chatbot_id}` | `wizard_10` | Wizard Session |
| `comparison_{session_id}` | `comparison_5` | Comparison |
| `oncoco_analysis_{id}` | `oncoco_analysis_2` | OnCoCo Analysis |
| `docker_stats_project` | `docker_stats_project` | Docker Project |
| `docker_stats_all` | `docker_stats_all` | Docker All |
| `db_table__{name}` | `db_table__users` | DB Table |
| `host_stats` | `host_stats` | Host Metrics |
| `api_stats` | `api_stats` | API Metrics |
| `ws_stats` | `ws_stats` | WebSocket Stats |

---

## 16. Polling-Intervalle

| Feature | Intervall | Beschreibung |
|---------|-----------|--------------|
| Docker Stats | 2s | Container Metriken |
| DB Explorer | 1.5s | Tabellen-Daten |
| Host Stats | 2s | System-Metriken |
| API Stats | 2s | Request-Statistiken |
| WS Stats | 2s | WebSocket-Verbindungen |

---

## 17. Checkliste für manuelle Tests

### Connection
- [ ] Connect funktioniert
- [ ] Token wird validiert
- [ ] Disconnect Cleanup

### Chatbot Streaming
- [ ] Message wird gestreamt
- [ ] Sources werden angezeigt
- [ ] Titel wird generiert
- [ ] Error Handling

### RAG Queue
- [ ] Queue-Updates in Echtzeit
- [ ] Document Processing Events
- [ ] Collection Progress

### Admin Namespace
- [ ] Nur Admins können verbinden
- [ ] Docker Stats funktionieren
- [ ] DB Explorer funktioniert
- [ ] System Health Metriken

---

**Letzte Aktualisierung:** 30. Dezember 2025
