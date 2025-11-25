/**
 * main.js
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Plugins
import { registerPlugins } from '@/plugins'
import router from '@/router.js'
import axios from 'axios'

// Components
import App from './App.vue'

// Composables
import { createApp } from 'vue'

const app = createApp(App)

// Register Vuetify and other plugins
registerPlugins(app)

// Set default Axios headers
axios.defaults.headers.common['Content-Type'] = 'application/json'

// Setup Axios interceptor for adding Bearer token to all requests
axios.interceptors.request.use(config => {
  const token = sessionStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, error => {
  return Promise.reject(error)
})

// Token refresh interceptor - redirect to login if token expires
axios.interceptors.response.use(
  response => response,
  async error => {
    // Don't redirect for login requests - let the login form handle auth errors
    const isLoginRequest = error.config?.url?.includes('/auth/') &&
                           error.config?.url?.includes('/login');

    // If 401 Unauthorized on non-login requests, redirect to login
    if (error.response?.status === 401 && !isLoginRequest) {
      console.log('Token expired or invalid, redirecting to login')
      // Clear tokens
      sessionStorage.removeItem('auth_token')
      sessionStorage.removeItem('auth_refreshToken')
      sessionStorage.removeItem('auth_idToken')
      sessionStorage.removeItem('auth_llars_roles')
      // Redirect to login
      window.location.href = '/login'
    }

    return Promise.reject(error)
  }
)

// Use router
app.use(router)

// Mount the app
app.mount('#app')

console.log('App initialized with custom authentication')
