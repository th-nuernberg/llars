"""
URL Validation for SSRF Prevention (CWE-918)

Validiert user-controlled URLs bevor sie für Server-seitige Requests
verwendet werden. Blockiert Zugriff auf:
- Private IP-Bereiche (10.x, 172.16-31.x, 192.168.x)
- Localhost / Loopback (127.x, ::1)
- Link-Local (169.254.x, fe80::)
- Docker-interne Hostnamen (*.internal, *.local, Containernamen)
- Cloud Metadata Endpoints (169.254.169.254)

Usage:
    from auth.url_validator import validate_url_not_internal

    # Raises ValueError bei internen/gefährlichen URLs
    validate_url_not_internal(user_provided_url)

    # Oder als Boolean-Check
    from auth.url_validator import is_url_safe
    if not is_url_safe(url):
        return error_response
"""

import ipaddress
import logging
import socket
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Bekannte Docker/Container-interne Hostnamen die nicht von außen erreichbar sein sollten
_BLOCKED_HOSTNAMES = frozenset({
    'localhost',
    'host.docker.internal',
    'gateway.docker.internal',
    'kubernetes.default',
    'metadata.google.internal',
    # LLARS-spezifische Container-Namen aus docker-compose
    'llars-db',
    'llars-redis',
    'llars-chromadb',
    'llars-flask',
    'authentik-server',
    'authentik-worker',
    'authentik-redis',
    'authentik-db',
})

# Blocked TLDs / Suffixes für interne Service-Discovery
_BLOCKED_SUFFIXES = (
    '.internal',
    '.local',
    '.svc',
    '.cluster.local',
    '.docker',
)

# Cloud Metadata IPs (AWS, GCP, Azure)
_METADATA_IPS = frozenset({
    '169.254.169.254',  # AWS / GCP / Azure Instance Metadata
    'fd00:ec2::254',    # AWS IMDSv2 IPv6
})


def _is_private_ip(ip_str: str) -> bool:
    """Prüft ob eine IP-Adresse privat, loopback oder link-local ist."""
    try:
        addr = ipaddress.ip_address(ip_str)
        return (
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_reserved
            or addr.is_multicast
            or ip_str in _METADATA_IPS
        )
    except ValueError:
        # Kein gültiges IP-Format → kein IP-Check möglich
        return False


def _is_blocked_hostname(hostname: str) -> bool:
    """Prüft ob ein Hostname auf einer Blocklist steht."""
    hostname_lower = hostname.lower().strip('.')

    if hostname_lower in _BLOCKED_HOSTNAMES:
        return True

    for suffix in _BLOCKED_SUFFIXES:
        if hostname_lower.endswith(suffix):
            return True

    return False


def validate_url_not_internal(url: str, allow_private: bool = False) -> str:
    """
    Validiert eine URL gegen SSRF-Angriffe.

    Prüft sowohl den Hostnamen als auch die aufgelöste IP-Adresse,
    um DNS-Rebinding-Angriffe zu verhindern.

    Args:
        url: Die zu validierende URL
        allow_private: Wenn True, werden private IPs erlaubt (für Admin-only Endpoints)

    Returns:
        Die validierte URL (stripped)

    Raises:
        ValueError: URL ist intern/gefährlich oder ungültig
    """
    if not url or not isinstance(url, str):
        raise ValueError('URL is required')

    url = url.strip()

    # Schema-Validierung: Nur http(s) erlaubt
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        raise ValueError(f'Only http:// and https:// URLs are allowed, got: {parsed.scheme}://')

    hostname = parsed.hostname
    if not hostname:
        raise ValueError('URL must contain a valid hostname')

    # Hostname-Blocklist prüfen
    if _is_blocked_hostname(hostname):
        logger.warning(f'SSRF blocked: hostname "{hostname}" is on the blocklist')
        raise ValueError(f'URL points to a blocked internal hostname')

    # Direkte IP-Prüfung (wenn User eine IP statt Hostname angibt)
    if _is_private_ip(hostname) and not allow_private:
        logger.warning(f'SSRF blocked: direct IP "{hostname}" is private/internal')
        raise ValueError(f'URL points to a private or internal IP address')

    # DNS-Auflösung prüfen (verhindert DNS-Rebinding Angriffe)
    if not allow_private:
        try:
            resolved_ips = socket.getaddrinfo(hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)
            for family, _type, _proto, _canonname, sockaddr in resolved_ips:
                ip_str = sockaddr[0]
                if _is_private_ip(ip_str):
                    logger.warning(
                        f'SSRF blocked: "{hostname}" resolves to private IP {ip_str}'
                    )
                    raise ValueError(f'URL hostname resolves to a private or internal IP address')
        except socket.gaierror:
            # DNS-Auflösung fehlgeschlagen - URL ist trotzdem syntaktisch valide,
            # der spätere Request wird den Fehler melden
            pass

    return url


def is_url_safe(url: str, allow_private: bool = False) -> bool:
    """
    Boolean-Variante von validate_url_not_internal.

    Returns:
        True wenn URL sicher ist, False sonst
    """
    try:
        validate_url_not_internal(url, allow_private=allow_private)
        return True
    except (ValueError, TypeError):
        return False
