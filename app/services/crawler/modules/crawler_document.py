# crawler_document.py
"""
Document processing for the crawler service.

This module handles the creation and linking of RAG documents from crawled web pages.
It implements the document deduplication and linking logic that allows documents
to exist in multiple collections efficiently.

Key responsibilities:
- Creating new RAGDocument records from crawled content
- Linking existing documents to new collections (deduplication)
- Storing screenshots and images as RAGDocumentChunks
- Managing the RAG processing queue

Document Linking Logic:
- If a document with the same content hash exists, it is LINKED to the collection
- If the document is new, it is CREATED and linked
- Documents can exist in multiple collections via CollectionDocumentLink

Used by: crawler_service.py, crawler_processing.py
Depends on: crawler_constants.py, db.tables
"""

from __future__ import annotations

import os
import logging
from datetime import datetime
from urllib.parse import urlparse
from typing import Dict, Optional, Any

from .crawler_constants import (
    RAG_DOCS_PATH,
    generate_filename_from_url,
    is_content_worth_indexing,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DOCUMENT PROCESSING
# =============================================================================

def process_crawled_page(
    job_id: str,
    page: Dict,
    collection_id: int,
    created_by: str,
    seen_hashes: set,
    active_crawls: Dict[str, Dict]
) -> Optional[Dict[str, Any]]:
    """
    Process a single crawled page and create/link the corresponding document.

    This is the main document processing function that handles:
    1. Content quality validation
    2. Duplicate detection (by content hash)
    3. Document creation or linking
    4. Screenshot and image storage
    5. RAG processing queue entry

    Args:
        job_id: UUID of the crawl job
        page: Crawled page data dict containing:
            - url: Source URL
            - content: Extracted text content
            - content_hash: SHA256 hash of content
            - metadata: Dict with title, description, language, keywords
            - screenshot: Optional screenshot data (Playwright)
            - images: Optional list of extracted images
        collection_id: Target collection ID
        created_by: Username of the user who initiated the crawl
        seen_hashes: Set of content hashes already seen in this crawl (for dedup)
        active_crawls: Reference to active jobs dict (for stats updates)

    Returns:
        Dict with 'action' ('new' or 'linked') and 'document' (serialized),
        or None if page was skipped/failed

    Database Effects:
        - May create RAGDocument
        - May create CollectionDocumentLink
        - May create RAGDocumentChunk (for screenshots/images)
        - May create RAGProcessingQueue entry
        - Commits on success, rolls back on error
    """
    from db.database import db
    from db.tables import (
        RAGDocument,
        RAGDocumentChunk,
        RAGProcessingQueue,
        CollectionDocumentLink
    )

    try:
        # =================================================================
        # STEP 1: Validate content quality
        # =================================================================
        if not is_content_worth_indexing(page.get('content', '')):
            logger.debug(f"Skipping page with insufficient content: {page.get('url', 'unknown')}")
            return None

        content_hash = page['content_hash']

        # =================================================================
        # STEP 2: Check for duplicates within this crawl session
        # =================================================================
        if content_hash in seen_hashes:
            logger.debug(f"Skipping duplicate content within crawl for {page['url']}")
            return None
        seen_hashes.add(content_hash)

        # =================================================================
        # STEP 3: Check if document already exists in database
        # =================================================================
        existing_doc = RAGDocument.query.filter_by(file_hash=content_hash).first()

        if existing_doc:
            return _link_existing_document(
                job_id=job_id,
                page=page,
                existing_doc=existing_doc,
                collection_id=collection_id,
                created_by=created_by,
                active_crawls=active_crawls
            )
        else:
            return _create_new_document(
                job_id=job_id,
                page=page,
                collection_id=collection_id,
                created_by=created_by,
                active_crawls=active_crawls
            )

    except Exception as e:
        logger.error(f"Error processing document for {page.get('url', 'unknown')}: {e}")
        from db.database import db
        db.session.rollback()
        active_crawls[job_id]['errors'].append({
            'url': page.get('url', 'unknown'),
            'error': str(e)
        })
        return None


# =============================================================================
# DOCUMENT LINKING (Existing Document)
# =============================================================================

def _link_existing_document(
    job_id: str,
    page: Dict,
    existing_doc: Any,
    collection_id: int,
    created_by: str,
    active_crawls: Dict[str, Dict]
) -> Optional[Dict[str, Any]]:
    """
    Link an existing document to a new collection.

    When crawled content matches an existing document (by hash), we link
    the existing document to the new collection instead of creating a duplicate.
    This saves storage and maintains consistency.

    Args:
        job_id: UUID of the crawl job
        page: Crawled page data
        existing_doc: Existing RAGDocument object
        collection_id: Target collection ID
        created_by: Username
        active_crawls: Active jobs dict for stats

    Returns:
        Dict with action='linked' and serialized document, or None
    """
    from db.database import db
    from db.tables import RAGDocumentChunk, CollectionDocumentLink

    # Check if already linked to this collection
    existing_link = CollectionDocumentLink.query.filter_by(
        collection_id=collection_id,
        document_id=existing_doc.id
    ).first()

    if existing_link:
        logger.debug(f"Document already linked to collection for {page['url']}")
        return None

    # =================================================================
    # Handle screenshots for existing document (if not already present)
    # =================================================================
    screenshot_data = page.get('screenshot') if isinstance(page, dict) else None
    if screenshot_data and not existing_doc.screenshot_path:
        _add_screenshots_to_document(
            job_id=job_id,
            doc=existing_doc,
            page=page,
            screenshot_data=screenshot_data
        )

    # =================================================================
    # Create the collection link
    # =================================================================
    link = CollectionDocumentLink(
        collection_id=collection_id,
        document_id=existing_doc.id,
        link_type='linked',              # Indicates this was linked, not created
        source_url=page['url'],
        crawl_job_id=job_id,
        linked_at=datetime.now(),
        linked_by=created_by
    )
    db.session.add(link)
    db.session.commit()

    # Update lexical search index for the linked document
    try:
        from services.chatbot.lexical_index import LexicalSearchIndex
        LexicalSearchIndex.reindex_document(existing_doc.id)
    except Exception as exc:
        logger.warning(f"[CrawlerDocument] Lexical index update failed for doc {existing_doc.id}: {exc}")

    # Update stats
    active_crawls[job_id]['documents_linked'] += 1
    logger.info(f"[Job {job_id}] Linked existing document {existing_doc.id} to collection {collection_id}")

    # Return serialized document for WebSocket update
    try:
        from services.rag.document_service import DocumentService
        return {
            'action': 'linked',
            'document': DocumentService.serialize_document(existing_doc)
        }
    except Exception:
        return None


# =============================================================================
# DOCUMENT CREATION (New Document)
# =============================================================================

def _create_new_document(
    job_id: str,
    page: Dict,
    collection_id: int,
    created_by: str,
    active_crawls: Dict[str, Dict]
) -> Optional[Dict[str, Any]]:
    """
    Create a new document from crawled page content.

    Creates the markdown file, database record, screenshots/images,
    and queues for RAG processing.

    Args:
        job_id: UUID of the crawl job
        page: Crawled page data
        collection_id: Target collection ID
        created_by: Username
        active_crawls: Active jobs dict for stats

    Returns:
        Dict with action='new' and serialized document, or None
    """
    from db.database import db
    from db.tables import (
        RAGDocument,
        RAGDocumentChunk,
        RAGProcessingQueue,
        CollectionDocumentLink
    )

    # =================================================================
    # STEP 1: Write content to markdown file
    # =================================================================
    filename = generate_filename_from_url(page['url'])
    file_path = os.path.join(RAG_DOCS_PATH, filename)
    os.makedirs(RAG_DOCS_PATH, exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(page['content'])

    # =================================================================
    # STEP 2: Create RAGDocument record
    # =================================================================
    screenshot_data = page.get('screenshot')
    screenshot_path = screenshot_data.get('screenshot_path') if screenshot_data else None

    doc = RAGDocument(
        # File information
        filename=filename,
        original_filename=page['metadata'].get('title', page['url'])[:255],
        file_path=file_path,
        file_size_bytes=len(page['content'].encode('utf-8')),
        mime_type='text/markdown',
        file_hash=page['content_hash'],

        # Metadata from page
        title=page['metadata'].get('title', '')[:255],
        description=page['metadata'].get('description', '')[:500],
        author=urlparse(page['url']).netloc,
        language=page['metadata'].get('language', 'de'),
        keywords=page['metadata'].get('keywords', ''),

        # Status and collection
        status='pending',
        collection_id=collection_id,
        is_public=False,  # Inherit visibility from collection

        # Ownership
        uploaded_by=created_by,
        uploaded_at=datetime.now(),

        # Playwright/Vision-LLM fields
        screenshot_path=screenshot_path,
        source_url=page['url']
    )
    db.session.add(doc)
    db.session.flush()  # Get document ID

    # Set screenshot URL for API access
    if screenshot_path and not getattr(doc, 'screenshot_url', None):
        doc.screenshot_url = f"/api/rag/documents/{doc.id}/screenshot"

    # =================================================================
    # STEP 3: Store extracted images as chunks
    # =================================================================
    images = page.get('images', [])
    if images:
        _store_image_chunks(doc.id, images)
        logger.info(f"[Job {job_id}] Stored {len(images)} images for document {doc.id}")

    # =================================================================
    # STEP 4: Store screenshots as chunks
    # =================================================================
    if screenshot_data:
        stored_count = _store_screenshot_chunks(
            doc_id=doc.id,
            page=page,
            screenshot_data=screenshot_data
        )
        if stored_count:
            logger.info(f"[Job {job_id}] Stored {stored_count} screenshot(s) for document {doc.id}")

    # =================================================================
    # STEP 5: Create collection link
    # =================================================================
    link = CollectionDocumentLink(
        collection_id=collection_id,
        document_id=doc.id,
        link_type='new',                 # Indicates this document was created by this crawl
        source_url=page['url'],
        crawl_job_id=job_id,
        linked_at=datetime.now(),
        linked_by=created_by
    )
    db.session.add(link)

    # =================================================================
    # STEP 6: Queue for RAG processing
    # =================================================================
    queue_entry = RAGProcessingQueue(
        document_id=doc.id,
        priority=5,                      # Default priority
        status='queued',
        created_at=datetime.now()
    )
    db.session.add(queue_entry)
    db.session.commit()

    # =================================================================
    # STEP 7: Update statistics
    # =================================================================
    active_crawls[job_id]['documents_created'] += 1

    if images:
        active_crawls[job_id]['images_extracted'] = (
            active_crawls[job_id].get('images_extracted', 0) + len(images)
        )

    if screenshot_data and screenshot_path:
        active_crawls[job_id]['screenshots_taken'] = (
            active_crawls[job_id].get('screenshots_taken', 0) +
            screenshot_data.get('screenshot_count', 1)
        )

    crawler_type = page.get('crawler_type', 'basic')
    logger.info(f"[Job {job_id}] Created new document {doc.id} for {page['url']} (crawler: {crawler_type})")

    # Return serialized document for WebSocket update
    try:
        from services.rag.document_service import DocumentService
        return {
            'action': 'new',
            'document': DocumentService.serialize_document(doc)
        }
    except Exception:
        return None


# =============================================================================
# SCREENSHOT AND IMAGE STORAGE
# =============================================================================

def _add_screenshots_to_document(
    job_id: str,
    doc: Any,
    page: Dict,
    screenshot_data: Dict
) -> None:
    """
    Add screenshots to an existing document that doesn't have them yet.

    Called when linking an existing document that was originally crawled
    without screenshots (e.g., basic crawler) to a collection where
    screenshots are now available.

    Args:
        job_id: UUID of the crawl job
        doc: Existing RAGDocument object
        page: Crawled page data
        screenshot_data: Screenshot data from Playwright crawler
    """
    from db.database import db
    from db.tables import RAGDocumentChunk

    screenshot_path = screenshot_data.get('screenshot_path')
    if screenshot_path:
        doc.screenshot_path = screenshot_path
        if not getattr(doc, 'screenshot_url', None):
            doc.screenshot_url = f"/api/rag/documents/{doc.id}/screenshot"

    # Check if document already has screenshot chunks
    has_screenshot_chunks = (
        RAGDocumentChunk.query
        .filter_by(document_id=doc.id)
        .filter(RAGDocumentChunk.chunk_index >= 99999)
        .count() > 0
    )

    if not has_screenshot_chunks:
        stored_count = _store_screenshot_chunks(
            doc_id=doc.id,
            page=page,
            screenshot_data=screenshot_data
        )
        if stored_count:
            logger.info(
                f"[Job {job_id}] Stored {stored_count} screenshot(s) for existing document {doc.id}"
            )


def _store_image_chunks(doc_id: int, images: list) -> None:
    """
    Store extracted images as RAGDocumentChunks.

    Images are stored with high chunk indices (10000+) to avoid
    collision with regular text chunks.

    Args:
        doc_id: Document ID to attach images to
        images: List of image dicts with path, url, alt_text, mime_type
    """
    from db.database import db
    from db.tables import RAGDocumentChunk

    for idx, img in enumerate(images):
        image_chunk = RAGDocumentChunk(
            document_id=doc_id,
            chunk_index=10000 + idx,      # High index for images
            content=f"[Bild: {img.get('alt_text', 'Bild ohne Beschreibung')}]",
            has_image=True,
            image_path=img.get('image_path'),
            image_url=img.get('source_url'),
            image_alt_text=img.get('alt_text'),
            image_mime_type=img.get('mime_type', 'image/jpeg'),
            embedding_status='pending'
        )
        db.session.add(image_chunk)


def _store_screenshot_chunks(
    doc_id: int,
    page: Dict,
    screenshot_data: Dict
) -> int:
    """
    Store screenshots as RAGDocumentChunks.

    Screenshots are stored with very high chunk indices (99999+) to
    distinguish them from regular content and images. These chunks
    enable Vision-LLM queries and UI preview.

    Args:
        doc_id: Document ID to attach screenshots to
        page: Page data (for URL and metadata)
        screenshot_data: Screenshot data dict with screenshots list

    Returns:
        Number of screenshots stored
    """
    from db.database import db
    from db.tables import RAGDocumentChunk

    screenshot_entries = screenshot_data.get('screenshots') or []
    screenshot_path = screenshot_data.get('screenshot_path')

    # Fallback: if no entries but path exists, create single entry
    if not screenshot_entries and screenshot_path:
        screenshot_entries = [{'screenshot_path': screenshot_path}]

    stored = 0
    for idx, shot in enumerate(screenshot_entries):
        shot_path = (shot or {}).get('screenshot_path')
        if not shot_path:
            continue

        screenshot_chunk = RAGDocumentChunk(
            document_id=doc_id,
            chunk_index=99999 + idx,      # Very high index for screenshots
            content=f"[Screenshot der Webseite: {page['url']}]",
            has_image=True,
            image_path=shot_path,
            image_url=page['url'],
            image_alt_text=f"Screenshot von {page.get('metadata', {}).get('title', page['url'])}",
            image_mime_type='image/png',
            embedding_status='pending'
        )
        db.session.add(screenshot_chunk)
        stored += 1

    return stored
