"""
Content Extraction Module

Handles text content and metadata extraction from web pages.
Includes regex-based structured data extraction as fallback.
Also extracts brand colors from websites.
"""

import re
import asyncio
import logging
from typing import Tuple, Dict, List, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from colorsys import rgb_to_hls

logger = logging.getLogger(__name__)


def _hex_to_rgb(hex_color: str) -> Optional[Tuple[int, int, int]]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    if len(hex_color) != 6:
        return None
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB to hex color."""
    return f'#{r:02x}{g:02x}{b:02x}'


def _is_valid_brand_color(r: int, g: int, b: int) -> bool:
    """
    Check if a color is suitable as a brand color.
    Excludes pure black, white, grays, browser defaults, and very dark/light colors.
    """
    # Exclude pure primary colors (often browser defaults)
    if (r == 0 and g == 0 and b > 200) or \
       (r > 200 and g == 0 and b == 0) or \
       (r == 0 and g > 200 and b == 0):
        return False

    # Exclude common browser default link colors
    hex_color = f"#{r:02x}{g:02x}{b:02x}".lower()
    browser_defaults = {
        '#0000ee', '#0000ff', '#0066cc',  # Browser default link colors
        '#551a8b', '#800080',              # Browser default visited link colors
        '#ff0000', '#ee0000',              # Pure red (often error states)
        '#00ff00', '#008000',              # Pure green (often success states)
        '#ffffff', '#000000',              # Pure white/black
        '#333333', '#666666', '#999999',   # Common text grays
    }
    if hex_color in browser_defaults:
        return False

    # Convert to HLS for saturation check
    h, l, s = rgb_to_hls(r / 255, g / 255, b / 255)

    # Exclude grays (low saturation) and extremes
    if s < 0.15:  # Too gray
        return False
    if l < 0.15 or l > 0.85:  # Too dark or too light
        return False

    # Exclude pure black/white/gray
    if abs(r - g) < 15 and abs(g - b) < 15 and abs(r - b) < 15:
        return False

    return True


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
    # Includes common CMS/theme-specific selectors (WordPress, Divi, Elementor, etc.)
    MAIN_SELECTORS = [
        'main', 'article', '[role="main"]',
        '.content', '.article', '.post-content', '.entry-content',
        # Divi Theme (Elegant Themes) - very common WordPress builder
        '.et_pb_section', '#et-main-area', '.et_pb_text',
        # Elementor
        '.elementor-widget-container', '.elementor-section',
        # WPBakery
        '.vc_row', '.wpb_wrapper',
        # Generic fallbacks
        '#content', '#main-content', '.main-content', '.page-content'
    ]

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

        # For page builders (Divi, Elementor), content is spread across multiple elements
        # Try combining all text elements if single selector didn't yield enough content
        if not text_content or len(text_content) < 200:
            combined_content = await self._extract_combined_page_builder_content(page, url)
            if combined_content and len(combined_content) > len(text_content or ''):
                text_content = combined_content
                logger.debug(f"Used combined page builder extraction: {len(text_content)} chars")

        # Fallback to body if no content found
        if not text_content or len(text_content) < 100:
            logger.debug("Using body fallback for content extraction")
            text_content = await self._fallback_body_extraction(page, url)

        return text_content

    async def _extract_combined_page_builder_content(self, page, url: str) -> str:
        """
        Extract content from page builders that spread text across many elements.
        Combines text from multiple Divi, Elementor, WPBakery modules.

        Args:
            page: Playwright page object
            url: URL (for logging)

        Returns:
            Combined text content
        """
        page_builder_selectors = [
            # Divi text modules
            '.et_pb_text_inner',
            '.et_pb_blurb_description',
            '.et_pb_slide_description',
            # Elementor widgets
            '.elementor-widget-text-editor',
            '.elementor-widget-heading',
            # WPBakery
            '.wpb_text_column',
            # Generic text containers
            '.text-content', '.text-block', 'p',
        ]

        all_texts = []

        try:
            for selector in page_builder_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements[:50]:  # Limit to prevent huge extractions
                        try:
                            text = await asyncio.wait_for(
                                element.inner_text(),
                                timeout=2.0
                            )
                            if text and len(text.strip()) > 20:  # Skip tiny snippets
                                all_texts.append(text.strip())
                        except Exception:
                            continue
                except Exception:
                    continue

            if all_texts:
                combined = '\n\n'.join(all_texts)
                logger.debug(f"Combined {len(all_texts)} page builder elements: {len(combined)} chars total")
                return combined

        except Exception as e:
            logger.debug(f"Error in combined page builder extraction: {e}")

        return ''

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

    async def extract_brand_color(self, page, url: str) -> Optional[str]:
        """
        Extract the primary/brand color from a website.

        Checks in order of priority:
        1. Meta theme-color tag
        2. CSS custom properties (--primary-color, --brand-color, etc.)
        3. Common brand element colors (header, primary buttons, links)

        Args:
            page: Playwright page object
            url: URL of the page

        Returns:
            Hex color string (e.g., '#ff5500') or None if not found
        """
        try:
            color = await page.evaluate('''() => {
                // Helper to parse color to hex
                function parseColor(color) {
                    if (!color || color === 'transparent' || color === 'inherit' || color === 'initial') {
                        return null;
                    }
                    // Already hex
                    if (color.startsWith('#')) {
                        let hex = color.slice(1);
                        if (hex.length === 3) {
                            hex = hex.split('').map(c => c + c).join('');
                        }
                        if (hex.length === 6 && /^[0-9a-fA-F]{6}$/.test(hex)) {
                            return '#' + hex.toLowerCase();
                        }
                        return null;
                    }
                    // RGB(A) format
                    const rgbMatch = color.match(/rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/i);
                    if (rgbMatch) {
                        const r = parseInt(rgbMatch[1]);
                        const g = parseInt(rgbMatch[2]);
                        const b = parseInt(rgbMatch[3]);
                        return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('').toLowerCase();
                    }
                    return null;
                }

                // Helper to check if color is a valid brand color (not gray/black/white/browser defaults)
                function isValidBrandColor(hex) {
                    if (!hex) return false;

                    // Blacklist of browser default colors and common non-brand colors
                    const browserDefaults = [
                        '#0000ee', '#0000ff', '#0066cc',  // Browser default link colors
                        '#551a8b', '#800080',              // Browser default visited link colors
                        '#ff0000', '#ee0000',              // Pure red (often error states)
                        '#00ff00', '#008000',              // Pure green (often success states)
                        '#ffffff', '#000000',              // Pure white/black
                        '#333333', '#666666', '#999999',   // Common text grays
                    ];
                    if (browserDefaults.includes(hex.toLowerCase())) return false;

                    const r = parseInt(hex.slice(1, 3), 16);
                    const g = parseInt(hex.slice(3, 5), 16);
                    const b = parseInt(hex.slice(5, 7), 16);

                    // Exclude pure primary colors (often browser defaults)
                    if ((r === 0 && g === 0 && b > 200) || // Pure blue
                        (r > 200 && g === 0 && b === 0) || // Pure red
                        (r === 0 && g > 200 && b === 0)) { // Pure green
                        return false;
                    }

                    // Convert to HSL for saturation check
                    const max = Math.max(r, g, b) / 255;
                    const min = Math.min(r, g, b) / 255;
                    const l = (max + min) / 2;
                    const s = max === min ? 0 : (l > 0.5 ? (max - min) / (2 - max - min) : (max - min) / (max + min));

                    // Exclude grays (low saturation) and extremes
                    if (s < 0.15) return false;
                    if (l < 0.15 || l > 0.85) return false;

                    // Exclude near-grays
                    if (Math.abs(r - g) < 15 && Math.abs(g - b) < 15 && Math.abs(r - b) < 15) return false;

                    return true;
                }

                // 1. Check meta theme-color (highest priority)
                const themeColor = document.querySelector('meta[name="theme-color"]');
                if (themeColor) {
                    const color = parseColor(themeColor.getAttribute('content'));
                    if (isValidBrandColor(color)) return color;
                }

                // 2. Check CSS custom properties
                const root = document.documentElement;
                const computedStyle = getComputedStyle(root);
                const cssVarNames = [
                    '--primary-color', '--primary', '--brand-color', '--brand',
                    '--main-color', '--accent-color', '--theme-color',
                    '--color-primary', '--color-brand', '--wp-admin-theme-color',
                    '--global-palette1'  // Kadence theme
                ];
                for (const varName of cssVarNames) {
                    const value = computedStyle.getPropertyValue(varName).trim();
                    if (value) {
                        const color = parseColor(value);
                        if (isValidBrandColor(color)) return color;
                    }
                }

                // 3. Check common brand elements
                const brandSelectors = [
                    'header', 'nav', '.navbar', '.header',
                    '.site-header', '#masthead', '.menu-primary',
                    'a', '.btn-primary', '.button-primary', '[class*="primary"]',
                    '.logo', '.brand', '.site-title'
                ];

                const colorCounts = {};

                for (const selector of brandSelectors) {
                    try {
                        const elements = document.querySelectorAll(selector);
                        for (const el of [...elements].slice(0, 10)) {
                            const style = getComputedStyle(el);

                            // Check background-color
                            let color = parseColor(style.backgroundColor);
                            if (isValidBrandColor(color)) {
                                colorCounts[color] = (colorCounts[color] || 0) + 2;
                            }

                            // Check color (text color, especially for links)
                            color = parseColor(style.color);
                            if (isValidBrandColor(color)) {
                                colorCounts[color] = (colorCounts[color] || 0) + 1;
                            }

                            // Check border-color
                            color = parseColor(style.borderColor);
                            if (isValidBrandColor(color)) {
                                colorCounts[color] = (colorCounts[color] || 0) + 1;
                            }
                        }
                    } catch (e) {}
                }

                // Return most common valid brand color
                const sortedColors = Object.entries(colorCounts)
                    .sort((a, b) => b[1] - a[1]);

                if (sortedColors.length > 0) {
                    return sortedColors[0][0];
                }

                return null;
            }''')

            if color:
                # Validate the color on backend too
                rgb = _hex_to_rgb(color)
                if rgb and _is_valid_brand_color(*rgb):
                    logger.debug(f"Extracted brand color from {url}: {color}")
                    return color

        except Exception as e:
            logger.debug(f"Error extracting brand color from {url}: {e}")

        return None
