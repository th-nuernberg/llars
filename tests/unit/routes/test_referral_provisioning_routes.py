"""Route tests for referral demo-content provisioning (the IJCAI QR link).

Two surfaces, through the real blueprint:
- admin config: POST /api/referral/admin/campaigns/<id>/links and
  PUT /api/referral/admin/links/<id> must round-trip a valid provision_json and
  reject a malformed one with a 400 (the ids are admin-trusted, the SHAPE is not).
- public sign-up: POST /api/referral/register must hand the freshly created
  account the configured prompts/jobs — and must still succeed if that fails.

The redeem counterpart lives in test_referral_redeem_routes.py (REDEEM_013/014).
Test IDs use the PROV_API_ prefix.
"""

from unittest.mock import MagicMock, patch

import pytest


def _grant_admin_referral_permission(rdb):
    """Give the seeded admin role admin:referral:manage.

    The route conftest seeds a generic permission set that predates the referral
    admin API; without this the admin user would 403 before reaching validation.
    """
    from db.models.permission import Permission, Role, RolePermission

    perm = Permission.query.filter_by(permission_key='admin:referral:manage').first()
    if perm is None:
        perm = Permission(
            permission_key='admin:referral:manage',
            display_name='Manage Referrals',
            category='admin',
            description='Manage referral campaigns and links',
        )
        rdb.session.add(perm)
        rdb.session.commit()

    role = Role.query.filter_by(role_name='admin').first()
    existing = RolePermission.query.filter_by(role_id=role.id, permission_id=perm.id).first()
    if existing is None:
        rdb.session.add(RolePermission(role_id=role.id, permission_id=perm.id))
        rdb.session.commit()


def _make_campaign():
    """Active campaign to hang the links off."""
    from services.referral_service import ReferralService
    from db.models.referral import ReferralCampaignStatus

    campaign = ReferralService.create_campaign(name='Admin Link Tests', created_by='admin')
    ReferralService.update_campaign_status(campaign.id, ReferralCampaignStatus.ACTIVE)
    return campaign


class TestAdminLinkProvisionJson:
    """provision_json handling on the admin create/update link endpoints."""

    def test_PROV_API_001_create_link_accepts_provision_json(self, auth_admin, real_app, rdb):
        """[PROV-API-001] A valid config is stored and returned parsed."""
        with real_app.app_context():
            from db.models.referral import ReferralLink

            _grant_admin_referral_permission(rdb)
            campaign = _make_campaign()

            resp = auth_admin.post(
                f'/api/referral/admin/campaigns/{campaign.id}/links',
                json={
                    'role_name': 'ijcai_reviewer',
                    'label': 'IJCAI QR',
                    'provision_json': {'clone_prompt_ids': [1, 2], 'share_job_ids': [3]},
                },
            )

            assert resp.status_code == 201
            body = resp.get_json()
            assert body['link']['role_name'] == 'ijcai_reviewer'
            assert body['link']['provision_json'] == {
                'clone_prompt_ids': [1, 2],
                'share_job_ids': [3],
            }
            stored = ReferralLink.query.get(body['link']['id'])
            assert stored.get_provision_config() == {
                'clone_prompt_ids': [1, 2],
                'share_job_ids': [3],
            }

    def test_PROV_API_002_create_link_without_provision_json(self, auth_admin, real_app, rdb):
        """[PROV-API-002] The field is optional — omitting it leaves the column NULL."""
        with real_app.app_context():
            from db.models.referral import ReferralLink

            _grant_admin_referral_permission(rdb)
            campaign = _make_campaign()

            resp = auth_admin.post(
                f'/api/referral/admin/campaigns/{campaign.id}/links',
                json={'role_name': 'evaluator'},
            )

            assert resp.status_code == 201
            body = resp.get_json()
            assert body['link']['provision_json'] == {}
            assert ReferralLink.query.get(body['link']['id']).provision_json is None

    @pytest.mark.parametrize('bad', [
        [1, 2, 3],
        'totally not json',
        {'evil_key': [1]},
        {'clone_prompt_ids': 'nope'},
        {'share_job_ids': ['3']},
    ])
    def test_PROV_API_003_create_link_rejects_junk(self, bad, auth_admin, real_app, rdb):
        """[PROV-API-003] A malformed config is a 400, not a silently ignored field."""
        with real_app.app_context():
            _grant_admin_referral_permission(rdb)
            campaign = _make_campaign()

            resp = auth_admin.post(
                f'/api/referral/admin/campaigns/{campaign.id}/links',
                json={'role_name': 'evaluator', 'provision_json': bad},
            )

            assert resp.status_code == 400

    def test_PROV_API_004_update_link_sets_and_clears(self, auth_admin, real_app, rdb):
        """[PROV-API-004] PUT sets a config; an explicit null clears it again."""
        with real_app.app_context():
            from db.models.referral import ReferralLink
            from services.referral_service import ReferralService

            _grant_admin_referral_permission(rdb)
            campaign = _make_campaign()
            link = ReferralService.create_link(
                campaign_id=campaign.id, created_by='admin', role_name='evaluator'
            )

            resp = auth_admin.put(
                f'/api/referral/admin/links/{link.id}',
                json={'provision_json': {'share_job_ids': [9]}},
            )
            assert resp.status_code == 200
            assert resp.get_json()['link']['provision_json'] == {'share_job_ids': [9]}

            # Unrelated update must leave the config untouched.
            resp = auth_admin.put(
                f'/api/referral/admin/links/{link.id}', json={'label': 'Renamed'}
            )
            assert resp.status_code == 200
            assert resp.get_json()['link']['provision_json'] == {'share_job_ids': [9]}

            # Explicit null clears it.
            resp = auth_admin.put(
                f'/api/referral/admin/links/{link.id}', json={'provision_json': None}
            )
            assert resp.status_code == 200
            assert resp.get_json()['link']['provision_json'] == {}
            assert ReferralLink.query.get(link.id).provision_json is None

    def test_PROV_API_005_update_link_rejects_junk(self, auth_admin, real_app, rdb):
        """[PROV-API-005] A malformed config on update is a 400 as well."""
        with real_app.app_context():
            from services.referral_service import ReferralService

            _grant_admin_referral_permission(rdb)
            campaign = _make_campaign()
            link = ReferralService.create_link(
                campaign_id=campaign.id, created_by='admin', role_name='evaluator'
            )

            resp = auth_admin.put(
                f'/api/referral/admin/links/{link.id}',
                json={'provision_json': {'clone_prompt_ids': [1], 'nope': [2]}},
            )

            assert resp.status_code == 400

    def test_PROV_API_006_non_admin_cannot_set_provision_json(self, auth_user, real_app, rdb):
        """[PROV-API-006] SECURITY: the endpoint stays gated on admin:referral:manage."""
        with real_app.app_context():
            _grant_admin_referral_permission(rdb)
            campaign = _make_campaign()

            resp = auth_user.post(
                f'/api/referral/admin/campaigns/{campaign.id}/links',
                json={'provision_json': {'clone_prompt_ids': [1]}},
            )

            assert resp.status_code == 403


def _seed_demo_content(rdb):
    """Owner account + one source prompt + one source generation job."""
    from db.models.generation import GenerationJob
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
    return prompt, job


class TestRegisterProvisioning:
    """POST /api/referral/register — the conference QR path."""

    @patch('services.authentik_admin_service.AuthentikAdminService.create_user',
           return_value=(True, None, {}))
    @patch('services.referral_service.get_setting', return_value=True)
    def test_PROV_API_010_register_provisions_demo_content(
        self, _mock_setting, _mock_create, rclient, real_app, rdb
    ):
        """[PROV-API-010] A new registrant gets the prompt cloned + the job shared."""
        with real_app.app_context():
            from db.models.generation import GenerationJobShare
            from db.models.scenario import UserPrompt
            from db.tables import User
            from services.referral_service import ReferralService

            prompt, job = _seed_demo_content(rdb)
            campaign = _make_campaign()
            link = ReferralService.create_link(
                campaign_id=campaign.id,
                created_by='admin',
                role_name='evaluator',
                slug='ijcai-demo-link',
                provision_json={
                    'clone_prompt_ids': [prompt.prompt_id],
                    'share_job_ids': [job.id],
                },
            )

            resp = rclient.post('/api/referral/register', json={
                'code': link.code,
                'username': 'visitor01',
                'password': 'conference2026',
                'email': 'visitor01@example.org',
            })

            assert resp.status_code == 201
            visitor = User.query.filter_by(username='visitor01').first()
            assert visitor is not None
            clone = UserPrompt.query.filter_by(user_id=visitor.id).one()
            assert clone.name == 'Structured Situation Analysis'
            assert clone.prompt_id != prompt.prompt_id
            assert GenerationJobShare.query.filter_by(
                job_id=job.id, shared_with_user_id=visitor.id
            ).count() == 1

    @patch('services.authentik_admin_service.AuthentikAdminService.create_user',
           return_value=(True, None, {}))
    @patch('services.referral_service.get_setting', return_value=True)
    def test_PROV_API_011_register_survives_provisioning_failure(
        self, _mock_setting, _mock_create, rclient, real_app, rdb
    ):
        """[PROV-API-011] A provisioning error must never cost the visitor their account."""
        with real_app.app_context():
            from db.tables import User
            from services.referral_service import ReferralService

            _prompt, job = _seed_demo_content(rdb)
            campaign = _make_campaign()
            link = ReferralService.create_link(
                campaign_id=campaign.id,
                created_by='admin',
                role_name='evaluator',
                slug='ijcai-broken-link',
                provision_json={'share_job_ids': [job.id]},
            )

            with patch('db.models.generation.GenerationJob.query',
                       new_callable=MagicMock) as job_query:
                job_query.get.side_effect = RuntimeError('DB exploded')
                resp = rclient.post('/api/referral/register', json={
                    'code': link.code,
                    'username': 'visitor02',
                    'password': 'conference2026',
                    'email': 'visitor02@example.org',
                })

            assert resp.status_code == 201
            assert User.query.filter_by(username='visitor02').first() is not None
