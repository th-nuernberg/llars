"""KAIMO Admin Routes.

Admin panel endpoints for managing KAIMO cases.
Routes handle HTTP request/response formatting and delegate business logic to services.
"""

from flask import Blueprint, jsonify, request

from decorators.permission_decorator import require_permission
from auth.auth_utils import AuthUtils
from services.kaimo import (
    KaimoCaseService,
    KaimoDocumentService,
    KaimoHintService,
    KaimoCategoryService,
)
from services.kaimo.kaimo_case_service import (
    CaseNotFoundException,
    CaseAlreadyExistsException,
    CaseHasAssessmentsException,
)
from services.kaimo.kaimo_document_service import (
    DocumentNotFoundException,
    InvalidDocumentTypeException,
    InvalidDateFormatException,
)
from services.kaimo.kaimo_hint_service import (
    HintNotFoundException,
    InvalidRatingException,
)

kaimo_admin_bp = Blueprint('kaimo_admin', __name__, url_prefix='/admin')


@kaimo_admin_bp.route('/cases', methods=['GET'])
@require_permission('admin:kaimo:manage')
def list_cases_admin():
    """List all KAIMO cases with lightweight counts."""
    try:
        cases = KaimoCaseService.get_all_cases_with_counts()
        return jsonify({"success": True, "cases": cases, "total": len(cases)}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


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
    category_ids = data.get('categories')

    if not name or not display_name:
        return jsonify({"success": False, "error": "name and display_name are required"}), 400

    try:
        created_by = AuthUtils.extract_username_without_validation() or 'system'
        case = KaimoCaseService.create_case(
            name=name,
            display_name=display_name,
            created_by=created_by,
            description=description,
            icon=icon,
            color=color,
            category_ids=category_ids
        )

        return jsonify({
            "success": True,
            "case": {
                "id": case.id,
                "name": case.name,
                "display_name": case.display_name,
                "status": case.status,
            }
        }), 201

    except CaseAlreadyExistsException as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@kaimo_admin_bp.route('/cases/<int:case_id>/publish', methods=['POST'])
@require_permission('admin:kaimo:manage')
def publish_case(case_id: int):
    """Publish a KAIMO case."""
    try:
        case = KaimoCaseService.publish_case(case_id)
        return jsonify({"success": True, "case_id": case.id, "status": case.status}), 200

    except CaseNotFoundException as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@kaimo_admin_bp.route('/cases/<int:case_id>', methods=['PUT'])
@require_permission('admin:kaimo:manage')
def update_case(case_id: int):
    """Update a KAIMO case."""
    data = request.get_json() or {}

    try:
        case = KaimoCaseService.update_case(
            case_id=case_id,
            name=data.get('name'),
            display_name=data.get('display_name'),
            description=data.get('description'),
            icon=data.get('icon'),
            color=data.get('color'),
            status=data.get('status')
        )

        return jsonify({
            "success": True,
            "case": {
                "id": case.id,
                "name": case.name,
                "display_name": case.display_name,
                "status": case.status,
            }
        }), 200

    except CaseNotFoundException as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except CaseAlreadyExistsException as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@kaimo_admin_bp.route('/cases/<int:case_id>', methods=['DELETE'])
@require_permission('admin:kaimo:manage')
def delete_case(case_id: int):
    """Delete a KAIMO case."""
    force = request.args.get('force', 'false').lower() == 'true'

    try:
        KaimoCaseService.delete_case(case_id, force=force)
        return jsonify({"success": True, "case_id": case_id}), 200

    except CaseNotFoundException as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except CaseHasAssessmentsException as e:
        return jsonify({
            "success": False,
            "error": f"Case has {e.assessment_count} assessments. Use force=true to delete anyway."
        }), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@kaimo_admin_bp.route('/cases/<int:case_id>', methods=['GET'])
@require_permission('admin:kaimo:manage')
def get_case_admin(case_id: int):
    """Get KAIMO case details for admin (with all documents and hints)."""
    try:
        case_details = KaimoCaseService.get_case_details(case_id)
        return jsonify({"success": True, "case": case_details}), 200

    except CaseNotFoundException as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@kaimo_admin_bp.route('/cases/<int:case_id>/documents', methods=['POST'])
@require_permission('admin:kaimo:manage')
def add_document(case_id: int):
    """Add a document to a KAIMO case."""
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

    try:
        # Verify case exists first
        KaimoCaseService.get_case_by_id(case_id)

        document = KaimoDocumentService.add_document(
            case_id=case_id,
            title=title,
            content=content,
            document_type=document_type,
            document_date=document_date,
            sort_order=sort_order
        )

        return jsonify({
            "success": True,
            "document": {
                "id": document.id,
                "title": document.title,
                "document_type": document.document_type,
                "sort_order": document.sort_order,
            }
        }), 201

    except CaseNotFoundException as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except InvalidDocumentTypeException as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except InvalidDateFormatException as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@kaimo_admin_bp.route('/cases/<int:case_id>/documents/<int:doc_id>', methods=['PUT'])
@require_permission('admin:kaimo:manage')
def update_document(case_id: int, doc_id: int):
    """Update a document in a KAIMO case."""
    data = request.get_json() or {}

    try:
        document = KaimoDocumentService.update_document(
            case_id=case_id,
            doc_id=doc_id,
            title=data.get('title'),
            content=data.get('content'),
            document_type=data.get('document_type'),
            document_date=data.get('document_date'),
            sort_order=data.get('sort_order')
        )

        return jsonify({
            "success": True,
            "document": {
                "id": document.id,
                "title": document.title,
            }
        }), 200

    except DocumentNotFoundException as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except InvalidDocumentTypeException as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except InvalidDateFormatException as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@kaimo_admin_bp.route('/cases/<int:case_id>/documents/<int:doc_id>', methods=['DELETE'])
@require_permission('admin:kaimo:manage')
def delete_document(case_id: int, doc_id: int):
    """Delete a document from a KAIMO case."""
    try:
        KaimoDocumentService.delete_document(case_id, doc_id)
        return jsonify({"success": True, "document_id": doc_id}), 200

    except DocumentNotFoundException as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@kaimo_admin_bp.route('/cases/<int:case_id>/hints', methods=['POST'])
@require_permission('admin:kaimo:manage')
def add_hint(case_id: int):
    """Add a hint to a KAIMO case."""
    data = request.get_json() or {}
    content = data.get('content')
    document_id = data.get('document_id')
    expected_category_id = data.get('expected_category_id')
    expected_subcategory_id = data.get('expected_subcategory_id')
    expected_rating = data.get('expected_rating')
    sort_order = data.get('sort_order', 0)

    if not content:
        return jsonify({"success": False, "error": "content is required"}), 400

    try:
        # Verify case exists first
        KaimoCaseService.get_case_by_id(case_id)

        hint = KaimoHintService.add_hint(
            case_id=case_id,
            content=content,
            document_id=document_id,
            expected_category_id=expected_category_id,
            expected_subcategory_id=expected_subcategory_id,
            expected_rating=expected_rating,
            sort_order=sort_order
        )

        return jsonify({
            "success": True,
            "hint": {
                "id": hint.id,
                "content": hint.content[:100] + '...' if len(hint.content) > 100 else hint.content,
                "sort_order": hint.sort_order,
            }
        }), 201

    except CaseNotFoundException as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except DocumentNotFoundException as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except InvalidRatingException as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@kaimo_admin_bp.route('/cases/<int:case_id>/hints/<int:hint_id>', methods=['PUT'])
@require_permission('admin:kaimo:manage')
def update_hint(case_id: int, hint_id: int):
    """Update a hint in a KAIMO case."""
    data = request.get_json() or {}

    try:
        hint = KaimoHintService.update_hint(
            case_id=case_id,
            hint_id=hint_id,
            content=data.get('content'),
            document_id=data.get('document_id'),
            expected_category_id=data.get('expected_category_id'),
            expected_subcategory_id=data.get('expected_subcategory_id'),
            expected_rating=data.get('expected_rating'),
            sort_order=data.get('sort_order')
        )

        return jsonify({
            "success": True,
            "hint": {
                "id": hint.id,
                "content": hint.content[:100] + '...' if len(hint.content) > 100 else hint.content,
            }
        }), 200

    except HintNotFoundException as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except DocumentNotFoundException as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except InvalidRatingException as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@kaimo_admin_bp.route('/cases/<int:case_id>/hints/<int:hint_id>', methods=['DELETE'])
@require_permission('admin:kaimo:manage')
def delete_hint(case_id: int, hint_id: int):
    """Delete a hint from a KAIMO case."""
    try:
        KaimoHintService.delete_hint(case_id, hint_id)
        return jsonify({"success": True, "hint_id": hint_id}), 200

    except HintNotFoundException as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@kaimo_admin_bp.route('/cases/<int:case_id>/results', methods=['GET'])
@require_permission('admin:kaimo:results')
def get_case_results(case_id: int):
    """Get aggregated assessment results for a KAIMO case."""
    try:
        results = KaimoCaseService.get_case_results(case_id)
        return jsonify({"success": True, **results}), 200

    except CaseNotFoundException as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@kaimo_admin_bp.route('/categories', methods=['GET'])
@require_permission('admin:kaimo:manage')
def get_categories_admin():
    """Get all KAIMO categories with subcategories."""
    try:
        categories = KaimoCategoryService.get_all_categories_with_subcategories()
        return jsonify({"success": True, "categories": categories}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
