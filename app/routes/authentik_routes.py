"""
OIDC Authentication Routes (Authentik-backed)
These routes provide compatibility with the frontend while using Authentik for authentication.
Uses Authentik's OAuth2/OIDC endpoints for proper token issuance and validation.
"""

from typing import Optional

from flask import Blueprint, jsonify, request, g, current_app
from auth.decorators import authentik_required, admin_required, public_endpoint
from auth.oidc_validator import get_username, get_user_id
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError, UnauthorizedError
from services.user_profile_service import build_avatar_url

# Create blueprint for Authentik-specific routes
authentik_auth_blueprint = Blueprint('authentik_auth', __name__)


@authentik_auth_blueprint.route('/health_check', methods=['GET'])
@public_endpoint
def health_check():
    """Health check endpoint - no authentication required"""
    try:
        from services.system_event_service import SystemEventService

        SystemEventService.log_event(
            event_type="system.health_check",
            severity="info",
            message="Authentik health check OK",
            throttle_key="authentik_health_check_ok",
            throttle_seconds=300,
        )
    except Exception:
        pass
    return jsonify({"message": "Server is running with Authentik authentication"}), 200


@authentik_auth_blueprint.route('/me', methods=['GET'])
@authentik_required
def get_current_user():
    """
    Get current authenticated user information
    Uses Authentik token to return user details
    Rate limit: 100 requests per hour per IP
    """
    from db.database import db

    # g.authentik_user is now a User object after decorators.py fix
    user = g.authentik_user
    username = user.username if hasattr(user, 'username') else str(user)
    user_id = user.id if hasattr(user, 'id') else g.authentik_user_id

    # Get or generate avatar seed
    avatar_seed = None
    if hasattr(user, 'get_avatar_seed'):
        avatar_seed = user.get_avatar_seed()
        db.session.commit()  # Persist if newly generated

    return jsonify({
        "username": username,
        "user_id": user_id,
        "avatar_seed": avatar_seed,
        "avatar_url": build_avatar_url(user),
        "roles": g.authentik_token.get('realm_access', {}).get('roles', []),
        "email": g.authentik_token.get('email'),
        "name": g.authentik_token.get('name'),
        "preferred_username": g.authentik_token.get('preferred_username')
    }), 200


@authentik_auth_blueprint.route('/validate', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='authentik')
def validate_token_endpoint():
    """
    Validate token endpoint - for frontend to check if token is still valid
    Rate limit: 200 requests per hour per IP
    """
    token_payload = g.authentik_token

    return jsonify({
        'valid': True,
        'username': get_username(token_payload),
        'user_id': get_user_id(token_payload),
        'roles': token_payload.get('realm_access', {}).get('roles', [])
    }), 200


@authentik_auth_blueprint.route('/admin/check', methods=['GET'])
@admin_required
def check_admin():
    """
    Admin check endpoint - returns 200 if user is admin, 403 otherwise
    """
    return jsonify({
        "message": "User has admin privileges",
        "username": g.authentik_user
    }), 200


# Maximal so viele Stufen des Autorisierungs-Flows durchlaufen. Der Flow hat
# real genau eine (Consent); die Schranke ist gegen eine Fehlkonfiguration, die
# sonst eine Endlosschleife im Request-Thread erzeugen wuerde.
_MAX_AUTHZ_FLOW_STEPS = 5


def _authorization_code(session, authentik_base_url, auth_response):
    """Den Authorization-Code aus der Antwort von /application/o/authorize/ holen.

    Zwei Formen sind normal, und die zweite ist der Grund, warum es diese
    Funktion gibt:

    1. 302 direkt auf ``redirect_uri?code=...`` — kein Consent noetig.
    2. 302 in den Autorisierungs-Flow. Authentik erzwingt bei ``offline_access``
       ``prompt=consent`` (providers/oauth2/views/authorize.py), und zwar
       UNABHAENGIG davon, ob der Flow eine implizite Consent-Stage hat. Der Flow
       muss dann ausgefuehrt werden, sonst gibt es keinen Code — und ohne
       ``offline_access`` gibt Authentik kein Refresh-Token aus
       (providers/oauth2/views/token.py). Genau diese Zwickmuehle hat Bewertende
       stuendlich rausgeworfen.

    Der Login-Flow wird weiter oben schon per Flow-Executor gefahren; hier
    passiert dasselbe fuer den Autorisierungs-Flow. Die Consent-Stage
    beantwortet man mit ``{"component": "ak-stage-consent", "token": <token>}``
    — der Token kommt aus der Challenge und wird serverseitig gegen die Session
    geprueft (stages/consent/stage.py, ConsentChallengeResponse).

    Gibt den Code zurueck oder ``None``; der Aufrufer behandelt None als
    "Login fehlgeschlagen".
    """
    from urllib.parse import urlparse, parse_qs

    def _code_from(url):
        return (parse_qs(urlparse(url or '').query).get('code') or [None])[0]

    if auth_response.status_code not in (302, 303):
        return None

    location = auth_response.headers.get('Location', '')
    code = _code_from(location)
    if code:
        return code

    parsed = urlparse(location)
    segments = [seg for seg in parsed.path.split('/') if seg]
    if not segments:
        return None
    # ".../if/flow/<slug>/" bzw. ".../flows/-/<slug>/" — der Slug steht hinten.
    flow_slug = segments[-1]
    executor = f"{authentik_base_url}/api/v3/flows/executor/{flow_slug}/"
    # Die Query der Authorize-Anfrage muss mitgereicht werden, sonst weiss der
    # Executor nicht, welche Autorisierung er gerade abarbeitet.
    query = {'query': parsed.query}
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    for _ in range(_MAX_AUTHZ_FLOW_STEPS):
        stage = session.get(
            executor, params=query, headers={'Accept': 'application/json'}, timeout=10
        )
        if stage.status_code != 200:
            return None
        data = stage.json()

        code = _code_from(data.get('to'))
        if code:
            return code

        component = data.get('component')
        if component != 'ak-stage-consent':
            # Jede andere Stufe (MFA, Prompt, Fehler) laesst sich hier nicht
            # blind beantworten — dann lieber sauber scheitern als raten.
            current_app.logger.warning(
                f"Authorization flow stopped at unexpected stage: {component}"
            )
            return None

        # CSRF: Die POSTs des LOGIN-Flows laufen noch mit anonymer Session,
        # da prueft DRF nicht. Ab hier ist die Session authentifiziert, und
        # SessionAuthentication.enforce_csrf schlaegt zu — ohne Header kommt
        # "CSRF Failed: CSRF token missing" zurueck, das der Executor als
        # ak-stage-flow-error ausliefert. Authentik benennt beides eigen
        # (root/settings.py): Cookie authentik_csrf, Header X-authentik-CSRF —
        # das uebliche X-CSRFToken wird NICHT gelesen. Das Cookie erst hier
        # abholen, weil Django es unterwegs erneuern kann.
        post_headers = dict(headers)
        csrf_token = session.cookies.get('authentik_csrf')
        if csrf_token:
            post_headers['X-authentik-CSRF'] = csrf_token
            # Django prueft den Referer nur bei HTTPS; intern laeuft es ueber
            # HTTP. Mitschicken kostet nichts und haelt den Aufruf gueltig,
            # falls die interne Strecke spaeter auf TLS umgestellt wird.
            post_headers['Referer'] = f"{authentik_base_url}/"

        result = session.post(
            executor, params=query, headers=post_headers, timeout=10,
            json={'component': 'ak-stage-consent', 'token': data.get('token')},
        )
        if result.status_code != 200:
            return None
        code = _code_from(result.json().get('to'))
        if code:
            return code

    current_app.logger.warning('Authorization flow did not yield a code')
    return None


@authentik_auth_blueprint.route('/refresh', methods=['POST'])
@public_endpoint
@handle_api_errors(logger_name='authentik')
def refresh():
    """
    Exchange a refresh token for a fresh access token.

    Why this exists (INCIDENT 2026-07-29): Authentik issues access tokens with a
    60-minute lifetime and the login response has always included a
    ``refresh_token`` — but nothing ever used it. There was no refresh endpoint
    and no client-side call, so after exactly one hour the next API request 401'd
    and the axios interceptor hard-logged the user out. For raters working
    through a few hundred labeling items that meant a forced re-login mid-study,
    every hour, losing whatever was in flight.

    ``@public_endpoint`` on purpose: by the time a refresh is needed the access
    token is typically already expired, so requiring a valid one would defeat
    the point. The refresh token itself is the credential here — Authentik
    validates it and will reject anything revoked, expired or forged.

    Returns the same shape as ``/login`` (access_token, refresh_token, ...,
    plus ``llars_roles``) so the frontend can reuse one storage path.
    """
    import os
    import requests as http_requests

    data = request.get_json() or {}
    refresh_token = data.get('refresh_token')

    if not refresh_token:
        raise ValidationError('refresh_token required')

    authentik_base_url = os.getenv('AUTHENTIK_INTERNAL_URL', 'http://authentik-server:9000')
    client_id = os.getenv('AUTHENTIK_BACKEND_CLIENT_ID', 'llars-backend')
    client_secret = os.getenv(
        'AUTHENTIK_BACKEND_CLIENT_SECRET',
        'llars-backend-secret-change-in-production'
    )

    try:
        token_response = http_requests.post(
            f"{authentik_base_url}/application/o/token/",
            data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': client_id,
                'client_secret': client_secret,
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
    except http_requests.RequestException as exc:
        current_app.logger.error(f"Refresh request to Authentik failed: {exc}")
        raise ValidationError('Authentication service error')

    if token_response.status_code != 200:
        # Revoked / expired / rotated-away refresh token. 401 (not 400) so the
        # frontend's existing "session is over" path handles it: the interceptor
        # only falls back to a real logout once the refresh itself is rejected.
        current_app.logger.info(
            f"Refresh rejected by Authentik: {token_response.status_code}"
        )
        raise UnauthorizedError('Refresh token invalid or expired')

    token_data = token_response.json()

    # Roles live in MariaDB, not in the Authentik token, so a refreshed token
    # needs the same enrichment as a login — otherwise the client would silently
    # lose llars_roles on refresh and the router's power-role checks would start
    # treating the user as an evaluator.
    username = None
    try:
        from auth.oidc_validator import validate_token as _validate
        payload = _validate(token_data.get('access_token') or '')
        if payload:
            username = get_username(payload)
    except Exception as exc:  # pragma: no cover - defensive
        current_app.logger.warning(f"Could not read username from refreshed token: {exc}")

    if username:
        _enrich_token_with_roles(token_data, username)

    return jsonify(token_data), 200


@authentik_auth_blueprint.route('/login', methods=['POST'])
@public_endpoint
@handle_api_errors(logger_name='authentik')
def login():
    """
    Login endpoint - authenticates via Authentik Flow Executor API
    Rate limit: 10 requests per minute per IP

    Uses Authentik's Flow Executor API to authenticate users via the
    llars-api-authentication flow, then exchanges the session for an OAuth2 token.
    Returns RS256 signed JWT tokens from Authentik.
    """
    import os
    import requests as http_requests
    import uuid

    # Get credentials from request
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        raise ValidationError('Username and password required')

    current_app.logger.info(f"Login attempt received for user: {username}")

    try:
        # Authentik configuration
        authentik_base_url = os.getenv('AUTHENTIK_INTERNAL_URL', 'http://authentik-server:9000')
        flow_slug = 'llars-api-authentication'
        client_id = os.getenv('AUTHENTIK_BACKEND_CLIENT_ID', 'llars-backend')
        client_secret = os.getenv('AUTHENTIK_BACKEND_CLIENT_SECRET', 'llars-backend-secret-change-in-production')

        # Create a session to maintain cookies (Authentik browser session)
        session = http_requests.Session()

        # Step 1: Start the authentication flow
        flow_url = f"{authentik_base_url}/api/v3/flows/executor/{flow_slug}/"
        current_app.logger.info(f"Starting Authentik flow for {username}")

        # Get initial flow state
        flow_response = session.get(
            flow_url,
            headers={'Accept': 'application/json'},
            timeout=10
        )

        if flow_response.status_code != 200:
            current_app.logger.error(f"Failed to start flow: {flow_response.status_code} - {flow_response.text}")
            raise ValidationError('Authentication service error')

        flow_data = flow_response.json()
        current_app.logger.debug(f"Flow response: {flow_data}")

        # Step 2: Submit username to identification stage
        if flow_data.get('component') == 'ak-stage-identification':
            flow_response = session.post(
                flow_url,
                json={'uid_field': username},
                headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                timeout=10
            )

            if flow_response.status_code != 200:
                current_app.logger.error(f"Identification failed: {flow_response.status_code}")
                try:
                    from services.system_event_service import SystemEventService

                    SystemEventService.log_event(
                        event_type="auth.login_failed",
                        severity="warning",
                        username=username,
                        entity_type="user",
                        entity_id=username,
                        message=f"Login failed for '{username}' (identification stage)",
                    )
                except Exception:
                    pass
                raise UnauthorizedError('Invalid credentials')

            flow_data = flow_response.json()
            current_app.logger.debug(f"After identification: {flow_data}")

        # Step 3: Submit password to password stage
        if flow_data.get('component') == 'ak-stage-password':
            flow_response = session.post(
                flow_url,
                json={'password': password},
                headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                timeout=10
            )

            if flow_response.status_code != 200:
                current_app.logger.warning(f"Password validation failed for {username}")
                try:
                    from services.system_event_service import SystemEventService

                    SystemEventService.log_event(
                        event_type="auth.login_failed",
                        severity="warning",
                        username=username,
                        entity_type="user",
                        entity_id=username,
                        message=f"Login failed for '{username}' (password stage)",
                    )
                except Exception:
                    pass
                raise UnauthorizedError('Invalid credentials')

            flow_data = flow_response.json()
            current_app.logger.debug(f"After password: {flow_data}")

        # Check if authentication was successful
        # Flow executor returns redirect_to on success, or component for next stage
        if flow_data.get('type') == 'redirect' or 'to' in flow_data:
            current_app.logger.info(f"User {username} authenticated successfully via flow")

            # Step 4: Now use the authenticated session to get an OAuth2 token
            # We need to initiate an OAuth2 authorization flow
            state = str(uuid.uuid4())
            nonce = str(uuid.uuid4())

            # Get authorization code using implicit consent flow
            auth_url = f"{authentik_base_url}/application/o/authorize/"
            auth_params = {
                'response_type': 'code',
                'client_id': client_id,
                'redirect_uri': f"{authentik_base_url}/",  # Placeholder, we intercept
                # offline_access ist NICHT optional: ohne diesen Scope stellt
                # Authentik gar kein Refresh-Token aus (token.py:637), und die
                # komplette Erneuerungsmechanik im Frontend laeuft ins Leere —
                # Rauswurf nach spaetestens 60 Minuten. Der Scope ist dem
                # Provider in Authentik zugewiesen; er zwingt aber prompt=consent
                # auf, weshalb der Redirect danach in den Autorisierungs-Flow
                # geht statt zum Code. Das faengt _authorization_code() ab.
                'scope': 'openid profile email offline_access',
                'state': state,
                'nonce': nonce
            }

            auth_response = session.get(
                auth_url,
                params=auth_params,
                allow_redirects=False,  # We want to capture the redirect
                timeout=10
            )

            # Check for authorization code in redirect
            if auth_response.status_code in [302, 303]:
                current_app.logger.debug(
                    f"Auth redirect: {auth_response.headers.get('Location', '')}"
                )
                auth_code = _authorization_code(
                    session, authentik_base_url, auth_response
                )

                if auth_code:

                    # Step 5: Exchange authorization code for tokens
                    token_url = f"{authentik_base_url}/application/o/token/"
                    token_response = http_requests.post(
                        token_url,
                        data={
                            'grant_type': 'authorization_code',
                            'code': auth_code,
                            'redirect_uri': f"{authentik_base_url}/",
                            'client_id': client_id,
                            'client_secret': client_secret
                        },
                        headers={'Content-Type': 'application/x-www-form-urlencoded'},
                        timeout=10
                    )

                    if token_response.status_code == 200:
                        token_data = token_response.json()
                        current_app.logger.info(f"User {username} logged in successfully")
                        try:
                            from services.system_event_service import SystemEventService

                            SystemEventService.log_event(
                                event_type="auth.login",
                                severity="info",
                                username=username,
                                entity_type="user",
                                entity_id=username,
                                message=f"User '{username}' logged in",
                            )
                        except Exception:
                            pass

                        # Enrich with LLARS roles
                        _enrich_token_with_roles(token_data, username)

                        response = jsonify(token_data)

                        # Optional but important for real SSO:
                        # If the user later opens another OIDC-protected app (e.g., Matomo),
                        # Authentik will only skip the login prompt if the browser has an
                        # Authentik session cookie. Our login is server-side, so we propagate
                        # the Authentik session cookie to the browser here.
                        authentik_session_cookie = session.cookies.get('authentik_session')
                        if authentik_session_cookie:
                            forwarded_proto = request.headers.get('X-Forwarded-Proto', request.scheme)
                            response.set_cookie(
                                'authentik_session',
                                authentik_session_cookie,
                                httponly=True,
                                secure=(forwarded_proto == 'https'),
                                samesite='Lax',
                                path='/'
                            )

                        return response, 200
                    else:
                        current_app.logger.error(f"Token exchange failed: {token_response.text}")
                        try:
                            from services.system_event_service import SystemEventService

                            SystemEventService.log_event(
                                event_type="auth.login_error",
                                severity="error",
                                username=username,
                                entity_type="user",
                                entity_id=username,
                                message=f"Token exchange failed for '{username}'",
                            )
                        except Exception:
                            pass

            # If we can't get OAuth token, authentication failed
            current_app.logger.error(f"Could not obtain OAuth token for {username}")
            try:
                from services.system_event_service import SystemEventService

                SystemEventService.log_event(
                    event_type="auth.login_error",
                    severity="error",
                    username=username,
                    entity_type="user",
                    entity_id=username,
                    message=f"Could not obtain OAuth token for '{username}'",
                )
            except Exception:
                pass
            raise ValidationError('Could not obtain access token')

        # Authentication failed - check for error messages
        if flow_data.get('response_errors'):
            errors = flow_data.get('response_errors', {})
            current_app.logger.warning(f"Authentication failed for {username}: {errors}")
            raise UnauthorizedError('Invalid credentials')

        # Unknown state
        current_app.logger.error(f"Unexpected flow state: {flow_data}")
        raise ValidationError('Authentication error')

    except http_requests.exceptions.ConnectionError as e:
        current_app.logger.error(f"Cannot connect to Authentik: {e}")
        try:
            from services.system_event_service import SystemEventService

            SystemEventService.log_event(
                event_type="auth.service_error",
                severity="error",
                message="Cannot connect to Authentik",
                details={"error": str(e)},
                throttle_key="authentik_connect_error",
                throttle_seconds=60,
            )
        except Exception:
            pass
        raise ValidationError('Authentication service unavailable')
    except http_requests.exceptions.Timeout as e:
        current_app.logger.error(f"Authentik request timeout: {e}")
        try:
            from services.system_event_service import SystemEventService

            SystemEventService.log_event(
                event_type="auth.service_error",
                severity="error",
                message="Authentik request timeout",
                details={"error": str(e)},
                throttle_key="authentik_timeout",
                throttle_seconds=60,
            )
        except Exception:
            pass
        raise ValidationError('Authentication service timeout')


def issue_authentik_token(username: str, password: str) -> Optional[dict]:
    """
    Authenticate the given credentials against Authentik and return an
    OAuth2 token bundle ({access_token, id_token, expires_in, ...,
    llars_roles}). Returns ``None`` if any step of the flow fails.

    Extracted from ``login()`` so that other routes (e.g. the referral
    self-registration handler) can issue a token immediately after
    creating a user, without a second HTTP round-trip to ``/auth/login``.

    Does not raise — the caller decides how to handle a None result.
    Side effects: enriches the token with ``llars_roles`` via
    ``_enrich_token_with_roles``.
    """
    import os
    import uuid
    import requests as http_requests
    from urllib.parse import urlparse, parse_qs

    if not username or not password:
        return None

    authentik_base_url = os.getenv('AUTHENTIK_INTERNAL_URL', 'http://authentik-server:9000')
    flow_slug = 'llars-api-authentication'
    client_id = os.getenv('AUTHENTIK_BACKEND_CLIENT_ID', 'llars-backend')
    client_secret = os.getenv('AUTHENTIK_BACKEND_CLIENT_SECRET',
                              'llars-backend-secret-change-in-production')

    try:
        session = http_requests.Session()
        flow_url = f"{authentik_base_url}/api/v3/flows/executor/{flow_slug}/"

        flow_response = session.get(
            flow_url, headers={'Accept': 'application/json'}, timeout=10
        )
        if flow_response.status_code != 200:
            return None
        flow_data = flow_response.json()

        if flow_data.get('component') == 'ak-stage-identification':
            flow_response = session.post(
                flow_url,
                json={'uid_field': username},
                headers={'Accept': 'application/json',
                         'Content-Type': 'application/json'},
                timeout=10,
            )
            if flow_response.status_code != 200:
                return None
            flow_data = flow_response.json()

        if flow_data.get('component') == 'ak-stage-password':
            flow_response = session.post(
                flow_url,
                json={'password': password},
                headers={'Accept': 'application/json',
                         'Content-Type': 'application/json'},
                timeout=10,
            )
            if flow_response.status_code != 200:
                return None
            flow_data = flow_response.json()

        if not (flow_data.get('type') == 'redirect' or 'to' in flow_data):
            return None

        # OAuth2 authorization code → token exchange
        state = str(uuid.uuid4())
        nonce = str(uuid.uuid4())
        auth_response = session.get(
            f"{authentik_base_url}/application/o/authorize/",
            params={
                'response_type': 'code',
                'client_id': client_id,
                'redirect_uri': f"{authentik_base_url}/",
                # Siehe login(): ohne offline_access kein Refresh-Token.
                'scope': 'openid profile email offline_access',
                'state': state,
                'nonce': nonce,
            },
            allow_redirects=False,
            timeout=10,
        )
        auth_code = _authorization_code(session, authentik_base_url, auth_response)
        if not auth_code:
            return None

        token_response = http_requests.post(
            f"{authentik_base_url}/application/o/token/",
            data={
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': f"{authentik_base_url}/",
                'client_id': client_id,
                'client_secret': client_secret,
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10,
        )
        if token_response.status_code != 200:
            return None

        token_data = token_response.json()
        _enrich_token_with_roles(token_data, username)
        return token_data
    except Exception as exc:  # noqa: BLE001 — explicit best-effort
        try:
            from flask import current_app
            current_app.logger.warning(
                f"issue_authentik_token({username}) failed: {exc}"
            )
        except Exception:
            pass
        return None


def _enrich_token_with_roles(token_data: dict, username: str) -> None:
    """Add LLARS-specific roles from MariaDB to the token response"""
    try:
        from db.database import db
        from sqlalchemy import text
        user_roles = ['user']

        result = db.session.execute(
            text("""
                SELECT r.role_name
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.username = :username
            """),
            {'username': username}
        )

        for row in result:
            role_name = row[0]
            if role_name == 'viewer':
                role_name = 'evaluator'
            if role_name not in user_roles:
                user_roles.append(role_name)

        token_data['llars_roles'] = user_roles

    except Exception as e:
        from flask import current_app
        current_app.logger.warning(f"Could not fetch LLARS roles for {username}: {e}")

    # Referral-binding (Burghardt 2026-05-18): if the user originally
    # registered via a referral link that points at a specific scenario,
    # surface that scenario_id in the login response so the frontend
    # router can shortcut them straight into the rater flow on EVERY
    # subsequent login — not just on the initial registration redirect.
    # Best-effort: failures (no row, dropped link, schema mismatch) are
    # swallowed; the absence of the field just means "no shortcut".
    try:
        from db.database import db
        from db.models.referral import ReferralRegistration, ReferralLink
        registration = (
            db.session.query(ReferralRegistration)
            .filter_by(username=username)
            .first()
        )
        target_scenario_id = None
        if registration and registration.link_id:
            link = db.session.get(ReferralLink, registration.link_id)
            if link and getattr(link, 'target_scenario_id', None):
                target_scenario_id = link.target_scenario_id
        if target_scenario_id:
            token_data['referral_target_scenario_id'] = target_scenario_id
    except Exception as e:
        from flask import current_app
        current_app.logger.warning(
            f"Could not resolve referral target for {username}: {e}"
        )
