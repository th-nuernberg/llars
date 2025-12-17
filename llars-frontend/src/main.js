/**
 * main.js
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Plugins
import { registerPlugins } from '@/plugins'
import router from '@/router.js'
import axios from 'axios'

// Global Styles
import '@/styles/global.css'

// Components
import App from './App.vue'

// Global LLARS Components
import LBtn from '@/components/common/LBtn.vue'
import LIconBtn from '@/components/common/LIconBtn.vue'
import LTag from '@/components/common/LTag.vue'
import LCard from '@/components/common/LCard.vue'
import LTabs from '@/components/common/LTabs.vue'
import LAvatar from '@/components/common/LAvatar.vue'
import { initMatomo } from '@/plugins/llars-metrics'
import { useAuth } from '@/composables/useAuth'

// Composables
import { createApp } from 'vue'

const app = createApp(App)

// Register Vuetify and other plugins
registerPlugins(app)

// Register global LLARS components
app.component('LBtn', LBtn)
app.component('LIconBtn', LIconBtn)
app.component('LTag', LTag)
app.component('LCard', LCard)
app.component('LTabs', LTabs)
app.component('LAvatar', LAvatar)

// Set default Axios headers
axios.defaults.headers.common['Content-Type'] = 'application/json'

const auth = useAuth()

// Setup Axios interceptor for adding Bearer token to all requests
axios.interceptors.request.use(config => {
  const token = auth.getToken()
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
      auth.logout()
      // Redirect to login
      const current = `${window.location.pathname}${window.location.search}${window.location.hash}`
      window.location.href = `/login?redirect=${encodeURIComponent(current)}`
    }

    return Promise.reject(error)
  }
)

// Use router
app.use(router)

// Matomo (Analytics)
initMatomo({ router })

// Mount the app
app.mount('#app')

console.log('App initialized with custom authentication')
