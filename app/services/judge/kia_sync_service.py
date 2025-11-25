"""
KIA Data Sync Service - Automatisches Laden von KIA-Daten aus GitLab.

Lädt JSON-Daten aus dem GitLab Repository:
https://git.informatik.fh-nuernberg.de/e-beratung/kia/kia-data

Struktur: data/saeule_{N}/raw/json/*.json

Säulen:
1. Rollenspiele
2. Feature aus Säule 1
3. Anonymisierte Daten
4. Synthetisch generiert
5. Live-Testungen
"""

import logging
import json
import hashlib
import base64
import requests
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Pillar configuration
# Korrekte Pfade: data/saeule_X/common/json (nicht raw/json)
PILLAR_CONFIG = {
    1: {"name": "Rollenspiele", "path": "data/saeule_1/common/json"},
    2: {"name": "Feature aus Säule 1", "path": "data/saeule_2/common/json"},
    3: {"name": "Anonymisierte Daten", "path": "data/saeule_3/common/json"},
    4: {"name": "Synthetisch generiert", "path": "data/saeule_4/common/json"},
    5: {"name": "Live-Testungen", "path": "data/saeule_5/common/json"},
}


class SyncStatus(Enum):
    """Status of pillar data availability"""
    AVAILABLE = "available"
    NOT_FOUND = "not_found"
    ERROR = "error"
    SYNCING = "syncing"


@dataclass
class PillarStatus:
    """Status information for a single pillar"""
    pillar_number: int
    pillar_name: str
    status: SyncStatus
    file_count: int = 0
    thread_count: int = 0
    last_sync: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class SyncResult:
    """Result of a sync operation"""
    success: bool
    pillar_number: int
    files_processed: int = 0
    threads_created: int = 0
    threads_updated: int = 0
    threads_skipped: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class KIASyncService:
    """
    Service for synchronizing KIA data from GitLab repository.

    Uses GitLab API to fetch JSON files from specified paths
    and imports them into the LLARS database.
    """

    # GitLab configuration
    GITLAB_HOST = "git.informatik.fh-nuernberg.de"
    PROJECT_PATH = "e-beratung/kia/kia-data"
    API_VERSION = "v4"

    def __init__(self, gitlab_token: Optional[str] = None):
        """
        Initialize the sync service.

        Args:
            gitlab_token: GitLab Personal Access Token for API access.
                         If not provided, tries to get from environment.
        """
        self.gitlab_token = gitlab_token or self._get_token_from_env()
        self.base_url = f"https://{self.GITLAB_HOST}/api/{self.API_VERSION}"
        self.project_id = None  # Will be fetched on first API call

    def _get_token_from_env(self) -> Optional[str]:
        """Get GitLab token from environment variables."""
        import os
        return os.environ.get('GITLAB_TOKEN') or os.environ.get('KIA_GITLAB_TOKEN')

    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers."""
        headers = {"Content-Type": "application/json"}
        if self.gitlab_token:
            headers["PRIVATE-TOKEN"] = self.gitlab_token
        return headers

    def _get_project_id(self) -> Optional[int]:
        """Fetch the project ID from GitLab API."""
        if self.project_id:
            return self.project_id

        try:
            # URL-encode the project path
            encoded_path = requests.utils.quote(self.PROJECT_PATH, safe='')
            url = f"{self.base_url}/projects/{encoded_path}"

            response = requests.get(url, headers=self._get_headers(), timeout=10)

            if response.status_code == 200:
                self.project_id = response.json().get('id')
                logger.info(f"[KIASync] Got project ID: {self.project_id}")
                return self.project_id
            elif response.status_code == 401:
                logger.error("[KIASync] Authentication failed - check GitLab token")
            elif response.status_code == 404:
                logger.error(f"[KIASync] Project not found: {self.PROJECT_PATH}")
            else:
                logger.error(f"[KIASync] Failed to get project: {response.status_code}")

        except requests.RequestException as e:
            logger.error(f"[KIASync] Request failed: {e}")

        return None

    def check_pillar_availability(self) -> Dict[int, PillarStatus]:
        """
        Check which pillars have data available in the repository.

        Returns:
            Dict mapping pillar number to PillarStatus
        """
        results = {}
        project_id = self._get_project_id()

        for pillar_num, config in PILLAR_CONFIG.items():
            status = PillarStatus(
                pillar_number=pillar_num,
                pillar_name=config["name"],
                status=SyncStatus.NOT_FOUND
            )

            if not project_id:
                status.status = SyncStatus.ERROR
                status.error_message = "Could not connect to GitLab"
                results[pillar_num] = status
                continue

            try:
                # Check if directory exists via repository tree API
                encoded_path = requests.utils.quote(config["path"], safe='')
                url = f"{self.base_url}/projects/{project_id}/repository/tree"
                params = {"path": config["path"], "per_page": 100}

                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=10
                )

                if response.status_code == 200:
                    files = response.json()
                    json_files = [f for f in files if f.get('name', '').endswith('.json')]

                    if json_files:
                        status.status = SyncStatus.AVAILABLE
                        status.file_count = len(json_files)
                        logger.info(f"[KIASync] Säule {pillar_num}: {len(json_files)} JSON files found")
                    else:
                        status.status = SyncStatus.NOT_FOUND
                        status.error_message = "Directory exists but no JSON files found"

                elif response.status_code == 404:
                    status.status = SyncStatus.NOT_FOUND
                    status.error_message = f"Path not found: {config['path']}"
                    logger.info(f"[KIASync] Säule {pillar_num}: Not found (yet)")
                else:
                    status.status = SyncStatus.ERROR
                    status.error_message = f"API error: {response.status_code}"

            except requests.RequestException as e:
                status.status = SyncStatus.ERROR
                status.error_message = str(e)

            results[pillar_num] = status

        return results

    def get_pillar_files(self, pillar_number: int) -> List[Dict]:
        """
        Get list of JSON files for a specific pillar.

        Args:
            pillar_number: Pillar number (1-5)

        Returns:
            List of file info dicts with 'name', 'path', 'id' keys
        """
        if pillar_number not in PILLAR_CONFIG:
            return []

        project_id = self._get_project_id()
        if not project_id:
            return []

        config = PILLAR_CONFIG[pillar_number]

        try:
            url = f"{self.base_url}/projects/{project_id}/repository/tree"
            params = {"path": config["path"], "per_page": 100, "recursive": False}

            all_files = []
            page = 1

            while True:
                params["page"] = page
                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=10
                )

                if response.status_code != 200:
                    break

                files = response.json()
                if not files:
                    break

                json_files = [f for f in files if f.get('name', '').endswith('.json')]
                all_files.extend(json_files)
                page += 1

                # Safety limit
                if page > 10:
                    break

            return all_files

        except requests.RequestException as e:
            logger.error(f"[KIASync] Failed to list files for pillar {pillar_number}: {e}")
            return []

    def fetch_file_content(self, file_path: str) -> Optional[Dict]:
        """
        Fetch and parse a JSON file from the repository.

        Args:
            file_path: Path to file in repository

        Returns:
            Parsed JSON content or None on error
        """
        project_id = self._get_project_id()
        if not project_id:
            return None

        try:
            encoded_path = requests.utils.quote(file_path, safe='')
            url = f"{self.base_url}/projects/{project_id}/repository/files/{encoded_path}/raw"
            params = {"ref": "main"}  # or "master" depending on default branch

            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                # Try master branch
                params["ref"] = "master"
                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=30
                )
                if response.status_code == 200:
                    return response.json()

            logger.error(f"[KIASync] Failed to fetch {file_path}: {response.status_code}")
            return None

        except json.JSONDecodeError as e:
            logger.error(f"[KIASync] Invalid JSON in {file_path}: {e}")
            return None
        except requests.RequestException as e:
            logger.error(f"[KIASync] Request failed for {file_path}: {e}")
            return None

    def sync_pillar(self, pillar_number: int, force: bool = False) -> SyncResult:
        """
        Synchronize data for a specific pillar.

        Args:
            pillar_number: Pillar number (1-5)
            force: If True, re-import even if data exists

        Returns:
            SyncResult with statistics
        """
        from db.db import db
        from db.tables import EmailThread, Message, PillarThread

        result = SyncResult(success=False, pillar_number=pillar_number)

        if pillar_number not in PILLAR_CONFIG:
            result.errors.append(f"Invalid pillar number: {pillar_number}")
            return result

        config = PILLAR_CONFIG[pillar_number]
        logger.info(f"[KIASync] Starting sync for Säule {pillar_number}: {config['name']}")

        # Get file list
        files = self.get_pillar_files(pillar_number)
        if not files:
            result.errors.append("No files found or access denied")
            return result

        result.files_processed = len(files)

        for file_info in files:
            file_path = file_info.get('path')
            file_name = file_info.get('name')

            try:
                # Fetch file content
                content = self.fetch_file_content(file_path)
                if not content:
                    result.errors.append(f"Could not fetch: {file_name}")
                    continue

                # Process the JSON content
                import_result = self._import_thread_data(
                    content,
                    pillar_number,
                    config['name'],
                    file_name,
                    force
                )

                if import_result == "created":
                    result.threads_created += 1
                elif import_result == "updated":
                    result.threads_updated += 1
                elif import_result == "skipped":
                    result.threads_skipped += 1
                else:
                    result.errors.append(f"Failed to import: {file_name}")

            except Exception as e:
                logger.error(f"[KIASync] Error processing {file_name}: {e}")
                result.errors.append(f"{file_name}: {str(e)}")

        # Commit all changes
        try:
            db.session.commit()
            result.success = True
            logger.info(
                f"[KIASync] Säule {pillar_number} sync complete: "
                f"{result.threads_created} created, {result.threads_updated} updated, "
                f"{result.threads_skipped} skipped"
            )
        except Exception as e:
            db.session.rollback()
            result.errors.append(f"Database commit failed: {e}")
            logger.error(f"[KIASync] Commit failed: {e}")

        return result

    def _import_thread_data(
        self,
        data: Dict,
        pillar_number: int,
        pillar_name: str,
        source_file: str,
        force: bool = False
    ) -> str:
        """
        Import a single thread from JSON data.

        Expected JSON structure:
        {
            "thread_id": int or "id",
            "chat_id": int (optional),
            "subject": str (optional),
            "messages": [
                {
                    "content": str,
                    "sender": str,
                    "timestamp": str (ISO format, optional),
                    "is_counsellor": bool (optional)
                }
            ]
        }

        Returns:
            "created", "updated", "skipped", or "error"
        """
        from db.db import db
        from db.tables import EmailThread, Message, PillarThread

        # Extract thread info - handle various JSON structures
        thread_id = data.get('thread_id') or data.get('id')
        if not thread_id:
            # Generate ID from filename hash
            thread_id = int(hashlib.md5(source_file.encode()).hexdigest()[:8], 16)

        chat_id = data.get('chat_id', thread_id)
        subject = data.get('subject', f"KIA Säule {pillar_number} - {source_file}")
        messages_data = data.get('messages', data.get('conversation', []))

        if not messages_data:
            logger.warning(f"[KIASync] No messages in {source_file}")
            return "error"

        # Check if thread already exists for this pillar
        existing_pillar_thread = PillarThread.query.filter_by(
            pillar_number=pillar_number
        ).join(EmailThread).filter(
            EmailThread.chat_id == chat_id
        ).first()

        if existing_pillar_thread and not force:
            return "skipped"

        # Find or create EmailThread
        # Use a unique identifier combining pillar and source
        source_hash = hashlib.md5(f"{pillar_number}_{source_file}".encode()).hexdigest()[:8]
        kia_chat_id = int(source_hash, 16) % 1000000  # Keep it reasonable

        email_thread = EmailThread.query.filter_by(
            chat_id=kia_chat_id,
            institut_id=pillar_number  # Use institut_id to mark pillar source
        ).first()

        is_new = False
        if not email_thread:
            email_thread = EmailThread(
                chat_id=kia_chat_id,
                institut_id=pillar_number,
                subject=subject,
                sender=f"KIA-Säule-{pillar_number}"
            )
            db.session.add(email_thread)
            db.session.flush()  # Get the thread_id
            is_new = True
        else:
            # Update existing
            email_thread.subject = subject
            if force:
                # Delete existing messages for re-import
                Message.query.filter_by(thread_id=email_thread.thread_id).delete()

        # Import messages
        for idx, msg_data in enumerate(messages_data):
            content = msg_data.get('content', msg_data.get('text', ''))
            sender = msg_data.get('sender', msg_data.get('role', 'unknown'))

            # Parse timestamp if available
            timestamp = None
            if 'timestamp' in msg_data:
                try:
                    timestamp = datetime.fromisoformat(msg_data['timestamp'].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()

            # Determine if counsellor (Berater)
            is_counsellor = msg_data.get('is_counsellor', False)
            if not is_counsellor:
                # Try to infer from sender
                sender_lower = sender.lower()
                is_counsellor = any(term in sender_lower for term in
                    ['berater', 'counsellor', 'counselor', 'assistant', 'bot'])

            message = Message(
                thread_id=email_thread.thread_id,
                sender=sender,
                content=content,
                timestamp=timestamp,
                generated_by=f"KIA-Import-Saeule-{pillar_number}"
            )
            db.session.add(message)

        # Create or update PillarThread mapping
        if existing_pillar_thread:
            existing_pillar_thread.metadata_json = {
                "source_file": source_file,
                "sync_date": datetime.now().isoformat(),
                "message_count": len(messages_data)
            }
            return "updated"
        else:
            pillar_thread = PillarThread(
                thread_id=email_thread.thread_id,
                pillar_number=pillar_number,
                pillar_name=pillar_name,
                metadata_json={
                    "source_file": source_file,
                    "sync_date": datetime.now().isoformat(),
                    "message_count": len(messages_data)
                }
            )
            db.session.add(pillar_thread)
            return "created"

    def sync_all_pillars(self, force: bool = False) -> Dict[int, SyncResult]:
        """
        Synchronize all available pillars.

        Args:
            force: If True, re-import even if data exists

        Returns:
            Dict mapping pillar number to SyncResult
        """
        results = {}

        # First check availability
        availability = self.check_pillar_availability()

        for pillar_num, status in availability.items():
            if status.status == SyncStatus.AVAILABLE:
                results[pillar_num] = self.sync_pillar(pillar_num, force)
            else:
                results[pillar_num] = SyncResult(
                    success=False,
                    pillar_number=pillar_num,
                    errors=[status.error_message or "Not available"]
                )

        return results

    def get_sync_status(self) -> Dict:
        """
        Get comprehensive sync status for all pillars.

        Returns:
            Dict with pillar status and database statistics
        """
        from db.db import db
        from db.tables import PillarThread, EmailThread, Message

        # Check GitLab availability
        availability = self.check_pillar_availability()

        # Get database statistics
        pillar_stats = {}
        for pillar_num in PILLAR_CONFIG.keys():
            thread_count = PillarThread.query.filter_by(
                pillar_number=pillar_num
            ).count()

            # Get message count for threads in this pillar
            message_count = db.session.query(Message).join(
                EmailThread,
                Message.thread_id == EmailThread.thread_id
            ).join(
                PillarThread,
                PillarThread.thread_id == EmailThread.thread_id
            ).filter(
                PillarThread.pillar_number == pillar_num
            ).count()

            # Get last sync time
            last_sync = db.session.query(
                db.func.max(PillarThread.created_at)
            ).filter(
                PillarThread.pillar_number == pillar_num
            ).scalar()

            pillar_stats[pillar_num] = {
                "name": PILLAR_CONFIG[pillar_num]["name"],
                "gitlab_status": availability[pillar_num].status.value,
                "gitlab_file_count": availability[pillar_num].file_count,
                "db_thread_count": thread_count,
                "db_message_count": message_count,
                "last_sync": last_sync.isoformat() if last_sync else None,
                "error": availability[pillar_num].error_message
            }

        return {
            "pillars": pillar_stats,
            "gitlab_connected": self._get_project_id() is not None,
            "total_threads": PillarThread.query.count(),
            "checked_at": datetime.now().isoformat()
        }


# Singleton instance
_sync_service: Optional[KIASyncService] = None


def get_kia_sync_service(gitlab_token: Optional[str] = None) -> KIASyncService:
    """Get or create the KIA sync service singleton."""
    global _sync_service

    if _sync_service is None or gitlab_token:
        _sync_service = KIASyncService(gitlab_token)

    return _sync_service
