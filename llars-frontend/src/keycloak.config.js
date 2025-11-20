/**
 * Keycloak Configuration for LLARS Frontend
 *
 * This configuration is used to initialize the Keycloak client
 * Environment variables are injected by Vite at build time
 */

export const keycloakConfig = {
  // Keycloak server URL - defaults to localhost for development
  url: import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost:8090',

  // Realm name
  realm: import.meta.env.VITE_KEYCLOAK_REALM || 'llars',

  // Client ID for the frontend application
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'llars-frontend'
}

export const keycloakInitOptions = {
  // Authentication method on page load
  // 'check-sso' = Only authenticate if user is already logged in
  // 'login-required' = Always redirect to login if not authenticated
  onLoad: 'check-sso',

  // Use silent check-sso for better UX (check authentication in hidden iframe)
  silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',

  // Check login iframe for session status monitoring
  checkLoginIframe: true,
  checkLoginIframeInterval: 5,

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
