# RAG Routes Module Structure

## Overview

The RAG routes have been refactored from a single monolithic file (RAGRoutes.py) into smaller, focused modules for better maintainability.

## Module Structure

```
routes/rag/
├── __init__.py              # Main blueprint registration
├── collection_routes.py     # Collection management
├── document_routes.py       # Document management  
├── search_routes.py         # Search and statistics
├── admin_routes.py          # Admin and processing queue
└── RAGRoutes.py            # DEPRECATED - backward compatibility wrapper
```

## Blueprint Organization

### Main Blueprint (`rag_bp`)
- **Prefix:** `/api/rag`
- **Defined in:** `__init__.py`
- **Purpose:** Aggregates all RAG sub-blueprints

### Sub-Blueprints

#### 1. Collection Routes (`rag_collection_bp`)
**File:** `collection_routes.py`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/collections` | List all collections |
| GET | `/collections/<id>` | Get collection details |
| POST | `/collections` | Create new collection |
| PUT | `/collections/<id>` | Update collection |
| DELETE | `/collections/<id>` | Delete collection |

**Permissions:**
- View: `feature:rag:view`
- Edit: `feature:rag:edit`
- Delete: `feature:rag:delete`

#### 2. Document Routes (`rag_document_bp`)
**File:** `document_routes.py`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents` | List documents (with filters) |
| GET | `/documents/<id>` | Get document details |
| GET | `/documents/<id>/content` | Get document text content |
| GET | `/documents/<id>/chunks` | Get document chunks |
| GET | `/documents/<id>/download` | Download document file |
| POST | `/documents/upload` | Upload single document |
| POST | `/documents/upload-multiple` | Upload multiple documents |
| PUT | `/documents/<id>` | Update document metadata |
| DELETE | `/documents/<id>` | Delete document |

**Permissions:**
- View: `feature:rag:view`
- Edit: `feature:rag:edit`
- Delete: `feature:rag:delete`

**Helper Functions:**
- `allowed_file(filename)` - Check file extension
- `get_file_hash(file_path)` - Calculate SHA-256 hash

**Configuration:**
- `ALLOWED_EXTENSIONS`: `{'pdf', 'txt', 'md', 'docx', 'doc'}`
- `MAX_FILE_SIZE`: `50 MB`
- `RAG_DOCS_PATH`: `/app/rag_docs`

#### 3. Search Routes (`rag_search_bp`)
**File:** `search_routes.py`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stats` | System overview stats |
| GET | `/stats/overview` | System overview stats (alias) |
| GET | `/stats/popular-documents` | Most retrieved documents |
| GET | `/stats/popular-queries` | Most common queries |
| GET | `/embedding-info` | Embedding model information |

**Permissions:**
- All endpoints: `feature:rag:view`

#### 4. Admin Routes (`rag_admin_bp`)
**File:** `admin_routes.py`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/processing-queue` | Get queue status |
| POST | `/processing-queue/<id>/retry` | Retry failed processing |

**Permissions:**
- View: `feature:rag:view`
- Edit: `feature:rag:edit`

## Usage

### New Code (Recommended)

```python
from routes.rag import rag_bp
app.register_blueprint(rag_bp)
```

This registers all RAG routes under `/api/rag/*`

### Legacy Code (Deprecated)

```python
from routes.rag.RAGRoutes import rag_collection_bp, rag_document_bp
# This still works but will issue a DeprecationWarning
```

## Migration Guide

### For Developers

1. **Update imports:**
   ```python
   # Old
   from routes.rag.RAGRoutes import some_function
   
   # New
   from routes.rag import rag_bp
   # Or for specific sub-blueprint:
   from routes.rag.document_routes import rag_document_bp
   ```

2. **Blueprint registration:**
   ```python
   # Old (if directly using data_blueprint)
   # Routes were registered on data_blueprint
   
   # New
   app.register_blueprint(rag_bp)  # All RAG routes
   ```

### For Frontend/API Consumers

**No changes required.** All endpoint URLs remain the same:
- `/api/rag/collections`
- `/api/rag/documents`
- `/api/rag/stats`
- etc.

## Benefits of Refactoring

1. **Modularity:** Each file focuses on a specific domain (collections, documents, search, admin)
2. **Maintainability:** Easier to find and update specific functionality
3. **Code Organization:** ~1200 lines split into 4 files of ~200-400 lines each
4. **Clear Separation:** Business logic separated by concern
5. **Backward Compatibility:** Old code continues to work with deprecation warnings

## File Sizes

| File | Lines | Purpose |
|------|-------|---------|
| `collection_routes.py` | ~280 | Collection CRUD operations |
| `document_routes.py` | ~650 | Document upload, management, download |
| `search_routes.py` | ~190 | Statistics and embedding info |
| `admin_routes.py` | ~95 | Processing queue management |
| `__init__.py` | ~35 | Blueprint registration |
| `RAGRoutes.py` | ~85 | Deprecated wrapper |

## Future Improvements

1. **Remove deprecated file:** After migration period, delete `RAGRoutes.py`
2. **Add search endpoints:** Implement actual RAG search/retrieval in `search_routes.py`
3. **Add tests:** Create unit tests for each module
4. **Add API docs:** Generate OpenAPI/Swagger docs from routes

---

**Last Updated:** 2025-11-28
**Refactored By:** Claude Code
