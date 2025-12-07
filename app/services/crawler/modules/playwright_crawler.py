"""
Playwright-based Web Crawler with Screenshot and Vision-LLM Support

Orchestrator class that uses specialized modules for different responsibilities:
- ScreenshotCapture: Screenshot functionality
- ImageExtractor: Image extraction and processing
- VisionLLMProcessor: Vision-LLM data extraction
- ContentExtractor: Text content and metadata extraction

Uses headless Chromium for full JavaScript rendering.
"""

import re
import hashlib
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple, Callable
from urllib.parse import urlparse, urlunparse

from .screenshot_capture import ScreenshotCapture
from .image_extractor import ImageExtractor
from .vision_llm_processor import VisionLLMProcessor
from .content_extractor import ContentExtractor

logger = logging.getLogger(__name__)


class PlaywrightCrawler:
    """
    Advanced web crawler using Playwright for JavaScript rendering.
    Orchestrates specialized modules for screenshot, image, and content extraction.
    """

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    # Screenshot settings
    SCREENSHOT_WIDTH = 1920
    SCREENSHOT_HEIGHT = 1080

    def __init__(
        self,
        base_url: str,
        max_pages: int = 50,
        max_depth: int = 3,
        delay_seconds: float = 1.5,
        timeout: int = 30000,  # milliseconds for Playwright
        follow_external: bool = False,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        extract_images: bool = True,
        max_images_per_page: int = 10,
        image_storage_path: str = '/app/storage/rag_images',
        screenshot_storage_path: str = '/app/storage/screenshots',
        use_vision_llm: bool = True,
        vision_llm_model: str = 'mistralai/Mistral-Small-3.2-24B-Instruct-2506',
        litellm_base_url: Optional[str] = None,
        litellm_api_key: Optional[str] = None
    ):
        """
        Initialize the Playwright crawler.

        Args:
            base_url: Starting URL to crawl
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum link depth from base URL
            delay_seconds: Delay between requests
            timeout: Page load timeout in milliseconds
            follow_external: Whether to follow external links
            include_patterns: URL patterns to include
            exclude_patterns: URL patterns to exclude
            extract_images: Whether to extract images
            max_images_per_page: Maximum images per page
            image_storage_path: Path for image storage
            screenshot_storage_path: Path for screenshot storage
            use_vision_llm: Whether to use Vision-LLM for extraction
            vision_llm_model: Vision-capable LLM model name
            litellm_base_url: LiteLLM API base URL
            litellm_api_key: LiteLLM API key
        """
        # Core settings
        self.base_url = self._normalize_url(base_url)
        self.base_domain = urlparse(self.base_url).netloc
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay_seconds = delay_seconds
        self.timeout = timeout
        self.follow_external = follow_external

        # Initialize specialized modules
        self.screenshot_capture = ScreenshotCapture(screenshot_storage_path)
        self.image_extractor = ImageExtractor(image_storage_path, max_images_per_page) if extract_images else None
        self.vision_llm = VisionLLMProcessor(
            model=vision_llm_model,
            litellm_base_url=litellm_base_url,
            litellm_api_key=litellm_api_key
        ) if use_vision_llm else None
        self.content_extractor = ContentExtractor()

        # Settings
        self.extract_images = extract_images
        self.use_vision_llm = use_vision_llm

        # URL filtering
        self.include_patterns = [re.compile(p) for p in (include_patterns or [])]
        self.exclude_patterns = [re.compile(p) for p in (exclude_patterns or [
            r'\.pdf$', r'\.zip$', r'\.exe$', r'\.dmg$',
            r'\.mp3$', r'\.mp4$', r'\.avi$', r'\.mov$',
            r'/login', r'/logout', r'/signin', r'/signup',
            r'/cart', r'/checkout', r'/account',
            r'\?.*utm_', r'#'
        ])]

        # State
        self.visited_urls: Set[str] = set()
        self.crawled_pages: List[Dict] = []
        self.content_hashes: Set[str] = set()

        # Statistics
        self.stats = {
            'pages_crawled': 0,
            'pages_skipped': 0,
            'screenshots_taken': 0,
            'images_extracted': 0,
            'vision_extractions': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for consistent comparison."""
        parsed = urlparse(url)
        if not parsed.scheme:
            url = 'https://' + url
            parsed = urlparse(url)
        path = parsed.path.rstrip('/') or '/'
        return urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            path,
            '', '', ''
        ))

    def _is_same_domain(self, url: str) -> bool:
        """Check if URL belongs to the same domain."""
        return urlparse(url).netloc.lower() == self.base_domain.lower()

    def _should_crawl(self, url: str) -> bool:
        """Determine if a URL should be crawled."""
        if url in self.visited_urls:
            return False

        if not self.follow_external and not self._is_same_domain(url):
            return False

        for pattern in self.exclude_patterns:
            if pattern.search(url):
                return False

        if self.include_patterns:
            if not any(p.search(url) for p in self.include_patterns):
                return False

        return True

    async def crawl_async(
        self,
        progress_callback: Optional[Callable] = None,
        page_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        Execute the crawl asynchronously.

        Args:
            progress_callback: Optional callback(current, total, url)
            page_callback: Optional callback(page_data) for each page

        Returns:
            List of crawled pages with content, screenshots, and metadata
        """
        from playwright.async_api import async_playwright

        self.stats['start_time'] = datetime.now()
        logger.info(f"[Playwright] Starting crawl of {self.base_url} (max {self.max_pages} pages)")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            context = await browser.new_context(
                viewport={'width': self.SCREENSHOT_WIDTH, 'height': self.SCREENSHOT_HEIGHT},
                user_agent=self.USER_AGENT,
                locale='de-DE'
            )

            page = await context.new_page()

            # Queue: (url, depth)
            queue = [(self.base_url, 0)]

            while queue and len(self.crawled_pages) < self.max_pages:
                url, depth = queue.pop(0)

                if url in self.visited_urls:
                    continue

                if depth > self.max_depth:
                    continue

                if not self._should_crawl(url):
                    self.stats['pages_skipped'] += 1
                    continue

                self.visited_urls.add(url)

                logger.info(f"[Playwright] Crawling [{len(self.crawled_pages)+1}/{self.max_pages}]: {url}")

                try:
                    # Navigate to page
                    await self._navigate_to_page(page, url)

                    # Wait for dynamic content
                    await asyncio.sleep(2)

                    # Get HTML for fallback extraction
                    html = await page.content()

                    # Extract text content and metadata
                    text, metadata = await self.content_extractor.extract_text_content(page, url)

                    if text and len(text) > 100:
                        content_hash = hashlib.sha256(text.encode()).hexdigest()

                        # Skip duplicates
                        if content_hash in self.content_hashes:
                            logger.debug(f"Skipping duplicate content: {url}")
                            continue
                        self.content_hashes.add(content_hash)

                        # Take screenshot
                        screenshot_data = await self.screenshot_capture.capture_full_page(page, url, content_hash)
                        if screenshot_data:
                            self.stats['screenshots_taken'] += 1

                        # Extract structured data
                        structured_data = await self._extract_structured_data(screenshot_data, html, url)

                        # Enhance content with structured data
                        enhanced_content = self._enhance_content_with_structured_data(text, structured_data)

                        # Extract images
                        images = []
                        if self.extract_images and self.image_extractor:
                            images = await self.image_extractor.extract_images_from_page(page, url, content_hash)
                            self.stats['images_extracted'] += len(images)

                        # Build page data
                        page_data = {
                            'url': url,
                            'depth': depth,
                            'content': enhanced_content,
                            'content_length': len(enhanced_content),
                            'content_hash': content_hash,
                            'metadata': metadata,
                            'structured_data': structured_data,
                            'images': images,
                            'screenshot': screenshot_data,
                            'crawled_at': datetime.now().isoformat(),
                            'crawler_type': 'playwright'
                        }

                        self.crawled_pages.append(page_data)
                        self.stats['pages_crawled'] += 1

                        # Callback
                        if page_callback:
                            try:
                                page_callback(page_data)
                            except Exception as e:
                                logger.error(f"Error in page_callback for {url}: {e}")

                        # Extract links for queue
                        if depth < self.max_depth:
                            links = await self.content_extractor.extract_links(page, url)
                            for link in links:
                                normalized_link = self._normalize_url(link)
                                if normalized_link not in self.visited_urls:
                                    queue.append((normalized_link, depth + 1))

                        if progress_callback:
                            progress_callback(len(self.crawled_pages), self.max_pages, url)
                    else:
                        self.stats['pages_skipped'] += 1

                except Exception as e:
                    logger.warning(f"Error crawling {url}: {e}")
                    self.stats['errors'] += 1

                # Polite delay
                await asyncio.sleep(self.delay_seconds)

            await browser.close()

        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

        logger.info(f"[Playwright] Crawl complete: {self.stats['pages_crawled']} pages in {duration:.1f}s")
        logger.info(f"[Playwright] Stats: {self.stats}")

        return self.crawled_pages

    async def _navigate_to_page(self, page, url: str):
        """
        Navigate to page with robust error handling.

        Args:
            page: Playwright page object
            url: URL to navigate to
        """
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
            # Try to wait for networkidle but don't fail if it times out
            try:
                await page.wait_for_load_state('networkidle', timeout=10000)
            except Exception:
                pass  # networkidle timeout is acceptable
        except Exception as nav_error:
            logger.warning(f"Navigation error for {url}: {nav_error}")
            # Try with just load event
            try:
                await page.goto(url, wait_until='load', timeout=self.timeout)
            except Exception:
                raise nav_error

    async def _extract_structured_data(
        self,
        screenshot_data: Optional[Dict],
        html: str,
        url: str
    ) -> Dict:
        """
        Extract structured data using Vision-LLM or regex fallback.

        Args:
            screenshot_data: Screenshot data with base64
            html: Raw HTML content
            url: Page URL

        Returns:
            Dict with structured data fields
        """
        structured_data = {}

        # Try Vision-LLM first
        if self.use_vision_llm and self.vision_llm and screenshot_data:
            structured_data = await self.vision_llm.extract_structured_data(
                screenshot_data['base64_data'],
                url
            )
            if structured_data and any(v for v in structured_data.values() if v):
                self.stats['vision_extractions'] += 1

        # Fallback to regex if Vision-LLM failed or disabled
        if not structured_data or not any(v for v in structured_data.values() if v):
            structured_data = self.content_extractor.extract_structured_data_regex(html, url)

        return structured_data

    def _enhance_content_with_structured_data(self, text: str, structured_data: Dict) -> str:
        """
        Enhance content with extracted structured data.

        Args:
            text: Original text content
            structured_data: Extracted structured data

        Returns:
            Enhanced content with structured data section
        """
        if not any(v for v in structured_data.values() if v and v != []):
            return text

        structured_section = "\n\n## Extrahierte Informationen\n"

        if structured_data.get('company_name'):
            structured_section += f"- **Firma:** {structured_data['company_name']}\n"
        if structured_data.get('owner'):
            structured_section += f"- **Inhaber/Geschäftsführer:** {structured_data['owner']}\n"
        if structured_data.get('email'):
            structured_section += f"- **E-Mail:** {structured_data['email']}\n"
        if structured_data.get('phone'):
            structured_section += f"- **Telefon:** {structured_data['phone']}\n"
        if structured_data.get('address'):
            structured_section += f"- **Adresse:** {structured_data['address']}\n"
        if structured_data.get('vat_id'):
            structured_section += f"- **USt-IdNr:** {structured_data['vat_id']}\n"
        if structured_data.get('website_purpose'):
            structured_section += f"- **Beschreibung:** {structured_data['website_purpose']}\n"
        if structured_data.get('services'):
            services = structured_data['services']
            if isinstance(services, list) and services:
                structured_section += f"- **Leistungen:** {', '.join(services)}\n"
        if structured_data.get('team_members'):
            members = structured_data['team_members']
            if isinstance(members, list) and members:
                structured_section += f"- **Team:** {', '.join(members)}\n"

        # Insert before source footer
        if "\n\n---\nQuelle:" in text:
            return text.replace("\n\n---\nQuelle:", f"{structured_section}\n\n---\nQuelle:")
        else:
            return text + structured_section

    def crawl(
        self,
        progress_callback: Optional[Callable] = None,
        page_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        Synchronous wrapper for crawl_async.

        Args:
            progress_callback: Optional callback(current, total, url)
            page_callback: Optional callback(page_data) for each page

        Returns:
            List of crawled pages
        """
        return asyncio.run(self.crawl_async(progress_callback, page_callback))

    def get_stats(self) -> Dict:
        """
        Return crawl statistics.

        Returns:
            Dict with crawl statistics
        """
        stats = self.stats.copy()
        if stats['start_time'] and stats['end_time']:
            stats['duration_seconds'] = (stats['end_time'] - stats['start_time']).total_seconds()
        return stats
