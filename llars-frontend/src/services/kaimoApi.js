import axios from 'axios'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

const baseUrl = import.meta.env.VITE_API_BASE_URL || ''

const getToken = () => getAuthStorageItem(AUTH_STORAGE_KEYS.token)

export async function getKaimoCases() {
  const token = getToken()
  const res = await axios.get(`${baseUrl}/api/kaimo/cases`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function getKaimoCase(caseId) {
  const token = getToken()
  const res = await axios.get(`${baseUrl}/api/kaimo/cases/${caseId}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function createKaimoCase(payload) {
  const token = getToken()
  const res = await axios.post(`${baseUrl}/api/kaimo/admin/cases`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function publishKaimoCase(caseId) {
  const token = getToken()
  const res = await axios.post(`${baseUrl}/api/kaimo/admin/cases/${caseId}/publish`, {}, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

// ============ Admin API - Export/Import ============

export async function exportKaimoCase(caseId, includeAssessments = false) {
  const token = getToken()
  const params = includeAssessments ? '?include_assessments=true' : ''
  const res = await axios.get(`${baseUrl}/api/kaimo/admin/cases/${caseId}/export${params}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function importKaimoCase(exportData, options = {}) {
  const token = getToken()
  const payload = {
    export: exportData,
    name_override: options.nameOverride || null,
    status_override: options.statusOverride || null,
    publish: options.publish || false
  }
  const res = await axios.post(`${baseUrl}/api/kaimo/admin/cases/import`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

// ============ Admin API - Cases ============

export async function updateKaimoCase(caseId, payload) {
  const token = getToken()
  const res = await axios.put(`${baseUrl}/api/kaimo/admin/cases/${caseId}`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function deleteKaimoCase(caseId, force = false) {
  const token = getToken()
  const url = force
    ? `${baseUrl}/api/kaimo/admin/cases/${caseId}?force=true`
    : `${baseUrl}/api/kaimo/admin/cases/${caseId}`
  const res = await axios.delete(url, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function getKaimoCaseAdmin(caseId) {
  const token = getToken()
  const res = await axios.get(`${baseUrl}/api/kaimo/admin/cases/${caseId}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function getKaimoAdminCases() {
  const token = getToken()
  const res = await axios.get(`${baseUrl}/api/kaimo/admin/cases`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

// ============ Admin API - Documents ============

export async function createKaimoDocument(caseId, payload) {
  const token = getToken()
  const res = await axios.post(`${baseUrl}/api/kaimo/admin/cases/${caseId}/documents`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function updateKaimoDocument(caseId, docId, payload) {
  const token = getToken()
  const res = await axios.put(`${baseUrl}/api/kaimo/admin/cases/${caseId}/documents/${docId}`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function deleteKaimoDocument(caseId, docId) {
  const token = getToken()
  const res = await axios.delete(`${baseUrl}/api/kaimo/admin/cases/${caseId}/documents/${docId}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

// ============ Admin API - Hints ============

export async function createKaimoHint(caseId, payload) {
  const token = getToken()
  const res = await axios.post(`${baseUrl}/api/kaimo/admin/cases/${caseId}/hints`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function updateKaimoHint(caseId, hintId, payload) {
  const token = getToken()
  const res = await axios.put(`${baseUrl}/api/kaimo/admin/cases/${caseId}/hints/${hintId}`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function deleteKaimoHint(caseId, hintId) {
  const token = getToken()
  const res = await axios.delete(`${baseUrl}/api/kaimo/admin/cases/${caseId}/hints/${hintId}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

// ============ Admin API - Results & Categories ============

export async function getKaimoCaseResults(caseId) {
  const token = getToken()
  const res = await axios.get(`${baseUrl}/api/kaimo/admin/cases/${caseId}/results`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function getKaimoCategories() {
  const token = getToken()
  const res = await axios.get(`${baseUrl}/api/kaimo/admin/categories`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

// ============ User API - Assessment Workflow ============

export async function startKaimoAssessment(caseId) {
  const token = getToken()
  const res = await axios.post(`${baseUrl}/api/kaimo/cases/${caseId}/start`, {}, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function getKaimoAssessment(assessmentId) {
  const token = getToken()
  const res = await axios.get(`${baseUrl}/api/kaimo/assessments/${assessmentId}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function saveHintAssignment(assessmentId, hintId, payload) {
  const token = getToken()
  const res = await axios.put(`${baseUrl}/api/kaimo/assessments/${assessmentId}/hints/${hintId}`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function completeAssessment(assessmentId, payload) {
  const token = getToken()
  const res = await axios.post(`${baseUrl}/api/kaimo/assessments/${assessmentId}/complete`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

// ============ User API - Categories ============

export async function getKaimoUserCategories() {
  const token = getToken()
  const res = await axios.get(`${baseUrl}/api/kaimo/categories`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}
