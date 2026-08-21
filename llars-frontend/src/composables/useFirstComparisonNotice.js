/**
 * useFirstComparisonNotice - one-time "thank you" after the FIRST saved comparison
 *
 * DEPRECATED / NO LONGER WIRED UP (2026-06): the per-comparison thank-you notice
 * this composable powered has been superseded by a UNIVERSAL first-evaluation
 * notice owned by EvaluationSession.vue. That shell watches the scenario's
 * completed-count 0 → ≥1 transition and shows a generic thank-you ONCE per
 * scenario for ALL evaluation types (ranking, rating, labeling, authenticity,
 * comparison, …) — see EvaluationSession.vue#maybeShowFirstEvaluationNotice.
 * ComparisonInterface no longer imports or invokes this composable, so it does
 * not double-fire. This file is retained (with its unit tests) as a reusable
 * one-time per-user gate in case another flow needs it; it is otherwise unused.
 *
 * Study requirement (in Zusammenarbeit mit den Sozialwissenschaften, mail-comparison study / scenario 492): the very
 * first time a participant successfully saves an A/B comparison rating, show a
 * short confirmation that nudges them toward the "Weiter" button. It must
 * appear EXACTLY ONCE per user and never reappear on later cases, reloads, or
 * even on a different device.
 *
 * Persistence strategy (defence in depth — the flag must NEVER be lost):
 *   1. Backend user-setting  (authoritative, survives device change / cache
 *      clear): stored under `user.settings_json.firstComparisonNoticeSeen`
 *      via `GET/PUT /api/user/settings` (preferences merge). This is the
 *      reliable source of truth — it is the same generic per-user JSON store
 *      already used for other UI preferences.
 *   2. localStorage fast-path (per username): avoids a network round-trip /
 *      flash on every page load and keeps the notice suppressed instantly even
 *      before the backend GET resolves. Scoped by username so two accounts on
 *      one browser don't share the flag.
 *
 * Read   = localStorage hit short-circuits; otherwise we ask the backend and
 *          cache the answer in localStorage.
 * Write  = set localStorage immediately (so a fast follow-up save can't double
 *          fire) AND PUT the backend flag. A failed backend PUT is tolerated:
 *          the localStorage flag still prevents a repeat on this device, and we
 *          simply retry the PUT on the next successful save attempt because the
 *          backend flag is still false. Worst case the user sees it at most
 *          once per device — acceptable and far better than losing the flag.
 *
 * Decoupled from the comparison composable so it can be unit-tested in
 * isolation and reused if another flow ever needs the same one-time gate.
 */
import { ref } from 'vue'
import axios from 'axios'

// Key inside `user.settings_json` (backend preferences blob).
const BACKEND_PREF_KEY = 'firstComparisonNoticeSeen'

// localStorage key prefix; the active username is appended so the fast-path is
// per-user on shared browsers. Falls back to "_anon" when no username is set.
const LS_KEY_PREFIX = 'llars:firstComparisonNoticeSeen:'

function lsKey() {
  let username = '_anon'
  try {
    username = (typeof localStorage !== 'undefined' && localStorage.getItem('username')) || '_anon'
  } catch {
    // localStorage may throw in private-mode / SSR — treat as anon.
  }
  return `${LS_KEY_PREFIX}${username}`
}

function lsGet() {
  try {
    return typeof localStorage !== 'undefined' && localStorage.getItem(lsKey()) === '1'
  } catch {
    return false
  }
}

function lsSet() {
  try {
    if (typeof localStorage !== 'undefined') localStorage.setItem(lsKey(), '1')
  } catch {
    // best-effort; backend flag remains the source of truth
  }
}

export function useFirstComparisonNotice() {
  // Whether the one-time notice is currently displayed.
  const noticeVisible = ref(false)

  // Resolved "already seen" state. `null` = not yet determined (backend not
  // queried and no localStorage hit). Guards against firing before we know.
  const seen = ref(lsGet() ? true : null)

  /**
   * Ensure we know whether the notice was already seen. Cheap when the
   * localStorage fast-path already answered; otherwise asks the backend once.
   * Safe to call repeatedly — only hits the network until `seen` is resolved.
   */
  async function ensureSeenLoaded() {
    if (seen.value !== null) return seen.value
    try {
      const { data } = await axios.get('/api/user/settings')
      const prefs = data?.settings?.preferences || {}
      const value = prefs[BACKEND_PREF_KEY] === true
      seen.value = value
      if (value) lsSet() // backfill the fast-path cache
    } catch {
      // Network/backend failure: leave `seen` unresolved so we don't wrongly
      // suppress the notice. The localStorage flag (if any) already set it.
      seen.value = lsGet() ? true : null
    }
    return seen.value === true
  }

  /**
   * Mark the notice as seen everywhere. localStorage is set synchronously so a
   * rapid second save can't re-trigger; the backend PUT is fire-and-forget but
   * awaited so callers/tests can observe completion.
   */
  async function markSeen() {
    seen.value = true
    lsSet()
    try {
      await axios.put('/api/user/settings', {
        preferences: { [BACKEND_PREF_KEY]: true }
      })
    } catch {
      // Tolerated — see module docstring. localStorage still suppresses on this
      // device and the backend flag stays false so the next save retries.
    }
  }

  /**
   * Call AFTER a comparison save has actually succeeded. Shows the notice
   * exactly once (the first time) and persists the seen-flag. No-ops on every
   * subsequent call. Returns true when it triggered the notice this time.
   */
  async function maybeShowAfterFirstSave() {
    // Fast path: localStorage already says seen → never show.
    if (lsGet() || seen.value === true) return false

    // Resolve against the backend (covers device change / cleared cache).
    const already = await ensureSeenLoaded()
    if (already) return false

    noticeVisible.value = true
    await markSeen()
    return true
  }

  function dismiss() {
    noticeVisible.value = false
  }

  return {
    noticeVisible,
    seen,
    ensureSeenLoaded,
    maybeShowAfterFirstSave,
    markSeen,
    dismiss,
    // exported for tests
    _BACKEND_PREF_KEY: BACKEND_PREF_KEY,
  }
}
