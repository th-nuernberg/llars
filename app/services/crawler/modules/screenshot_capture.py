"""
Screenshot Capture Module

Handles Playwright screenshot functionality including full-page captures,
image processing, and base64 encoding for Vision-LLM integration.
"""

import io
import os
import base64
import logging
from typing import Optional, Dict
from PIL import Image

logger = logging.getLogger(__name__)


class ScreenshotCapture:
    """
    Handles screenshot capture and processing for web pages.

    Responsibilities:
    - Capture full-page screenshots using Playwright
    - Process screenshots with PIL (RGB conversion, optimization)
    - Generate base64-encoded versions for Vision-LLM
    - Save screenshots to storage with proper naming
    """

    # Screenshot settings
    SCREENSHOT_WIDTH = 1920
    SCREENSHOT_HEIGHT = 1080
    FULL_PAGE_SCREENSHOT = True

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
            # Wait for page to be fully loaded
            await page.wait_for_load_state('networkidle', timeout=10000)

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
