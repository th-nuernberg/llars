# crawler_collection.py
"""
Collection management for the crawler service.

This module handles the creation and configuration of RAG collections
that store crawled web content. Collections are the organizational
unit for documents in the RAG system.

Key responsibilities:
- Creating new collections for crawl jobs
- Configuring collection metadata (name, description, source)
- Setting up embedding model associations

Used by: crawler_service.py
Depends on: crawler_constants.py, db.tables
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from .crawler_constants import (
    DEFAULT_ICON,
    DEFAULT_COLOR,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    build_crawl_collection_name,
    get_default_embedding_model_id,
)

logger = logging.getLogger(__name__)


# =============================================================================
# COLLECTION CREATION
# =============================================================================

def create_crawl_collection(
    urls: List[str],
    display_name: str,
    description: str,
    created_by: str,
    job_id: str
):
    """
    Create and persist a new RAGCollection for a crawl job.

    Creates a collection with appropriate defaults for web-crawled content.
    The collection is immediately persisted to the database (flush, not commit)
    so other operations can reference it.

    Args:
        urls: List of URLs being crawled (first URL used as source_url)
        display_name: User-friendly name for the collection
        description: Description text (auto-generated if empty)
        created_by: Username of the user who initiated the crawl
        job_id: UUID of the crawl job (used for unique naming)

    Returns:
        RAGCollection: The newly created collection object (already flushed to DB)

    Database Effects:
        - Inserts new row into rag_collections table
        - Uses db.session.flush() (caller must commit)

    Example:
        >>> collection = create_crawl_collection(
        ...     urls=["https://example.com"],
        ...     display_name="Example Site",
        ...     description="",
        ...     created_by="admin",
        ...     job_id="abc12345-..."
        ... )
        >>> print(collection.id)  # Available after flush
        42
    """
    from db.db import db
    from db.tables import RAGCollection

    # Generate safe internal name from domain + job ID
    internal_name = build_crawl_collection_name(urls, display_name, job_id)

    # Get default embedding model for new collections
    embedding_model = get_default_embedding_model_id()

    # Auto-generate description if not provided
    auto_description = description
    if not auto_description and urls:
        auto_description = f"Webcrawl von: {', '.join(urls)}"

    collection = RAGCollection(
        # Naming
        name=internal_name,                    # Internal unique name
        display_name=display_name,             # User-facing name

        # Metadata
        description=auto_description,
        icon=DEFAULT_ICON,                     # mdi-web icon
        color=DEFAULT_COLOR,                   # Blue color

        # RAG Configuration
        embedding_model=embedding_model,
        chunk_size=DEFAULT_CHUNK_SIZE,         # 1500 chars
        chunk_overlap=DEFAULT_CHUNK_OVERLAP,   # 300 chars overlap

        # Status flags
        is_active=True,
        is_public=True,

        # Ownership and timestamps
        created_by=created_by,
        created_at=datetime.now(),

        # Source tracking (for crawler-created collections)
        source_type='crawler',
        source_url=urls[0] if urls else None,
        crawl_job_id=job_id
    )

    db.session.add(collection)
    db.session.flush()  # Get ID without committing (caller controls transaction)

    logger.info(
        f"[CrawlerCollection] Created collection '{display_name}' "
        f"(internal: {internal_name}, ID: {collection.id})"
    )

    return collection


# =============================================================================
# COLLECTION UPDATES
# =============================================================================

def update_collection_for_crawl(
    collection_id: int,
    job_id: str,
    source_url: Optional[str] = None
) -> None:
    """
    Update an existing collection with crawl job metadata.

    Called when adding crawled content to an existing collection
    (e.g., when re-crawling or extending a collection).

    Args:
        collection_id: ID of the existing collection
        job_id: UUID of the current crawl job
        source_url: Primary URL being crawled (optional)

    Database Effects:
        - Updates crawl_job_id
        - May update source_type to 'mixed' if was 'upload'
        - May set source_url if not already set
        - Commits changes
    """
    from db.db import db
    from db.tables import RAGCollection

    collection = RAGCollection.query.get(collection_id)
    if not collection:
        logger.warning(f"[CrawlerCollection] Collection {collection_id} not found for update")
        return

    # Track the current crawl job
    collection.crawl_job_id = job_id

    # Update source type if this was previously upload-only
    if collection.source_type == 'upload':
        collection.source_type = 'mixed'
        logger.info(f"[CrawlerCollection] Collection {collection_id} source_type changed to 'mixed'")

    # Set source URL if not already set
    if not collection.source_url and source_url:
        collection.source_url = source_url

    db.session.commit()


def update_collection_stats(
    collection_id: int,
    brand_color: Optional[str] = None
) -> None:
    """
    Update collection statistics after crawl completion.

    Recalculates document count from actual links and optionally
    saves the extracted brand color.

    Args:
        collection_id: ID of the collection to update
        brand_color: Hex color extracted from the website (optional)

    Database Effects:
        - Updates document_count from CollectionDocumentLink count
        - May update color if brand_color provided and no color set
        - Commits changes
    """
    from db.db import db
    from db.tables import RAGCollection, CollectionDocumentLink

    try:
        collection = RAGCollection.query.get(collection_id)
        if not collection:
            logger.warning(f"[CrawlerCollection] Collection {collection_id} not found for stats update")
            return

        # Count actual document links (more accurate than document_count field)
        link_count = CollectionDocumentLink.query.filter_by(
            collection_id=collection_id
        ).count()
        collection.document_count = link_count

        # Save brand color if extracted and collection has no color yet
        if brand_color and not collection.color:
            collection.color = brand_color
            logger.info(f"[CrawlerCollection] Saved brand color {brand_color} to collection {collection_id}")

        db.session.commit()

        logger.debug(f"[CrawlerCollection] Updated collection {collection_id} stats: {link_count} documents")

    except Exception as e:
        logger.warning(f"[CrawlerCollection] Could not update collection stats: {e}")
