"""
Link Preview Service for Messaging.

Extracts URLs from message text, fetches Open Graph metadata,
and caches results in the MessagingLinkPreview table.
"""

import hashlib
import ipaddress
import logging
import re
import socket
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from db import db
from db.models.messaging import MessagingLinkPreview, MessagingMessage

logger = logging.getLogger(__name__)

URL_REGEX = re.compile(r'https?://[^\s<>\[\](){}\'",;]+', re.IGNORECASE)
MAX_URLS_PER_MESSAGE = 5
FETCH_TIMEOUT = 5
MAX_CONTENT_BYTES = 512 * 1024  # 512 KB
CACHE_TTL_HOURS = 24
USER_AGENT = "LLARS-LinkPreview/1.0 (+https://llars.app)"


def extract_urls(text: str) -> list[str]:
    """Extract up to MAX_URLS_PER_MESSAGE URLs from text."""
    if not text:
        return []

    matches = URL_REGEX.findall(text)
    # Strip trailing punctuation
    cleaned = []
    for url in matches:
        url = re.sub(r'[.,;:!?)]+$', '', url)
        if url and url not in cleaned:
            cleaned.append(url)
        if len(cleaned) >= MAX_URLS_PER_MESSAGE:
            break
    return cleaned


def _is_safe_url(url: str) -> bool:
    """
    SSRF protection: reject URLs pointing to localhost, private IPs, or non-http schemes.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        # Block obvious localhost names
        if hostname in ('localhost', '127.0.0.1', '::1', '0.0.0.0'):
            return False

        # Resolve hostname and check for private IPs
        try:
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            for family, _type, _proto, _canonname, sockaddr in addr_info:
                ip = ipaddress.ip_address(sockaddr[0])
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    return False
        except (socket.gaierror, ValueError):
            return False

        return True
    except Exception:
        return False


def _fetch_og_metadata(url: str) -> Optional[dict]:
    """
    Fetch and parse Open Graph metadata from a URL.

    Returns dict with keys: title, description, image_url, site_name, favicon_url
    or None on failure.
    """
    try:
        resp = requests.get(
            url,
            timeout=FETCH_TIMEOUT,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html",
            },
            stream=True,
            allow_redirects=True,
        )

        # Only process HTML responses
        content_type = resp.headers.get("Content-Type", "")
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return None

        # Read limited content
        content = resp.raw.read(MAX_CONTENT_BYTES, decode_content=True)
        resp.close()

        soup = BeautifulSoup(content, "html.parser")
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        def get_og(prop: str) -> Optional[str]:
            tag = soup.find("meta", property=f"og:{prop}")
            if tag:
                return tag.get("content", "").strip() or None
            return None

        title = get_og("title")
        if not title:
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else None

        description = get_og("description")
        if not description:
            meta_desc = soup.find("meta", attrs={"name": "description"})
            description = meta_desc.get("content", "").strip() if meta_desc else None

        image_url = get_og("image")
        if image_url and image_url.startswith("/"):
            image_url = base_url + image_url

        site_name = get_og("site_name")

        # Favicon
        favicon_url = None
        icon_link = soup.find("link", rel=lambda x: x and "icon" in x)
        if icon_link and icon_link.get("href"):
            favicon_url = icon_link["href"]
            if favicon_url.startswith("/"):
                favicon_url = base_url + favicon_url

        if not title and not description:
            return None

        return {
            "title": (title or "")[:300],
            "description": (description or "")[:500],
            "image_url": (image_url or "")[:2000] or None,
            "site_name": (site_name or "")[:200] or None,
            "favicon_url": (favicon_url or "")[:2000] or None,
        }

    except requests.RequestException as exc:
        logger.debug("[LinkPreview] Fetch failed for %s: %s", url, exc)
        return None
    except Exception as exc:
        logger.warning("[LinkPreview] Parse error for %s: %s", url, exc)
        return None


def _url_hash(url: str) -> str:
    """SHA-256 hash of a URL for cache lookup."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def fetch_and_cache_preview(url: str) -> Optional[dict]:
    """
    Fetch OG metadata for a URL, using the DB cache (24h TTL).

    Returns a dict suitable for JSON storage, or None.
    """
    url_h = _url_hash(url)

    # Check cache
    cached = MessagingLinkPreview.query.filter_by(url_hash=url_h).first()
    if cached:
        age = datetime.utcnow() - cached.fetched_at
        if age < timedelta(hours=CACHE_TTL_HOURS):
            if cached.fetch_error:
                return None
            return {
                "url": cached.url,
                "title": cached.title,
                "description": cached.description,
                "image_url": cached.image_url,
                "site_name": cached.site_name,
                "favicon_url": cached.favicon_url,
            }
        # Expired — will re-fetch below

    # SSRF check
    if not _is_safe_url(url):
        logger.info("[LinkPreview] Blocked unsafe URL: %s", url)
        return None

    meta = _fetch_og_metadata(url)

    # Upsert cache row
    if cached:
        cached.fetched_at = datetime.utcnow()
        if meta:
            cached.title = meta["title"]
            cached.description = meta["description"]
            cached.image_url = meta["image_url"]
            cached.site_name = meta["site_name"]
            cached.favicon_url = meta["favicon_url"]
            cached.fetch_error = None
        else:
            cached.fetch_error = "No metadata found"
    else:
        preview = MessagingLinkPreview(
            url_hash=url_h,
            url=url[:2000],
            title=meta["title"] if meta else None,
            description=meta["description"] if meta else None,
            image_url=meta["image_url"] if meta else None,
            site_name=meta["site_name"] if meta else None,
            favicon_url=meta["favicon_url"] if meta else None,
            fetched_at=datetime.utcnow(),
            fetch_error=None if meta else "No metadata found",
        )
        db.session.add(preview)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

    if not meta:
        return None

    return {
        "url": url,
        "title": meta["title"],
        "description": meta["description"],
        "image_url": meta["image_url"],
        "site_name": meta["site_name"],
        "favicon_url": meta["favicon_url"],
    }


def process_message_links(message_id: int) -> Optional[list]:
    """
    Extract URLs from a message, fetch previews, and store them on the message.

    Returns the list of preview dicts, or None if no previews.
    """
    msg = MessagingMessage.query.get(message_id)
    if not msg or not msg.content or msg.is_deleted or msg.is_encrypted:
        return None

    urls = extract_urls(msg.content)
    if not urls:
        return None

    previews = []
    for url in urls:
        preview = fetch_and_cache_preview(url)
        if preview:
            previews.append(preview)

    if previews:
        msg.link_previews = previews
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return None

    return previews or None
