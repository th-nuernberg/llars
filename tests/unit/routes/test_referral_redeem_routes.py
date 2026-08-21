"""Route tests for POST /api/referral/redeem.

Exercises the authenticated redeem flow end-to-end through the real blueprint:
auth → validate_link → enroll → provision → attribute. Verifies idempotency and
that an existing user's scenario role is never downgraded by redeeming a code.
"""

from unittest.mock import MagicMock, patch

import pytest


def _make_campaign_with_link(target_scenario_id=None, role_name='evaluator',
                             slug=None, active=True, provision_json=None):
    """Create an active campaign + link directly via the service."""
    from services.referral_service import ReferralService
    from db.models.referral import ReferralCampaignStatus

    campaign = ReferralService.create_campaign(name='Redeem Test', created_by='admin')
    ReferralService.update_campaign_status(campaign.id, ReferralCampaignStatus.ACTIVE)
    link = ReferralService.create_link(
        campaign_id=campaign.id,
        created_by='admin',
        role_name=role_name,
        slug=slug,
        target_scenario_id=target_scenario_id,
        provision_json=provision_json,
    )
    if not active:
        ReferralService.deactivate_link(link.id)
    return campaign, link


def _make_scenario(rdb):
    from db.models.scenario import RatingScenarios
    sc = RatingScenarios(scenario_name='Study', function_type_id=3, created_by='admin')
    rdb.session.add(sc)
    rdb.session.commit()
    rdb.session.refresh(sc)
    return sc


class TestRedeemReferral:
    """Tests for POST /api/referral/redeem (authenticated)."""

    def test_REDEEM_001_unauthenticated(self, rclient, rdb, rmock_token):
        resp = rclient.post('/api/referral/redeem', json={'code': 'anything'})
        assert resp.status_code == 401

    @patch('services.referral_service.get_setting', return_value=True)
    def test_REDEEM_002_valid_code_enrolls_and_attributes(
        self, _mock_setting, auth_user, real_app, rdb
    ):
        with real_app.app_context():
            from db.models.scenario import ScenarioUsers, MembershipStatus
            from db.models.referral import ReferralRegistration
            from db.tables import User

            scenario = _make_scenario(rdb)
            _campaign, link = _make_campaign_with_link(target_scenario_id=scenario.id)

            resp = auth_user.post('/api/referral/redeem', json={'code': link.code})
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['success'] is True
            assert data['target_scenario_id'] == scenario.id
            assert data['already_enrolled'] is False

            user = User.query.filter_by(username='testuser').first()
            row = ScenarioUsers.query.filter_by(
                scenario_id=scenario.id, user_id=user.id
            ).first()
            assert row is not None
            assert row.evaluation_role == 'assessor'
            assert row.membership_status == MembershipStatus.ACTIVE
            assert ReferralRegistration.query.filter_by(username='testuser').count() == 1

    @patch('services.referral_service.get_setting', return_value=True)
    def test_REDEEM_003_by_slug(self, _mock_setting, auth_user, real_app, rdb):
        with real_app.app_context():
            scenario = _make_scenario(rdb)
            _campaign, link = _make_campaign_with_link(
                target_scenario_id=scenario.id, slug='kann-ki-beratung-test'
            )
            resp = auth_user.post(
                '/api/referral/redeem', json={'code': 'kann-ki-beratung-test'}
            )
            assert resp.status_code == 200
            assert resp.get_json()['target_scenario_id'] == scenario.id

    @patch('services.referral_service.get_setting', return_value=True)
    def test_REDEEM_004_idempotent(self, _mock_setting, auth_user, real_app, rdb):
        with real_app.app_context():
            from db.models.scenario import ScenarioUsers
            from db.tables import User

            scenario = _make_scenario(rdb)
            _campaign, link = _make_campaign_with_link(target_scenario_id=scenario.id)

            first = auth_user.post('/api/referral/redeem', json={'code': link.code})
            second = auth_user.post('/api/referral/redeem', json={'code': link.code})
            assert first.status_code == 200
            assert second.status_code == 200
            assert second.get_json()['already_enrolled'] is True

            user = User.query.filter_by(username='testuser').first()
            assert ScenarioUsers.query.filter_by(
                scenario_id=scenario.id, user_id=user.id
            ).count() == 1

    @patch('services.referral_service.get_setting', return_value=True)
    def test_REDEEM_005_invalid_code_404(self, _mock_setting, auth_user, real_app, rdb):
        with real_app.app_context():
            resp = auth_user.post(
                '/api/referral/redeem', json={'code': 'does-not-exist'}
            )
            assert resp.status_code == 404

    @patch('services.referral_service.get_setting', return_value=True)
    def test_REDEEM_006_inactive_link_400(self, _mock_setting, auth_user, real_app, rdb):
        with real_app.app_context():
            _campaign, link = _make_campaign_with_link(active=False)
            resp = auth_user.post('/api/referral/redeem', json={'code': link.code})
            assert resp.status_code == 400

    def test_REDEEM_007_missing_code_400(self, auth_user, real_app, rdb):
        with real_app.app_context():
            resp = auth_user.post('/api/referral/redeem', json={})
            assert resp.status_code == 400

    @patch('services.referral_service.get_setting', return_value=True)
    def test_REDEEM_008_existing_role_not_downgraded(
        self, _mock_setting, auth_researcher, real_app, rdb
    ):
        """A researcher who already owns the scenario keeps OWNER on redeem."""
        with real_app.app_context():
            from db.models.scenario import (
                ScenarioUsers, MembershipStatus, ScenarioRoles,
            )
            from db.tables import User

            scenario = _make_scenario(rdb)
            user = User.query.filter_by(username='researcher').first()
            pre = ScenarioUsers(
                scenario_id=scenario.id, user_id=user.id,
                manager_role='owner', evaluation_role='none',
                is_viewer=False, is_assessor=False,
                membership_status=MembershipStatus.ACTIVE, role=ScenarioRoles.OWNER,
            )
            rdb.session.add(pre)
            rdb.session.commit()

            _campaign, link = _make_campaign_with_link(target_scenario_id=scenario.id)
            resp = auth_researcher.post('/api/referral/redeem', json={'code': link.code})
            assert resp.status_code == 200
            assert resp.get_json()['already_enrolled'] is True

            row = ScenarioUsers.query.filter_by(
                scenario_id=scenario.id, user_id=user.id
            ).first()
            assert row.manager_role == 'owner'  # NOT downgraded
            assert row.evaluation_role == 'none'

    # ----- Study welcome mail on first enroll (parity with /register) -----

    @patch('services.email_service.send_link_welcome')
    @patch('services.authentik_admin_service.AuthentikAdminService.find_user')
    @patch('services.referral_service.get_setting', return_value=True)
    def test_REDEEM_009_welcome_mail_sent_when_email_on_file(
        self, _mock_setting, mock_find_user, mock_send, auth_user, real_app, rdb
    ):
        """First enroll with an email on file → the per-link welcome mail is
        sent with the same username/scenario payload as the /register flow
        (send_link_welcome routes standard/kkb/custom by link.welcome_template)."""
        mock_find_user.return_value = {
            'username': 'testuser', 'email': 'testuser@example.org',
        }
        with real_app.app_context():
            scenario = _make_scenario(rdb)
            _campaign, link = _make_campaign_with_link(target_scenario_id=scenario.id)

            resp = auth_user.post('/api/referral/redeem', json={'code': link.code})
            assert resp.status_code == 200
            assert resp.get_json()['already_enrolled'] is False

            mock_send.assert_called_once()
            kwargs = mock_send.call_args.kwargs
            assert kwargs['username'] == 'testuser'
            assert kwargs['email'] == 'testuser@example.org'
            assert kwargs['scenario_id'] == scenario.id
            assert kwargs['link'].id == link.id

    @patch('services.email_service.send_link_welcome')
    @patch('services.authentik_admin_service.AuthentikAdminService.find_user')
    @patch('services.referral_service.get_setting', return_value=True)
    def test_REDEEM_010_no_welcome_mail_when_no_email(
        self, _mock_setting, mock_find_user, mock_send, auth_user, real_app, rdb
    ):
        """Email-less user (no address in Authentik) → no welcome mail queued."""
        mock_find_user.return_value = {'username': 'testuser', 'email': ''}
        with real_app.app_context():
            scenario = _make_scenario(rdb)
            _campaign, link = _make_campaign_with_link(target_scenario_id=scenario.id)

            resp = auth_user.post('/api/referral/redeem', json={'code': link.code})
            assert resp.status_code == 200
            mock_send.assert_not_called()

    @patch('services.email_service.send_registration_confirmation')
    @patch('services.authentik_admin_service.AuthentikAdminService.find_user')
    @patch('services.referral_service.get_setting', return_value=True)
    def test_REDEEM_011_no_resend_on_repeat_redeem(
        self, _mock_setting, mock_find_user, mock_send, auth_user, real_app, rdb
    ):
        """Repeat redeem (already enrolled) must NOT resend the welcome mail."""
        mock_find_user.return_value = {
            'username': 'testuser', 'email': 'testuser@example.org',
        }
        with real_app.app_context():
            scenario = _make_scenario(rdb)
            _campaign, link = _make_campaign_with_link(target_scenario_id=scenario.id)

            auth_user.post('/api/referral/redeem', json={'code': link.code})
            mock_send.reset_mock()
            # Second redeem: already a member → already_enrolled True, no mail.
            second = auth_user.post('/api/referral/redeem', json={'code': link.code})
            assert second.status_code == 200
            assert second.get_json()['already_enrolled'] is True
            mock_send.assert_not_called()

    @patch('services.email_service.send_registration_confirmation',
           side_effect=RuntimeError('SMTP down'))
    @patch('services.authentik_admin_service.AuthentikAdminService.find_user')
    @patch('services.referral_service.get_setting', return_value=True)
    def test_REDEEM_012_mail_failure_does_not_fail_redeem(
        self, _mock_setting, mock_find_user, _mock_send, auth_user, real_app, rdb
    ):
        """A welcome-mail exception is best-effort and must NOT fail redeem."""
        mock_find_user.return_value = {
            'username': 'testuser', 'email': 'testuser@example.org',
        }
        with real_app.app_context():
            from db.models.scenario import ScenarioUsers
            from db.tables import User

            scenario = _make_scenario(rdb)
            _campaign, link = _make_campaign_with_link(target_scenario_id=scenario.id)

            resp = auth_user.post('/api/referral/redeem', json={'code': link.code})
            # Redeem still succeeds; enrollment still happened.
            assert resp.status_code == 200
            assert resp.get_json()['target_scenario_id'] == scenario.id
            user = User.query.filter_by(username='testuser').first()
            assert ScenarioUsers.query.filter_by(
                scenario_id=scenario.id, user_id=user.id
            ).count() == 1

    @patch('services.referral_service.get_setting', return_value=True)
    def test_REDEEM_013_provisions_demo_content(
        self, _mock_setting, auth_user, real_app, rdb
    ):
        """A demo link's provision_json is applied on redeem (clone + share)."""
        with real_app.app_context():
            from db.models.generation import GenerationJob, GenerationJobShare
            from db.models.scenario import UserPrompt
            from db.tables import User

            owner = User(username='ijcai_demo', password_hash='x',
                         api_key='key-ijcai-demo', is_active=True)
            rdb.session.add(owner)
            rdb.session.commit()

            prompt = UserPrompt(
                user_id=owner.id,
                name='Structured Situation Analysis',
                content={'blocks': [{'id': 'b1', 'text': 'Analyse {{content}}'}]},
            )
            job = GenerationJob(
                name='Counselling Case Analysis',
                config_json={'mode': 'matrix'},
                created_by='ijcai_demo',
            )
            rdb.session.add_all([prompt, job])
            rdb.session.commit()

            _campaign, link = _make_campaign_with_link(provision_json={
                'clone_prompt_ids': [prompt.prompt_id],
                'share_job_ids': [job.id],
            })

            resp = auth_user.post('/api/referral/redeem', json={'code': link.code})
            assert resp.status_code == 200

            user = User.query.filter_by(username='testuser').first()
            clone = UserPrompt.query.filter_by(user_id=user.id).one()
            assert clone.name == 'Structured Situation Analysis'
            assert GenerationJobShare.query.filter_by(
                job_id=job.id, shared_with_user_id=user.id
            ).count() == 1

    @patch('services.referral_service.get_setting', return_value=True)
    def test_REDEEM_014_provisioning_failure_does_not_fail_redeem(
        self, _mock_setting, auth_user, real_app, rdb
    ):
        """A provisioning error is swallowed — the redeem itself still succeeds."""
        with real_app.app_context():
            from db.models.scenario import ScenarioUsers
            from db.tables import User

            scenario = _make_scenario(rdb)
            _campaign, link = _make_campaign_with_link(
                target_scenario_id=scenario.id,
                provision_json={'share_job_ids': [1]},
            )

            with patch('db.models.generation.GenerationJob.query',
                       new_callable=MagicMock) as job_query:
                job_query.get.side_effect = RuntimeError('DB exploded')
                resp = auth_user.post('/api/referral/redeem', json={'code': link.code})

            assert resp.status_code == 200
            user = User.query.filter_by(username='testuser').first()
            assert ScenarioUsers.query.filter_by(
                scenario_id=scenario.id, user_id=user.id
            ).count() == 1
