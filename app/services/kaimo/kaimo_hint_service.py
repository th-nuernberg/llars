"""KAIMO Hint Service.

Business logic for managing KAIMO hints.
"""

from datetime import datetime
from typing import Optional

from db.database import db
from db.models import KaimoCase, KaimoHint, KaimoDocument


class HintNotFoundException(Exception):
    """Raised when a hint is not found."""
    pass


class DocumentNotFoundException(Exception):
    """Raised when a referenced document is not found."""
    pass


class InvalidRatingException(Exception):
    """Raised when an invalid rating is provided."""
    pass


VALID_RATINGS = ('risk', 'resource', 'unclear')


class KaimoHintService:
    """Service for managing KAIMO hints."""

    @staticmethod
    def add_hint(
        case_id: int,
        content: str,
        document_id: Optional[int] = None,
        expected_category_id: Optional[int] = None,
        expected_subcategory_id: Optional[int] = None,
        expected_rating: Optional[str] = None,
        sort_order: int = 0
    ) -> KaimoHint:
        """Add a hint to a KAIMO case.

        Args:
            case_id: The case ID.
            content: Hint content.
            document_id: Optional document ID this hint relates to.
            expected_category_id: Optional expected category ID.
            expected_subcategory_id: Optional expected subcategory ID.
            expected_rating: Optional expected rating (risk, resource, unclear).
            sort_order: Display order (default: 0).

        Returns:
            The created KaimoHint instance.

        Raises:
            DocumentNotFoundException: If document_id doesn't exist in the case.
            InvalidRatingException: If expected_rating is invalid.
        """
        # Validate rating
        if expected_rating and expected_rating not in VALID_RATINGS:
            raise InvalidRatingException(
                f"expected_rating must be one of: {', '.join(VALID_RATINGS)}"
            )

        # Validate document_id if provided
        if document_id:
            doc = KaimoDocument.query.filter_by(id=document_id, case_id=case_id).first()
            if not doc:
                raise DocumentNotFoundException(f"Document {document_id} not found in case {case_id}")

        # Create hint
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

        # Update case timestamp
        case = KaimoCase.query.get(case_id)
        if case:
            case.updated_at = datetime.utcnow()

        db.session.commit()
        return hint

    @staticmethod
    def get_hint(case_id: int, hint_id: int) -> KaimoHint:
        """Get a hint by ID.

        Args:
            case_id: The case ID.
            hint_id: The hint ID.

        Returns:
            The KaimoHint instance.

        Raises:
            HintNotFoundException: If the hint doesn't exist.
        """
        hint = KaimoHint.query.filter_by(id=hint_id, case_id=case_id).first()
        if not hint:
            raise HintNotFoundException(f"Hint {hint_id} not found in case {case_id}")
        return hint

    @staticmethod
    def update_hint(
        case_id: int,
        hint_id: int,
        content: Optional[str] = None,
        document_id: Optional[int] = None,
        expected_category_id: Optional[int] = None,
        expected_subcategory_id: Optional[int] = None,
        expected_rating: Optional[str] = None,
        sort_order: Optional[int] = None
    ) -> KaimoHint:
        """Update a hint.

        Args:
            case_id: The case ID.
            hint_id: The hint ID.
            content: Optional new content.
            document_id: Optional new document ID (or None to clear).
            expected_category_id: Optional new expected category ID.
            expected_subcategory_id: Optional new expected subcategory ID.
            expected_rating: Optional new expected rating.
            sort_order: Optional new sort order.

        Returns:
            The updated KaimoHint instance.

        Raises:
            HintNotFoundException: If the hint doesn't exist.
            DocumentNotFoundException: If document_id doesn't exist in the case.
            InvalidRatingException: If expected_rating is invalid.
        """
        hint = KaimoHintService.get_hint(case_id, hint_id)

        # Update content
        if content is not None:
            hint.content = content

        # Update document_id
        if document_id is not None:
            if document_id:
                doc = KaimoDocument.query.filter_by(id=document_id, case_id=case_id).first()
                if not doc:
                    raise DocumentNotFoundException(f"Document {document_id} not found in case {case_id}")
            hint.document_id = document_id

        # Update expected category
        if expected_category_id is not None:
            hint.expected_category_id = expected_category_id

        # Update expected subcategory
        if expected_subcategory_id is not None:
            hint.expected_subcategory_id = expected_subcategory_id

        # Update expected rating
        if expected_rating is not None:
            if expected_rating and expected_rating not in VALID_RATINGS:
                raise InvalidRatingException(
                    f"expected_rating must be one of: {', '.join(VALID_RATINGS)}"
                )
            hint.expected_rating = expected_rating

        # Update sort order
        if sort_order is not None:
            hint.sort_order = sort_order

        # Update case timestamp
        case = KaimoCase.query.get(case_id)
        if case:
            case.updated_at = datetime.utcnow()

        db.session.commit()
        return hint

    @staticmethod
    def delete_hint(case_id: int, hint_id: int) -> None:
        """Delete a hint.

        Args:
            case_id: The case ID.
            hint_id: The hint ID.

        Raises:
            HintNotFoundException: If the hint doesn't exist.
        """
        hint = KaimoHintService.get_hint(case_id, hint_id)

        db.session.delete(hint)

        # Update case timestamp
        case = KaimoCase.query.get(case_id)
        if case:
            case.updated_at = datetime.utcnow()

        db.session.commit()
