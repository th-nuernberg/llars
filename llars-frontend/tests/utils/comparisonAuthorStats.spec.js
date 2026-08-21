/**
 * Comparison Author Statistics Tests
 *
 * Tests for the author-level aggregation of pairwise comparison votes:
 * win rate + Wilson CI, Bradley–Terry strengths, pairwise win rates and
 * AB/BA self-agreement.
 *
 * Test IDs: UTIL_CAS_001 - UTIL_CAS_050
 */

import { describe, it, expect } from 'vitest'
import {
  wilsonInterval,
  bradleyTerry,
  computeAuthorStats,
  pairKey,
} from '@/utils/comparisonAuthorStats'

describe('wilsonInterval', () => {
  it('UTIL_CAS_001: returns [0,0] for n=0', () => {
    expect(wilsonInterval(0, 0)).toEqual({ low: 0, high: 0 })
  })

  it('UTIL_CAS_002: brackets the point estimate', () => {
    const { low, high } = wilsonInterval(7, 10)
    expect(low).toBeGreaterThan(0)
    expect(high).toBeLessThan(1)
    expect(low).toBeLessThan(0.7)
    expect(high).toBeGreaterThan(0.7)
  })

  it('UTIL_CAS_003: clamps to [0,1]', () => {
    const { low, high } = wilsonInterval(10, 10)
    expect(low).toBeGreaterThanOrEqual(0)
    expect(high).toBeLessThanOrEqual(1)
  })

  it('UTIL_CAS_004: tolerates fractional successes (ties)', () => {
    const { low, high } = wilsonInterval(5.5, 11)
    expect(low).toBeGreaterThan(0)
    expect(high).toBeLessThan(1)
    expect(low).toBeLessThan(0.5)
    expect(high).toBeGreaterThan(0.5)
  })
})

describe('bradleyTerry', () => {
  it('UTIL_CAS_010: single author → strength 1', () => {
    expect(bradleyTerry(['x'], { x: 0 }, {})).toEqual({ x: 1 })
  })

  it('UTIL_CAS_011: normalises to mean 1 (sum = #authors)', () => {
    const keys = ['h', 'm']
    // h beats m 8 of 10
    const wins = { h: 8, m: 2 }
    const pairCounts = { [pairKey('h', 'm')]: 10 }
    const p = bradleyTerry(keys, wins, pairCounts)
    const sum = keys.reduce((s, k) => s + p[k], 0)
    expect(sum).toBeCloseTo(2, 5)
    expect(p.h).toBeGreaterThan(p.m)
  })

  it('UTIL_CAS_012: stronger system gets higher strength across a star graph', () => {
    const keys = ['h', 'a', 'b']
    // human beats both a lot; a beats b moderately
    const wins = { h: 14, a: 6, b: 4 } // appearances differ; values illustrative
    const pc = {}
    pc[pairKey('h', 'a')] = 10
    pc[pairKey('h', 'b')] = 10
    pc[pairKey('a', 'b')] = 4
    const p = bradleyTerry(keys, wins, pc)
    expect(p.h).toBeGreaterThan(p.a)
    expect(p.a).toBeGreaterThan(p.b)
  })
})

describe('computeAuthorStats', () => {
  it('UTIL_CAS_020: empty input → empty result', () => {
    const r = computeAuthorStats([])
    expect(r.systems).toEqual([])
    expect(r.pairings).toEqual([])
    expect(r.totalComparisons).toBe(0)
    expect(r.selfAgreement).toBeNull()
  })

  it('UTIL_CAS_021: counts appearances, wins and win rate per author', () => {
    const votes = [
      { a: 'human', b: 'llm:m', choice: 'a', labelA: 'Mensch', labelB: 'm' },
      { a: 'human', b: 'llm:m', choice: 'a' },
      { a: 'human', b: 'llm:m', choice: 'b' },
      { a: 'human', b: 'llm:m', choice: 'b' },
    ]
    const r = computeAuthorStats(votes)
    expect(r.totalComparisons).toBe(4)
    const human = r.systems.find(s => s.key === 'human')
    const m = r.systems.find(s => s.key === 'llm:m')
    expect(human.appearances).toBe(4)
    expect(human.wins).toBe(2)
    expect(human.winRatePct).toBe(50)
    expect(m.winRatePct).toBe(50)
    expect(human.label).toBe('Mensch')
  })

  it('UTIL_CAS_022: ties count as half a win to each side', () => {
    const votes = [
      { a: 'human', b: 'llm:m', choice: 'tie' },
      { a: 'human', b: 'llm:m', choice: 'tie' },
    ]
    const r = computeAuthorStats(votes)
    const human = r.systems.find(s => s.key === 'human')
    expect(human.wins).toBe(1) // 0.5 + 0.5
    expect(human.winRatePct).toBe(50)
  })

  it('UTIL_CAS_023: ranks the more-often-chosen author first', () => {
    const votes = [
      { a: 'human', b: 'llm:m', choice: 'a' },
      { a: 'human', b: 'llm:m', choice: 'a' },
      { a: 'human', b: 'llm:m', choice: 'a' },
      { a: 'human', b: 'llm:m', choice: 'b' },
    ]
    const r = computeAuthorStats(votes)
    expect(r.systems[0].key).toBe('human')
    expect(r.systems[0].rank).toBe(1)
    expect(r.systems[1].rank).toBe(2)
  })

  it('UTIL_CAS_024: builds pairwise win rates summing to ~100', () => {
    const votes = [
      { a: 'human', b: 'llm:m', choice: 'a', labelA: 'Mensch', labelB: 'm' },
      { a: 'human', b: 'llm:m', choice: 'a' },
      { a: 'human', b: 'llm:m', choice: 'b' },
    ]
    const r = computeAuthorStats(votes)
    expect(r.pairings).toHaveLength(1)
    const p = r.pairings[0]
    expect(p.total).toBe(3)
    expect(Math.round(p.aRatePct + p.bRatePct)).toBe(100)
  })

  it('UTIL_CAS_025: ignores votes with a missing option source', () => {
    const votes = [
      { a: 'human', b: null, choice: 'a' },
      { a: null, b: 'llm:m', choice: 'b' },
      { a: 'human', b: 'llm:m', choice: 'a' },
    ]
    const r = computeAuthorStats(votes)
    expect(r.totalComparisons).toBe(1)
  })

  it('UTIL_CAS_026: self-agreement is null without mirrored presentations', () => {
    const votes = [
      { username: 'u1', a: 'human', b: 'llm:m', choice: 'a' },
      { username: 'u1', a: 'human', b: 'llm:m', choice: 'a' },
    ]
    expect(computeAuthorStats(votes).selfAgreement).toBeNull()
  })

  it('UTIL_CAS_027: self-agreement computed across AB/BA mirror, position-independent', () => {
    // u1 picks the human in both orders → agrees; u2 flips with position → disagrees
    const votes = [
      { username: 'u1', a: 'human', b: 'llm:m', choice: 'a' }, // chose human (A slot)
      { username: 'u1', a: 'llm:m', b: 'human', choice: 'b' }, // chose human (B slot)
      { username: 'u2', a: 'human', b: 'llm:m', choice: 'a' }, // chose human (A slot)
      { username: 'u2', a: 'llm:m', b: 'human', choice: 'a' }, // chose llm (A slot)
    ]
    const r = computeAuthorStats(votes)
    expect(r.selfAgreement).toBeCloseTo(50, 5)
  })
})
