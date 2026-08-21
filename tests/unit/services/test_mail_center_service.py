"""
Unit tests for the Admin Mail-Center: email_service instrumentation,
recipient resolution, send orchestration, acceptance matching and log queries.

SMTP is always mocked (no network); ``email_log`` rows are written to the
in-memory SQLite test DB. Test-IDs use the MAIL_ prefix.
"""

import pytest
from unittest.mock import patch, MagicMock

# Import the Mail-Center models at collection time so their tables are part of
# SQLAlchemy metadata before the `db` fixture runs create_all().
from db.models.email_log import (  # noqa: E402
    EmailLog, ReferralInvitation, MailType, MailStatus, PREVIEW_MAX_CHARS,
)


def _make_campaign_and_link(db, slug='study-x', label='Study X'):
    from db.models.referral import ReferralCampaign, ReferralLink
    campaign = ReferralCampaign(name='C', created_by='admin', status='active')
    db.session.add(campaign)
    db.session.flush()
    link = ReferralLink(
        campaign_id=campaign.id, code='CODE123', slug=slug, label=label,
        role_name='evaluator', created_by='admin',
    )
    db.session.add(link)
    db.session.commit()
    return link


class TestEmailServiceInstrumentation:
    """record_and_send / send_* write exactly one email_log row per attempt."""

    def test_MAIL_001_record_and_send_logs_sent(self, app, db, app_context):
        """[MAIL-001] A successful async send writes a 'sent' email_log row."""
        from services import email_service
        with patch.object(email_service, 'send_async') as mock_send:
            res = email_service.record_and_send(
                mail_type='announcement',
                to_email='alice@example.com',
                subject='Hi',
                body_text='body',
            )
        assert mock_send.called
        assert res['status'] == 'sent'
        row = EmailLog.query.get(res['log_id'])
        assert row is not None
        assert row.status == MailStatus.SENT.value
        assert row.recipient_email == 'alice@example.com'

    def test_MAIL_002_skips_synthetic_inbox(self, app, db, app_context):
        """[MAIL-002] @noemail.invalid is logged as 'skipped' and never sent."""
        from services import email_service
        with patch.object(email_service, 'send_async') as mock_send:
            res = email_service.record_and_send(
                mail_type='welcome',
                to_email='bob+study@noemail.invalid',
                subject='Welcome',
                body_text='body',
            )
        assert not mock_send.called
        assert res['status'] == 'skipped'
        row = EmailLog.query.get(res['log_id'])
        assert row.status == MailStatus.SKIPPED.value

    def test_MAIL_003_sync_failure_logged(self, app, db, app_context):
        """[MAIL-003] A blocking send that fails records status 'failed'."""
        from services import email_service
        with patch.object(email_service, '_send_sync', return_value=False):
            res = email_service.record_and_send(
                mail_type='announcement',
                to_email='carol@example.com',
                subject='Hi',
                body_text='body',
                async_send=False,
            )
        assert res['status'] == 'failed'
        row = EmailLog.query.get(res['log_id'])
        assert row.status == MailStatus.FAILED.value
        assert row.error

    def test_MAIL_004_password_reset_never_stores_body(self, app, db, app_context):
        """[MAIL-004] Reset mail logs type/recipient/subject but no body/token."""
        from services import email_service
        with patch.object(email_service, 'send_async'):
            email_service.send_password_reset(
                username='dave', email='dave@example.com',
                reset_link='https://x/reset?token=SECRET123',
            )
        row = EmailLog.query.filter_by(mail_type='password_reset').first()
        assert row is not None
        # No meta preview, and the secret token must not appear anywhere logged.
        assert (row.meta_json or {}) == {} or 'token' not in str(row.meta_json)
        assert 'SECRET123' not in (row.subject or '')
        assert 'SECRET123' not in str(row.meta_json)

    def test_MAIL_005_welcome_username_in_subject(self, app, db, app_context):
        """[MAIL-005] Welcome mail puts the username in the subject + logs it."""
        from services import email_service
        with patch.object(email_service, 'send_async'):
            email_service.send_registration_confirmation(
                username='erin', email='erin@example.com',
            )
        row = EmailLog.query.filter_by(mail_type='welcome').first()
        assert row is not None
        assert 'erin' in row.subject
        assert (row.meta_json or {}).get('username') == 'erin'

    def test_MAIL_006_announcement_preview_truncated(self, app, db, app_context):
        """[MAIL-006] Announcement stores only a <=280-char body preview."""
        from services import email_service
        long_body = 'x' * 1000
        with patch.object(email_service, 'send_async'):
            email_service.send_announcement(
                to_email='f@example.com', subject='S', body=long_body,
            )
        row = EmailLog.query.filter_by(mail_type='announcement').first()
        assert len(row.meta_json['preview']) <= PREVIEW_MAX_CHARS


class TestRecipientResolution:
    """resolve_recipients dedups, validates and skips synthetic addresses."""

    def test_MAIL_010_dedup_and_validate(self, app, db, app_context):
        """[MAIL-010] Mixed list is deduped, validated, garbage dropped."""
        from services.mail.mail_center_service import MailCenterService
        spec = {
            'emails': ['a@x.com', 'A@X.com', 'bad', 'b@y.com'],
            'list_text': 'c@z.com, a@x.com\n nope@@bad',
        }
        addrs, info = MailCenterService.resolve_recipients(spec)
        assert sorted(addrs) == ['a@x.com', 'b@y.com', 'c@z.com']
        assert info['count'] == 3
        assert info['skipped_invalid'] >= 1
        assert info['skipped_duplicate'] >= 1

    def test_MAIL_011_skips_noemail_invalid(self, app, db, app_context):
        """[MAIL-011] Synthetic @noemail.invalid addresses are skipped."""
        from services.mail.mail_center_service import MailCenterService
        addrs, info = MailCenterService.resolve_recipients(
            {'emails': ['real@x.com', 'u+study@noemail.invalid']}
        )
        assert addrs == ['real@x.com']

    def test_MAIL_012_by_referral_link(self, app, db, app_context):
        """[MAIL-012] Ref-link resolution reads registration-time emails."""
        from db.models.referral import ReferralRegistration
        from services.mail.mail_center_service import MailCenterService
        link = _make_campaign_and_link(db)
        db.session.add(ReferralRegistration(
            link_id=link.id, username='u1', metadata_json={'email': 'u1@x.com'}))
        db.session.add(ReferralRegistration(
            link_id=link.id, username='u2', metadata_json={'email': 'u2+study@noemail.invalid'}))
        db.session.commit()
        addrs, _ = MailCenterService.resolve_recipients({'referral_link_id': link.id})
        assert addrs == ['u1@x.com']


class TestInviteAndAcceptance:
    """Invitation send writes invitation rows; registration flips to accepted."""

    def test_MAIL_020_send_invitations_creates_rows(self, app, db, app_context):
        """[MAIL-020] Each invitation send upserts a referral_invitation row."""
        from services import email_service
        from services.mail.mail_center_service import MailCenterService
        link = _make_campaign_and_link(db)
        # Small list → inline blocking send, which calls _send_sync.
        with patch.object(email_service, '_send_sync', return_value=True):
            result = MailCenterService.send_invitations(
                link=link, recipients=['inv1@x.com', 'inv2@x.com'], intro='Komm rein',
            )
        assert result['sent'] == 2
        invs = ReferralInvitation.query.filter_by(referral_link_id=link.id).all()
        assert {i.email for i in invs} == {'inv1@x.com', 'inv2@x.com'}
        assert all(i.email_log_id is not None for i in invs)
        # And each produced an email_log invitation row tied to the link.
        logs = EmailLog.query.filter_by(mail_type='invitation', referral_link_id=link.id).all()
        assert len(logs) == 2

    def test_MAIL_021_match_on_registration(self, app, db, app_context):
        """[MAIL-021] A real-email registration flips an open invitation."""
        from services.mail.mail_center_service import MailCenterService
        link = _make_campaign_and_link(db)
        inv = ReferralInvitation(referral_link_id=link.id, email='join@x.com')
        db.session.add(inv)
        db.session.commit()
        matched = MailCenterService.match_invitation_on_registration(
            link_id=link.id, email='Join@X.com', user_id=42,
        )
        assert matched is True
        refreshed = ReferralInvitation.query.get(inv.id)
        assert refreshed.accepted_user_id == 42
        assert refreshed.status == 'accepted'

    def test_MAIL_022_no_match_without_email(self, app, db, app_context):
        """[MAIL-022] Synthetic/blank emails never match (optional-email gap)."""
        from services.mail.mail_center_service import MailCenterService
        link = _make_campaign_and_link(db)
        db.session.add(ReferralInvitation(referral_link_id=link.id, email='join@x.com'))
        db.session.commit()
        assert MailCenterService.match_invitation_on_registration(
            link_id=link.id, email='u+study@noemail.invalid', user_id=1) is False
        assert MailCenterService.match_invitation_on_registration(
            link_id=link.id, email='', user_id=1) is False

    def test_MAIL_023_link_invitation_stats(self, app, db, app_context):
        """[MAIL-023] Per-link funnel reports invited/accepted/pending + unmatched."""
        from db.models.referral import ReferralRegistration
        from services.mail.mail_center_service import MailCenterService
        link = _make_campaign_and_link(db)
        # 2 invited, 1 accepted.
        i1 = ReferralInvitation(referral_link_id=link.id, email='a@x.com', accepted_user_id=1)
        i2 = ReferralInvitation(referral_link_id=link.id, email='b@x.com')
        db.session.add_all([i1, i2])
        # A registration with no matching invitation (no email) → unmatched.
        db.session.add(ReferralRegistration(
            link_id=link.id, username='z', metadata_json={'email': ''}))
        db.session.commit()
        stats = MailCenterService.link_invitation_stats(link.id)
        assert stats['invited'] == 2
        assert stats['accepted'] == 1
        assert stats['pending'] == 1
        assert stats['registered_unmatched'] >= 1


class TestLogQuery:
    """query_log filters + paginates the central email_log."""

    def test_MAIL_030_filter_by_type_and_status(self, app, db, app_context):
        """[MAIL-030] Log query filters by mail_type and status."""
        from services.mail.mail_center_service import MailCenterService
        db.session.add(EmailLog(
            mail_type='welcome', recipient_email='a@x.com', subject='W',
            status='sent'))
        db.session.add(EmailLog(
            mail_type='announcement', recipient_email='b@x.com', subject='A',
            status='failed'))
        db.session.commit()
        res = MailCenterService.query_log(mail_type='welcome')
        assert res['total'] == 1
        assert res['entries'][0]['mail_type'] == 'welcome'
        res2 = MailCenterService.query_log(status='failed')
        assert res2['total'] == 1


class TestPreviewRendering:
    """render_invitation / render_announcement produce branded HTML."""

    def test_MAIL_040_invitation_embeds_link(self, app, app_context):
        """[MAIL-040] Invitation is the long branded recruitment mail: embeds the
        join link + brand gradient, has the fixed subject "Kann KI Beratung?",
        shows the custom intro, and does NOT surface the recruiting-source label
        to recipients."""
        from services import email_service
        out = email_service.render_invitation(
            link_url='https://llars/join/study-x', label='Study X', intro='Hi')
        assert 'https://llars/join/study-x' in out['body_html']
        assert '#b0ca97' in out['body_html']
        assert out['subject'] == 'Kann KI Beratung?'
        assert 'Liebe Fachkräfte' in out['body_html']   # long recruitment version
        assert 'Hi' in out['body_html']                  # custom intro embedded
        assert 'Study X' not in out['body_html']         # source label not shown

    def test_MAIL_041_announcement_renders_markdown(self, app, app_context):
        """[MAIL-041] Announcement body renders to safe HTML in the brand shell."""
        from services import email_service
        out = email_service.render_announcement(subject='News', body='**bold** text')
        assert 'News' in out['subject']
        assert '#88c4c8' in out['body_html']
