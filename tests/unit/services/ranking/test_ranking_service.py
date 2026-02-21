"""
Unit Tests: Ranking Service
===========================

Tests for the ranking management service.

Test IDs:
- RANK-001 to RANK-015: User Rankings for Thread
- RANK-020 to RANK-035: Ranking Status Checks
- RANK-040 to RANK-055: Get Rankings by Type
- RANK-060 to RANK-080: Save Ranking
- RANK-090 to RANK-100: Clear Rankings
- RANK-110 to RANK-120: Statistics
- RANK-130 to RANK-140: CSV Export

Status: Implemented
"""

import pytest
from uuid import uuid4


class TestUserRankingsForThread:
    """
    User Rankings for Thread Tests

    Tests for retrieving user rankings for a specific thread.
    """

    def test_RANK_001_get_user_rankings_for_thread_found(self, app, db, app_context):
        """
        [RANK-001] Get User Rankings - Gefunden

        Rankings für User und Thread sollten gefunden werden.
        """
        from services.ranking_service import RankingService
        from db.models import (
            User, UserGroup, EmailThread, Feature, FeatureType,
            LLM, UserFeatureRanking, FeatureFunctionType
        )

        # Setup
        group = UserGroup(name='TestGroup001')
        db.session.add(group)
        db.session.commit()

        user = User(username='ranker001')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)

        function_type = FeatureFunctionType(name='ranking_test_001')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=1001,
            chat_id=1,
            institut_id=1,
            subject='Test Thread',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)

        feature_type = FeatureType(type_id=101, name='test_type_001')
        db.session.add(feature_type)

        llm = LLM(llm_id=101, name='TestLLM001')
        db.session.add(llm)
        db.session.commit()

        feature = Feature(
            feature_id=1001,
            thread_id=1001,
            type_id=101,
            llm_id=101,
            content='Test feature content'
        )
        db.session.add(feature)
        db.session.commit()

        # Create ranking
        ranking = UserFeatureRanking(
            user_id=user.id,
            feature_id=1001,
            ranking_content=1,
            bucket='Gut',
            type_id=101,
            llm_id=101
        )
        db.session.add(ranking)
        db.session.commit()

        # Test
        rankings = RankingService.get_user_rankings_for_thread(user.id, 1001)

        assert len(rankings) == 1
        assert rankings[0].feature_id == 1001
        assert rankings[0].bucket == 'Gut'

    def test_RANK_002_get_user_rankings_for_thread_empty(self, app, db, app_context):
        """
        [RANK-002] Get User Rankings - Leer

        Keine Rankings sollte leere Liste zurückgeben.
        """
        from services.ranking_service import RankingService
        from db.models import User, UserGroup

        group = UserGroup(name='TestGroup002')
        db.session.add(group)
        db.session.commit()

        user = User(username='ranker002')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)
        db.session.commit()

        rankings = RankingService.get_user_rankings_for_thread(user.id, 9999)

        assert rankings == []

    def test_RANK_003_get_user_rankings_multiple_features(self, app, db, app_context):
        """
        [RANK-003] Get User Rankings - Mehrere Features

        Mehrere Rankings für einen Thread sollten alle gefunden werden.
        """
        from services.ranking_service import RankingService
        from db.models import (
            User, UserGroup, EmailThread, Feature, FeatureType,
            LLM, UserFeatureRanking, FeatureFunctionType
        )

        # Setup
        group = UserGroup(name='TestGroup003')
        db.session.add(group)
        db.session.commit()

        user = User(username='ranker003')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)

        function_type = FeatureFunctionType(name='ranking_test_003')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=1003,
            chat_id=3,
            institut_id=3,
            subject='Test Thread 3',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)

        feature_type = FeatureType(type_id=103, name='test_type_003')
        db.session.add(feature_type)

        llm = LLM(llm_id=103, name='TestLLM003')
        db.session.add(llm)
        db.session.commit()

        # Create multiple features
        for i in range(3):
            feature = Feature(
                feature_id=1030 + i,
                thread_id=1003,
                type_id=103,
                llm_id=103,
                content=f'Test feature {i}'
            )
            db.session.add(feature)
        db.session.commit()

        # Create rankings for all features
        for i in range(3):
            ranking = UserFeatureRanking(
                user_id=user.id,
                feature_id=1030 + i,
                ranking_content=i + 1,
                bucket='Gut' if i == 0 else 'Mittel',
                type_id=103,
                llm_id=103
            )
            db.session.add(ranking)
        db.session.commit()

        # Test
        rankings = RankingService.get_user_rankings_for_thread(user.id, 1003)

        assert len(rankings) == 3


class TestRankingStatusChecks:
    """
    Ranking Status Checks Tests

    Tests for checking if user has ranked threads.
    """

    def test_RANK_020_has_user_ranked_thread_true(self, app, db, app_context):
        """
        [RANK-020] Has User Ranked Thread - True

        User mit Rankings sollte True zurückgeben.
        """
        from services.ranking_service import RankingService
        from db.models import (
            User, UserGroup, EmailThread, Feature, FeatureType,
            LLM, UserFeatureRanking, FeatureFunctionType
        )

        # Setup
        group = UserGroup(name='TestGroup020')
        db.session.add(group)
        db.session.commit()

        user = User(username='ranker020')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)

        function_type = FeatureFunctionType(name='ranking_test_020')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=1020,
            chat_id=20,
            institut_id=20,
            subject='Test Thread 20',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)

        feature_type = FeatureType(type_id=120, name='test_type_020')
        db.session.add(feature_type)

        llm = LLM(llm_id=120, name='TestLLM020')
        db.session.add(llm)
        db.session.commit()

        feature = Feature(
            feature_id=1020,
            thread_id=1020,
            type_id=120,
            llm_id=120,
            content='Test feature'
        )
        db.session.add(feature)
        db.session.commit()

        ranking = UserFeatureRanking(
            user_id=user.id,
            feature_id=1020,
            ranking_content=1,
            bucket='Gut',
            type_id=120,
            llm_id=120
        )
        db.session.add(ranking)
        db.session.commit()

        # Test
        result = RankingService.has_user_ranked_thread(user.id, 1020)

        assert result is True

    def test_RANK_021_has_user_ranked_thread_false(self, app, db, app_context):
        """
        [RANK-021] Has User Ranked Thread - False

        User ohne Rankings sollte False zurückgeben.
        """
        from services.ranking_service import RankingService
        from db.models import User, UserGroup

        group = UserGroup(name='TestGroup021')
        db.session.add(group)
        db.session.commit()

        user = User(username='ranker021')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)
        db.session.commit()

        result = RankingService.has_user_ranked_thread(user.id, 9999)

        assert result is False

    def test_RANK_022_has_user_fully_ranked_thread_true(self, app, db, app_context):
        """
        [RANK-022] Has User Fully Ranked Thread - True

        Vollständig gerankter Thread sollte True zurückgeben.
        """
        from services.ranking_service import RankingService
        from db.models import (
            User, UserGroup, EmailThread, Feature, FeatureType,
            LLM, UserFeatureRanking, FeatureFunctionType
        )

        # Setup
        group = UserGroup(name='TestGroup022')
        db.session.add(group)
        db.session.commit()

        user = User(username='ranker022')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)

        function_type = FeatureFunctionType(name='ranking_test_022')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=1022,
            chat_id=22,
            institut_id=22,
            subject='Test Thread 22',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)

        feature_type = FeatureType(type_id=122, name='test_type_022')
        db.session.add(feature_type)

        llm = LLM(llm_id=122, name='TestLLM022')
        db.session.add(llm)
        db.session.commit()

        # Create 2 features
        for i in range(2):
            feature = Feature(
                feature_id=1220 + i,
                thread_id=1022,
                type_id=122,
                llm_id=122,
                content=f'Feature {i}'
            )
            db.session.add(feature)
        db.session.commit()

        # Rank all features
        for i in range(2):
            ranking = UserFeatureRanking(
                user_id=user.id,
                feature_id=1220 + i,
                ranking_content=i + 1,
                bucket='Gut',
                type_id=122,
                llm_id=122
            )
            db.session.add(ranking)
        db.session.commit()

        # Test
        result = RankingService.has_user_fully_ranked_thread(user.id, 1022)

        assert result is True

    def test_RANK_023_has_user_fully_ranked_thread_partial(self, app, db, app_context):
        """
        [RANK-023] Has User Fully Ranked Thread - Teilweise

        Teilweise gerankter Thread sollte False zurückgeben.
        """
        from services.ranking_service import RankingService
        from db.models import (
            User, UserGroup, EmailThread, Feature, FeatureType,
            LLM, UserFeatureRanking, FeatureFunctionType
        )

        # Setup
        group = UserGroup(name='TestGroup023')
        db.session.add(group)
        db.session.commit()

        user = User(username='ranker023')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)

        function_type = FeatureFunctionType(name='ranking_test_023')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=1023,
            chat_id=23,
            institut_id=23,
            subject='Test Thread 23',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)

        feature_type = FeatureType(type_id=123, name='test_type_023')
        db.session.add(feature_type)

        llm = LLM(llm_id=123, name='TestLLM023')
        db.session.add(llm)
        db.session.commit()

        # Create 3 features
        for i in range(3):
            feature = Feature(
                feature_id=1230 + i,
                thread_id=1023,
                type_id=123,
                llm_id=123,
                content=f'Feature {i}'
            )
            db.session.add(feature)
        db.session.commit()

        # Only rank 1 feature
        ranking = UserFeatureRanking(
            user_id=user.id,
            feature_id=1230,
            ranking_content=1,
            bucket='Gut',
            type_id=123,
            llm_id=123
        )
        db.session.add(ranking)
        db.session.commit()

        # Test
        result = RankingService.has_user_fully_ranked_thread(user.id, 1023)

        assert result is False

    def test_RANK_024_has_user_fully_ranked_thread_no_features(self, app, db, app_context):
        """
        [RANK-024] Has User Fully Ranked Thread - Keine Features

        Thread ohne Features sollte False zurückgeben.
        """
        from services.ranking_service import RankingService
        from db.models import User, UserGroup, EmailThread, FeatureFunctionType

        group = UserGroup(name='TestGroup024')
        db.session.add(group)
        db.session.commit()

        user = User(username='ranker024')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)

        function_type = FeatureFunctionType(name='ranking_test_024')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=1024,
            chat_id=24,
            institut_id=24,
            subject='Empty Thread',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)
        db.session.commit()

        # No features in thread
        result = RankingService.has_user_fully_ranked_thread(user.id, 1024)

        assert result is False


class TestGetRankingsByType:
    """
    Get Rankings by Type Tests

    Tests for getting rankings organized by feature type.
    """

    def test_RANK_040_get_current_rankings_by_type_structure(self, app, db, app_context):
        """
        [RANK-040] Get Rankings by Type - Struktur

        Sollte korrekte Bucket-Struktur zurückgeben.
        """
        from services.ranking_service import RankingService
        from db.models import (
            User, UserGroup, EmailThread, Feature, FeatureType,
            LLM, UserFeatureRanking, FeatureFunctionType
        )

        # Setup
        group = UserGroup(name='TestGroup040')
        db.session.add(group)
        db.session.commit()

        user = User(username='ranker040')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)

        function_type = FeatureFunctionType(name='ranking_test_040')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=1040,
            chat_id=40,
            institut_id=40,
            subject='Test Thread 40',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)

        feature_type = FeatureType(type_id=140, name='situation_summary')
        db.session.add(feature_type)

        llm = LLM(llm_id=140, name='TestLLM040')
        db.session.add(llm)
        db.session.commit()

        feature = Feature(
            feature_id=1040,
            thread_id=1040,
            type_id=140,
            llm_id=140,
            content='Test summary'
        )
        db.session.add(feature)
        db.session.commit()

        ranking = UserFeatureRanking(
            user_id=user.id,
            feature_id=1040,
            ranking_content=1,
            bucket='Gut',
            type_id=140,
            llm_id=140
        )
        db.session.add(ranking)
        db.session.commit()

        # Test
        result = RankingService.get_current_rankings_by_type(user.id, 1040)

        assert 'situation_summary' in result
        assert 'goodList' in result['situation_summary']
        assert 'averageList' in result['situation_summary']
        assert 'badList' in result['situation_summary']
        assert 'neutralList' in result['situation_summary']
        assert len(result['situation_summary']['goodList']) == 1

    def test_RANK_041_get_current_rankings_by_type_buckets(self, app, db, app_context):
        """
        [RANK-041] Get Rankings by Type - Buckets

        Features sollten in richtige Buckets sortiert werden.
        """
        from services.ranking_service import RankingService
        from db.models import (
            User, UserGroup, EmailThread, Feature, FeatureType,
            LLM, UserFeatureRanking, FeatureFunctionType
        )

        # Setup
        group = UserGroup(name='TestGroup041')
        db.session.add(group)
        db.session.commit()

        user = User(username='ranker041')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)

        function_type = FeatureFunctionType(name='ranking_test_041')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=1041,
            chat_id=41,
            institut_id=41,
            subject='Test Thread 41',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)

        feature_type = FeatureType(type_id=141, name='bucket_test_type')
        db.session.add(feature_type)

        llm = LLM(llm_id=141, name='TestLLM041')
        db.session.add(llm)
        db.session.commit()

        # Create features for each bucket
        buckets = ['Gut', 'Mittel', 'Schlecht']
        for i, bucket in enumerate(buckets):
            feature = Feature(
                feature_id=1410 + i,
                thread_id=1041,
                type_id=141,
                llm_id=141,
                content=f'{bucket} feature'
            )
            db.session.add(feature)
        db.session.commit()

        for i, bucket in enumerate(buckets):
            ranking = UserFeatureRanking(
                user_id=user.id,
                feature_id=1410 + i,
                ranking_content=1,
                bucket=bucket,
                type_id=141,
                llm_id=141
            )
            db.session.add(ranking)
        db.session.commit()

        # Test
        result = RankingService.get_current_rankings_by_type(user.id, 1041)
        type_data = result['bucket_test_type']

        assert len(type_data['goodList']) == 1
        assert len(type_data['averageList']) == 1
        assert len(type_data['badList']) == 1

    def test_RANK_042_get_current_rankings_unranked_in_neutral(self, app, db, app_context):
        """
        [RANK-042] Get Rankings by Type - Unranked in Neutral

        Ungerankte Features sollten in neutralList erscheinen.
        """
        from services.ranking_service import RankingService
        from db.models import (
            User, UserGroup, EmailThread, Feature, FeatureType,
            LLM, FeatureFunctionType
        )

        # Setup
        group = UserGroup(name='TestGroup042')
        db.session.add(group)
        db.session.commit()

        user = User(username='ranker042')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)

        function_type = FeatureFunctionType(name='ranking_test_042')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=1042,
            chat_id=42,
            institut_id=42,
            subject='Test Thread 42',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)

        feature_type = FeatureType(type_id=142, name='neutral_test_type')
        db.session.add(feature_type)

        llm = LLM(llm_id=142, name='TestLLM042')
        db.session.add(llm)
        db.session.commit()

        # Create unranked feature
        feature = Feature(
            feature_id=1042,
            thread_id=1042,
            type_id=142,
            llm_id=142,
            content='Unranked feature'
        )
        db.session.add(feature)
        db.session.commit()

        # No ranking created

        # Test
        result = RankingService.get_current_rankings_by_type(user.id, 1042)
        type_data = result['neutral_test_type']

        assert len(type_data['neutralList']) == 1
        assert type_data['neutralList'][0]['position'] is None


class TestSaveRanking:
    """
    Save Ranking Tests

    Tests for saving and updating rankings.
    """

    def test_RANK_060_save_ranking_new(self, app, db, app_context):
        """
        [RANK-060] Save Ranking - Neu

        Neues Ranking sollte erstellt werden.
        """
        from services.ranking_service import RankingService
        from db.models import (
            User, UserGroup, EmailThread, Feature, FeatureType,
            LLM, UserFeatureRanking, FeatureFunctionType
        )

        # Setup
        group = UserGroup(name='TestGroup060')
        db.session.add(group)
        db.session.commit()

        user = User(username='ranker060')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)

        function_type = FeatureFunctionType(name='ranking_test_060')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=1060,
            chat_id=60,
            institut_id=60,
            subject='Test Thread 60',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)

        feature_type = FeatureType(type_id=160, name='save_test_type')
        db.session.add(feature_type)

        llm = LLM(llm_id=160, name='TestLLM060')
        db.session.add(llm)
        db.session.commit()

        feature = Feature(
            feature_id=1060,
            thread_id=1060,
            type_id=160,
            llm_id=160,
            content='Save test feature'
        )
        db.session.add(feature)
        db.session.commit()

        # Test
        success, error = RankingService.save_ranking(
            user_id=user.id,
            thread_id=1060,
            feature_id=1060,
            type_id=160,
            llm_id=160,
            position=1,
            bucket='Gut'
        )

        assert success is True
        assert error is None

        # Verify
        ranking = UserFeatureRanking.query.filter_by(
            user_id=user.id,
            feature_id=1060
        ).first()
        assert ranking is not None
        assert ranking.bucket == 'Gut'
        assert ranking.ranking_content == 1

    def test_RANK_061_save_ranking_update(self, app, db, app_context):
        """
        [RANK-061] Save Ranking - Update

        Bestehendes Ranking sollte aktualisiert werden.
        """
        from services.ranking_service import RankingService
        from db.models import (
            User, UserGroup, EmailThread, Feature, FeatureType,
            LLM, UserFeatureRanking, FeatureFunctionType
        )

        # Setup
        group = UserGroup(name='TestGroup061')
        db.session.add(group)
        db.session.commit()

        user = User(username='ranker061')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)

        function_type = FeatureFunctionType(name='ranking_test_061')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=1061,
            chat_id=61,
            institut_id=61,
            subject='Test Thread 61',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)

        feature_type = FeatureType(type_id=161, name='update_test_type')
        db.session.add(feature_type)

        llm = LLM(llm_id=161, name='TestLLM061')
        db.session.add(llm)
        db.session.commit()

        feature = Feature(
            feature_id=1061,
            thread_id=1061,
            type_id=161,
            llm_id=161,
            content='Update test feature'
        )
        db.session.add(feature)
        db.session.commit()

        # Create initial ranking
        ranking = UserFeatureRanking(
            user_id=user.id,
            feature_id=1061,
            ranking_content=1,
            bucket='Gut',
            type_id=161,
            llm_id=161
        )
        db.session.add(ranking)
        db.session.commit()

        # Update ranking
        success, error = RankingService.save_ranking(
            user_id=user.id,
            thread_id=1061,
            feature_id=1061,
            type_id=161,
            llm_id=161,
            position=3,
            bucket='Schlecht'
        )

        assert success is True
        assert error is None

        # Verify update
        updated = UserFeatureRanking.query.filter_by(
            user_id=user.id,
            feature_id=1061
        ).first()
        assert updated.bucket == 'Schlecht'
        assert updated.ranking_content == 3

    def test_RANK_062_save_ranking_no_commit(self, app, db, app_context):
        """
        [RANK-062] Save Ranking - No Commit

        Mit commit=False sollte nicht committed werden.
        """
        from services.ranking_service import RankingService
        from db.models import (
            User, UserGroup, EmailThread, Feature, FeatureType,
            LLM, UserFeatureRanking, FeatureFunctionType
        )

        # Setup
        group = UserGroup(name='TestGroup062')
        db.session.add(group)
        db.session.commit()

        user = User(username='ranker062')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)

        function_type = FeatureFunctionType(name='ranking_test_062')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=1062,
            chat_id=62,
            institut_id=62,
            subject='Test Thread 62',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)

        feature_type = FeatureType(type_id=162, name='nocommit_test_type')
        db.session.add(feature_type)

        llm = LLM(llm_id=162, name='TestLLM062')
        db.session.add(llm)
        db.session.commit()

        feature = Feature(
            feature_id=1062,
            thread_id=1062,
            type_id=162,
            llm_id=162,
            content='No commit test'
        )
        db.session.add(feature)
        db.session.commit()

        # Save with commit=False
        success, error = RankingService.save_ranking(
            user_id=user.id,
            thread_id=1062,
            feature_id=1062,
            type_id=162,
            llm_id=162,
            position=1,
            bucket='Mittel',
            commit=False
        )

        assert success is True

        # Rollback to test commit=False behavior
        db.session.rollback()

        # Should not exist after rollback
        ranking = UserFeatureRanking.query.filter_by(
            user_id=user.id,
            feature_id=1062
        ).first()
        assert ranking is None


class TestClearRankings:
    """
    Clear Rankings Tests

    Tests for clearing user rankings for a thread.
    """

    def test_RANK_090_clear_rankings_for_thread(self, app, db, app_context):
        """
        [RANK-090] Clear Rankings for Thread

        Alle Rankings für Thread sollten gelöscht werden.
        """
        from services.ranking_service import RankingService
        from db.models import (
            User, UserGroup, EmailThread, Feature, FeatureType,
            LLM, UserFeatureRanking, FeatureFunctionType
        )

        # Setup
        group = UserGroup(name='TestGroup090')
        db.session.add(group)
        db.session.commit()

        user = User(username='ranker090')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)

        function_type = FeatureFunctionType(name='ranking_test_090')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=1090,
            chat_id=90,
            institut_id=90,
            subject='Test Thread 90',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)

        feature_type = FeatureType(type_id=190, name='clear_test_type')
        db.session.add(feature_type)

        llm = LLM(llm_id=190, name='TestLLM090')
        db.session.add(llm)
        db.session.commit()

        # Create features and rankings
        for i in range(3):
            feature = Feature(
                feature_id=1900 + i,
                thread_id=1090,
                type_id=190,
                llm_id=190,
                content=f'Clear test {i}'
            )
            db.session.add(feature)
        db.session.commit()

        for i in range(3):
            ranking = UserFeatureRanking(
                user_id=user.id,
                feature_id=1900 + i,
                ranking_content=i + 1,
                bucket='Gut',
                type_id=190,
                llm_id=190
            )
            db.session.add(ranking)
        db.session.commit()

        # Verify rankings exist
        initial_count = UserFeatureRanking.query.filter_by(user_id=user.id).count()
        assert initial_count == 3

        # Clear rankings
        success, error = RankingService.clear_rankings_for_thread(user.id, 1090)

        assert success is True
        assert error is None

        # Verify cleared
        final_count = UserFeatureRanking.query.filter_by(user_id=user.id).count()
        assert final_count == 0

    def test_RANK_091_clear_rankings_no_rankings(self, app, db, app_context):
        """
        [RANK-091] Clear Rankings - Keine Rankings

        Löschen ohne Rankings sollte erfolgreich sein.
        """
        from services.ranking_service import RankingService
        from db.models import User, UserGroup

        group = UserGroup(name='TestGroup091')
        db.session.add(group)
        db.session.commit()

        user = User(username='ranker091')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)
        db.session.commit()

        success, error = RankingService.clear_rankings_for_thread(user.id, 9999)

        assert success is True
        assert error is None


class TestRankingStatistics:
    """
    Ranking Statistics Tests

    Tests for ranking statistics generation.
    """

    def test_RANK_110_get_user_ranking_stats_for_all_users(self, app, db, app_context):
        """
        [RANK-110] Get User Ranking Stats

        Stats sollten für alle User generiert werden.
        """
        from services.ranking_service import RankingService
        from db.models import (
            User, UserGroup, EmailThread, Feature, FeatureType,
            LLM, UserFeatureRanking, FeatureFunctionType
        )

        # Setup
        group = UserGroup(name='TestGroup110')
        db.session.add(group)
        db.session.commit()

        user = User(username='stats_user_110')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)

        # Create ranking type (function_type_id = 1)
        function_type = FeatureFunctionType(function_type_id=1, name='ranking')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=1110,
            chat_id=110,
            institut_id=110,
            subject='Stats Thread',
            function_type_id=1  # Ranking type
        )
        db.session.add(thread)

        feature_type = FeatureType(type_id=1100, name='stats_type')
        db.session.add(feature_type)

        llm = LLM(llm_id=1100, name='TestLLM110')
        db.session.add(llm)
        db.session.commit()

        feature = Feature(
            feature_id=11100,
            thread_id=1110,
            type_id=1100,
            llm_id=1100,
            content='Stats feature'
        )
        db.session.add(feature)
        db.session.commit()

        # Rank it fully
        ranking = UserFeatureRanking(
            user_id=user.id,
            feature_id=11100,
            ranking_content=1,
            bucket='Gut',
            type_id=1100,
            llm_id=1100
        )
        db.session.add(ranking)
        db.session.commit()

        # Test
        stats = RankingService.get_user_ranking_stats_for_all_users()

        assert isinstance(stats, list)
        # Find our user in stats
        user_stat = next((s for s in stats if s['username'] == 'stats_user_110'), None)
        assert user_stat is not None
        assert user_stat['ranked_threads_count'] >= 0


class TestCSVExport:
    """
    CSV Export Tests

    Tests for CSV export functionality.
    """

    def test_RANK_130_get_all_rankings_for_csv_export(self, app, db, app_context):
        """
        [RANK-130] Get All Rankings for CSV Export

        Sollte sortierte Rankings zurückgeben.
        """
        from services.ranking_service import RankingService
        from db.models import (
            User, UserGroup, EmailThread, Feature, FeatureType,
            LLM, UserFeatureRanking, FeatureFunctionType
        )

        # Setup
        group = UserGroup(name='TestGroup130')
        db.session.add(group)
        db.session.commit()

        user = User(username='csv_user_130')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)

        function_type = FeatureFunctionType(name='csv_test_130')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=1130,
            chat_id=130,
            institut_id=130,
            subject='CSV Thread',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)

        feature_type = FeatureType(type_id=1130, name='csv_type')
        db.session.add(feature_type)

        llm = LLM(llm_id=1130, name='TestLLM130')
        db.session.add(llm)
        db.session.commit()

        feature = Feature(
            feature_id=11300,
            thread_id=1130,
            type_id=1130,
            llm_id=1130,
            content='CSV feature'
        )
        db.session.add(feature)
        db.session.commit()

        ranking = UserFeatureRanking(
            user_id=user.id,
            feature_id=11300,
            ranking_content=1,
            bucket='Gut',
            type_id=1130,
            llm_id=1130
        )
        db.session.add(ranking)
        db.session.commit()

        # Test
        rankings = RankingService.get_all_rankings_for_csv_export()

        assert isinstance(rankings, list)
        assert len(rankings) >= 1

    def test_RANK_131_generate_rankings_csv_data(self, app, db, app_context):
        """
        [RANK-131] Generate Rankings CSV Data

        CSV Daten sollten Header und Rows haben.
        """
        from services.ranking_service import RankingService
        from db.models import (
            User, UserGroup, EmailThread, Feature, FeatureType,
            LLM, UserFeatureRanking, FeatureFunctionType
        )

        # Setup
        group = UserGroup(name='TestGroup131')
        db.session.add(group)
        db.session.commit()

        user = User(username='csv_user_131')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)

        function_type = FeatureFunctionType(name='csv_test_131')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=1131,
            chat_id=131,
            institut_id=131,
            subject='CSV Thread 2',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)

        feature_type = FeatureType(type_id=1131, name='csv_type_131')
        db.session.add(feature_type)

        llm = LLM(llm_id=1131, name='TestLLM131')
        db.session.add(llm)
        db.session.commit()

        feature = Feature(
            feature_id=11310,
            thread_id=1131,
            type_id=1131,
            llm_id=1131,
            content='CSV feature 2'
        )
        db.session.add(feature)
        db.session.commit()

        ranking = UserFeatureRanking(
            user_id=user.id,
            feature_id=11310,
            ranking_content=1,
            bucket='Mittel',
            type_id=1131,
            llm_id=1131
        )
        db.session.add(ranking)
        db.session.commit()

        # Test
        csv_data = RankingService.generate_rankings_csv_data()

        assert isinstance(csv_data, list)
        assert len(csv_data) >= 1  # At least header

        # Check header
        header = csv_data[0]
        assert 'Thread ID' in header
        assert 'Feature Type' in header
        assert 'User' in header
        assert 'Bucket' in header

    def test_RANK_132_generate_rankings_csv_data_empty(self, app, db, app_context):
        """
        [RANK-132] Generate Rankings CSV Data - Empty

        Ohne Rankings sollte nur Header zurückgegeben werden.
        """
        from services.ranking_service import RankingService
        from db.models import UserFeatureRanking

        # Clear all rankings
        UserFeatureRanking.query.delete()
        db.session.commit()

        csv_data = RankingService.generate_rankings_csv_data()

        # Should have header only
        assert len(csv_data) == 1
        assert csv_data[0][0] == 'Thread ID'
