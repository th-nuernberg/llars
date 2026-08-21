# routes.py
#
# ⚠️ DEPRECATED: This file is legacy dead code and should NOT be imported.
# All routes have been migrated to:
#   - auth/auth_routes.py (register, login, logout, register_admin)
#   - auth/data_routes.py (email_threads, rankings, admin operations)
#
# This file previously contained unprotected route handlers that attached
# to the shared auth_blueprint and data_blueprint. It was identified as a
# security risk (CRITICAL) during the security audit on 2026-02-26 because
# the routes lacked @authentik_required / @require_permission decorators.
#
# The route handlers have been removed to prevent accidental reactivation.
# Helper functions that delegated to services have also been removed since
# no code imports them (verified via codebase grep).
#
# If you need any of these routes, use the properly secured versions in
# routes/auth/auth_routes.py and routes/auth/data_routes.py.

import warnings

warnings.warn(
    "routes.routes is deprecated and should not be imported. "
    "Use routes.auth.auth_routes and routes.auth.data_routes instead.",
    DeprecationWarning,
    stacklevel=2,
)
