"""
OnCoCo Analysis Service Module

Provides sentence-level classification of counseling conversations
using the OnCoCo (Online Counseling Conversations) model.
"""

from .oncoco_service import (
    OnCoCoService,
    get_oncoco_service,
    ClassificationResult,
    MessageAnalysis,
    ThreadAnalysis
)
from .oncoco_labels import (
    ONCOCO_LABELS,
    LABEL_HIERARCHY,
    get_label_level2,
    get_label_display_name,
    get_label_role,
    get_label_category
)

__all__ = [
    'OnCoCoService',
    'get_oncoco_service',
    'ClassificationResult',
    'MessageAnalysis',
    'ThreadAnalysis',
    'ONCOCO_LABELS',
    'LABEL_HIERARCHY',
    'get_label_level2',
    'get_label_display_name',
    'get_label_role',
    'get_label_category'
]
