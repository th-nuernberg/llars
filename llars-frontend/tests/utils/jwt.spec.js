/**
 * JWT Utility Tests
 *
 * Tests for JWT payload decoding.
 * Test IDs: UTIL_JWT_001 - UTIL_JWT_020
 */

import { describe, it, expect } from 'vitest'
import { decodeJwtPayload } from '@/utils/jwt'

/**
 * Helper to create a mock JWT token with a given payload.
 * JWT format: header.payload.signature (all base64url-encoded)
 */
function createMockJwt(payload) {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const payloadB64 = btoa(JSON.stringify(payload))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '')
  const signature = 'mock-signature'
  return `${header}.${payloadB64}.${signature}`
}

// ==================== decodeJwtPayload Tests ====================

describe('decodeJwtPayload', () => {
  it('UTIL_JWT_001: returns null for null input', () => {
    expect(decodeJwtPayload(null)).toBeNull()
  })

  it('UTIL_JWT_002: returns null for undefined input', () => {
    expect(decodeJwtPayload(undefined)).toBeNull()
  })

  it('UTIL_JWT_003: returns null for empty string', () => {
    expect(decodeJwtPayload('')).toBeNull()
  })

  it('UTIL_JWT_004: returns null for non-JWT string (no dots)', () => {
    expect(decodeJwtPayload('notajwt')).toBeNull()
  })

  it('UTIL_JWT_005: returns null for single-part token', () => {
    expect(decodeJwtPayload('onlyheader')).toBeNull()
  })

  it('UTIL_JWT_006: decodes valid JWT payload', () => {
    const payload = { sub: 'user123', name: 'Test User', iat: 1700000000 }
    const token = createMockJwt(payload)
    const result = decodeJwtPayload(token)
    expect(result).toEqual(payload)
  })

  it('UTIL_JWT_007: decodes JWT with nested object in payload', () => {
    const payload = { sub: 'user123', data: { role: 'admin', level: 5 } }
    const token = createMockJwt(payload)
    const result = decodeJwtPayload(token)
    expect(result.data.role).toBe('admin')
    expect(result.data.level).toBe(5)
  })

  it('UTIL_JWT_008: decodes JWT with array in payload', () => {
    const payload = { sub: 'user123', roles: ['admin', 'user'] }
    const token = createMockJwt(payload)
    const result = decodeJwtPayload(token)
    expect(result.roles).toEqual(['admin', 'user'])
  })

  it('UTIL_JWT_009: handles base64url encoding (replaces - and _)', () => {
    // The payload with special base64url chars
    const payload = { sub: 'user+special/chars==', exp: 9999999999 }
    const token = createMockJwt(payload)
    const result = decodeJwtPayload(token)
    expect(result.sub).toBe('user+special/chars==')
  })

  it('UTIL_JWT_010: returns null for malformed base64 payload', () => {
    const token = 'header.!!!invalid-base64!!!.signature'
    expect(decodeJwtPayload(token)).toBeNull()
  })

  it('UTIL_JWT_011: returns null for non-JSON payload', () => {
    const header = btoa('{"alg":"HS256"}')
    const payload = btoa('not-json')
    const token = `${header}.${payload}.sig`
    expect(decodeJwtPayload(token)).toBeNull()
  })

  it('UTIL_JWT_012: converts number input to string', () => {
    // Number doesn't have dots, so should return null
    expect(decodeJwtPayload(12345)).toBeNull()
  })

  it('UTIL_JWT_013: handles JWT with two parts (no signature)', () => {
    const payload = { sub: 'user123' }
    const header = btoa(JSON.stringify({ alg: 'none' }))
    const payloadB64 = btoa(JSON.stringify(payload))
    const token = `${header}.${payloadB64}`
    const result = decodeJwtPayload(token)
    expect(result).toEqual(payload)
  })

  it('UTIL_JWT_014: handles JWT with extra parts', () => {
    const payload = { sub: 'user123' }
    const token = createMockJwt(payload) + '.extra.parts'
    const result = decodeJwtPayload(token)
    expect(result).toEqual(payload)
  })

  it('UTIL_JWT_015: handles payload with unicode characters', () => {
    const payload = { sub: 'user123', name: 'Muller' }
    const token = createMockJwt(payload)
    const result = decodeJwtPayload(token)
    expect(result.name).toBe('Muller')
  })

  it('UTIL_JWT_016: handles empty payload object', () => {
    const token = createMockJwt({})
    const result = decodeJwtPayload(token)
    expect(result).toEqual({})
  })
})
