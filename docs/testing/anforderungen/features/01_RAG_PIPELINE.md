# Feature Testanforderungen: RAG Pipeline

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Übersicht

Dieses Dokument beschreibt alle Tests für die LLARS RAG (Retrieval-Augmented Generation) Pipeline.

**Komponenten:** Upload → Chunking → Embedding → Storage → Retrieval → Reranking

---

## 1. Document Upload

**API:** `POST /api/rag/documents/upload`, `POST /api/rag/documents/upload-multiple`
**Service:** `DocumentService`

### Validierung

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-U01 | PDF Upload | Dokument erstellt | Integration |
| RAG-U02 | TXT Upload | Dokument erstellt | Integration |
| RAG-U03 | MD Upload | Dokument erstellt | Integration |
| RAG-U04 | DOCX Upload | Dokument erstellt | Integration |
| RAG-U05 | Unerlaubter Typ (.exe) | 400 Bad Request | Integration |
| RAG-U06 | Zu große Datei (>50MB) | 400 Bad Request | Integration |
| RAG-U07 | Duplicate Hash | 409 Conflict | Integration |
| RAG-U08 | Leere Datei | 400 Bad Request | Integration |

### Multi-Upload

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-MU01 | 5 Files gleichzeitig | Alle erstellt | Integration |
| RAG-MU02 | Mix valid/invalid | Valide erstellt, Fehler für Invalid | Integration |
| RAG-MU03 | 20 Files (Limit-Test) | Alle verarbeitet | Integration |

### Queue-Integration

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-Q01 | Nach Upload | RAGProcessingQueue Eintrag | Integration |
| RAG-Q02 | Priority | Default 5, konfigurierbar | Integration |
| RAG-Q03 | Status | queued nach Upload | Integration |

---

## 2. Chunking

**Service:** `LumberChunker`

### Text Splitting

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-CH01 | Standard Text | Chunks mit 1500 chars | Unit |
| RAG-CH02 | Overlap | 300 chars Überlappung | Unit |
| RAG-CH03 | Separator Priority | Markdown Headers zuerst | Unit |
| RAG-CH04 | Kurzer Text | Ein Chunk | Unit |
| RAG-CH05 | Sehr langer Text | Mehrere Chunks | Unit |

### PDF Processing

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-PDF01 | Multi-Page PDF | Chunks mit page_number | Integration |
| RAG-PDF02 | PDF mit Bildern | Bilder extrahiert | Integration |
| RAG-PDF03 | Scanned PDF | OCR-Text (wenn konfiguriert) | Integration |
| RAG-PDF04 | Korrupte PDF | Fehler abgefangen | Integration |

### Chunk Metadata

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-CM01 | start_char | Korrekte Position | Unit |
| RAG-CM02 | end_char | Korrekte Position | Unit |
| RAG-CM03 | chunk_index | Sequentiell | Unit |
| RAG-CM04 | page_number | Bei PDFs vorhanden | Unit |

---

## 3. Embedding

**Services:** `EmbeddingModelService`, `CollectionEmbeddingService`

### Model Selection

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-E01 | LiteLLM verfügbar | LiteLLM verwendet | Integration |
| RAG-E02 | LiteLLM nicht verfügbar | Local Fallback | Integration |
| RAG-E03 | Local nicht verfügbar | MiniLM Fallback | Integration |
| RAG-E04 | Kein Model verfügbar | Fehler | Integration |
| RAG-E05 | Model Cache (1h) | Kein neuer Check | Unit |

### Embedding Generation

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-EG01 | Text Embedding | 1024 Dims (VDR-2B) | Integration |
| RAG-EG02 | Fallback Embedding | 384 Dims (MiniLM) | Integration |
| RAG-EG03 | Batch Embedding | 256 Chunks pro Batch | Integration |
| RAG-EG04 | Image Embedding | Multimodal Support | Integration |
| RAG-EG05 | Error Recovery | Retry mit Backoff | Integration |

### Collection Embedding

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-CE01 | Start Embedding | Status: processing | Integration |
| RAG-CE02 | Progress Updates | 0-100% via WebSocket | Integration |
| RAG-CE03 | Complete | Status: completed | Integration |
| RAG-CE04 | Error | Status: failed, Message | Integration |
| RAG-CE05 | Pause Embedding | Pausiert | Integration |
| RAG-CE06 | Resume Embedding | Fortgesetzt | Integration |

---

## 4. ChromaDB Storage

**Pfad:** `/app/storage/vectorstore/`

### Collection Management

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-S01 | Collection erstellen | Chroma Collection | Integration |
| RAG-S02 | Collection Name | llars_{name}_{model} | Integration |
| RAG-S03 | Collection löschen | Chunks entfernt | Integration |
| RAG-S04 | Metadata | hnsw:space=cosine | Integration |

### Vector Storage

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-VS01 | Upsert Chunks | Vectors gespeichert | Integration |
| RAG-VS02 | Vector ID Format | doc_{id}_chunk_{i}_{uuid} | Integration |
| RAG-VS03 | Metadata Storage | document_id, chunk_index | Integration |
| RAG-VS04 | Duplicate Detection | Hash-basiert | Integration |

### Self-Healing

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-SH01 | Chroma leer, DB hat Chunks | Backfill | Integration |
| RAG-SH02 | Inconsistent State | Re-Index | Integration |

---

## 5. Retrieval

**Service:** `ChatService`

### Semantic Search

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-R01 | Basic Query | Top-K Results | Integration |
| RAG-R02 | Query Embedding | Same Model as Docs | Integration |
| RAG-R03 | Cosine Similarity | Korrekte Scores | Integration |
| RAG-R04 | Empty Query | Keine Ergebnisse | Integration |
| RAG-R05 | Multi-Collection | Merged Results | Integration |

### Lexical Search

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-LS01 | Token Extraction | Stopwords gefiltert | Unit |
| RAG-LS02 | Compound Words | Gesplittet | Unit |
| RAG-LS03 | German Synonyms | Expanded | Unit |
| RAG-LS04 | BM25 Scoring | Overlap Ratio | Unit |

### Hybrid Search

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-HS01 | Vector + Lexical | Combined Score | Integration |
| RAG-HS02 | Alpha Parameter | Gewichtung korrekt | Unit |
| RAG-HS03 | Fallback to Lexical | Bei Vector-Fehler | Integration |

---

## 6. Reranking

**Service:** `Reranker`
**Modes:** off, lexical, cross-encoder

### Lexical Reranking

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-RR01 | Mode: lexical | Token-Overlap | Integration |
| RAG-RR02 | Score Formula | (1-α)*vector + α*overlap | Unit |
| RAG-RR03 | Alpha Default | 0.15 | Unit |

### Cross-Encoder

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-CR01 | Mode: cross-encoder | CE Score | Integration |
| RAG-CR02 | Model Cache | LRU (4 max) | Unit |
| RAG-CR03 | German Model | ELECTRA-based | Integration |

---

## 7. Access Control

**Service:** `RAGAccessService`

### Document Access

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-AC01 | Owner Access | Immer erlaubt | Unit |
| RAG-AC02 | Admin Access | Immer erlaubt | Unit |
| RAG-AC03 | Public Document | Jeder kann sehen | Unit |
| RAG-AC04 | Collection Permission | Cascade zu Docs | Unit |
| RAG-AC05 | Explicit Permission | User/Role-based | Unit |
| RAG-AC06 | No Permission | 403 Forbidden | Integration |

### Collection Access

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RAG-ACC01 | Owner Access | Immer erlaubt | Unit |
| RAG-ACC02 | Public Collection | Jeder kann sehen | Unit |
| RAG-ACC03 | Shared Collection | Explizit geteilt | Unit |
| RAG-ACC04 | Role-based Access | Via Rolle | Unit |

---

## 8. API Endpoints

### Documents

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| API-D01 | GET /api/rag/documents | Liste mit Filter | Integration |
| API-D02 | GET /api/rag/documents/:id | Document Details | Integration |
| API-D03 | GET /api/rag/documents/:id/content | Full Text | Integration |
| API-D04 | GET /api/rag/documents/:id/chunks | Chunk Liste | Integration |
| API-D05 | GET /api/rag/documents/:id/download | Original File | Integration |
| API-D06 | PUT /api/rag/documents/:id | Update Metadata | Integration |
| API-D07 | DELETE /api/rag/documents/:id | Soft Delete | Integration |

### Collections

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| API-C01 | GET /api/rag/collections | Liste | Integration |
| API-C02 | GET /api/rag/collections/:id | Details | Integration |
| API-C03 | POST /api/rag/collections | Create | Integration |
| API-C04 | PUT /api/rag/collections/:id | Update | Integration |
| API-C05 | DELETE /api/rag/collections/:id | Delete + Cascade | Integration |
| API-C06 | POST /api/rag/collections/:id/embed | Start Embedding | Integration |
| API-C07 | DELETE /api/rag/collections/:id/embed | Pause Embedding | Integration |
| API-C08 | POST /api/rag/collections/:id/reindex | Requeue All | Integration |

---

## 9. Test-Code

```python
# tests/integration/rag/test_pipeline.py
import pytest
from pathlib import Path


class TestDocumentUpload:
    """Document Upload Tests"""

    def test_RAG_U01_pdf_upload(self, authenticated_client, test_pdf):
        """PDF Upload erstellt Dokument"""
        with open(test_pdf, 'rb') as f:
            response = authenticated_client.post(
                '/api/rag/documents/upload',
                data={'file': (f, 'test.pdf')},
                content_type='multipart/form-data'
            )
        assert response.status_code == 201
        assert 'document_id' in response.json

    def test_RAG_U05_invalid_type(self, authenticated_client):
        """Unerlaubter Dateityp wird abgelehnt"""
        response = authenticated_client.post(
            '/api/rag/documents/upload',
            data={'file': (b'content', 'malware.exe')},
            content_type='multipart/form-data'
        )
        assert response.status_code == 400
        assert 'unsupported' in response.json['error'].lower()


class TestChunking:
    """Chunking Tests"""

    def test_RAG_CH01_standard_chunking(self, lumber_chunker, sample_text):
        """Standard Text wird in 1500-char Chunks geteilt"""
        chunks = lumber_chunker.chunk_text(sample_text)
        for chunk in chunks:
            assert len(chunk.text) <= 1500

    def test_RAG_CH02_overlap(self, lumber_chunker, long_text):
        """Chunks haben 300 chars Überlappung"""
        chunks = lumber_chunker.chunk_text(long_text)
        if len(chunks) > 1:
            # Prüfe Überlappung zwischen erstem und zweitem Chunk
            overlap = chunks[0].text[-300:]
            assert overlap in chunks[1].text


class TestEmbedding:
    """Embedding Tests"""

    def test_RAG_E01_litellm_embedding(self, embedding_service, sample_texts):
        """LiteLLM Embedding generiert 1024 Dimensionen"""
        embeddings = embedding_service.embed_texts(sample_texts)
        assert len(embeddings[0]) == 1024

    def test_RAG_E03_fallback(self, embedding_service_no_litellm, sample_texts):
        """Fallback zu MiniLM bei LiteLLM-Fehler"""
        embeddings = embedding_service_no_litellm.embed_texts(sample_texts)
        assert len(embeddings[0]) == 384  # MiniLM dimensions


class TestRetrieval:
    """Retrieval Tests"""

    def test_RAG_R01_basic_query(self, rag_service, indexed_collection):
        """Basic Query gibt Top-K Results"""
        results = rag_service.search(
            query="test query",
            collection_id=indexed_collection.id,
            top_k=4
        )
        assert len(results) <= 4
        assert all('score' in r for r in results)

    def test_RAG_R05_multi_collection(self, rag_service, two_collections):
        """Multi-Collection Search merged Results"""
        results = rag_service.search(
            query="test query",
            collection_ids=[c.id for c in two_collections],
            top_k=4
        )
        # Results können aus beiden Collections kommen
        collection_ids = {r['collection_id'] for r in results}
        assert len(collection_ids) >= 1


class TestAccessControl:
    """Access Control Tests"""

    def test_RAG_AC01_owner_access(self, rag_access_service, user, owned_document):
        """Owner hat immer Zugriff"""
        assert rag_access_service.can_view_document(user, owned_document) is True

    def test_RAG_AC06_no_permission(self, client, researcher_token, private_document):
        """Kein Zugriff ohne Permission"""
        response = client.get(
            f'/api/rag/documents/{private_document.id}',
            headers={'Authorization': f'Bearer {researcher_token}'}
        )
        assert response.status_code == 403
```

---

## 10. Fixtures

```python
# tests/conftest.py
import pytest
from pathlib import Path


@pytest.fixture
def test_pdf():
    """Test PDF Datei"""
    return Path(__file__).parent / 'fixtures/files/test.pdf'


@pytest.fixture
def sample_text():
    """Sample Text für Chunking"""
    return "Lorem ipsum " * 500  # ~6000 chars


@pytest.fixture
def lumber_chunker(app):
    """LumberChunker Instance"""
    from app.services.rag.lumber_chunker import LumberChunker
    return LumberChunker(chunk_size=1500, chunk_overlap=300)


@pytest.fixture
def embedding_service(app):
    """EmbeddingModelService Instance"""
    from app.services.rag.embedding_model_service import EmbeddingModelService
    return EmbeddingModelService()


@pytest.fixture
def indexed_collection(db, test_documents):
    """Collection mit indexierten Dokumenten"""
    from app.db.models import RAGCollection
    collection = RAGCollection(
        name='test_collection',
        embedding_model='test-model',
        total_chunks=10
    )
    db.session.add(collection)
    db.session.commit()
    return collection
```

---

## 11. E2E Test-Code

```typescript
// e2e/rag/rag-pipeline.spec.ts
import { test, expect } from '../fixtures/auth'

test.describe('RAG Pipeline', () => {
  test('complete upload to retrieval flow', async ({ adminPage }) => {
    // 1. Upload
    await adminPage.goto('/admin?tab=rag')
    await adminPage.setInputFiles('input[type="file"]', 'e2e/fixtures/test.pdf')
    await expect(adminPage.locator('.upload-success')).toBeVisible({ timeout: 30000 })

    // 2. Wait for Embedding
    await expect(adminPage.locator('.embedding-status:has-text("completed")')).toBeVisible({
      timeout: 120000
    })

    // 3. Test in Chat
    await adminPage.goto('/chat')
    await adminPage.click('.chatbot-item >> nth=0')
    await adminPage.fill('.message-input', 'What is in the document?')
    await adminPage.click('button:has-text("Senden")')

    // 4. Check Sources
    await expect(adminPage.locator('.sources-panel .source-chunk')).toBeVisible({
      timeout: 30000
    })
  })
})
```

---

## 12. Checkliste für manuelle Tests

### Upload
- [ ] PDF hochladen funktioniert
- [ ] TXT/MD/DOCX hochladen funktioniert
- [ ] Ungültige Dateien werden abgelehnt
- [ ] Duplikate werden erkannt
- [ ] Multi-Upload funktioniert

### Embedding
- [ ] Embedding startet automatisch
- [ ] Progress wird angezeigt
- [ ] Status wechselt zu "completed"
- [ ] Fehler werden angezeigt

### Retrieval
- [ ] Chat findet relevante Chunks
- [ ] Sources werden angezeigt
- [ ] Multi-Collection funktioniert

### Access Control
- [ ] Nur erlaubte Dokumente sichtbar
- [ ] Sharing funktioniert
- [ ] Admin sieht alles

---

## 13. Umgebungsvariablen

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `LITELLM_API_KEY` | - | LiteLLM API Key |
| `LITELLM_BASE_URL` | - | LiteLLM Base URL |
| `HF_HOME` | - | HuggingFace Cache |
| `RAG_RERANK_MODE` | `lexical` | off/lexical/cross-encoder |
| `RAG_RERANK_ALPHA` | `0.15` | Lexical Weight |
| `LEXICAL_INDEX_PATH` | - | FTS Index Path |

---

**Letzte Aktualisierung:** 30. Dezember 2025
