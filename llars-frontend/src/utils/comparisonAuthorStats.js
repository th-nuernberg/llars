/**
 * Comparison author statistics
 *
 * Aggregates pairwise comparison votes (A / B / tie) onto the AUTHOR level
 * (human vs the individual LLM models) so the scenario analysis can answer
 * "how often was the human picked vs an AI" and rank the systems.
 *
 * Produces, from a flat list of votes:
 *   - systems:   per-author win rate + Wilson 95% CI + Bradley–Terry strength + rank
 *   - pairings:  head-to-head win rates for every author pair that actually met
 *   - selfAgreement: position-order (AB/BA) self-consistency of the raters, or
 *                    null when the data has no mirrored presentations
 *
 * Pure functions only — no Vue, no I/O — so the math is unit-testable
 * independently of the component that renders it.
 *
 * Vote shape: { username?, a, b, choice, labelA?, labelB? }
 *   a / b   : author keys for the A-slot and B-slot option (e.g. 'human',
 *             'llm:mis24b-instruct'). null/undefined options are skipped.
 *   choice  : 'a' | 'b' | 'tie' (case-insensitive). Ties count as half a win
 *             to each side (standard for win-rate / Bradley–Terry).
 */

// Unit Separator (U+001F): a control char that cannot appear in an author key
// (e.g. 'human', 'llm:mis24b-instruct'), so composite map keys stay unambiguous.
const SEP = String.fromCharCode(31)

/** Order-independent key for an unordered author pair. Exported for tests. */
export function pairKey(a, b) {
  return a < b ? `${a}${SEP}${b}` : `${b}${SEP}${a}`
}
function dirKey(winner, loser) {
  return `${winner}${SEP}${loser}`
}

/**
 * Wilson score interval for a binomial proportion. Robust for small n and
 * extreme proportions (unlike the normal approximation). `successes` may be
 * fractional (ties contribute 0.5), which Wilson tolerates fine.
 * Returns proportions in [0, 1].
 */
export function wilsonInterval(successes, n, z = 1.96) {
  if (!n || n <= 0) return { low: 0, high: 0 }
  const phat = successes / n
  const z2 = z * z
  const denom = 1 + z2 / n
  const center = (phat + z2 / (2 * n)) / denom
  const margin = (z * Math.sqrt((phat * (1 - phat) + z2 / (4 * n)) / n)) / denom
  return { low: Math.max(0, center - margin), high: Math.min(1, center + margin) }
}

/**
 * Bradley–Terry strengths via the standard MM (minorization–maximization)
 * iteration: p_i ← W_i / Σ_j n_ij / (p_i + p_j), normalised each step to mean 1
 * (so the strengths sum to the number of authors — matches the convention where
 * an average system scores 1.0).
 *
 * IDENTIFIABILITY: Bradley–Terry strengths are only comparable WITHIN a connected
 * comparison graph. If the authors split into disconnected groups (no item ever
 * pits one group against the other), the mean-1 normalisation still emits a single
 * global ranking, but the cross-group ordering is a normalisation artefact with no
 * statistical meaning. In LLARS this is safe: the human reference is compared
 * against every LLM on each item, so the graph is connected through the human node.
 *
 * @param {string[]} keys author keys
 * @param {Object} wins map key → total wins (ties as 0.5)
 * @param {Object} pairCounts map pairKey(i,j) → number of comparisons between i and j
 */
export function bradleyTerry(keys, wins, pairCounts, { iterations = 500, tol = 1e-10 } = {}) {
  const n = keys.length
  if (n === 0) return {}
  if (n === 1) return { [keys[0]]: 1 }

  let p = {}
  keys.forEach(k => { p[k] = 1 })
  const nij = (i, j) => pairCounts[pairKey(i, j)] || 0

  for (let iter = 0; iter < iterations; iter++) {
    const pNew = {}
    for (const i of keys) {
      let denom = 0
      for (const j of keys) {
        if (i === j) continue
        const nn = nij(i, j)
        if (nn > 0) denom += nn / (p[i] + p[j])
      }
      const w = wins[i] || 0
      // denom === 0 means i never met anyone (isolated) → keep prior strength.
      pNew[i] = denom > 0 ? w / denom : p[i]
      // A winless author would collapse to 0; floor it so the value stays finite
      // and the row still renders (its strength is just very small).
      if (!(pNew[i] > 0)) pNew[i] = 1e-9
    }
    // Normalise to mean 1 (sum = n).
    const sum = keys.reduce((s, k) => s + pNew[k], 0)
    const scale = sum > 0 ? n / sum : 1
    let maxDelta = 0
    for (const k of keys) {
      pNew[k] *= scale
      maxDelta = Math.max(maxDelta, Math.abs(pNew[k] - p[k]))
    }
    p = pNew
    if (maxDelta < tol) break
  }
  return p
}

/**
 * Position-order (AB/BA) self-agreement of the raters: for a given rater and an
 * unordered author pair seen in BOTH slot orders, did they pick the SAME author
 * regardless of position? Returns a percentage, or null when there are no
 * mirrored presentations (the common case when every item has a fixed A/B).
 */
function computeSelfAgreement(votes) {
  const byJudgePair = {}
  for (const v of votes) {
    if (!v.username || v.a == null || v.b == null || v.a === v.b) continue
    const c = String(v.choice || '').toLowerCase()
    if (c !== 'a' && c !== 'b') continue // ties carry no positional signal
    const chosenAuthor = c === 'a' ? v.a : v.b
    const pk = pairKey(v.a, v.b)
    // Orientation = is the lexicographically-smaller author in the A slot?
    const orient = v.a < v.b ? 'AB' : 'BA'
    const k = `${v.username}${SEP}${pk}`
    if (!byJudgePair[k]) byJudgePair[k] = { AB: [], BA: [] }
    byJudgePair[k][orient].push(chosenAuthor)
  }
  const mode = arr => {
    const cnt = {}
    arr.forEach(x => { cnt[x] = (cnt[x] || 0) + 1 })
    return Object.keys(cnt).sort((a, b) => cnt[b] - cnt[a])[0]
  }
  let agree = 0
  let total = 0
  for (const k of Object.keys(byJudgePair)) {
    const g = byJudgePair[k]
    if (!g.AB.length || !g.BA.length) continue
    total++
    if (mode(g.AB) === mode(g.BA)) agree++
  }
  return total > 0 ? (agree / total) * 100 : null
}

/**
 * Main entry point. See module docstring for the vote shape and outputs.
 */
export function computeAuthorStats(votes) {
  const appearances = {}
  const wins = {}
  const labels = {}
  const pairCounts = {}
  const pairWins = {}
  let totalComparisons = 0

  const ensure = (k, label) => {
    if (k == null) return
    if (!(k in appearances)) { appearances[k] = 0; wins[k] = 0 }
    if (label && !labels[k]) labels[k] = label
  }

  for (const v of votes || []) {
    const a = v.a
    const b = v.b
    if (a == null || b == null || a === b) continue
    ensure(a, v.labelA)
    ensure(b, v.labelB)
    appearances[a]++
    appearances[b]++
    totalComparisons++
    const c = String(v.choice || '').toLowerCase()
    const pk = pairKey(a, b)
    pairCounts[pk] = (pairCounts[pk] || 0) + 1
    if (c === 'a') {
      wins[a] += 1
      pairWins[dirKey(a, b)] = (pairWins[dirKey(a, b)] || 0) + 1
    } else if (c === 'b') {
      wins[b] += 1
      pairWins[dirKey(b, a)] = (pairWins[dirKey(b, a)] || 0) + 1
    } else {
      // tie → half a win each
      wins[a] += 0.5
      wins[b] += 0.5
      pairWins[dirKey(a, b)] = (pairWins[dirKey(a, b)] || 0) + 0.5
      pairWins[dirKey(b, a)] = (pairWins[dirKey(b, a)] || 0) + 0.5
    }
  }

  const keys = Object.keys(appearances)
  const bt = bradleyTerry(keys, wins, pairCounts)

  const systems = keys.map(k => {
    const nApp = appearances[k]
    const w = wins[k]
    const ci = wilsonInterval(w, nApp)
    return {
      key: k,
      label: labels[k] || k,
      appearances: nApp,
      wins: w,
      winRatePct: nApp ? (w / nApp) * 100 : 0,
      ciLowPct: ci.low * 100,
      ciHighPct: ci.high * 100,
      bt: bt[k] ?? 0,
    }
  })
  // Rank by Bradley–Terry strength (win rate as tie-breaker).
  systems.sort((x, y) => (y.bt - x.bt) || (y.winRatePct - x.winRatePct))
  systems.forEach((s, i) => { s.rank = i + 1 })

  const pairings = Object.keys(pairCounts).map(pk => {
    const [k1, k2] = pk.split(SEP)
    const w1 = pairWins[dirKey(k1, k2)] || 0
    const w2 = pairWins[dirKey(k2, k1)] || 0
    const total = pairCounts[pk]
    return {
      aKey: k1,
      bKey: k2,
      aLabel: labels[k1] || k1,
      bLabel: labels[k2] || k2,
      aWins: w1,
      bWins: w2,
      total,
      aRatePct: total ? (w1 / total) * 100 : 0,
      bRatePct: total ? (w2 / total) * 100 : 0,
    }
  })
  pairings.sort((x, y) => (y.total - x.total) || x.aLabel.localeCompare(y.aLabel))

  return {
    systems,
    pairings,
    totalComparisons,
    selfAgreement: computeSelfAgreement(votes || []),
  }
}
