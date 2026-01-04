"""KAIMO Document Service.

Business logic for managing KAIMO documents.
"""

from datetime import datetime
from typing import Optional

from db.database import db
from db.models import KaimoCase, KaimoDocument


class DocumentNotFoundException(Exception):
    """Raised when a document is not found."""
    pass


class InvalidDocumentTypeException(Exception):
    """Raised when an invalid document type is provided."""
    pass


class InvalidDateFormatException(Exception):
    """Raised when an invalid date format is provided."""
    pass


VALID_DOCUMENT_TYPES = ('aktenvermerk', 'bericht', 'protokoll', 'sonstiges')


class KaimoDocumentService:
    """Service for managing KAIMO documents."""

    @staticmethod
    def add_document(
        case_id: int,
        title: str,
        content: str,
        document_type: str,
        document_date: Optional[str] = None,
        sort_order: int = 0
    ) -> KaimoDocument:
        """Add a document to a KAIMO case.

        Args:
            case_id: The case ID.
            title: Document title.
            content: Document content.
            document_type: Document type (aktenvermerk, bericht, protokoll, sonstiges).
            document_date: Optional ISO date string.
            sort_order: Display order (default: 0).

        Returns:
            The created KaimoDocument instance.

        Raises:
            InvalidDocumentTypeException: If document_type is invalid.
            InvalidDateFormatException: If document_date format is invalid.
        """
        # Validate document type
        if document_type not in VALID_DOCUMENT_TYPES:
            raise InvalidDocumentTypeException(
                f"document_type must be one of: {', '.join(VALID_DOCUMENT_TYPES)}"
            )

        # Parse date if provided
        parsed_date = None
        if document_date:
            try:
                parsed_date = datetime.fromisoformat(document_date.replace('Z', '+00:00')).date()
            except (ValueError, AttributeError):
                raise InvalidDateFormatException("Invalid date format. Expected ISO format.")

        # Create document
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

        # Update case timestamp
        case = KaimoCase.query.get(case_id)
        if case:
            case.updated_at = datetime.utcnow()

        db.session.commit()
        return document

    @staticmethod
    def get_document(case_id: int, doc_id: int) -> KaimoDocument:
        """Get a document by ID.

        Args:
            case_id: The case ID.
            doc_id: The document ID.

        Returns:
            The KaimoDocument instance.

        Raises:
            DocumentNotFoundException: If the document doesn't exist.
        """
        document = KaimoDocument.query.filter_by(id=doc_id, case_id=case_id).first()
        if not document:
            raise DocumentNotFoundException(f"Document {doc_id} not found in case {case_id}")
        return document

    @staticmethod
    def update_document(
        case_id: int,
        doc_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        document_type: Optional[str] = None,
        document_date: Optional[str] = None,
        sort_order: Optional[int] = None
    ) -> KaimoDocument:
        """Update a document.

        Args:
            case_id: The case ID.
            doc_id: The document ID.
            title: Optional new title.
            content: Optional new content.
            document_type: Optional new document type.
            document_date: Optional new date (ISO string or None to clear).
            sort_order: Optional new sort order.

        Returns:
            The updated KaimoDocument instance.

        Raises:
            DocumentNotFoundException: If the document doesn't exist.
            InvalidDocumentTypeException: If document_type is invalid.
            InvalidDateFormatException: If document_date format is invalid.
        """
        document = KaimoDocumentService.get_document(case_id, doc_id)

        # Update title
        if title is not None:
            document.title = title

        # Update content
        if content is not None:
            document.content = content

        # Update document type
        if document_type is not None:
            if document_type not in VALID_DOCUMENT_TYPES:
                raise InvalidDocumentTypeException(
                    f"document_type must be one of: {', '.join(VALID_DOCUMENT_TYPES)}"
                )
            document.document_type = document_type

        # Update document date
        if document_date is not None:
            if document_date:
                try:
                    document.document_date = datetime.fromisoformat(
                        document_date.replace('Z', '+00:00')
                    ).date()
                except (ValueError, AttributeError):
                    raise InvalidDateFormatException("Invalid date format. Expected ISO format.")
            else:
                document.document_date = None

        # Update sort order
        if sort_order is not None:
            document.sort_order = sort_order

        # Update case timestamp
        case = KaimoCase.query.get(case_id)
        if case:
            case.updated_at = datetime.utcnow()

        db.session.commit()
        return document

    @staticmethod
    def delete_document(case_id: int, doc_id: int) -> None:
        """Delete a document.

        Args:
            case_id: The case ID.
            doc_id: The document ID.

        Raises:
            DocumentNotFoundException: If the document doesn't exist.
        """
        document = KaimoDocumentService.get_document(case_id, doc_id)

        db.session.delete(document)

        # Update case timestamp
        case = KaimoCase.query.get(case_id)
        if case:
            case.updated_at = datetime.utcnow()

        db.session.commit()
