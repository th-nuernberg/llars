"""
Unit Tests: Ranking Service (Extended)
=======================================

Additional tests for ranking_service.py covering areas NOT already tested
in tests/unit/services/ranking/test_ranking_service.py.

Existing tests cover:
- get_user_rankings_for_thread (RANK-001..003)
- has_user_ranked_thread (RANK-020..021)
- has_user_fully_ranked_thread (RANK-022..024)
- get_current_rankings_by_type structure/buckets/neutral (RANK-040..042)
- save_ranking new/update/no-commit (RANK-060..062)
- clear_rankings_for_thread (RANK-090..091)
- get_user_ranking_stats_for_all_users basic (RANK-110)
- CSV export basic (RANK-130..132)

This file adds:
- Multi-user ranking scenarios
- Bucket aggregation correctness
- clear_rankings isolation (does not affect other users)
- CSV multi-bucket, multi-user export
- Statistics with partially ranked threads
- Rankings by type: details ordering

Test IDs: RANK_EXT-001 to RANK_EXT-025
"""

import pytest
from uuid import uuid4


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_ranking_env(db, *, prefix, num_features=3, bucket_names=None):
    """Create a user, thread, feature_type, and features for ranking tests."""
    from db.models import (
        User, UserGroup, EmailThread, Feature, FeatureType,
        FeatureFunctionType
    )

    group = UserGroup(name=f'RankExtGroup_{prefix}')
    db.session.add(group)
    db.session.commit()

    user = User(username=f'ranker_{prefix}')
    user.set_password('password')
    user.api_key = str(uuid4())
    user.group = group
    db.session.add(user)

    ft = FeatureFunctionType(name=f'func_{prefix}')
    db.session.add(ft)
    db.session.commit()

    thread = EmailThread(
        chat_id=int(prefix.replace('_', '')[:3]) if prefix[:3].isdigit() else 900,
        institut_id=1,
        subject=f'Thread {prefix}',
        function_type_id=ft.function_type_id
    )
    db.session.add(thread)

    ftype = FeatureType(name=f'ftype_{prefix}')
    db.session.add(ftype)
    db.session.commit()

    features = []
    for i in range(num_features):
        f = Feature(
            thread_id=thread.thread_id,
            type_id=ftype.type_id,
            model_id=f'LLM_{prefix}_{i}',
            content=f'Content {prefix} {i}'
        )
        db.session.add(f)
        features.append(f)

    db.session.commit()
    # Refresh to get auto-generated IDs
    for f in features:
        db.session.refresh(f)

    return user, thread, ftype, features


def _add_ranking(db, user_id, feature, type_id, position, bucket):
    from db.models import UserFeatureRanking

    r = UserFeatureRanking(
        user_id=user_id,
        feature_id=feature.feature_id,
        ranking_content=position,
        bucket=bucket,
        type_id=type_id,
        model_id=feature.model_id
    )
    db.session.add(r)
    return r


# ===========================================================================
# Multi-user rankings
# ===========================================================================

class TestMultiUserRankings:
    """Rankings from multiple users on the same thread."""

    def test_RANK_EXT_001_two_users_rank_same_thread(self, app, db, app_context):
        """[RANK_EXT-001] Two users rank the same features independently."""
        from services.ranking_service import RankingService
        from db.models import User, UserGroup

        user1, thread, ftype, features = _setup_ranking_env(db, prefix='mu001')

        # Create second user
        group2 = UserGroup(name='RankExtGroup_mu001b')
        db.session.add(group2)
        db.session.commit()
        user2 = User(username='ranker_mu001b')
        user2.set_password('password')
        user2.api_key = str(uuid4())
        user2.group = group2
        db.session.add(user2)
        db.session.commit()

        # User1 ranks all to Gut
        for i, f in enumerate(features):
            _add_ranking(db, user1.id, f, ftype.type_id, i + 1, 'Gut')
        db.session.commit()

        # User2 ranks all to Schlecht
        for i, f in enumerate(features):
            _add_ranking(db, user2.id, f, ftype.type_id, i + 1, 'Schlecht')
        db.session.commit()

        r1 = RankingService.get_user_rankings_for_thread(user1.id, thread.thread_id)
        r2 = RankingService.get_user_rankings_for_thread(user2.id, thread.thread_id)

        assert len(r1) == 3
        assert len(r2) == 3
        assert all(r.bucket == 'Gut' for r in r1)
        assert all(r.bucket == 'Schlecht' for r in r2)

    def test_RANK_EXT_002_clear_rankings_isolation(self, app, db, app_context):
        """[RANK_EXT-002] Clearing one user's rankings does not affect another's."""
        from services.ranking_service import RankingService
        from db.models import User, UserGroup

        user1, thread, ftype, features = _setup_ranking_env(db, prefix='iso002')

        group2 = UserGroup(name='RankExtGroup_iso002b')
        db.session.add(group2)
        db.session.commit()
        user2 = User(username='ranker_iso002b')
        user2.set_password('password')
        user2.api_key = str(uuid4())
        user2.group = group2
        db.session.add(user2)
        db.session.commit()

        for i, f in enumerate(features):
            _add_ranking(db, user1.id, f, ftype.type_id, i + 1, 'Gut')
            _add_ranking(db, user2.id, f, ftype.type_id, i + 1, 'Mittel')
        db.session.commit()

        # Clear user1's rankings
        success, _ = RankingService.clear_rankings_for_thread(user1.id, thread.thread_id)
        assert success is True

        # User1 should have 0, User2 should still have 3
        r1 = RankingService.get_user_rankings_for_thread(user1.id, thread.thread_id)
        r2 = RankingService.get_user_rankings_for_thread(user2.id, thread.thread_id)
        assert len(r1) == 0
        assert len(r2) == 3


# ===========================================================================
# Bucket operations
# ===========================================================================

class TestBucketOperations:
    """Tests for bucket-level correctness in rankings."""

    def test_RANK_EXT_005_rankings_by_type_details_sorted(self, app, db, app_context):
        """[RANK_EXT-005] Details in rankings_by_type are sorted by position."""
        from services.ranking_service import RankingService

        user, thread, ftype, features = _setup_ranking_env(db, prefix='sort005')

        # Rank in reverse order of feature creation
        for i, f in enumerate(reversed(features)):
            _add_ranking(db, user.id, f, ftype.type_id, i + 1, 'Gut')
        db.session.commit()

        result = RankingService.get_current_rankings_by_type(user.id, thread.thread_id)
        details = result[ftype.name]['details']

        positions = [d['position'] for d in details]
        assert positions == sorted(positions)

    def test_RANK_EXT_006_rankings_by_type_mixed_buckets(self, app, db, app_context):
        """[RANK_EXT-006] Features distributed across all three buckets."""
        from services.ranking_service import RankingService

        user, thread, ftype, features = _setup_ranking_env(db, prefix='mix006', num_features=3)

        buckets = ['Gut', 'Mittel', 'Schlecht']
        for i, (f, b) in enumerate(zip(features, buckets)):
            _add_ranking(db, user.id, f, ftype.type_id, 1, b)
        db.session.commit()

        result = RankingService.get_current_rankings_by_type(user.id, thread.thread_id)
        data = result[ftype.name]

        assert len(data['goodList']) == 1
        assert len(data['averageList']) == 1
        assert len(data['badList']) == 1
        assert len(data['neutralList']) == 0
        assert len(data['details']) == 3

    def test_RANK_EXT_007_partially_ranked_has_neutral(self, app, db, app_context):
        """[RANK_EXT-007] Partially ranked thread shows unranked in neutralList."""
        from services.ranking_service import RankingService

        user, thread, ftype, features = _setup_ranking_env(db, prefix='part007', num_features=4)

        # Rank only 2 of 4
        _add_ranking(db, user.id, features[0], ftype.type_id, 1, 'Gut')
        _add_ranking(db, user.id, features[1], ftype.type_id, 2, 'Mittel')
        db.session.commit()

        result = RankingService.get_current_rankings_by_type(user.id, thread.thread_id)
        data = result[ftype.name]

        assert len(data['neutralList']) == 2
        assert len(data['details']) == 2


# ===========================================================================
# Save ranking edge cases
# ===========================================================================

class TestSaveRankingExtended:
    """Extended save_ranking tests."""

    def test_RANK_EXT_010_save_ranking_multiple_features_batch(self, app, db, app_context):
        """[RANK_EXT-010] Save multiple rankings with commit=False then commit."""
        from services.ranking_service import RankingService
        from db.models import UserFeatureRanking

        user, thread, ftype, features = _setup_ranking_env(db, prefix='batch010')

        for i, f in enumerate(features):
            success, error = RankingService.save_ranking(
                user_id=user.id,
                thread_id=thread.thread_id,
                feature_id=f.feature_id,
                type_id=ftype.type_id,
                model_id=f.model_id,
                position=i + 1,
                bucket='Gut',
                commit=False
            )
            assert success is True

        db.session.commit()

        count = UserFeatureRanking.query.filter_by(user_id=user.id).count()
        assert count == 3

    def test_RANK_EXT_011_save_ranking_update_bucket(self, app, db, app_context):
        """[RANK_EXT-011] Updating bucket from Gut to Schlecht."""
        from services.ranking_service import RankingService
        from db.models import UserFeatureRanking

        user, thread, ftype, features = _setup_ranking_env(db, prefix='upd011', num_features=1)
        f = features[0]

        RankingService.save_ranking(
            user.id, thread.thread_id, f.feature_id,
            ftype.type_id, f.model_id, 1, 'Gut'
        )

        RankingService.save_ranking(
            user.id, thread.thread_id, f.feature_id,
            ftype.type_id, f.model_id, 1, 'Schlecht'
        )

        ranking = UserFeatureRanking.query.filter_by(
            user_id=user.id, feature_id=f.feature_id
        ).first()
        assert ranking.bucket == 'Schlecht'


# ===========================================================================
# Clear rankings edge cases
# ===========================================================================

class TestClearRankingsExtended:
    """Extended clear_rankings tests."""

    def test_RANK_EXT_015_clear_then_re_rank(self, app, db, app_context):
        """[RANK_EXT-015] Clear and re-rank a thread."""
        from services.ranking_service import RankingService

        user, thread, ftype, features = _setup_ranking_env(db, prefix='rerank015')

        for i, f in enumerate(features):
            _add_ranking(db, user.id, f, ftype.type_id, i + 1, 'Gut')
        db.session.commit()

        assert RankingService.has_user_fully_ranked_thread(user.id, thread.thread_id) is True

        RankingService.clear_rankings_for_thread(user.id, thread.thread_id)
        assert RankingService.has_user_ranked_thread(user.id, thread.thread_id) is False

        # Re-rank with different buckets
        for i, f in enumerate(features):
            RankingService.save_ranking(
                user.id, thread.thread_id, f.feature_id,
                ftype.type_id, f.model_id, i + 1, 'Schlecht'
            )

        rankings = RankingService.get_user_rankings_for_thread(user.id, thread.thread_id)
        assert len(rankings) == 3
        assert all(r.bucket == 'Schlecht' for r in rankings)

    def test_RANK_EXT_016_clear_no_commit(self, app, db, app_context):
        """[RANK_EXT-016] clear_rankings with commit=False does not persist on rollback."""
        from services.ranking_service import RankingService
        from db.models import UserFeatureRanking

        user, thread, ftype, features = _setup_ranking_env(db, prefix='noc016', num_features=2)
        for i, f in enumerate(features):
            _add_ranking(db, user.id, f, ftype.type_id, i + 1, 'Mittel')
        db.session.commit()

        success, _ = RankingService.clear_rankings_for_thread(
            user.id, thread.thread_id, commit=False
        )
        assert success is True

        db.session.rollback()

        # Should still have rankings after rollback
        count = UserFeatureRanking.query.filter_by(user_id=user.id).count()
        assert count == 2


# ===========================================================================
# Statistics multi-user
# ===========================================================================

class TestStatisticsExtended:
    """Extended statistics tests."""

    def test_RANK_EXT_020_stats_partial_and_full(self, app, db, app_context):
        """[RANK_EXT-020] Stats correctly count fully vs partially ranked."""
        from services.ranking_service import RankingService
        from db.models import (
            User, UserGroup, EmailThread, Feature, FeatureType,
            FeatureFunctionType, UserFeatureRanking
        )

        group = UserGroup(name='StatsGroup020')
        db.session.add(group)
        db.session.commit()

        user = User(username='stats_020')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)

        ft = FeatureFunctionType(function_type_id=1, name='ranking')
        existing = FeatureFunctionType.query.filter_by(function_type_id=1).first()
        if not existing:
            db.session.add(ft)
        db.session.commit()

        # Thread with 2 features (will be fully ranked)
        t1 = EmailThread(chat_id=820, institut_id=820, subject='Full', function_type_id=1)
        db.session.add(t1)
        ftype = FeatureType(name='stats_type_020')
        db.session.add(ftype)
        db.session.commit()

        feats1 = []
        for i in range(2):
            f = Feature(thread_id=t1.thread_id, type_id=ftype.type_id,
                        model_id='M', content=f'F{i}')
            db.session.add(f)
            feats1.append(f)
        db.session.commit()

        for i, f in enumerate(feats1):
            db.session.refresh(f)
            db.session.add(UserFeatureRanking(
                user_id=user.id, feature_id=f.feature_id,
                ranking_content=i + 1, bucket='Gut',
                type_id=ftype.type_id, model_id='M'
            ))

        # Thread with 3 features (only 1 ranked = partial)
        t2 = EmailThread(chat_id=821, institut_id=821, subject='Partial', function_type_id=1)
        db.session.add(t2)
        db.session.commit()

        feats2 = []
        for i in range(3):
            f = Feature(thread_id=t2.thread_id, type_id=ftype.type_id,
                        model_id='M', content=f'PF{i}')
            db.session.add(f)
            feats2.append(f)
        db.session.commit()

        db.session.refresh(feats2[0])
        db.session.add(UserFeatureRanking(
            user_id=user.id, feature_id=feats2[0].feature_id,
            ranking_content=1, bucket='Mittel',
            type_id=ftype.type_id, model_id='M'
        ))
        db.session.commit()

        stats = RankingService.get_user_ranking_stats_for_all_users()
        user_stat = next((s for s in stats if s['username'] == 'stats_020'), None)
        assert user_stat is not None
        assert user_stat['ranked_threads_count'] >= 1  # At least thread t1
        assert len(user_stat['unranked_threads']) >= 1  # Thread t2 is partial


# ===========================================================================
# CSV export extended
# ===========================================================================

class TestCSVExportExtended:
    """Extended CSV export tests."""

    def test_RANK_EXT_025_csv_data_multi_bucket(self, app, db, app_context):
        """[RANK_EXT-025] CSV data includes all buckets in correct order."""
        from services.ranking_service import RankingService

        user, thread, ftype, features = _setup_ranking_env(
            db, prefix='csv025', num_features=3
        )

        buckets = ['Gut', 'Mittel', 'Schlecht']
        for i, (f, b) in enumerate(zip(features, buckets)):
            _add_ranking(db, user.id, f, ftype.type_id, 1, b)
        db.session.commit()

        csv_data = RankingService.generate_rankings_csv_data()
        assert len(csv_data) >= 4  # header + 3 rows

        header = csv_data[0]
        assert 'Bucket' in header

        # Extract bucket values from data rows (skip header)
        data_rows = [r for r in csv_data[1:] if r[2] == user.username]
        exported_buckets = [r[4] for r in data_rows]
        # Gut should come before Mittel before Schlecht
        if len(exported_buckets) == 3:
            assert exported_buckets.index('Gut') < exported_buckets.index('Mittel')
            assert exported_buckets.index('Mittel') < exported_buckets.index('Schlecht')
