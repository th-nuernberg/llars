"""
Unit tests for ReferralService.provision_demo_content + the provision_json contract.

Covers the WP1 backend provisioning of the IJCAI conference demo link:
a registrant gets curated prompts CLONED into their account and pre-built batch
generation jobs SHARED read-only, driven by referral_links.provision_json.

Test IDs use the PROV_ prefix (referral demo provisioning).
"""

import json
from unittest.mock import MagicMock, patch

import pytest

# Imported at module level so the generation tables are registered with the
# SQLAlchemy metadata BEFORE the `db` fixture runs create_all() — the parent
# conftest only imports the core model modules.
from db.models.generation import GenerationJob, GenerationJobShare  # noqa: F401


def _make_user(db, username):
    """Create a plain active user (mirrors the helper in test_referral_service)."""
    from db.tables import User
    user = User(
        username=username,
        password_hash='x',
        api_key=f'key-{username}',
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()
    db.session.refresh(user)
    return user


def _make_link(provision_json=None, role_name='evaluator'):
    """Create a campaign + link, optionally carrying a provisioning config."""
    from services.referral_service import ReferralService
    campaign = ReferralService.create_campaign(name='Provisioning', created_by='admin')
    return ReferralService.create_link(
        campaign_id=campaign.id,
        created_by='admin',
        role_name=role_name,
        provision_json=provision_json,
    )


def _make_prompt(db, owner_id, name='Structured Situation Analysis'):
    """Create a source UserPrompt owned by the demo account."""
    from db.models.scenario import UserPrompt
    prompt = UserPrompt(
        user_id=owner_id,
        name=name,
        content={
            'blocks': [{'id': 'b1', 'text': 'Analyse {{content}}', 'author': 'ijcai_demo'}],
            'collaboration_attribution': ['ijcai_demo'],
        },
        rendered_content={'blocks': [{'id': 'b1', 'text': 'Analyse {{content}}'}]},
    )
    db.session.add(prompt)
    db.session.commit()
    db.session.refresh(prompt)
    return prompt


def _make_job(db, created_by='ijcai_demo', name='Counselling Case Analysis'):
    """Create a source GenerationJob owned by the demo account."""
    job = GenerationJob(
        name=name,
        config_json={'mode': 'matrix'},
        created_by=created_by,
    )
    db.session.add(job)
    db.session.commit()
    db.session.refresh(job)
    return job


class TestProvisionClonePrompts:
    """clone_prompt_ids: every registrant gets an own editable copy."""

    def test_PROV_001_clones_prompt_into_target_account(self, app, db, app_context):
        """[PROV-001] Source prompt is copied to the registrant, name preserved."""
        from services.referral_service import ReferralService
        from db.models.scenario import UserPrompt

        owner = _make_user(db, 'ijcai_demo')
        visitor = _make_user(db, 'demo-ijcai-1')
        source = _make_prompt(db, owner.id)
        link = _make_link({'clone_prompt_ids': [source.prompt_id]})

        summary = ReferralService.provision_demo_content(visitor, link)

        assert summary['prompts_cloned'] == 1
        assert summary['errors'] == 0
        clone = UserPrompt.query.filter_by(user_id=visitor.id).one()
        assert clone.prompt_id != source.prompt_id
        assert clone.name == source.name
        assert clone.content == source.content
        assert clone.rendered_content == source.rendered_content

    def test_PROV_002_clone_content_is_deep_copied(self, app, db, app_context):
        """[PROV-002] Editing the clone must not mutate the shared source prompt."""
        from services.referral_service import ReferralService
        from db.models.scenario import UserPrompt

        owner = _make_user(db, 'ijcai_demo')
        visitor = _make_user(db, 'demo-ijcai-2')
        source = _make_prompt(db, owner.id)
        link = _make_link({'clone_prompt_ids': [source.prompt_id]})

        ReferralService.provision_demo_content(visitor, link)

        clone = UserPrompt.query.filter_by(user_id=visitor.id).one()
        clone.content['blocks'][0]['text'] = 'visitor edit'
        assert source.content['blocks'][0]['text'] == 'Analyse {{content}}'

    def test_PROV_003_clone_keeps_attribution_fields(self, app, db, app_context):
        """[PROV-003] collaboration_attribution / block author credit the original."""
        from services.referral_service import ReferralService
        from db.models.scenario import UserPrompt

        owner = _make_user(db, 'ijcai_demo')
        visitor = _make_user(db, 'demo-ijcai-3')
        source = _make_prompt(db, owner.id)
        link = _make_link({'clone_prompt_ids': [source.prompt_id]})

        ReferralService.provision_demo_content(visitor, link)

        clone = UserPrompt.query.filter_by(user_id=visitor.id).one()
        assert clone.content['collaboration_attribution'] == ['ijcai_demo']
        assert clone.content['blocks'][0]['author'] == 'ijcai_demo'

    def test_PROV_004_clone_is_idempotent_by_name(self, app, db, app_context):
        """[PROV-004] Running twice (register + redeem) creates exactly one copy."""
        from services.referral_service import ReferralService
        from db.models.scenario import UserPrompt

        owner = _make_user(db, 'ijcai_demo')
        visitor = _make_user(db, 'demo-ijcai-4')
        source = _make_prompt(db, owner.id)
        link = _make_link({'clone_prompt_ids': [source.prompt_id]})

        ReferralService.provision_demo_content(visitor, link)
        second = ReferralService.provision_demo_content(visitor, link)

        assert second['prompts_cloned'] == 0
        assert second['prompts_skipped'] == 1
        assert UserPrompt.query.filter_by(user_id=visitor.id).count() == 1

    def test_PROV_005_existing_same_name_prompt_is_not_overwritten(self, app, db, app_context):
        """[PROV-005] A prompt the user already edited under that name stays untouched."""
        from services.referral_service import ReferralService
        from db.models.scenario import UserPrompt

        owner = _make_user(db, 'ijcai_demo')
        visitor = _make_user(db, 'demo-ijcai-5')
        source = _make_prompt(db, owner.id)
        own = UserPrompt(
            user_id=visitor.id,
            name=source.name,
            content={'blocks': [{'id': 'b1', 'text': 'my own version'}]},
        )
        db.session.add(own)
        db.session.commit()
        link = _make_link({'clone_prompt_ids': [source.prompt_id]})

        summary = ReferralService.provision_demo_content(visitor, link)

        assert summary['prompts_cloned'] == 0
        assert summary['prompts_skipped'] == 1
        kept = UserPrompt.query.filter_by(user_id=visitor.id).one()
        assert kept.content['blocks'][0]['text'] == 'my own version'

    def test_PROV_006_unknown_prompt_id_is_skipped(self, app, db, app_context):
        """[PROV-006] A deleted/unknown source id is skipped, never raised."""
        from services.referral_service import ReferralService
        from db.models.scenario import UserPrompt

        visitor = _make_user(db, 'demo-ijcai-6')
        link = _make_link({'clone_prompt_ids': [999999]})

        summary = ReferralService.provision_demo_content(visitor, link)

        assert summary['prompts_cloned'] == 0
        assert summary['prompts_skipped'] == 1
        assert summary['errors'] == 0
        assert UserPrompt.query.filter_by(user_id=visitor.id).count() == 0


class TestProvisionShareJobs:
    """share_job_ids: read-only access to pre-built batch generations."""

    def test_PROV_010_shares_job_with_registrant(self, app, db, app_context):
        """[PROV-010] A GenerationJobShare row is created for the registrant."""
        from services.referral_service import ReferralService

        _make_user(db, 'ijcai_demo')
        visitor = _make_user(db, 'demo-ijcai-10')
        job = _make_job(db)
        link = _make_link({'share_job_ids': [job.id]})

        summary = ReferralService.provision_demo_content(visitor, link)

        assert summary['jobs_shared'] == 1
        assert summary['errors'] == 0
        share = GenerationJobShare.query.filter_by(
            job_id=job.id, shared_with_user_id=visitor.id
        ).one()
        assert share.id is not None

    def test_PROV_011_share_is_idempotent(self, app, db, app_context):
        """[PROV-011] A repeat run does not create a duplicate share row."""
        from services.referral_service import ReferralService

        _make_user(db, 'ijcai_demo')
        visitor = _make_user(db, 'demo-ijcai-11')
        job = _make_job(db)
        link = _make_link({'share_job_ids': [job.id]})

        ReferralService.provision_demo_content(visitor, link)
        second = ReferralService.provision_demo_content(visitor, link)

        assert second['jobs_shared'] == 0
        assert second['jobs_skipped'] == 1
        assert GenerationJobShare.query.filter_by(job_id=job.id).count() == 1

    def test_PROV_012_job_owner_is_skipped(self, app, db, app_context):
        """[PROV-012] Sharing a job with its own creator is a no-op."""
        from services.referral_service import ReferralService

        owner = _make_user(db, 'ijcai_demo')
        job = _make_job(db, created_by=owner.username)
        link = _make_link({'share_job_ids': [job.id]})

        summary = ReferralService.provision_demo_content(owner, link)

        assert summary['jobs_shared'] == 0
        assert summary['jobs_skipped'] == 1
        assert GenerationJobShare.query.count() == 0

    def test_PROV_013_unknown_job_id_is_skipped(self, app, db, app_context):
        """[PROV-013] An unknown job id is skipped without an exception."""
        from services.referral_service import ReferralService

        visitor = _make_user(db, 'demo-ijcai-13')
        link = _make_link({'share_job_ids': [424242]})

        summary = ReferralService.provision_demo_content(visitor, link)

        assert summary['jobs_shared'] == 0
        assert summary['jobs_skipped'] == 1
        assert summary['errors'] == 0
        assert GenerationJobShare.query.count() == 0

    def test_PROV_014_clone_and_share_in_one_pass(self, app, db, app_context):
        """[PROV-014] Both lists are applied in a single provisioning run."""
        from services.referral_service import ReferralService
        from db.models.scenario import UserPrompt

        owner = _make_user(db, 'ijcai_demo')
        visitor = _make_user(db, 'demo-ijcai-14')
        prompt = _make_prompt(db, owner.id)
        job = _make_job(db)
        link = _make_link({
            'clone_prompt_ids': [prompt.prompt_id],
            'share_job_ids': [job.id],
        })

        summary = ReferralService.provision_demo_content(visitor, link)

        assert summary['prompts_cloned'] == 1
        assert summary['jobs_shared'] == 1
        assert UserPrompt.query.filter_by(user_id=visitor.id).count() == 1
        assert GenerationJobShare.query.filter_by(shared_with_user_id=visitor.id).count() == 1


class TestProvisionDefensiveBehaviour:
    """Provisioning must NEVER break registration (visitor at a conference booth)."""

    def test_PROV_020_no_provision_json_is_noop(self, app, db, app_context):
        """[PROV-020] A plain link (NULL provision_json) provisions nothing."""
        from services.referral_service import ReferralService

        visitor = _make_user(db, 'demo-ijcai-20')
        link = _make_link()

        summary = ReferralService.provision_demo_content(visitor, link)

        assert summary == {
            'prompts_cloned': 0, 'prompts_skipped': 0,
            'jobs_shared': 0, 'jobs_skipped': 0, 'errors': 0,
        }

    @pytest.mark.parametrize('raw', ['', '   ', 'not json at all', '{"broken": ', '[1, 2, 3]', '"nope"'])
    def test_PROV_021_invalid_provision_json_is_noop(self, raw, app, db, app_context):
        """[PROV-021] Garbage in the column → warn + provision nothing, no exception."""
        from services.referral_service import ReferralService
        from db.models.scenario import UserPrompt

        visitor = _make_user(db, 'demo-ijcai-21')
        link = _make_link()
        # Bypass the API validation: simulate a hand-edited / legacy DB row.
        link.provision_json = raw
        db.session.commit()

        summary = ReferralService.provision_demo_content(visitor, link)

        assert summary['prompts_cloned'] == 0
        assert summary['jobs_shared'] == 0
        assert summary['errors'] == 0
        assert UserPrompt.query.filter_by(user_id=visitor.id).count() == 0

    def test_PROV_022_unexpected_exception_is_swallowed(self, app, db, app_context):
        """[PROV-022] Any unexpected error is logged, counted, and never re-raised."""
        from services.referral_service import ReferralService

        visitor = _make_user(db, 'demo-ijcai-22')
        link = _make_link({'share_job_ids': [1]})

        with patch('db.models.generation.GenerationJob.query', new_callable=MagicMock) as q:
            q.get.side_effect = RuntimeError('DB exploded')
            summary = ReferralService.provision_demo_content(visitor, link)

        assert summary['errors'] == 1
        assert summary['jobs_shared'] == 0


class TestProvisionJsonValidation:
    """_normalize_provision_json: admin input is validated, junk is a 400."""

    def test_PROV_030_valid_config_is_stored_as_json_text(self, app, db, app_context):
        """[PROV-030] create_link stores the normalized config as JSON text."""
        link = _make_link({'clone_prompt_ids': [1, 2], 'share_job_ids': [3]})

        assert json.loads(link.provision_json) == {
            'clone_prompt_ids': [1, 2],
            'share_job_ids': [3],
        }
        assert link.to_dict()['provision_json'] == {
            'clone_prompt_ids': [1, 2],
            'share_job_ids': [3],
        }

    def test_PROV_031_json_string_input_is_accepted(self, app, db, app_context):
        """[PROV-031] The same object may be passed as a JSON string."""
        link = _make_link('{"share_job_ids": [7]}')

        assert json.loads(link.provision_json) == {'share_job_ids': [7]}

    def test_PROV_032_empty_config_stores_null(self, app, db, app_context):
        """[PROV-032] {} / empty lists mean 'provision nothing' → NULL column."""
        assert _make_link({}).provision_json is None
        assert _make_link({'clone_prompt_ids': []}).provision_json is None

    @pytest.mark.parametrize('bad', [
        [1, 2, 3],                                # not an object
        'totally not json',                       # unparseable string
        {'evil_key': [1]},                        # unknown key
        {'clone_prompt_ids': 'nope'},             # not a list
        {'clone_prompt_ids': ['1']},              # not ints
        {'share_job_ids': [True]},                # bool is not an id
        {'share_job_ids': [1.5]},                 # float is not an id
    ])
    def test_PROV_033_invalid_config_raises_validation_error(self, bad, app, db, app_context):
        """[PROV-033] Anything outside the contract is rejected (→ HTTP 400)."""
        from decorators.error_handler import ValidationError

        with pytest.raises(ValidationError):
            _make_link(bad)

    def test_PROV_034_update_link_sets_and_clears_config(self, app, db, app_context):
        """[PROV-034] update_link: absent = unchanged, {} = clear."""
        from services.referral_service import ReferralService

        link = _make_link({'share_job_ids': [5]})

        unchanged = ReferralService.update_link(link.id, label='Still provisioning')
        assert json.loads(unchanged.provision_json) == {'share_job_ids': [5]}

        replaced = ReferralService.update_link(link.id, provision_json={'share_job_ids': [6]})
        assert json.loads(replaced.provision_json) == {'share_job_ids': [6]}

        cleared = ReferralService.update_link(link.id, provision_json={})
        assert cleared.provision_json is None

    def test_PROV_035_update_link_rejects_junk(self, app, db, app_context):
        """[PROV-035] An update with a malformed config is rejected too."""
        from services.referral_service import ReferralService
        from decorators.error_handler import ValidationError

        link = _make_link()
        with pytest.raises(ValidationError):
            ReferralService.update_link(link.id, provision_json={'oops': [1]})


class TestReferralRoleAllowlist:
    """ijcai_reviewer must be grantable by a public link; admin must not."""

    def test_PROV_040_ijcai_reviewer_is_allowlisted(self, app, db, app_context):
        """[PROV-040] The demo role passes the referral role validator."""
        from services.referral_service import (
            ALLOWED_REFERRAL_ROLES, _validate_referral_role,
        )

        assert 'ijcai_reviewer' in ALLOWED_REFERRAL_ROLES
        _validate_referral_role('ijcai_reviewer')  # must not raise

    def test_PROV_041_link_can_grant_ijcai_reviewer(self, app, db, app_context):
        """[PROV-041] A link can be created and updated to the demo role."""
        from services.referral_service import ReferralService

        link = _make_link(role_name='ijcai_reviewer')
        assert link.role_name == 'ijcai_reviewer'

        updated = ReferralService.update_link(link.id, role_name='ijcai_reviewer')
        assert updated.role_name == 'ijcai_reviewer'

    def test_PROV_042_admin_role_still_rejected(self, app, db, app_context):
        """[PROV-042] SECURITY regression: the allowlist still blocks 'admin'."""
        from decorators.error_handler import ValidationError

        with pytest.raises(ValidationError):
            _make_link(role_name='admin')
