import { ref, computed } from 'vue';
import axios from 'axios';

// Auth state
const token = ref(null);
const refreshToken = ref(null);
const idToken = ref(null);
const tokenParsed = ref(null);
const llarsRoles = ref([]);

// Load tokens from sessionStorage on init
const loadTokensFromStorage = () => {
  token.value = sessionStorage.getItem('auth_token');
  refreshToken.value = sessionStorage.getItem('auth_refreshToken');
  idToken.value = sessionStorage.getItem('auth_idToken');

  // Load LLARS roles from storage
  const storedRoles = sessionStorage.getItem('auth_llars_roles');
  if (storedRoles) {
    try {
      llarsRoles.value = JSON.parse(storedRoles);
    } catch (e) {
      console.error('Failed to parse stored roles:', e);
      llarsRoles.value = [];
    }
  }

  if (token.value) {
    try {
      tokenParsed.value = JSON.parse(atob(token.value.split('.')[1]));
    } catch (e) {
      console.error('Failed to parse token:', e);
    }
  }
};

// Initialize on load
loadTokensFromStorage();

export const useAuth = () => {
  const isAuthenticated = computed(() => !!token.value);

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

      // Store in sessionStorage
      sessionStorage.setItem('auth_token', access_token);
      sessionStorage.setItem('auth_refreshToken', refresh_token);
      if (id_token) {
        sessionStorage.setItem('auth_idToken', id_token);
      }
      // Store LLARS roles for router guard access
      sessionStorage.setItem('auth_llars_roles', JSON.stringify(roles || []));

      // Store username in localStorage for App.vue compatibility
      if (tokenParsed.value?.preferred_username) {
        localStorage.setItem('username', tokenParsed.value.preferred_username);
      } else if (username) {
        localStorage.setItem('username', username);
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

    sessionStorage.removeItem('auth_token');
    sessionStorage.removeItem('auth_refreshToken');
    sessionStorage.removeItem('auth_idToken');
    sessionStorage.removeItem('auth_llars_roles');

    // Remove username from localStorage
    localStorage.removeItem('username');
  };

  const getToken = () => token.value;

  return {
    isAuthenticated,
    userRoles,
    isAdmin,
    tokenParsed,
    login,
    logout,
    getToken
  };
};
