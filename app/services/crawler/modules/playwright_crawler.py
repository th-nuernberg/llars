"""
Playwright-based Web Crawler with Screenshot and Vision-LLM Support

Uses headless Chromium for full JavaScript rendering,
captures screenshots, and uses Vision-LLM for intelligent data extraction.
"""

import re
import os
import io
import time
import hashlib
import logging
import base64
import asyncio
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple, Callable
from urllib.parse import urljoin, urlparse, urlunparse
from PIL import Image

logger = logging.getLogger(__name__)


class PlaywrightCrawler:
    """
    Advanced web crawler using Playwright for JavaScript rendering.
    Captures screenshots and uses Vision-LLM for intelligent extraction.
    """

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    # Screenshot settings
    SCREENSHOT_WIDTH = 1920
    SCREENSHOT_HEIGHT = 1080
    FULL_PAGE_SCREENSHOT = True

    # Image settings
    SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    MAX_IMAGE_SIZE = (1024, 1024)
    MAX_IMAGE_BYTES = 5 * 1024 * 1024

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
        self.base_url = self._normalize_url(base_url)
        self.base_domain = urlparse(self.base_url).netloc
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay_seconds = delay_seconds
        self.timeout = timeout
        self.follow_external = follow_external

        # Image settings
        self.extract_images = extract_images
        self.max_images_per_page = max_images_per_page
        self.image_storage_path = image_storage_path
        self.screenshot_storage_path = screenshot_storage_path

        # Vision-LLM settings
        self.use_vision_llm = use_vision_llm
        self.vision_llm_model = vision_llm_model
        self.litellm_base_url = litellm_base_url or os.getenv('LITELLM_BASE_URL', 'https://kiz1.in.ohmportal.de/llmproxy/v1')
        self.litellm_api_key = litellm_api_key or os.getenv('LITELLM_API_KEY', '')

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

        # Create storage directories
        for path in [self.image_storage_path, self.screenshot_storage_path]:
            if path:
                os.makedirs(path, exist_ok=True)

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

    async def _take_screenshot(self, page, url: str, page_hash: str) -> Optional[Dict]:
        """
        Take a screenshot of the current page.

        Returns:
            Dict with screenshot path, base64 data, and dimensions
        """
        try:
            # Wait for page to be fully loaded
            await page.wait_for_load_state('networkidle', timeout=10000)

            # Take screenshot
            screenshot_bytes = await page.screenshot(
                full_page=self.FULL_PAGE_SCREENSHOT,
                type='png'
            )

            # Process with PIL
            image = Image.open(io.BytesIO(screenshot_bytes))

            # Convert to RGB
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')

            # Save full-size screenshot as PNG
            filename = f"screenshot_{page_hash[:16]}.png"
            filepath = os.path.join(self.screenshot_storage_path, filename)
            image.save(filepath, 'PNG', optimize=True)

            # Create smaller version for Vision-LLM (max 2048x2048)
            vision_image = image.copy()
            if vision_image.size[0] > 2048 or vision_image.size[1] > 2048:
                vision_image.thumbnail((2048, 2048), Image.Resampling.LANCZOS)

            # Generate base64 for Vision-LLM
            buffer = io.BytesIO()
            vision_image.save(buffer, format='JPEG', quality=85)
            base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

            self.stats['screenshots_taken'] += 1

            return {
                'screenshot_path': filepath,
                'base64_data': base64_data,
                'mime_type': 'image/jpeg',
                'width': image.size[0],
                'height': image.size[1]
            }

        except Exception as e:
            logger.warning(f"Failed to take screenshot for {url}: {e}")
            return None

    async def _extract_with_vision_llm(
        self,
        screenshot_base64: str,
        html_text: str,
        url: str
    ) -> Dict:
        """
        Use Vision-LLM to extract structured data from screenshot.

        Returns:
            Dict with extracted business information
        """
        if not self.use_vision_llm:
            return {}

        try:
            import openai

            client = openai.OpenAI(
                base_url=self.litellm_base_url,
                api_key=self.litellm_api_key
            )

            extraction_prompt = """Analysiere diesen Screenshot einer Website und extrahiere folgende Informationen.
Antworte NUR im JSON-Format ohne zusätzlichen Text.

Extrahiere diese Felder (setze null wenn nicht gefunden):
{
    "company_name": "Vollständiger Firmenname",
    "owner": "Name des Inhabers oder Geschäftsführers",
    "email": "Kontakt E-Mail Adresse",
    "phone": "Telefonnummer",
    "address": "Vollständige Adresse",
    "vat_id": "USt-IdNr falls vorhanden",
    "website_purpose": "Kurze Beschreibung wofür die Website/Firma steht (max 2 Sätze)",
    "services": ["Liste der angebotenen Dienstleistungen/Produkte"],
    "team_members": ["Liste der Teammitglieder mit Namen und Rolle falls sichtbar"]
}

Wichtig:
- Extrahiere nur Informationen die KLAR SICHTBAR sind
- Für owner: Suche nach "Inhaber", "Geschäftsführer", "CEO" oder ähnlichen Bezeichnungen
- Ignoriere generische Platzhalter oder Lorem ipsum
- Antworte AUSSCHLIESSLICH mit validem JSON"""

            response = client.chat.completions.create(
                model=self.vision_llm_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": extraction_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{screenshot_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )

            # Handle None response content
            response_content = response.choices[0].message.content
            if not response_content:
                logger.warning(f"Vision-LLM returned empty response for {url}")
                return {}

            response_text = response_content.strip()

            # Parse JSON response
            import json

            # Clean up response (remove markdown code blocks if present)
            if response_text.startswith('```'):
                response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
                response_text = re.sub(r'\n?```$', '', response_text)

            extracted = json.loads(response_text)
            self.stats['vision_extractions'] += 1

            logger.info(f"Vision-LLM extracted data for {url}: {list(k for k, v in extracted.items() if v)}")

            return extracted

        except Exception as e:
            logger.warning(f"Vision-LLM extraction failed for {url}: {e}")
            return {}

    def _extract_structured_data_regex(self, html: str, url: str) -> Dict:
        """
        Fallback: Extract structured data using regex patterns.
        Used when Vision-LLM is disabled or fails.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')
        structured = {
            'company_name': None,
            'owner': None,
            'email': None,
            'phone': None,
            'address': None,
            'vat_id': None,
            'website_purpose': None,
            'services': [],
            'team_members': []
        }

        full_text = soup.get_text(separator=' ', strip=True)

        # Email
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', full_text)
        contact_emails = [e for e in emails if not any(x in e.lower() for x in ['noreply', 'no-reply', 'example'])]
        if contact_emails:
            structured['email'] = contact_emails[0]

        # Phone (German)
        phone_patterns = [
            r'\+49\s*[\d\s/\-()]+',
            r'0\d{2,4}[\s/\-]?\d{3,}[\s/\-]?\d{2,}',
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, full_text)
            if phones:
                structured['phone'] = phones[0].strip()
                break

        # Owner - improved patterns
        owner_patterns = [
            r'Inhaber[:\s]+([A-ZÄÖÜa-zäöüß][a-zäöüß]+\s+[A-ZÄÖÜa-zäöüß][a-zäöüß]+)',
            r'Geschäftsführer[:\s]+([A-ZÄÖÜa-zäöüß][a-zäöüß]+\s+[A-ZÄÖÜa-zäöüß][a-zäöüß]+)',
            r'Geschäftsführung[:\s]+([A-ZÄÖÜa-zäöüß][a-zäöüß]+\s+[A-ZÄÖÜa-zäöüß][a-zäöüß]+)',
        ]
        for pattern in owner_patterns:
            match = re.search(pattern, full_text)
            if match:
                owner = match.group(1).strip()
                if len(owner.split()) >= 2:  # At least first and last name
                    structured['owner'] = owner
                    break

        # Company name
        company_patterns = [
            r'([A-ZÄÖÜa-zäöüß\s\-&]+(?:GmbH|AG|GbR|OHG|KG|UG|e\.?K\.?))',
        ]
        for pattern in company_patterns:
            match = re.search(pattern, full_text)
            if match:
                structured['company_name'] = match.group(1).strip()
                break

        # VAT ID
        vat_match = re.search(r'USt\.?-?(?:Id\.?-?)?Nr\.?:?\s*(DE\s*\d{9})', full_text, re.IGNORECASE)
        if vat_match:
            structured['vat_id'] = vat_match.group(1).replace(' ', '')

        # Address
        address_patterns = [
            r'(\d{5}\s+[A-ZÄÖÜa-zäöüß\-]+)',
            r'([A-ZÄÖÜa-zäöüß]+str(?:aße|\.)\s+\d+[a-z]?)',
        ]
        address_parts = []
        for pattern in address_patterns:
            matches = re.findall(pattern, full_text)
            address_parts.extend(matches[:2])
        if address_parts:
            structured['address'] = ', '.join(address_parts[:2])

        return structured

    async def _extract_images_from_page(self, page, url: str, page_hash: str) -> List[Dict]:
        """Extract images from the rendered page."""
        if not self.extract_images:
            return []

        images = []
        seen_urls = set()

        try:
            img_elements = await page.query_selector_all('img[src]')

            for img in img_elements[:self.max_images_per_page * 2]:  # Get more, filter later
                if len(images) >= self.max_images_per_page:
                    break

                try:
                    src = await img.get_attribute('src')
                    alt = await img.get_attribute('alt') or ''

                    if not src or src.startswith('data:') or 'pixel' in src.lower():
                        continue

                    # Get dimensions
                    box = await img.bounding_box()
                    if box and (box['width'] < 100 or box['height'] < 100):
                        continue

                    # Resolve URL
                    absolute_url = urljoin(url, src)
                    if absolute_url in seen_urls:
                        continue
                    seen_urls.add(absolute_url)

                    # Check extension
                    ext = os.path.splitext(urlparse(absolute_url).path)[1].lower()
                    if ext not in self.SUPPORTED_IMAGE_FORMATS:
                        continue

                    # Download and process image
                    image_data = await self._fetch_and_process_image(absolute_url, page_hash, len(images))
                    if image_data:
                        image_data['alt_text'] = alt
                        image_data['source_url'] = absolute_url
                        images.append(image_data)
                        self.stats['images_extracted'] += 1

                except Exception as e:
                    logger.debug(f"Error processing image element: {e}")
                    continue

        except Exception as e:
            logger.warning(f"Error extracting images from {url}: {e}")

        return images

    async def _fetch_and_process_image(self, url: str, page_hash: str, index: int) -> Optional[Dict]:
        """Fetch and process a single image."""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        return None

                    content_length = response.headers.get('Content-Length')
                    if content_length and int(content_length) > self.MAX_IMAGE_BYTES:
                        return None

                    image_data = await response.read()
                    if len(image_data) > self.MAX_IMAGE_BYTES:
                        return None

            # Process with PIL
            image = Image.open(io.BytesIO(image_data))

            if image.size[0] < 100 or image.size[1] < 100:
                return None

            # Convert to RGB
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])
                image = background
            elif image.mode not in ['RGB', 'L']:
                image = image.convert('RGB')

            # Resize if needed
            if image.size[0] > self.MAX_IMAGE_SIZE[0] or image.size[1] > self.MAX_IMAGE_SIZE[1]:
                image.thumbnail(self.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)

            # Save
            filename = f"{page_hash[:16]}_{index}.jpg"
            filepath = os.path.join(self.image_storage_path, filename)
            image.save(filepath, 'JPEG', quality=85)

            # Base64
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

            return {
                'image_path': filepath,
                'base64_data': base64_data,
                'mime_type': 'image/jpeg',
                'width': image.size[0],
                'height': image.size[1]
            }

        except Exception as e:
            logger.debug(f"Failed to process image {url}: {e}")
            return None

    async def _extract_links(self, page, url: str) -> List[str]:
        """Extract links from the rendered page."""
        links = []

        try:
            link_elements = await page.query_selector_all('a[href]')

            for link in link_elements:
                try:
                    href = await link.get_attribute('href')
                    if not href or href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                        continue

                    absolute_url = urljoin(url, href)
                    normalized = self._normalize_url(absolute_url)

                    if normalized not in links:
                        links.append(normalized)

                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"Error extracting links from {url}: {e}")

        return links

    async def _extract_text_content(self, page, url: str) -> Tuple[str, Dict]:
        """Extract text content and metadata from the rendered page."""
        metadata = {
            'url': url,
            'title': '',
            'description': '',
            'keywords': '',
            'language': 'de',
            'author': ''
        }

        try:
            # Get title with timeout
            try:
                title = await page.title()
                metadata['title'] = title or ''
            except Exception:
                metadata['title'] = ''

            # Get meta tags
            try:
                meta_desc = await page.query_selector('meta[name="description"]')
                if meta_desc:
                    metadata['description'] = await meta_desc.get_attribute('content') or ''
            except Exception:
                pass

            # Remove only truly unwanted elements (not content!)
            # Note: Avoiding broad selectors like [class*="nav"] as they can remove content containers
            try:
                await asyncio.wait_for(
                    page.evaluate('''() => {
                        // Only remove elements that are definitely not content
                        const safeSelectors = [
                            'script', 'style', 'noscript', 'iframe',
                            '[class*="cookie-banner"]', '[class*="cookie-notice"]',
                            '[class*="gdpr"]', '[id*="cookie"]',
                            '[class*="popup"]', '[class*="modal"]',
                            '[aria-hidden="true"]'
                        ];
                        safeSelectors.forEach(selector => {
                            try {
                                document.querySelectorAll(selector).forEach(el => el.remove());
                            } catch(e) {}
                        });
                    }'''),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                logger.debug(f"Timeout removing unwanted elements for {url}")
            except Exception as e:
                logger.debug(f"Error removing elements: {e}")

            # Get main content with timeout protection
            main_selectors = ['main', 'article', '[role="main"]', '.content', '.article']
            text_content = ''

            for selector in main_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        # Use element.inner_text() directly
                        try:
                            text_content = await asyncio.wait_for(
                                element.inner_text(),
                                timeout=10.0
                            )
                        except asyncio.TimeoutError:
                            logger.debug(f"Timeout on inner_text for {selector}")
                            continue

                        if text_content and len(text_content) > 200:
                            logger.debug(f"Found content in {selector}: {len(text_content)} chars")
                            break
                except asyncio.TimeoutError:
                    logger.debug(f"Timeout finding selector {selector}")
                    continue
                except Exception as e:
                    logger.debug(f"Error extracting from {selector}: {e}")
                    continue

            # Fallback to body if no content found
            if not text_content or len(text_content) < 100:
                logger.debug("Using body fallback for content extraction")
                try:
                    text_content = await asyncio.wait_for(
                        page.evaluate('() => document.body ? document.body.innerText : ""'),
                        timeout=15.0
                    )
                    logger.debug(f"Body fallback extracted: {len(text_content)} chars")
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout extracting body text from {url}")
                    # Last resort: get raw HTML text
                    try:
                        html = await page.content()
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(html, 'html.parser')
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        text_content = soup.get_text(separator=' ', strip=True)
                        logger.debug(f"BeautifulSoup fallback extracted: {len(text_content)} chars")
                    except Exception:
                        text_content = ''
                except Exception as e:
                    logger.warning(f"Error in fallback body extraction: {e}")
                    text_content = ''

            if not text_content:
                return '', metadata

            # Clean up
            text_content = re.sub(r'\n{3,}', '\n\n', text_content)
            text_content = re.sub(r' {2,}', ' ', text_content)

            # Format
            formatted = f"# {metadata['title']}\n\n{text_content}" if metadata['title'] else text_content
            formatted += f"\n\n---\nQuelle: {url}\n"

            return formatted.strip(), metadata

        except Exception as e:
            logger.warning(f"Error extracting text from {url}: {e}")
            return '', metadata

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
                    # Navigate to page with more reliable wait strategy
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

                    # Wait for dynamic content
                    await asyncio.sleep(2)

                    # Get HTML for fallback extraction
                    html = await page.content()

                    # Extract text content
                    text, metadata = await self._extract_text_content(page, url)

                    if text and len(text) > 100:
                        content_hash = hashlib.sha256(text.encode()).hexdigest()

                        # Skip duplicates
                        if content_hash in self.content_hashes:
                            logger.debug(f"Skipping duplicate content: {url}")
                            continue
                        self.content_hashes.add(content_hash)

                        # Take screenshot
                        screenshot_data = await self._take_screenshot(page, url, content_hash)

                        # Extract structured data
                        structured_data = {}

                        if self.use_vision_llm and screenshot_data:
                            # Use Vision-LLM for intelligent extraction
                            structured_data = await self._extract_with_vision_llm(
                                screenshot_data['base64_data'],
                                html,
                                url
                            )

                        # Fallback to regex if Vision-LLM failed or disabled
                        if not structured_data or not any(v for v in structured_data.values() if v):
                            structured_data = self._extract_structured_data_regex(html, url)

                        # Enhance content with structured data
                        enhanced_content = text
                        if any(v for v in structured_data.values() if v and v != []):
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

                            if "\n\n---\nQuelle:" in enhanced_content:
                                enhanced_content = enhanced_content.replace(
                                    "\n\n---\nQuelle:",
                                    f"{structured_section}\n\n---\nQuelle:"
                                )
                            else:
                                enhanced_content += structured_section

                        # Extract images
                        images = await self._extract_images_from_page(page, url, content_hash)

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
                            links = await self._extract_links(page, url)
                            for link in links:
                                if link not in self.visited_urls:
                                    queue.append((link, depth + 1))

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

    def crawl(
        self,
        progress_callback: Optional[Callable] = None,
        page_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        Synchronous wrapper for crawl_async.
        """
        return asyncio.run(self.crawl_async(progress_callback, page_callback))

    def get_stats(self) -> Dict:
        """Return crawl statistics."""
        stats = self.stats.copy()
        if stats['start_time'] and stats['end_time']:
            stats['duration_seconds'] = (stats['end_time'] - stats['start_time']).total_seconds()
        return stats
