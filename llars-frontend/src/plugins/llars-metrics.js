const parseBoolean = (value, defaultValue = false) => {
  if (value === undefined || value === null) return defaultValue
  const normalized = String(value).trim().toLowerCase()
  if (['1', 'true', 'yes', 'y', 'on'].includes(normalized)) return true
  if (['0', 'false', 'no', 'n', 'off'].includes(normalized)) return false
  return defaultValue
}

import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

const parseJwt = (jwtToken) => {
  if (!jwtToken) return null
  try {
    const parts = String(jwtToken).split('.')
    if (parts.length < 2) return null
    return JSON.parse(atob(parts[1]))
  } catch (e) {
    return null
  }
}

const computeMatomoBaseUrl = () => {
  const configured = String(import.meta.env.VITE_MATOMO_BASE_URL || '').trim()
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

const buildCustomUrl = (route) => {
  const includeQuery = parseBoolean(import.meta.env.VITE_MATOMO_INCLUDE_QUERY, false)
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

const getClickName = (el) => {
  const explicit =
    el.getAttribute('data-matomo-name') ||
    el.getAttribute('data-track') ||
    el.getAttribute('data-testid') ||
    el.getAttribute('aria-label') ||
    el.getAttribute('title') ||
    el.id

  if (explicit) return sanitizeLabel(explicit)

  const text = sanitizeLabel(el.innerText)
  if (text) return text

  const firstClass = (el.className || '')
    .toString()
    .split(/\s+/)
    .filter(Boolean)[0]
  return firstClass ? `.${firstClass}` : el.tagName.toLowerCase()
}

export const matomoTrackEvent = (category, action, name, value) => {
  if (!window?._paq) return
  const payload = ['trackEvent', String(category), String(action)]
  if (name !== undefined) payload.push(String(name))
  if (value !== undefined) payload.push(Number(value))
  window._paq.push(payload)
}

export const matomoSetUserId = (userId) => {
  if (!window?._paq) return
  if (!userId) return
  window._paq.push(['setUserId', String(userId)])
}

export const matomoResetUserId = () => {
  if (!window?._paq) return
  window._paq.push(['resetUserId'])
}

export const initMatomo = ({ router } = {}) => {
  const enabled = parseBoolean(import.meta.env.VITE_MATOMO_ENABLED, false)
  if (!enabled) return

  window._paq = window._paq || []

  const baseUrl = computeMatomoBaseUrl()
  const siteId = String(import.meta.env.VITE_MATOMO_SITE_ID || '1')

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

  if (parseBoolean(import.meta.env.VITE_MATOMO_DISABLE_COOKIES, false)) {
    window._paq.push(['disableCookies'])
  }

  if (parseBoolean(import.meta.env.VITE_MATOMO_REQUIRE_CONSENT, false)) {
    window._paq.push(['requireConsent'])
  } else if (parseBoolean(import.meta.env.VITE_MATOMO_REQUIRE_COOKIE_CONSENT, false)) {
    window._paq.push(['requireCookieConsent'])
  }

  window._paq.push(['setTrackerUrl', trackerUrl])
  window._paq.push(['setSiteId', siteId])
  window._paq.push(['enableLinkTracking'])

  if (parseBoolean(import.meta.env.VITE_MATOMO_SET_USER_ID, true)) {
    const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
    const payload = parseJwt(token)
    let storedUsername = null
    try {
      storedUsername = localStorage.getItem('username')
    } catch (e) {
      storedUsername = null
    }
    const userId =
      payload?.preferred_username ||
      payload?.sub ||
      storedUsername
    if (userId) {
      matomoSetUserId(userId)
    }
  }

  if (router) {
    router.afterEach((to) => {
      window._paq.push(['setCustomUrl', buildCustomUrl(to)])
      window._paq.push(['setDocumentTitle', buildDocumentTitle(to)])
      window._paq.push(['trackPageView'])
    })

    if (parseBoolean(import.meta.env.VITE_MATOMO_TRACK_CLICKS, true)) {
      document.addEventListener(
        'click',
        (event) => {
          const clickable = findClickableTarget(event.target)
          if (!clickable) return
          if (clickable.closest('[data-matomo-ignore], [data-track-ignore]')) return

          const routeLabel = buildRouteLabel(router.currentRoute?.value)
          const clickName = getClickName(clickable)

          matomoTrackEvent(routeLabel, 'click', clickName)
        },
        true
      )
    }
  }

  ensureMatomoScriptLoaded(scriptUrl)
}
