import os
import re
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from db.db import db
from db.tables import RAGDocument, RAGDocumentChunk, CollectionDocumentLink

logger = logging.getLogger(__name__)


class LexicalSearchIndex:
    _DEFAULT_DB_NAME = "lexical_index.sqlite"
    _SCHEMA_VERSION = "1"
    _TOKEN_RE = re.compile(r"[\wäöüÄÖÜß]+", re.UNICODE)
    _STOPWORDS_DE = {
        'a', 'aber', 'als', 'am', 'an', 'auch', 'auf', 'aus', 'bei', 'bin', 'bis', 'bist', 'da', 'dadurch', 'daher',
        'darum', 'das', 'dass', 'dein', 'deine', 'dem', 'den', 'der', 'des', 'dich', 'die', 'dies', 'diese', 'dieser',
        'dieses', 'dir', 'doch', 'dort', 'du', 'durch', 'ein', 'eine', 'einem', 'einen', 'einer', 'eines', 'er', 'es',
        'euer', 'eure', 'für', 'hatte', 'hatten', 'hattest', 'hattet', 'hier', 'hinter', 'ich', 'ihr', 'ihre', 'im',
        'in', 'ist', 'ja', 'jede', 'jedem', 'jeden', 'jeder', 'jedes', 'jener', 'jenes', 'jetzt', 'kann', 'kannst',
        'können', 'könnt', 'machen', 'mein', 'meine', 'mit', 'muss', 'musst', 'müssen', 'müsst', 'nach', 'nachdem',
        'nein', 'nicht', 'nun', 'oder', 'seid', 'sein', 'seine', 'sich', 'sie', 'sind', 'so', 'soll', 'sollen',
        'sollst', 'sollt', 'sonst', 'soweit', 'sowie', 'und', 'unser', 'unsere', 'unter', 'vom', 'von', 'vor', 'wann',
        'warum', 'was', 'weiter', 'weitere', 'wenn', 'wer', 'werde', 'werden', 'werdet', 'weshalb', 'wie', 'wieder',
        'wieso', 'wir', 'wird', 'wirst', 'wo', 'woher', 'wohin', 'zu', 'zum', 'zur', 'über'
    }

    @classmethod
    def _get_db_path(cls) -> str:
        configured = os.environ.get("LEXICAL_INDEX_PATH")
        if configured:
            return configured
        base_dir = Path(__file__).resolve().parents[2]  # /app/app
        return str(base_dir / "data" / "rag" / "indexes" / cls._DEFAULT_DB_NAME)

    @classmethod
    def _connect(cls) -> sqlite3.Connection:
        path = cls._get_db_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        conn = sqlite3.connect(path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    @classmethod
    def _ensure_schema(cls, conn: sqlite3.Connection) -> None:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS rag_fts_meta (key TEXT PRIMARY KEY, value TEXT)"
        )
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS rag_fts USING fts5(
                title,
                content,
                document_id UNINDEXED,
                chunk_id UNINDEXED,
                chunk_index UNINDEXED,
                collection_ids UNINDEXED,
                filename UNINDEXED,
                page_number UNINDEXED,
                start_char UNINDEXED,
                end_char UNINDEXED,
                vector_id UNINDEXED,
                tokenize='trigram'
            )
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO rag_fts_meta (key, value) VALUES ('schema_version', ?)",
            (cls._SCHEMA_VERSION,)
        )
        conn.commit()

    @classmethod
    def _build_query(cls, query: str) -> str:
        tokens = [t.lower() for t in cls._TOKEN_RE.findall(query or "")]
        tokens = [t for t in tokens if len(t) >= 2 and t not in cls._STOPWORDS_DE]
        if not tokens:
            return ""

        groups = []
        for token in tokens:
            if len(token) <= 5:
                groups.append(token)
                continue
            trigrams = [token[i:i + 3] for i in range(len(token) - 2)]
            if not trigrams:
                groups.append(token)
                continue
            step = max(1, len(trigrams) // 8)
            selected = trigrams[::step][:8]
            group = " OR ".join(selected)
            groups.append(f"({group})")

        return " AND ".join(groups)

    @classmethod
    def _collection_ids_to_string(cls, collection_ids: List[int]) -> str:
        unique = [str(cid) for cid in dict.fromkeys(collection_ids) if cid is not None]
        if not unique:
            return ""
        return "|" + "|".join(unique) + "|"

    @classmethod
    def _get_document_collection_ids(cls, document: RAGDocument) -> List[int]:
        ids = [link.collection_id for link in document.collection_links if link.collection_id]
        if not ids and document.collection_id:
            ids = [document.collection_id]
        return ids

    @classmethod
    def reindex_document(cls, document_id: int) -> None:
        document = RAGDocument.query.get(document_id)
        if not document:
            return

        collection_ids = cls._get_document_collection_ids(document)
        collection_ids_str = cls._collection_ids_to_string(collection_ids)

        chunks = (
            RAGDocumentChunk.query
            .filter_by(document_id=document_id, has_image=False)
            .order_by(RAGDocumentChunk.chunk_index.asc())
            .all()
        )

        if not chunks:
            return

        conn = cls._connect()
        try:
            cls._ensure_schema(conn)
            conn.execute("DELETE FROM rag_fts WHERE document_id = ?", (str(document_id),))

            rows = []
            for chunk in chunks:
                rows.append((
                    document.title or document.original_filename or document.filename or "",
                    chunk.content or "",
                    str(document.id),
                    str(chunk.id),
                    str(chunk.chunk_index),
                    collection_ids_str,
                    document.filename or "",
                    str(chunk.page_number) if chunk.page_number is not None else "",
                    str(chunk.start_char) if chunk.start_char is not None else "",
                    str(chunk.end_char) if chunk.end_char is not None else "",
                    chunk.vector_id or ""
                ))

            conn.executemany(
                """
                INSERT INTO rag_fts (
                    title, content, document_id, chunk_id, chunk_index, collection_ids,
                    filename, page_number, start_char, end_char, vector_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows
            )
            conn.commit()
        finally:
            conn.close()

    @classmethod
    def remove_document(cls, document_id: int) -> None:
        conn = cls._connect()
        try:
            cls._ensure_schema(conn)
            conn.execute("DELETE FROM rag_fts WHERE document_id = ?", (str(document_id),))
            conn.commit()
        finally:
            conn.close()

    @classmethod
    def remove_collection(cls, collection_id: int) -> None:
        conn = cls._connect()
        try:
            cls._ensure_schema(conn)
            token = f"|{collection_id}|"
            cursor = conn.execute(
                "SELECT rowid, collection_ids FROM rag_fts WHERE collection_ids LIKE ?",
                (f"%{token}%",)
            )
            updates = []
            for rowid, value in cursor.fetchall():
                if not value:
                    continue
                updated = value.replace(token, "|")
                updated = updated.replace("||", "|")
                if updated == "|":
                    updated = ""
                updates.append((updated, rowid))
            if updates:
                conn.executemany(
                    "UPDATE rag_fts SET collection_ids = ? WHERE rowid = ?",
                    updates
                )
            conn.commit()
        finally:
            conn.close()

    @classmethod
    def ensure_collection_indexed(cls, collection_id: int) -> None:
        if not collection_id:
            return
        conn = cls._connect()
        try:
            cls._ensure_schema(conn)
            token = f"|{collection_id}|"
            cursor = conn.execute(
                "SELECT 1 FROM rag_fts WHERE collection_ids LIKE ? LIMIT 1",
                (f"%{token}%",)
            )
            exists = cursor.fetchone() is not None
        finally:
            conn.close()

        if exists:
            return

        doc_ids = set()
        linked_ids = (
            db.session.query(CollectionDocumentLink.document_id)
            .filter(CollectionDocumentLink.collection_id == collection_id)
            .all()
        )
        doc_ids.update([row[0] for row in linked_ids if row and row[0]])
        direct_ids = (
            db.session.query(RAGDocument.id)
            .filter(RAGDocument.collection_id == collection_id)
            .all()
        )
        doc_ids.update([row[0] for row in direct_ids if row and row[0]])

        for doc_id in doc_ids:
            try:
                cls.reindex_document(doc_id)
            except Exception as exc:
                logger.warning(f"[LexicalSearchIndex] Failed to index document {doc_id}: {exc}")

    @classmethod
    def search(
        cls,
        query: str,
        collection_ids: Optional[List[int]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        fts_query = cls._build_query(query)
        if not fts_query:
            return []

        if collection_ids:
            for cid in collection_ids:
                cls.ensure_collection_indexed(cid)

        conn = cls._connect()
        try:
            cls._ensure_schema(conn)
            where = ""
            params: List[Any] = [fts_query]
            if collection_ids:
                filters = []
                for cid in collection_ids:
                    filters.append("collection_ids LIKE ?")
                    params.append(f"%|{cid}|%")
                where = " AND (" + " OR ".join(filters) + ")"
            params.append(limit)

            rows = conn.execute(
                f"""
                SELECT
                    title,
                    content,
                    document_id,
                    chunk_id,
                    chunk_index,
                    collection_ids,
                    filename,
                    page_number,
                    start_char,
                    end_char,
                    vector_id,
                    bm25(rag_fts, 5.0, 1.0) AS score
                FROM rag_fts
                WHERE rag_fts MATCH ? {where}
                ORDER BY score
                LIMIT ?
                """,
                params
            ).fetchall()
        finally:
            conn.close()

        results = []
        for row in rows:
            title, content, doc_id, chunk_id, chunk_index, _, filename, page_number, start_char, end_char, vector_id, score = row
            results.append({
                'content': content,
                'score': float(score) if score is not None else 0.0,
                'document_id': int(doc_id) if doc_id else None,
                'title': title,
                'filename': filename,
                'chunk_index': int(chunk_index) if chunk_index else None,
                'page_number': int(page_number) if page_number else None,
                'start_char': int(start_char) if start_char else None,
                'end_char': int(end_char) if end_char else None,
                'vector_id': vector_id,
                'metadata': {
                    'document_id': int(doc_id) if doc_id else None,
                    'chunk_index': int(chunk_index) if chunk_index else None,
                    'filename': filename,
                    'page_number': int(page_number) if page_number else None,
                    'start_char': int(start_char) if start_char else None,
                    'end_char': int(end_char) if end_char else None,
                    'vector_id': vector_id
                }
            })
        return results
