"""
Feature Rating Service

Handles feature-rating related business logic including:
- User feature ratings
- Thread rating completion status
"""

from typing import Dict, List

from db.database import db


class FeatureRatingService:
    """
    Core service for feature rating management.
    """

    @staticmethod
    def get_user_ratings_for_thread(user_id: int, thread_id: int) -> List['UserFeatureRating']:
        """
        Get all feature ratings by a user for a specific thread.
        """
        from db.models import UserFeatureRating, Feature

        ratings = (
            UserFeatureRating.query.filter_by(user_id=user_id)
            .join(Feature)
            .filter(Feature.thread_id == thread_id)
            .all()
        )
        return ratings

    @staticmethod
    def get_user_ratings_map_for_thread(user_id: int, thread_id: int) -> Dict[int, 'UserFeatureRating']:
        """
        Convenience helper returning a map: feature_id -> UserFeatureRating.
        """
        ratings = FeatureRatingService.get_user_ratings_for_thread(user_id, thread_id)
        return {rating.feature_id: rating for rating in ratings}

    @staticmethod
    def has_user_fully_rated_thread(user_id: int, thread_id: int) -> bool:
        """
        Check if user has rated all features in a thread.
        """
        from db.models import Feature

        total_features = db.session.query(Feature).filter_by(thread_id=thread_id).count()
        if total_features == 0:
            return False

        rated_count = len(FeatureRatingService.get_user_ratings_for_thread(user_id, thread_id))
        return rated_count == total_features

