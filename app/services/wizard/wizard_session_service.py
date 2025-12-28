"""
Wizard Session Service

Server-authoritative session management for the Chatbot Builder Wizard.
Uses Redis for real-time state with MariaDB as fallback for durability.

Key design principles:
- Server is always source of truth
- All time calculations happen server-side
- Sessions survive server restarts via Redis persistence + DB fallback
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Singleton instance
_wizard_session_service = None


def get_wizard_session_service():
    """Get the singleton WizardSessionService instance."""
    global _wizard_session_service
    if _wizard_session_service is None:
        from main import redis_client
        _wizard_session_service = WizardSessionService(redis_client)
    return _wizard_session_service


class WizardSessionService:
    """
    Manages wizard sessions in Redis with DB fallback.

    Redis Key Structure:
        wizard:session:{chatbot_id}           - Hash with session state
        wizard:session:{chatbot_id}:progress  - Hash with live progress data
        wizard:user:{user_id}:sessions        - Set of active session IDs for user
        wizard:active                         - Set of all active wizard sessions
    """

    # Redis key templates
    KEY_SESSION = "wizard:session:{chatbot_id}"
    KEY_PROGRESS = "wizard:session:{chatbot_id}:progress"
    KEY_USER_SESSIONS = "wizard:user:{user_id}:sessions"
    KEY_ACTIVE = "wizard:active"

    # TTL settings (seconds)
    TTL_ABANDONED = 604800  # 7 days for inactive sessions

    # Valid build statuses
    VALID_STATUSES = {'draft', 'crawling', 'embedding', 'configuring', 'ready', 'error', 'paused'}

    # Status to step mapping
    STATUS_TO_STEP = {
        'draft': 1,
        'crawling': 2,
        'embedding': 3,
        'configuring': 4,
        'ready': 5,
        'error': None,
        'paused': None,
    }

    def __init__(self, redis_client):
        """Initialize with Redis client."""
        self.redis = redis_client
        logger.info("[WizardSessionService] Initialized with Redis client")

    # ========== Session CRUD ==========

    def create_session(
        self,
        chatbot_id: int,
        user_id: int,
        username: str,
        source_url: str,
        crawler_config: Dict = None,
        wizard_data: Dict = None
    ) -> Dict[str, Any]:
        """
        Create a new wizard session.

        Args:
            chatbot_id: The chatbot ID (primary key)
            user_id: The user ID who owns this session
            username: Username for display
            source_url: The URL being crawled
            crawler_config: Optional crawler configuration
            wizard_data: Optional initial wizard data

        Returns:
            The created session dict
        """
        now = datetime.utcnow().isoformat()

        session = {
            'chatbot_id': str(chatbot_id),
            'user_id': str(user_id),
            'username': username,
            'build_status': 'draft',
            'current_step': '1',
            'crawler_job_id': '',
            'collection_id': '',
            'source_url': source_url,

            # Timestamps
            'created_at': now,
            'crawl_started_at': '',
            'embed_started_at': '',
            'paused_at': '',
            'last_activity_at': now,

            # Elapsed time (accumulated seconds)
            'elapsed_crawl_time': '0',
            'elapsed_embed_time': '0',

            # Config (JSON serialized)
            'crawler_config': json.dumps(crawler_config or {}),
            'wizard_data': json.dumps(wizard_data or {}),

            # Error state
            'error_message': '',
            'error_source': '',
        }

        session_key = self.KEY_SESSION.format(chatbot_id=chatbot_id)

        # Store session in Redis
        self.redis.hset(session_key, mapping=session)

        # Add to user's sessions set
        user_sessions_key = self.KEY_USER_SESSIONS.format(user_id=user_id)
        self.redis.sadd(user_sessions_key, str(chatbot_id))

        # Add to active sessions set
        self.redis.sadd(self.KEY_ACTIVE, str(chatbot_id))

        # Set TTL for abandoned session cleanup
        self.redis.expire(session_key, self.TTL_ABANDONED)

        logger.info(f"[WizardSessionService] Created session for chatbot {chatbot_id}")

        return self._deserialize_session(session)

    def get_session(self, chatbot_id: int) -> Optional[Dict[str, Any]]:
        """
        Get session by chatbot ID.

        Args:
            chatbot_id: The chatbot ID

        Returns:
            Session dict or None if not found
        """
        session_key = self.KEY_SESSION.format(chatbot_id=chatbot_id)
        session = self.redis.hgetall(session_key)

        if not session:
            # Try to recover from database
            return self._recover_from_db(chatbot_id)

        # Refresh TTL on access
        self.redis.expire(session_key, self.TTL_ABANDONED)

        return self._deserialize_session(session)

    def update_session(self, chatbot_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update session fields.

        Args:
            chatbot_id: The chatbot ID
            updates: Dict of fields to update

        Returns:
            True if successful
        """
        session_key = self.KEY_SESSION.format(chatbot_id=chatbot_id)

        # Check session exists
        if not self.redis.exists(session_key):
            logger.warning(f"[WizardSessionService] Session {chatbot_id} not found for update")
            return False

        # Serialize complex fields
        serialized = {}
        for key, value in updates.items():
            if isinstance(value, dict):
                serialized[key] = json.dumps(value)
            elif value is None:
                serialized[key] = ''
            else:
                serialized[key] = str(value)

        # Always update last_activity_at
        serialized['last_activity_at'] = datetime.utcnow().isoformat()

        self.redis.hset(session_key, mapping=serialized)

        # Refresh TTL
        self.redis.expire(session_key, self.TTL_ABANDONED)

        return True

    def delete_session(self, chatbot_id: int) -> bool:
        """
        Delete session (on completion or cancellation).

        Args:
            chatbot_id: The chatbot ID

        Returns:
            True if deleted
        """
        session_key = self.KEY_SESSION.format(chatbot_id=chatbot_id)
        progress_key = self.KEY_PROGRESS.format(chatbot_id=chatbot_id)

        # Get user_id before deleting
        user_id = self.redis.hget(session_key, 'user_id')

        # Delete session and progress
        self.redis.delete(session_key)
        self.redis.delete(progress_key)

        # Remove from active sessions
        self.redis.srem(self.KEY_ACTIVE, str(chatbot_id))

        # Remove from user's sessions
        if user_id:
            user_sessions_key = self.KEY_USER_SESSIONS.format(user_id=user_id)
            self.redis.srem(user_sessions_key, str(chatbot_id))

        logger.info(f"[WizardSessionService] Deleted session for chatbot {chatbot_id}")

        return True

    # ========== Status Transitions ==========

    def transition_status(
        self,
        chatbot_id: int,
        new_status: str,
        error_message: str = None,
        error_source: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Transition session to new status with proper bookkeeping.
        Handles elapsed time tracking and step advancement.

        Args:
            chatbot_id: The chatbot ID
            new_status: The new status
            error_message: Optional error message
            error_source: Optional error source (crawl, embed, config)

        Returns:
            Updated session dict or None if failed
        """
        if new_status not in self.VALID_STATUSES:
            logger.error(f"[WizardSessionService] Invalid status: {new_status}")
            return None

        session = self.get_session(chatbot_id)
        if not session:
            logger.error(f"[WizardSessionService] Session {chatbot_id} not found for transition")
            return None

        old_status = session['build_status']
        now = datetime.utcnow()
        now_iso = now.isoformat()

        updates = {
            'build_status': new_status,
            'last_activity_at': now_iso,
        }

        # Handle time tracking on status change
        if old_status == 'crawling' and new_status != 'crawling':
            # Stop crawl timer
            if session.get('crawl_started_at'):
                started = datetime.fromisoformat(session['crawl_started_at'])
                elapsed = float(session.get('elapsed_crawl_time', 0))
                elapsed += (now - started).total_seconds()
                updates['elapsed_crawl_time'] = str(elapsed)

        if old_status == 'embedding' and new_status != 'embedding':
            # Stop embed timer
            if session.get('embed_started_at'):
                started = datetime.fromisoformat(session['embed_started_at'])
                elapsed = float(session.get('elapsed_embed_time', 0))
                elapsed += (now - started).total_seconds()
                updates['elapsed_embed_time'] = str(elapsed)

        # Start timers for new status
        if new_status == 'crawling' and old_status != 'crawling':
            updates['crawl_started_at'] = now_iso

        if new_status == 'embedding' and old_status != 'embedding':
            updates['embed_started_at'] = now_iso

        # Handle pause
        if new_status == 'paused':
            updates['paused_at'] = now_iso

        # Handle error
        if new_status == 'error':
            updates['error_message'] = error_message or ''
            updates['error_source'] = error_source or ''
        else:
            # Clear error on non-error status
            updates['error_message'] = ''
            updates['error_source'] = ''

        # Update step based on status
        new_step = self.STATUS_TO_STEP.get(new_status)
        if new_step is not None:
            updates['current_step'] = str(new_step)

        self.update_session(chatbot_id, updates)

        logger.info(f"[WizardSessionService] Transitioned {chatbot_id}: {old_status} -> {new_status}")

        return self.get_session(chatbot_id)

    # ========== Progress Updates ==========

    def update_crawl_progress(self, chatbot_id: int, progress: Dict) -> None:
        """
        Update crawl progress atomically.

        Args:
            chatbot_id: The chatbot ID
            progress: Progress dict with crawl stats
        """
        progress_key = self.KEY_PROGRESS.format(chatbot_id=chatbot_id)

        # Serialize all values to strings
        serialized = {k: str(v) if v is not None else '' for k, v in progress.items()}

        self.redis.hset(progress_key, mapping=serialized)
        self.redis.expire(progress_key, self.TTL_ABANDONED)

    def update_embedding_progress(self, chatbot_id: int, progress: Dict) -> None:
        """
        Update embedding progress atomically.

        Args:
            chatbot_id: The chatbot ID
            progress: Progress dict with embedding stats
        """
        progress_key = self.KEY_PROGRESS.format(chatbot_id=chatbot_id)

        # Serialize all values to strings
        serialized = {k: str(v) if v is not None else '' for k, v in progress.items()}

        self.redis.hset(progress_key, mapping=serialized)
        self.redis.expire(progress_key, self.TTL_ABANDONED)

    def get_progress(self, chatbot_id: int) -> Dict[str, Any]:
        """
        Get current progress snapshot.

        Args:
            chatbot_id: The chatbot ID

        Returns:
            Progress dict
        """
        progress_key = self.KEY_PROGRESS.format(chatbot_id=chatbot_id)
        progress = self.redis.hgetall(progress_key)

        if not progress:
            return {}

        # Convert numeric strings back to int/float
        result = {}
        for key, value in progress.items():
            if value == '':
                result[key] = None
            elif value.isdigit():
                result[key] = int(value)
            else:
                try:
                    result[key] = float(value)
                except ValueError:
                    result[key] = value

        return result

    # ========== Time Tracking ==========

    def get_elapsed_time(self, chatbot_id: int) -> Dict[str, float]:
        """
        Calculate elapsed time server-side.

        Args:
            chatbot_id: The chatbot ID

        Returns:
            Dict with {crawl, embed, total} in seconds
        """
        session = self.get_session(chatbot_id)
        if not session:
            return {'crawl': 0, 'embed': 0, 'total': 0}

        now = datetime.utcnow()
        crawl_elapsed = float(session.get('elapsed_crawl_time', 0) or 0)
        embed_elapsed = float(session.get('elapsed_embed_time', 0) or 0)

        # Add running time if currently active
        if session['build_status'] == 'crawling' and session.get('crawl_started_at'):
            try:
                started = datetime.fromisoformat(session['crawl_started_at'])
                crawl_elapsed += (now - started).total_seconds()
            except ValueError:
                pass

        if session['build_status'] == 'embedding' and session.get('embed_started_at'):
            try:
                started = datetime.fromisoformat(session['embed_started_at'])
                embed_elapsed += (now - started).total_seconds()
            except ValueError:
                pass

        return {
            'crawl': round(crawl_elapsed, 1),
            'embed': round(embed_elapsed, 1),
            'total': round(crawl_elapsed + embed_elapsed, 1)
        }

    def pause_timers(self, chatbot_id: int) -> None:
        """Pause time tracking (on pause/error)."""
        self.transition_status(chatbot_id, 'paused')

    def resume_timers(self, chatbot_id: int) -> None:
        """Resume time tracking from paused state."""
        session = self.get_session(chatbot_id)
        if not session or session['build_status'] != 'paused':
            return

        # Resume to previous active status based on progress
        progress = self.get_progress(chatbot_id)

        if progress.get('embedding_progress', 0) > 0:
            self.transition_status(chatbot_id, 'embedding')
        elif progress.get('crawl_stage') in ['crawling', 'planning', 'planning_done']:
            self.transition_status(chatbot_id, 'crawling')
        else:
            self.transition_status(chatbot_id, 'draft')

    # ========== Wizard Data ==========

    def update_wizard_data(self, chatbot_id: int, wizard_data: Dict) -> bool:
        """
        Update wizard configuration data.

        Args:
            chatbot_id: The chatbot ID
            wizard_data: Dict with wizard form data

        Returns:
            True if successful
        """
        session = self.get_session(chatbot_id)
        if not session:
            return False

        # Merge with existing wizard_data
        existing = session.get('wizard_data', {})
        if isinstance(existing, str):
            try:
                existing = json.loads(existing)
            except json.JSONDecodeError:
                existing = {}

        merged = {**existing, **wizard_data}

        return self.update_session(chatbot_id, {'wizard_data': merged})

    def get_wizard_data(self, chatbot_id: int) -> Dict[str, Any]:
        """Get wizard configuration data."""
        session = self.get_session(chatbot_id)
        if not session:
            return {}

        return session.get('wizard_data', {})

    # ========== User Session Management ==========

    def get_user_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all active sessions for a user.

        Args:
            user_id: The user ID

        Returns:
            List of session dicts
        """
        user_sessions_key = self.KEY_USER_SESSIONS.format(user_id=user_id)
        chatbot_ids = self.redis.smembers(user_sessions_key)

        sessions = []
        for chatbot_id in chatbot_ids:
            session = self.get_session(int(chatbot_id))
            if session:
                sessions.append(session)
            else:
                # Clean up stale reference
                self.redis.srem(user_sessions_key, chatbot_id)

        return sessions

    def get_resumable_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the most recent resumable session for a user.

        A resumable session is one that is not 'ready' or 'error' status.

        Args:
            user_id: The user ID

        Returns:
            Most recent resumable session or None
        """
        sessions = self.get_user_sessions(user_id)

        resumable = [
            s for s in sessions
            if s['build_status'] not in ('ready', 'error')
        ]

        if not resumable:
            return None

        # Sort by last_activity_at descending
        resumable.sort(
            key=lambda s: s.get('last_activity_at', ''),
            reverse=True
        )

        return resumable[0]

    # ========== Internal Helpers ==========

    def _deserialize_session(self, session: Dict[str, str]) -> Dict[str, Any]:
        """Deserialize session from Redis string values."""
        result = {}

        for key, value in session.items():
            if key in ('crawler_config', 'wizard_data'):
                # Parse JSON fields
                try:
                    result[key] = json.loads(value) if value else {}
                except json.JSONDecodeError:
                    result[key] = {}
            elif key in ('chatbot_id', 'collection_id', 'current_step'):
                # Parse int fields (NOT user_id - it may be a username string)
                try:
                    result[key] = int(value) if value else None
                except ValueError:
                    result[key] = None
            elif key == 'user_id':
                # user_id can be int or username string - try int first
                if value:
                    try:
                        result[key] = int(value)
                    except ValueError:
                        # It's a username string, keep as-is for lookup purposes
                        result[key] = value
                else:
                    result[key] = None
            elif key in ('elapsed_crawl_time', 'elapsed_embed_time'):
                # Parse float fields
                result[key] = float(value) if value else 0.0
            else:
                # Keep as string (or None for empty)
                result[key] = value if value else None

        return result

    def _recover_from_db(self, chatbot_id: int) -> Optional[Dict[str, Any]]:
        """
        Recover session from database if not in Redis.

        This handles the case where Redis was restarted but the chatbot
        still has an active wizard session in the database.
        """
        try:
            from db.tables import Chatbot

            chatbot = Chatbot.query.get(chatbot_id)
            if not chatbot or chatbot.build_status in ('ready', None):
                return None

            # Reconstruct session from database
            # Note: chatbot.created_by is a username string, not a user ID
            session = {
                'chatbot_id': str(chatbot.id),
                'user_id': '',  # Not available from DB recovery - use username for lookups
                'username': chatbot.created_by or '',
                'build_status': chatbot.build_status or 'draft',
                'current_step': str(self.STATUS_TO_STEP.get(chatbot.build_status, 1)),
                'crawler_job_id': '',
                'collection_id': str(chatbot.primary_collection_id) if chatbot.primary_collection_id else '',
                'source_url': chatbot.source_url or '',
                'created_at': chatbot.created_at.isoformat() if chatbot.created_at else '',
                'crawl_started_at': '',
                'embed_started_at': '',
                'paused_at': '',
                'last_activity_at': datetime.utcnow().isoformat(),
                'elapsed_crawl_time': '0',
                'elapsed_embed_time': '0',
                'crawler_config': '{}',
                'wizard_data': json.dumps({
                    'name': chatbot.name,
                    'displayName': chatbot.display_name,
                    'systemPrompt': chatbot.system_prompt,
                    'modelName': chatbot.model_name,
                    'welcomeMessage': chatbot.welcome_message,
                    'fallbackMessage': chatbot.fallback_message,
                    'icon': chatbot.icon,
                    'color': chatbot.color,
                }),
                'error_message': chatbot.build_error or '',
                'error_source': '',
            }

            # Store recovered session in Redis
            session_key = self.KEY_SESSION.format(chatbot_id=chatbot_id)
            self.redis.hset(session_key, mapping=session)
            self.redis.expire(session_key, self.TTL_ABANDONED)

            # Add to active sessions
            self.redis.sadd(self.KEY_ACTIVE, str(chatbot_id))

            # Note: We don't add to user_sessions since we don't have the user_id
            # The user can still resume via chatbot_id directly

            logger.info(f"[WizardSessionService] Recovered session {chatbot_id} from database")

            return self._deserialize_session(session)

        except Exception as e:
            logger.error(f"[WizardSessionService] Failed to recover session {chatbot_id}: {e}")
            return None
