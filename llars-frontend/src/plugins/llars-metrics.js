import { ref } from 'vue'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'
import { decodeJwtPayload } from '@/utils/jwt'

const DEFAULT_ANALYTICS_CONFIG = Object.freeze({
  matomo_enabled: true,
  matomo_base_url: '/analytics/',
  matomo_site_id: 1,
  include_query: false,
  disable_cookies: true,  // Privacy: No cookies by default
  require_consent: true,  // Privacy: Require user consent before tracking
  require_cookie_consent: false,
  set_user_id: false,  // Privacy: Don't track user ID by default
  dimension_route_id: 0,
  dimension_module_id: 0,
  dimension_entity_id: 0,
  dimension_view_id: 0,
  dimension_role_id: 0,
  track_clicks: true,
  track_hovers: false,
  hover_min_ms: 400,
  hover_sample_rate: 1,
  heartbeat_enabled: true,
  heartbeat_seconds: 15
})

const CONSENT_STORAGE_KEY = 'llars_analytics_consent'
const CONSENT_VALUES = Object.freeze({
  granted: 'granted',
  denied: 'denied'
})

const safeStorageGet = (key) => {
  if (typeof window === 'undefined') return null
  try {
    return window.localStorage?.getItem(key) ?? null
  } catch (e) {
    return null
  }
}

const safeStorageSet = (key, value) => {
  if (typeof window === 'undefined') return false
  try {
    window.localStorage?.setItem(key, value)
    return true
  } catch (e) {
    return false
  }
}

const safeStorageRemove = (key) => {
  if (typeof window === 'undefined') return
  try {
    window.localStorage?.removeItem(key)
  } catch (e) {
    // ignore
  }
}

const loadConsentState = () => {
  const stored = safeStorageGet(CONSENT_STORAGE_KEY)
  if (stored === CONSENT_VALUES.granted || stored === CONSENT_VALUES.denied) {
    return stored
  }
  return null
}

let runtimeConfig = { ...DEFAULT_ANALYTICS_CONFIG }
const analyticsConfigRef = ref({ ...runtimeConfig })
const analyticsConsentRef = ref(loadConsentState())
let listenersInstalled = false
let hasTrackedInitialPageView = false
let routerRef = null

const parseJwt = (jwtToken) => {
  return decodeJwtPayload(jwtToken)
}

const resolveUserId = () => {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  const payload = parseJwt(token)
  let storedUsername = null
  try {
    storedUsername = localStorage.getItem('username')
  } catch (e) {
    storedUsername = null
  }
  return payload?.preferred_username || payload?.sub || storedUsername
}

const computeMatomoBaseUrl = (baseUrlSetting) => {
  const configured = String(baseUrlSetting || '').trim()
  if (configured) {
    if (configured.startsWith('http://') || configured.startsWith('https://')) {
      return configured.endsWith('/') ? configured : `${configured}/`
    }
    if (configured.startsWith('/')) {
      return `${window.location.origin}${configured.endsWith('/') ? configured : `${configured}/`}`
    }
    return `${window.location.origin}/${configured.endsWith('/') ? configured : `${configured}/`}`
  }

  return `${window.location.origin}/analytics/`
}

const ensureMatomoScriptLoaded = (scriptUrl) => {
  if (document.querySelector(`script[data-matomo-src="${scriptUrl}"]`)) return

  const script = document.createElement('script')
  script.async = true
  script.src = scriptUrl
  script.setAttribute('data-matomo-src', scriptUrl)
  document.head.appendChild(script)
}

const buildRouteLabel = (route) => {
  if (!route) return 'unknown'
  return String(route.name || route.path || 'unknown')
}

const buildCustomUrl = (route, includeQuery) => {
  const raw = includeQuery ? route?.fullPath : route?.path
  const path = String(raw || window.location.pathname || '/')
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  try {
    return `${window.location.origin}${normalizedPath}`
  } catch (e) {
    return normalizedPath
  }
}

const buildDocumentTitle = (route) => {
  const metaTitle = route?.meta?.title
  if (metaTitle) return String(metaTitle)
  if (route?.name) return String(route.name)
  return String(route?.path || document.title || 'LLARS')
}

const findClickableTarget = (eventTarget) => {
  if (!eventTarget || !(eventTarget instanceof Element)) return null
  return eventTarget.closest('button, a, [role="button"], .v-btn')
}

const sanitizeLabel = (label) => {
  if (!label) return ''
  const trimmed = String(label).replace(/\s+/g, ' ').trim()
  if (!trimmed) return ''

  const withoutEmails = trimmed.replace(
    /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi,
    '<email>'
  )
  const withoutUrls = withoutEmails.replace(/https?:\/\/\S+/gi, '<url>')
  const withoutLongNumbers = withoutUrls.replace(/\b\d{4,}\b/g, '<num>')
  return withoutLongNumbers.slice(0, 120)
}

const getDescribedByText = (el) => {
  if (!el?.getAttribute) return ''
  const describedById = el.getAttribute('aria-describedby')
  if (!describedById) return ''
  const describedBy = document.getElementById(describedById)
  if (!describedBy) return ''
  return sanitizeLabel(describedBy.textContent || describedBy.innerText)
}

const getIconIdentifier = (el) => {
  if (!el?.querySelector) return ''
  const iconEl =
    el.querySelector('i[class*="mdi-"], span[class*="mdi-"]') ||
    el.querySelector('i[class*="fa-"], span[class*="fa-"]')
  if (!iconEl) return ''
  const classes = Array.from(iconEl.classList || [])
  const knownPrefixes = ['mdi-', 'fa-']
  const match = classes.find((c) => knownPrefixes.some((p) => c.startsWith(p)) && c !== 'mdi' && c !== 'fa')
  return match ? sanitizeLabel(match) : ''
}

const getClickName = (el) => {
  const explicit =
    el.getAttribute('data-matomo-name') ||
    el.getAttribute('data-track') ||
    el.getAttribute('data-testid') ||
    el.getAttribute('aria-label') ||
    el.getAttribute('title') ||
    el.id

  if (explicit) return sanitizeLabel(explicit)

  const describedBy = getDescribedByText(el)
  if (describedBy) return describedBy

  const text = sanitizeLabel(el.innerText)
  if (text) return text

  const icon = getIconIdentifier(el)
  if (icon) return icon

  const firstClass = (el.className || '')
    .toString()
    .split(/\s+/)
    .filter(Boolean)[0]
  return firstClass ? `.${firstClass}` : el.tagName.toLowerCase()
}

const sanitizeDimensionValue = (value) => {
  if (value === null || value === undefined) return ''
  const trimmed = String(value).replace(/\s+/g, ' ').trim()
  if (!trimmed) return ''
  const withoutEmails = trimmed.replace(
    /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi,
    '<email>'
  )
  const withoutUrls = withoutEmails.replace(/https?:\/\/\S+/gi, '<url>')
  return withoutUrls.slice(0, 120)
}

const normalizeRouteValue = (route) => {
  if (route?.name) return sanitizeDimensionValue(route.name)
  const fallbackPath = typeof window !== 'undefined' ? window.location.pathname : ''
  const rawPath = String(route?.path || fallbackPath || '')
  if (!rawPath) return 'unknown'
  const normalized = rawPath
    .split('/')
    .map((part) => {
      if (!part) return ''
      if (/^\d+$/.test(part)) return ':id'
      if (/^[0-9a-f]{8,}$/i.test(part)) return ':id'
      if (/^[0-9a-f-]{12,}$/i.test(part)) return ':id'
      return part
    })
    .join('/')
  return sanitizeDimensionValue(normalized || 'unknown')
}

const inferModuleValue = (route) => {
  const raw = String(route?.name || route?.path || '').toLowerCase()
  if (!raw) return 'general'
  if (raw.includes('prompt')) return 'prompt'
  if (raw.includes('markdown')) return 'markdown'
  if (raw.includes('chat')) return 'chat'
  if (raw.includes('comparison') || raw.includes('rater') || raw.includes('ranker') || raw.includes('evaluation')) {
    return 'evaluation'
  }
  if (raw.includes('judge')) return 'judge'
  if (raw.includes('kaimo')) return 'kaimo'
  if (raw.includes('oncoco')) return 'oncoco'
  if (raw.includes('authenticity')) return 'authenticity'
  if (raw.includes('admin')) return 'admin'
  return 'general'
}

const getRoleValue = () => {
  const raw = getAuthStorageItem(AUTH_STORAGE_KEYS.roles)
  if (!raw) return 'anonymous'
  try {
    const parsed = JSON.parse(raw)
    const list = Array.isArray(parsed) ? parsed : [parsed].filter(Boolean)
    if (!list.length) return 'authenticated'
    if (list.includes('admin')) return 'admin'
    if (list.includes('researcher')) return 'researcher'
    if (list.includes('evaluator')) return 'evaluator'
    if (list.includes('viewer')) return 'evaluator'
    return String(list[0])
  } catch (e) {
    return 'authenticated'
  }
}

const getDimensionIds = (config) => ({
  route: Number(config?.dimension_route_id || 0),
  module: Number(config?.dimension_module_id || 0),
  entity: Number(config?.dimension_entity_id || 0),
  view: Number(config?.dimension_view_id || 0),
  role: Number(config?.dimension_role_id || 0)
})

const buildDefaultDimensions = (config, route) => {
  const targetRoute = route || routerRef?.currentRoute?.value
  return {
    route: normalizeRouteValue(targetRoute),
    module: inferModuleValue(targetRoute),
    role: getRoleValue()
  }
}

const buildDimensionValues = (config, options = {}) => {
  const base = buildDefaultDimensions(config, options.route)
  const merged = { ...base, ...(options.dimensions || {}) }
  const sanitized = {}
  Object.entries(merged).forEach(([key, value]) => {
    const clean = sanitizeDimensionValue(value)
    if (clean) {
      sanitized[key] = clean
    }
  })
  return sanitized
}

const applyCustomDimensions = (config, dimensionValues) => {
  if (!window?._paq || !config) return []
  const ids = getDimensionIds(config)
  const applied = []
  Object.entries(dimensionValues || {}).forEach(([key, value]) => {
    const id = ids[key]
    if (!id || value === undefined || value === null || value === '') return
    window._paq.push(['setCustomDimension', id, String(value)])
    applied.push(id)
  })
  return applied
}

const clearCustomDimensions = (ids) => {
  if (!window?._paq) return
  ids.forEach((id) => {
    window._paq.push(['deleteCustomDimension', id])
  })
}

const requiresConsent = (config) => Boolean(config?.require_consent || config?.require_cookie_consent)

const hasConsent = (config) => {
  if (!requiresConsent(config)) return true
  return analyticsConsentRef.value === CONSENT_VALUES.granted
}

const applyConsentStateToPaq = (config, state) => {
  if (!window?._paq || !requiresConsent(config)) return
  if (config.require_consent) {
    if (state === CONSENT_VALUES.granted) {
      window._paq.push(['setConsentGiven'])
    } else {
      window._paq.push(['forgetConsentGiven'])
    }
  } else if (config.require_cookie_consent) {
    if (state === CONSENT_VALUES.granted) {
      window._paq.push(['rememberCookieConsentGiven'])
    } else {
      window._paq.push(['forgetCookieConsentGiven'])
    }
  }
}

const normalizeConfig = (config) => {
  if (!config || typeof config !== 'object') return { ...DEFAULT_ANALYTICS_CONFIG }

  const merged = { ...DEFAULT_ANALYTICS_CONFIG, ...config }
  merged.matomo_enabled = Boolean(merged.matomo_enabled)
  merged.matomo_base_url = String(merged.matomo_base_url || '/analytics/').trim() || '/analytics/'
  merged.matomo_site_id = Math.max(1, Number(merged.matomo_site_id || 1))
  merged.include_query = Boolean(merged.include_query)
  merged.disable_cookies = Boolean(merged.disable_cookies)
  merged.require_consent = Boolean(merged.require_consent)
  merged.require_cookie_consent = Boolean(merged.require_cookie_consent)
  merged.set_user_id = Boolean(merged.set_user_id)
  merged.dimension_route_id = Math.max(0, Math.round(Number(merged.dimension_route_id || 0)))
  merged.dimension_module_id = Math.max(0, Math.round(Number(merged.dimension_module_id || 0)))
  merged.dimension_entity_id = Math.max(0, Math.round(Number(merged.dimension_entity_id || 0)))
  merged.dimension_view_id = Math.max(0, Math.round(Number(merged.dimension_view_id || 0)))
  merged.dimension_role_id = Math.max(0, Math.round(Number(merged.dimension_role_id || 0)))
  merged.track_clicks = Boolean(merged.track_clicks)
  merged.track_hovers = Boolean(merged.track_hovers)
  merged.hover_min_ms = Math.max(0, Math.round(Number(merged.hover_min_ms ?? 400)))
  merged.hover_sample_rate = Math.min(1, Math.max(0, Number(merged.hover_sample_rate ?? 1)))
  merged.heartbeat_enabled = Boolean(merged.heartbeat_enabled)
  merged.heartbeat_seconds = Math.max(5, Math.round(Number(merged.heartbeat_seconds ?? 15)))

  return merged
}

const trackPageView = (route, config) => {
  if (!config?.matomo_enabled) return
  if (!window?._paq) return
  if (!hasConsent(config)) return

  window._paq.push(['setCustomUrl', buildCustomUrl(route, config.include_query)])
  window._paq.push(['setDocumentTitle', buildDocumentTitle(route)])

  const dimensions = buildDimensionValues(config, { route })
  const applied = applyCustomDimensions(config, dimensions)

  window._paq.push(['trackPageView'])
  clearCustomDimensions(applied)
}

const applyMatomoConfigToPaq = (config, router) => {
  if (!config?.matomo_enabled) {
    if (window?._paq) {
      window._paq.push(['disableHeartBeatTimer'])
    }
    return
  }

  window._paq = window._paq || []

  const baseUrl = computeMatomoBaseUrl(config.matomo_base_url)
  const siteId = String(config.matomo_site_id || '1')

  let trackerUrl = `${baseUrl}matomo.php`
  let scriptUrl = `${baseUrl}matomo.js`
  try {
    const baseOrigin = new URL(baseUrl).origin
    if (baseOrigin === window.location.origin) {
      trackerUrl = `${window.location.origin}/metrics.php`
      scriptUrl = `${window.location.origin}/metrics.js`
    }
  } catch (e) {
    // Fall back to default URLs
  }

  if (config.disable_cookies) {
    window._paq.push(['disableCookies'])
  }

  if (config.require_consent) {
    window._paq.push(['requireConsent'])
  } else if (config.require_cookie_consent) {
    window._paq.push(['requireCookieConsent'])
  }
  applyConsentStateToPaq(config, analyticsConsentRef.value)

  // More accurate "time on page" tracking (sends periodic pings while user is active)
  if (config.heartbeat_enabled) {
    window._paq.push(['enableHeartBeatTimer', config.heartbeat_seconds])
  } else {
    window._paq.push(['disableHeartBeatTimer'])
  }

  window._paq.push(['setTrackerUrl', trackerUrl])
  window._paq.push(['setSiteId', siteId])
  window._paq.push(['enableLinkTracking'])

  if (config.set_user_id && hasConsent(config)) {
    const userId = resolveUserId()
    if (userId) {
      matomoSetUserId(userId)
    }
  }

  if (!hasTrackedInitialPageView && router) {
    const current = router.currentRoute?.value
    if (current) {
      trackPageView(current, config)
      hasTrackedInitialPageView = true
    }
  }

  ensureMatomoScriptLoaded(scriptUrl)
}

export const getAnalyticsConfig = () => ({ ...runtimeConfig })
export const useAnalyticsConfig = () => analyticsConfigRef
export const getAnalyticsConsentState = () => analyticsConsentRef.value
export const useAnalyticsConsent = () => analyticsConsentRef

export const setAnalyticsConsentState = (state) => {
  const normalized =
    state === CONSENT_VALUES.granted || state === CONSENT_VALUES.denied ? state : null
  analyticsConsentRef.value = normalized

  if (normalized) {
    safeStorageSet(CONSENT_STORAGE_KEY, normalized)
  } else {
    safeStorageRemove(CONSENT_STORAGE_KEY)
  }

  applyConsentStateToPaq(runtimeConfig, normalized)

  if (normalized === CONSENT_VALUES.granted && runtimeConfig?.set_user_id) {
    const userId = resolveUserId()
    if (userId) {
      matomoSetUserId(userId)
    }
  }

  if (normalized === CONSENT_VALUES.denied) {
    matomoResetUserId()
  }
}

export const setAnalyticsConfig = (config, { router } = {}) => {
  runtimeConfig = normalizeConfig(config)
  analyticsConfigRef.value = { ...runtimeConfig }
  if (router) {
    routerRef = router
  }
  if (!runtimeConfig.matomo_enabled) {
    hasTrackedInitialPageView = false
  }
  applyMatomoConfigToPaq(runtimeConfig, router)
  return getAnalyticsConfig()
}

export const loadAnalyticsConfig = async () => {
  try {
    const response = await fetch('/api/analytics/config', { credentials: 'same-origin' })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const json = await response.json()
    return normalizeConfig(json)
  } catch (e) {
    return getAnalyticsConfig()
  }
}

export const matomoTrackEvent = (category, action, name, value, options = undefined) => {
  if (!runtimeConfig?.matomo_enabled) return
  if (!window?._paq) return
  if (!hasConsent(runtimeConfig)) return

  let eventValue = value
  let opts = options
  if (value && typeof value === 'object' && options === undefined) {
    opts = value
    eventValue = undefined
  }

  const dimensions = buildDimensionValues(runtimeConfig, {
    route: opts?.route,
    dimensions: opts?.dimensions
  })
  const applied = applyCustomDimensions(runtimeConfig, dimensions)

  const payload = ['trackEvent', String(category), String(action)]
  if (name !== undefined) payload.push(String(name))
  if (eventValue !== undefined) payload.push(Number(eventValue))
  window._paq.push(payload)

  clearCustomDimensions(applied)
}

export const matomoSetUserId = (userId) => {
  if (!runtimeConfig?.matomo_enabled) return
  if (!runtimeConfig?.set_user_id) return
  if (!window?._paq) return
  if (!hasConsent(runtimeConfig)) return
  if (!userId) return
  window._paq.push(['setUserId', String(userId)])
}

export const matomoResetUserId = () => {
  if (!window?._paq) return
  window._paq.push(['resetUserId'])
}

export const initMatomo = ({ router, config } = {}) => {
  if (router) {
    routerRef = router
  }
  if (router && !listenersInstalled) {
    listenersInstalled = true

    router.afterEach((to) => {
      trackPageView(to, runtimeConfig)
    })

    document.addEventListener(
      'click',
      (event) => {
        if (!runtimeConfig?.matomo_enabled || !runtimeConfig?.track_clicks) return
        const clickable = findClickableTarget(event.target)
        if (!clickable) return
        if (clickable.closest('[data-matomo-ignore], [data-track-ignore]')) return

        const routeLabel = buildRouteLabel(router.currentRoute?.value)
        const clickName = getClickName(clickable)

        matomoTrackEvent(routeLabel, 'click', clickName)
      },
      true
    )

    let supportsHover = true
    try {
      supportsHover = window.matchMedia ? window.matchMedia('(hover: hover)').matches : true
    } catch (e) {
      supportsHover = true
    }

    if (supportsHover) {
      const hoverStarts = new WeakMap()
      const overEvent = 'onpointerover' in window ? 'pointerover' : 'mouseover'
      const outEvent = 'onpointerout' in window ? 'pointerout' : 'mouseout'

      document.addEventListener(
        overEvent,
        (event) => {
          if (!runtimeConfig?.matomo_enabled || !runtimeConfig?.track_hovers) return
          const clickable = findClickableTarget(event.target)
          if (!clickable) return
          if (clickable.closest('[data-matomo-ignore], [data-track-ignore]')) return

          const related = event.relatedTarget
          if (related instanceof Element && clickable.contains(related)) return
          hoverStarts.set(clickable, Date.now())
        },
        true
      )

      document.addEventListener(
        outEvent,
        (event) => {
          if (!runtimeConfig?.matomo_enabled || !runtimeConfig?.track_hovers) return
          const clickable = findClickableTarget(event.target)
          if (!clickable) return
          if (clickable.closest('[data-matomo-ignore], [data-track-ignore]')) return

          const related = event.relatedTarget
          if (related instanceof Element && clickable.contains(related)) return

          const startedAt = hoverStarts.get(clickable)
          if (!startedAt) return
          hoverStarts.delete(clickable)

          const durationMs = Math.min(60_000, Math.max(0, Date.now() - startedAt))
          if (durationMs < runtimeConfig.hover_min_ms) return
          if (runtimeConfig.hover_sample_rate < 1 && Math.random() >= runtimeConfig.hover_sample_rate) return

          const routeLabel = buildRouteLabel(router.currentRoute?.value)
          const clickName = getClickName(clickable)
          matomoTrackEvent(routeLabel, 'hover', clickName, durationMs)
        },
        true
      )
    }
  }

  if (config) {
    setAnalyticsConfig(config, { router })
  } else {
    loadAnalyticsConfig().then((loadedConfig) => {
      setAnalyticsConfig(loadedConfig, { router })
    })
  }
}
