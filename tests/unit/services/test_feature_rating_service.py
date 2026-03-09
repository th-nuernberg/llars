"""
Unit tests for FeatureRatingService.

Tests feature-rating related business logic including:
- Getting user feature ratings for a thread
- Building feature rating maps
- Checking if a user has fully rated all features
"""

import pytest
from services.feature_rating_service import FeatureRatingService


class TestGetUserRatingsForThread:
    """Tests for FeatureRatingService.get_user_ratings_for_thread."""

    def test_FEAT_RATE_001_returns_ratings_for_user_and_thread(self, app, db, app_context):
        """[FEAT_RATE-001] Should return all ratings for a specific user and thread."""
        from db.models.user import User
        from db.models.scenario import (
            FeatureFunctionType, EvaluationItem, Feature, FeatureType,
            UserFeatureRating,
        )

        # Seed prerequisite data
        fft = FeatureFunctionType(name='test_func')
        db.session.add(fft)
        db.session.commit()

        ft = FeatureType(type_id=1, name='summary')
        db.session.add(ft)
        db.session.commit()

        user = User(username='rater1', password_hash='x', api_key='k1')
        db.session.add(user)
        db.session.commit()

        item = EvaluationItem(
            chat_id=1, institut_id=1,
            subject='Test thread', function_type_id=fft.function_type_id,
        )
        db.session.add(item)
        db.session.commit()

        feat1 = Feature(item_id=item.item_id, type_id=ft.type_id, content='f1')
        feat2 = Feature(item_id=item.item_id, type_id=ft.type_id, content='f2')
        db.session.add_all([feat1, feat2])
        db.session.commit()

        r1 = UserFeatureRating(user_id=user.id, feature_id=feat1.feature_id, rating_content=4.0)
        r2 = UserFeatureRating(user_id=user.id, feature_id=feat2.feature_id, rating_content=3.0)
        db.session.add_all([r1, r2])
        db.session.commit()

        ratings = FeatureRatingService.get_user_ratings_for_thread(user.id, item.item_id)

        assert len(ratings) == 2
        feature_ids = {r.feature_id for r in ratings}
        assert feat1.feature_id in feature_ids
        assert feat2.feature_id in feature_ids

    def test_FEAT_RATE_002_returns_empty_when_no_ratings(self, app, db, app_context):
        """[FEAT_RATE-002] Should return empty list when user has no ratings for thread."""
        from db.models.user import User
        from db.models.scenario import (
            FeatureFunctionType, EvaluationItem, Feature, FeatureType,
        )

        fft = FeatureFunctionType(name='test_func')
        db.session.add(fft)
        db.session.commit()

        ft = FeatureType(type_id=1, name='summary')
        db.session.add(ft)
        db.session.commit()

        user = User(username='rater2', password_hash='x', api_key='k2')
        db.session.add(user)
        db.session.commit()

        item = EvaluationItem(
            chat_id=2, institut_id=1,
            subject='Empty', function_type_id=fft.function_type_id,
        )
        db.session.add(item)
        db.session.commit()

        feat = Feature(item_id=item.item_id, type_id=ft.type_id, content='f')
        db.session.add(feat)
        db.session.commit()

        ratings = FeatureRatingService.get_user_ratings_for_thread(user.id, item.item_id)
        assert ratings == []

    def test_FEAT_RATE_003_does_not_return_ratings_from_other_threads(self, app, db, app_context):
        """[FEAT_RATE-003] Should not leak ratings from a different thread."""
        from db.models.user import User
        from db.models.scenario import (
            FeatureFunctionType, EvaluationItem, Feature, FeatureType,
            UserFeatureRating,
        )

        fft = FeatureFunctionType(name='test_func')
        db.session.add(fft)
        db.session.commit()

        ft = FeatureType(type_id=1, name='summary')
        db.session.add(ft)
        db.session.commit()

        user = User(username='rater3', password_hash='x', api_key='k3')
        db.session.add(user)
        db.session.commit()

        item_a = EvaluationItem(chat_id=10, institut_id=1, subject='A', function_type_id=fft.function_type_id)
        item_b = EvaluationItem(chat_id=11, institut_id=1, subject='B', function_type_id=fft.function_type_id)
        db.session.add_all([item_a, item_b])
        db.session.commit()

        feat_a = Feature(item_id=item_a.item_id, type_id=ft.type_id, content='fa')
        feat_b = Feature(item_id=item_b.item_id, type_id=ft.type_id, content='fb')
        db.session.add_all([feat_a, feat_b])
        db.session.commit()

        r_a = UserFeatureRating(user_id=user.id, feature_id=feat_a.feature_id, rating_content=5.0)
        r_b = UserFeatureRating(user_id=user.id, feature_id=feat_b.feature_id, rating_content=2.0)
        db.session.add_all([r_a, r_b])
        db.session.commit()

        ratings = FeatureRatingService.get_user_ratings_for_thread(user.id, item_a.item_id)
        assert len(ratings) == 1
        assert ratings[0].feature_id == feat_a.feature_id


class TestGetUserRatingsMapForThread:
    """Tests for FeatureRatingService.get_user_ratings_map_for_thread."""

    def test_FEAT_RATE_004_returns_dict_keyed_by_feature_id(self, app, db, app_context):
        """[FEAT_RATE-004] Should return a dict mapping feature_id to UserFeatureRating."""
        from db.models.user import User
        from db.models.scenario import (
            FeatureFunctionType, EvaluationItem, Feature, FeatureType,
            UserFeatureRating,
        )

        fft = FeatureFunctionType(name='test_func')
        db.session.add(fft)
        db.session.commit()

        ft = FeatureType(type_id=1, name='summary')
        db.session.add(ft)
        db.session.commit()

        user = User(username='rater4', password_hash='x', api_key='k4')
        db.session.add(user)
        db.session.commit()

        item = EvaluationItem(chat_id=20, institut_id=1, subject='Map', function_type_id=fft.function_type_id)
        db.session.add(item)
        db.session.commit()

        feat1 = Feature(item_id=item.item_id, type_id=ft.type_id, content='f1')
        feat2 = Feature(item_id=item.item_id, type_id=ft.type_id, content='f2')
        db.session.add_all([feat1, feat2])
        db.session.commit()

        r1 = UserFeatureRating(user_id=user.id, feature_id=feat1.feature_id, rating_content=4.0)
        r2 = UserFeatureRating(user_id=user.id, feature_id=feat2.feature_id, rating_content=5.0)
        db.session.add_all([r1, r2])
        db.session.commit()

        rating_map = FeatureRatingService.get_user_ratings_map_for_thread(user.id, item.item_id)

        assert isinstance(rating_map, dict)
        assert len(rating_map) == 2
        assert rating_map[feat1.feature_id].rating_content == 4.0
        assert rating_map[feat2.feature_id].rating_content == 5.0

    def test_FEAT_RATE_005_returns_empty_dict_when_no_ratings(self, app, db, app_context):
        """[FEAT_RATE-005] Should return empty dict when no ratings exist."""
        rating_map = FeatureRatingService.get_user_ratings_map_for_thread(user_id=9999, thread_id=9999)
        assert rating_map == {}


class TestHasUserFullyRatedThread:
    """Tests for FeatureRatingService.has_user_fully_rated_thread."""

    def test_FEAT_RATE_006_returns_true_when_all_features_rated(self, app, db, app_context):
        """[FEAT_RATE-006] Should return True when user rated all features in thread."""
        from db.models.user import User
        from db.models.scenario import (
            FeatureFunctionType, EvaluationItem, Feature, FeatureType,
            UserFeatureRating,
        )

        fft = FeatureFunctionType(name='test_func')
        db.session.add(fft)
        db.session.commit()

        ft = FeatureType(type_id=1, name='summary')
        db.session.add(ft)
        db.session.commit()

        user = User(username='rater5', password_hash='x', api_key='k5')
        db.session.add(user)
        db.session.commit()

        item = EvaluationItem(chat_id=30, institut_id=1, subject='Full', function_type_id=fft.function_type_id)
        db.session.add(item)
        db.session.commit()

        feat1 = Feature(item_id=item.item_id, type_id=ft.type_id, content='f1')
        feat2 = Feature(item_id=item.item_id, type_id=ft.type_id, content='f2')
        db.session.add_all([feat1, feat2])
        db.session.commit()

        db.session.add_all([
            UserFeatureRating(user_id=user.id, feature_id=feat1.feature_id, rating_content=4.0),
            UserFeatureRating(user_id=user.id, feature_id=feat2.feature_id, rating_content=3.0),
        ])
        db.session.commit()

        assert FeatureRatingService.has_user_fully_rated_thread(user.id, item.item_id) is True

    def test_FEAT_RATE_007_returns_false_when_partially_rated(self, app, db, app_context):
        """[FEAT_RATE-007] Should return False when only some features are rated."""
        from db.models.user import User
        from db.models.scenario import (
            FeatureFunctionType, EvaluationItem, Feature, FeatureType,
            UserFeatureRating,
        )

        fft = FeatureFunctionType(name='test_func')
        db.session.add(fft)
        db.session.commit()

        ft = FeatureType(type_id=1, name='summary')
        db.session.add(ft)
        db.session.commit()

        user = User(username='rater6', password_hash='x', api_key='k6')
        db.session.add(user)
        db.session.commit()

        item = EvaluationItem(chat_id=31, institut_id=1, subject='Partial', function_type_id=fft.function_type_id)
        db.session.add(item)
        db.session.commit()

        feat1 = Feature(item_id=item.item_id, type_id=ft.type_id, content='f1')
        feat2 = Feature(item_id=item.item_id, type_id=ft.type_id, content='f2')
        db.session.add_all([feat1, feat2])
        db.session.commit()

        db.session.add(
            UserFeatureRating(user_id=user.id, feature_id=feat1.feature_id, rating_content=4.0)
        )
        db.session.commit()

        assert FeatureRatingService.has_user_fully_rated_thread(user.id, item.item_id) is False

    def test_FEAT_RATE_008_returns_false_when_thread_has_no_features(self, app, db, app_context):
        """[FEAT_RATE-008] Should return False when thread has zero features."""
        from db.models.user import User
        from db.models.scenario import FeatureFunctionType, EvaluationItem

        fft = FeatureFunctionType(name='test_func')
        db.session.add(fft)
        db.session.commit()

        user = User(username='rater7', password_hash='x', api_key='k7')
        db.session.add(user)
        db.session.commit()

        item = EvaluationItem(chat_id=32, institut_id=1, subject='Empty', function_type_id=fft.function_type_id)
        db.session.add(item)
        db.session.commit()

        assert FeatureRatingService.has_user_fully_rated_thread(user.id, item.item_id) is False

    def test_FEAT_RATE_009_returns_false_when_no_ratings_at_all(self, app, db, app_context):
        """[FEAT_RATE-009] Should return False when user has zero ratings on a thread with features."""
        from db.models.user import User
        from db.models.scenario import (
            FeatureFunctionType, EvaluationItem, Feature, FeatureType,
        )

        fft = FeatureFunctionType(name='test_func')
        db.session.add(fft)
        db.session.commit()

        ft = FeatureType(type_id=1, name='summary')
        db.session.add(ft)
        db.session.commit()

        user = User(username='rater8', password_hash='x', api_key='k8')
        db.session.add(user)
        db.session.commit()

        item = EvaluationItem(chat_id=33, institut_id=1, subject='Unrated', function_type_id=fft.function_type_id)
        db.session.add(item)
        db.session.commit()

        feat = Feature(item_id=item.item_id, type_id=ft.type_id, content='f1')
        db.session.add(feat)
        db.session.commit()

        assert FeatureRatingService.has_user_fully_rated_thread(user.id, item.item_id) is False
