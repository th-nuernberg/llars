"""WebSocket connection and message metrics service.

Tracks Socket.IO connections, namespaces, rooms, and message rates.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, List, Optional, Set


@dataclass
class ConnectionEvent:
    """Single connection event."""
    timestamp: float
    event_type: str  # 'connect' | 'disconnect'
    namespace: str
    sid: str
    username: Optional[str] = None
    reason: Optional[str] = None  # disconnect reason


@dataclass
class MessageEvent:
    """Single message event."""
    timestamp: float
    direction: str  # 'in' | 'out'
    namespace: str
    event_name: str
    size_bytes: int = 0


class WebSocketMetricsService:
    """Collect and aggregate WebSocket metrics."""

    # Ring buffer sizes
    MAX_EVENTS = 1000
    MAX_MESSAGES = 5000

    _lock = threading.Lock()

    # Active connections: namespace -> set of sids
    _connections: Dict[str, Set[str]] = defaultdict(set)

    # Connection metadata: sid -> {namespace, username, connected_at}
    _connection_info: Dict[str, Dict[str, Any]] = {}

    # Connection events history
    _connection_events: Deque[ConnectionEvent] = deque(maxlen=MAX_EVENTS)

    # Message events for rate calculation
    _message_events: Deque[MessageEvent] = deque(maxlen=MAX_MESSAGES)

    # Room tracking: namespace -> room -> set of sids
    _rooms: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))

    # Namespace labels for display
    NAMESPACE_LABELS = {
        '/': 'Default',
        '/admin': 'Admin',
        '/chat': 'Chat',
        '/collab': 'Collaboration',
        '/judge': 'Judge',
        '/crawler': 'Crawler',
        '/oncoco': 'OnCoCo',
    }

    @classmethod
    def record_connect(
        cls,
        namespace: str,
        sid: str,
        username: Optional[str] = None,
    ) -> None:
        """Record a new connection."""
        event = ConnectionEvent(
            timestamp=time.time(),
            event_type='connect',
            namespace=namespace,
            sid=sid,
            username=username,
        )

        with cls._lock:
            cls._connections[namespace].add(sid)
            cls._connection_info[sid] = {
                'namespace': namespace,
                'username': username,
                'connected_at': time.time(),
            }
            cls._connection_events.append(event)

    @classmethod
    def record_disconnect(
        cls,
        namespace: str,
        sid: str,
        reason: Optional[str] = None,
    ) -> None:
        """Record a disconnection."""
        with cls._lock:
            info = cls._connection_info.pop(sid, {})
            username = info.get('username')

        event = ConnectionEvent(
            timestamp=time.time(),
            event_type='disconnect',
            namespace=namespace,
            sid=sid,
            username=username,
            reason=reason,
        )

        with cls._lock:
            cls._connections[namespace].discard(sid)
            cls._connection_events.append(event)

            # Clean up room memberships
            for room_dict in cls._rooms.values():
                for room_sids in room_dict.values():
                    room_sids.discard(sid)

    @classmethod
    def record_room_join(cls, namespace: str, room: str, sid: str) -> None:
        """Record a room join."""
        with cls._lock:
            cls._rooms[namespace][room].add(sid)

    @classmethod
    def record_room_leave(cls, namespace: str, room: str, sid: str) -> None:
        """Record a room leave."""
        with cls._lock:
            cls._rooms[namespace][room].discard(sid)

    @classmethod
    def record_message(
        cls,
        direction: str,
        namespace: str,
        event_name: str,
        size_bytes: int = 0,
    ) -> None:
        """Record a message event."""
        event = MessageEvent(
            timestamp=time.time(),
            direction=direction,
            namespace=namespace,
            event_name=event_name,
            size_bytes=size_bytes,
        )

        with cls._lock:
            cls._message_events.append(event)

    @classmethod
    def get_connection_count(cls, namespace: Optional[str] = None) -> int:
        """Get current connection count."""
        with cls._lock:
            if namespace:
                return len(cls._connections.get(namespace, set()))
            return sum(len(sids) for sids in cls._connections.values())

    @classmethod
    def get_namespace_stats(cls) -> List[Dict[str, Any]]:
        """Get stats per namespace."""
        window_seconds = 60
        cutoff = time.time() - window_seconds

        with cls._lock:
            # Get message counts per namespace
            messages = [m for m in cls._message_events if m.timestamp >= cutoff]

            namespace_messages: Dict[str, Dict[str, int]] = defaultdict(
                lambda: {'in': 0, 'out': 0, 'bytes_in': 0, 'bytes_out': 0}
            )
            for m in messages:
                stats = namespace_messages[m.namespace]
                if m.direction == 'in':
                    stats['in'] += 1
                    stats['bytes_in'] += m.size_bytes
                else:
                    stats['out'] += 1
                    stats['bytes_out'] += m.size_bytes

            # Build stats per namespace
            results = []
            all_namespaces = set(cls._connections.keys()) | set(namespace_messages.keys())

            for ns in sorted(all_namespaces):
                clients = len(cls._connections.get(ns, set()))
                rooms = len([r for r, sids in cls._rooms.get(ns, {}).items() if sids])
                msg_stats = namespace_messages.get(ns, {'in': 0, 'out': 0, 'bytes_in': 0, 'bytes_out': 0})

                results.append({
                    'namespace': ns,
                    'label': cls.NAMESPACE_LABELS.get(ns, ns),
                    'clients': clients,
                    'rooms': rooms,
                    'messages_in': msg_stats['in'],
                    'messages_out': msg_stats['out'],
                    'messages_in_per_sec': round(msg_stats['in'] / window_seconds, 2),
                    'messages_out_per_sec': round(msg_stats['out'] / window_seconds, 2),
                    'bytes_in': msg_stats['bytes_in'],
                    'bytes_out': msg_stats['bytes_out'],
                })

            return results

    @classmethod
    def get_message_rates(cls, window_seconds: int = 60) -> Dict[str, Any]:
        """Get overall message rates."""
        cutoff = time.time() - window_seconds

        with cls._lock:
            messages = [m for m in cls._message_events if m.timestamp >= cutoff]

        if not messages:
            return {
                'messages_in': 0,
                'messages_out': 0,
                'messages_in_per_sec': 0.0,
                'messages_out_per_sec': 0.0,
                'bytes_in': 0,
                'bytes_out': 0,
                'bytes_in_per_sec': 0.0,
                'bytes_out_per_sec': 0.0,
            }

        in_count = sum(1 for m in messages if m.direction == 'in')
        out_count = sum(1 for m in messages if m.direction == 'out')
        bytes_in = sum(m.size_bytes for m in messages if m.direction == 'in')
        bytes_out = sum(m.size_bytes for m in messages if m.direction == 'out')

        return {
            'messages_in': in_count,
            'messages_out': out_count,
            'messages_in_per_sec': round(in_count / window_seconds, 2),
            'messages_out_per_sec': round(out_count / window_seconds, 2),
            'bytes_in': bytes_in,
            'bytes_out': bytes_out,
            'bytes_in_per_sec': round(bytes_in / window_seconds, 2),
            'bytes_out_per_sec': round(bytes_out / window_seconds, 2),
        }

    @classmethod
    def get_recent_events(cls, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent connection events."""
        with cls._lock:
            events = list(cls._connection_events)[-limit:]

        return [
            {
                'timestamp': e.timestamp,
                'event_type': e.event_type,
                'namespace': e.namespace,
                'namespace_label': cls.NAMESPACE_LABELS.get(e.namespace, e.namespace),
                'sid': e.sid[:8] + '...' if len(e.sid) > 8 else e.sid,
                'username': e.username,
                'reason': e.reason,
                'age_seconds': round(time.time() - e.timestamp, 1),
            }
            for e in reversed(events)
        ]

    @classmethod
    def get_connection_history(cls, window_seconds: int = 300, buckets: int = 60) -> List[Dict[str, Any]]:
        """Get connection count history for charts."""
        bucket_size = window_seconds / buckets
        cutoff = time.time() - window_seconds

        with cls._lock:
            events = [e for e in cls._connection_events if e.timestamp >= cutoff]

        if not events:
            return []

        # Count connections per bucket
        now = time.time()
        history: List[Dict[str, Any]] = []

        # We need to track running total of connections
        # This is tricky - we'll approximate by counting connects/disconnects per bucket

        for i in range(buckets):
            bucket_start = now - window_seconds + (i * bucket_size)
            bucket_end = bucket_start + bucket_size

            bucket_events = [
                e for e in events
                if bucket_start <= e.timestamp < bucket_end
            ]

            connects = sum(1 for e in bucket_events if e.event_type == 'connect')
            disconnects = sum(1 for e in bucket_events if e.event_type == 'disconnect')

            history.append({
                'timestamp': bucket_start,
                'connects': connects,
                'disconnects': disconnects,
                'net_change': connects - disconnects,
            })

        return history

    @classmethod
    def get_message_history(cls, window_seconds: int = 300, buckets: int = 60) -> List[Dict[str, Any]]:
        """Get message rate history for charts."""
        bucket_size = window_seconds / buckets
        cutoff = time.time() - window_seconds

        with cls._lock:
            messages = [m for m in cls._message_events if m.timestamp >= cutoff]

        if not messages:
            return []

        now = time.time()
        history: List[Dict[str, Any]] = []

        for i in range(buckets):
            bucket_start = now - window_seconds + (i * bucket_size)
            bucket_end = bucket_start + bucket_size

            bucket_messages = [
                m for m in messages
                if bucket_start <= m.timestamp < bucket_end
            ]

            in_count = sum(1 for m in bucket_messages if m.direction == 'in')
            out_count = sum(1 for m in bucket_messages if m.direction == 'out')

            history.append({
                'timestamp': bucket_start,
                'messages_in': in_count,
                'messages_out': out_count,
                'messages_in_per_sec': round(in_count / bucket_size, 2) if bucket_size > 0 else 0,
                'messages_out_per_sec': round(out_count / bucket_size, 2) if bucket_size > 0 else 0,
            })

        return history

    @classmethod
    def get_snapshot(cls) -> Dict[str, Any]:
        """Get a complete snapshot of WebSocket metrics."""
        return {
            'ok': True,
            'timestamp': time.time(),
            'total_connections': cls.get_connection_count(),
            'namespaces': cls.get_namespace_stats(),
            'rates': cls.get_message_rates(60),
            'recent_events': cls.get_recent_events(15),
            'connection_history': cls.get_connection_history(300, 60),
            'message_history': cls.get_message_history(300, 60),
        }


def create_socketio_metrics_wrapper(socketio):
    """Wrap Socket.IO to track metrics.

    Call this after socketio is initialized to add metrics tracking.
    """
    original_emit = socketio.emit

    def tracked_emit(event, data=None, *args, **kwargs):
        namespace = kwargs.get('namespace', '/')
        try:
            import json
            size = len(json.dumps(data)) if data else 0
        except Exception:
            size = 0

        WebSocketMetricsService.record_message(
            direction='out',
            namespace=namespace,
            event_name=event,
            size_bytes=size,
        )
        return original_emit(event, data, *args, **kwargs)

    socketio.emit = tracked_emit

    return socketio
