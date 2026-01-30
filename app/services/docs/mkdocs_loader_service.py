"""
MkDocs Loader Service

Loads MkDocs documentation files and syncs them to a RAG collection
for the LLARS chatbot. Each document is chunked by Markdown headings
and includes the documentation URL as metadata.
"""

import hashlib
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from db.database import db
from db.models.rag import (
    RAGCollection,
    RAGDocument,
    RAGDocumentChunk,
    RAGProcessingQueue,
    CollectionDocumentLink,
)

logger = logging.getLogger(__name__)

# Configuration
DOCS_COLLECTION_NAME = 'llars-documentation'
DOCS_COLLECTION_DISPLAY_NAME = 'LLARS-Dokumentation'
DOCS_COLLECTION_DESCRIPTION = (
    'Automatisch synchronisierte LLARS-Dokumentation aus MkDocs. '
    'Enthält Anleitungen, API-Referenz und Projektdokumentation.'
)
DOCS_COLLECTION_ICON = '📚'
DOCS_COLLECTION_COLOR = '#b0ca97'

# Path to docs directory (relative to app root)
MKDOCS_ROOT = '/app/docs'
DOCS_DIR = '/app/docs/docs'
MKDOCS_YML = '/app/docs/mkdocs.yml'

# Files/directories to exclude from indexing
EXCLUDE_PATTERNS = [
    'archive/',  # Archived/outdated documentation
    'projekte/ReAct/',  # Exercise materials, not documentation
    'projekte/anonymize/',  # Internal project files
    'projekte/Diss/',  # Dissertation materials
    'projekte/markdown collab/',  # Space in name causes issues
]


class MkDocsLoaderService:
    """
    Service for loading MkDocs documentation into RAG collections.

    Features:
    - Parses mkdocs.yml for navigation structure
    - Chunks Markdown by headings (## / ###) for semantic coherence
    - Computes MD5 hashes to only update changed files
    - Stores documentation URLs as metadata for citation
    """

    def __init__(self, docs_dir: str = DOCS_DIR, mkdocs_yml: str = MKDOCS_YML):
        """
        Initialize the MkDocs loader.

        Args:
            docs_dir: Path to the MkDocs docs directory
            mkdocs_yml: Path to mkdocs.yml configuration
        """
        self.docs_dir = Path(docs_dir)
        self.mkdocs_yml_path = Path(mkdocs_yml)
        self.project_url = os.environ.get('PROJECT_URL', 'http://localhost:55080')

    def get_doc_url(self, relative_path: str) -> str:
        """
        Convert a file path to its MkDocs URL.

        MkDocs with use_directory_urls: true converts:
        - index.md -> /docs/
        - getting-started/overview.md -> /docs/getting-started/overview/

        Args:
            relative_path: Path relative to docs/docs/ (e.g., 'getting-started/overview.md')

        Returns:
            Full URL to the documentation page
        """
        # Remove .md extension
        path_without_ext = relative_path.replace('.md', '')

        # Handle index.md specially
        if path_without_ext == 'index':
            return f"{self.project_url}/docs/"

        # Handle nested index.md
        if path_without_ext.endswith('/index'):
            path_without_ext = path_without_ext[:-6]  # Remove '/index'

        return f"{self.project_url}/docs/{path_without_ext}/"

    def get_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file content."""
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    def should_exclude(self, relative_path: str) -> bool:
        """Check if a file should be excluded from indexing."""
        for pattern in EXCLUDE_PATTERNS:
            if pattern in relative_path:
                return True
        return False

    def parse_mkdocs_nav(self) -> Dict[str, str]:
        """
        Parse mkdocs.yml to get navigation structure.

        Returns:
            Dict mapping file paths to their navigation titles
        """
        nav_titles = {}

        if not self.mkdocs_yml_path.exists():
            logger.warning(f"[MkDocsLoader] mkdocs.yml not found at {self.mkdocs_yml_path}")
            return nav_titles

        try:
            with open(self.mkdocs_yml_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            nav = config.get('nav', [])
            self._extract_nav_titles(nav, nav_titles)
        except Exception as e:
            logger.error(f"[MkDocsLoader] Error parsing mkdocs.yml: {e}")

        return nav_titles

    def _extract_nav_titles(self, nav_items: List, titles: Dict[str, str], prefix: str = '') -> None:
        """Recursively extract navigation titles from mkdocs.yml nav structure."""
        for item in nav_items:
            if isinstance(item, dict):
                for title, value in item.items():
                    if isinstance(value, str):
                        # Direct file reference
                        titles[value] = f"{prefix}{title}" if prefix else title
                    elif isinstance(value, list):
                        # Nested navigation
                        new_prefix = f"{prefix}{title} > " if prefix else f"{title} > "
                        self._extract_nav_titles(value, titles, new_prefix)

    def chunk_markdown(self, content: str, source_url: str, title: str) -> List[Dict]:
        """
        Split Markdown content into chunks based on headings.

        Uses ## and ### headings as chunk boundaries for semantic coherence.
        Each chunk includes metadata for RAG retrieval.

        Args:
            content: Full Markdown content
            source_url: URL to the documentation page
            title: Document title from navigation

        Returns:
            List of chunk dicts with content and metadata
        """
        chunks = []

        # Split by ## headings (H2)
        h2_pattern = re.compile(r'^(##\s+.+)$', re.MULTILINE)
        sections = h2_pattern.split(content)

        # First section is content before any H2
        intro_content = sections[0].strip() if sections else ''
        if intro_content:
            chunks.append({
                'content': intro_content,
                'section_title': title,
                'source_url': source_url,
                'chunk_type': 'intro'
            })

        # Process H2 sections
        for i in range(1, len(sections), 2):
            if i + 1 >= len(sections):
                break

            h2_heading = sections[i].strip()
            section_content = sections[i + 1].strip()

            if not section_content:
                continue

            # Extract heading text
            section_title = h2_heading.replace('## ', '').strip()
            full_section_title = f"{title} > {section_title}"

            # Further split large sections by ### (H3) if content is long
            if len(section_content) > 2000:
                h3_chunks = self._split_by_h3(
                    h2_heading + '\n\n' + section_content,
                    source_url,
                    title,
                    section_title
                )
                chunks.extend(h3_chunks)
            else:
                full_content = f"{h2_heading}\n\n{section_content}"
                chunks.append({
                    'content': full_content,
                    'section_title': full_section_title,
                    'source_url': source_url,
                    'chunk_type': 'section'
                })

        # If no H2 sections found, create single chunk from whole content
        if not chunks:
            chunks.append({
                'content': content,
                'section_title': title,
                'source_url': source_url,
                'chunk_type': 'full'
            })

        return chunks

    def _split_by_h3(
        self,
        content: str,
        source_url: str,
        doc_title: str,
        section_title: str
    ) -> List[Dict]:
        """Split content further by H3 headings."""
        chunks = []
        h3_pattern = re.compile(r'^(###\s+.+)$', re.MULTILINE)
        sections = h3_pattern.split(content)

        # First part is H2 heading and intro
        intro = sections[0].strip()
        if intro:
            chunks.append({
                'content': intro,
                'section_title': f"{doc_title} > {section_title}",
                'source_url': source_url,
                'chunk_type': 'section'
            })

        # Process H3 sections
        for i in range(1, len(sections), 2):
            if i + 1 >= len(sections):
                break

            h3_heading = sections[i].strip()
            subsection_content = sections[i + 1].strip()

            if not subsection_content:
                continue

            subsection_title = h3_heading.replace('### ', '').strip()
            full_content = f"{h3_heading}\n\n{subsection_content}"

            chunks.append({
                'content': full_content,
                'section_title': f"{doc_title} > {section_title} > {subsection_title}",
                'source_url': source_url,
                'chunk_type': 'subsection'
            })

        return chunks if chunks else [{
            'content': content,
            'section_title': f"{doc_title} > {section_title}",
            'source_url': source_url,
            'chunk_type': 'section'
        }]

    def get_or_create_collection(self) -> RAGCollection:
        """Get or create the LLARS documentation RAG collection."""
        collection = RAGCollection.query.filter_by(name=DOCS_COLLECTION_NAME).first()

        if not collection:
            # Use VDR-2B (via LiteLLM/KIZ) as preferred model for best quality
            # The embedding worker will fall back to MiniLM if VDR-2B is unavailable
            preferred_embedding_model = 'llamaindex/vdr-2b-multi-v1'

            collection = RAGCollection(
                name=DOCS_COLLECTION_NAME,
                display_name=DOCS_COLLECTION_DISPLAY_NAME,
                description=DOCS_COLLECTION_DESCRIPTION,
                icon=DOCS_COLLECTION_ICON,
                color=DOCS_COLLECTION_COLOR,
                embedding_model=preferred_embedding_model,
                chunk_size=1500,
                chunk_overlap=300,
                retrieval_k=8,
                is_active=True,
                is_public=True,
                source_type='upload',
                created_by='system',
                created_at=datetime.now()
            )
            db.session.add(collection)
            db.session.commit()
            logger.info(
                f"[MkDocsLoader] Created documentation collection: {DOCS_COLLECTION_NAME} "
                f"(embedding model: {preferred_embedding_model})"
            )

        return collection

    def load_documentation(self) -> Tuple[int, int, int, int]:
        """
        Load all MkDocs documentation files into the collection.

        Returns:
            Tuple of (created_count, updated_count, skipped_count, deleted_count)
        """
        if not self.docs_dir.exists():
            logger.warning(f"[MkDocsLoader] Docs directory not found: {self.docs_dir}")
            return 0, 0, 0, 0

        collection = self.get_or_create_collection()
        nav_titles = self.parse_mkdocs_nav()

        created = 0
        updated = 0
        skipped = 0

        # Find all .md files
        md_files = list(self.docs_dir.rglob('*.md'))
        logger.info(f"[MkDocsLoader] Found {len(md_files)} markdown files")

        # Track all current source URLs for deletion detection
        current_source_urls = set()

        for md_file in md_files:
            relative_path = str(md_file.relative_to(self.docs_dir))

            # Skip excluded paths
            if self.should_exclude(relative_path):
                logger.debug(f"[MkDocsLoader] Skipping excluded: {relative_path}")
                skipped += 1
                continue

            # Track this URL as current
            source_url = self.get_doc_url(relative_path)
            current_source_urls.add(source_url)

            try:
                result = self._process_markdown_file(
                    md_file, relative_path, collection, nav_titles
                )
                if result == 'created':
                    created += 1
                elif result == 'updated':
                    updated += 1
                else:
                    skipped += 1
            except Exception as e:
                logger.error(f"[MkDocsLoader] Error processing {relative_path}: {e}")
                skipped += 1

        # Remove documents that no longer exist in the filesystem
        deleted = self._remove_deleted_documents(collection, current_source_urls)

        # Update collection statistics
        collection.document_count = RAGDocument.query.filter_by(collection_id=collection.id).count()
        collection.total_chunks = RAGDocumentChunk.query.join(RAGDocument).filter(
            RAGDocument.collection_id == collection.id
        ).count()
        collection.updated_at = datetime.now()
        db.session.commit()

        logger.info(
            f"[MkDocsLoader] Sync complete: {created} created, {updated} updated, "
            f"{skipped} skipped, {deleted} deleted"
        )
        return created, updated, skipped, deleted

    def _process_markdown_file(
        self,
        file_path: Path,
        relative_path: str,
        collection: RAGCollection,
        nav_titles: Dict[str, str]
    ) -> str:
        """
        Process a single markdown file.

        Returns:
            'created', 'updated', or 'skipped'
        """
        # Calculate file hash
        file_hash = self.get_file_hash(file_path)

        # Get document URL and title
        source_url = self.get_doc_url(relative_path)
        nav_title = nav_titles.get(relative_path, '')

        # Extract title from file if not in nav
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if not nav_title:
            # Try to get title from first H1
            h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if h1_match:
                nav_title = h1_match.group(1).strip()
            else:
                # Use filename as title
                nav_title = relative_path.replace('.md', '').replace('/', ' > ').replace('-', ' ').title()

        # Check if document already exists (by source_url)
        existing_doc = RAGDocument.query.filter_by(source_url=source_url).first()

        if existing_doc:
            # Check if content changed
            if existing_doc.file_hash == file_hash:
                return 'skipped'

            # Update existing document
            return self._update_document(existing_doc, content, file_hash, nav_title, source_url)
        else:
            # Create new document
            return self._create_document(
                file_path, relative_path, content, file_hash,
                nav_title, source_url, collection
            )

    def _create_document(
        self,
        file_path: Path,
        relative_path: str,
        content: str,
        file_hash: str,
        title: str,
        source_url: str,
        collection: RAGCollection
    ) -> str:
        """Create a new document from markdown file."""
        file_size = file_path.stat().st_size

        # Create document entry
        doc = RAGDocument(
            filename=relative_path.replace('/', '_'),
            original_filename=file_path.name,
            file_path=str(file_path),
            file_size_bytes=file_size,
            mime_type='text/markdown',
            file_hash=file_hash,
            title=title,
            description=f"LLARS-Dokumentation: {title}",
            language='de',
            status='pending',
            collection_id=collection.id,
            is_public=True,
            uploaded_by='system',
            source_url=source_url,
            uploaded_at=datetime.now()
        )
        db.session.add(doc)
        db.session.flush()

        # Create collection link
        link = CollectionDocumentLink(
            collection_id=collection.id,
            document_id=doc.id,
            link_type='new',
            source_url=source_url,
            linked_at=datetime.now(),
            linked_by='system'
        )
        db.session.add(link)

        # Create chunks
        chunks = self.chunk_markdown(content, source_url, title)
        self._create_chunks(doc, chunks)

        # Add to processing queue for embedding
        queue_entry = RAGProcessingQueue(
            document_id=doc.id,
            priority=3,  # Lower priority than user uploads
            status='queued',
            created_at=datetime.now()
        )
        db.session.add(queue_entry)

        db.session.commit()
        logger.info(f"[MkDocsLoader] Created: {title} ({len(chunks)} chunks)")
        return 'created'

    def _update_document(
        self,
        doc: RAGDocument,
        content: str,
        file_hash: str,
        title: str,
        source_url: str
    ) -> str:
        """Update an existing document with new content."""
        # Delete old chunks
        RAGDocumentChunk.query.filter_by(document_id=doc.id).delete()

        # Update document
        doc.file_hash = file_hash
        doc.title = title
        doc.description = f"LLARS-Dokumentation: {title}"
        doc.status = 'pending'
        doc.updated_at = datetime.now()

        # Create new chunks
        chunks = self.chunk_markdown(content, source_url, title)
        self._create_chunks(doc, chunks)

        # Add to processing queue for re-embedding
        existing_queue = RAGProcessingQueue.query.filter_by(
            document_id=doc.id,
            status='queued'
        ).first()
        if not existing_queue:
            queue_entry = RAGProcessingQueue(
                document_id=doc.id,
                priority=3,
                status='queued',
                created_at=datetime.now()
            )
            db.session.add(queue_entry)

        db.session.commit()
        logger.info(f"[MkDocsLoader] Updated: {title} ({len(chunks)} chunks)")
        return 'updated'

    def _create_chunks(self, doc: RAGDocument, chunks: List[Dict]) -> None:
        """Create chunk entries for a document."""
        for i, chunk_data in enumerate(chunks):
            # Include source URL in chunk content for better retrieval context
            chunk_content = chunk_data['content']

            # Add metadata hint at the end of content
            if chunk_data.get('source_url'):
                chunk_content += f"\n\n[Quelle: {chunk_data['source_url']}]"

            chunk = RAGDocumentChunk(
                document_id=doc.id,
                chunk_index=i,
                content=chunk_content,
                content_hash=hashlib.md5(chunk_content.encode()).hexdigest(),
                embedding_status='pending',
                created_at=datetime.now()
            )
            db.session.add(chunk)

        doc.chunk_count = len(chunks)

    def _remove_deleted_documents(
        self,
        collection: RAGCollection,
        current_source_urls: set
    ) -> int:
        """
        Remove documents from the collection that no longer exist in the filesystem.

        Args:
            collection: The RAG collection
            current_source_urls: Set of source URLs that currently exist

        Returns:
            Number of deleted documents
        """
        # Get all documents in this collection with source URLs starting with our docs base
        docs_url_prefix = f"{self.project_url}/docs/"
        existing_docs = RAGDocument.query.filter(
            RAGDocument.collection_id == collection.id,
            RAGDocument.source_url.like(f"{docs_url_prefix}%")
        ).all()

        deleted = 0
        for doc in existing_docs:
            if doc.source_url not in current_source_urls:
                logger.info(f"[MkDocsLoader] Removing deleted document: {doc.title} ({doc.source_url})")

                # Delete chunks first (foreign key constraint)
                RAGDocumentChunk.query.filter_by(document_id=doc.id).delete()

                # Delete collection links
                CollectionDocumentLink.query.filter_by(document_id=doc.id).delete()

                # Delete processing queue entries
                RAGProcessingQueue.query.filter_by(document_id=doc.id).delete()

                # Delete the document
                db.session.delete(doc)
                deleted += 1

        if deleted > 0:
            db.session.commit()

        return deleted

    def sync_llars_documentation(self) -> Dict:
        """
        Main entry point for syncing LLARS documentation.

        Called by startup task to ensure documentation is up-to-date.

        Returns:
            Dict with sync statistics
        """
        logger.info("[MkDocsLoader] Starting LLARS documentation sync...")

        try:
            created, updated, skipped, deleted = self.load_documentation()

            # Ensure the default chatbot has this collection
            self._assign_to_default_chatbot()

            return {
                'success': True,
                'created': created,
                'updated': updated,
                'skipped': skipped,
                'deleted': deleted,
                'message': (
                    f"Synced LLARS documentation: {created} created, {updated} updated, "
                    f"{skipped} skipped, {deleted} deleted"
                )
            }
        except Exception as e:
            logger.error(f"[MkDocsLoader] Sync failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Documentation sync failed: {e}"
            }

    def _assign_to_default_chatbot(self) -> None:
        """
        Ensure the LLARS documentation collection is assigned to the default chatbot.
        """
        from db.tables import Chatbot, ChatbotCollection

        collection = RAGCollection.query.filter_by(name=DOCS_COLLECTION_NAME).first()
        if not collection:
            return

        # Find default LLARS chatbot
        chatbot = Chatbot.query.filter_by(name='standard_admin').first()
        if not chatbot:
            logger.warning("[MkDocsLoader] Default chatbot 'standard_admin' not found")
            return

        # Check if already assigned
        existing = ChatbotCollection.query.filter_by(
            chatbot_id=chatbot.id,
            collection_id=collection.id
        ).first()

        if not existing:
            assignment = ChatbotCollection(
                chatbot_id=chatbot.id,
                collection_id=collection.id,
                priority=1,  # Higher priority than general collection
                weight=1.5,  # Boost documentation results
                is_primary=False,
                assigned_by='system',
                assigned_at=datetime.now()
            )
            db.session.add(assignment)
            db.session.commit()
            logger.info(
                f"[MkDocsLoader] Assigned documentation collection to chatbot '{chatbot.display_name}'"
            )
