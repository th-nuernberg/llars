import { ref, computed } from 'vue';
import axios from 'axios';

// Auth state
const token = ref(null);
const refreshToken = ref(null);
const idToken = ref(null);
const tokenParsed = ref(null);

// Load tokens from sessionStorage on init
const loadTokensFromStorage = () => {
  token.value = sessionStorage.getItem('kc_token');
  refreshToken.value = sessionStorage.getItem('kc_refreshToken');
  idToken.value = sessionStorage.getItem('kc_idToken');

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
    return tokenParsed.value?.realm_access?.roles || [];
  });

  const isAdmin = computed(() => {
    return userRoles.value.includes('admin');
  });

  const login = async (username, password) => {
    const keycloakUrl = import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost:55090';
    const realm = import.meta.env.VITE_KEYCLOAK_REALM || 'llars';
    const clientId = import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'llars-frontend';

    const tokenUrl = `${keycloakUrl}/realms/${realm}/protocol/openid-connect/token`;

    const params = new URLSearchParams();
    params.append('client_id', clientId);
    params.append('grant_type', 'password');
    params.append('username', username);
    params.append('password', password);
    params.append('scope', 'openid');

    try {
      const response = await axios.post(tokenUrl, params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });

      // Store tokens
      const { access_token, refresh_token, id_token } = response.data;

      token.value = access_token;
      refreshToken.value = refresh_token;
      idToken.value = id_token;

      // Parse token
      try {
        tokenParsed.value = JSON.parse(atob(access_token.split('.')[1]));
      } catch (e) {
        console.error('Failed to parse token:', e);
      }

      // Store in sessionStorage
      sessionStorage.setItem('kc_token', access_token);
      sessionStorage.setItem('kc_refreshToken', refresh_token);
      if (id_token) {
        sessionStorage.setItem('kc_idToken', id_token);
      }

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

    sessionStorage.removeItem('kc_token');
    sessionStorage.removeItem('kc_refreshToken');
    sessionStorage.removeItem('kc_idToken');
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
