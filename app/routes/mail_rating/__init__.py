"""
Mail Rating Module
Refactored from MailRatingRoutes.py into focused sub-modules.

Handles email thread rating functionality including:
- Thread listing and details
- Mail history (thread-level) ratings
- Individual message ratings
- Admin statistics
"""

# Import all route modules to register them with the blueprint
from . import mail_rating_threads
from . import mail_rating_history
from . import mail_rating_messages
from . import mail_rating_stats

__all__ = [
    'mail_rating_threads',
    'mail_rating_history',
    'mail_rating_messages',
    'mail_rating_stats'
]
