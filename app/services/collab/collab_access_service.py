"""
Collaboration Access Service

Provides unified access control for LaTeX and Markdown collaboration features.
This eliminates code duplication between latex_collab_routes.py and markdown_collab_routes.py.

Usage:
    from services.collab import CollabAccessService

    # For LaTeX
    CollabAccessService.require_workspace_access(
        workspace, username,
        member_model=LatexWorkspaceMember
    )

    # For Markdown
    CollabAccessService.require_workspace_access(
        workspace, username,
        member_model=MarkdownWorkspaceMember
    )
"""

from typing import Optional, Type, Any

from decorators.error_handler import ForbiddenError
from services.permission_service import PermissionService


class CollabAccessService:
    """
    Centralized access control for collaboration workspaces and documents.

    Supports both LaTeX and Markdown collaboration by accepting the appropriate
    model classes as parameters.
    """

    # Permission used to identify admin users
    ADMIN_PERMISSION = "admin:permissions:manage"

    @classmethod
    def is_admin(cls, username: Optional[str]) -> bool:
        """
        Check if a user has admin privileges.

        Args:
            username: The username to check

        Returns:
            True if user is admin, False otherwise
        """
        if not username:
            return False
        return PermissionService.check_permission(username, cls.ADMIN_PERMISSION)

    @classmethod
    def require_workspace_access(
        cls,
        workspace: Any,
        username: str,
        member_model: Type[Any],
        error_message: str = "Kein Zugriff auf diesen Workspace"
    ) -> None:
        """
        Verify user has access to a workspace (owner, member, or admin).

        Args:
            workspace: The workspace object (LatexWorkspace or MarkdownWorkspace)
            username: The username requesting access
            member_model: The member model class (LatexWorkspaceMember or MarkdownWorkspaceMember)
            error_message: Custom error message for access denial

        Raises:
            ForbiddenError: If user does not have access
        """
        # Admins always have access
        if cls.is_admin(username):
            return

        # Owner always has access
        if workspace.owner_username == username:
            return

        # Check membership
        member = member_model.query.filter_by(
            workspace_id=workspace.id,
            username=username
        ).first()

        if not member:
            raise ForbiddenError(error_message)

    @classmethod
    def require_workspace_manage(
        cls,
        workspace: Any,
        username: str,
        error_message: str = "Kein Zugriff auf diesen Workspace"
    ) -> None:
        """
        Verify user can manage a workspace (owner or admin only).

        Used for operations like:
        - Adding/removing members
        - Changing workspace settings
        - Deleting workspace

        Args:
            workspace: The workspace object
            username: The username requesting access
            error_message: Custom error message for access denial

        Raises:
            ForbiddenError: If user is not owner or admin
        """
        # Admins always have manage access
        if cls.is_admin(username):
            return

        # Only owner can manage
        if workspace.owner_username != username:
            raise ForbiddenError(error_message)

    @classmethod
    def require_document_access(
        cls,
        document: Any,
        username: str,
        member_model: Type[Any],
        error_message: str = "Kein Zugriff auf dieses Dokument"
    ) -> None:
        """
        Verify user has access to a document via its workspace.

        Args:
            document: The document object (LatexDocument or MarkdownDocument)
            username: The username requesting access
            member_model: The member model class
            error_message: Custom error message for access denial

        Raises:
            ForbiddenError: If user does not have access
        """
        # Admins always have access
        if cls.is_admin(username):
            return

        # Check workspace ownership
        if document.workspace and document.workspace.owner_username == username:
            return

        # Check workspace membership
        member = member_model.query.filter_by(
            workspace_id=document.workspace_id,
            username=username
        ).first()

        if member:
            return

        raise ForbiddenError(error_message)

    @classmethod
    def has_workspace_access(
        cls,
        workspace: Any,
        username: str,
        member_model: Type[Any]
    ) -> bool:
        """
        Check if user has access to a workspace (non-throwing version).

        Args:
            workspace: The workspace object
            username: The username to check
            member_model: The member model class

        Returns:
            True if user has access, False otherwise
        """
        try:
            cls.require_workspace_access(workspace, username, member_model)
            return True
        except ForbiddenError:
            return False

    @classmethod
    def has_workspace_manage(cls, workspace: Any, username: str) -> bool:
        """
        Check if user can manage a workspace (non-throwing version).

        Args:
            workspace: The workspace object
            username: The username to check

        Returns:
            True if user can manage, False otherwise
        """
        try:
            cls.require_workspace_manage(workspace, username)
            return True
        except ForbiddenError:
            return False

    @classmethod
    def has_document_access(
        cls,
        document: Any,
        username: str,
        member_model: Type[Any]
    ) -> bool:
        """
        Check if user has access to a document (non-throwing version).

        Args:
            document: The document object
            username: The username to check
            member_model: The member model class

        Returns:
            True if user has access, False otherwise
        """
        try:
            cls.require_document_access(document, username, member_model)
            return True
        except ForbiddenError:
            return False
