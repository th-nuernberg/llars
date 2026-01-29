"""KAIMO Export/Import Service.

Handles exporting and importing KAIMO cases as JSON for backup and seeding.
"""
from datetime import datetime
from typing import Optional
from db import db
from db.models import (
    KaimoCase,
    KaimoDocument,
    KaimoHint,
    KaimoCategory,
    KaimoSubcategory,
    KaimoCaseCategory,
)


class CaseExportException(Exception):
    """Raised when export fails."""
    pass


class CaseImportException(Exception):
    """Raised when import fails."""
    pass


class KaimoExportService:
    """Service for exporting and importing KAIMO cases."""

    EXPORT_VERSION = "1.0"

    @staticmethod
    def export_case(case_id: int, include_assessments: bool = False) -> dict:
        """
        Export a KAIMO case as JSON.

        Args:
            case_id: ID of the case to export
            include_assessments: Whether to include user assessments (default: False)

        Returns:
            Dict containing full case data for import

        Raises:
            CaseExportException: If case not found
        """
        case = KaimoCase.query.get(case_id)
        if not case:
            raise CaseExportException(f"Case with ID {case_id} not found")

        # Build category mapping (name -> display_name for reference)
        categories_data = []
        for case_cat in sorted(case.categories, key=lambda c: c.sort_order):
            cat = case_cat.category
            categories_data.append({
                "name": cat.name,
                "display_name": cat.display_name,
                "color": cat.color,
                "icon": cat.icon,
            })

        # Build documents
        documents_data = []
        doc_id_to_ref = {}  # Map DB IDs to export refs
        for idx, doc in enumerate(sorted(case.documents, key=lambda d: d.sort_order)):
            doc_ref = f"doc_{idx}"
            doc_id_to_ref[doc.id] = doc_ref
            documents_data.append({
                "ref": doc_ref,
                "title": doc.title,
                "content": doc.content,
                "document_type": doc.document_type,
                "document_date": doc.document_date.isoformat() if doc.document_date else None,
                "sort_order": doc.sort_order,
            })

        # Build hints
        hints_data = []
        for hint in sorted(case.hints, key=lambda h: h.sort_order):
            hint_export = {
                "content": hint.content,
                "sort_order": hint.sort_order,
                "expected_rating": hint.expected_rating,
            }

            # Reference document by ref
            if hint.document_id and hint.document_id in doc_id_to_ref:
                hint_export["document_ref"] = doc_id_to_ref[hint.document_id]

            # Reference category by name
            if hint.expected_category:
                hint_export["expected_category"] = hint.expected_category.name

            # Reference subcategory by name
            if hint.expected_subcategory:
                hint_export["expected_subcategory"] = hint.expected_subcategory.name

            hints_data.append(hint_export)

        export_data = {
            "export_version": KaimoExportService.EXPORT_VERSION,
            "exported_at": datetime.utcnow().isoformat(),
            "case": {
                "name": case.name,
                "display_name": case.display_name,
                "description": case.description,
                "icon": case.icon,
                "color": case.color,
                "status": case.status,
            },
            "categories": categories_data,
            "documents": documents_data,
            "hints": hints_data,
        }

        return export_data

    @staticmethod
    def import_case(
        data: dict,
        created_by: str,
        name_override: Optional[str] = None,
        status_override: Optional[str] = None
    ) -> KaimoCase:
        """
        Import a KAIMO case from JSON.

        Args:
            data: Export data dict
            created_by: Username of importer
            name_override: Override the case name (for avoiding conflicts)
            status_override: Override the status (default: 'draft')

        Returns:
            Created KaimoCase object

        Raises:
            CaseImportException: If import fails
        """
        # Validate export version
        version = data.get("export_version", "unknown")
        if version != KaimoExportService.EXPORT_VERSION:
            raise CaseImportException(
                f"Unsupported export version: {version}. Expected: {KaimoExportService.EXPORT_VERSION}"
            )

        case_data = data.get("case", {})
        if not case_data:
            raise CaseImportException("Missing 'case' data in import")

        # Check for name conflict
        case_name = name_override or case_data.get("name")
        if not case_name:
            raise CaseImportException("Case name is required")

        existing = KaimoCase.query.filter_by(name=case_name).first()
        if existing:
            raise CaseImportException(f"Case with name '{case_name}' already exists")

        # Create case
        case = KaimoCase(
            name=case_name,
            display_name=case_data.get("display_name", case_name),
            description=case_data.get("description"),
            icon=case_data.get("icon"),
            color=case_data.get("color"),
            status=status_override or "draft",
            created_by=created_by,
        )
        db.session.add(case)
        db.session.flush()

        # Link categories
        categories_data = data.get("categories", [])
        for idx, cat_data in enumerate(categories_data):
            cat_name = cat_data.get("name")
            if cat_name:
                category = KaimoCategory.query.filter_by(name=cat_name).first()
                if category:
                    link = KaimoCaseCategory(
                        case_id=case.id,
                        category_id=category.id,
                        sort_order=idx
                    )
                    db.session.add(link)

        # Create documents and build ref mapping
        documents_data = data.get("documents", [])
        doc_ref_to_id = {}
        for doc_data in documents_data:
            doc = KaimoDocument(
                case_id=case.id,
                title=doc_data.get("title", "Untitled"),
                content=doc_data.get("content", ""),
                document_type=doc_data.get("document_type", "sonstiges"),
                sort_order=doc_data.get("sort_order", 0),
            )

            # Parse date if present
            date_str = doc_data.get("document_date")
            if date_str:
                try:
                    from datetime import date
                    doc.document_date = date.fromisoformat(date_str)
                except ValueError:
                    pass  # Skip invalid dates

            db.session.add(doc)
            db.session.flush()

            # Store ref mapping
            ref = doc_data.get("ref")
            if ref:
                doc_ref_to_id[ref] = doc.id

        # Create hints
        hints_data = data.get("hints", [])
        for hint_data in hints_data:
            hint = KaimoHint(
                case_id=case.id,
                content=hint_data.get("content", ""),
                sort_order=hint_data.get("sort_order", 0),
                expected_rating=hint_data.get("expected_rating"),
            )

            # Link document by ref
            doc_ref = hint_data.get("document_ref")
            if doc_ref and doc_ref in doc_ref_to_id:
                hint.document_id = doc_ref_to_id[doc_ref]

            # Link expected category by name
            cat_name = hint_data.get("expected_category")
            if cat_name:
                category = KaimoCategory.query.filter_by(name=cat_name).first()
                if category:
                    hint.expected_category_id = category.id

            # Link expected subcategory by name
            subcat_name = hint_data.get("expected_subcategory")
            if subcat_name and hint.expected_category_id:
                subcategory = KaimoSubcategory.query.filter_by(
                    category_id=hint.expected_category_id,
                    name=subcat_name
                ).first()
                if subcategory:
                    hint.expected_subcategory_id = subcategory.id

            db.session.add(hint)

        db.session.commit()
        return case
