"""
Feature Function Types Seeder

Seeds the FeatureFunctionType table with default feature types.
"""


def initialize_feature_function_types(db):
    """
    Initialize feature function types.

    Types:
        1: ranking - Drag & Drop feature sorting
        2: rating - Star rating for features
        3: mail_rating - Email conversation rating
        4: comparison - Side-by-side text comparison
        5: authenticity - Fake/Echt detection
        6: judge - LLM-as-Judge evaluation
        7: text_classification - Text categorization
        8: text_rating - Single text quality rating

    Args:
        db: SQLAlchemy database instance
    """
    # Lazy import to avoid circular dependencies
    from ..tables import FeatureFunctionType

    # Define all function types
    function_types = [
        (1, 'ranking'),
        (2, 'rating'),
        (3, 'mail_rating'),
        (4, 'comparison'),
        (5, 'authenticity'),
        (6, 'judge'),
        (7, 'text_classification'),
        (8, 'text_rating'),
    ]

    # Add missing function types
    for type_id, name in function_types:
        if not FeatureFunctionType.query.filter_by(function_type_id=type_id).first():
            ft = FeatureFunctionType(function_type_id=type_id, name=name)
            db.session.add(ft)

    db.session.commit()
