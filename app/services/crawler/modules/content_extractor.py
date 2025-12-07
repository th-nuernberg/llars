"""
Content Extraction Module

Handles text content and metadata extraction from web pages.
Includes regex-based structured data extraction as fallback.
"""

import re
import asyncio
import logging
from typing import Tuple, Dict, List, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ContentExtractor:
    """
    Extracts text content, metadata, and structured data from web pages.

    Responsibilities:
    - Extract page title, description, and meta tags
    - Remove unwanted elements (scripts, styles, popups)
    - Extract main content with intelligent selector fallback
    - Regex-based structured data extraction (email, phone, address, etc.)
    - Link extraction from rendered pages
    """

    # Content selectors (ordered by priority)
    MAIN_SELECTORS = ['main', 'article', '[role="main"]', '.content', '.article']

    # Elements to remove (not content)
    SAFE_REMOVAL_SELECTORS = [
        'script', 'style', 'noscript', 'iframe',
        '[class*="cookie-banner"]', '[class*="cookie-notice"]',
        '[class*="gdpr"]', '[id*="cookie"]',
        '[class*="popup"]', '[class*="modal"]',
        '[aria-hidden="true"]'
    ]

    def __init__(self):
        """Initialize the content extractor."""
        pass

    async def extract_text_content(self, page, url: str) -> Tuple[str, Dict]:
        """
        Extract text content and metadata from the rendered page.

        Args:
            page: Playwright page object
            url: URL of the page

        Returns:
            Tuple of (formatted_text_content, metadata_dict)
        """
        metadata = {
            'url': url,
            'title': '',
            'description': '',
            'keywords': '',
            'language': 'de',
            'author': ''
        }

        try:
            # Extract metadata
            metadata = await self._extract_metadata(page, url)

            # Remove unwanted elements
            await self._remove_unwanted_elements(page, url)

            # Extract main content
            text_content = await self._extract_main_content(page, url)

            if not text_content:
                return '', metadata

            # Clean up whitespace
            text_content = self._clean_text(text_content)

            # Format with title and source
            formatted = self._format_content(text_content, metadata, url)

            return formatted.strip(), metadata

        except Exception as e:
            logger.warning(f"Error extracting text from {url}: {e}")
            return '', metadata

    async def _extract_metadata(self, page, url: str) -> Dict:
        """
        Extract metadata from page (title, description, etc.).

        Args:
            page: Playwright page object
            url: URL of the page

        Returns:
            Dict with metadata fields
        """
        metadata = {
            'url': url,
            'title': '',
            'description': '',
            'keywords': '',
            'language': 'de',
            'author': ''
        }

        # Get title
        try:
            title = await page.title()
            metadata['title'] = title or ''
        except Exception:
            metadata['title'] = ''

        # Get meta description
        try:
            meta_desc = await page.query_selector('meta[name="description"]')
            if meta_desc:
                metadata['description'] = await meta_desc.get_attribute('content') or ''
        except Exception:
            pass

        return metadata

    async def _remove_unwanted_elements(self, page, url: str):
        """
        Remove non-content elements from the page.

        Args:
            page: Playwright page object
            url: URL (for logging)
        """
        try:
            await asyncio.wait_for(
                page.evaluate(f'''() => {{
                    const safeSelectors = {self.SAFE_REMOVAL_SELECTORS};
                    safeSelectors.forEach(selector => {{
                        try {{
                            document.querySelectorAll(selector).forEach(el => el.remove());
                        }} catch(e) {{}}
                    }});
                }}'''),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.debug(f"Timeout removing unwanted elements for {url}")
        except Exception as e:
            logger.debug(f"Error removing elements: {e}")

    async def _extract_main_content(self, page, url: str) -> str:
        """
        Extract main text content with intelligent fallback.

        Args:
            page: Playwright page object
            url: URL (for logging)

        Returns:
            Extracted text content
        """
        text_content = ''

        # Try main content selectors first
        for selector in self.MAIN_SELECTORS:
            try:
                element = await page.query_selector(selector)
                if element:
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
            text_content = await self._fallback_body_extraction(page, url)

        return text_content

    async def _fallback_body_extraction(self, page, url: str) -> str:
        """
        Fallback extraction using body or BeautifulSoup.

        Args:
            page: Playwright page object
            url: URL (for logging)

        Returns:
            Extracted text content
        """
        try:
            text_content = await asyncio.wait_for(
                page.evaluate('() => document.body ? document.body.innerText : ""'),
                timeout=15.0
            )
            logger.debug(f"Body fallback extracted: {len(text_content)} chars")
            return text_content
        except asyncio.TimeoutError:
            logger.warning(f"Timeout extracting body text from {url}")
            # Last resort: BeautifulSoup on HTML
            return await self._beautifulsoup_extraction(page)
        except Exception as e:
            logger.warning(f"Error in fallback body extraction: {e}")
            return ''

    async def _beautifulsoup_extraction(self, page) -> str:
        """
        Last resort: Use BeautifulSoup to extract text from HTML.

        Args:
            page: Playwright page object

        Returns:
            Extracted text content
        """
        try:
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            text_content = soup.get_text(separator=' ', strip=True)
            logger.debug(f"BeautifulSoup fallback extracted: {len(text_content)} chars")
            return text_content
        except Exception:
            return ''

    def _clean_text(self, text: str) -> str:
        """
        Clean up whitespace and formatting in text.

        Args:
            text: Raw text content

        Returns:
            Cleaned text
        """
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove excessive spaces
        text = re.sub(r' {2,}', ' ', text)
        return text

    def _format_content(self, text_content: str, metadata: Dict, url: str) -> str:
        """
        Format content with title and source information.

        Args:
            text_content: Extracted text
            metadata: Page metadata
            url: Page URL

        Returns:
            Formatted content string
        """
        if metadata['title']:
            formatted = f"# {metadata['title']}\n\n{text_content}"
        else:
            formatted = text_content

        formatted += f"\n\n---\nQuelle: {url}\n"
        return formatted

    async def extract_links(self, page, url: str) -> List[str]:
        """
        Extract all links from the rendered page.

        Args:
            page: Playwright page object
            url: Base URL for resolving relative links

        Returns:
            List of absolute URLs
        """
        links = []

        try:
            link_elements = await page.query_selector_all('a[href]')

            for link in link_elements:
                try:
                    href = await link.get_attribute('href')
                    if not href or href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                        continue

                    absolute_url = urljoin(url, href)
                    if absolute_url not in links:
                        links.append(absolute_url)

                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"Error extracting links from {url}: {e}")

        return links

    def extract_structured_data_regex(self, html: str, url: str) -> Dict:
        """
        Fallback: Extract structured data using regex patterns.
        Used when Vision-LLM is disabled or fails.

        Args:
            html: Raw HTML content
            url: URL (for logging)

        Returns:
            Dict with extracted structured fields
        """
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

        # Email extraction
        structured['email'] = self._extract_email(full_text)

        # Phone extraction (German format)
        structured['phone'] = self._extract_phone(full_text)

        # Owner extraction
        structured['owner'] = self._extract_owner(full_text)

        # Company name extraction
        structured['company_name'] = self._extract_company_name(full_text)

        # VAT ID extraction
        structured['vat_id'] = self._extract_vat_id(full_text)

        # Address extraction
        structured['address'] = self._extract_address(full_text)

        return structured

    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address from text."""
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        contact_emails = [
            e for e in emails
            if not any(x in e.lower() for x in ['noreply', 'no-reply', 'example'])
        ]
        return contact_emails[0] if contact_emails else None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text (German format)."""
        phone_patterns = [
            r'\+49\s*[\d\s/\-()]+',
            r'0\d{2,4}[\s/\-]?\d{3,}[\s/\-]?\d{2,}',
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                return phones[0].strip()
        return None

    def _extract_owner(self, text: str) -> Optional[str]:
        """Extract owner/CEO name from text."""
        owner_patterns = [
            r'Inhaber[:\s]+([A-ZÄÖÜa-zäöüß][a-zäöüß]+\s+[A-ZÄÖÜa-zäöüß][a-zäöüß]+)',
            r'Geschäftsführer[:\s]+([A-ZÄÖÜa-zäöüß][a-zäöüß]+\s+[A-ZÄÖÜa-zäöüß][a-zäöüß]+)',
            r'Geschäftsführung[:\s]+([A-ZÄÖÜa-zäöüß][a-zäöüß]+\s+[A-ZÄÖÜa-zäöüß][a-zäöüß]+)',
        ]
        for pattern in owner_patterns:
            match = re.search(pattern, text)
            if match:
                owner = match.group(1).strip()
                if len(owner.split()) >= 2:  # At least first and last name
                    return owner
        return None

    def _extract_company_name(self, text: str) -> Optional[str]:
        """Extract company name from text."""
        company_patterns = [
            r'([A-ZÄÖÜa-zäöüß\s\-&]+(?:GmbH|AG|GbR|OHG|KG|UG|e\.?K\.?))',
        ]
        for pattern in company_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return None

    def _extract_vat_id(self, text: str) -> Optional[str]:
        """Extract VAT ID from text."""
        vat_match = re.search(r'USt\.?-?(?:Id\.?-?)?Nr\.?:?\s*(DE\s*\d{9})', text, re.IGNORECASE)
        if vat_match:
            return vat_match.group(1).replace(' ', '')
        return None

    def _extract_address(self, text: str) -> Optional[str]:
        """Extract address from text."""
        address_patterns = [
            r'(\d{5}\s+[A-ZÄÖÜa-zäöüß\-]+)',
            r'([A-ZÄÖÜa-zäöüß]+str(?:aße|\.)\s+\d+[a-z]?)',
        ]
        address_parts = []
        for pattern in address_patterns:
            matches = re.findall(pattern, text)
            address_parts.extend(matches[:2])
        if address_parts:
            return ', '.join(address_parts[:2])
        return None
