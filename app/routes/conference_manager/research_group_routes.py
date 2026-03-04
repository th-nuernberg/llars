"""
Research Group Routes - group management, membership, and access requests.
"""

import logging

from flask import Blueprint, jsonify, request, g

from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError, ForbiddenError
from decorators.permission_decorator import require_permission
from services.research_group_service import ResearchGroupService

logger = logging.getLogger(__name__)

research_group_bp = Blueprint("research_groups", __name__)


# ── Group CRUD ───────────────────────────────────────────────


@research_group_bp.route("/groups", methods=["GET"])
@require_permission("feature:conference_manager:view")
@handle_api_errors(logger_name="conference_manager")
def list_groups():
    """List all research groups (brief)."""
    search = request.args.get("search")
    groups = ResearchGroupService.list_groups(search=search)
    return jsonify({"success": True, "groups": groups}), 200


@research_group_bp.route("/groups/my", methods=["GET"])
@require_permission("feature:conference_manager:view")
@handle_api_errors(logger_name="conference_manager")
def get_my_groups():
    """Get groups the current user belongs to."""
    username = g.authentik_user.username
    groups = ResearchGroupService.get_user_groups(username)
    return jsonify({"success": True, "groups": groups}), 200


@research_group_bp.route("/groups/<int:group_id>", methods=["GET"])
@require_permission("feature:conference_manager:view")
@handle_api_errors(logger_name="conference_manager")
def get_group(group_id):
    """Get group details (members/admins only)."""
    username = g.authentik_user.username
    if not ResearchGroupService.check_group_access(group_id, username):
        raise ForbiddenError("Not a member of this group")

    group = ResearchGroupService.get_group(group_id)
    if not group:
        raise NotFoundError(f"Group {group_id} not found")

    group['user_role'] = ResearchGroupService.get_user_role_in_group(group_id, username)
    group['stats'] = ResearchGroupService.get_group_stats(group_id)
    return jsonify({"success": True, "group": group}), 200


@research_group_bp.route("/groups", methods=["POST"])
@require_permission("admin:system:configure")
@handle_api_errors(logger_name="conference_manager")
def create_group():
    """Create a new research group (admin only)."""
    data = request.get_json()
    if not data or not data.get("name"):
        raise ValidationError("Group name is required")

    username = g.authentik_user.username
    group = ResearchGroupService.create_group(data, username)
    return jsonify({"success": True, "group": group}), 201


@research_group_bp.route("/groups/<int:group_id>", methods=["PUT"])
@require_permission("feature:conference_manager:edit")
@handle_api_errors(logger_name="conference_manager")
def update_group(group_id):
    """Update a group (owner/admin only)."""
    username = g.authentik_user.username
    role = ResearchGroupService.get_user_role_in_group(group_id, username)

    from services.permission_service import PermissionService
    if role != 'owner' and not PermissionService.check_permission(username, "admin:permissions:manage"):
        raise ForbiddenError("Only group owners or admins can edit groups")

    data = request.get_json()
    if not data:
        raise ValidationError("Request body is required")

    group = ResearchGroupService.update_group(group_id, data, username)
    if not group:
        raise NotFoundError(f"Group {group_id} not found")
    return jsonify({"success": True, "group": group}), 200


@research_group_bp.route("/groups/<int:group_id>", methods=["DELETE"])
@require_permission("admin:system:configure")
@handle_api_errors(logger_name="conference_manager")
def delete_group(group_id):
    """Delete a group (admin only)."""
    deleted = ResearchGroupService.delete_group(group_id)
    if not deleted:
        raise NotFoundError(f"Group {group_id} not found")
    return jsonify({"success": True}), 200


# ── Members ──────────────────────────────────────────────────


@research_group_bp.route("/groups/<int:group_id>/members", methods=["GET"])
@require_permission("feature:conference_manager:view")
@handle_api_errors(logger_name="conference_manager")
def get_members(group_id):
    """Get group member list."""
    username = g.authentik_user.username
    if not ResearchGroupService.check_group_access(group_id, username):
        raise ForbiddenError("Not a member of this group")

    members = ResearchGroupService.get_members(group_id)
    return jsonify({"success": True, "members": members}), 200


@research_group_bp.route("/groups/<int:group_id>/members", methods=["POST"])
@require_permission("feature:conference_manager:edit")
@handle_api_errors(logger_name="conference_manager")
def add_member(group_id):
    """Add a member to the group (owner/member/admin)."""
    username = g.authentik_user.username
    if not ResearchGroupService.check_group_access(group_id, username, require_write=True):
        raise ForbiddenError("No write access to this group")

    data = request.get_json()
    if not data or not data.get("user_id"):
        raise ValidationError("user_id is required")

    role = data.get("role", "member")
    member = ResearchGroupService.add_member(
        group_id, data["user_id"], role, username
    )
    if not member:
        raise NotFoundError(f"Group {group_id} not found")
    return jsonify({"success": True, "member": member}), 201


@research_group_bp.route("/groups/<int:group_id>/members/<int:member_id>", methods=["PUT"])
@require_permission("feature:conference_manager:edit")
@handle_api_errors(logger_name="conference_manager")
def update_member_role(group_id, member_id):
    """Change a member's role (owner/admin only)."""
    username = g.authentik_user.username
    role = ResearchGroupService.get_user_role_in_group(group_id, username)

    from services.permission_service import PermissionService
    if role != 'owner' and not PermissionService.check_permission(username, "admin:permissions:manage"):
        raise ForbiddenError("Only group owners or admins can change roles")

    data = request.get_json()
    if not data or not data.get("role"):
        raise ValidationError("Role is required")

    member = ResearchGroupService.update_member_role(member_id, data["role"], username)
    if not member:
        raise NotFoundError(f"Member {member_id} not found")
    return jsonify({"success": True, "member": member}), 200


@research_group_bp.route("/groups/<int:group_id>/members/<int:member_id>", methods=["DELETE"])
@require_permission("feature:conference_manager:edit")
@handle_api_errors(logger_name="conference_manager")
def remove_member(group_id, member_id):
    """Remove a member (owner/admin/self)."""
    username = g.authentik_user.username

    from db.models import ResearchGroupMember
    member = ResearchGroupMember.query.get(member_id)
    if not member:
        raise NotFoundError(f"Member {member_id} not found")

    is_self = member.user and member.user.username == username

    from services.permission_service import PermissionService
    role = ResearchGroupService.get_user_role_in_group(group_id, username)
    if not is_self and role != 'owner' and not PermissionService.check_permission(username, "admin:permissions:manage"):
        raise ForbiddenError("Only group owners, admins, or the member themselves can remove members")

    removed = ResearchGroupService.remove_member(member_id, username)
    if not removed:
        raise NotFoundError(f"Member {member_id} not found")
    return jsonify({"success": True}), 200


# ── Access Requests ──────────────────────────────────────────


@research_group_bp.route("/groups/<int:group_id>/access-requests", methods=["POST"])
@require_permission("feature:conference_manager:view")
@handle_api_errors(logger_name="conference_manager")
def create_access_request(group_id):
    """Request access to a group."""
    username = g.authentik_user.username
    data = request.get_json() or {}

    result = ResearchGroupService.create_access_request(
        group_id, username, data.get("message")
    )
    if not result:
        raise ValidationError("Cannot create request (group not found or already a member)")
    return jsonify({"success": True, "request": result}), 201


@research_group_bp.route("/groups/access-requests", methods=["GET"])
@require_permission("feature:conference_manager:view")
@handle_api_errors(logger_name="conference_manager")
def list_pending_requests():
    """List pending access requests for groups where user is owner/member."""
    username = g.authentik_user.username
    requests = ResearchGroupService.list_pending_requests(username)
    return jsonify({"success": True, "requests": requests}), 200


@research_group_bp.route("/groups/<int:group_id>/access-requests", methods=["GET"])
@require_permission("feature:conference_manager:view")
@handle_api_errors(logger_name="conference_manager")
def list_group_requests(group_id):
    """List all access requests for a specific group."""
    username = g.authentik_user.username
    if not ResearchGroupService.check_group_access(group_id, username):
        raise ForbiddenError("Not a member of this group")

    requests = ResearchGroupService.list_group_requests(group_id)
    return jsonify({"success": True, "requests": requests}), 200


@research_group_bp.route("/access-requests/<int:request_id>", methods=["PUT"])
@require_permission("feature:conference_manager:edit")
@handle_api_errors(logger_name="conference_manager")
def resolve_access_request(request_id):
    """Approve or reject an access request."""
    username = g.authentik_user.username
    data = request.get_json()
    if not data or not data.get("action"):
        raise ValidationError("Action (approve/reject) is required")

    action = data["action"]
    if action not in ("approve", "reject"):
        raise ValidationError("Action must be 'approve' or 'reject'")

    # Verify user can manage this request's group
    from db.models import ResearchGroupAccessRequest
    req = ResearchGroupAccessRequest.query.get(request_id)
    if not req:
        raise NotFoundError(f"Request {request_id} not found")

    if not ResearchGroupService.check_group_access(req.group_id, username, require_write=True):
        raise ForbiddenError("No write access to this group")

    result = ResearchGroupService.resolve_access_request(request_id, action, username)
    if not result:
        raise NotFoundError(f"Request {request_id} not found or already resolved")
    return jsonify({"success": True, "result": result}), 200
