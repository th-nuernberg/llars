"""
Feature Function Types Seeder

Seeds the FeatureFunctionType table with default feature types.
"""


def initialize_feature_function_types(db):
    """
    Initialize feature function types (ranking, rating, mail_rating, comparison, authenticity).

    Args:
        db: SQLAlchemy database instance
    """
    # Lazy import to avoid circular dependencies
    from ..tables import FeatureFunctionType

    # Check if the feature function types are already in the database
    if not FeatureFunctionType.query.filter_by(function_type_id=1).first():
        ranking = FeatureFunctionType(function_type_id=1, name='ranking')
        db.session.add(ranking)
    if not FeatureFunctionType.query.filter_by(function_type_id=2).first():
        rating = FeatureFunctionType(function_type_id=2, name='rating')
        db.session.add(rating)
    if not FeatureFunctionType.query.filter_by(function_type_id=3).first():
        mail_rating = FeatureFunctionType(function_type_id=3, name='mail_rating')
        db.session.add(mail_rating)
    if not FeatureFunctionType.query.filter_by(function_type_id=4).first():
        comparison = FeatureFunctionType(function_type_id=4, name='comparison')
        db.session.add(comparison)
    if not FeatureFunctionType.query.filter_by(function_type_id=5).first():
        authenticity = FeatureFunctionType(function_type_id=5, name='authenticity')
        db.session.add(authenticity)

    db.session.commit()
