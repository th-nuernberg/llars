"""
SSRF defence: shared URL-safety guard.

Single source of truth for "is this URL safe to crawl from a backend
worker?". Used by:

- ``schemas.api_v1.chatbot_api.WizardCrawlSpec`` (request-time check
  on the v1 surface)
- ``services.chatbot.chatbot_creator.ChatbotCreator.create_wizard_chatbot``
  / ``start_crawl`` (defence-in-depth at the service layer, so legacy
  routes such as ``/api/chatbots/<id>/wizard/crawl`` and any future
  caller benefit too)

Three layers of check, in order of cost:

1. Literal IP — RFC1918 / loopback / link-local / reserved / multicast /
   unspecified / IPv4-mapped IPv6.
2. Hostname blocklist — well-known cloud-metadata + cluster-internal
   names, plus wildcard-DNS-to-IP suffix providers (.nip.io, .sslip.io,
   .xip.io) which let attackers smuggle 169.254.169.254 past an exact
   host match via ``foo.169.254.169.254.nip.io`` (H1 finding).
3. Best-effort DNS resolve — every A/AAAA returned for the host runs
   the same IP rules. Catches attacker-owned CNAMEs that resolve to
   internal IPs.

DNS notes
---------
``socket.setdefaulttimeout()`` is process-global; using it from a
validator races concurrent requests — thread A's ``finally`` clears
the cap mid-flight while thread B is still in ``getaddrinfo``, so a
hostile DNS could hang an unrelated sibling indefinitely. Use a
per-call ``ThreadPoolExecutor`` with ``future.result(timeout=...)``
instead. The resolver thread leaks at most until DNS responds
(best-effort), but the validating request always returns within
``DNS_TIMEOUT`` seconds.
"""

from __future__ import annotations

import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from urllib.parse import urlparse


DNS_TIMEOUT = 2.0

# Hostnames that are never allowed even if DNS would point them at a
# routable address. Cloud-metadata endpoints + cluster-internal DNS.
BLOCKED_HOSTS = {
    "localhost",
    "ip6-localhost",
    "ip6-loopback",
    "localhost.localdomain",
    "metadata.google.internal",
    "metadata.goog",
    "instance-data.ec2.internal",
    "kubernetes.default.svc",
    "kubernetes.default",
    "kubernetes",
}

# Suffixes whose subdomains are blocked. ``.nip.io`` & friends resolve
# any literal IP embedded in the hostname back to that IP, so a host
# of "foo.169.254.169.254.nip.io" is functionally an attempt to reach
# 169.254.169.254 even though the literal-IP layer didn't catch it.
BLOCKED_SUFFIXES = (
    ".localhost",
    ".internal",
    ".cluster.local",
    ".nip.io",
    ".sslip.io",
    ".xip.io",
)


class UnsafeUrlError(ValueError):
    """The given URL points at non-routable / internal-only space.

    Subclasses ValueError so existing Pydantic field-validators continue
    to surface it as a clean 400, and service-layer callers can raise it
    without adding a new exception family.
    """


def _is_internal_ip(ip_str: str) -> bool:
    """True if the literal IP is non-routable from a public crawler.

    IPv4-mapped IPv6 (``::ffff:a9fe:a9fe`` → ``169.254.169.254``) is
    flattened to the IPv4 form before the rule check; ``ipaddress``
    already classifies it correctly, but the explicit unwrap keeps the
    intent obvious in audits.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            ip = ip.ipv4_mapped
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        )
    except ValueError:
        return False


def assert_external_url_safe(url: str) -> None:
    """Raise :class:`UnsafeUrlError` if ``url`` shouldn't be fetched.

    Pure check — does not normalize the URL or modify any state. Safe
    to call from request-time validators (cheap unless step-3 DNS
    fires) and from background workers as a final fence before issuing
    the actual HTTP request.
    """
    if not url or not isinstance(url, str):
        raise UnsafeUrlError("url is empty or not a string")

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().strip()
    if not host:
        raise UnsafeUrlError("url has no host")

    if _is_internal_ip(host):
        raise UnsafeUrlError(
            f"url host {host} is a non-routable / internal address "
            f"and is not crawlable from this surface"
        )

    if host in BLOCKED_HOSTS or any(host.endswith(s) for s in BLOCKED_SUFFIXES):
        raise UnsafeUrlError(
            f"url host {host} is on the internal-host blocklist "
            f"and is not crawlable from this surface"
        )

    # Best-effort DNS resolve. Per-call executor so a hostile-slow DNS
    # cannot poison sibling validators via process-global defaults.
    infos = None
    try:
        with ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(socket.getaddrinfo, host, None)
            try:
                infos = future.result(timeout=DNS_TIMEOUT)
            except FuturesTimeout:
                infos = None
    except (socket.gaierror, OSError):
        infos = None

    if infos:
        for _fam, _, _, _, sockaddr in infos:
            ip_str = sockaddr[0] if sockaddr else None
            if ip_str and "%" in ip_str:
                # Strip IPv6 zone-id ("fe80::1%eth0") before parsing.
                ip_str = ip_str.split("%", 1)[0]
            if ip_str and _is_internal_ip(ip_str):
                raise UnsafeUrlError(
                    f"url host {host} resolves to internal IP {ip_str} "
                    f"and is not crawlable from this surface"
                )
