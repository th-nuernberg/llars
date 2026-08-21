import { ref, readonly } from 'vue'

/**
 * Study-consent state shared between /study-consent (where the user
 * actually reads + ticks the boxes) and /register (where the form
 * submission sends the recorded consent to the backend).
 *
 * Persisted in sessionStorage so a page refresh doesn't lose the
 * just-granted consent. sessionStorage (not localStorage) so the
 * consent dies with the tab — re-using a stale consent across
 * sessions would weaken the audit trail.
 *
 * The exposed surface is intentionally tiny:
 *   - `getConsent()` returns the current snapshot (or null)
 *   - `setConsent(snapshot)` records a new grant
 *   - `clearConsent()` removes it (used after successful register)
 *   - `consent` reactive ref auto-syncs across components
 *
 * Snapshot shape mirrors the backend register-endpoint contract:
 *   {
 *     version: 'study-consent-v2-2026-05',
 *     granted_at: '2026-05-11T15:42:00.123Z',  // client-side
 *     dataset_release: bool,                    // optional
 *     followup_contact: bool,                   // optional
 *     language: 'de' | 'en'
 *   }
 *
 * The three mandatory backend fields are implied = true (granting the
 * snapshot at all requires the user ticked the mandatory checkbox).
 */

const STORAGE_KEY = 'llars-study-consent'
const consent = ref(null)

// Hydrate from sessionStorage on module load (single source of truth).
try {
  const raw = sessionStorage.getItem(STORAGE_KEY)
  if (raw) consent.value = JSON.parse(raw)
} catch (_) {
  // sessionStorage may be unavailable (SSR, restricted-cookie mode);
  // composable still works, just without persistence.
}

function setConsent(snapshot) {
  consent.value = snapshot
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot))
  } catch (_) { /* see note above */ }
}

function clearConsent() {
  consent.value = null
  try {
    sessionStorage.removeItem(STORAGE_KEY)
  } catch (_) { /* see note above */ }
}

function getConsent() {
  return consent.value
}

export function useStudyConsent() {
  return {
    consent: readonly(consent),
    getConsent,
    setConsent,
    clearConsent,
  }
}
