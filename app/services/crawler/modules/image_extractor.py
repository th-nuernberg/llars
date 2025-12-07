"""
Image Extraction Module

Handles extraction, downloading, and processing of images from web pages.
Filters images by size, format, and quality requirements.
"""

import io
import os
import base64
import logging
from typing import List, Dict, Set, Optional
from urllib.parse import urljoin, urlparse
from PIL import Image

logger = logging.getLogger(__name__)


class ImageExtractor:
    """
    Extracts and processes images from web pages.

    Responsibilities:
    - Extract image elements from rendered pages
    - Download and validate images
    - Process images (resize, convert, optimize)
    - Filter images by size and format
    - Save images to storage
    """

    # Image settings
    SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    MAX_IMAGE_SIZE = (1024, 1024)
    MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5MB
    MIN_IMAGE_DIMENSION = 100  # Minimum width or height

    def __init__(
        self,
        image_storage_path: str = '/app/storage/rag_images',
        max_images_per_page: int = 10
    ):
        """
        Initialize the image extractor.

        Args:
            image_storage_path: Directory path for saving images
            max_images_per_page: Maximum number of images to extract per page
        """
        self.image_storage_path = image_storage_path
        self.max_images_per_page = max_images_per_page

        # Create storage directory
        if self.image_storage_path:
            os.makedirs(self.image_storage_path, exist_ok=True)

    async def extract_images_from_page(
        self,
        page,
        url: str,
        page_hash: str
    ) -> List[Dict]:
        """
        Extract all valid images from a rendered page.

        Args:
            page: Playwright page object
            url: URL of the page being crawled
            page_hash: Unique hash for the page content

        Returns:
            List of dicts containing image data (path, base64, dimensions, etc.)
        """
        images = []
        seen_urls: Set[str] = set()

        try:
            img_elements = await page.query_selector_all('img[src]')

            # Get more elements than needed to allow for filtering
            for img in img_elements[:self.max_images_per_page * 2]:
                if len(images) >= self.max_images_per_page:
                    break

                try:
                    src = await img.get_attribute('src')
                    alt = await img.get_attribute('alt') or ''

                    # Skip invalid or tracking pixels
                    if not src or src.startswith('data:') or 'pixel' in src.lower():
                        continue

                    # Get dimensions from rendered element
                    box = await img.bounding_box()
                    if box and (box['width'] < self.MIN_IMAGE_DIMENSION or box['height'] < self.MIN_IMAGE_DIMENSION):
                        continue

                    # Resolve to absolute URL
                    absolute_url = urljoin(url, src)
                    if absolute_url in seen_urls:
                        continue
                    seen_urls.add(absolute_url)

                    # Check file extension
                    ext = os.path.splitext(urlparse(absolute_url).path)[1].lower()
                    if ext not in self.SUPPORTED_IMAGE_FORMATS:
                        continue

                    # Download and process image
                    image_data = await self._fetch_and_process_image(
                        absolute_url,
                        page_hash,
                        len(images)
                    )

                    if image_data:
                        image_data['alt_text'] = alt
                        image_data['source_url'] = absolute_url
                        images.append(image_data)

                except Exception as e:
                    logger.debug(f"Error processing image element: {e}")
                    continue

        except Exception as e:
            logger.warning(f"Error extracting images from {url}: {e}")

        return images

    async def _fetch_and_process_image(
        self,
        url: str,
        page_hash: str,
        index: int
    ) -> Optional[Dict]:
        """
        Fetch and process a single image from URL.

        Args:
            url: Image URL to fetch
            page_hash: Unique hash for the page
            index: Image index on the page

        Returns:
            Dict with image data or None if processing fails
        """
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        return None

                    # Check size before downloading
                    content_length = response.headers.get('Content-Length')
                    if content_length and int(content_length) > self.MAX_IMAGE_BYTES:
                        logger.debug(f"Image too large (Content-Length): {url}")
                        return None

                    # Download image data
                    image_data = await response.read()
                    if len(image_data) > self.MAX_IMAGE_BYTES:
                        logger.debug(f"Image too large (actual size): {url}")
                        return None

            # Process with PIL
            image = Image.open(io.BytesIO(image_data))

            # Validate dimensions
            if image.size[0] < self.MIN_IMAGE_DIMENSION or image.size[1] < self.MIN_IMAGE_DIMENSION:
                logger.debug(f"Image too small: {url}")
                return None

            # Convert to RGB
            image = self._convert_to_rgb(image)

            # Resize if needed
            if image.size[0] > self.MAX_IMAGE_SIZE[0] or image.size[1] > self.MAX_IMAGE_SIZE[1]:
                image.thumbnail(self.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)

            # Save to storage
            filename = f"{page_hash[:16]}_{index}.jpg"
            filepath = os.path.join(self.image_storage_path, filename)
            image.save(filepath, 'JPEG', quality=85)

            # Generate base64
            base64_data = self._generate_base64(image)

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

    def _convert_to_rgb(self, image: Image.Image) -> Image.Image:
        """
        Convert image to RGB format, handling transparency.

        Args:
            image: PIL Image object

        Returns:
            RGB PIL Image
        """
        if image.mode == 'RGBA':
            # Create white background for transparent images
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            return background
        elif image.mode not in ['RGB', 'L']:
            return image.convert('RGB')
        return image

    def _generate_base64(self, image: Image.Image) -> str:
        """
        Generate base64-encoded JPEG.

        Args:
            image: PIL Image object

        Returns:
            Base64-encoded string
        """
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=85)
        base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return base64_data
