"""
Route tests for the Admin Mail-Center API (real blueprints via system API key).

Confirms the endpoints are reachable with the System Admin API key, validate
their input, and produce the expected previews / log reads. SMTP is mocked.
Test-IDs use the MAILR_ prefix.
"""

import pytest
from unittest.mock import patch

# Register Mail-Center tables in metadata before rdb's create_all().
from db.models.email_log import EmailLog, ReferralInvitation  # noqa: E402

API_KEY = {'X-API-Key': 'test-system-api-key-12345'}


def _seed_link(rdb):
    from db.models.referral import ReferralCampaign, ReferralLink
    c = ReferralCampaign(name='C', created_by='admin', status='active')
    rdb.session.add(c)
    rdb.session.flush()
    link = ReferralLink(campaign_id=c.id, code='ABC', slug='study-x',
                        label='Study X', role_name='evaluator', created_by='admin')
    rdb.session.add(link)
    rdb.session.commit()
    return link.id


class TestMailAdminRoutes:

    def test_MAILR_001_requires_auth(self, rclient, rdb):
        """[MAILR-001] No API key / token → 401 or 403, never 200."""
        resp = rclient.get('/api/admin/mail/log')
        assert resp.status_code in (401, 403)

    def test_MAILR_002_log_empty_ok(self, rclient, rdb):
        """[MAILR-002] Log endpoint returns paginated structure with API key."""
        resp = rclient.get('/api/admin/mail/log', headers=API_KEY)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['total'] == 0
        assert data['entries'] == []

    def test_MAILR_003_announce_preview(self, rclient, rdb):
        """[MAILR-003] Preview renders branded HTML + resolves recipient count."""
        resp = rclient.post('/api/admin/mail/preview', headers=API_KEY, json={
            'mode': 'announcement',
            'subject': 'Hallo',
            'body': '**Wichtig**',
            'recipient_spec': {'emails': ['a@x.com', 'a@x.com', 'b@y.com']},
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['subject'] == 'Hallo'
        assert '#b0ca97' in data['html']
        assert data['recipients']['count'] == 2

    def test_MAILR_004_invite_preview(self, rclient, rdb):
        """[MAILR-004] Invitation preview embeds the join link."""
        link_id = _seed_link(rdb)
        resp = rclient.post('/api/admin/mail/preview', headers=API_KEY, json={
            'mode': 'invitation',
            'referral_link_id': link_id,
            'intro': 'Komm rein',
            'recipients': ['x@y.com'],
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert '/join/study-x' in data['html']
        assert data['recipients']['count'] == 1

    def test_MAILR_005_announce_validates(self, rclient, rdb):
        """[MAILR-005] Announce without subject → 400."""
        resp = rclient.post('/api/admin/mail/announce', headers=API_KEY, json={
            'body': 'x', 'recipient_spec': {'emails': ['a@x.com']},
        })
        assert resp.status_code == 400

    def test_MAILR_006_invite_sends_and_logs(self, rclient, rdb):
        """[MAILR-006] Invite endpoint sends, logs, and creates invitation rows."""
        from services import email_service
        link_id = _seed_link(rdb)
        with patch.object(email_service, '_send_sync', return_value=True):
            resp = rclient.post('/api/admin/mail/invite', headers=API_KEY, json={
                'referral_link_id': link_id,
                'recipients': ['p@x.com', 'q@x.com'],
                'intro': 'Hi',
            })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['result']['sent'] == 2
        assert EmailLog.query.filter_by(mail_type='invitation').count() == 2
        assert ReferralInvitation.query.filter_by(referral_link_id=link_id).count() == 2

    def test_MAILR_007_link_invitation_stats(self, rclient, rdb):
        """[MAILR-007] Per-link invitation stats endpoint returns the funnel."""
        link_id = _seed_link(rdb)
        rdb.session.add(ReferralInvitation(referral_link_id=link_id, email='a@x.com'))
        rdb.session.commit()
        resp = rclient.get(f'/api/admin/referral/links/{link_id}/invitations',
                           headers=API_KEY)
        assert resp.status_code == 200
        stats = resp.get_json()['stats']
        assert stats['invited'] == 1
        assert stats['pending'] == 1

    def test_MAILR_008_invite_link_404(self, rclient, rdb):
        """[MAILR-008] Unknown referral link → 404."""
        resp = rclient.post('/api/admin/mail/invite', headers=API_KEY, json={
            'referral_link_id': 999999, 'recipients': ['a@x.com'],
        })
        assert resp.status_code == 404

    def test_MAILR_009_templates_requires_auth(self, rclient, rdb):
        """[MAILR-009] Template preview endpoint needs auth (no key → 401/403)."""
        resp = rclient.get('/api/admin/mail/templates')
        assert resp.status_code in (401, 403)

    def test_MAILR_010_templates_returns_three(self, rclient, rdb):
        """[MAILR-010] Templates endpoint returns the 3 standard mails rendered."""
        resp = rclient.get('/api/admin/mail/templates', headers=API_KEY)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        types = [t['type'] for t in data['templates']]
        assert types == [
            'welcome', 'password_reset', 'invitation', 'ijcai',
            'demo_invitation_de', 'demo_invitation_en',
        ]
        for t in data['templates']:
            assert t['subject'] and t['html'] and t['description']
            assert '#b0ca97' in t['html']

    def test_MAILR_011_templates_single_type(self, rclient, rdb):
        """[MAILR-011] ?type=welcome renders just that template with sample data."""
        resp = rclient.get('/api/admin/mail/templates?type=welcome', headers=API_KEY)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['templates']) == 1
        assert data['templates'][0]['type'] == 'welcome'
        assert 'Max Mustermann' in data['templates'][0]['html']

    def test_MAILR_012_templates_unknown_type_400(self, rclient, rdb):
        """[MAILR-012] An unknown ?type → 400 ValidationError."""
        resp = rclient.get('/api/admin/mail/templates?type=nope', headers=API_KEY)
        assert resp.status_code == 400

    # ---- Quick-send (Vorlagen → Schnellversand) -------------------------------

    def test_MAILR_013_send_template_requires_auth(self, rclient, rdb):
        """[MAILR-013] Quick-send endpoint needs auth (no key → 401/403)."""
        resp = rclient.post('/api/admin/mail/send-template',
                            json={'type': 'welcome', 'email': 'a@x.com'})
        assert resp.status_code in (401, 403)

    def test_MAILR_014_send_template_by_type_sends_and_logs(self, rclient, rdb):
        """[MAILR-014] Quick-send a standard template → sends + logs that type."""
        from services import email_service
        with patch.object(email_service, '_send_sync', return_value=True):
            resp = rclient.post('/api/admin/mail/send-template', headers=API_KEY, json={
                'type': 'welcome', 'email': 'q@x.com',
            })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['result']['status'] == 'sent'
        assert data['result']['email'] == 'q@x.com'
        assert EmailLog.query.filter_by(
            mail_type='welcome', recipient_email='q@x.com').count() == 1

    def test_MAILR_015_send_template_requires_email(self, rclient, rdb):
        """[MAILR-015] Missing email → 400."""
        resp = rclient.post('/api/admin/mail/send-template', headers=API_KEY,
                            json={'type': 'welcome'})
        assert resp.status_code == 400

    def test_MAILR_016_send_template_requires_type_or_html(self, rclient, rdb):
        """[MAILR-016] Neither type nor body_html → 400."""
        resp = rclient.post('/api/admin/mail/send-template', headers=API_KEY,
                            json={'email': 'a@x.com'})
        assert resp.status_code == 400

    def test_MAILR_017_send_template_unknown_type_400(self, rclient, rdb):
        """[MAILR-017] Unknown template type → 400."""
        resp = rclient.post('/api/admin/mail/send-template', headers=API_KEY,
                            json={'type': 'nope', 'email': 'a@x.com'})
        assert resp.status_code == 400

    def test_MAILR_018_send_template_invalid_email_400(self, rclient, rdb):
        """[MAILR-018] Unresolvable address → 400."""
        resp = rclient.post('/api/admin/mail/send-template', headers=API_KEY,
                            json={'type': 'welcome', 'email': 'not-an-email'})
        assert resp.status_code == 400

    def test_MAILR_019_send_template_raw_html_announcement(self, rclient, rdb):
        """[MAILR-019] Branded body_html (no type) → sent + logged as announcement."""
        from services import email_service
        with patch.object(email_service, '_send_sync', return_value=True):
            resp = rclient.post('/api/admin/mail/send-template', headers=API_KEY, json={
                'subject': 'Einladung',
                'body_html': '<html><body>Hi</body></html>',
                'email': 'z@x.com',
            })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['result']['status'] == 'sent'
        assert EmailLog.query.filter_by(
            mail_type='announcement', recipient_email='z@x.com').count() == 1
