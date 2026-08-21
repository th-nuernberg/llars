"""
Route Tests for Rating & Ranking API
======================================

Tests for app/routes/rating/ (rating_routes.py, ranking_routes.py, mail_rating_*).
Covers: Rating CRUD, ranking endpoints, feature type mapping, mail rating,
        admin statistics.

Uses real blueprints with mocked OIDC token validation.
Prefix: ROUTE_RATING
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# GET /api/email_threads/ratings (List rating threads)
# ---------------------------------------------------------------------------

class TestListRatingThreads:
    """Tests for GET /api/email_threads/ratings"""

    def test_ROUTE_RATING_LIST_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/email_threads/ratings')
        assert response.status_code == 401

    def test_ROUTE_RATING_LIST_002_authenticated_empty(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/email_threads/ratings')
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) == 0

    def test_ROUTE_RATING_LIST_003_evaluator_access(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/email_threads/ratings')
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)


# ---------------------------------------------------------------------------
# GET /api/email_threads/ratings/<thread_id> (Get thread for rating)
# ---------------------------------------------------------------------------

class TestGetRatingThread:
    """Tests for GET /api/email_threads/ratings/<thread_id>"""

    def test_ROUTE_RATING_GET_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/email_threads/ratings/1')
        assert response.status_code == 401

    @patch('routes.rating.rating_routes.SchemaAdapter.check_scenario_access')
    def test_ROUTE_RATING_GET_002_access_denied(self, mock_access, auth_admin, real_app):
        with real_app.app_context():
            from db.models.scenario import EvaluationItem
            from db.database import db

            item = EvaluationItem(
                chat_id=100,
                subject='Test Subject',
            )
            db.session.add(item)
            db.session.commit()

            mock_access.return_value = None
            response = auth_admin.get(f'/api/email_threads/ratings/{item.item_id}')
            assert response.status_code == 400

    @patch('routes.rating.rating_routes.FeatureRatingService.has_user_fully_rated_thread')
    @patch('routes.rating.rating_routes.FeatureRatingService.get_user_ratings_map_for_thread')
    @patch('routes.rating.rating_routes.SchemaAdapter.check_scenario_access')
    @patch('routes.rating.rating_routes.SchemaAdapter.get_rating_thread_data')
    def test_ROUTE_RATING_GET_003_success(self, mock_data, mock_access,
                                          mock_ratings_map, mock_rated,
                                          auth_admin, real_app):
        with real_app.app_context():
            from db.models.scenario import EvaluationItem
            from db.database import db

            item = EvaluationItem(
                chat_id=100,
                subject='Test Subject',
            )
            db.session.add(item)
            db.session.commit()

            mock_access.return_value = MagicMock()
            mock_data.return_value = {
                'chat_id': 100,
                'subject': 'Test Subject',
                'messages': [],
            }
            mock_rated.return_value = False
            mock_ratings_map.return_value = {}

            response = auth_admin.get(f'/api/email_threads/ratings/{item.item_id}')
            assert response.status_code == 200
            data = response.get_json()
            assert data['chat_id'] == 100


# ---------------------------------------------------------------------------
# GET /api/email_threads/ratings/<thread_id>/<feature_id> (Feature & messages)
# ---------------------------------------------------------------------------

class TestGetFeatureAndMessages:
    """Tests for GET /api/email_threads/ratings/<thread_id>/<feature_id>"""

    def test_ROUTE_RATING_FEAT_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/email_threads/ratings/1/1')
        assert response.status_code == 401

    @patch('routes.rating.rating_routes._check_rating_access')
    def test_ROUTE_RATING_FEAT_002_access_denied(self, mock_check, auth_admin, real_app):
        with real_app.app_context():
            mock_check.return_value = False
            response = auth_admin.get('/api/email_threads/ratings/999/1')
            assert response.status_code == 400

    @patch('routes.rating.rating_routes._check_rating_access')
    def test_ROUTE_RATING_FEAT_003_feature_not_found(self, mock_check, auth_admin, real_app):
        with real_app.app_context():
            mock_check.return_value = True
            response = auth_admin.get('/api/email_threads/ratings/999/999')
            assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/save_rating/<thread_id>/<feature_id> (Save rating)
# ---------------------------------------------------------------------------

class TestSaveRating:
    """Tests for POST /api/save_rating/<thread_id>/<feature_id>"""

    def test_ROUTE_RATING_SAVE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/save_rating/1/1',
                                json={'rating_content': 3, 'edited_feature': 'test'})
        assert response.status_code == 401

    @patch('routes.rating.rating_routes._check_rating_access')
    def test_ROUTE_RATING_SAVE_002_access_denied(self, mock_check, auth_admin, real_app):
        with real_app.app_context():
            mock_check.return_value = False
            response = auth_admin.post('/api/save_rating/999/1',
                                       json={'rating_content': 3, 'edited_feature': 'test'})
            assert response.status_code == 400

    @patch('routes.rating.rating_routes.user_can_evaluate_thread')
    @patch('routes.rating.rating_routes._check_rating_access')
    def test_ROUTE_RATING_SAVE_003_missing_fields(self, mock_check, mock_eval,
                                                   auth_admin, real_app):
        with real_app.app_context():
            mock_check.return_value = True
            mock_eval.return_value = True
            response = auth_admin.post('/api/save_rating/1/1',
                                       json={'rating_content': 3})
            assert response.status_code == 400

    @patch('routes.rating.rating_routes._emit_scenario_stats_updates')
    @patch('routes.rating.rating_routes.user_can_evaluate_thread')
    @patch('routes.rating.rating_routes._check_rating_access')
    def test_ROUTE_RATING_SAVE_004_success(self, mock_check, mock_eval, mock_emit,
                                            auth_admin, real_app):
        with real_app.app_context():
            from db.models.scenario import Feature, FeatureType, EvaluationItem
            from db.database import db

            item = EvaluationItem(
                chat_id=1, subject='s1',
            )
            db.session.add(item)
            db.session.commit()

            ft = FeatureType(name='Summary')
            db.session.add(ft)
            db.session.commit()

            feature = Feature(
                item_id=item.item_id,
                type_id=ft.type_id,
                model_id='test-model',
                content='feature content'
            )
            db.session.add(feature)
            db.session.commit()

            mock_check.return_value = True
            mock_eval.return_value = True

            response = auth_admin.post(
                f'/api/save_rating/{item.item_id}/{feature.feature_id}',
                json={'rating_content': 4, 'edited_feature': 'edited text'}
            )
            assert response.status_code == 201
            data = response.get_json()
            assert data['status'] == 'Rating saved successfully'


# ---------------------------------------------------------------------------
# GET /api/get_rating/<thread_id>/<feature_id> (Get rating)
# ---------------------------------------------------------------------------

class TestGetRating:
    """Tests for GET /api/get_rating/<thread_id>/<feature_id>"""

    def test_ROUTE_RATING_GETONE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/get_rating/1/1')
        assert response.status_code == 401

    @patch('routes.rating.rating_routes._check_rating_access')
    def test_ROUTE_RATING_GETONE_002_not_found(self, mock_check, auth_admin, real_app):
        with real_app.app_context():
            mock_check.return_value = True
            response = auth_admin.get('/api/get_rating/1/999')
            assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/feature_type_mapping (Feature type mapping)
# ---------------------------------------------------------------------------

class TestFeatureTypeMapping:
    """Tests for GET /api/feature_type_mapping"""

    def test_ROUTE_RATING_FTMAP_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/feature_type_mapping')
        assert response.status_code == 401

    def test_ROUTE_RATING_FTMAP_002_no_types(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/feature_type_mapping')
            assert response.status_code == 404

    def test_ROUTE_RATING_FTMAP_003_success(self, auth_admin, real_app):
        with real_app.app_context():
            from db.models.scenario import FeatureType
            from db.database import db

            ft = FeatureType(name='Summary')
            db.session.add(ft)
            db.session.commit()

            response = auth_admin.get('/api/feature_type_mapping')
            assert response.status_code == 200
            data = response.get_json()
            assert 'by_name' in data
            assert 'by_id' in data
            assert 'Summary' in data['by_name']


# ---------------------------------------------------------------------------
# GET /api/feature_type_mapping/<identifier> (Specific feature type)
# ---------------------------------------------------------------------------

class TestFeatureTypeLookup:
    """Tests for GET /api/feature_type_mapping/<identifier>"""

    def test_ROUTE_RATING_FTLOOKUP_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/feature_type_mapping/Summary')
        assert response.status_code == 401

    def test_ROUTE_RATING_FTLOOKUP_002_not_found_by_name(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/feature_type_mapping/Nonexistent')
            assert response.status_code == 404

    def test_ROUTE_RATING_FTLOOKUP_003_not_found_by_id(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/feature_type_mapping/999')
            assert response.status_code == 404

    def test_ROUTE_RATING_FTLOOKUP_004_by_name(self, auth_admin, real_app):
        with real_app.app_context():
            from db.models.scenario import FeatureType
            from db.database import db

            ft = FeatureType(name='Summary')
            db.session.add(ft)
            db.session.commit()

            response = auth_admin.get('/api/feature_type_mapping/Summary')
            assert response.status_code == 200
            data = response.get_json()
            assert 'type_id' in data

    def test_ROUTE_RATING_FTLOOKUP_005_by_id(self, auth_admin, real_app):
        with real_app.app_context():
            from db.models.scenario import FeatureType
            from db.database import db

            ft = FeatureType(name='Summary')
            db.session.add(ft)
            db.session.commit()

            response = auth_admin.get(f'/api/feature_type_mapping/{ft.type_id}')
            assert response.status_code == 200
            data = response.get_json()
            assert data['name'] == 'Summary'


# ---------------------------------------------------------------------------
# GET /api/email_threads/rankings (List ranking threads)
# ---------------------------------------------------------------------------

class TestListRankingThreads:
    """Tests for GET /api/email_threads/rankings"""

    def test_ROUTE_RATING_RANKLIST_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/email_threads/rankings')
        assert response.status_code == 401

    @patch('routes.rating.ranking_routes.FeatureService.get_function_type_by_name')
    def test_ROUTE_RATING_RANKLIST_002_no_function_type(self, mock_ft, auth_admin, real_app):
        with real_app.app_context():
            mock_ft.return_value = None
            response = auth_admin.get('/api/email_threads/rankings')
            assert response.status_code == 404

    @patch('routes.rating.ranking_routes.FeatureService.get_function_type_by_name')
    def test_ROUTE_RATING_RANKLIST_003_empty(self, mock_ft, auth_admin, real_app):
        with real_app.app_context():
            mock_ft.return_value = MagicMock(function_type_id=1)
            response = auth_admin.get('/api/email_threads/rankings')
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)


# ---------------------------------------------------------------------------
# GET /api/email_threads/<thread_id>/current_ranking (Current ranking)
# ---------------------------------------------------------------------------

class TestCurrentRanking:
    """Tests for GET /api/email_threads/<thread_id>/current_ranking"""

    def test_ROUTE_RATING_CURRANK_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/email_threads/1/current_ranking')
        assert response.status_code == 401

    @patch('routes.rating.ranking_routes._check_item_access')
    def test_ROUTE_RATING_CURRANK_002_access_denied(self, mock_check, auth_admin, real_app):
        with real_app.app_context():
            mock_check.return_value = False
            response = auth_admin.get('/api/email_threads/1/current_ranking')
            assert response.status_code == 400

    @patch('routes.rating.ranking_routes.RankingService.get_current_rankings_by_type')
    @patch('routes.rating.ranking_routes._check_item_access')
    def test_ROUTE_RATING_CURRANK_003_success(self, mock_check, mock_rankings,
                                               auth_admin, real_app):
        with real_app.app_context():
            mock_check.return_value = True
            mock_rankings.return_value = {}
            response = auth_admin.get('/api/email_threads/1/current_ranking')
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)


# ---------------------------------------------------------------------------
# POST /api/save_ranking/<thread_id> (Save ranking)
# ---------------------------------------------------------------------------

class TestSaveRanking:
    """Tests for POST /api/save_ranking/<thread_id>"""

    def test_ROUTE_RATING_SAVERANK_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/save_ranking/1', json=[])
        assert response.status_code == 401

    @patch('routes.rating.ranking_routes._check_item_access')
    def test_ROUTE_RATING_SAVERANK_002_access_denied(self, mock_check, auth_admin, real_app):
        with real_app.app_context():
            mock_check.return_value = False
            response = auth_admin.post('/api/save_ranking/1', json=[])
            assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/admin/user_ranking_stats (Admin ranking stats)
# ---------------------------------------------------------------------------

class TestAdminRankingStats:
    """Tests for GET /api/admin/user_ranking_stats"""

    def test_ROUTE_RATING_ADMSTATS_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/admin/user_ranking_stats')
        assert response.status_code == 401

    def test_ROUTE_RATING_ADMSTATS_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/admin/user_ranking_stats')
            assert response.status_code == 403

    @patch('routes.rating.ranking_routes.RankingService.get_user_ranking_stats_for_all_users')
    def test_ROUTE_RATING_ADMSTATS_003_admin_success(self, mock_stats, auth_admin, real_app):
        with real_app.app_context():
            mock_stats.return_value = [
                {'username': 'admin', 'total_ranked': 5, 'total_threads': 10}
            ]
            response = auth_admin.get('/api/admin/user_ranking_stats')
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)


# ---------------------------------------------------------------------------
# GET /api/email_threads/mailhistory_ratings (Mail rating threads)
# ---------------------------------------------------------------------------

class TestListMailRatingThreads:
    """Tests for GET /api/email_threads/mailhistory_ratings"""

    def test_ROUTE_RATING_MAILLIST_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/email_threads/mailhistory_ratings')
        assert response.status_code == 401

    def test_ROUTE_RATING_MAILLIST_002_authenticated_empty(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/email_threads/mailhistory_ratings')
            assert response.status_code == 200
            data = response.get_json()
            assert 'threads' in data
            assert isinstance(data['threads'], list)


# ---------------------------------------------------------------------------
# GET /api/admin/user_HistoryGeneration_stats (Admin mail rating stats)
# ---------------------------------------------------------------------------

class TestAdminMailRatingStats:
    """Tests for GET /api/admin/user_HistoryGeneration_stats"""

    def test_ROUTE_RATING_ADMMAIL_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/admin/user_HistoryGeneration_stats')
        assert response.status_code == 401

    def test_ROUTE_RATING_ADMMAIL_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/admin/user_HistoryGeneration_stats')
            assert response.status_code == 403
