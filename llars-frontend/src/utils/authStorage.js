const safeGetItem = (storage, key) => {
  try {
    return storage?.getItem(key) ?? null
  } catch (e) {
    return null
  }
}

const safeSetItem = (storage, key, value) => {
  try {
    storage?.setItem(key, value)
    return true
  } catch (e) {
    return false
  }
}

const safeRemoveItem = (storage, key) => {
  try {
    storage?.removeItem(key)
  } catch (e) {
    // ignore
  }
}

const memoryCache = new Map()

export const AUTH_STORAGE_KEYS = Object.freeze({
  token: 'auth_token',
  refreshToken: 'auth_refreshToken',
  idToken: 'auth_idToken',
  roles: 'auth_llars_roles'
})

export const getAuthStorageItem = (key) => {
  if (typeof window === 'undefined') return null
  const fromSession = safeGetItem(window.sessionStorage, key)
  if (fromSession !== null && fromSession !== undefined) {
    memoryCache.set(key, fromSession)
    return fromSession
  }

  const fromLocal = safeGetItem(window.localStorage, key)
  if (fromLocal !== null && fromLocal !== undefined) {
    memoryCache.set(key, fromLocal)
    return fromLocal
  }

  return memoryCache.get(key) ?? null
}

export const setAuthStorageItem = (key, value, { mirrorToLocalStorage = false } = {}) => {
  if (typeof window === 'undefined') return
  memoryCache.set(key, value)
  const storedInSession = safeSetItem(window.sessionStorage, key, value)
  if (mirrorToLocalStorage || !storedInSession) {
    safeSetItem(window.localStorage, key, value)
  }
}

export const removeAuthStorageItem = (key) => {
  if (typeof window === 'undefined') return
  memoryCache.delete(key)
  safeRemoveItem(window.sessionStorage, key)
  safeRemoveItem(window.localStorage, key)
}

export const clearAuthStorage = () => {
  Object.values(AUTH_STORAGE_KEYS).forEach((key) => removeAuthStorageItem(key))
}
