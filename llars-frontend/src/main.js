/**
 * main.js
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Plugins
import { registerPlugins, vuetify } from '@/plugins'
import router from '@/router.js'
import axios from 'axios'

// Global Styles
import '@/styles/global.css'

// Components
import App from './App.vue'

// Global LLARS Components
import LBtn from '@/components/common/LBtn.vue'
import LIcon from '@/components/common/LIcon.vue'
import LIconBtn from '@/components/common/LIconBtn.vue'
import LInfoTooltip from '@/components/common/LInfoTooltip.vue'
import LTooltip from '@/components/common/LTooltip.vue'
import LActionGroup from '@/components/common/LActionGroup.vue'
import LSlider from '@/components/common/LSlider.vue'
import LTag from '@/components/common/LTag.vue'
import LCard from '@/components/common/LCard.vue'
import LCardSkeleton from '@/components/common/LCardSkeleton.vue'
import LSkeleton from '@/components/common/LSkeleton.vue'
import LStatCard from '@/components/common/LStatCard.vue'
import LTabs from '@/components/common/LTabs.vue'
import LAvatar from '@/components/common/LAvatar.vue'
import LChart from '@/components/common/LChart.vue'
import LGauge from '@/components/common/LGauge.vue'
import LThemeToggle from '@/components/common/LThemeToggle.vue'
import LLanguageToggle from '@/components/common/LLanguageToggle.vue'
import LEvaluationLayout from '@/components/common/LEvaluationLayout.vue'
import LEvaluationStatus from '@/components/common/LEvaluationStatus.vue'
import LMessage from '@/components/common/LMessage.vue'
import LMessageList from '@/components/common/LMessageList.vue'
import LUserSearch from '@/components/common/LUserSearch.vue'
import LLoading from '@/components/common/LLoading.vue'
import { initMatomo } from '@/plugins/llars-metrics'
import { useAuth } from '@/composables/useAuth'
import { initAppTheme } from '@/composables/useAppTheme'
import { initLanguage } from '@/composables/useLanguage'
import i18n from '@/i18n'

// Composables
import { createApp } from 'vue'

const app = createApp(App)

// Register Vuetify and other plugins
registerPlugins(app)

// Initialize theme early (before mount, after Vuetify is ready)
// This ensures the correct theme is applied immediately
initAppTheme(vuetify)

// Initialize language (sets HTML lang attribute)
initLanguage()

// Register i18n for translations
app.use(i18n)

// Register global LLARS components
app.component('LBtn', LBtn)
app.component('LIcon', LIcon)
app.component('LIconBtn', LIconBtn)
app.component('LInfoTooltip', LInfoTooltip)
app.component('LTooltip', LTooltip)
app.component('LActionGroup', LActionGroup)
app.component('LSlider', LSlider)
app.component('LTag', LTag)
app.component('LCard', LCard)
app.component('LCardSkeleton', LCardSkeleton)
app.component('LSkeleton', LSkeleton)
app.component('LStatCard', LStatCard)
app.component('LTabs', LTabs)
app.component('LAvatar', LAvatar)
app.component('LChart', LChart)
app.component('LGauge', LGauge)
app.component('LThemeToggle', LThemeToggle)
app.component('LLanguageToggle', LLanguageToggle)
app.component('LEvaluationLayout', LEvaluationLayout)
app.component('LEvaluationStatus', LEvaluationStatus)
app.component('LMessage', LMessage)
app.component('LMessageList', LMessageList)
app.component('LUserSearch', LUserSearch)
app.component('LLoading', LLoading)

// Set default Axios headers
axios.defaults.headers.common['Content-Type'] = 'application/json'
// Ensure relative API calls work across dev/prod origins.
const rawApiBase = import.meta.env.VITE_API_BASE_URL || (typeof window !== 'undefined' ? window.location.origin : '')
const trimmedApiBase = String(rawApiBase || '').replace(/\/+$/, '')
axios.defaults.baseURL = trimmedApiBase.endsWith('/api')
  ? trimmedApiBase.slice(0, -4)
  : (trimmedApiBase || (typeof window !== 'undefined' ? window.location.origin : ''))

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
