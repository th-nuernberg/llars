"""
Feature Function Types Seeder

Seeds the FeatureFunctionType table with default feature types.
"""


def initialize_feature_function_types(db):
    """
    Initialize feature function types.

    Types:
        Generalized (domain-independent):
            1: ranking - Drag & Drop feature sorting
            2: rating - Star rating for features
            4: comparison - Side-by-side text comparison
            7: labeling - Text categorization (binary, multi-class, multi-label)

        LLARS-specific (email counseling domain):
            3: mail_rating - Email conversation rating
            5: authenticity - Fake/Echt detection

    Args:
        db: SQLAlchemy database instance
    """
    # Lazy import to avoid circular dependencies
    from ..tables import FeatureFunctionType

    # Define all function types
    # Note: IDs 6 (judge) and 8 (text_rating) were removed as they were
    # either backend-only services or redundant with existing types
    function_types = [
        # Generalized types
        (1, 'ranking'),
        (2, 'rating'),
        (4, 'comparison'),
        (7, 'labeling'),
        # LLARS-specific types
        (3, 'mail_rating'),
        (5, 'authenticity'),
    ]

    # Add missing function types
    for type_id, name in function_types:
        existing = FeatureFunctionType.query.filter_by(function_type_id=type_id).first()
        if not existing:
            ft = FeatureFunctionType(function_type_id=type_id, name=name)
            db.session.add(ft)
        elif existing.name != name:
            # Keep IDs stable but update legacy names (e.g., text_classification -> labeling)
            existing.name = name

    db.session.commit()
