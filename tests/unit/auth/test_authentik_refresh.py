"""
Unit tests for the Authentik token-refresh endpoint.

Route: app/routes/authentik_routes.py -> refresh()

Why this endpoint exists (INCIDENT 2026-07-29): Authentik issues access tokens
with a 60-minute lifetime, and every login response has always carried a
``refresh_token`` — but nothing ever used it. There was no backend endpoint and
no client-side call, so after exactly one hour the next API request 401'd and
the axios interceptor logged the user straight out. Raters working through a few
hundred labeling items were ejected mid-study, every hour.

These are UNIT tests that drive the real view function inside a request context,
NOT integration tests through the test client: ``tests/conftest.py`` registers a
*stub* blueprint at ``/auth/authentik`` (see ``test_authentik_bp``), so a client
call to ``/auth/authentik/refresh`` would never reach this code — it would 404,
and assertions like "not 401" would pass for entirely the wrong reason.

Test IDs: [REFRESH-001] through [REFRESH-007]
"""

import pytest


def _call_refresh(app, payload):
    """Invoke the real view inside a request context, return (body, status)."""
    from routes.authentik_routes import refresh

    with app.test_request_context(
        '/auth/authentik/refresh', method='POST', json=payload
    ):
        result = refresh()

    # @handle_api_errors returns either (response, status) or a bare response.
    if isinstance(result, tuple):
        response, status = result[0], result[1]
    else:
        response, status = result, result.status_code

    return response.get_json(), status


class _FakeResponse:
    """Minimal stand-in for a requests.Response."""

    def __init__(self, status_code, payload=None, text=''):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


class TestRefreshEndpoint:

    def test_REFRESH_001_missing_token_is_rejected(self, app, app_context):
        """[REFRESH-001] No refresh_token in the body -> 400, no upstream call."""
        body, status = _call_refresh(app, {})
        assert status == 400

    def test_REFRESH_002_empty_token_is_rejected(self, app, app_context):
        """[REFRESH-002] An empty string is treated as missing."""
        body, status = _call_refresh(app, {'refresh_token': ''})
        assert status == 400

    def test_REFRESH_003_success_returns_new_bundle(self, app, app_context, monkeypatch):
        """[REFRESH-003] A successful exchange returns the renewed tokens."""
        import requests as http_requests

        captured = {}

        def _post(url, data=None, **kwargs):
            captured['url'] = url
            captured['data'] = data
            return _FakeResponse(200, {
                'access_token': 'fresh-access',
                'refresh_token': 'fresh-refresh',
                'expires_in': 3600,
            })

        monkeypatch.setattr(http_requests, 'post', _post)

        body, status = _call_refresh(app, {'refresh_token': 'still-valid'})

        assert status == 200
        assert body['access_token'] == 'fresh-access'
        assert body['refresh_token'] == 'fresh-refresh'

    def test_REFRESH_004_uses_the_refresh_token_grant(self, app, app_context, monkeypatch):
        """[REFRESH-004] Calls Authentik's token endpoint with the right grant.

        Guards the contract with Authentik: a wrong grant_type or a dropped
        client_secret would fail only at runtime, against the real IdP.
        """
        import requests as http_requests

        captured = {}

        def _post(url, data=None, **kwargs):
            captured['url'] = url
            captured['data'] = data
            return _FakeResponse(200, {'access_token': 'a', 'refresh_token': 'b'})

        monkeypatch.setattr(http_requests, 'post', _post)

        _call_refresh(app, {'refresh_token': 'the-token'})

        assert captured['url'].endswith('/application/o/token/')
        assert captured['data']['grant_type'] == 'refresh_token'
        assert captured['data']['refresh_token'] == 'the-token'
        assert 'client_id' in captured['data']
        assert 'client_secret' in captured['data']

    def test_REFRESH_005_rejected_token_maps_to_401(self, app, app_context, monkeypatch):
        """[REFRESH-005] Authentik refusing the token surfaces as 401, not 400.

        The frontend only falls back to a real logout once the refresh itself is
        rejected, so this status is load-bearing.
        """
        import requests as http_requests

        monkeypatch.setattr(
            http_requests, 'post',
            lambda *a, **k: _FakeResponse(400, {'error': 'invalid_grant'}, 'invalid_grant')
        )

        body, status = _call_refresh(app, {'refresh_token': 'revoked'})
        assert status == 401

    def test_REFRESH_006_upstream_outage_does_not_500(self, app, app_context, monkeypatch):
        """[REFRESH-006] Authentik being unreachable is handled, not a crash."""
        import requests as http_requests

        def _boom(*a, **k):
            raise http_requests.RequestException('connection refused')

        monkeypatch.setattr(http_requests, 'post', _boom)

        body, status = _call_refresh(app, {'refresh_token': 'whatever'})
        assert status < 500

    def test_REFRESH_007_roles_are_re_enriched(self, app, app_context, monkeypatch):
        """[REFRESH-007] A refreshed token carries llars_roles again.

        Roles live in MariaDB, not in the Authentik token. Without re-enrichment
        the client would silently lose them on refresh and the router's
        power-role checks would start treating the user as a plain evaluator.
        """
        import requests as http_requests
        import routes.authentik_routes as ar

        monkeypatch.setattr(
            http_requests, 'post',
            lambda *a, **k: _FakeResponse(200, {'access_token': 'x', 'refresh_token': 'y'})
        )
        # Pretend the new access token decodes to a known user.
        monkeypatch.setattr(ar, 'get_username', lambda payload: 'someuser')
        monkeypatch.setattr(
            'auth.oidc_validator.validate_token', lambda tok: {'preferred_username': 'someuser'}
        )

        enriched = {}

        def _fake_enrich(token_data, username):
            enriched['username'] = username
            token_data['llars_roles'] = ['researcher']

        monkeypatch.setattr(ar, '_enrich_token_with_roles', _fake_enrich)

        body, status = _call_refresh(app, {'refresh_token': 'valid'})

        assert status == 200
        assert enriched['username'] == 'someuser'
        assert body['llars_roles'] == ['researcher']
