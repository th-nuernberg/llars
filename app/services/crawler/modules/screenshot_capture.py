"""
Screenshot Capture Module

Handles Playwright screenshot functionality including full-page captures,
image processing, and base64 encoding for Vision-LLM integration.

Supports splitting long pages into multiple viewport-sized screenshots.
"""

import io
import os
import base64
import logging
import math
from typing import Optional, Dict, List
from PIL import Image

logger = logging.getLogger(__name__)


class ScreenshotCapture:
    """
    Handles screenshot capture and processing for web pages.

    Responsibilities:
    - Capture full-page screenshots using Playwright
    - Split long pages into multiple viewport-sized screenshots
    - Process screenshots with PIL (RGB conversion, optimization)
    - Generate base64-encoded versions for Vision-LLM
    - Save screenshots to storage with proper naming
    """

    # Screenshot settings
    SCREENSHOT_WIDTH = 1280
    SCREENSHOT_HEIGHT = 800
    FULL_PAGE_SCREENSHOT = False  # Viewport only for browser-like screenshots

    # Multi-screenshot settings for long pages
    MAX_SINGLE_PAGE_HEIGHT = 4000  # Above this, split into multiple screenshots
    VIEWPORT_OVERLAP = 100  # Overlap between screenshots to avoid cutting content

    # Vision-LLM image constraints
    MAX_VISION_SIZE = 2048
    VISION_JPEG_QUALITY = 85

    def __init__(self, screenshot_storage_path: str = '/app/storage/screenshots'):
        """
        Initialize the screenshot capture module.

        Args:
            screenshot_storage_path: Directory path for saving screenshots
        """
        self.screenshot_storage_path = screenshot_storage_path

        # Create storage directory
        if self.screenshot_storage_path:
            os.makedirs(self.screenshot_storage_path, exist_ok=True)

    async def _wait_for_styles(self, page) -> None:
        """
        Wait for CSS and fonts to be fully loaded.

        Args:
            page: Playwright page object
        """
        try:
            # Ensure full load event fired
            await page.wait_for_load_state('load', timeout=20000)
        except Exception:
            pass  # Continue even if load times out

        try:
            # Wait for networkidle (CSS, fonts, images loaded)
            await page.wait_for_load_state('networkidle', timeout=20000)
        except Exception:
            pass  # Continue even if networkidle times out

        # Wait for fonts to load
        try:
            await page.evaluate('''() => {
                return document.fonts.ready;
            }''')
        except Exception:
            pass

        # Wait for any lazy-loaded styles
        try:
            await page.evaluate('''() => {
                return new Promise((resolve) => {
                    // Check if stylesheets are loaded
                    const styleSheets = document.styleSheets;
                    let loaded = true;
                    for (let i = 0; i < styleSheets.length; i++) {
                        try {
                            // Access rules to check if loaded
                            const rules = styleSheets[i].cssRules;
                        } catch (e) {
                            // Cross-origin stylesheet, skip
                        }
                    }
                    // Small delay to ensure styles are applied
                    setTimeout(resolve, 1000);
                });
            }''')
        except Exception:
            pass

    async def capture_page(
        self,
        page,
        url: str,
        page_hash: str,
        full_page: bool = True
    ) -> Optional[Dict]:
        """
        Capture a screenshot of the current page.

        Args:
            page: Playwright page object
            url: URL of the page being captured
            page_hash: Unique hash for the page content
            full_page: Whether to capture the full page or just viewport

        Returns:
            Dict with screenshot_path, base64_data, mime_type, width, height
            None if capture fails
        """
        try:
            # Wait for CSS and fonts to be fully loaded
            await self._wait_for_styles(page)

            # Take screenshot
            screenshot_bytes = await page.screenshot(
                full_page=full_page if full_page is not None else self.FULL_PAGE_SCREENSHOT,
                type='png'
            )

            # Process with PIL
            image = Image.open(io.BytesIO(screenshot_bytes))

            # Convert to RGB
            image = self._convert_to_rgb(image)

            # Save full-size screenshot as PNG
            filename = f"screenshot_{page_hash[:16]}.png"
            filepath = os.path.join(self.screenshot_storage_path, filename)
            image.save(filepath, 'PNG', optimize=True)

            # Create smaller version for Vision-LLM
            base64_data = self._create_vision_image(image)

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

    def _convert_to_rgb(self, image: Image.Image) -> Image.Image:
        """
        Convert image to RGB format.

        Args:
            image: PIL Image object

        Returns:
            RGB PIL Image
        """
        if image.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            return background
        elif image.mode != 'RGB':
            return image.convert('RGB')
        return image

    def _create_vision_image(self, image: Image.Image) -> str:
        """
        Create a base64-encoded JPEG optimized for Vision-LLM.

        Args:
            image: PIL Image object

        Returns:
            Base64-encoded JPEG string
        """
        # Create copy for resizing
        vision_image = image.copy()

        # Resize if needed (max 2048x2048 for most Vision-LLMs)
        if vision_image.size[0] > self.MAX_VISION_SIZE or vision_image.size[1] > self.MAX_VISION_SIZE:
            vision_image.thumbnail((self.MAX_VISION_SIZE, self.MAX_VISION_SIZE), Image.Resampling.LANCZOS)

        # Generate base64 JPEG
        buffer = io.BytesIO()
        vision_image.save(buffer, format='JPEG', quality=self.VISION_JPEG_QUALITY)
        base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return base64_data

    async def capture_full_page(self, page, url: str, page_hash: str) -> Optional[Dict]:
        """
        Capture a full-page screenshot (convenience method).

        Args:
            page: Playwright page object
            url: URL of the page being captured
            page_hash: Unique hash for the page content

        Returns:
            Dict with screenshot data or None if capture fails
        """
        return await self.capture_page(page, url, page_hash, full_page=True)

    async def capture_viewport(self, page, url: str, page_hash: str) -> Optional[Dict]:
        """
        Capture only the viewport (convenience method).

        Args:
            page: Playwright page object
            url: URL of the page being captured
            page_hash: Unique hash for the page content

        Returns:
            Dict with screenshot data or None if capture fails
        """
        return await self.capture_page(page, url, page_hash, full_page=False)

    async def capture_long_page(
        self,
        page,
        url: str,
        page_hash: str,
        viewport_height: int = 800
    ) -> Optional[Dict]:
        """
        Capture a long page by splitting it into multiple viewport-sized screenshots.

        For pages taller than MAX_SINGLE_PAGE_HEIGHT, this method scrolls through
        the page and captures multiple screenshots, returning them as an array.

        Args:
            page: Playwright page object
            url: URL of the page being captured
            page_hash: Unique hash for the page content
            viewport_height: Height of the viewport for each screenshot

        Returns:
            Dict with:
                - screenshot_path: Path to first/main screenshot
                - screenshots: List of all screenshot data (for long pages)
                - base64_data: Base64 of first screenshot (for Vision-LLM)
                - base64_data_all: List of base64 for all screenshots
                - mime_type, width, height, total_height, screenshot_count
            None if capture fails
        """
        try:
            # Wait for CSS and fonts to be fully loaded
            await self._wait_for_styles(page)

            # Get the full page height
            page_height = await page.evaluate('() => document.documentElement.scrollHeight')
            viewport_width = await page.evaluate('() => window.innerWidth')

            logger.info(f"Page height for {url}: {page_height}px")

            # If page is short enough, use single full-page screenshot
            if page_height <= self.MAX_SINGLE_PAGE_HEIGHT:
                result = await self.capture_page(page, url, page_hash, full_page=True)
                if result:
                    result['screenshots'] = [result]
                    result['base64_data_all'] = [result['base64_data']]
                    result['total_height'] = result['height']
                    result['screenshot_count'] = 1
                return result

            # For long pages, capture multiple viewport screenshots
            screenshots = []
            base64_list = []
            filepaths = []

            # Calculate number of screenshots needed
            effective_height = viewport_height - self.VIEWPORT_OVERLAP
            num_screenshots = math.ceil(page_height / effective_height)
            num_screenshots = min(num_screenshots, 20)  # Limit to 20 screenshots max

            logger.info(f"Capturing {num_screenshots} screenshots for long page: {url}")

            for i in range(num_screenshots):
                scroll_y = i * effective_height

                # Scroll to position
                await page.evaluate(f'window.scrollTo(0, {scroll_y})')

                # Wait for any lazy-loaded content
                await page.wait_for_timeout(800)

                # Take viewport screenshot
                screenshot_bytes = await page.screenshot(
                    full_page=False,
                    type='png'
                )

                # Process with PIL
                image = Image.open(io.BytesIO(screenshot_bytes))
                image = self._convert_to_rgb(image)

                # Save screenshot
                filename = f"screenshot_{page_hash[:16]}_{i+1:02d}.png"
                filepath = os.path.join(self.screenshot_storage_path, filename)
                image.save(filepath, 'PNG', optimize=True)
                filepaths.append(filepath)

                # Create base64 for Vision-LLM
                base64_data = self._create_vision_image(image)
                base64_list.append(base64_data)

                screenshot_data = {
                    'screenshot_path': filepath,
                    'base64_data': base64_data,
                    'mime_type': 'image/jpeg',
                    'width': image.size[0],
                    'height': image.size[1],
                    'scroll_position': scroll_y,
                    'index': i + 1
                }
                screenshots.append(screenshot_data)

            # Scroll back to top
            await page.evaluate('window.scrollTo(0, 0)')

            return {
                'screenshot_path': filepaths[0] if filepaths else None,
                'screenshots': screenshots,
                'base64_data': base64_list[0] if base64_list else None,
                'base64_data_all': base64_list,
                'mime_type': 'image/jpeg',
                'width': viewport_width,
                'height': viewport_height,
                'total_height': page_height,
                'screenshot_count': len(screenshots)
            }

        except Exception as e:
            logger.warning(f"Failed to capture long page screenshots for {url}: {e}")
            # Fallback to single screenshot
            return await self.capture_page(page, url, page_hash, full_page=True)
