"""
Decorators for LLars Application

This module contains decorators for route protection and access control.
"""

from .permission_decorator import require_permission

__all__ = ['require_permission']
