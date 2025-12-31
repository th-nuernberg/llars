"""
Zotero API Service

Handles all communication with the Zotero Web API v3.
Documentation: https://www.zotero.org/support/dev/web_api/v3/basics
"""

import logging
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)

ZOTERO_API_BASE = "https://api.zotero.org"
ZOTERO_API_VERSION = 3
DEFAULT_TIMEOUT = 30
MAX_ITEMS_PER_REQUEST = 100  # Zotero API limit


@dataclass
class ZoteroLibrary:
    """Represents a Zotero library (user or group)."""
    library_type: str  # "user" or "group"
    library_id: str
    name: str
    description: Optional[str] = None
    is_owner: bool = False


@dataclass
class ZoteroCollection:
    """Represents a Zotero collection within a library."""
    key: str
    name: str
    parent_key: Optional[str] = None
    num_items: int = 0


class ZoteroAPIError(Exception):
    """Exception for Zotero API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class ZoteroAPIService:
    """
    Service for interacting with the Zotero Web API.

    Usage:
        service = ZoteroAPIService(api_key="...")
        libraries = service.get_libraries(user_id="12345")
        bibtex = service.get_bibtex(library_type="user", library_id="12345")
    """

    def __init__(self, api_key: str):
        """
        Initialize the Zotero API service.

        Args:
            api_key: Zotero API key for authentication
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Zotero-API-Key": api_key,
            "Zotero-API-Version": str(ZOTERO_API_VERSION),
        })

    def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = DEFAULT_TIMEOUT,
        raw_response: bool = False,
    ) -> Any:
        """
        Make a request to the Zotero API.

        Args:
            endpoint: API endpoint (e.g., "/users/12345/items")
            params: Query parameters
            timeout: Request timeout in seconds
            raw_response: If True, return raw response text instead of JSON

        Returns:
            JSON response or raw text

        Raises:
            ZoteroAPIError: If the request fails
        """
        url = f"{ZOTERO_API_BASE}{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=timeout)

            # Handle backoff request from Zotero
            if "Backoff" in response.headers:
                backoff_seconds = int(response.headers["Backoff"])
                logger.warning(f"Zotero API backoff requested: {backoff_seconds}s")
                time.sleep(min(backoff_seconds, 10))  # Max 10s wait

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise ZoteroAPIError(
                    f"Rate limited. Retry after {retry_after}s",
                    status_code=429,
                )

            if response.status_code == 403:
                raise ZoteroAPIError(
                    "Access denied. API key may be invalid or lack permissions.",
                    status_code=403,
                )

            if response.status_code == 404:
                raise ZoteroAPIError(
                    f"Resource not found: {endpoint}",
                    status_code=404,
                )

            response.raise_for_status()

            if raw_response:
                return response.text

            # Return JSON for non-bibtex responses
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return response.json()
            return response.text

        except requests.exceptions.Timeout:
            raise ZoteroAPIError(f"Request timeout after {timeout}s")
        except requests.exceptions.RequestException as e:
            raise ZoteroAPIError(f"Request failed: {str(e)}")

    def verify_connection(self) -> Dict[str, Any]:
        """
        Verify that the API key is valid and get user info.

        Returns:
            Dict with user info including userID and username

        Raises:
            ZoteroAPIError: If verification fails
        """
        try:
            response = self._request("/keys/current")
            return {
                "user_id": str(response.get("userID", "")),
                "username": response.get("username", ""),
                "access": response.get("access", {}),
            }
        except ZoteroAPIError:
            raise
        except Exception as e:
            raise ZoteroAPIError(f"Failed to verify API key: {str(e)}")

    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get information about a Zotero user."""
        return self._request(f"/users/{user_id}")

    def get_libraries(self, user_id: str) -> List[ZoteroLibrary]:
        """
        Get all libraries accessible to the user (personal + groups).

        Args:
            user_id: Zotero user ID

        Returns:
            List of ZoteroLibrary objects
        """
        libraries = []

        # Add user's personal library
        libraries.append(ZoteroLibrary(
            library_type="user",
            library_id=user_id,
            name="My Library",
            is_owner=True,
        ))

        # Fetch group libraries
        try:
            groups = self._request(f"/users/{user_id}/groups")
            for group in groups:
                libraries.append(ZoteroLibrary(
                    library_type="group",
                    library_id=str(group["id"]),
                    name=group["data"].get("name", f"Group {group['id']}"),
                    description=group["data"].get("description"),
                    is_owner=group["data"].get("owner") == int(user_id),
                ))
        except ZoteroAPIError as e:
            logger.warning(f"Failed to fetch groups for user {user_id}: {e}")

        return libraries

    def get_collections(
        self,
        library_type: str,
        library_id: str,
        parent_key: Optional[str] = None,
    ) -> List[ZoteroCollection]:
        """
        Get collections in a library.

        Args:
            library_type: "user" or "group"
            library_id: User or group ID
            parent_key: If set, only return subcollections of this collection

        Returns:
            List of ZoteroCollection objects
        """
        prefix = f"/{library_type}s/{library_id}"

        if parent_key:
            endpoint = f"{prefix}/collections/{parent_key}/collections"
        else:
            endpoint = f"{prefix}/collections"

        try:
            collections_data = self._request(endpoint)
            return [
                ZoteroCollection(
                    key=c["key"],
                    name=c["data"].get("name", "Unnamed"),
                    parent_key=c["data"].get("parentCollection"),
                    num_items=c["meta"].get("numItems", 0),
                )
                for c in collections_data
            ]
        except ZoteroAPIError as e:
            logger.error(f"Failed to fetch collections: {e}")
            raise

    def get_collection_info(
        self,
        library_type: str,
        library_id: str,
        collection_key: str,
    ) -> ZoteroCollection:
        """Get information about a specific collection."""
        prefix = f"/{library_type}s/{library_id}"
        data = self._request(f"{prefix}/collections/{collection_key}")
        return ZoteroCollection(
            key=data["key"],
            name=data["data"].get("name", "Unnamed"),
            parent_key=data["data"].get("parentCollection"),
            num_items=data["meta"].get("numItems", 0),
        )

    def get_bibtex(
        self,
        library_type: str,
        library_id: str,
        collection_key: Optional[str] = None,
        include_child_items: bool = True,
    ) -> tuple[str, int]:
        """
        Fetch all items from a library/collection as BibTeX.

        Handles pagination automatically to retrieve all items.

        Args:
            library_type: "user" or "group"
            library_id: User or group ID
            collection_key: Optional collection key (None = entire library)
            include_child_items: Include child items (attachments, notes)

        Returns:
            Tuple of (bibtex_content, item_count)
        """
        prefix = f"/{library_type}s/{library_id}"

        if collection_key:
            base_endpoint = f"{prefix}/collections/{collection_key}/items"
        else:
            base_endpoint = f"{prefix}/items"

        all_bibtex = []
        total_items = 0
        start = 0

        while True:
            params = {
                "format": "bibtex",
                "limit": MAX_ITEMS_PER_REQUEST,
                "start": start,
            }

            if not include_child_items:
                params["itemType"] = "-attachment || note"

            try:
                bibtex = self._request(base_endpoint, params=params, raw_response=True)

                if not bibtex or bibtex.strip() == "":
                    break

                all_bibtex.append(bibtex)

                # Count items (each @type{ is one entry)
                item_count = bibtex.count("@")
                total_items += item_count

                # If we got fewer items than the limit, we're done
                if item_count < MAX_ITEMS_PER_REQUEST:
                    break

                start += MAX_ITEMS_PER_REQUEST

                # Safety: max 10000 items
                if start >= 10000:
                    logger.warning(f"Reached item limit for library {library_type}/{library_id}")
                    break

            except ZoteroAPIError as e:
                logger.error(f"Failed to fetch BibTeX page at start={start}: {e}")
                raise

        combined_bibtex = "\n\n".join(all_bibtex)
        return combined_bibtex, total_items

    def get_item_count(
        self,
        library_type: str,
        library_id: str,
        collection_key: Optional[str] = None,
    ) -> int:
        """
        Get the number of items in a library or collection without fetching content.

        Args:
            library_type: "user" or "group"
            library_id: User or group ID
            collection_key: Optional collection key

        Returns:
            Number of items
        """
        prefix = f"/{library_type}s/{library_id}"

        if collection_key:
            endpoint = f"{prefix}/collections/{collection_key}/items"
        else:
            endpoint = f"{prefix}/items"

        params = {"limit": 1, "format": "keys"}

        try:
            response = self.session.get(
                f"{ZOTERO_API_BASE}{endpoint}",
                params=params,
                timeout=DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            return int(response.headers.get("Total-Results", 0))
        except Exception as e:
            logger.warning(f"Failed to get item count: {e}")
            return 0
