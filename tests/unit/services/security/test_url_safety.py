"""
Unit tests for the shared SSRF guard.

Test IDs: SEC-URLSAFE-001..010.

Coverage focus is the corners that previously slipped past the original
``WizardCrawlSpec._block_internal_hosts`` implementation:

- F1: literal-IP rejection (RFC1918, loopback, link-local, cloud-meta).
- H1: wildcard-DNS-to-IP suffix bypass (.nip.io / .sslip.io / .xip.io).
- H1+: hostname blocklist for cluster-internal DNS.
- F1 / DNS-CNAME path: hosts that resolve to internal IPs.
- Empty / malformed input.
"""

from __future__ import annotations

import pytest

from services.security.url_safety import (
    UnsafeUrlError,
    assert_external_url_safe,
)


class TestSafeHosts:
    def test_SEC_URLSAFE_001_public_https_passes(self):
        # No exception → URL is considered safe to crawl.
        assert_external_url_safe("https://example.com")

    def test_SEC_URLSAFE_002_public_http_passes(self):
        assert_external_url_safe("http://example.com/path?q=1")


class TestLiteralIp:
    @pytest.mark.parametrize("url", [
        "http://169.254.169.254/latest/meta-data/",  # AWS IMDS
        "http://10.0.0.1/admin",                     # RFC1918
        "http://192.168.1.1/",                       # RFC1918
        "http://172.16.0.5/",                        # RFC1918
        "http://127.0.0.1/",                         # loopback
        "http://[::1]/",                             # IPv6 loopback
        "http://0.0.0.0/",                           # unspecified
    ])
    def test_SEC_URLSAFE_003_literal_internal_ip_rejected(self, url):
        with pytest.raises(UnsafeUrlError):
            assert_external_url_safe(url)


class TestHostnameBlocklist:
    @pytest.mark.parametrize("url", [
        "http://localhost/",
        "http://metadata.google.internal/",
        "http://kubernetes.default.svc/",
        "http://kubernetes/",
        "http://instance-data.ec2.internal/",
    ])
    def test_SEC_URLSAFE_004_blocked_host_rejected(self, url):
        with pytest.raises(UnsafeUrlError):
            assert_external_url_safe(url)

    @pytest.mark.parametrize("url", [
        "http://something.localhost/",
        "http://api.cluster.local/",
        "http://anything.internal/",
    ])
    def test_SEC_URLSAFE_005_blocked_suffix_rejected(self, url):
        with pytest.raises(UnsafeUrlError):
            assert_external_url_safe(url)


class TestNipIoBypass:
    """H1: regression — wildcard-DNS suffixes must not let an attacker
    smuggle internal IPs past the literal-IP layer."""

    @pytest.mark.parametrize("url", [
        "http://169.254.169.254.nip.io/latest/meta-data/",
        "http://foo.169.254.169.254.nip.io/",
        "http://10.0.0.1.nip.io/",
        "http://10.0.0.1.sslip.io/",
        "http://10.0.0.1.xip.io/",
    ])
    def test_SEC_URLSAFE_006_nip_io_variants_rejected(self, url):
        with pytest.raises(UnsafeUrlError):
            assert_external_url_safe(url)


class TestEmptyOrMalformed:
    def test_SEC_URLSAFE_007_empty_string_rejected(self):
        with pytest.raises(UnsafeUrlError):
            assert_external_url_safe("")

    def test_SEC_URLSAFE_008_no_host_rejected(self):
        with pytest.raises(UnsafeUrlError):
            assert_external_url_safe("file:///etc/passwd")

    def test_SEC_URLSAFE_009_non_string_rejected(self):
        with pytest.raises(UnsafeUrlError):
            assert_external_url_safe(None)  # type: ignore[arg-type]


class TestDnsResolution:
    """The DNS layer is best-effort — when it does fire, internal A
    records must be rejected. Hand-craft the resolver so we don't
    depend on the host's network state."""

    def test_SEC_URLSAFE_010_dns_to_internal_ip_rejected(self, monkeypatch):
        # Pretend "evil.example" resolves to 169.254.169.254.
        def fake_getaddrinfo(host, port, *args, **kwargs):
            return [(2, 1, 6, "", ("169.254.169.254", 0))]

        # Patch the symbol the module actually uses.
        from services.security import url_safety as mod
        monkeypatch.setattr(mod.socket, "getaddrinfo", fake_getaddrinfo)

        with pytest.raises(UnsafeUrlError):
            assert_external_url_safe("http://evil.example/")
