"""
Versioned, hashable consent texts for LLARS research-study referrals.

Each version is a Python module that exports the canonical UTF-8 text
(DE + EN) and pre-computes their SHA-256 digests. The digests get
written into the consent audit row so we can prove later *which exact
text the user clicked through to*, per BayLDA OH Einwilligung §VI
("Aufbewahren von Einwilligungen", Rn. 118–124) and Art. 5(2) DSGVO
Rechenschaftspflicht.

Add a new version when the text changes:
    consents/study_v4_2026_07.py  →  CONSENT_VERSION='study-consent-v4-…'
"""

from .study_v3_2026_05 import (
    CONSENT_VERSION,
    CONSENT_TEXT_DE,
    CONSENT_TEXT_EN,
    CONSENT_TEXT_SHA256_DE,
    CONSENT_TEXT_SHA256_EN,
)

__all__ = [
    'CONSENT_VERSION',
    'CONSENT_TEXT_DE',
    'CONSENT_TEXT_EN',
    'CONSENT_TEXT_SHA256_DE',
    'CONSENT_TEXT_SHA256_EN',
]
