"""
WebCrawler Core Module

Core crawler logic for extracting text content and images from websites.
Designed to be polite and respect website policies.
"""

import re
import os
import io
import time
import hashlib
import logging
import base64
import requests
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from PIL import Image

logger = logging.getLogger(__name__)


class WebCrawler:
    """
    Intelligent web crawler that extracts text content from websites.
    Designed to be polite and respect website policies.
    """

    USER_AGENT = "LLARSBot/1.0 (+https://github.com/llars; friendly-crawler)"

    # Supported image formats for extraction
    SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    MAX_IMAGE_SIZE = (1024, 1024)  # Max dimensions for stored images
    MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5MB max per image

    def __init__(
        self,
        base_url: str,
        max_pages: int = 50,
        max_depth: int = 3,
        delay_seconds: float = 1.0,
        timeout: int = 30,
        follow_external: bool = False,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        extract_images: bool = True,
        max_images_per_page: int = 10,
        image_storage_path: str = '/app/storage/rag_images'
    ):
        """
        Initialize the web crawler.

        Args:
            base_url: Starting URL to crawl
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum link depth from base URL
            delay_seconds: Delay between requests (politeness)
            timeout: Request timeout in seconds
            follow_external: Whether to follow links to other domains
            include_patterns: URL patterns to include (regex)
            exclude_patterns: URL patterns to exclude (regex)
            extract_images: Whether to extract and store images
            max_images_per_page: Maximum images to extract per page
            image_storage_path: Path to store extracted images
        """
        self.base_url = self._normalize_url(base_url)
        self.base_domain = urlparse(self.base_url).netloc
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay_seconds = delay_seconds
        self.timeout = timeout
        self.follow_external = follow_external

        # Image extraction settings
        self.extract_images = extract_images
        self.max_images_per_page = max_images_per_page
        self.image_storage_path = image_storage_path

        # URL filtering patterns
        self.include_patterns = [re.compile(p) for p in (include_patterns or [])]
        self.exclude_patterns = [re.compile(p) for p in (exclude_patterns or [
            # Binary/Media files
            r'\.pdf$', r'\.zip$', r'\.exe$', r'\.dmg$',
            r'\.mp3$', r'\.mp4$', r'\.avi$', r'\.mov$', r'\.webm$',
            r'\.png$', r'\.jpg$', r'\.jpeg$', r'\.gif$', r'\.svg$', r'\.ico$', r'\.webp$',
            r'\.woff$', r'\.woff2$', r'\.ttf$', r'\.eot$',
            # Code/Style files - these are NOT content
            r'\.css$', r'\.js$', r'\.json$', r'\.xml$',
            r'\.map$', r'\.min\.js$', r'\.min\.css$',
            # WordPress specific non-content
            r'/wp-content/plugins/.*\.(css|js)$',
            r'/wp-content/themes/.*\.(css|js)$',
            r'/wp-content/uploads/.*\.(css|js)$',
            r'/wp-includes/.*\.(css|js)$',
            r'/xmlrpc\.php',
            r'/wp-json/',
            # Feeds
            r'/feed/?$', r'/feed/.*$', r'/rss/?$', r'/atom/?$',
            r'/comments/feed',
            # Auth/Account pages
            r'/login', r'/logout', r'/signin', r'/signup',
            r'/cart', r'/checkout', r'/account',
            r'/wp-login', r'/wp-admin',
            # Tracking/Analytics
            r'\?.*utm_', r'#',
            # Common non-content paths
            r'/cdn-cgi/', r'/ajax/', r'/api/',
        ])]

        # State tracking
        self.visited_urls: Set[str] = set()
        self.crawled_pages: List[Dict] = []
        self.robots_parser: Optional[RobotFileParser] = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

        # Statistics
        self.stats = {
            'pages_crawled': 0,
            'pages_skipped': 0,
            'images_extracted': 0,
            'errors': 0,
            'total_bytes': 0,
            'start_time': None,
            'end_time': None
        }

        # Create image storage directory if needed
        if self.extract_images and self.image_storage_path:
            os.makedirs(self.image_storage_path, exist_ok=True)

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for consistent comparison."""
        parsed = urlparse(url)
        # Ensure scheme
        if not parsed.scheme:
            url = 'https://' + url
            parsed = urlparse(url)
        # Remove trailing slash and fragments
        path = parsed.path.rstrip('/') or '/'
        return urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            path,
            '', '', ''
        ))

    # ------------------------------------------------------------------
    # Discovery phase: quickly collect URLs without heavy extraction
    # ------------------------------------------------------------------

    def discover_urls(
        self,
        max_pages: int,
        max_depth: int,
        progress_callback=None
    ) -> List[str]:
        """
        Fast discovery of URLs (BFS), without text/image extraction.

        Uses parallel requests for speed. Returns a de-duplicated list of URLs.

        Args:
            max_pages: Maximum URLs to discover
            max_depth: Maximum crawl depth
            progress_callback: Optional callback(discovered_count, current_url)
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        discovered = []
        queue: List[Tuple[str, int]] = [(self.base_url, 0)]
        self.visited_urls = set()
        pending_urls: Set[str] = {self.base_url}

        def fetch_links(url: str) -> List[str]:
            """Fetch a page and extract all links quickly."""
            try:
                # Use shorter timeout for discovery
                # Don't use stream=True because we need automatic decompression
                response = self.session.get(
                    url,
                    timeout=min(10, self.timeout),
                    allow_redirects=True
                )
                response.raise_for_status()

                # Check content type - only process HTML
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' not in content_type and 'application/xhtml' not in content_type:
                    return []

                # Use response.text for automatic decompression and encoding handling
                # Limit to first 500KB worth of text
                content = response.text[:500 * 1024]

                # Quick regex-based link extraction (faster than BeautifulSoup for discovery)
                links = []
                # Match href="..." or href='...'
                href_pattern = r'href=["\']([^"\']+)["\']'
                for match in re.finditer(href_pattern, content, re.IGNORECASE):
                    href = match.group(1)
                    if href.startswith(('javascript:', 'mailto:', 'tel:', '#', 'data:')):
                        continue
                    try:
                        normalized = urljoin(url, href)
                        normalized = self._normalize_url(normalized)
                        if self._should_crawl(normalized):
                            links.append(normalized)
                    except Exception:
                        continue
                return links
            except Exception as e:
                logger.debug(f"[Discovery] Skip {url}: {e}")
                return []

        # Use thread pool for parallel discovery
        max_workers = min(8, max(2, max_pages // 5))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while queue and len(discovered) < max_pages:
                # Take batch from queue
                batch_size = min(max_workers * 2, len(queue), max_pages - len(discovered))
                batch = []

                for _ in range(batch_size):
                    if not queue:
                        break
                    url, depth = queue.pop(0)

                    if url in self.visited_urls:
                        continue

                    if depth > max_depth:
                        continue

                    self.visited_urls.add(url)
                    batch.append((url, depth))

                if not batch:
                    break

                # Submit batch for parallel fetching
                future_to_url = {
                    executor.submit(fetch_links, url): (url, depth)
                    for url, depth in batch
                }

                for future in as_completed(future_to_url):
                    url, depth = future_to_url[future]
                    discovered.append(url)

                    if progress_callback:
                        try:
                            progress_callback(len(discovered), url)
                        except Exception:
                            pass

                    # Add discovered links to queue
                    try:
                        new_links = future.result()
                        for link in new_links:
                            if link not in self.visited_urls and link not in pending_urls:
                                pending_urls.add(link)
                                queue.append((link, depth + 1))
                    except Exception as e:
                        logger.debug(f"[Discovery] Error processing {url}: {e}")

                    if len(discovered) >= max_pages:
                        break

        logger.info(f"[Discovery] Found {len(discovered)} URLs")
        return discovered

    def _is_same_domain(self, url: str) -> bool:
        """Check if URL belongs to the same domain."""
        return urlparse(url).netloc.lower() == self.base_domain.lower()

    def _should_crawl(self, url: str) -> bool:
        """Determine if a URL should be crawled."""
        # Already visited
        if url in self.visited_urls:
            return False

        # Check domain
        if not self.follow_external and not self._is_same_domain(url):
            return False

        # Check robots.txt
        if self.robots_parser and not self.robots_parser.can_fetch(self.USER_AGENT, url):
            logger.debug(f"Robots.txt disallows: {url}")
            return False

        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if pattern.search(url):
                logger.debug(f"Excluded by pattern: {url}")
                return False

        # Check include patterns (if any specified, URL must match at least one)
        if self.include_patterns:
            if not any(p.search(url) for p in self.include_patterns):
                return False

        return True

    def _load_robots_txt(self):
        """Load and parse robots.txt."""
        try:
            robots_url = urljoin(self.base_url, '/robots.txt')
            self.robots_parser = RobotFileParser()
            self.robots_parser.set_url(robots_url)
            self.robots_parser.read()
            logger.info(f"Loaded robots.txt from {robots_url}")

            # Try to get crawl delay from robots.txt
            crawl_delay = self.robots_parser.crawl_delay(self.USER_AGENT)
            if crawl_delay:
                self.delay_seconds = max(self.delay_seconds, crawl_delay)
                logger.info(f"Using crawl delay from robots.txt: {self.delay_seconds}s")
        except Exception as e:
            logger.warning(f"Could not load robots.txt: {e}")
            self.robots_parser = None

    def _extract_text(self, html: str, url: str) -> Tuple[str, Dict]:
        """
        Extract clean text content from HTML.

        Returns:
            Tuple of (text_content, metadata)
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Extract metadata
        metadata = {
            'url': url,
            'title': '',
            'description': '',
            'keywords': '',
            'language': 'de',
            'author': ''
        }

        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text(strip=True)

        # Meta tags
        for meta in soup.find_all('meta'):
            name = (meta.get('name') or meta.get('property') or '').lower()
            content = meta.get('content', '')

            if name in ['description', 'og:description']:
                metadata['description'] = content
            elif name == 'keywords':
                metadata['keywords'] = content
            elif name == 'author':
                metadata['author'] = content
            elif name in ['language', 'og:locale']:
                metadata['language'] = content[:2] if content else 'de'

        # First, capture raw body text before aggressive filtering (for fallback)
        raw_soup = BeautifulSoup(html, 'html.parser')
        for el in raw_soup.find_all(['script', 'style', 'noscript']):
            el.decompose()
        raw_body = raw_soup.find('body')
        raw_body_text = raw_body.get_text(separator=' ', strip=True) if raw_body else ''

        # Remove unwanted elements
        for element in soup.find_all([
            'script', 'style', 'nav', 'header', 'footer',
            'aside', 'form', 'button', 'iframe', 'noscript',
            'svg', 'img', 'video', 'audio'
        ]):
            element.decompose()

        # Remove elements by class/id that typically contain non-content
        for selector in [
            '[class*="nav"]', '[class*="menu"]', '[class*="sidebar"]',
            '[class*="footer"]', '[class*="header"]', '[class*="cookie"]',
            '[class*="popup"]', '[class*="modal"]', '[class*="ad-"]',
            '[id*="nav"]', '[id*="menu"]', '[id*="sidebar"]',
            '[id*="footer"]', '[id*="header"]', '[id*="cookie"]'
        ]:
            for element in soup.select(selector):
                element.decompose()

        # Try to find main content area
        main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find('[role="main"]') or
            soup.find(class_=re.compile(r'content|article|post|entry')) or
            soup.find('body')
        )

        if not main_content:
            main_content = soup

        # Extract text with structure
        text_parts = []

        # Add title as header
        if metadata['title']:
            text_parts.append(f"# {metadata['title']}\n")

        # Process headings and paragraphs
        for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'td', 'th']):
            text = element.get_text(separator=' ', strip=True)
            if text and len(text) > 10:  # Skip very short content
                tag = element.name
                if tag.startswith('h'):
                    level = int(tag[1])
                    text_parts.append(f"\n{'#' * level} {text}\n")
                elif tag == 'li':
                    text_parts.append(f"- {text}")
                else:
                    text_parts.append(text)

        # Clean up and join
        text = '\n'.join(text_parts)

        # Fallback: If we got very little text, use raw body text
        if len(text) < 200 and raw_body_text and len(raw_body_text) > 100:
            # Clean up the raw text - remove excessive whitespace
            fallback_text = re.sub(r'\s+', ' ', raw_body_text).strip()
            # Remove common navigation/footer patterns
            fallback_text = re.sub(r'(Cookie|Datenschutz|Impressum|©|All Rights Reserved).*$', '', fallback_text, flags=re.IGNORECASE)

            if len(fallback_text) > len(text):
                text = f"# {metadata['title']}\n\n{fallback_text}" if metadata['title'] else fallback_text
                logger.info(f"Used fallback text extraction for {url} ({len(fallback_text)} chars)")

        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)

        # Add source information
        text += f"\n\n---\nQuelle: {url}\n"

        return text.strip(), metadata

    def _extract_images(self, html: str, base_url: str, page_hash: str) -> List[Dict]:
        """
        Extract relevant images from HTML page.

        Args:
            html: HTML content
            base_url: Base URL for resolving relative paths
            page_hash: Hash of the page for unique image naming

        Returns:
            List of image dictionaries with url, alt_text, stored_path, base64_data
        """
        if not self.extract_images:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        images = []
        seen_urls = set()

        # Find all images
        for img in soup.find_all('img', src=True):
            if len(images) >= self.max_images_per_page:
                break

            src = img.get('src', '')
            alt = img.get('alt', '') or img.get('title', '')

            # Skip data URLs, tracking pixels, icons
            if src.startswith('data:') or 'pixel' in src.lower() or 'tracking' in src.lower():
                continue

            # Skip tiny images (likely icons)
            width = img.get('width')
            height = img.get('height')
            if width and height:
                try:
                    if int(width) < 100 or int(height) < 100:
                        continue
                except (ValueError, TypeError):
                    pass

            # Resolve absolute URL
            absolute_url = urljoin(base_url, src)

            # Check file extension
            parsed = urlparse(absolute_url)
            ext = os.path.splitext(parsed.path)[1].lower()
            if ext not in self.SUPPORTED_IMAGE_FORMATS:
                continue

            # Skip duplicates
            if absolute_url in seen_urls:
                continue
            seen_urls.add(absolute_url)

            # Try to fetch and process the image
            image_data = self._fetch_and_process_image(absolute_url, page_hash, len(images))
            if image_data:
                image_data['alt_text'] = alt
                image_data['source_url'] = absolute_url
                images.append(image_data)
                self.stats['images_extracted'] += 1

        return images

    def _fetch_and_process_image(self, url: str, page_hash: str, index: int) -> Optional[Dict]:
        """
        Fetch and process a single image.

        Returns:
            Dict with image_path, base64_data, mime_type, width, height or None
        """
        try:
            response = self.session.get(url, timeout=10, stream=True)
            response.raise_for_status()

            # Check content length
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > self.MAX_IMAGE_BYTES:
                logger.debug(f"Image too large: {url}")
                return None

            # Read image data
            image_data = response.content
            if len(image_data) > self.MAX_IMAGE_BYTES:
                logger.debug(f"Image too large after download: {url}")
                return None

            # Open and process with PIL
            image = Image.open(io.BytesIO(image_data))

            # Skip very small images
            if image.size[0] < 100 or image.size[1] < 100:
                return None

            # Convert to RGB if needed
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])
                image = background
            elif image.mode not in ['RGB', 'L']:
                image = image.convert('RGB')

            # Resize if too large
            if image.size[0] > self.MAX_IMAGE_SIZE[0] or image.size[1] > self.MAX_IMAGE_SIZE[1]:
                image.thumbnail(self.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)

            # Generate filename
            ext = '.jpg'  # Standardize to JPEG
            filename = f"{page_hash}_{index}{ext}"
            filepath = os.path.join(self.image_storage_path, filename)

            # Save image
            image.save(filepath, 'JPEG', quality=85)

            # Generate base64 for inline use
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

    def _extract_structured_data(self, html: str, url: str) -> Dict:
        """
        Extract structured business/contact information from the page.

        Returns:
            Dict with owner, company, contact info, social links, etc.
        """
        soup = BeautifulSoup(html, 'html.parser')
        structured = {
            'company_name': None,
            'owner': None,
            'email': None,
            'phone': None,
            'address': None,
            'social_links': [],
            'legal_form': None,
            'vat_id': None,
            'registration': None
        }

        # Get all text for pattern matching
        full_text = soup.get_text(separator=' ', strip=True)

        # Extract emails
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, full_text)
        if emails:
            # Filter out common non-contact emails
            contact_emails = [e for e in emails if not any(x in e.lower() for x in ['noreply', 'no-reply', 'donotreply', 'example'])]
            if contact_emails:
                structured['email'] = contact_emails[0]

        # Extract phone numbers (German format)
        phone_patterns = [
            r'\+49\s*[\d\s/\-()]+',
            r'0\d{2,4}[\s/\-]?\d{3,}[\s/\-]?\d{2,}',
            r'Tel\.?:?\s*[\d\s/\-+()]+',
            r'Telefon:?\s*[\d\s/\-+()]+',
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, full_text)
            if phones:
                # Clean up the phone number
                phone = re.sub(r'[^\d+]', '', phones[0])
                if len(phone) >= 8:
                    structured['phone'] = phones[0].strip()
                    break

        # Look for Impressum/About sections for owner/company info
        impressum_patterns = [
            r'Inhaber:?\s*([A-ZÄÖÜa-zäöüß\s\-]+)',
            r'Geschäftsführer:?\s*([A-ZÄÖÜa-zäöüß\s\-]+)',
            r'Geschäftsführung:?\s*([A-ZÄÖÜa-zäöüß\s\-]+)',
            r'Verantwortlich:?\s*([A-ZÄÖÜa-zäöüß\s\-]+)',
            r'Vertretungsberechtig[te]+:?\s*([A-ZÄÖÜa-zäöüß\s\-]+)',
        ]
        for pattern in impressum_patterns:
            match = re.search(pattern, full_text)
            if match:
                owner = match.group(1).strip()
                # Filter out common false positives
                if len(owner) > 3 and not any(x in owner.lower() for x in ['gmbh', 'ag', 'gbr', 'ohg', 'kg']):
                    structured['owner'] = owner
                    break

        # Extract company name from various sources
        company_patterns = [
            r'([A-ZÄÖÜa-zäöüß\s\-&]+)\s+(?:GmbH|AG|GbR|OHG|KG|UG|e\.?K\.?)',
            r'Firma:?\s*([A-ZÄÖÜa-zäöüß\s\-&]+)',
        ]
        for pattern in company_patterns:
            match = re.search(pattern, full_text)
            if match:
                structured['company_name'] = match.group(0).strip()
                break

        # Look for VAT ID
        vat_pattern = r'USt\.?-?(?:Id\.?-?)?Nr\.?:?\s*(DE\s*\d{9})'
        vat_match = re.search(vat_pattern, full_text, re.IGNORECASE)
        if vat_match:
            structured['vat_id'] = vat_match.group(1).replace(' ', '')

        # Extract social media links
        social_domains = ['facebook.com', 'twitter.com', 'x.com', 'instagram.com', 'linkedin.com', 'xing.com', 'youtube.com']
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            for domain in social_domains:
                if domain in href:
                    structured['social_links'].append({
                        'platform': domain.split('.')[0],
                        'url': link['href']
                    })
                    break

        # Try to extract address
        address_patterns = [
            r'(\d{5}\s+[A-ZÄÖÜa-zäöüß\s\-]+)',  # PLZ + Stadt
            r'([A-ZÄÖÜa-zäöüß\s\-]+str(?:aße|\.)\s+\d+[a-z]?)',  # Straße + Nr
        ]
        address_parts = []
        for pattern in address_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                address_parts.extend(matches[:2])
        if address_parts:
            structured['address'] = ', '.join(address_parts[:2])

        return structured

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract and normalize all links from HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        links = []

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']

            # Skip javascript, mailto, tel links
            if href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                continue

            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)
            normalized = self._normalize_url(absolute_url)

            if normalized not in links:
                links.append(normalized)

        return links

    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a single page with error handling."""
        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type and 'application/xhtml' not in content_type:
                logger.debug(f"Skipping non-HTML content: {url}")
                return None

            self.stats['total_bytes'] += len(response.content)
            return response.text

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching {url}")
            self.stats['errors'] += 1
        except requests.exceptions.HTTPError as e:
            logger.warning(f"HTTP error {e.response.status_code} for {url}")
            self.stats['errors'] += 1
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error for {url}: {e}")
            self.stats['errors'] += 1

        return None

    def fetch_page_content(self, url: str) -> Optional[Dict]:
        """
        Fetch a single page and extract text, metadata, and images.
        Designed for worker usage in multi-threaded fetch.
        """
        html = self._fetch_page(url)
        if not html:
            return None

        text, metadata = self._extract_text(html, url)
        if not text or len(text) < 50:
            return None

        content_hash = hashlib.sha256(text.encode()).hexdigest()

        images = []
        if self.extract_images:
            images = self._extract_images(html, url, content_hash[:16])

        structured_data = self._extract_structured_data(html, url)

        page_data = {
            'url': url,
            'depth': 0,
            'content': text,
            'content_length': len(text),
            'content_hash': content_hash,
            'metadata': metadata,
            'structured_data': structured_data,
            'images': images,
            'crawled_at': datetime.now().isoformat(),
            'crawler_type': 'basic'
        }
        return page_data

    def crawl(self, progress_callback=None, page_callback=None) -> List[Dict]:
        """
        Execute the crawl starting from base_url.

        Args:
            progress_callback: Optional callback function(current, total, url)
            page_callback: Optional callback function(page_data) called for each page
                           immediately after it's crawled (for live document creation)

        Returns:
            List of crawled pages with content and metadata
        """
        self.stats['start_time'] = datetime.now()
        logger.info(f"Starting crawl of {self.base_url} (max {self.max_pages} pages, depth {self.max_depth})")

        # Load robots.txt
        self._load_robots_txt()

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

            # Mark as visited
            self.visited_urls.add(url)

            # Fetch page
            logger.info(f"Crawling [{len(self.crawled_pages)+1}/{self.max_pages}]: {url}")
            html = self._fetch_page(url)

            if html:
                # Extract content
                text, metadata = self._extract_text(html, url)

                if text and len(text) > 100:  # Minimum content threshold
                    content_hash = hashlib.sha256(text.encode()).hexdigest()

                    # Extract images if enabled
                    images = []
                    if self.extract_images:
                        images = self._extract_images(html, url, content_hash[:16])

                    # Extract structured business data
                    structured_data = self._extract_structured_data(html, url)

                    # Enhance content with structured data if found
                    enhanced_content = text
                    if any(v for v in structured_data.values() if v and v != []):
                        structured_section = "\n\n## Kontaktinformationen\n"
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

                        # Insert before the source line
                        if "\n\n---\nQuelle:" in enhanced_content:
                            enhanced_content = enhanced_content.replace(
                                "\n\n---\nQuelle:",
                                f"{structured_section}\n\n---\nQuelle:"
                            )
                        else:
                            enhanced_content += structured_section

                    page_data = {
                        'url': url,
                        'depth': depth,
                        'content': enhanced_content,
                        'content_length': len(enhanced_content),
                        'content_hash': content_hash,
                        'metadata': metadata,
                        'structured_data': structured_data,
                        'images': images,
                        'crawled_at': datetime.now().isoformat()
                    }
                    self.crawled_pages.append(page_data)
                    self.stats['pages_crawled'] += 1

                    # Call page callback immediately for live document creation
                    if page_callback:
                        try:
                            page_callback(page_data)
                        except Exception as e:
                            logger.error(f"Error in page_callback for {url}: {e}")

                    # Extract and queue links
                    if depth < self.max_depth:
                        links = self._extract_links(html, url)
                        for link in links:
                            if link not in self.visited_urls:
                                queue.append((link, depth + 1))

                    if progress_callback:
                        progress_callback(
                            len(self.crawled_pages),
                            self.max_pages,
                            url
                        )
                else:
                    logger.debug(f"Skipping page with insufficient content: {url}")
                    self.stats['pages_skipped'] += 1

            # Polite delay
            time.sleep(self.delay_seconds)

        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

        logger.info(f"Crawl complete: {self.stats['pages_crawled']} pages in {duration:.1f}s")
        logger.info(f"Stats: {self.stats}")

        return self.crawled_pages

    def get_stats(self) -> Dict:
        """Return crawl statistics."""
        stats = self.stats.copy()
        if stats['start_time'] and stats['end_time']:
            stats['duration_seconds'] = (stats['end_time'] - stats['start_time']).total_seconds()
        return stats
