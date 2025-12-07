"""KAIMO Case Service.

Business logic for managing KAIMO cases.
"""

from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy import func

from db.db import db
from db.models import (
    KaimoCase,
    KaimoDocument,
    KaimoHint,
    KaimoCategory,
    KaimoCaseCategory,
    KaimoUserAssessment,
)


class CaseNotFoundException(Exception):
    """Raised when a case is not found."""
    pass


class CaseAlreadyExistsException(Exception):
    """Raised when trying to create a case with a duplicate name."""
    pass


class CaseHasAssessmentsException(Exception):
    """Raised when trying to delete a case with assessments."""
    def __init__(self, assessment_count: int):
        self.assessment_count = assessment_count
        super().__init__(f"Case has {assessment_count} assessments")


class KaimoCaseService:
    """Service for managing KAIMO cases."""

    @staticmethod
    def get_all_cases_with_counts() -> List[Dict]:
        """Get all KAIMO cases with document, hint, and assessment counts.

        Returns:
            List of case dictionaries with counts.
        """
        cases = KaimoCase.query.order_by(KaimoCase.created_at.desc()).all()

        # Get counts in bulk for efficiency
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

        result = []
        for c in cases:
            result.append({
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

        return result

    @staticmethod
    def get_case_by_id(case_id: int) -> KaimoCase:
        """Get a KAIMO case by ID.

        Args:
            case_id: The case ID.

        Returns:
            The KaimoCase instance.

        Raises:
            CaseNotFoundException: If the case doesn't exist.
        """
        case = KaimoCase.query.get(case_id)
        if not case:
            raise CaseNotFoundException(f"Case {case_id} not found")
        return case

    @staticmethod
    def create_case(
        name: str,
        display_name: str,
        created_by: str,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        category_ids: Optional[List[int]] = None
    ) -> KaimoCase:
        """Create a new KAIMO case.

        Args:
            name: Unique case name (identifier).
            display_name: Human-readable case name.
            created_by: Username of creator.
            description: Optional case description.
            icon: Optional icon identifier.
            color: Optional color code.
            category_ids: Optional list of category IDs to link. If not provided,
                         default categories will be used.

        Returns:
            The created KaimoCase instance.

        Raises:
            CaseAlreadyExistsException: If a case with this name already exists.
        """
        # Check for duplicate name
        existing = KaimoCase.query.filter_by(name=name).first()
        if existing:
            raise CaseAlreadyExistsException(f"Case with name '{name}' already exists")

        # Create case
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
        db.session.flush()  # Get case.id

        # Link categories
        if category_ids and isinstance(category_ids, list):
            categories = KaimoCategory.query.filter(KaimoCategory.id.in_(category_ids)).all()
        else:
            # Use default categories
            categories = KaimoCategory.query.filter_by(is_default=True).order_by(KaimoCategory.sort_order).all()

        for idx, cat in enumerate(categories, start=1):
            link = KaimoCaseCategory(case_id=case.id, category_id=cat.id, sort_order=idx)
            db.session.add(link)

        db.session.commit()
        return case

    @staticmethod
    def update_case(
        case_id: int,
        name: Optional[str] = None,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        status: Optional[str] = None
    ) -> KaimoCase:
        """Update a KAIMO case.

        Args:
            case_id: The case ID.
            name: Optional new name.
            display_name: Optional new display name.
            description: Optional new description.
            icon: Optional new icon.
            color: Optional new color.
            status: Optional new status (draft, published, archived).

        Returns:
            The updated KaimoCase instance.

        Raises:
            CaseNotFoundException: If the case doesn't exist.
            CaseAlreadyExistsException: If the new name is already taken.
        """
        case = KaimoCaseService.get_case_by_id(case_id)

        # Update name if provided and check for duplicates
        if name is not None:
            existing = KaimoCase.query.filter(
                KaimoCase.name == name,
                KaimoCase.id != case_id
            ).first()
            if existing:
                raise CaseAlreadyExistsException(f"Case with name '{name}' already exists")
            case.name = name

        # Update other fields
        if display_name is not None:
            case.display_name = display_name
        if description is not None:
            case.description = description
        if icon is not None:
            case.icon = icon
        if color is not None:
            case.color = color
        if status is not None and status in ('draft', 'published', 'archived'):
            case.status = status
            if status == 'published' and not case.published_at:
                case.published_at = datetime.utcnow()

        case.updated_at = datetime.utcnow()
        db.session.commit()
        return case

    @staticmethod
    def publish_case(case_id: int) -> KaimoCase:
        """Publish a KAIMO case.

        Args:
            case_id: The case ID.

        Returns:
            The updated KaimoCase instance.

        Raises:
            CaseNotFoundException: If the case doesn't exist.
        """
        case = KaimoCaseService.get_case_by_id(case_id)
        case.status = 'published'
        case.published_at = datetime.utcnow()
        case.updated_at = datetime.utcnow()
        db.session.commit()
        return case

    @staticmethod
    def delete_case(case_id: int, force: bool = False) -> None:
        """Delete a KAIMO case.

        Args:
            case_id: The case ID.
            force: If True, delete even if assessments exist.

        Raises:
            CaseNotFoundException: If the case doesn't exist.
            CaseHasAssessmentsException: If the case has assessments and force=False.
        """
        case = KaimoCaseService.get_case_by_id(case_id)

        # Check for assessments
        assessment_count = KaimoUserAssessment.query.filter_by(case_id=case_id).count()
        if assessment_count > 0 and not force:
            raise CaseHasAssessmentsException(assessment_count)

        db.session.delete(case)
        db.session.commit()

    @staticmethod
    def get_case_details(case_id: int) -> Dict:
        """Get detailed case information including documents, hints, and categories.

        Args:
            case_id: The case ID.

        Returns:
            Dictionary with complete case details.

        Raises:
            CaseNotFoundException: If the case doesn't exist.
        """
        case = KaimoCaseService.get_case_by_id(case_id)

        # Get related data
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

        return {
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

    @staticmethod
    def get_case_results(case_id: int) -> Dict:
        """Get aggregated assessment results for a case.

        Args:
            case_id: The case ID.

        Returns:
            Dictionary with statistics and hint results.

        Raises:
            CaseNotFoundException: If the case doesn't exist.
        """
        from db.models import KaimoHintAssignment

        case = KaimoCaseService.get_case_by_id(case_id)

        # Get all assessments
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

        return {
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
        }
