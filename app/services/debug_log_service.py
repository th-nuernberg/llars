"""
Per-User Debug Log Service

Ermöglicht Admins, für einzelne User in Production kurzzeitig detaillierte
Fehler-Logs und Console-Output zu aktivieren. Debug-Flags werden in Redis
gespeichert und verfallen automatisch nach einer konfigurierbaren TTL.

Anwendungsfälle:
- Admin aktiviert Debug-Modus für User "evaluator" für 30 Minuten
- Während dieser Zeit sieht der User detaillierte Fehlermeldungen
- Nach Ablauf der TTL wird automatisch auf generische Meldungen zurückgestellt

Redis-Key-Schema:
    debug:user:{username} → "1" mit TTL in Sekunden

Usage:
    from services.debug_log_service import is_user_debug_enabled

    if is_user_debug_enabled('evaluator'):
        # Zeige detaillierte Fehlermeldung
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Redis-Key-Prefix für Debug-Flags
_REDIS_KEY_PREFIX = 'debug:user:'

# Standard-TTL: 30 Minuten
DEFAULT_DEBUG_TTL_SECONDS = 30 * 60

# Maximale TTL: 24 Stunden (verhindert versehentlich endlosen Debug-Modus)
MAX_DEBUG_TTL_SECONDS = 24 * 60 * 60


def _get_redis():
    """Lazy-Import des Redis-Clients aus main.py."""
    from main import redis_client
    return redis_client


def is_user_debug_enabled(username: str) -> bool:
    """
    Prüft ob für den User Debug-Logging aktiviert ist.

    Wird vom Error Handler aufgerufen um zu entscheiden,
    ob Fehlerdetails an den Client zurückgegeben werden.

    Args:
        username: Der zu prüfende Username

    Returns:
        True wenn Debug-Modus aktiv, False sonst
    """
    if not username:
        return False
    try:
        redis = _get_redis()
        return redis.exists(f'{_REDIS_KEY_PREFIX}{username}') > 0
    except Exception:
        # Redis nicht erreichbar → sicherheitshalber kein Debug
        return False


def enable_user_debug(username: str, ttl_seconds: Optional[int] = None) -> dict:
    """
    Aktiviert Debug-Logging für einen User mit automatischem Ablauf.

    Args:
        username: Username für den Debug aktiviert wird
        ttl_seconds: Dauer in Sekunden (Default: 30 Min, Max: 24h)

    Returns:
        Dict mit Status-Informationen
    """
    if not username:
        raise ValueError('Username is required')

    ttl = ttl_seconds or DEFAULT_DEBUG_TTL_SECONDS
    ttl = max(60, min(ttl, MAX_DEBUG_TTL_SECONDS))  # Clamp: 1 Min bis 24h

    try:
        redis = _get_redis()
        redis.setex(f'{_REDIS_KEY_PREFIX}{username}', ttl, '1')
        logger.info(f'Debug logging enabled for user "{username}" (TTL: {ttl}s)')
        return {
            'username': username,
            'debug_enabled': True,
            'ttl_seconds': ttl,
            'ttl_minutes': round(ttl / 60, 1),
        }
    except Exception as e:
        logger.error(f'Failed to enable debug for "{username}": {e}')
        raise


def disable_user_debug(username: str) -> dict:
    """
    Deaktiviert Debug-Logging für einen User sofort.

    Args:
        username: Username für den Debug deaktiviert wird

    Returns:
        Dict mit Status-Informationen
    """
    if not username:
        raise ValueError('Username is required')

    try:
        redis = _get_redis()
        redis.delete(f'{_REDIS_KEY_PREFIX}{username}')
        logger.info(f'Debug logging disabled for user "{username}"')
        return {
            'username': username,
            'debug_enabled': False,
        }
    except Exception as e:
        logger.error(f'Failed to disable debug for "{username}": {e}')
        raise


def get_user_debug_status(username: str) -> dict:
    """
    Gibt den aktuellen Debug-Status für einen User zurück.

    Args:
        username: Username zum Abfragen

    Returns:
        Dict mit enabled-Flag und verbleibender TTL
    """
    if not username:
        return {'username': username, 'debug_enabled': False, 'ttl_remaining': 0}

    try:
        redis = _get_redis()
        key = f'{_REDIS_KEY_PREFIX}{username}'
        ttl = redis.ttl(key)  # -2 = key existiert nicht, -1 = kein Ablauf
        enabled = ttl > 0

        return {
            'username': username,
            'debug_enabled': enabled,
            'ttl_remaining': max(0, ttl),
            'ttl_remaining_minutes': round(max(0, ttl) / 60, 1) if enabled else 0,
        }
    except Exception:
        return {'username': username, 'debug_enabled': False, 'ttl_remaining': 0}


def get_all_debug_users() -> list:
    """
    Gibt alle User mit aktivem Debug-Modus zurück.

    Returns:
        Liste von Dicts mit Username und verbleibender TTL
    """
    try:
        redis = _get_redis()
        keys = redis.keys(f'{_REDIS_KEY_PREFIX}*')
        users = []
        for key in keys:
            username = key.replace(_REDIS_KEY_PREFIX, '')
            ttl = redis.ttl(key)
            if ttl > 0:
                users.append({
                    'username': username,
                    'ttl_remaining': ttl,
                    'ttl_remaining_minutes': round(ttl / 60, 1),
                })
        return sorted(users, key=lambda u: u['username'])
    except Exception:
        return []
