import { ref, computed } from 'vue';
import axios from 'axios';
import { matomoResetUserId, matomoSetUserId } from '@/plugins/llars-metrics';
import { usePermissions } from '@/composables/usePermissions';
import { decodeJwtPayload } from '@/utils/jwt';
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
const avatarSeed = ref(null);
const collabColor = ref(null);

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
      console.error('Failed to parse stored roles:', e);
      llarsRoles.value = [];
    }
  }

  // Load avatar seed from storage
  const storedAvatarSeed = getAuthStorageItem(AUTH_STORAGE_KEYS.avatarSeed);
  if (storedAvatarSeed) {
    avatarSeed.value = storedAvatarSeed;
  }

  // Load collab color from storage
  const storedCollabColor = getAuthStorageItem(AUTH_STORAGE_KEYS.collabColor);
  if (storedCollabColor) {
    collabColor.value = storedCollabColor;
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
      avatarSeed.value = null;
      collabColor.value = null;
      clearStoredTokens();
    }
  }
};

// Fetch user profile to get avatar_seed
const fetchUserProfile = async () => {
  if (!token.value) return null;

  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080';
    const response = await axios.get(`${baseUrl}/auth/authentik/me`, {
      headers: {
        Authorization: `Bearer ${token.value}`
      }
    });

    const { avatar_seed } = response.data;
    if (avatar_seed) {
      avatarSeed.value = avatar_seed;
      setAuthStorageItem(AUTH_STORAGE_KEYS.avatarSeed, avatar_seed);
    }

    return response.data;
  } catch (e) {
    console.error('Failed to fetch user profile:', e);
    return null;
  }
};

// Fetch user settings (collab_color, avatar_seed)
const fetchUserSettings = async () => {
  if (!token.value) return null;

  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080';
    const response = await axios.get(`${baseUrl}/api/users/me/settings`, {
      headers: {
        Authorization: `Bearer ${token.value}`
      }
    });

    const { collab_color, avatar_seed } = response.data;

    if (collab_color) {
      collabColor.value = collab_color;
      setAuthStorageItem(AUTH_STORAGE_KEYS.collabColor, collab_color);
    }

    if (avatar_seed) {
      avatarSeed.value = avatar_seed;
      setAuthStorageItem(AUTH_STORAGE_KEYS.avatarSeed, avatar_seed);
    }

    return response.data;
  } catch (e) {
    console.error('Failed to fetch user settings:', e);
    return null;
  }
};

// Update user's collab color
const updateCollabColor = async (color) => {
  if (!token.value) return false;

  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080';
    const response = await axios.patch(`${baseUrl}/api/users/me/settings`, {
      collab_color: color
    }, {
      headers: {
        Authorization: `Bearer ${token.value}`
      }
    });

    if (response.data.success) {
      collabColor.value = color;
      if (color) {
        setAuthStorageItem(AUTH_STORAGE_KEYS.collabColor, color);
      } else {
        // Remove from storage if null
        setAuthStorageItem(AUTH_STORAGE_KEYS.collabColor, '');
      }
      return true;
    }
    return false;
  } catch (e) {
    console.error('Failed to update collab color:', e);
    return false;
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
      tokenParsed.value = parseJwt(access_token);
      if (!tokenParsed.value) {
        console.error('Failed to parse token');
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
    avatarSeed.value = null;
    collabColor.value = null;

    clearStoredTokens();

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
    collabColor,
    login,
    logout,
    getToken,
    isTokenExpired,
    fetchUserProfile,
    fetchUserSettings,
    updateCollabColor
  };
};
