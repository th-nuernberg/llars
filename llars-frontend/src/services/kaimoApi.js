import axios from 'axios'

const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:80'

export async function getKaimoCases() {
  const token = sessionStorage.getItem('auth_token')
  const res = await axios.get(`${baseUrl}/api/kaimo/cases`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function getKaimoCase(caseId) {
  const token = sessionStorage.getItem('auth_token')
  const res = await axios.get(`${baseUrl}/api/kaimo/cases/${caseId}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function createKaimoCase(payload) {
  const token = sessionStorage.getItem('auth_token')
  const res = await axios.post(`${baseUrl}/api/kaimo/admin/cases`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function publishKaimoCase(caseId) {
  const token = sessionStorage.getItem('auth_token')
  const res = await axios.post(`${baseUrl}/api/kaimo/admin/cases/${caseId}/publish`, {}, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

// ============ Admin API - Cases ============

export async function updateKaimoCase(caseId, payload) {
  const token = sessionStorage.getItem('auth_token')
  const res = await axios.put(`${baseUrl}/api/kaimo/admin/cases/${caseId}`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function deleteKaimoCase(caseId, force = false) {
  const token = sessionStorage.getItem('auth_token')
  const url = force
    ? `${baseUrl}/api/kaimo/admin/cases/${caseId}?force=true`
    : `${baseUrl}/api/kaimo/admin/cases/${caseId}`
  const res = await axios.delete(url, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function getKaimoCaseAdmin(caseId) {
  const token = sessionStorage.getItem('auth_token')
  const res = await axios.get(`${baseUrl}/api/kaimo/admin/cases/${caseId}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function getKaimoAdminCases() {
  const token = sessionStorage.getItem('auth_token')
  const res = await axios.get(`${baseUrl}/api/kaimo/admin/cases`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

// ============ Admin API - Documents ============

export async function createKaimoDocument(caseId, payload) {
  const token = sessionStorage.getItem('auth_token')
  const res = await axios.post(`${baseUrl}/api/kaimo/admin/cases/${caseId}/documents`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function updateKaimoDocument(caseId, docId, payload) {
  const token = sessionStorage.getItem('auth_token')
  const res = await axios.put(`${baseUrl}/api/kaimo/admin/cases/${caseId}/documents/${docId}`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function deleteKaimoDocument(caseId, docId) {
  const token = sessionStorage.getItem('auth_token')
  const res = await axios.delete(`${baseUrl}/api/kaimo/admin/cases/${caseId}/documents/${docId}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

// ============ Admin API - Hints ============

export async function createKaimoHint(caseId, payload) {
  const token = sessionStorage.getItem('auth_token')
  const res = await axios.post(`${baseUrl}/api/kaimo/admin/cases/${caseId}/hints`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function updateKaimoHint(caseId, hintId, payload) {
  const token = sessionStorage.getItem('auth_token')
  const res = await axios.put(`${baseUrl}/api/kaimo/admin/cases/${caseId}/hints/${hintId}`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function deleteKaimoHint(caseId, hintId) {
  const token = sessionStorage.getItem('auth_token')
  const res = await axios.delete(`${baseUrl}/api/kaimo/admin/cases/${caseId}/hints/${hintId}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

// ============ Admin API - Results & Categories ============

export async function getKaimoCaseResults(caseId) {
  const token = sessionStorage.getItem('auth_token')
  const res = await axios.get(`${baseUrl}/api/kaimo/admin/cases/${caseId}/results`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function getKaimoCategories() {
  const token = sessionStorage.getItem('auth_token')
  const res = await axios.get(`${baseUrl}/api/kaimo/admin/categories`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

// ============ User API - Assessment Workflow ============

export async function startKaimoAssessment(caseId) {
  const token = sessionStorage.getItem('auth_token')
  const res = await axios.post(`${baseUrl}/api/kaimo/cases/${caseId}/start`, {}, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function getKaimoAssessment(assessmentId) {
  const token = sessionStorage.getItem('auth_token')
  const res = await axios.get(`${baseUrl}/api/kaimo/assessments/${assessmentId}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function saveHintAssignment(assessmentId, hintId, payload) {
  const token = sessionStorage.getItem('auth_token')
  const res = await axios.put(`${baseUrl}/api/kaimo/assessments/${assessmentId}/hints/${hintId}`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function completeAssessment(assessmentId, payload) {
  const token = sessionStorage.getItem('auth_token')
  const res = await axios.post(`${baseUrl}/api/kaimo/assessments/${assessmentId}/complete`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

// ============ User API - Categories ============

export async function getKaimoUserCategories() {
  const token = sessionStorage.getItem('auth_token')
  const res = await axios.get(`${baseUrl}/api/kaimo/categories`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}
