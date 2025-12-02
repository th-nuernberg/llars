"""KAIMO Admin Routes.

Admin panel endpoints for managing KAIMO cases.
"""

from datetime import datetime
import jwt
from flask import Blueprint, jsonify, request
from sqlalchemy import func

from db.db import db
from db.models import (
    KaimoCase,
    KaimoDocument,
    KaimoHint,
    KaimoCategory,
    KaimoCaseCategory,
    KaimoUserAssessment,
    KaimoHintAssignment,
    KaimoSubcategory,
)
from decorators.permission_decorator import require_permission

kaimo_admin_bp = Blueprint('kaimo_admin', __name__, url_prefix='/admin')


def _get_username_from_token():
    """Extract username from Authorization header without verifying signature."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    decoded = jwt.decode(token, options={"verify_signature": False})
    return (
        decoded.get('preferred_username')
        or decoded.get('username')
        or decoded.get('name')
        or decoded.get('uid')
        or decoded.get('sub')
    )


@kaimo_admin_bp.route('/cases', methods=['GET'])
@require_permission('admin:kaimo:manage')
def list_cases_admin():
    """List all KAIMO cases with lightweight counts."""
    cases = KaimoCase.query.order_by(KaimoCase.created_at.desc()).all()

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
    assessment_counts = dict(
        db.session.query(KaimoUserAssessment.case_id, func.count(KaimoUserAssessment.id))
        .group_by(KaimoUserAssessment.case_id)
        .all()
    )

    payload = []
    for c in cases:
        payload.append({
            "id": c.id,
            "name": c.name,
            "display_name": c.display_name,
            "description": c.description,
            "status": c.status,
            "icon": c.icon,
            "color": c.color,
            "created_by": c.created_by,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "published_at": c.published_at.isoformat() if c.published_at else None,
            "document_count": doc_counts.get(c.id, 0),
            "hint_count": hint_counts.get(c.id, 0),
            "assessment_count": assessment_counts.get(c.id, 0),
        })

    return jsonify({"success": True, "cases": payload, "total": len(payload)}), 200


@kaimo_admin_bp.route('/cases', methods=['POST'])
@require_permission('admin:kaimo:manage')
def create_case():
    """Create a new KAIMO case (draft)."""
    data = request.get_json() or {}
    name = data.get('name')
    display_name = data.get('display_name')
    description = data.get('description')
    icon = data.get('icon')
    color = data.get('color')
    category_ids = data.get('categories')  # optional list of category IDs

    if not name or not display_name:
        return jsonify({"success": False, "error": "name and display_name are required"}), 400

    existing = KaimoCase.query.filter_by(name=name).first()
    if existing:
        return jsonify({"success": False, "error": "Case with this name already exists"}), 400

    created_by = _get_username_from_token() or 'system'

    case = KaimoCase(
        name=name,
        display_name=display_name,
        description=description,
        icon=icon,
        color=color,
        status='draft',
        created_by=created_by,
        created_at=datetime.utcnow(),
    )
    db.session.add(case)
    db.session.flush()  # get case.id

    # Link categories: use provided IDs or default categories
    if category_ids and isinstance(category_ids, list):
        categories = KaimoCategory.query.filter(KaimoCategory.id.in_(category_ids)).all()
    else:
        categories = KaimoCategory.query.filter_by(is_default=True).order_by(KaimoCategory.sort_order).all()

    for idx, cat in enumerate(categories, start=1):
        link = KaimoCaseCategory(case_id=case.id, category_id=cat.id, sort_order=idx)
        db.session.add(link)

    db.session.commit()

    return jsonify({
        "success": True,
        "case": {
            "id": case.id,
            "name": case.name,
            "display_name": case.display_name,
            "status": case.status,
        }
    }), 201


@kaimo_admin_bp.route('/cases/<int:case_id>/publish', methods=['POST'])
@require_permission('admin:kaimo:manage')
def publish_case(case_id: int):
    """Publish a KAIMO case."""
    case = KaimoCase.query.get(case_id)
    if not case:
        return jsonify({"success": False, "error": "Case not found"}), 404

    case.status = 'published'
    case.published_at = datetime.utcnow()
    case.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"success": True, "case_id": case.id, "status": case.status}), 200


@kaimo_admin_bp.route('/cases/<int:case_id>', methods=['PUT'])
@require_permission('admin:kaimo:manage')
def update_case(case_id: int):
    """Update a KAIMO case."""
    case = KaimoCase.query.get(case_id)
    if not case:
        return jsonify({"success": False, "error": "Case not found"}), 404

    data = request.get_json() or {}

    # Update fields if provided
    if 'name' in data:
        # Check if name is already taken by another case
        existing = KaimoCase.query.filter(
            KaimoCase.name == data['name'],
            KaimoCase.id != case_id
        ).first()
        if existing:
            return jsonify({"success": False, "error": "Case with this name already exists"}), 400
        case.name = data['name']

    if 'display_name' in data:
        case.display_name = data['display_name']
    if 'description' in data:
        case.description = data['description']
    if 'icon' in data:
        case.icon = data['icon']
    if 'color' in data:
        case.color = data['color']
    if 'status' in data and data['status'] in ('draft', 'published', 'archived'):
        case.status = data['status']
        if data['status'] == 'published' and not case.published_at:
            case.published_at = datetime.utcnow()

    case.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "success": True,
        "case": {
            "id": case.id,
            "name": case.name,
            "display_name": case.display_name,
            "status": case.status,
        }
    }), 200


@kaimo_admin_bp.route('/cases/<int:case_id>', methods=['DELETE'])
@require_permission('admin:kaimo:manage')
def delete_case(case_id: int):
    """Delete a KAIMO case."""
    case = KaimoCase.query.get(case_id)
    if not case:
        return jsonify({"success": False, "error": "Case not found"}), 404

    force = request.args.get('force', 'false').lower() == 'true'

    # Check if case has assessments
    assessment_count = KaimoUserAssessment.query.filter_by(case_id=case_id).count()
    if assessment_count > 0 and not force:
        return jsonify({
            "success": False,
            "error": f"Case has {assessment_count} assessments. Use force=true to delete anyway."
        }), 400

    db.session.delete(case)
    db.session.commit()

    return jsonify({"success": True, "case_id": case_id}), 200


@kaimo_admin_bp.route('/cases/<int:case_id>', methods=['GET'])
@require_permission('admin:kaimo:manage')
def get_case_admin(case_id: int):
    """Get KAIMO case details for admin (with all documents and hints)."""
    case = KaimoCase.query.get(case_id)
    if not case:
        return jsonify({"success": False, "error": "Case not found"}), 404

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
    categories = (
        db.session.query(KaimoCategory)
        .join(KaimoCaseCategory, KaimoCaseCategory.category_id == KaimoCategory.id)
        .filter(KaimoCaseCategory.case_id == case_id)
        .order_by(KaimoCaseCategory.sort_order)
        .all()
    )
    assessment_count = KaimoUserAssessment.query.filter_by(case_id=case.id).count()

    return jsonify({
        "success": True,
        "case": {
            "id": case.id,
            "name": case.name,
            "display_name": case.display_name,
            "description": case.description,
            "icon": case.icon,
            "color": case.color,
            "status": case.status,
            "created_by": case.created_by,
            "created_at": case.created_at.isoformat() if case.created_at else None,
            "updated_at": case.updated_at.isoformat() if case.updated_at else None,
            "published_at": case.published_at.isoformat() if case.published_at else None,
            "assessment_count": assessment_count,
            "documents": [
                {
                    "id": d.id,
                    "title": d.title,
                    "content": d.content,
                    "document_type": d.document_type,
                    "document_date": d.document_date.isoformat() if d.document_date else None,
                    "sort_order": d.sort_order,
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                } for d in documents
            ],
            "hints": [
                {
                    "id": h.id,
                    "content": h.content,
                    "document_id": h.document_id,
                    "expected_category_id": h.expected_category_id,
                    "expected_subcategory_id": h.expected_subcategory_id,
                    "expected_rating": h.expected_rating,
                    "sort_order": h.sort_order,
                    "created_at": h.created_at.isoformat() if h.created_at else None,
                } for h in hints
            ],
            "categories": [
                {
                    "id": cat.id,
                    "name": cat.name,
                    "display_name": cat.display_name,
                } for cat in categories
            ],
        }
    }), 200


@kaimo_admin_bp.route('/cases/<int:case_id>/documents', methods=['POST'])
@require_permission('admin:kaimo:manage')
def add_document(case_id: int):
    """Add a document to a KAIMO case."""
    case = KaimoCase.query.get(case_id)
    if not case:
        return jsonify({"success": False, "error": "Case not found"}), 404

    data = request.get_json() or {}
    title = data.get('title')
    content = data.get('content')
    document_type = data.get('document_type')
    document_date = data.get('document_date')
    sort_order = data.get('sort_order', 0)

    if not title or not content or not document_type:
        return jsonify({
            "success": False,
            "error": "title, content, and document_type are required"
        }), 400

    if document_type not in ('aktenvermerk', 'bericht', 'protokoll', 'sonstiges'):
        return jsonify({
            "success": False,
            "error": "document_type must be one of: aktenvermerk, bericht, protokoll, sonstiges"
        }), 400

    # Parse date if provided
    parsed_date = None
    if document_date:
        try:
            parsed_date = datetime.fromisoformat(document_date.replace('Z', '+00:00')).date()
        except ValueError:
            return jsonify({"success": False, "error": "Invalid date format"}), 400

    document = KaimoDocument(
        case_id=case_id,
        title=title,
        content=content,
        document_type=document_type,
        document_date=parsed_date,
        sort_order=sort_order,
        created_at=datetime.utcnow(),
    )
    db.session.add(document)

    case.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "success": True,
        "document": {
            "id": document.id,
            "title": document.title,
            "document_type": document.document_type,
            "sort_order": document.sort_order,
        }
    }), 201


@kaimo_admin_bp.route('/cases/<int:case_id>/documents/<int:doc_id>', methods=['PUT'])
@require_permission('admin:kaimo:manage')
def update_document(case_id: int, doc_id: int):
    """Update a document in a KAIMO case."""
    document = KaimoDocument.query.filter_by(id=doc_id, case_id=case_id).first()
    if not document:
        return jsonify({"success": False, "error": "Document not found"}), 404

    data = request.get_json() or {}

    if 'title' in data:
        document.title = data['title']
    if 'content' in data:
        document.content = data['content']
    if 'document_type' in data:
        if data['document_type'] not in ('aktenvermerk', 'bericht', 'protokoll', 'sonstiges'):
            return jsonify({
                "success": False,
                "error": "document_type must be one of: aktenvermerk, bericht, protokoll, sonstiges"
            }), 400
        document.document_type = data['document_type']
    if 'document_date' in data:
        if data['document_date']:
            try:
                document.document_date = datetime.fromisoformat(
                    data['document_date'].replace('Z', '+00:00')
                ).date()
            except ValueError:
                return jsonify({"success": False, "error": "Invalid date format"}), 400
        else:
            document.document_date = None
    if 'sort_order' in data:
        document.sort_order = data['sort_order']

    case = KaimoCase.query.get(case_id)
    if case:
        case.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "success": True,
        "document": {
            "id": document.id,
            "title": document.title,
        }
    }), 200


@kaimo_admin_bp.route('/cases/<int:case_id>/documents/<int:doc_id>', methods=['DELETE'])
@require_permission('admin:kaimo:manage')
def delete_document(case_id: int, doc_id: int):
    """Delete a document from a KAIMO case."""
    document = KaimoDocument.query.filter_by(id=doc_id, case_id=case_id).first()
    if not document:
        return jsonify({"success": False, "error": "Document not found"}), 404

    db.session.delete(document)

    case = KaimoCase.query.get(case_id)
    if case:
        case.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({"success": True, "document_id": doc_id}), 200


@kaimo_admin_bp.route('/cases/<int:case_id>/hints', methods=['POST'])
@require_permission('admin:kaimo:manage')
def add_hint(case_id: int):
    """Add a hint to a KAIMO case."""
    case = KaimoCase.query.get(case_id)
    if not case:
        return jsonify({"success": False, "error": "Case not found"}), 404

    data = request.get_json() or {}
    content = data.get('content')
    document_id = data.get('document_id')
    expected_category_id = data.get('expected_category_id')
    expected_subcategory_id = data.get('expected_subcategory_id')
    expected_rating = data.get('expected_rating')
    sort_order = data.get('sort_order', 0)

    if not content:
        return jsonify({"success": False, "error": "content is required"}), 400

    if expected_rating and expected_rating not in ('risk', 'resource', 'unclear'):
        return jsonify({
            "success": False,
            "error": "expected_rating must be one of: risk, resource, unclear"
        }), 400

    # Validate document_id if provided
    if document_id:
        doc = KaimoDocument.query.filter_by(id=document_id, case_id=case_id).first()
        if not doc:
            return jsonify({"success": False, "error": "Document not found"}), 404

    hint = KaimoHint(
        case_id=case_id,
        content=content,
        document_id=document_id,
        expected_category_id=expected_category_id,
        expected_subcategory_id=expected_subcategory_id,
        expected_rating=expected_rating,
        sort_order=sort_order,
        created_at=datetime.utcnow(),
    )
    db.session.add(hint)

    case.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "success": True,
        "hint": {
            "id": hint.id,
            "content": hint.content[:100] + '...' if len(hint.content) > 100 else hint.content,
            "sort_order": hint.sort_order,
        }
    }), 201


@kaimo_admin_bp.route('/cases/<int:case_id>/hints/<int:hint_id>', methods=['PUT'])
@require_permission('admin:kaimo:manage')
def update_hint(case_id: int, hint_id: int):
    """Update a hint in a KAIMO case."""
    hint = KaimoHint.query.filter_by(id=hint_id, case_id=case_id).first()
    if not hint:
        return jsonify({"success": False, "error": "Hint not found"}), 404

    data = request.get_json() or {}

    if 'content' in data:
        hint.content = data['content']
    if 'document_id' in data:
        if data['document_id']:
            doc = KaimoDocument.query.filter_by(id=data['document_id'], case_id=case_id).first()
            if not doc:
                return jsonify({"success": False, "error": "Document not found"}), 404
        hint.document_id = data['document_id']
    if 'expected_category_id' in data:
        hint.expected_category_id = data['expected_category_id']
    if 'expected_subcategory_id' in data:
        hint.expected_subcategory_id = data['expected_subcategory_id']
    if 'expected_rating' in data:
        if data['expected_rating'] and data['expected_rating'] not in ('risk', 'resource', 'unclear'):
            return jsonify({
                "success": False,
                "error": "expected_rating must be one of: risk, resource, unclear"
            }), 400
        hint.expected_rating = data['expected_rating']
    if 'sort_order' in data:
        hint.sort_order = data['sort_order']

    case = KaimoCase.query.get(case_id)
    if case:
        case.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "success": True,
        "hint": {
            "id": hint.id,
            "content": hint.content[:100] + '...' if len(hint.content) > 100 else hint.content,
        }
    }), 200


@kaimo_admin_bp.route('/cases/<int:case_id>/hints/<int:hint_id>', methods=['DELETE'])
@require_permission('admin:kaimo:manage')
def delete_hint(case_id: int, hint_id: int):
    """Delete a hint from a KAIMO case."""
    hint = KaimoHint.query.filter_by(id=hint_id, case_id=case_id).first()
    if not hint:
        return jsonify({"success": False, "error": "Hint not found"}), 404

    db.session.delete(hint)

    case = KaimoCase.query.get(case_id)
    if case:
        case.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({"success": True, "hint_id": hint_id}), 200


@kaimo_admin_bp.route('/cases/<int:case_id>/results', methods=['GET'])
@require_permission('admin:kaimo:results')
def get_case_results(case_id: int):
    """Get aggregated assessment results for a KAIMO case."""
    case = KaimoCase.query.get(case_id)
    if not case:
        return jsonify({"success": False, "error": "Case not found"}), 404

    from db.models import KaimoHintAssignment

    # Get all assessments for this case
    assessments = KaimoUserAssessment.query.filter_by(case_id=case_id).all()

    # Get all hints
    hints = KaimoHint.query.filter_by(case_id=case_id).order_by(KaimoHint.sort_order).all()

    # Aggregate results per hint
    hint_results = []
    for hint in hints:
        assignments = (
            db.session.query(KaimoHintAssignment)
            .join(KaimoUserAssessment)
            .filter(
                KaimoUserAssessment.case_id == case_id,
                KaimoHintAssignment.hint_id == hint.id
            )
            .all()
        )

        # Count category assignments
        category_counts = {}
        subcategory_counts = {}
        rating_counts = {'risk': 0, 'resource': 0, 'unclear': 0, 'unassigned': 0}

        for assignment in assignments:
            if assignment.assigned_category_id:
                category_counts[assignment.assigned_category_id] = (
                    category_counts.get(assignment.assigned_category_id, 0) + 1
                )
            if assignment.assigned_subcategory_id:
                subcategory_counts[assignment.assigned_subcategory_id] = (
                    subcategory_counts.get(assignment.assigned_subcategory_id, 0) + 1
                )
            if assignment.rating:
                rating_counts[assignment.rating] = rating_counts.get(assignment.rating, 0) + 1
            else:
                rating_counts['unassigned'] += 1

        hint_results.append({
            "hint_id": hint.id,
            "content": hint.content[:100] + '...' if len(hint.content) > 100 else hint.content,
            "expected_category_id": hint.expected_category_id,
            "expected_subcategory_id": hint.expected_subcategory_id,
            "expected_rating": hint.expected_rating,
            "total_assignments": len(assignments),
            "category_counts": category_counts,
            "subcategory_counts": subcategory_counts,
            "rating_counts": rating_counts,
        })

    # Overall statistics
    total_assessments = len(assessments)
    completed_assessments = sum(1 for a in assessments if a.status == 'completed')

    verdict_counts = {
        'inconclusive': 0,
        'not_endangered': 0,
        'endangered': 0,
        'no_verdict': 0,
    }
    for assessment in assessments:
        if assessment.final_verdict:
            verdict_counts[assessment.final_verdict] = verdict_counts.get(assessment.final_verdict, 0) + 1
        else:
            verdict_counts['no_verdict'] += 1

    avg_duration = None
    if completed_assessments > 0:
        durations = [a.duration_seconds for a in assessments if a.duration_seconds]
        if durations:
            avg_duration = sum(durations) // len(durations)

    return jsonify({
        "success": True,
        "case_id": case_id,
        "case_name": case.display_name,
        "statistics": {
            "total_assessments": total_assessments,
            "completed_assessments": completed_assessments,
            "in_progress_assessments": total_assessments - completed_assessments,
            "verdict_counts": verdict_counts,
            "avg_duration_seconds": avg_duration,
        },
        "hint_results": hint_results,
    }), 200


@kaimo_admin_bp.route('/categories', methods=['GET'])
@require_permission('admin:kaimo:manage')
def get_categories_admin():
    """Get all KAIMO categories with subcategories."""
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
            "name": cat.name,
            "display_name": cat.display_name,
            "description": cat.description,
            "icon": cat.icon,
            "color": cat.color,
            "sort_order": cat.sort_order,
            "is_default": cat.is_default,
            "subcategories": [
                {
                    "id": sub.id,
                    "name": sub.name,
                    "display_name": sub.display_name,
                    "description": sub.description,
                    "sort_order": sub.sort_order,
                    "is_default": sub.is_default,
                } for sub in subcategories
            ]
        })

    return jsonify({"success": True, "categories": payload}), 200
