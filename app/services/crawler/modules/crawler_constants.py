# crawler_constants.py
"""
Constants and utility functions for the crawler service.

This module provides:
- Configuration constants for crawling (paths, chunk sizes, icons)
- Text processing utilities (slugify, filename generation)
- Content validation for quality filtering

Used by: crawler_service.py, crawler_document.py, crawler_collection.py
"""

from __future__ import annotations

import re
import uuid
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# =============================================================================
# CRAWLER CONFIGURATION CONSTANTS
# =============================================================================

# Path where crawled documents are stored as markdown files
RAG_DOCS_PATH = '/app/data/rag/crawls'

# Default chunking parameters for RAG processing
DEFAULT_CHUNK_SIZE = 1500      # Characters per chunk
DEFAULT_CHUNK_OVERLAP = 300    # Overlap between chunks for context preservation

# Default UI display settings for crawl collections
DEFAULT_ICON = 'mdi-web'       # Material Design Icon for web content
DEFAULT_COLOR = '#2196F3'      # Blue color for web-crawled collections

# Minimum content length to consider a page worth indexing
# Pages with less content are likely navigation-only or error pages
MIN_CONTENT_LENGTH = 100


# =============================================================================
# TEXT PROCESSING UTILITIES
# =============================================================================

def slugify(value: str, max_length: int = 200) -> str:
    """
    Create a URL-safe slug from any string.

    Converts text to lowercase, replaces non-alphanumeric characters with
    underscores, and trims to max length. Used for creating safe internal
    collection names and filenames.

    Args:
        value: Input string to slugify
        max_length: Maximum length of resulting slug (default: 200)

    Returns:
        Safe slug string, or 'site' if input is empty

    Examples:
        >>> slugify("Hello World!")
        'hello_world'
        >>> slugify("www.example.com/about-us")
        'www_example_com_about_us'
    """
    value = (value or '').strip().lower()
    # Replace any non-alphanumeric character with underscore
    value = re.sub(r'[^a-z0-9]+', '_', value)
    # Remove leading/trailing underscores
    value = value.strip('_')
    if not value:
        value = 'site'
    return value[:max_length].rstrip('_')


def generate_filename_from_url(url: str, title: str = None) -> str:
    """
    Generate a meaningful, filesystem-safe filename from a URL.

    Creates a readable filename that preserves the URL structure:
    - Domain becomes the prefix
    - Path segments are included
    - File extension is always .md for markdown

    Args:
        url: Full URL to generate filename from
        title: Optional page title (currently unused, reserved for future)

    Returns:
        Filesystem-safe filename with .md extension

    Examples:
        >>> generate_filename_from_url("https://example.com/about/team/")
        'example_com_about_team.md'
        >>> generate_filename_from_url("https://www.test.org/")
        'test_org_home.md'
    """
    try:
        parsed = urlparse(url)

        # Extract and slugify domain (remove www. prefix)
        domain = parsed.netloc.replace('www.', '')
        domain_slug = slugify(domain, max_length=50)

        # Extract and slugify path
        path = parsed.path.strip('/')
        if path:
            path_slug = slugify(path, max_length=100)
        else:
            path_slug = 'home'  # Root URL gets 'home' suffix

        filename = f"{domain_slug}_{path_slug}.md"
        return filename

    except Exception:
        # Fallback to UUID-based filename if URL parsing fails
        return f"page_{uuid.uuid4().hex[:12]}.md"


# =============================================================================
# CONTENT VALIDATION
# =============================================================================

def is_content_worth_indexing(content: str) -> bool:
    """
    Determine if page content is substantial enough to index.

    Filters out low-quality pages that would pollute the RAG index:
    - Empty or near-empty pages
    - Navigation-only pages (menus, footers)
    - Pages with mostly symbols/numbers (e.g., JSON responses)

    Args:
        content: Raw text content of the page

    Returns:
        True if content should be indexed, False otherwise

    Quality Criteria:
        - Minimum 100 characters of actual text
        - At least 30% alphabetic characters (filters out data dumps)
    """
    if not content:
        return False

    # Normalize whitespace and measure actual content
    cleaned = ' '.join(content.split())

    # Check minimum length
    if len(cleaned) < MIN_CONTENT_LENGTH:
        logger.debug(f"Content too short ({len(cleaned)} chars), skipping")
        return False

    # Check alphabetic ratio (filters out JSON, code dumps, etc.)
    alpha_chars = sum(1 for c in cleaned if c.isalpha())
    alpha_ratio = alpha_chars / len(cleaned) if cleaned else 0

    if alpha_ratio < 0.3:  # Less than 30% letters
        logger.debug(f"Content has too few letters ({alpha_chars}/{len(cleaned)}), skipping")
        return False

    return True


# =============================================================================
# COLLECTION NAME GENERATION
# =============================================================================

def build_crawl_collection_name(urls: list, display_name: str, job_id: str) -> str:
    """
    Build a unique, safe internal name for crawl collections.

    Creates a deterministic but unique name based on:
    - Domain of first URL (for readability)
    - Job ID suffix (for uniqueness)

    Args:
        urls: List of URLs being crawled
        display_name: User-provided display name
        job_id: UUID of the crawl job

    Returns:
        Safe internal collection name (e.g., 'crawl_example_com_a1b2c3d4')
    """
    domain = ''
    if urls:
        try:
            domain = urlparse(urls[0]).netloc
        except Exception:
            domain = ''

    base = domain or display_name or 'site'
    slug = slugify(base, max_length=180)
    return f"crawl_{slug}_{job_id[:8]}"


# =============================================================================
# DATABASE UTILITIES
# =============================================================================

def get_default_embedding_model_id() -> str:
    """
    Get the default embedding model ID from the database.

    Queries the llm_models table for the model marked as default
    for the 'embedding' model type.

    Returns:
        Model ID string (e.g., 'llamaindex/vdr-2b-multi-v1')

    Raises:
        ValueError: If no default embedding model is configured
    """
    from db.models.llm_model import LLMModel
    model_id = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_EMBEDDING)
    if not model_id:
        raise ValueError("No default embedding model configured in llm_models")
    return model_id
