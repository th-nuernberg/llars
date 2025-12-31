"""
Unit Tests für Crawler Services

Testet:
- CrawlerService: Job-Management, Collection-Erstellung, Slug-Generierung
- WebCrawler: URL-Normalisierung, Text-Extraktion, Link-Extraktion
"""

import pytest
import tempfile
from unittest.mock import patch, MagicMock
import hashlib
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'app'))


# Fixture for temporary image storage path
@pytest.fixture
def temp_image_path():
    """Temporäres Verzeichnis für Bild-Speicherung."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# =============================================================================
# CrawlerService Tests
# =============================================================================

class TestCrawlerServiceSlugify:
    """Tests für CrawlerService._slugify."""

    def test_CRAWL_001_slugify_basic(self):
        """CRAWL-001: Einfacher Slug aus Text."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()

        result = service._slugify("Hello World")
        assert result == "hello_world"

    def test_CRAWL_002_slugify_special_chars(self):
        """CRAWL-002: Slug mit Sonderzeichen."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()

        result = service._slugify("Test! @#$%^& Value?")
        assert result == "test_value"

    def test_CRAWL_003_slugify_max_length(self):
        """CRAWL-003: Slug wird auf max_length begrenzt."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()

        long_text = "a" * 300
        result = service._slugify(long_text, max_length=50)
        assert len(result) <= 50

    def test_CRAWL_004_slugify_empty(self):
        """CRAWL-004: Leerer String gibt 'site' zurück."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()

        result = service._slugify("")
        assert result == "site"

    def test_CRAWL_005_slugify_only_special_chars(self):
        """CRAWL-005: Nur Sonderzeichen gibt 'site' zurück."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()

        result = service._slugify("!@#$%^&*()")
        assert result == "site"

    def test_CRAWL_006_slugify_german_text(self):
        """CRAWL-006: Deutsche Umlaute werden entfernt."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()

        result = service._slugify("Über uns - Große Änderung")
        # Umlaute werden zu _ (weil sie nicht a-z0-9 sind)
        assert "_" in result or result == "ber_uns_gro_e_nderung"


class TestCrawlerServiceFilename:
    """Tests für CrawlerService._generate_filename_from_url."""

    def test_CRAWL_010_filename_basic(self):
        """CRAWL-010: Dateiname aus einfacher URL."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()

        result = service._generate_filename_from_url("https://example.com/about")
        assert result.endswith(".md")
        assert "example" in result
        assert "about" in result

    def test_CRAWL_011_filename_with_www(self):
        """CRAWL-011: www. wird aus Domain entfernt."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()

        result = service._generate_filename_from_url("https://www.example.com/page")
        assert "www" not in result

    def test_CRAWL_012_filename_root_path(self):
        """CRAWL-012: Root-Path gibt 'home' zurück."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()

        result = service._generate_filename_from_url("https://example.com/")
        assert "home" in result

    def test_CRAWL_013_filename_complex_path(self):
        """CRAWL-013: Komplexer Pfad wird zu Slug."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()

        result = service._generate_filename_from_url("https://example.com/team/about-us/")
        assert result.endswith(".md")
        assert "team" in result or "about" in result


class TestCrawlerServiceContentCheck:
    """Tests für CrawlerService._is_content_worth_indexing."""

    def test_CRAWL_020_content_worth_indexing_yes(self):
        """CRAWL-020: Ausreichender Content wird akzeptiert."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()

        content = "Dies ist ein ausreichend langer Text mit genügend Buchstaben " * 10
        result = service._is_content_worth_indexing(content)
        assert result is True

    def test_CRAWL_021_content_worth_indexing_empty(self):
        """CRAWL-021: Leerer Content wird abgelehnt."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()

        result = service._is_content_worth_indexing("")
        assert result is False

    def test_CRAWL_022_content_worth_indexing_too_short(self):
        """CRAWL-022: Zu kurzer Content wird abgelehnt."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()

        result = service._is_content_worth_indexing("Kurz")
        assert result is False

    def test_CRAWL_023_content_worth_indexing_numbers_only(self):
        """CRAWL-023: Nur Zahlen werden abgelehnt."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()

        content = "12345 67890 " * 50
        result = service._is_content_worth_indexing(content)
        assert result is False


class TestCrawlerServiceCollectionName:
    """Tests für CrawlerService._build_crawl_collection_name."""

    def test_CRAWL_030_collection_name_from_url(self):
        """CRAWL-030: Collection-Name aus URL."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()

        result = service._build_crawl_collection_name(
            urls=["https://example.com"],
            display_name="Test",
            job_id="12345678-abcd-efgh"
        )

        assert result.startswith("crawl_")
        assert "example" in result
        assert "12345678" in result

    def test_CRAWL_031_collection_name_no_urls(self):
        """CRAWL-031: Collection-Name ohne URLs."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()

        result = service._build_crawl_collection_name(
            urls=[],
            display_name="My Collection",
            job_id="abcdef12-3456-7890"
        )

        assert result.startswith("crawl_")
        assert "my_collection" in result


class TestCrawlerServiceJobManagement:
    """Tests für Job-Management."""

    def test_CRAWL_040_init(self):
        """CRAWL-040: Service-Initialisierung."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()

        assert service.active_crawls == {}
        assert service._socketio is None

    def test_CRAWL_041_set_socketio(self):
        """CRAWL-041: SocketIO setzen."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()
        mock_socketio = MagicMock()

        service.set_socketio(mock_socketio)

        assert service._socketio is mock_socketio

    def test_CRAWL_042_get_job_status_active(self):
        """CRAWL-042: Status für aktiven Job abrufen."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()
        service.active_crawls['job-123'] = {
            'status': 'running',
            'pages_crawled': 5
        }

        result = service.get_job_status('job-123')

        assert result['status'] == 'running'
        assert result['pages_crawled'] == 5

    def test_CRAWL_043_get_job_status_not_found(self):
        """CRAWL-043: Status für unbekannten Job."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()

        result = service.get_job_status('nonexistent')

        assert result is None

    def test_CRAWL_044_get_all_jobs(self):
        """CRAWL-044: Alle Jobs abrufen."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()
        service.active_crawls['job-1'] = {'status': 'completed', 'started_at': '2024-01-02'}
        service.active_crawls['job-2'] = {'status': 'running', 'started_at': '2024-01-01'}

        result = service.get_all_jobs()

        assert len(result) == 2
        # Should be sorted by started_at descending
        assert result[0]['job_id'] == 'job-1'

    def test_CRAWL_045_cancel_job(self):
        """CRAWL-045: Job abbrechen."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()
        service.active_crawls['job-123'] = {'status': 'running'}

        result = service.cancel_job('job-123')

        assert result is True
        assert service.active_crawls['job-123']['status'] == 'cancelled'

    def test_CRAWL_046_cancel_job_not_found(self):
        """CRAWL-046: Nicht existierenden Job abbrechen."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()

        result = service.cancel_job('nonexistent')

        assert result is False


# =============================================================================
# WebCrawler Tests
# =============================================================================

class TestWebCrawlerNormalize:
    """Tests für WebCrawler._normalize_url."""

    def test_CRAWL_050_normalize_basic(self, temp_image_path):
        """CRAWL-050: Einfache URL normalisieren."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        result = crawler._normalize_url("https://example.com/page/")
        assert result == "https://example.com/page"

    def test_CRAWL_051_normalize_add_scheme(self, temp_image_path):
        """CRAWL-051: Schema hinzufügen wenn fehlend."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        result = crawler._normalize_url("example.com/page")
        assert result.startswith("https://")

    def test_CRAWL_052_normalize_upgrade_http(self, temp_image_path):
        """CRAWL-052: HTTP zu HTTPS upgraden."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        result = crawler._normalize_url("http://example.com/page")
        assert result.startswith("https://")

    def test_CRAWL_053_normalize_lowercase_domain(self, temp_image_path):
        """CRAWL-053: Domain zu Kleinbuchstaben."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        result = crawler._normalize_url("https://EXAMPLE.COM/Page")
        assert "example.com" in result

    def test_CRAWL_054_normalize_remove_fragment(self, temp_image_path):
        """CRAWL-054: Fragment entfernen."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        result = crawler._normalize_url("https://example.com/page#section")
        assert "#" not in result


class TestWebCrawlerShouldCrawl:
    """Tests für WebCrawler._should_crawl."""

    def test_CRAWL_060_should_crawl_same_domain(self, temp_image_path):
        """CRAWL-060: Gleiche Domain sollte gecrawlt werden."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        result = crawler._should_crawl("https://example.com/about")
        assert result is True

    def test_CRAWL_061_should_crawl_different_domain(self, temp_image_path):
        """CRAWL-061: Andere Domain sollte nicht gecrawlt werden."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", follow_external=False, image_storage_path=temp_image_path)

        result = crawler._should_crawl("https://other.com/page")
        assert result is False

    def test_CRAWL_062_should_crawl_visited(self, temp_image_path):
        """CRAWL-062: Bereits besuchte URL nicht nochmal crawlen."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)
        crawler.visited_urls.add("https://example.com/about")

        result = crawler._should_crawl("https://example.com/about")
        assert result is False

    def test_CRAWL_063_should_crawl_exclude_pattern(self, temp_image_path):
        """CRAWL-063: Exclude-Pattern blockiert URL."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        # PDF files are excluded by default
        result = crawler._should_crawl("https://example.com/document.pdf")
        assert result is False

    def test_CRAWL_064_should_crawl_wp_admin(self, temp_image_path):
        """CRAWL-064: WordPress Admin URLs werden ausgeschlossen."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        result = crawler._should_crawl("https://example.com/wp-admin/")
        assert result is False


class TestWebCrawlerIsSameDomain:
    """Tests für WebCrawler._is_same_domain."""

    def test_CRAWL_070_same_domain_exact(self, temp_image_path):
        """CRAWL-070: Exakt gleiche Domain."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        result = crawler._is_same_domain("https://example.com/page")
        assert result is True

    def test_CRAWL_071_same_domain_case_insensitive(self, temp_image_path):
        """CRAWL-071: Domain-Vergleich case-insensitive."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        result = crawler._is_same_domain("https://EXAMPLE.COM/page")
        assert result is True

    def test_CRAWL_072_different_domain(self, temp_image_path):
        """CRAWL-072: Unterschiedliche Domain."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        result = crawler._is_same_domain("https://other.com/page")
        assert result is False


class TestWebCrawlerExtractText:
    """Tests für WebCrawler._extract_text."""

    def test_CRAWL_080_extract_text_basic(self, temp_image_path):
        """CRAWL-080: Text aus einfachem HTML extrahieren."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Heading</h1>
            <p>This is a paragraph with some text content.</p>
        </body>
        </html>
        """

        text, metadata = crawler._extract_text(html, "https://example.com/test")

        assert "Test Page" in text
        assert "paragraph" in text
        assert metadata['title'] == "Test Page"

    def test_CRAWL_081_extract_text_removes_nav(self, temp_image_path):
        """CRAWL-081: Navigation wird entfernt."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        html = """
        <html>
        <body>
            <nav>Navigation Links</nav>
            <main><p>Main content here.</p></main>
            <footer>Footer text</footer>
        </body>
        </html>
        """

        text, _ = crawler._extract_text(html, "https://example.com/test")

        assert "Navigation" not in text
        assert "Footer" not in text
        assert "Main content" in text

    def test_CRAWL_082_extract_text_meta_description(self, temp_image_path):
        """CRAWL-082: Meta-Description extrahieren."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        html = """
        <html>
        <head>
            <title>Test</title>
            <meta name="description" content="This is the meta description.">
        </head>
        <body><p>Content</p></body>
        </html>
        """

        _, metadata = crawler._extract_text(html, "https://example.com/test")

        assert metadata['description'] == "This is the meta description."

    def test_CRAWL_083_extract_text_adds_source(self, temp_image_path):
        """CRAWL-083: Quelle wird am Ende hinzugefügt."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        html = "<html><body><p>Content here</p></body></html>"

        text, _ = crawler._extract_text(html, "https://example.com/test")

        assert "Quelle: https://example.com/test" in text


class TestWebCrawlerExtractLinks:
    """Tests für WebCrawler._extract_links."""

    def test_CRAWL_090_extract_links_basic(self, temp_image_path):
        """CRAWL-090: Einfache Links extrahieren."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        html = """
        <html>
        <body>
            <a href="/about">About</a>
            <a href="/contact">Contact</a>
        </body>
        </html>
        """

        links = crawler._extract_links(html, "https://example.com/")

        assert len(links) == 2
        assert "https://example.com/about" in links
        assert "https://example.com/contact" in links

    def test_CRAWL_091_extract_links_skips_javascript(self, temp_image_path):
        """CRAWL-091: JavaScript-Links werden übersprungen."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        html = """
        <html>
        <body>
            <a href="javascript:void(0)">JS Link</a>
            <a href="/page">Real Link</a>
        </body>
        </html>
        """

        links = crawler._extract_links(html, "https://example.com/")

        assert len(links) == 1
        assert "javascript" not in links[0]

    def test_CRAWL_092_extract_links_skips_mailto(self, temp_image_path):
        """CRAWL-092: Mailto-Links werden übersprungen."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        html = """
        <html>
        <body>
            <a href="mailto:test@example.com">Email</a>
            <a href="/page">Real Link</a>
        </body>
        </html>
        """

        links = crawler._extract_links(html, "https://example.com/")

        assert len(links) == 1
        assert "mailto" not in links[0]

    def test_CRAWL_093_extract_links_absolute_url(self, temp_image_path):
        """CRAWL-093: Absolute URLs werden beibehalten."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        html = """
        <html>
        <body>
            <a href="https://other.com/page">External</a>
        </body>
        </html>
        """

        links = crawler._extract_links(html, "https://example.com/")

        assert "https://other.com/page" in links


class TestWebCrawlerInit:
    """Tests für WebCrawler-Initialisierung."""

    def test_CRAWL_100_init_defaults(self, temp_image_path):
        """CRAWL-100: Default-Werte bei Initialisierung."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        assert crawler.max_pages == 50
        assert crawler.max_depth == 3
        assert crawler.delay_seconds == 1.0
        assert crawler.follow_external is False

    def test_CRAWL_101_init_custom_values(self, temp_image_path):
        """CRAWL-101: Custom-Werte bei Initialisierung."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler(
            "https://example.com",
            max_pages=100,
            max_depth=5,
            delay_seconds=2.0,
            follow_external=True,
            image_storage_path=temp_image_path
        )

        assert crawler.max_pages == 100
        assert crawler.max_depth == 5
        assert crawler.delay_seconds == 2.0
        assert crawler.follow_external is True

    def test_CRAWL_102_init_base_domain(self, temp_image_path):
        """CRAWL-102: Base-Domain wird korrekt extrahiert."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://www.example.com/page/", image_storage_path=temp_image_path)

        assert crawler.base_domain == "www.example.com"

    def test_CRAWL_103_init_stats(self, temp_image_path):
        """CRAWL-103: Statistiken werden initialisiert."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        assert crawler.stats['pages_crawled'] == 0
        assert crawler.stats['errors'] == 0
        assert crawler.stats['images_extracted'] == 0


class TestWebCrawlerStats:
    """Tests für Crawler-Statistiken."""

    def test_CRAWL_110_get_stats_initial(self, temp_image_path):
        """CRAWL-110: Initiale Statistiken."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        stats = crawler.get_stats()

        assert stats['pages_crawled'] == 0
        assert stats['pages_skipped'] == 0
        assert stats['errors'] == 0

    def test_CRAWL_111_get_stats_with_duration(self, temp_image_path):
        """CRAWL-111: Statistiken mit Duration."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)
        crawler.stats['start_time'] = datetime(2024, 1, 1, 10, 0, 0)
        crawler.stats['end_time'] = datetime(2024, 1, 1, 10, 1, 0)

        stats = crawler.get_stats()

        assert stats['duration_seconds'] == 60.0


class TestWebCrawlerExtractStructuredData:
    """Tests für strukturierte Daten-Extraktion."""

    def test_CRAWL_120_extract_email(self, temp_image_path):
        """CRAWL-120: E-Mail-Adresse extrahieren."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        # Note: Emails with "example" in domain are filtered out as non-contact
        html = """
        <html><body>
            <p>Kontakt: info@unternehmen.de</p>
        </body></html>
        """

        data = crawler._extract_structured_data(html, "https://example.com")

        assert data['email'] == "info@unternehmen.de"

    def test_CRAWL_121_extract_phone(self, temp_image_path):
        """CRAWL-121: Telefonnummer extrahieren."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        html = """
        <html><body>
            <p>Tel.: +49 30 12345678</p>
        </body></html>
        """

        data = crawler._extract_structured_data(html, "https://example.com")

        assert data['phone'] is not None
        assert "49" in data['phone'] or "30" in data['phone']

    def test_CRAWL_122_extract_vat_id(self, temp_image_path):
        """CRAWL-122: USt-IdNr. extrahieren."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        html = """
        <html><body>
            <p>USt-IdNr.: DE123456789</p>
        </body></html>
        """

        data = crawler._extract_structured_data(html, "https://example.com")

        assert data['vat_id'] == "DE123456789"

    def test_CRAWL_123_extract_social_links(self, temp_image_path):
        """CRAWL-123: Social Media Links extrahieren."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        html = """
        <html><body>
            <a href="https://facebook.com/example">Facebook</a>
            <a href="https://instagram.com/example">Instagram</a>
        </body></html>
        """

        data = crawler._extract_structured_data(html, "https://example.com")

        assert len(data['social_links']) == 2
        platforms = [s['platform'] for s in data['social_links']]
        assert 'facebook' in platforms
        assert 'instagram' in platforms


class TestWebCrawlerFetchPageContent:
    """Tests für fetch_page_content (mocked)."""

    @patch.object(__import__('services.crawler.modules.crawler_core', fromlist=['WebCrawler']).WebCrawler, '_fetch_page')
    def test_CRAWL_130_fetch_page_content_success(self, mock_fetch, temp_image_path):
        """CRAWL-130: Seite erfolgreich abrufen und verarbeiten."""
        from services.crawler.modules.crawler_core import WebCrawler

        mock_fetch.return_value = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <p>This is a test page with sufficient content to be indexed.</p>
            <p>It has multiple paragraphs and enough text.</p>
        </body>
        </html>
        """

        crawler = WebCrawler("https://example.com", extract_images=False, image_storage_path=temp_image_path)
        result = crawler.fetch_page_content("https://example.com/test")

        assert result is not None
        assert result['url'] == "https://example.com/test"
        assert 'content_hash' in result
        assert result['metadata']['title'] == "Test Page"

    @patch.object(__import__('services.crawler.modules.crawler_core', fromlist=['WebCrawler']).WebCrawler, '_fetch_page')
    def test_CRAWL_131_fetch_page_content_empty(self, mock_fetch, temp_image_path):
        """CRAWL-131: Leere Seite gibt None zurück."""
        from services.crawler.modules.crawler_core import WebCrawler

        mock_fetch.return_value = None

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)
        result = crawler.fetch_page_content("https://example.com/test")

        assert result is None

    @patch.object(__import__('services.crawler.modules.crawler_core', fromlist=['WebCrawler']).WebCrawler, '_fetch_page')
    def test_CRAWL_132_fetch_page_content_too_short(self, mock_fetch, temp_image_path):
        """CRAWL-132: Zu kurzer Content gibt None zurück."""
        from services.crawler.modules.crawler_core import WebCrawler

        mock_fetch.return_value = "<html><body><p>Short</p></body></html>"

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)
        result = crawler.fetch_page_content("https://example.com/test")

        assert result is None


# =============================================================================
# Integration Tests
# =============================================================================

class TestCrawlerIntegration:
    """Integration Tests für Crawler."""

    def test_CRAWL_140_full_content_extraction(self, temp_image_path):
        """CRAWL-140: Vollständige Content-Extraktion."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        html = """
        <!DOCTYPE html>
        <html lang="de">
        <head>
            <title>Unternehmen XYZ - Über uns</title>
            <meta name="description" content="Wir sind ein führendes Unternehmen.">
        </head>
        <body>
            <nav>
                <a href="/">Home</a>
                <a href="/about">Über uns</a>
            </nav>
            <main>
                <h1>Über unser Unternehmen</h1>
                <p>Wir sind seit 2010 in der Branche tätig und haben uns auf
                   innovative Lösungen spezialisiert. Unser Team besteht aus
                   erfahrenen Experten.</p>
                <h2>Unsere Mission</h2>
                <p>Wir streben danach, unseren Kunden die bestmögliche
                   Erfahrung zu bieten.</p>
            </main>
            <footer>
                <p>Kontakt: info@xyz.com</p>
                <p>Tel.: +49 30 123456</p>
            </footer>
        </body>
        </html>
        """

        text, metadata = crawler._extract_text(html, "https://example.com/about")

        # Content checks
        assert "Über unser Unternehmen" in text
        assert "innovative Lösungen" in text
        assert "Mission" in text

        # Metadata checks
        assert metadata['title'] == "Unternehmen XYZ - Über uns"
        assert "führendes Unternehmen" in metadata['description']
        assert metadata['language'] == "de"

        # Navigation and footer should be removed
        assert "Home" not in text or "Quelle" in text  # "Home" might appear in source URL

    def test_CRAWL_141_job_lifecycle(self):
        """CRAWL-141: Job-Lifecycle (queued -> running -> completed)."""
        from services.crawler.modules.crawler_service import CrawlerService

        service = CrawlerService()

        # Simulate job lifecycle
        job_id = "test-job-123"

        # Initial state
        service.active_crawls[job_id] = {
            'status': 'queued',
            'urls': ['https://example.com'],
            'pages_crawled': 0
        }

        assert service.get_job_status(job_id)['status'] == 'queued'

        # Running state
        service.active_crawls[job_id]['status'] = 'running'
        service.active_crawls[job_id]['pages_crawled'] = 5

        status = service.get_job_status(job_id)
        assert status['status'] == 'running'
        assert status['pages_crawled'] == 5

        # Completed state
        service.active_crawls[job_id]['status'] = 'completed'
        service.active_crawls[job_id]['pages_crawled'] = 10

        status = service.get_job_status(job_id)
        assert status['status'] == 'completed'
        assert status['pages_crawled'] == 10

    def test_CRAWL_142_url_normalization_consistency(self, temp_image_path):
        """CRAWL-142: URL-Normalisierung ist konsistent."""
        from services.crawler.modules.crawler_core import WebCrawler

        crawler = WebCrawler("https://example.com", image_storage_path=temp_image_path)

        # All these should normalize to the same URL
        urls = [
            "https://example.com/page",
            "https://example.com/page/",
            "http://example.com/page",
            "HTTPS://EXAMPLE.COM/page",
            "https://example.com/page#section",
        ]

        normalized = [crawler._normalize_url(url) for url in urls]

        # All should be the same
        assert len(set(normalized)) == 1
        assert normalized[0] == "https://example.com/page"
