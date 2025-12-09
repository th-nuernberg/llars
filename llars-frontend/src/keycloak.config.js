/**
 * Legacy Keycloak configuration (nicht mehr aktiv verwendet; Authentik ist Standard).
 * Bleibt für historische Kompatibilität und Referenz bestehen.
 */

export const keycloakConfig = {
  // Legacy Keycloak server URL - defaults to localhost for development
  url: import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost:55090',

  // Realm name
  realm: import.meta.env.VITE_KEYCLOAK_REALM || 'llars',

  // Client ID for the frontend application
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'llars-frontend'
}

export const keycloakInitOptions = {
  // Authentication method on page load
  // 'check-sso' = Only authenticate if user is already logged in (no forced redirect)
  // This allows the login page to be shown first
  onLoad: 'check-sso',

  // Check login iframe for session status monitoring
  // DISABLED: Can cause redirect loops in development (historic Keycloak issue)
  checkLoginIframe: false,

  // Enable PKCE (Proof Key for Code Exchange) for added security
  pkceMethod: 'S256',

  // Response mode
  responseMode: 'fragment',

  // Flow type
  flow: 'standard'
}

export default {
  config: keycloakConfig,
  init: keycloakInitOptions
}
