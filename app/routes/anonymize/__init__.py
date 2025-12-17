"""
Anonymize Routes

Offline-first pseudonymization endpoints (text + DOCX/PDF upload).

Mounted under: /api/anonymize
"""

from flask import Blueprint

anonymize_bp = Blueprint("anonymize", __name__, url_prefix="/api/anonymize")

# Attach routes
from routes.anonymize.anonymize_routes import *  # noqa: F401,F403

__all__ = ["anonymize_bp"]

