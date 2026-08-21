"""
Unit tests for the pure render functions of the transactional email service.

Covers the welcome / password-reset render extraction (so the three standard
mails are previewable, not just sendable) and the standard-template sample-data
renderer that backs the Mail-Center "Vorlagen" tab. No SMTP, no DB — these are
pure functions returning ``{subject, body_text, body_html}``. Test-IDs use the
EMAILR_ prefix.
"""

import pytest

from services import email_service


class TestRenderFunctions:

    def test_EMAILR_001_render_welcome_shape(self):
        """[EMAILR-001] render_welcome returns the expected keys + content."""
        r = email_service.render_welcome(username='alice')
        assert set(r) == {'subject', 'body_text', 'body_html'}
        assert 'alice' in r['subject']
        assert 'alice' in r['body_text']
        assert 'alice' in r['body_html']
        # Branded shell present.
        assert '#b0ca97' in r['body_html']

    def test_EMAILR_002_render_welcome_escapes_html(self):
        """[EMAILR-002] HTML-special username is escaped in the HTML body."""
        r = email_service.render_welcome(username='<script>x</script>')
        assert '<script>' not in r['body_html']
        assert '&lt;script&gt;' in r['body_html']

    def test_EMAILR_003_render_welcome_scenario_link(self):
        """[EMAILR-003] A scenario id produces a direct study link."""
        r = email_service.render_welcome(username='bob', scenario_id=42)
        assert '/scenarios/42/evaluate' in r['body_text']

    def test_EMAILR_004_render_password_reset_shape(self):
        """[EMAILR-004] render_password_reset returns shape + embeds the link."""
        link = 'https://example.org/reset?token=abc'
        r = email_service.render_password_reset(username='carol', reset_link=link)
        assert set(r) == {'subject', 'body_text', 'body_html'}
        assert link in r['body_text']
        assert link in r['body_html']
        assert 'carol' in r['body_html']

    def test_EMAILR_005_render_password_reset_ttl(self):
        """[EMAILR-005] The validity window is rendered into the body."""
        r = email_service.render_password_reset(
            username='dan', reset_link='https://x/y', ttl_hours=6
        )
        assert '6 Stunden' in r['body_text']
        assert '6 Stunden' in r['body_html']


class TestStandardTemplates:

    def test_EMAILR_010_render_all_three(self):
        """[EMAILR-010] All standard templates render with sample data."""
        tpls = email_service.render_standard_templates()
        assert [t['type'] for t in tpls] == [
            'welcome', 'password_reset', 'invitation', 'ijcai',
            'demo_invitation_de', 'demo_invitation_en',
        ]
        for t in tpls:
            assert set(t) == {'type', 'subject', 'html', 'text', 'description', 'variables'}
            assert t['subject']
            assert '#b0ca97' in t['html']
            assert t['description']
            assert isinstance(t['variables'], list) and t['variables']

    def test_EMAILR_011_sample_data_is_marked(self):
        """[EMAILR-011] Sample placeholders are present (clearly fake)."""
        welcome = email_service.render_standard_template('welcome')
        assert email_service.SAMPLE_USERNAME in welcome['html']
        reset = email_service.render_standard_template('password_reset')
        assert email_service.SAMPLE_RESET_LINK in reset['html']
        inv = email_service.render_standard_template('invitation')
        assert '/join/beispiel-studie' in inv['html']

    def test_EMAILR_012_unknown_type_raises(self):
        """[EMAILR-012] An unknown template type raises ValueError."""
        with pytest.raises(ValueError):
            email_service.render_standard_template('does_not_exist')


class TestSendStillWorks:

    def test_EMAILR_020_send_registration_calls_render(self, monkeypatch):
        """[EMAILR-020] send_registration_confirmation routes through record_and_send."""
        captured = {}

        def fake_record_and_send(**kwargs):
            captured.update(kwargs)
            return {'status': 'sent', 'log_id': 1}

        monkeypatch.setattr(email_service, 'record_and_send', fake_record_and_send)
        email_service.send_registration_confirmation(username='eve', email='eve@x.com')
        assert captured['mail_type'] == 'welcome'
        assert captured['to_email'] == 'eve@x.com'
        assert 'eve' in captured['subject']
        assert 'eve' in captured['body_html']

    def test_EMAILR_021_send_password_reset_calls_render(self, monkeypatch):
        """[EMAILR-021] send_password_reset routes the rendered body to send."""
        captured = {}

        def fake_record_and_send(**kwargs):
            captured.update(kwargs)
            return {'status': 'sent', 'log_id': 1}

        monkeypatch.setattr(email_service, 'record_and_send', fake_record_and_send)
        email_service.send_password_reset(
            username='frank', email='frank@x.com',
            reset_link='https://example.org/reset?token=xyz',
        )
        assert captured['mail_type'] == 'password_reset'
        assert captured['to_email'] == 'frank@x.com'
        assert 'https://example.org/reset?token=xyz' in captured['body_html']
        # PRIVACY: reset mails carry no meta preview.
        assert 'meta' not in captured or captured.get('meta') is None

    def test_EMAILR_022_send_password_reset_skips_synthetic(self, monkeypatch):
        """[EMAILR-022] Synthetic inbox → no send attempt at all."""
        called = {'n': 0}

        def fake_record_and_send(**kwargs):
            called['n'] += 1
            return {'status': 'sent', 'log_id': 1}

        monkeypatch.setattr(email_service, 'record_and_send', fake_record_and_send)
        email_service.send_password_reset(
            username='ghost', email='ghost@noemail.invalid',
            reset_link='https://x/y',
        )
        assert called['n'] == 0


class TestStandardWelcome:
    """Standard-/Custom-Willkommensmail + Link-Routing (EMAILR_1xx)."""

    def test_EMAILR_101_standard_welcome_fills_study_and_name(self):
        r = email_service.render_standard_welcome(
            username='vrm-user', display_name='Anna', study_name='VRM Pilotstudie',
            scenario_id=42,
        )
        assert set(r) == {'subject', 'body_text', 'body_html'}
        assert 'VRM Pilotstudie' in r['subject'] and 'vrm-user' in r['subject']
        assert 'Hallo Anna' in r['body_text']
        assert '/scenarios/42/evaluate' in r['body_text']
        # The study-agnostic mail must never carry the KKB study branding.
        assert 'Kann KI' not in r['body_text'] and 'Kann KI' not in r['body_html']

    def test_EMAILR_102_standard_welcome_without_study(self):
        r = email_service.render_standard_welcome(username='u2')
        assert 'LLARS' in r['subject']
        assert '/login' in r['body_text']

    def test_EMAILR_103_placeholders_replaced_verbatim(self):
        out = email_service._fill_welcome_placeholders(
            'Hi {name}, {study}: {study_link} {unknown}',
            {'name': 'Bo', 'study': 'S', 'study_link': 'http://x'},
        )
        # Known placeholders filled; unknown ones stay literal (no crash à la
        # str.format on user-authored braces).
        assert out == 'Hi Bo, S: http://x {unknown}'

    def test_EMAILR_104_custom_welcome_escapes_html_body(self):
        r = email_service.render_custom_welcome(
            subject_template='Hi {name}',
            body_template='<b>{name}</b>\nZeile 2',
            mapping={'name': 'A<script>'},
            header_title='Studie X',
        )
        assert r['subject'] == 'Hi A<script>'
        assert '<script>' not in r['body_html']  # escaped
        assert '<br>' in r['body_html']          # newline -> br

    def test_EMAILR_105_send_link_welcome_routing(self, monkeypatch):
        captured = []
        monkeypatch.setattr(email_service, 'record_and_send',
                            lambda **kw: captured.append(kw))

        class _Link:
            id = None
            label = 'Meine Studie'
            welcome_template = 'standard'
            welcome_subject = None
            welcome_body = None

        class _Custom(_Link):
            welcome_template = 'custom'
            welcome_subject = 'Los, {name}!'
            welcome_body = 'Willkommen bei {study}.'

        class _Kkb(_Link):
            welcome_template = 'kkb'

        for link in (_Link(), _Custom(), _Kkb()):
            email_service.send_link_welcome(
                link=link, username='u', email='t@example.org', display_name='Anna',
            )

        templates = [c['meta']['welcome_template'] for c in captured]
        assert templates == ['standard', 'custom', 'kkb']
        assert captured[1]['subject'] == 'Los, Anna!'
        assert 'Kann KI Beratung' in captured[2]['subject']
        assert 'Kann KI' not in captured[0]['subject']
