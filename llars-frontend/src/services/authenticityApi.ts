import { BASE_URL } from '@/config'
import axios from 'axios'

export type AuthenticityVote = {
  vote: 'real' | 'fake'
  confidence?: number | null
  notes?: string | null
}

export type AuthenticityMetadata = {
  confidence?: number | null
  notes?: string | null
}

export const listAuthenticityThreads = () =>
  axios.get(`${BASE_URL}/api/email_threads/authenticity`).then(r => r.data)

export const getAuthenticityThread = (threadId: number) =>
  axios.get(`${BASE_URL}/api/email_threads/authenticity/${threadId}`).then(r => r.data)

export const saveAuthenticityVote = (threadId: number, payload: AuthenticityVote) =>
  axios.post(`${BASE_URL}/api/email_threads/authenticity/${threadId}/vote`, payload).then(r => r.data)

export const updateAuthenticityMetadata = (threadId: number, payload: AuthenticityMetadata) =>
  axios.patch(`${BASE_URL}/api/email_threads/authenticity/${threadId}/metadata`, payload).then(r => r.data)

export const importAuthenticityDataset = (items: any) =>
  axios.post(`${BASE_URL}/api/admin/authenticity/import`, items).then(r => r.data)

