export const decodeJwtPayload = (jwtToken) => {
  if (!jwtToken) return null
  try {
    const parts = String(jwtToken).split('.')
    if (parts.length < 2) return null

    const base64Url = parts[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const pad = '='.repeat((4 - (base64.length % 4)) % 4)
    const json = atob(`${base64}${pad}`)
    return JSON.parse(json)
  } catch (e) {
    return null
  }
}

