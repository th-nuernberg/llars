import { ref, computed } from 'vue';
import axios from 'axios';
import { matomoResetUserId, matomoSetUserId } from '@/plugins/llars-metrics';
import {
  AUTH_STORAGE_KEYS,
  clearAuthStorage,
  getAuthStorageItem,
  setAuthStorageItem
} from '@/utils/authStorage';

// Auth state
const token = ref(null);
const refreshToken = ref(null);
const idToken = ref(null);
const tokenParsed = ref(null);
const llarsRoles = ref([]);

const parseJwt = (jwtToken) => {
  if (!jwtToken) return null;
  try {
    const parts = jwtToken.split('.');
    if (parts.length < 2) return null;
    return JSON.parse(atob(parts[1]));
  } catch (e) {
    return null;
  }
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
      console.error('Failed to parse stored roles:', e);
      llarsRoles.value = [];
    }
  }

  if (token.value) {
    tokenParsed.value = parseJwt(token.value);
    if (!tokenParsed.value) {
      console.error('Failed to parse token');
    }
    if (isTokenExpired(token.value, 0)) {
      // Token expired → treat as logged out (avoids getting stuck with stale tokens)
      token.value = null;
      refreshToken.value = null;
      idToken.value = null;
      tokenParsed.value = null;
      llarsRoles.value = [];
      clearStoredTokens();
    }
  }
};

// Initialize on load
loadTokensFromStorage();

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
    // Check for 'admin' role or 'authentik Admins' group
    return userRoles.value.includes('admin') ||
           userRoles.value.includes('authentik Admins');
  });

  const login = async (username, password) => {
    // Use backend proxy endpoint for authentication (avoids CORS issues)
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080';
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
      const { access_token, refresh_token, id_token, llars_roles: roles } = response.data;

      token.value = access_token;
      refreshToken.value = refresh_token;
      idToken.value = id_token;
      llarsRoles.value = roles || [];

      // Parse token
      try {
        tokenParsed.value = JSON.parse(atob(access_token.split('.')[1]));
      } catch (e) {
        console.error('Failed to parse token:', e);
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
      if (tokenParsed.value?.preferred_username) {
        localStorage.setItem('username', tokenParsed.value.preferred_username);
      } else if (username) {
        localStorage.setItem('username', username);
      }

      // Matomo User-ID tracking (optional)
      const matomoUserId = tokenParsed.value?.preferred_username || tokenParsed.value?.sub || username;
      if (matomoUserId) {
        matomoSetUserId(matomoUserId);
      }

      return { success: true };
    } catch (error) {
      console.error('Login error:', error);

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
    token.value = null;
    refreshToken.value = null;
    idToken.value = null;
    tokenParsed.value = null;
    llarsRoles.value = [];

    clearStoredTokens();

    // Matomo: end user association
    matomoResetUserId();
  };

  const getToken = () => token.value;

  return {
    isAuthenticated,
    userRoles,
    isAdmin,
    tokenParsed,
    login,
    logout,
    getToken,
    isTokenExpired
  };
};
