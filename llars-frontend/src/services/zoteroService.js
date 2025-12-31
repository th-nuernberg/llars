/**
 * Zotero Integration Service
 *
 * Provides API calls for Zotero account connection, library management, and sync.
 */

import axios from 'axios'
import { BASE_URL } from '@/config.js'

const API_BASE = `${BASE_URL}/api/zotero`

// Create axios instance with auth header
function getAuthHeaders() {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function apiGet(endpoint, params = {}) {
  const response = await axios.get(`${API_BASE}${endpoint}`, {
    headers: getAuthHeaders(),
    params
  })
  return response.data
}

async function apiPost(endpoint, data = {}) {
  const response = await axios.post(`${API_BASE}${endpoint}`, data, {
    headers: getAuthHeaders()
  })
  return response.data
}

async function apiPatch(endpoint, data = {}) {
  const response = await axios.patch(`${API_BASE}${endpoint}`, data, {
    headers: getAuthHeaders()
  })
  return response.data
}

async function apiDelete(endpoint) {
  const response = await axios.delete(`${API_BASE}${endpoint}`, {
    headers: getAuthHeaders()
  })
  return response.data
}

/**
 * Check if Zotero OAuth is available (configured by admin)
 */
export async function checkOAuthAvailable() {
  return apiGet('/oauth-available')
}

/**
 * Get current user's Zotero connection status
 */
export async function getConnectionStatus() {
  return apiGet('/status')
}

/**
 * Start OAuth flow to connect Zotero account
 * Returns authorization URL to redirect user to
 */
export async function startOAuth() {
  return apiPost('/connect/oauth/start')
}

/**
 * Connect Zotero account using a manually provided API key
 * @param {string} apiKey - Zotero API key
 */
export async function connectWithApiKey(apiKey) {
  return apiPost('/connect/api-key', { api_key: apiKey })
}

/**
 * Disconnect Zotero account
 */
export async function disconnect() {
  return apiDelete('/disconnect')
}

/**
 * Get all Zotero libraries accessible to the user
 */
export async function getLibraries() {
  return apiGet('/libraries')
}

/**
 * Get collections in a Zotero library
 * @param {string} libraryType - "user" or "group"
 * @param {string} libraryId - User or group ID
 */
export async function getCollections(libraryType, libraryId) {
  return apiGet(`/libraries/${libraryType}/${libraryId}/collections`)
}

/**
 * Get Zotero libraries linked to a workspace
 * @param {number} workspaceId - Workspace ID
 */
export async function getWorkspaceLibraries(workspaceId) {
  return apiGet(`/workspaces/${workspaceId}/libraries`)
}

/**
 * Link a Zotero library/collection to a workspace
 * @param {number} workspaceId - Workspace ID
 * @param {Object} libraryData - Library data
 */
export async function addWorkspaceLibrary(workspaceId, libraryData) {
  return apiPost(`/workspaces/${workspaceId}/libraries`, libraryData)
}

/**
 * Unlink a Zotero library from a workspace
 * @param {number} workspaceId - Workspace ID
 * @param {number} libraryId - Library link ID
 */
export async function removeWorkspaceLibrary(workspaceId, libraryId) {
  return apiDelete(`/workspaces/${workspaceId}/libraries/${libraryId}`)
}

/**
 * Manually sync a Zotero library to update the .bib file
 * @param {number} workspaceId - Workspace ID
 * @param {number} libraryId - Library link ID
 */
export async function syncLibrary(workspaceId, libraryId) {
  return apiPost(`/workspaces/${workspaceId}/libraries/${libraryId}/sync`)
}

/**
 * Update library sync settings
 * @param {number} workspaceId - Workspace ID
 * @param {number} libraryId - Library link ID
 * @param {Object} settings - Settings to update
 */
export async function updateLibrarySettings(workspaceId, libraryId, settings) {
  return apiPatch(`/workspaces/${workspaceId}/libraries/${libraryId}/settings`, settings)
}

/**
 * Get sync history for a library
 * @param {number} workspaceId - Workspace ID
 * @param {number} libraryId - Library link ID
 * @param {number} limit - Number of logs to fetch
 */
export async function getSyncLogs(workspaceId, libraryId, limit = 20) {
  return apiGet(`/workspaces/${workspaceId}/libraries/${libraryId}/logs`, { limit })
}

export default {
  checkOAuthAvailable,
  getConnectionStatus,
  startOAuth,
  connectWithApiKey,
  disconnect,
  getLibraries,
  getCollections,
  getWorkspaceLibraries,
  addWorkspaceLibrary,
  removeWorkspaceLibrary,
  syncLibrary,
  updateLibrarySettings,
  getSyncLogs,
}
