"""
Research Group Service

Handles research group CRUD, membership management, and access requests
for the Conference Manager's multi-group feature.
"""

import re
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from db.database import db

logger = logging.getLogger(__name__)


def _slugify(name: str) -> str:
    """Convert a group name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    return slug.strip('-')


class ResearchGroupService:
    """Service for managing research groups and memberships."""

    # ── Group CRUD ───────────────────────────────────────────

    @staticmethod
    def list_groups(search: Optional[str] = None) -> List[Dict[str, Any]]:
        from db.models import ResearchGroup

        query = ResearchGroup.query.order_by(ResearchGroup.name.asc())
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    ResearchGroup.name.ilike(pattern),
                    ResearchGroup.slug.ilike(pattern),
                )
            )
        groups = [g.to_dict() for g in query.all()]
        for g in groups:
            g['stats'] = ResearchGroupService.get_group_stats(g['id'])
        return groups

    @staticmethod
    def get_user_groups(username: str) -> List[Dict[str, Any]]:
        """Get all groups where user is a member."""
        from db.models import ResearchGroup, ResearchGroupMember, User

        user = User.query.filter_by(username=username).first()
        if not user:
            return []

        memberships = (
            ResearchGroupMember.query
            .filter_by(user_id=user.id)
            .all()
        )

        results = []
        for m in memberships:
            group_dict = m.group.to_dict()
            group_dict['user_role'] = m.role.value
            results.append(group_dict)

        return results

    @staticmethod
    def get_group(group_id: int) -> Optional[Dict[str, Any]]:
        from db.models import ResearchGroup

        group = ResearchGroup.query.get(group_id)
        return group.to_dict() if group else None

    @staticmethod
    def create_group(data: Dict[str, Any], username: str) -> Dict[str, Any]:
        from db.models import ResearchGroup, ResearchGroupMember, ResearchGroupRole, User

        slug = _slugify(data.get('slug') or data['name'])

        # Ensure unique slug
        existing = ResearchGroup.query.filter_by(slug=slug).first()
        if existing:
            suffix = 1
            while ResearchGroup.query.filter_by(slug=f"{slug}-{suffix}").first():
                suffix += 1
            slug = f"{slug}-{suffix}"

        group = ResearchGroup(
            name=data['name'],
            slug=slug,
            description=data.get('description'),
            created_by=username,
        )
        db.session.add(group)
        db.session.flush()

        # Add creator as owner
        user = User.query.filter_by(username=username).first()
        if user:
            member = ResearchGroupMember(
                group_id=group.id,
                user_id=user.id,
                role=ResearchGroupRole.OWNER,
                added_by=username,
            )
            db.session.add(member)

        db.session.commit()
        return group.to_dict()

    @staticmethod
    def update_group(group_id: int, data: Dict[str, Any], username: str) -> Optional[Dict[str, Any]]:
        from db.models import ResearchGroup

        group = ResearchGroup.query.get(group_id)
        if not group:
            return None

        if 'name' in data:
            group.name = data['name']
        if 'description' in data:
            group.description = data['description']
        if 'slug' in data:
            new_slug = _slugify(data['slug'])
            existing = ResearchGroup.query.filter(
                ResearchGroup.slug == new_slug,
                ResearchGroup.id != group_id,
            ).first()
            if not existing:
                group.slug = new_slug

        db.session.commit()
        return group.to_dict()

    @staticmethod
    def delete_group(group_id: int) -> bool:
        from db.models import ResearchGroup

        group = ResearchGroup.query.get(group_id)
        if not group:
            return False
        db.session.delete(group)
        db.session.commit()
        return True

    # ── Membership ───────────────────────────────────────────

    @staticmethod
    def get_members(group_id: int) -> List[Dict[str, Any]]:
        from db.models import ResearchGroupMember

        members = (
            ResearchGroupMember.query
            .filter_by(group_id=group_id)
            .order_by(ResearchGroupMember.role.asc(), ResearchGroupMember.added_at.asc())
            .all()
        )
        return [m.to_dict() for m in members]

    @staticmethod
    def add_member(group_id: int, user_id: int, role: str, added_by: str) -> Optional[Dict[str, Any]]:
        from db.models import ResearchGroupMember, ResearchGroupRole, ResearchGroup

        group = ResearchGroup.query.get(group_id)
        if not group:
            return None

        # Check if already member
        existing = ResearchGroupMember.query.filter_by(
            group_id=group_id, user_id=user_id
        ).first()
        if existing:
            return existing.to_dict()

        try:
            member_role = ResearchGroupRole(role)
        except ValueError:
            member_role = ResearchGroupRole.MEMBER

        member = ResearchGroupMember(
            group_id=group_id,
            user_id=user_id,
            role=member_role,
            added_by=added_by,
        )
        db.session.add(member)
        db.session.commit()
        return member.to_dict()

    @staticmethod
    def update_member_role(member_id: int, role: str, username: str) -> Optional[Dict[str, Any]]:
        from db.models import ResearchGroupMember, ResearchGroupRole

        member = ResearchGroupMember.query.get(member_id)
        if not member:
            return None

        try:
            member.role = ResearchGroupRole(role)
        except ValueError:
            return None

        db.session.commit()
        return member.to_dict()

    @staticmethod
    def remove_member(member_id: int, username: str) -> bool:
        from db.models import ResearchGroupMember

        member = ResearchGroupMember.query.get(member_id)
        if not member:
            return False

        db.session.delete(member)
        db.session.commit()
        return True

    # ── Access Control ───────────────────────────────────────

    @staticmethod
    def get_user_role_in_group(group_id: int, username: str) -> Optional[str]:
        """Get user's role in a group, or None if not a member."""
        from db.models import ResearchGroupMember, User

        user = User.query.filter_by(username=username).first()
        if not user:
            return None

        member = ResearchGroupMember.query.filter_by(
            group_id=group_id, user_id=user.id
        ).first()
        return member.role.value if member else None

    @staticmethod
    def check_group_access(group_id: int, username: str, require_write: bool = False) -> bool:
        """Check if user has access to a group. Admins always have access."""
        from db.models import User

        user = User.query.filter_by(username=username).first()
        if not user:
            return False

        # Check admin
        from services.permission_service import PermissionService
        if PermissionService.check_permission(username, "admin:permissions:manage"):
            return True

        role = ResearchGroupService.get_user_role_in_group(group_id, username)
        if not role:
            return False

        if require_write and role == 'viewer':
            return False

        return True

    # ── Access Requests ──────────────────────────────────────

    @staticmethod
    def create_access_request(group_id: int, username: str, message: Optional[str] = None) -> Optional[Dict[str, Any]]:
        from db.models import ResearchGroup, ResearchGroupAccessRequest, ResearchGroupRequestStatus

        group = ResearchGroup.query.get(group_id)
        if not group:
            return None

        # Check if already a member
        role = ResearchGroupService.get_user_role_in_group(group_id, username)
        if role:
            return None

        # Check existing pending request
        existing = ResearchGroupAccessRequest.query.filter_by(
            group_id=group_id,
            requester_username=username,
            status=ResearchGroupRequestStatus.PENDING,
        ).first()
        if existing:
            return {
                "id": existing.id,
                "status": "already_pending",
            }

        # Delete any previous rejected request to allow re-request
        old_rejected = ResearchGroupAccessRequest.query.filter_by(
            group_id=group_id,
            requester_username=username,
            status=ResearchGroupRequestStatus.REJECTED,
        ).first()
        if old_rejected:
            db.session.delete(old_rejected)
            db.session.flush()

        req = ResearchGroupAccessRequest(
            group_id=group_id,
            requester_username=username,
            message=message,
        )
        db.session.add(req)
        db.session.commit()

        return {
            "id": req.id,
            "group_id": group_id,
            "status": "pending",
        }

    @staticmethod
    def list_pending_requests(username: str) -> List[Dict[str, Any]]:
        """List pending access requests for groups where user is owner/member."""
        from db.models import (
            ResearchGroupAccessRequest, ResearchGroupMember,
            ResearchGroupRequestStatus, ResearchGroupRole, User,
        )

        user = User.query.filter_by(username=username).first()
        if not user:
            return []

        # Get groups where user is owner or member
        memberships = ResearchGroupMember.query.filter(
            ResearchGroupMember.user_id == user.id,
            ResearchGroupMember.role.in_([ResearchGroupRole.OWNER, ResearchGroupRole.MEMBER]),
        ).all()

        group_ids = [m.group_id for m in memberships]
        if not group_ids:
            return []

        requests = (
            ResearchGroupAccessRequest.query
            .filter(
                ResearchGroupAccessRequest.group_id.in_(group_ids),
                ResearchGroupAccessRequest.status == ResearchGroupRequestStatus.PENDING,
            )
            .order_by(ResearchGroupAccessRequest.created_at.desc())
            .all()
        )

        # Batch-load avatar data for requesters
        requester_usernames = list({r.requester_username for r in requests})
        user_lookup = {}
        if requester_usernames:
            for u in User.query.filter(User.username.in_(requester_usernames)).all():
                avatar_url = None
                if u.avatar_public_id and u.avatar_file:
                    avatar_url = f"/api/users/avatar/{u.avatar_public_id}"
                user_lookup[u.username] = {
                    "avatar_seed": u.avatar_seed,
                    "avatar_url": avatar_url,
                }

        results = []
        for r in requests:
            avatar = user_lookup.get(r.requester_username, {})
            results.append({
                "id": r.id,
                "group_id": r.group_id,
                "group_name": r.group.name if r.group else None,
                "requester_username": r.requester_username,
                "requester_avatar_seed": avatar.get("avatar_seed"),
                "requester_avatar_url": avatar.get("avatar_url"),
                "message": r.message,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })
        return results

    @staticmethod
    def list_group_requests(group_id: int) -> List[Dict[str, Any]]:
        """List all access requests for a specific group."""
        from db.models import ResearchGroupAccessRequest, User

        requests = (
            ResearchGroupAccessRequest.query
            .filter_by(group_id=group_id)
            .order_by(ResearchGroupAccessRequest.created_at.desc())
            .all()
        )

        # Batch-load avatar data for requesters
        requester_usernames = list({r.requester_username for r in requests})
        user_lookup = {}
        if requester_usernames:
            for u in User.query.filter(User.username.in_(requester_usernames)).all():
                avatar_url = None
                if u.avatar_public_id and u.avatar_file:
                    avatar_url = f"/api/users/avatar/{u.avatar_public_id}"
                user_lookup[u.username] = {
                    "avatar_seed": u.avatar_seed,
                    "avatar_url": avatar_url,
                }

        results = []
        for r in requests:
            avatar = user_lookup.get(r.requester_username, {})
            results.append({
                "id": r.id,
                "group_id": r.group_id,
                "requester_username": r.requester_username,
                "requester_avatar_seed": avatar.get("avatar_seed"),
                "requester_avatar_url": avatar.get("avatar_url"),
                "status": r.status.value,
                "message": r.message,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
                "resolved_by": r.resolved_by,
            })
        return results

    @staticmethod
    def resolve_access_request(
        request_id: int, action: str, resolved_by: str
    ) -> Optional[Dict[str, Any]]:
        """Approve or reject an access request."""
        from db.models import (
            ResearchGroupAccessRequest, ResearchGroupRequestStatus,
            ResearchGroupMember, ResearchGroupRole, User,
        )

        req = ResearchGroupAccessRequest.query.get(request_id)
        if not req or req.status != ResearchGroupRequestStatus.PENDING:
            return None

        if action == 'approve':
            req.status = ResearchGroupRequestStatus.APPROVED
            req.resolved_at = datetime.utcnow()
            req.resolved_by = resolved_by

            # Add user as member
            user = User.query.filter_by(username=req.requester_username).first()
            if user:
                existing = ResearchGroupMember.query.filter_by(
                    group_id=req.group_id, user_id=user.id
                ).first()
                if not existing:
                    member = ResearchGroupMember(
                        group_id=req.group_id,
                        user_id=user.id,
                        role=ResearchGroupRole.MEMBER,
                        added_by=resolved_by,
                    )
                    db.session.add(member)

        elif action == 'reject':
            req.status = ResearchGroupRequestStatus.REJECTED
            req.resolved_at = datetime.utcnow()
            req.resolved_by = resolved_by
        else:
            return None

        db.session.commit()
        return {
            "id": req.id,
            "status": req.status.value,
            "action": action,
        }

    # ── Statistics ───────────────────────────────────────────

    @staticmethod
    def get_group_stats(group_id: int) -> Dict[str, Any]:
        """Get statistics for a specific group."""
        from db.models import Conference, Paper, ResearchGroupMember, ResearchGroupAccessRequest, ResearchGroupRequestStatus

        return {
            "conferences": Conference.query.filter_by(group_id=group_id).count(),
            "papers": Paper.query.filter_by(group_id=group_id).count(),
            "members": ResearchGroupMember.query.filter_by(group_id=group_id).count(),
            "pending_requests": ResearchGroupAccessRequest.query.filter_by(
                group_id=group_id, status=ResearchGroupRequestStatus.PENDING
            ).count(),
        }
