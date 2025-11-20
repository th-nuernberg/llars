/**
 * main.js
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Plugins
import { registerPlugins } from '@/plugins'
import router from '@/router.js'
import VueKeyCloak from '@dsb-norge/vue-keycloak-js'
import axios from 'axios'

// Components
import App from './App.vue'

// Composables
import { createApp } from 'vue'

// Keycloak Configuration
import keycloakConfigModule from './keycloak.config.js'

const app = createApp(App)

// Register Vuetify and other plugins
registerPlugins(app)

// Keycloak Plugin Configuration
app.use(VueKeyCloak, {
  config: keycloakConfigModule.config,
  init: keycloakConfigModule.init,
  onReady: (keycloak) => {
    console.log('Keycloak initialized successfully')
    console.log('Authenticated:', keycloak.authenticated)

    // Setup Axios interceptor for adding Bearer token to all requests
    axios.interceptors.request.use(config => {
      if (keycloak.authenticated && keycloak.token) {
        config.headers.Authorization = `Bearer ${keycloak.token}`
      }
      return config
    }, error => {
      return Promise.reject(error)
    })

    // Token refresh interceptor - refresh token if it's about to expire
    axios.interceptors.response.use(
      response => response,
      async error => {
        const originalRequest = error.config

        // If 401 Unauthorized and we have a token, try to refresh
        if (error.response?.status === 401 && keycloak.authenticated && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            // Try to update token (refresh if expires in less than 30 seconds)
            const refreshed = await keycloak.updateToken(30)
            if (refreshed) {
              console.log('Token refreshed successfully')
              // Retry the original request with new token
              originalRequest.headers.Authorization = `Bearer ${keycloak.token}`
              return axios(originalRequest)
            }
          } catch (refreshError) {
            console.error('Token refresh failed:', refreshError)
            // Redirect to login if refresh fails
            keycloak.login()
            return Promise.reject(refreshError)
          }
        }

        return Promise.reject(error)
      }
    )

    // Use router after Keycloak is ready
    app.use(router)

    // Mount the app after Keycloak is initialized
    app.mount('#app')
  },
  onInitError: (error) => {
    console.error('Keycloak initialization failed:', error)
    // Still mount the app even if Keycloak fails (fallback to login page)
    app.use(router)
    app.mount('#app')
  }
})
