import { ref, computed } from 'vue';
import axios from 'axios';
import { matomoResetUserId, matomoSetUserId } from '@/plugins/llars-metrics';
import { usePermissions } from '@/composables/usePermissions';
import { decodeJwtPayload } from '@/utils/jwt';
import { logI18n } from '@/utils/logI18n';
import { setConsoleLogsEnabled } from '@/utils/consoleController';
// Standalone composable (no dependency back on useAuth) — safe to import
// here without creating a circular reference. Used to restore a returning
// user's profile language on every login.
import { useLanguage } from '@/composables/useLanguage';
import {
  AUTH_STORAGE_KEYS,
  clearAuthStorage,
  getAuthStorageItem,
  setAuthStorageItem
} from '@/utils/authStorage';

// Renew this long before the access token expires. Authentik issues 60-minute
// tokens, so 5 minutes leaves ample room for a slow network without refreshing
// so eagerly that we churn tokens.
const REFRESH_LEAD_MS = 5 * 60 * 1000;

// Module-level (not per-composable-instance): every useAuth() call shares one
// in-flight refresh and one timer, otherwise each component mounting the
// composable would schedule its own renewal.
let refreshInFlight = null;
let refreshTimer = null;

// Auth state
const token = ref(null);
const refreshToken = ref(null);
const idToken = ref(null);
const tokenParsed = ref(null);
const llarsRoles = ref([]);
const avatarSeed = ref(null);
const avatarUrl = ref(null);
const avatarChangesLeft = ref(null);
const collabColor = ref(null);
const consoleLogsEnabled = ref(false);

const parseJwt = (jwtToken) => {
  return decodeJwtPayload(jwtToken);
};

const isTokenExpired = (jwtToken, skewSeconds = 30) => {
  const payload = parseJwt(jwtToken);
  const exp = payload?.exp;
  if (!exp) return false;
  const now = Math.floor(Date.now() / 1000);
  return now >= (exp - skewSeconds);
};

const clearStoredTokens = () => {
  clearAuthStorage();
  try {
    localStorage.removeItem('username');
  } catch (e) {
    // ignore
  }
};

// Load tokens from sessionStorage on init
const loadTokensFromStorage = () => {
  token.value = getAuthStorageItem(AUTH_STORAGE_KEYS.token);
  refreshToken.value = getAuthStorageItem(AUTH_STORAGE_KEYS.refreshToken);
  idToken.value = getAuthStorageItem(AUTH_STORAGE_KEYS.idToken);

  // Load LLARS roles from storage
  const storedRoles = getAuthStorageItem(AUTH_STORAGE_KEYS.roles);
  if (storedRoles) {
    try {
      llarsRoles.value = JSON.parse(storedRoles);
    } catch (e) {
      logI18n('error', 'logs.auth.parseStoredRolesFailed', e);
      llarsRoles.value = [];
    }
  }

  // Load avatar seed from storage
  const storedAvatarSeed = getAuthStorageItem(AUTH_STORAGE_KEYS.avatarSeed);
  if (storedAvatarSeed) {
    avatarSeed.value = storedAvatarSeed;
  }

  // Load avatar URL from storage
  const storedAvatarUrl = getAuthStorageItem(AUTH_STORAGE_KEYS.avatarUrl);
  if (storedAvatarUrl) {
    avatarUrl.value = storedAvatarUrl;
  }

  // Load collab color from storage
  const storedCollabColor = getAuthStorageItem(AUTH_STORAGE_KEYS.collabColor);
  if (storedCollabColor) {
    collabColor.value = storedCollabColor;
  }

  if (token.value) {
    tokenParsed.value = parseJwt(token.value);
    if (!tokenParsed.value) {
      logI18n('error', 'logs.auth.parseTokenFailed');
    }
    if (isTokenExpired(token.value, 0)) {
      // Token expired → treat as logged out (avoids getting stuck with stale tokens)
      token.value = null;
      refreshToken.value = null;
      idToken.value = null;
      tokenParsed.value = null;
      llarsRoles.value = [];
      avatarSeed.value = null;
      avatarUrl.value = null;
      avatarChangesLeft.value = null;
      collabColor.value = null;
      clearStoredTokens();
    }
  }
};

// Fetch user profile to get avatar_seed
const fetchUserProfile = async () => {
  if (!token.value) return null;

  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
    const response = await axios.get(`${baseUrl}/auth/authentik/me`, {
      headers: {
        Authorization: `Bearer ${token.value}`
      }
    });

    const { avatar_seed, avatar_url, avatar_changes_left } = response.data;
    if (avatar_seed) {
      avatarSeed.value = avatar_seed;
      setAuthStorageItem(AUTH_STORAGE_KEYS.avatarSeed, avatar_seed);
    }
    if (avatar_url !== undefined) {
      avatarUrl.value = avatar_url || null;
      if (avatar_url) {
        setAuthStorageItem(AUTH_STORAGE_KEYS.avatarUrl, avatar_url);
      } else {
        setAuthStorageItem(AUTH_STORAGE_KEYS.avatarUrl, '');
      }
    }
    if (avatar_changes_left !== undefined && avatar_changes_left !== null) {
      avatarChangesLeft.value = avatar_changes_left;
    }

    return response.data;
  } catch (e) {
    logI18n('error', 'logs.auth.profileFetchFailed', e);
    return null;
  }
};

// Fetch user settings (collab_color, avatar_seed)
const fetchUserSettings = async () => {
  if (!token.value) return null;

  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
    const response = await axios.get(`${baseUrl}/api/users/me/settings`, {
      headers: {
        Authorization: `Bearer ${token.value}`
      }
    });

    const { collab_color, avatar_seed, avatar_url, avatar_changes_left, console_logs_enabled } = response.data;

    // Apply console logging preference
    consoleLogsEnabled.value = Boolean(console_logs_enabled);
    setConsoleLogsEnabled(consoleLogsEnabled.value);

    // Restore the returning user's persisted UI language from their
    // profile preferences. Only when a supported language is actually
    // present — we never override an explicit in-session choice with a
    // missing value. setLanguage itself ignores anything unsupported.
    const profileLanguage = response.data?.preferences?.language;
    if (profileLanguage === 'de' || profileLanguage === 'en') {
      try {
        useLanguage().setLanguage(profileLanguage);
      } catch (_) {
        // i18n not yet ready — language falls back to localStorage default
      }
    }

    if (collab_color) {
      collabColor.value = collab_color;
      setAuthStorageItem(AUTH_STORAGE_KEYS.collabColor, collab_color);
    }

    if (avatar_seed) {
      avatarSeed.value = avatar_seed;
      setAuthStorageItem(AUTH_STORAGE_KEYS.avatarSeed, avatar_seed);
    }
    if (avatar_url !== undefined) {
      avatarUrl.value = avatar_url || null;
      if (avatar_url) {
        setAuthStorageItem(AUTH_STORAGE_KEYS.avatarUrl, avatar_url);
      } else {
        setAuthStorageItem(AUTH_STORAGE_KEYS.avatarUrl, '');
      }
    }
    if (avatar_changes_left !== undefined && avatar_changes_left !== null) {
      avatarChangesLeft.value = avatar_changes_left;
    }

    return response.data;
  } catch (e) {
    logI18n('error', 'logs.auth.settingsFetchFailed', e);
    return null;
  }
};

// Update user's collab color
const updateCollabColor = async (color) => {
  if (!token.value) return false;

  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
    const response = await axios.patch(`${baseUrl}/api/users/me/settings`, {
      collab_color: color
    }, {
      headers: {
        Authorization: `Bearer ${token.value}`
      }
    });

    if (response.data.success) {
      const nextColor = response.data.collab_color ?? color;
      collabColor.value = nextColor;
      if (nextColor) {
        setAuthStorageItem(AUTH_STORAGE_KEYS.collabColor, nextColor);
      } else {
        // Remove from storage if null
        setAuthStorageItem(AUTH_STORAGE_KEYS.collabColor, '');
      }
      return true;
    }
    return false;
  } catch (e) {
    logI18n('error', 'logs.auth.updateCollabColorFailed', e);
    return false;
  }
};

const applyAvatarResponse = (data) => {
  if (!data) return;
  if (data.avatar_seed) {
    avatarSeed.value = data.avatar_seed;
    setAuthStorageItem(AUTH_STORAGE_KEYS.avatarSeed, data.avatar_seed);
  }
  if (Object.prototype.hasOwnProperty.call(data, 'avatar_url')) {
    avatarUrl.value = data.avatar_url || null;
    if (data.avatar_url) {
      setAuthStorageItem(AUTH_STORAGE_KEYS.avatarUrl, data.avatar_url);
    } else {
      setAuthStorageItem(AUTH_STORAGE_KEYS.avatarUrl, '');
    }
  }
  if (data.avatar_changes_left !== undefined && data.avatar_changes_left !== null) {
    avatarChangesLeft.value = data.avatar_changes_left;
  }
};

const uploadAvatar = async (file) => {
  if (!token.value) return { success: false };
  if (!file) return { success: false };

  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post(`${baseUrl}/api/users/me/avatar`, formData, {
      headers: {
        Authorization: `Bearer ${token.value}`,
        'Content-Type': 'multipart/form-data'
      }
    });

    if (response.data.success) {
      applyAvatarResponse(response.data);
      return { success: true };
    }
    return { success: false, error: response.data.error };
  } catch (e) {
    logI18n('error', 'logs.auth.uploadAvatarFailed', e);
    return { success: false, error: e?.response?.data?.error || e?.message };
  }
};

const regenerateAvatar = async () => {
  if (!token.value) return { success: false };

  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
    const response = await axios.patch(`${baseUrl}/api/users/me/avatar`, {}, {
      headers: {
        Authorization: `Bearer ${token.value}`
      }
    });

    if (response.data.success) {
      applyAvatarResponse(response.data);
      return { success: true };
    }
    return { success: false, error: response.data.error };
  } catch (e) {
    logI18n('error', 'logs.auth.regenerateAvatarFailed', e);
    return { success: false, error: e?.response?.data?.error || e?.message };
  }
};

const resetAvatar = async () => {
  if (!token.value) return { success: false };

  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
    const response = await axios.delete(`${baseUrl}/api/users/me/avatar`, {
      headers: {
        Authorization: `Bearer ${token.value}`
      }
    });

    if (response.data.success) {
      applyAvatarResponse(response.data);
      return { success: true };
    }
    return { success: false, error: response.data.error };
  } catch (e) {
    logI18n('error', 'logs.auth.resetAvatarFailed', e);
    return { success: false, error: e?.response?.data?.error || e?.message };
  }
};

// Initialize on load
loadTokensFromStorage();

// Fetch profile and settings if we have a token
if (token.value && !avatarSeed.value) {
  fetchUserProfile();
}
if (token.value && !collabColor.value) {
  fetchUserSettings();
}

export const useAuth = () => {
  const isAuthenticated = computed(() => !!token.value && !isTokenExpired(token.value));

  const userRoles = computed(() => {
    // Use stored LLARS roles (from backend response, based on Authentik groups)
    // Fallback to token groups for backwards compatibility
    return llarsRoles.value.length > 0
      ? llarsRoles.value
      : (tokenParsed.value?.groups || []);
  });

  const isAdmin = computed(() => {
    // Source of truth: LLARS roles (DB-backed via backend login response)
    return userRoles.value.includes('admin');
  });

  /**
   * Apply a token bundle from any authentication flow into the current
   * auth state. Extracted so that flows other than the explicit login
   * form (e.g. self-registration via referral link) can authenticate
   * the user immediately after server-side credential creation, without
   * forcing a second password prompt.
   *
   * `tokenData` matches the /auth/authentik/login response shape:
   *   { access_token, refresh_token, id_token, llars_roles, ... }
   * `usernameHint` is used as a fallback when the JWT doesn't expose
   * preferred_username (e.g. fresh accounts that haven't propagated yet).
   */
  const applyTokenBundle = async (tokenData, usernameHint) => {
    if (!tokenData || !tokenData.access_token) return false;
    const {
      access_token,
      refresh_token,
      id_token,
      llars_roles: roles,
      referral_target_scenario_id: referralTarget,
    } = tokenData;

    token.value = access_token;
    refreshToken.value = refresh_token;
    idToken.value = id_token;
    llarsRoles.value = roles || [];

    // Mirror what login() does — persist the referral-bound scenario
    // so the router can shortcut on subsequent navigations.
    try {
      if (referralTarget != null) {
        localStorage.setItem('llars-referral-target-scenario', String(referralTarget))
      } else {
        localStorage.removeItem('llars-referral-target-scenario')
      }
    } catch (e) {
      // ignore
    }

    tokenParsed.value = parseJwt(access_token);

    setAuthStorageItem(AUTH_STORAGE_KEYS.token, access_token);
    setAuthStorageItem(AUTH_STORAGE_KEYS.refreshToken, refresh_token);
    if (id_token) setAuthStorageItem(AUTH_STORAGE_KEYS.idToken, id_token);
    setAuthStorageItem(AUTH_STORAGE_KEYS.roles, JSON.stringify(roles || []));

    try {
      const u = tokenParsed.value?.preferred_username || usernameHint;
      if (u) localStorage.setItem('username', u);
    } catch (_) { /* storage blocked */ }

    const matomoUserId = tokenParsed.value?.preferred_username
      || tokenParsed.value?.sub
      || usernameHint;
    if (matomoUserId) matomoSetUserId(matomoUserId);

    // Refresh dependent state — best effort, never throw.
    try {
      const perms = usePermissions();
      perms.clearPermissions();
      await perms.fetchPermissions(true);
    } catch (_) { /* refetched later */ }
    try { await fetchUserProfile(); } catch (_) { /* avatar fallback */ }
    try { await fetchUserSettings(); } catch (_) { /* default color */ }

    return true;
  };

  /**
   * Trade the stored refresh token for a fresh access token.
   *
   * INCIDENT 2026-07-29: Authentik access tokens live 60 minutes and a
   * refresh_token was stored on every login — but never used. There was no
   * backend endpoint and no client call, so after an hour the next request
   * 401'd and the axios interceptor logged the user straight out, mid-study.
   *
   * Single-flight: a burst of parallel requests all 401'ing at once must
   * trigger ONE refresh, not one per request — otherwise they race, and with
   * refresh-token rotation the losers would invalidate the winner's token.
   *
   * Returns the new access token, or null when the session is genuinely over
   * (caller should then log out).
   */
  const refreshAccessToken = async () => {
    if (refreshInFlight) return refreshInFlight;

    const current = refreshToken.value || getAuthStorageItem(AUTH_STORAGE_KEYS.refreshToken);
    if (!current) return null;

    const baseUrl = import.meta.env.VITE_API_BASE_URL || '';

    refreshInFlight = (async () => {
      try {
        // Bare axios config: the global request interceptor would attach the
        // (expired) access token, which this endpoint neither needs nor reads.
        const response = await axios.post(
          `${baseUrl}/auth/authentik/refresh`,
          { refresh_token: current },
          { headers: { 'Content-Type': 'application/json' }, _skipAuthRefresh: true }
        );

        const applied = await applyTokenBundle(response.data);
        if (!applied) return null;

        scheduleTokenRefresh();
        return token.value;
      } catch (error) {
        logI18n('error', 'logs.auth.refreshFailed', error);
        return null;
      } finally {
        refreshInFlight = null;
      }
    })();

    return refreshInFlight;
  };

  /**
   * Renew the token a few minutes BEFORE it expires, so a long-running rater
   * never hits a 401 in the first place. Reactive refresh (in the axios
   * interceptor) stays as the safety net for sleep/suspend, where the timer
   * does not fire on time.
   */
  const scheduleTokenRefresh = () => {
    if (refreshTimer) {
      clearTimeout(refreshTimer);
      refreshTimer = null;
    }
    if (typeof window === 'undefined') return;

    const exp = tokenParsed.value?.exp;
    if (!exp) return;

    const msUntilExpiry = exp * 1000 - Date.now();
    // Renew at T-5min, but never sleep less than 10s (guards against a tight
    // loop if the clock is skewed or the token is already near-dead).
    const delay = Math.max(10_000, msUntilExpiry - REFRESH_LEAD_MS);

    refreshTimer = window.setTimeout(() => {
      refreshTimer = null;
      if (token.value) refreshAccessToken();
    }, delay);
  };

  const login = async (username, password) => {
    // Use backend proxy endpoint for authentication (avoids CORS issues)
    const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
    const loginUrl = `${baseUrl}/auth/authentik/login`;

    try {
      const response = await axios.post(loginUrl, {
        username,
        password
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      // Store tokens and roles
      const {
        access_token,
        refresh_token,
        id_token,
        llars_roles: roles,
        referral_target_scenario_id: referralTarget
      } = response.data;

      token.value = access_token;
      refreshToken.value = refresh_token;
      idToken.value = id_token;
      llarsRoles.value = roles || [];

      // Persist the referral-bound landing scenario so the router can
      // shortcut single-scenario raters on every subsequent navigation
      // without re-asking the backend. Cleared on logout (see logout()).
      try {
        if (referralTarget != null) {
          localStorage.setItem('llars-referral-target-scenario', String(referralTarget))
        } else {
          localStorage.removeItem('llars-referral-target-scenario')
        }
      } catch (e) {
        // ignore (e.g., Safari private mode / blocked storage)
      }

      // Parse token
      tokenParsed.value = parseJwt(access_token);
      if (!tokenParsed.value) {
        logI18n('error', 'logs.auth.parseTokenFailed');
      }

      // Store in sessionStorage (with safe fallback)
      setAuthStorageItem(AUTH_STORAGE_KEYS.token, access_token);
      setAuthStorageItem(AUTH_STORAGE_KEYS.refreshToken, refresh_token);
      if (id_token) {
        setAuthStorageItem(AUTH_STORAGE_KEYS.idToken, id_token);
      }
      // Store LLARS roles for router guard access
      setAuthStorageItem(AUTH_STORAGE_KEYS.roles, JSON.stringify(roles || []));

      // Store username in localStorage for App.vue compatibility
      try {
        if (tokenParsed.value?.preferred_username) {
          localStorage.setItem('username', tokenParsed.value.preferred_username);
        } else if (username) {
          localStorage.setItem('username', username);
        }
      } catch (e) {
        // ignore (e.g., Safari private mode / blocked storage)
      }

      // Matomo User-ID tracking (optional)
      const matomoUserId = tokenParsed.value?.preferred_username || tokenParsed.value?.sub || username;
      if (matomoUserId) {
        matomoSetUserId(matomoUserId);
      }

      // Arm the silent renewal for this session.
      scheduleTokenRefresh();

      // Ensure permission cache is refreshed for the newly logged-in user
      try {
        const perms = usePermissions();
        perms.clearPermissions();
        await perms.fetchPermissions(true);
      } catch (e) {
        // ignore - UI will refetch on demand
      }

      // Fetch profile metadata (e.g., avatar_seed) immediately so UI (AppBar) stays consistent
      try {
        await fetchUserProfile();
      } catch (e) {
        // ignore - avatar can fall back to username-based seed
      }

      // Fetch user settings (collab_color) immediately after login
      try {
        await fetchUserSettings();
      } catch (e) {
        // ignore - color can fall back to default
      }

      return { success: true };
    } catch (error) {
      logI18n('error', 'logs.auth.loginError', error);

      let errorMessage = 'Ein unerwarteter Fehler ist aufgetreten.';

      if (error.response) {
        const status = error.response.status;
        if (status === 401) {
          errorMessage = 'Ungültiger Benutzername oder Passwort.';
        } else if (status === 400) {
          errorMessage = 'Fehlerhafte Anfrage. Bitte überprüfen Sie Ihre Eingaben.';
        } else {
          errorMessage = error.response.data.error_description || error.response.statusText;
        }
      } else if (error.request) {
        errorMessage = 'Keine Verbindung zum Server. Bitte überprüfen Sie Ihre Netzwerkverbindung.';
      }

      return { success: false, error: errorMessage };
    }
  };

  const logout = () => {
    // Kill any pending renewal first: a timer firing after logout would mint a
    // fresh token for a user who just signed out.
    if (refreshTimer) {
      clearTimeout(refreshTimer);
      refreshTimer = null;
    }
    refreshInFlight = null;

    token.value = null;
    refreshToken.value = null;
    idToken.value = null;
    tokenParsed.value = null;
    llarsRoles.value = [];
    avatarSeed.value = null;
    avatarUrl.value = null;
    avatarChangesLeft.value = null;
    collabColor.value = null;
    consoleLogsEnabled.value = false;
    setConsoleLogsEnabled(false);

    clearStoredTokens();

    // Drop the referral-landing hint so the next user on this browser
    // (e.g. shared workstation) doesn't accidentally get redirected
    // into someone else's scenario.
    try {
      localStorage.removeItem('llars-referral-target-scenario')
    } catch (e) {
      // ignore
    }

    // Matomo: end user association
    matomoResetUserId();

    // Clear cached permissions/roles (shared state)
    try {
      const perms = usePermissions();
      perms.clearPermissions();
    } catch (e) {
      // ignore
    }
  };

  const getToken = () => token.value;

  return {
    isAuthenticated,
    userRoles,
    isAdmin,
    tokenParsed,
    avatarSeed,
    avatarUrl,
    avatarChangesLeft,
    collabColor,
    consoleLogsEnabled,
    login,
    applyTokenBundle,
    logout,
    getToken,
    isTokenExpired,
    refreshAccessToken,
    scheduleTokenRefresh,
    fetchUserProfile,
    fetchUserSettings,
    updateCollabColor,
    uploadAvatar,
    regenerateAvatar,
    resetAvatar
  };
};
