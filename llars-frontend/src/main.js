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
// MDI Font for native MDI icons (used when bypassing llars icon set)
import '@mdi/font/css/materialdesignicons.css'

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
import LLabelButton from '@/components/common/LLabelButton.vue'
import LUserOrigin from '@/components/common/LUserOrigin.vue'
import LOriginLegend from '@/components/common/LOriginLegend.vue'
import LCard from '@/components/common/LCard.vue'
import LCardSkeleton from '@/components/common/LCardSkeleton.vue'
import LSkeleton from '@/components/common/LSkeleton.vue'
import LStatCard from '@/components/common/LStatCard.vue'
import LTabs from '@/components/common/LTabs.vue'
import LAvatar from '@/components/common/LAvatar.vue'
import LChart from '@/components/common/LChart.vue'
import LGauge from '@/components/common/LGauge.vue'
import LThemeToggle from '@/components/common/LThemeToggle.vue'
import LViewToggle from '@/components/common/LViewToggle.vue'
import LListTable from '@/components/common/LListTable.vue'
import LLanguageToggle from '@/components/common/LLanguageToggle.vue'
import LEvaluationLayout from '@/components/common/LEvaluationLayout.vue'
import LEvaluationStatus from '@/components/common/LEvaluationStatus.vue'
import LMessage from '@/components/common/LMessage.vue'
import LMessageList from '@/components/common/LMessageList.vue'
import LUserSearch from '@/components/common/LUserSearch.vue'
import LLoading from '@/components/common/LLoading.vue'
import LCheckbox from '@/components/common/LCheckbox.vue'
import LRadio from '@/components/common/LRadio.vue'
import LRadioGroup from '@/components/common/LRadioGroup.vue'
import LSwitch from '@/components/common/LSwitch.vue'
import LAIFieldButton from '@/components/common/LAIFieldButton.vue'
import LlarsBrand from '@/components/common/LlarsBrand.vue'
import LShareDialog from '@/components/common/LShareDialog.vue'
import { initMatomo } from '@/plugins/llars-metrics'
import { useAuth } from '@/composables/useAuth'
import { initAppTheme } from '@/composables/useAppTheme'
import { initLanguage } from '@/composables/useLanguage'
import i18n from '@/i18n'
import { logI18n } from '@/utils/logI18n'
import { installConsoleController } from '@/utils/consoleController'

// Composables
import { createApp } from 'vue'

// Suppress console output in production (before anything else logs)
installConsoleController()

const app = createApp(App)
const CHUNK_RELOAD_STORAGE_KEY = 'llars:chunk-reload-at'
const CHUNK_RELOAD_COOLDOWN_MS = 30_000

function isDynamicImportLoadError(error) {
  const message = String(error?.message || error || '').toLowerCase()
  return (
    message.includes('failed to fetch dynamically imported module') ||
    message.includes('importing a module script failed') ||
    message.includes('failed to load module script') ||
    message.includes('loading chunk')
  )
}

function reloadForChunkMismatch(reason = 'unknown') {
  if (typeof window === 'undefined') {
    return false
  }

  const now = Date.now()
  const lastReloadAt = Number(window.sessionStorage.getItem(CHUNK_RELOAD_STORAGE_KEY) || '0')
  if (Number.isFinite(lastReloadAt) && now - lastReloadAt < CHUNK_RELOAD_COOLDOWN_MS) {
    return false
  }

  window.sessionStorage.setItem(CHUNK_RELOAD_STORAGE_KEY, String(now))
  console.warn('[LLARS] Reloading app after dynamic import mismatch:', reason)
  const currentUrl = `${window.location.pathname}${window.location.search}${window.location.hash}`
  window.location.replace(currentUrl)
  return true
}

if (typeof window !== 'undefined') {
  window.addEventListener('vite:preloadError', event => {
    const preloadError = event?.payload || event?.error || event
    if (!isDynamicImportLoadError(preloadError)) {
      return
    }

    event?.preventDefault?.()
    reloadForChunkMismatch('vite:preloadError')
  })
}

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
app.component('LLabelButton', LLabelButton)
app.component('LUserOrigin', LUserOrigin)
app.component('LOriginLegend', LOriginLegend)
app.component('LCard', LCard)
app.component('LCardSkeleton', LCardSkeleton)
app.component('LSkeleton', LSkeleton)
app.component('LStatCard', LStatCard)
app.component('LTabs', LTabs)
app.component('LAvatar', LAvatar)
app.component('LChart', LChart)
app.component('LGauge', LGauge)
app.component('LThemeToggle', LThemeToggle)
app.component('LViewToggle', LViewToggle)
app.component('LListTable', LListTable)
app.component('LLanguageToggle', LLanguageToggle)
app.component('LEvaluationLayout', LEvaluationLayout)
app.component('LEvaluationStatus', LEvaluationStatus)
app.component('LMessage', LMessage)
app.component('LMessageList', LMessageList)
app.component('LUserSearch', LUserSearch)
app.component('LLoading', LLoading)
app.component('LCheckbox', LCheckbox)
app.component('LRadio', LRadio)
app.component('LRadioGroup', LRadioGroup)
app.component('LSwitch', LSwitch)
app.component('LAIFieldButton', LAIFieldButton)
app.component('LlarsBrand', LlarsBrand)
app.component('LShareDialog', LShareDialog)

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

// Re-arm silent renewal for a session restored from storage (page reload).
// login() arms it for fresh logins; without this a reload would leave the tab
// with no scheduled refresh and it would die at the 60-minute mark again.
auth.scheduleTokenRefresh()

// Token refresh interceptor.
//
// INCIDENT 2026-07-29: this used to log the user out on the FIRST 401, with no
// attempt to renew — even though a refresh_token was sitting in storage the
// whole time. Raters were ejected mid-study every hour. Now a 401 first tries
// exactly one silent refresh and replays the original request; only if the
// refresh itself is rejected (revoked/expired) do we fall back to logging out.
axios.interceptors.response.use(
  response => response,
  async error => {
    const original = error.config || {}

    // Don't redirect for login requests - let the login form handle auth errors
    const isLoginRequest = original.url?.includes('/auth/') &&
                           original.url?.includes('/login');
    // The refresh call itself must never recurse through this handler.
    const isRefreshRequest = original._skipAuthRefresh === true ||
                             original.url?.includes('/auth/authentik/refresh');

    if (error.response?.status === 401 && !isLoginRequest && !isRefreshRequest) {
      // `_retried` bounds this to one attempt per request: if the replay also
      // 401s, the new token is genuinely not accepted and we stop.
      if (!original._retried) {
        original._retried = true
        const newToken = await auth.refreshAccessToken()
        if (newToken) {
          original.headers = { ...(original.headers || {}), Authorization: `Bearer ${newToken}` }
          return axios(original)
        }
      }

      logI18n('log', 'logs.main.tokenExpiredRedirect')
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

router.onError((error) => {
  if (!isDynamicImportLoadError(error)) {
    return
  }

  const recovered = reloadForChunkMismatch('router:onError')
  if (!recovered) {
    console.error('[LLARS] Dynamic import failed and auto-reload cooldown is active:', error)
  }
})

// Matomo (Analytics)
initMatomo({ router })

// Mount the app
app.mount('#app')

logI18n('log', 'logs.main.appInitialized')
