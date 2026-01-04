"""KAIMO User Routes.

User-facing endpoints for KAIMO panel.
"""

from datetime import datetime
from flask import Blueprint, jsonify, request
from decorators.permission_decorator import require_permission
from decorators.error_handler import (
    handle_api_errors,
    NotFoundError,
    ValidationError,
    ForbiddenError,
    UnauthorizedError,
)
from db.database import db
from db.models import (
    KaimoCase,
    KaimoDocument,
    KaimoHint,
    KaimoCategory,
    KaimoCaseCategory,
    KaimoSubcategory,
    KaimoUserAssessment,
    KaimoHintAssignment,
)
from sqlalchemy import func
from auth.auth_utils import AuthUtils

kaimo_user_bp = Blueprint('kaimo_user', __name__)


def _get_case_categories(case_id: int):
    """Return categories for a case, falling back to defaults."""
    links = (
        db.session.query(KaimoCategory)
        .join(KaimoCaseCategory, KaimoCaseCategory.category_id == KaimoCategory.id)
        .filter(KaimoCaseCategory.case_id == case_id)
        .order_by(KaimoCaseCategory.sort_order)
        .all()
    )
    if links:
        return links
    return KaimoCategory.query.filter_by(is_default=True).order_by(KaimoCategory.sort_order).all()


@kaimo_user_bp.route('/cases', methods=['GET'])
@require_permission('feature:kaimo:view')
@handle_api_errors(logger_name='kaimo.user')
def list_cases_user():
    """List published KAIMO cases for users."""
    cases = (
        KaimoCase.query.filter(KaimoCase.status != 'archived')
        .order_by(KaimoCase.created_at.desc())
        .all()
    )

    doc_counts = dict(
        db.session.query(KaimoDocument.case_id, func.count(KaimoDocument.id))
        .group_by(KaimoDocument.case_id)
        .all()
    )
    hint_counts = dict(
        db.session.query(KaimoHint.case_id, func.count(KaimoHint.id))
        .group_by(KaimoHint.case_id)
        .all()
    )

    payload = []
    for c in cases:
        if c.status not in ('published', 'draft'):
            continue
        payload.append({
            "id": c.id,
            "display_name": c.display_name,
            "description": c.description,
            "icon": c.icon,
            "color": c.color,
            "status": c.status,
            "document_count": doc_counts.get(c.id, 0),
            "hint_count": hint_counts.get(c.id, 0),
            "estimated_duration_minutes": 30,  # placeholder until durations are tracked
        })

    return jsonify({"success": True, "cases": payload}), 200


@kaimo_user_bp.route('/cases/<int:case_id>', methods=['GET'])
@require_permission('feature:kaimo:view')
@handle_api_errors(logger_name='kaimo.user')
def get_case_detail(case_id: int):
    """Get KAIMO case detail with documents, categories, hints."""
    case = KaimoCase.query.get(case_id)
    if not case:
        raise NotFoundError("Case not found")

    categories = _get_case_categories(case.id)
    subcategories = KaimoSubcategory.query.filter(
        KaimoSubcategory.category_id.in_([c.id for c in categories])
    ).order_by(KaimoSubcategory.sort_order).all()

    documents = (
        KaimoDocument.query.filter_by(case_id=case.id)
        .order_by(KaimoDocument.sort_order, KaimoDocument.id)
        .all()
    )
    hints = (
        KaimoHint.query.filter_by(case_id=case.id)
        .order_by(KaimoHint.sort_order, KaimoHint.id)
        .all()
    )

    return jsonify({
        "success": True,
        "case": {
            "id": case.id,
            "display_name": case.display_name,
            "description": case.description,
            "icon": case.icon,
            "color": case.color,
            "status": case.status,
            "documents": [
                {
                    "id": d.id,
                    "title": d.title,
                    "content": d.content,
                    "document_type": d.document_type,
                    "document_date": d.document_date.isoformat() if d.document_date else None,
                    "sort_order": d.sort_order,
                } for d in documents
            ],
            "categories": [
                {
                    "id": cat.id,
                    "display_name": cat.display_name,
                    "icon": cat.icon,
                    "color": cat.color,
                    "sort_order": cat.sort_order,
                } for cat in categories
            ],
            "subcategories": [
                {
                    "id": sub.id,
                    "category_id": sub.category_id,
                    "display_name": sub.display_name,
                    "sort_order": sub.sort_order,
                } for sub in subcategories
            ],
            "hints": [
                {
                    "id": h.id,
                    "content": h.content,
                    "source_document_id": h.document_id,
                    "expected_category_id": h.expected_category_id,
                    "expected_subcategory_id": h.expected_subcategory_id,
                    "expected_rating": h.expected_rating,
                    "sort_order": h.sort_order,
                } for h in hints
            ],
        },
        "my_assessment": None,  # placeholder until assessment endpoints are implemented
    }), 200


@kaimo_user_bp.route('/cases/<int:case_id>/start', methods=['POST'])
@require_permission('feature:kaimo:edit')
@handle_api_errors(logger_name='kaimo.user')
def start_assessment(case_id: int):
    """Start or continue an assessment for a case."""
    case = KaimoCase.query.get(case_id)
    if not case:
        raise NotFoundError("Case not found")

    user_id = AuthUtils.extract_username_without_validation()
    if not user_id:
        raise UnauthorizedError("User ID not found in token")

    # Check if user already has an assessment for this case
    assessment = KaimoUserAssessment.query.filter_by(
        case_id=case_id,
        user_id=user_id
    ).first()

    if assessment:
        # Return existing assessment
        return jsonify({
            "success": True,
            "assessment": {
                "id": assessment.id,
                "case_id": assessment.case_id,
                "status": assessment.status,
                "started_at": assessment.started_at.isoformat() if assessment.started_at else None,
                "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
            }
        }), 200

    # Create new assessment
    assessment = KaimoUserAssessment(
        case_id=case_id,
        user_id=user_id,
        username=user_id,
        status='in_progress',
        started_at=datetime.utcnow(),
    )
    db.session.add(assessment)
    db.session.commit()

    return jsonify({
        "success": True,
        "assessment": {
            "id": assessment.id,
            "case_id": assessment.case_id,
            "status": assessment.status,
            "started_at": assessment.started_at.isoformat() if assessment.started_at else None,
        }
    }), 201


@kaimo_user_bp.route('/assessments/<int:assessment_id>', methods=['GET'])
@require_permission('feature:kaimo:view')
@handle_api_errors(logger_name='kaimo.user')
def get_assessment(assessment_id: int):
    """Get assessment details with all hint assignments."""
    assessment = KaimoUserAssessment.query.get(assessment_id)
    if not assessment:
        raise NotFoundError("Assessment not found")

    user_id = AuthUtils.extract_username_without_validation()
    if not user_id:
        raise UnauthorizedError("User ID not found in token")

    # Check if user owns this assessment
    if assessment.user_id != user_id:
        raise ForbiddenError("Access denied")

    # Get all hint assignments
    assignments = (
        KaimoHintAssignment.query
        .filter_by(assessment_id=assessment_id)
        .all()
    )

    return jsonify({
        "success": True,
        "assessment": {
            "id": assessment.id,
            "case_id": assessment.case_id,
            "status": assessment.status,
            "final_verdict": assessment.final_verdict,
            "final_comment": assessment.final_comment,
            "started_at": assessment.started_at.isoformat() if assessment.started_at else None,
            "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
            "duration_seconds": assessment.duration_seconds,
            "hint_assignments": [
                {
                    "id": a.id,
                    "hint_id": a.hint_id,
                    "assigned_category_id": a.assigned_category_id,
                    "assigned_subcategory_id": a.assigned_subcategory_id,
                    "rating": a.rating,
                    "assigned_at": a.assigned_at.isoformat() if a.assigned_at else None,
                } for a in assignments
            ]
        }
    }), 200


@kaimo_user_bp.route('/assessments/<int:assessment_id>/hints/<int:hint_id>', methods=['PUT'])
@require_permission('feature:kaimo:edit')
@handle_api_errors(logger_name='kaimo.user')
def update_hint_assignment(assessment_id: int, hint_id: int):
    """Update or create a hint assignment."""
    assessment = KaimoUserAssessment.query.get(assessment_id)
    if not assessment:
        raise NotFoundError("Assessment not found")

    user_id = AuthUtils.extract_username_without_validation()
    if not user_id:
        raise UnauthorizedError("User ID not found in token")

    # Check if user owns this assessment
    if assessment.user_id != user_id:
        raise ForbiddenError("Access denied")

    # Check if assessment is already completed
    if assessment.status == 'completed':
        raise ValidationError("Cannot modify completed assessment")

    # Verify hint belongs to the same case
    hint = KaimoHint.query.filter_by(id=hint_id, case_id=assessment.case_id).first()
    if not hint:
        raise NotFoundError("Hint not found")

    data = request.get_json() or {}
    assigned_category_id = data.get('assigned_category_id')
    assigned_subcategory_id = data.get('assigned_subcategory_id')
    rating = data.get('rating')

    # Validate rating if provided
    if rating and rating not in ('risk', 'resource', 'unclear'):
        raise ValidationError("rating must be one of: risk, resource, unclear")

    # Check if assignment already exists (upsert logic)
    assignment = KaimoHintAssignment.query.filter_by(
        assessment_id=assessment_id,
        hint_id=hint_id
    ).first()

    if assignment:
        # Update existing assignment
        if assigned_category_id is not None:
            assignment.assigned_category_id = assigned_category_id
        if assigned_subcategory_id is not None:
            assignment.assigned_subcategory_id = assigned_subcategory_id
        if rating is not None:
            assignment.rating = rating
        assignment.assigned_at = datetime.utcnow()
    else:
        # Create new assignment
        assignment = KaimoHintAssignment(
            assessment_id=assessment_id,
            hint_id=hint_id,
            assigned_category_id=assigned_category_id,
            assigned_subcategory_id=assigned_subcategory_id,
            rating=rating,
            assigned_at=datetime.utcnow(),
        )
        db.session.add(assignment)

    db.session.commit()

    return jsonify({
        "success": True,
        "assignment": {
            "id": assignment.id,
            "hint_id": assignment.hint_id,
            "assigned_category_id": assignment.assigned_category_id,
            "assigned_subcategory_id": assignment.assigned_subcategory_id,
            "rating": assignment.rating,
        }
    }), 200


@kaimo_user_bp.route('/assessments/<int:assessment_id>/complete', methods=['POST'])
@require_permission('feature:kaimo:edit')
@handle_api_errors(logger_name='kaimo.user')
def complete_assessment(assessment_id: int):
    """Complete an assessment."""
    assessment = KaimoUserAssessment.query.get(assessment_id)
    if not assessment:
        raise NotFoundError("Assessment not found")

    user_id = AuthUtils.extract_username_without_validation()
    if not user_id:
        raise UnauthorizedError("User ID not found in token")

    # Check if user owns this assessment
    if assessment.user_id != user_id:
        raise ForbiddenError("Access denied")

    # Check if assessment is already completed
    if assessment.status == 'completed':
        raise ValidationError("Assessment already completed")

    data = request.get_json() or {}
    final_verdict = data.get('final_verdict')
    final_comment = data.get('final_comment')

    # Validate final_verdict if provided
    if final_verdict and final_verdict not in ('inconclusive', 'not_endangered', 'endangered'):
        raise ValidationError("final_verdict must be one of: inconclusive, not_endangered, endangered")

    # Update assessment
    assessment.status = 'completed'
    assessment.final_verdict = final_verdict
    assessment.final_comment = final_comment
    assessment.completed_at = datetime.utcnow()

    # Calculate duration in seconds
    if assessment.started_at and assessment.completed_at:
        duration = (assessment.completed_at - assessment.started_at).total_seconds()
        assessment.duration_seconds = int(duration)

    db.session.commit()

    return jsonify({
        "success": True,
        "assessment": {
            "id": assessment.id,
            "status": assessment.status,
            "final_verdict": assessment.final_verdict,
            "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
            "duration_seconds": assessment.duration_seconds,
        }
    }), 200


@kaimo_user_bp.route('/categories', methods=['GET'])
@require_permission('feature:kaimo:view')
@handle_api_errors(logger_name='kaimo.user')
def get_categories_user():
    """Get all KAIMO categories for users (for dropdowns)."""
    categories = KaimoCategory.query.order_by(KaimoCategory.sort_order).all()

    payload = []
    for cat in categories:
        subcategories = (
            KaimoSubcategory.query
            .filter_by(category_id=cat.id)
            .order_by(KaimoSubcategory.sort_order)
            .all()
        )

        payload.append({
            "id": cat.id,
            "display_name": cat.display_name,
            "icon": cat.icon,
            "color": cat.color,
            "subcategories": [
                {
                    "id": sub.id,
                    "display_name": sub.display_name,
                } for sub in subcategories
            ]
        })

    return jsonify({"success": True, "categories": payload}), 200
