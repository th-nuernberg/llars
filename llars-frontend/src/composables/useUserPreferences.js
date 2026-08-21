/**
 * useUserPreferences Composable
 *
 * Client-seitige Benutzer-Präferenzen für UI-Verhalten (z.B. Tastatur-Shortcuts
 * in der Evaluation). Persistiert PRO USER im Backend unter
 * `user.settings_json.preferences` (GET/PUT /api/user/settings) — dadurch folgt
 * die Einstellung dem User geräte- und browserübergreifend, nicht nur diesem
 * Browser. Zusätzlich wird der Wert in localStorage gecacht, damit er beim
 * nächsten Laden sofort verfügbar ist (der Server-Wert korrigiert den Cache beim
 * ersten Laden, falls sie auseinanderlaufen).
 *
 * Singleton-Pattern (Modul-Level State) wie useAppTheme: alle Komponenten teilen
 * denselben reaktiven Zustand. Standardwerte sind bewusst konservativ (Shortcuts
 * AUS) — jeder User aktiviert sie selbst unter Settings → Präferenzen.
 *
 * Dieses Objekt wird künftig um weitere Präferenzen erweitert (der Settings-Tab
 * ist als Sammelfläche gedacht).
 */
import { ref } from 'vue'
import axios from 'axios'

// localStorage-Cache-Keys (namespaced, um Kollisionen zu vermeiden). Der Cache
// dient nur der sofortigen Verfügbarkeit; maßgeblich ist der Server-Wert.
const LS_SPACEBAR_ADVANCE = 'llars:pref:spacebarAdvance'

function readCachedBool(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw === null ? fallback : raw === 'true'
  } catch {
    return fallback
  }
}

function writeCachedBool(key, val) {
  try {
    localStorage.setItem(key, val ? 'true' : 'false')
  } catch {
    /* localStorage nicht verfügbar (z.B. Privatmodus) — Präferenz bleibt session-lokal */
  }
}

// --- Shared (Singleton) State ------------------------------------------------
// Leertaste = "Weiter" in der Evaluation. Standard: AUS.
const spacebarAdvance = ref(readCachedBool(LS_SPACEBAR_ADVANCE, false))

// Verhindert mehrfaches Laden vom Server, wenn das Composable in mehreren
// Komponenten (Settings + EvaluationSession) verwendet wird.
let serverLoadStarted = false

/**
 * Präferenzen vom Server laden und den lokalen Zustand/Cache korrigieren.
 * Fehlertolerant: offline/nicht eingeloggt → der gecachte Wert bleibt.
 */
async function loadFromServer() {
  try {
    const { data } = await axios.get('/api/user/settings')
    const prefs = data?.settings?.preferences || {}
    if (typeof prefs.spacebarAdvance === 'boolean') {
      spacebarAdvance.value = prefs.spacebarAdvance
      writeCachedBool(LS_SPACEBAR_ADVANCE, prefs.spacebarAdvance)
    }
  } catch {
    /* Server nicht erreichbar / nicht eingeloggt — Cache-Wert bleibt gültig */
  }
}

/**
 * Setzt "Leertaste = Weiter" und persistiert PRO USER im Backend (+ Cache).
 * Optimistisch: der reaktive Zustand ändert sich sofort; ein fehlgeschlagener
 * PUT lässt die Einstellung lokal aktiv (kein harter Fehler für den Nutzer).
 */
async function setSpacebarAdvance(val) {
  const next = Boolean(val)
  spacebarAdvance.value = next
  writeCachedBool(LS_SPACEBAR_ADVANCE, next)
  await axios.put('/api/user/settings', { preferences: { spacebarAdvance: next } })
}

export function useUserPreferences() {
  // Beim ersten Konsumenten einmalig vom Server laden (Server = Source of Truth).
  if (!serverLoadStarted) {
    serverLoadStarted = true
    loadFromServer()
  }
  return {
    spacebarAdvance,
    setSpacebarAdvance,
    reloadPreferences: loadFromServer,
  }
}
