/**
 * Generation Output Parser Tests
 *
 * Tests for parsing LLM generation output with think/thinking blocks.
 * Test IDs: UTIL_GEN_001 - UTIL_GEN_040
 */

import { describe, it, expect } from 'vitest'
import {
  parseGenerationOutput,
  previewGenerationOutput
} from '@/utils/generationOutputParser'

// ==================== parseGenerationOutput Tests ====================

describe('parseGenerationOutput', () => {
  it('UTIL_GEN_001: returns empty result for null input', () => {
    const result = parseGenerationOutput(null)
    expect(result.visibleContent).toBe('')
    expect(result.thoughtsContent).toBe('')
    expect(result.hasThoughts).toBe(false)
  })

  it('UTIL_GEN_002: returns empty result for undefined input', () => {
    const result = parseGenerationOutput(undefined)
    expect(result.visibleContent).toBe('')
    expect(result.thoughtsContent).toBe('')
    expect(result.hasThoughts).toBe(false)
  })

  it('UTIL_GEN_003: returns empty result for empty string', () => {
    const result = parseGenerationOutput('')
    expect(result.visibleContent).toBe('')
    expect(result.thoughtsContent).toBe('')
    expect(result.hasThoughts).toBe(false)
  })

  it('UTIL_GEN_004: returns text as-is when no think blocks', () => {
    const result = parseGenerationOutput('Hello, World!')
    expect(result.visibleContent).toBe('Hello, World!')
    expect(result.thoughtsContent).toBe('')
    expect(result.hasThoughts).toBe(false)
  })

  it('UTIL_GEN_005: extracts content from <think> block', () => {
    const input = '<think>I need to think about this</think>Here is the answer.'
    const result = parseGenerationOutput(input)
    expect(result.visibleContent).toBe('Here is the answer.')
    expect(result.thoughtsContent).toBe('I need to think about this')
    expect(result.hasThoughts).toBe(true)
  })

  it('UTIL_GEN_006: extracts content from <thinking> block', () => {
    const input = '<thinking>Processing...</thinking>The result is 42.'
    const result = parseGenerationOutput(input)
    expect(result.visibleContent).toBe('The result is 42.')
    expect(result.thoughtsContent).toBe('Processing...')
    expect(result.hasThoughts).toBe(true)
  })

  it('UTIL_GEN_007: handles multiple think blocks', () => {
    const input = '<think>First thought</think>Visible part<think>Second thought</think> more text.'
    const result = parseGenerationOutput(input)
    expect(result.visibleContent).toContain('Visible part')
    expect(result.visibleContent).toContain('more text.')
    expect(result.thoughtsContent).toContain('First thought')
    expect(result.thoughtsContent).toContain('Second thought')
    expect(result.hasThoughts).toBe(true)
  })

  it('UTIL_GEN_008: handles think block with multiline content', () => {
    const input = '<think>\nLine 1\nLine 2\nLine 3\n</think>Answer here.'
    const result = parseGenerationOutput(input)
    expect(result.visibleContent).toBe('Answer here.')
    expect(result.thoughtsContent).toContain('Line 1')
    expect(result.thoughtsContent).toContain('Line 2')
    expect(result.thoughtsContent).toContain('Line 3')
  })

  it('UTIL_GEN_009: handles dangling open think tag (streaming)', () => {
    const input = 'Visible content<think>Still thinking... incomplete'
    const result = parseGenerationOutput(input)
    expect(result.visibleContent).toBe('Visible content')
    expect(result.thoughtsContent).toContain('Still thinking... incomplete')
    expect(result.hasThoughts).toBe(true)
  })

  it('UTIL_GEN_010: handles empty think block', () => {
    const input = '<think></think>Just the answer.'
    const result = parseGenerationOutput(input)
    expect(result.visibleContent).toBe('Just the answer.')
    expect(result.thoughtsContent).toBe('')
    expect(result.hasThoughts).toBe(false)
  })

  it('UTIL_GEN_011: normalizes \\r\\n to \\n', () => {
    const input = 'Line 1\r\nLine 2\r\n'
    const result = parseGenerationOutput(input)
    expect(result.visibleContent).toContain('Line 1\nLine 2')
  })

  it('UTIL_GEN_012: trims whitespace from visible content', () => {
    const input = '  <think>thoughts</think>  answer  '
    const result = parseGenerationOutput(input)
    expect(result.visibleContent).toBe('answer')
  })

  it('UTIL_GEN_013: trims whitespace from thoughts content', () => {
    const input = '<think>  thoughts  </think>answer'
    const result = parseGenerationOutput(input)
    expect(result.thoughtsContent).toBe('thoughts')
  })

  it('UTIL_GEN_014: handles case-insensitive think tags', () => {
    const input = '<Think>Thought</Think>Answer'
    const result = parseGenerationOutput(input)
    expect(result.visibleContent).toBe('Answer')
    expect(result.thoughtsContent).toBe('Thought')
  })

  it('UTIL_GEN_015: handles spaces in think tags', () => {
    const input = '< think >Thought</ think >Answer'
    const result = parseGenerationOutput(input)
    expect(result.visibleContent).toBe('Answer')
    expect(result.thoughtsContent).toBe('Thought')
  })

  it('UTIL_GEN_016: handles non-string input by converting to string', () => {
    const result = parseGenerationOutput(12345)
    expect(result.visibleContent).toBe('12345')
    expect(result.hasThoughts).toBe(false)
  })

  it('UTIL_GEN_017: removes stray closing think tags', () => {
    const input = 'Answer</think> text'
    const result = parseGenerationOutput(input)
    expect(result.visibleContent).not.toContain('</think>')
    expect(result.visibleContent).toContain('Answer')
    expect(result.visibleContent).toContain('text')
  })

  it('UTIL_GEN_018: joins multiple thought chunks with double newline', () => {
    const input = '<think>Thought A</think>Middle<think>Thought B</think>End'
    const result = parseGenerationOutput(input)
    expect(result.thoughtsContent).toBe('Thought A\n\nThought B')
  })

  it('UTIL_GEN_019: handles dangling <thinking> tag', () => {
    const input = 'Hello <thinking>still processing'
    const result = parseGenerationOutput(input)
    expect(result.visibleContent).toBe('Hello')
    expect(result.thoughtsContent).toContain('still processing')
    expect(result.hasThoughts).toBe(true)
  })
})

// ==================== previewGenerationOutput Tests ====================

describe('previewGenerationOutput', () => {
  it('UTIL_GEN_020: returns empty string for null input', () => {
    expect(previewGenerationOutput(null)).toBe('')
  })

  it('UTIL_GEN_021: returns empty string for empty input', () => {
    expect(previewGenerationOutput('')).toBe('')
  })

  it('UTIL_GEN_022: returns full text when under maxLength', () => {
    const text = 'Short answer.'
    expect(previewGenerationOutput(text)).toBe('Short answer.')
  })

  it('UTIL_GEN_023: truncates text exceeding maxLength', () => {
    const text = 'A'.repeat(300)
    const result = previewGenerationOutput(text, 200)
    expect(result.length).toBeLessThanOrEqual(200)
    expect(result.endsWith('...')).toBe(true)
  })

  it('UTIL_GEN_024: strips think blocks before previewing', () => {
    const input = '<think>Long thought content here</think>Short answer.'
    const result = previewGenerationOutput(input)
    expect(result).toBe('Short answer.')
    expect(result).not.toContain('think')
  })

  it('UTIL_GEN_025: respects custom maxLength', () => {
    const text = 'Hello, World! This is a test string.'
    const result = previewGenerationOutput(text, 10)
    expect(result.length).toBeLessThanOrEqual(10)
    expect(result.endsWith('...')).toBe(true)
  })

  it('UTIL_GEN_026: default maxLength is 200', () => {
    const text = 'A'.repeat(250)
    const result = previewGenerationOutput(text)
    expect(result.length).toBeLessThanOrEqual(200)
  })

  it('UTIL_GEN_027: returns exact text at boundary length', () => {
    const text = 'A'.repeat(200)
    const result = previewGenerationOutput(text, 200)
    expect(result).toBe(text)
    expect(result.endsWith('...')).toBe(false)
  })

  it('UTIL_GEN_028: returns empty for input with only think blocks', () => {
    const input = '<think>All thoughts, no answer</think>'
    const result = previewGenerationOutput(input)
    expect(result).toBe('')
  })
})
