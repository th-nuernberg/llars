"""
Tests for LinkPreviewService - URL extraction, OG metadata, and caching.

Covers:
- URL extraction from text
- SSRF protection (_is_safe_url)
- Open Graph metadata fetching
- URL hashing
- Cache lookup and expiration
- Fetch and cache preview workflow
- Message link processing
"""

import hashlib
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


class TestExtractUrls:
    """Test URL extraction from text."""

    def test_LINK_001_extracts_http_urls(self):
        """LINK_001: Extracts http:// URLs from text."""
        from services.link_preview_service import extract_urls

        result = extract_urls("Visit http://example.com for more info")
        assert result == ["http://example.com"]

    def test_LINK_002_extracts_https_urls(self):
        """LINK_002: Extracts https:// URLs from text."""
        from services.link_preview_service import extract_urls

        result = extract_urls("Check https://example.com/page")
        assert result == ["https://example.com/page"]

    def test_LINK_003_extracts_multiple_urls(self):
        """LINK_003: Extracts multiple unique URLs."""
        from services.link_preview_service import extract_urls

        text = "See https://a.com and https://b.com or https://c.com"
        result = extract_urls(text)
        assert len(result) == 3

    def test_LINK_004_limits_to_max_urls(self):
        """LINK_004: Limits extraction to MAX_URLS_PER_MESSAGE."""
        from services.link_preview_service import extract_urls, MAX_URLS_PER_MESSAGE

        text = " ".join(f"https://site{i}.com" for i in range(10))
        result = extract_urls(text)
        assert len(result) <= MAX_URLS_PER_MESSAGE

    def test_LINK_005_strips_trailing_punctuation(self):
        """LINK_005: Strips trailing punctuation from URLs."""
        from services.link_preview_service import extract_urls

        result = extract_urls("Visit https://example.com.")
        assert result == ["https://example.com"]

    def test_LINK_006_deduplicates_urls(self):
        """LINK_006: Returns only unique URLs."""
        from services.link_preview_service import extract_urls

        text = "https://dup.com and https://dup.com again"
        result = extract_urls(text)
        assert len(result) == 1

    def test_LINK_007_empty_text_returns_empty(self):
        """LINK_007: Empty or None text returns empty list."""
        from services.link_preview_service import extract_urls

        assert extract_urls("") == []
        assert extract_urls(None) == []

    def test_LINK_008_no_urls_returns_empty(self):
        """LINK_008: Text without URLs returns empty list."""
        from services.link_preview_service import extract_urls

        assert extract_urls("No URLs here at all") == []


class TestIsSafeUrl:
    """Test SSRF protection."""

    def test_LINK_010_rejects_localhost(self):
        """LINK_010: Rejects localhost URLs."""
        from services.link_preview_service import _is_safe_url

        assert _is_safe_url("http://localhost/admin") is False
        assert _is_safe_url("http://127.0.0.1/admin") is False
        assert _is_safe_url("http://0.0.0.0/admin") is False

    def test_LINK_011_rejects_non_http_schemes(self):
        """LINK_011: Rejects non-http schemes."""
        from services.link_preview_service import _is_safe_url

        assert _is_safe_url("ftp://example.com") is False
        assert _is_safe_url("file:///etc/passwd") is False

    def test_LINK_012_rejects_private_ips(self):
        """LINK_012: Rejects private IP addresses."""
        from services.link_preview_service import _is_safe_url

        with patch('services.link_preview_service.socket.getaddrinfo') as mock_gai:
            mock_gai.return_value = [
                (2, 1, 6, '', ('192.168.1.1', 80)),
            ]
            assert _is_safe_url("http://internal.company.com") is False

    @patch('services.link_preview_service.socket.getaddrinfo')
    def test_LINK_013_accepts_public_urls(self, mock_gai):
        """LINK_013: Accepts URLs resolving to public IPs."""
        from services.link_preview_service import _is_safe_url

        mock_gai.return_value = [
            (2, 1, 6, '', ('93.184.216.34', 80)),  # example.com
        ]

        assert _is_safe_url("https://example.com") is True

    def test_LINK_014_rejects_no_hostname(self):
        """LINK_014: Rejects URLs without hostname."""
        from services.link_preview_service import _is_safe_url

        assert _is_safe_url("http://") is False

    @patch('services.link_preview_service.socket.getaddrinfo')
    def test_LINK_015_rejects_dns_failure(self, mock_gai):
        """LINK_015: Rejects URLs that fail DNS resolution."""
        from services.link_preview_service import _is_safe_url
        import socket

        mock_gai.side_effect = socket.gaierror("DNS lookup failed")

        assert _is_safe_url("https://nonexistent.invalid") is False


class TestFetchOgMetadata:
    """Test Open Graph metadata fetching."""

    @patch('services.link_preview_service.requests.get')
    def test_LINK_020_extracts_og_metadata(self, mock_get):
        """LINK_020: Extracts OG title, description, image."""
        from services.link_preview_service import _fetch_og_metadata

        html = """
        <html><head>
        <meta property="og:title" content="Test Page">
        <meta property="og:description" content="A test description">
        <meta property="og:image" content="https://example.com/image.jpg">
        <meta property="og:site_name" content="TestSite">
        <link rel="icon" href="/favicon.ico">
        </head><body></body></html>
        """

        mock_resp = MagicMock()
        mock_resp.headers = {'Content-Type': 'text/html; charset=utf-8'}
        mock_resp.raw.read.return_value = html.encode('utf-8')
        mock_get.return_value = mock_resp

        result = _fetch_og_metadata("https://example.com")

        assert result is not None
        assert result['title'] == 'Test Page'
        assert result['description'] == 'A test description'
        assert result['image_url'] == 'https://example.com/image.jpg'
        assert result['site_name'] == 'TestSite'
        assert result['favicon_url'] == 'https://example.com/favicon.ico'

    @patch('services.link_preview_service.requests.get')
    def test_LINK_021_falls_back_to_title_tag(self, mock_get):
        """LINK_021: Falls back to <title> when no OG title."""
        from services.link_preview_service import _fetch_og_metadata

        html = "<html><head><title>Fallback Title</title></head><body></body></html>"

        mock_resp = MagicMock()
        mock_resp.headers = {'Content-Type': 'text/html'}
        mock_resp.raw.read.return_value = html.encode('utf-8')
        mock_get.return_value = mock_resp

        result = _fetch_og_metadata("https://example.com")

        assert result is not None
        assert result['title'] == 'Fallback Title'

    @patch('services.link_preview_service.requests.get')
    def test_LINK_022_returns_none_for_non_html(self, mock_get):
        """LINK_022: Returns None for non-HTML responses."""
        from services.link_preview_service import _fetch_og_metadata

        mock_resp = MagicMock()
        mock_resp.headers = {'Content-Type': 'application/json'}
        mock_get.return_value = mock_resp

        result = _fetch_og_metadata("https://api.example.com/data")
        assert result is None

    @patch('services.link_preview_service.requests.get')
    def test_LINK_023_returns_none_on_request_error(self, mock_get):
        """LINK_023: Returns None on request exception."""
        from services.link_preview_service import _fetch_og_metadata
        import requests as req_lib

        mock_get.side_effect = req_lib.RequestException("Timeout")

        result = _fetch_og_metadata("https://timeout.com")
        assert result is None

    @patch('services.link_preview_service.requests.get')
    def test_LINK_024_returns_none_no_metadata(self, mock_get):
        """LINK_024: Returns None when no title or description found."""
        from services.link_preview_service import _fetch_og_metadata

        html = "<html><head></head><body>Just text</body></html>"

        mock_resp = MagicMock()
        mock_resp.headers = {'Content-Type': 'text/html'}
        mock_resp.raw.read.return_value = html.encode('utf-8')
        mock_get.return_value = mock_resp

        result = _fetch_og_metadata("https://bare.com")
        assert result is None

    @patch('services.link_preview_service.requests.get')
    def test_LINK_025_relative_image_made_absolute(self, mock_get):
        """LINK_025: Relative image URLs are made absolute."""
        from services.link_preview_service import _fetch_og_metadata

        html = """
        <html><head>
        <meta property="og:title" content="Test">
        <meta property="og:image" content="/images/photo.jpg">
        </head></html>
        """

        mock_resp = MagicMock()
        mock_resp.headers = {'Content-Type': 'text/html'}
        mock_resp.raw.read.return_value = html.encode('utf-8')
        mock_get.return_value = mock_resp

        result = _fetch_og_metadata("https://example.com/page")

        assert result['image_url'] == 'https://example.com/images/photo.jpg'


class TestUrlHash:
    """Test URL hashing."""

    def test_LINK_030_url_hash_is_sha256(self):
        """LINK_030: URL hash is SHA-256 hex digest."""
        from services.link_preview_service import _url_hash

        url = "https://example.com"
        expected = hashlib.sha256(url.encode('utf-8')).hexdigest()

        assert _url_hash(url) == expected

    def test_LINK_031_different_urls_different_hashes(self):
        """LINK_031: Different URLs produce different hashes."""
        from services.link_preview_service import _url_hash

        assert _url_hash("https://a.com") != _url_hash("https://b.com")


class TestFetchAndCachePreview:
    """Test fetch_and_cache_preview workflow."""

    @patch('services.link_preview_service._is_safe_url', return_value=True)
    @patch('services.link_preview_service._fetch_og_metadata')
    @patch('services.link_preview_service.MessagingLinkPreview')
    @patch('services.link_preview_service.db')
    def test_LINK_040_creates_cache_entry(self, mock_db, mock_mlp, mock_fetch, mock_safe):
        """LINK_040: Creates new cache entry on first fetch."""
        from services.link_preview_service import fetch_and_cache_preview

        mock_mlp.query.filter_by.return_value.first.return_value = None
        mock_fetch.return_value = {
            'title': 'Test',
            'description': 'Desc',
            'image_url': None,
            'site_name': None,
            'favicon_url': None,
        }

        result = fetch_and_cache_preview("https://example.com")

        assert result is not None
        assert result['title'] == 'Test'
        mock_db.session.add.assert_called_once()
        mock_db.session.commit.assert_called_once()

    @patch('services.link_preview_service.MessagingLinkPreview')
    @patch('services.link_preview_service.db')
    def test_LINK_041_returns_cached_entry(self, mock_db, mock_mlp):
        """LINK_041: Returns cached entry within TTL."""
        from services.link_preview_service import fetch_and_cache_preview

        cached = MagicMock()
        cached.fetched_at = datetime.utcnow() - timedelta(hours=1)
        cached.fetch_error = None
        cached.url = "https://example.com"
        cached.title = "Cached Title"
        cached.description = "Cached Desc"
        cached.image_url = None
        cached.site_name = None
        cached.favicon_url = None
        mock_mlp.query.filter_by.return_value.first.return_value = cached

        result = fetch_and_cache_preview("https://example.com")

        assert result['title'] == 'Cached Title'

    @patch('services.link_preview_service.MessagingLinkPreview')
    @patch('services.link_preview_service.db')
    def test_LINK_042_returns_none_for_cached_error(self, mock_db, mock_mlp):
        """LINK_042: Returns None for cached fetch error within TTL."""
        from services.link_preview_service import fetch_and_cache_preview

        cached = MagicMock()
        cached.fetched_at = datetime.utcnow() - timedelta(hours=1)
        cached.fetch_error = "No metadata found"
        mock_mlp.query.filter_by.return_value.first.return_value = cached

        result = fetch_and_cache_preview("https://nodata.com")
        assert result is None

    @patch('services.link_preview_service._is_safe_url', return_value=False)
    @patch('services.link_preview_service.MessagingLinkPreview')
    @patch('services.link_preview_service.db')
    def test_LINK_043_returns_none_for_unsafe_url(self, mock_db, mock_mlp, mock_safe):
        """LINK_043: Returns None for unsafe URLs."""
        from services.link_preview_service import fetch_and_cache_preview

        mock_mlp.query.filter_by.return_value.first.return_value = None

        result = fetch_and_cache_preview("http://localhost/admin")
        assert result is None


class TestProcessMessageLinks:
    """Test message link processing."""

    @patch('services.link_preview_service.fetch_and_cache_preview')
    @patch('services.link_preview_service.MessagingMessage')
    @patch('services.link_preview_service.db')
    def test_LINK_050_processes_message_with_urls(self, mock_db, mock_mm, mock_fetch):
        """LINK_050: Extracts URLs and fetches previews for a message."""
        from services.link_preview_service import process_message_links

        mock_msg = MagicMock()
        mock_msg.content = "Check https://example.com for info"
        mock_msg.is_deleted = False
        mock_msg.is_encrypted = False
        mock_mm.query.get.return_value = mock_msg

        mock_fetch.return_value = {'title': 'Example', 'url': 'https://example.com',
                                   'description': 'Desc', 'image_url': None,
                                   'site_name': None, 'favicon_url': None}

        result = process_message_links(message_id=1)

        assert result is not None
        assert len(result) == 1
        assert result[0]['title'] == 'Example'

    @patch('services.link_preview_service.MessagingMessage')
    def test_LINK_051_returns_none_for_missing_message(self, mock_mm):
        """LINK_051: Returns None when message not found."""
        from services.link_preview_service import process_message_links

        mock_mm.query.get.return_value = None

        assert process_message_links(message_id=999) is None

    @patch('services.link_preview_service.MessagingMessage')
    def test_LINK_052_returns_none_for_deleted_message(self, mock_mm):
        """LINK_052: Returns None for deleted messages."""
        from services.link_preview_service import process_message_links

        mock_msg = MagicMock()
        mock_msg.content = "https://example.com"
        mock_msg.is_deleted = True
        mock_msg.is_encrypted = False
        mock_mm.query.get.return_value = mock_msg

        assert process_message_links(message_id=1) is None

    @patch('services.link_preview_service.MessagingMessage')
    def test_LINK_053_returns_none_for_encrypted_message(self, mock_mm):
        """LINK_053: Returns None for encrypted messages."""
        from services.link_preview_service import process_message_links

        mock_msg = MagicMock()
        mock_msg.content = "https://example.com"
        mock_msg.is_deleted = False
        mock_msg.is_encrypted = True
        mock_mm.query.get.return_value = mock_msg

        assert process_message_links(message_id=1) is None

    @patch('services.link_preview_service.MessagingMessage')
    def test_LINK_054_returns_none_for_no_urls(self, mock_mm):
        """LINK_054: Returns None when message has no URLs."""
        from services.link_preview_service import process_message_links

        mock_msg = MagicMock()
        mock_msg.content = "No URLs here"
        mock_msg.is_deleted = False
        mock_msg.is_encrypted = False
        mock_mm.query.get.return_value = mock_msg

        assert process_message_links(message_id=1) is None
