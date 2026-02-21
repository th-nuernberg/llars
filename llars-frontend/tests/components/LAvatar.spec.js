/**
 * LAvatar Component Tests
 *
 * Tests for the LLARS avatar component with DiceBear integration.
 * Test IDs: COMP_AVT_001 - COMP_AVT_055
 *
 * Coverage:
 * - Rendering and structure
 * - Size variants (xs, sm, md, lg, xl)
 * - Image source handling (custom src, generated, fallback)
 * - DiceBear URL generation
 * - Color generation from seed/username
 * - Fallback initial display
 * - Error handling
 * - Clickable state
 * - Watchers and reactivity
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import LAvatar from '@/components/common/LAvatar.vue'

function mountLAvatar(props = {}, options = {}) {
  return mount(LAvatar, {
    props,
    ...options
  })
}

describe('LAvatar', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_AVT_001: renders with default props', () => {
      const wrapper = mountLAvatar()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-avatar').exists()).toBe(true)
    })

    it('COMP_AVT_002: has l-avatar class', () => {
      const wrapper = mountLAvatar()

      expect(wrapper.classes()).toContain('l-avatar')
    })

    it('COMP_AVT_003: applies default size class (md)', () => {
      const wrapper = mountLAvatar()

      expect(wrapper.classes()).toContain('l-avatar--md')
    })

    it('COMP_AVT_004: renders image when avatarUrl is available', () => {
      const wrapper = mountLAvatar({ username: 'testuser' })

      expect(wrapper.find('img').exists()).toBe(true)
    })

    it('COMP_AVT_005: renders fallback span when no image available', async () => {
      const wrapper = mountLAvatar({ username: 'testuser' })

      // Simulate both images failing
      await wrapper.find('img').trigger('error')
      await nextTick()
      // After first error, still shows generated avatar
      if (wrapper.find('img').exists()) {
        await wrapper.find('img').trigger('error')
        await nextTick()
      }

      expect(wrapper.find('.l-avatar__fallback').exists()).toBe(true)
    })
  })

  // ==================== Size Tests ====================

  describe('Sizes', () => {
    const sizes = ['xs', 'sm', 'md', 'lg', 'xl']
    const sizePixels = { xs: 24, sm: 32, md: 40, lg: 56, xl: 80 }

    sizes.forEach((size, index) => {
      it(`COMP_AVT_${String(6 + index).padStart(3, '0')}: renders ${size} size correctly`, () => {
        const wrapper = mountLAvatar({ size })

        expect(wrapper.classes()).toContain(`l-avatar--${size}`)
      })
    })

    it('COMP_AVT_011: applies correct width for xs size', () => {
      const wrapper = mountLAvatar({ size: 'xs' })

      expect(wrapper.attributes('style')).toContain('width: 24px')
      expect(wrapper.attributes('style')).toContain('height: 24px')
    })

    it('COMP_AVT_012: applies correct width for md size', () => {
      const wrapper = mountLAvatar({ size: 'md' })

      expect(wrapper.attributes('style')).toContain('width: 40px')
      expect(wrapper.attributes('style')).toContain('height: 40px')
    })

    it('COMP_AVT_013: applies correct width for xl size', () => {
      const wrapper = mountLAvatar({ size: 'xl' })

      expect(wrapper.attributes('style')).toContain('width: 80px')
      expect(wrapper.attributes('style')).toContain('height: 80px')
    })
  })

  // ==================== Image Source Tests ====================

  describe('Image Source', () => {
    it('COMP_AVT_014: uses custom src when provided', () => {
      const wrapper = mountLAvatar({ src: 'https://example.com/avatar.png' })
      const img = wrapper.find('img')

      expect(img.attributes('src')).toBe('https://example.com/avatar.png')
    })

    it('COMP_AVT_015: generates DiceBear URL when no src provided', () => {
      const wrapper = mountLAvatar({ username: 'testuser' })
      const img = wrapper.find('img')

      expect(img.attributes('src')).toContain('api.dicebear.com')
    })

    it('COMP_AVT_016: includes seed in DiceBear URL', () => {
      const wrapper = mountLAvatar({ seed: 'unique-seed' })
      const img = wrapper.find('img')

      expect(img.attributes('src')).toContain('seed=unique-seed')
    })

    it('COMP_AVT_017: uses username as seed fallback', () => {
      const wrapper = mountLAvatar({ username: 'johndoe' })
      const img = wrapper.find('img')

      expect(img.attributes('src')).toContain('seed=johndoe')
    })

    it('COMP_AVT_018: uses "anonymous" when no seed or username', () => {
      const wrapper = mountLAvatar()
      const img = wrapper.find('img')

      expect(img.attributes('src')).toContain('seed=anonymous')
    })

    it('COMP_AVT_019: includes variant in DiceBear URL', () => {
      const wrapper = mountLAvatar({ variant: 'identicon' })
      const img = wrapper.find('img')

      expect(img.attributes('src')).toContain('/identicon/')
    })

    it('COMP_AVT_020: uses default variant (bottts-neutral)', () => {
      const wrapper = mountLAvatar()
      const img = wrapper.find('img')

      expect(img.attributes('src')).toContain('/bottts-neutral/')
    })

    it('COMP_AVT_021: includes size parameter (2x for retina)', () => {
      const wrapper = mountLAvatar({ size: 'md' })
      const img = wrapper.find('img')

      // md = 40px, 2x for retina = 80
      expect(img.attributes('src')).toContain('size=80')
    })

    it('COMP_AVT_022: includes backgroundColor in DiceBear URL', () => {
      const wrapper = mountLAvatar({ backgroundColor: 'ff0000' })
      const img = wrapper.find('img')

      expect(img.attributes('src')).toContain('backgroundColor=ff0000')
    })
  })

  // ==================== Fallback Tests ====================

  describe('Fallback Initial', () => {
    it('COMP_AVT_023: shows question mark when no username', async () => {
      const wrapper = mountLAvatar()

      // Trigger errors to show fallback
      await wrapper.find('img').trigger('error')
      await nextTick()
      if (wrapper.find('img').exists()) {
        await wrapper.find('img').trigger('error')
        await nextTick()
      }

      expect(wrapper.find('.l-avatar__fallback').text()).toBe('?')
    })

    it('COMP_AVT_024: shows first letter of username capitalized', async () => {
      const wrapper = mountLAvatar({ username: 'johndoe' })

      await wrapper.find('img').trigger('error')
      await nextTick()
      if (wrapper.find('img').exists()) {
        await wrapper.find('img').trigger('error')
        await nextTick()
      }

      expect(wrapper.find('.l-avatar__fallback').text()).toBe('J')
    })

    it('COMP_AVT_025: capitalizes lowercase initial', async () => {
      const wrapper = mountLAvatar({ username: 'alice' })

      await wrapper.find('img').trigger('error')
      await nextTick()
      if (wrapper.find('img').exists()) {
        await wrapper.find('img').trigger('error')
        await nextTick()
      }

      expect(wrapper.find('.l-avatar__fallback').text()).toBe('A')
    })

    it('COMP_AVT_026: handles already uppercase initial', async () => {
      const wrapper = mountLAvatar({ username: 'Bob' })

      await wrapper.find('img').trigger('error')
      await nextTick()
      if (wrapper.find('img').exists()) {
        await wrapper.find('img').trigger('error')
        await nextTick()
      }

      expect(wrapper.find('.l-avatar__fallback').text()).toBe('B')
    })

    it('COMP_AVT_027: handles empty username', async () => {
      const wrapper = mountLAvatar({ username: '' })

      await wrapper.find('img').trigger('error')
      await nextTick()
      if (wrapper.find('img').exists()) {
        await wrapper.find('img').trigger('error')
        await nextTick()
      }

      expect(wrapper.find('.l-avatar__fallback').text()).toBe('?')
    })
  })

  // ==================== Alt Text Tests ====================

  describe('Alt Text', () => {
    it('COMP_AVT_028: uses custom alt when provided', () => {
      const wrapper = mountLAvatar({ alt: 'Profile picture', username: 'user' })
      const img = wrapper.find('img')

      expect(img.attributes('alt')).toBe('Profile picture')
    })

    it('COMP_AVT_029: uses username as alt fallback', () => {
      const wrapper = mountLAvatar({ username: 'johndoe' })
      const img = wrapper.find('img')

      expect(img.attributes('alt')).toBe('johndoe')
    })

    it('COMP_AVT_030: uses empty string when no alt or username', () => {
      const wrapper = mountLAvatar()
      const img = wrapper.find('img')

      expect(img.attributes('alt')).toBe('')
    })
  })

  // ==================== Clickable Tests ====================

  describe('Clickable', () => {
    it('COMP_AVT_031: does not have clickable class by default', () => {
      const wrapper = mountLAvatar()

      expect(wrapper.classes()).not.toContain('l-avatar--clickable')
    })

    it('COMP_AVT_032: has clickable class when clickable prop is true', () => {
      const wrapper = mountLAvatar({ clickable: true })

      expect(wrapper.classes()).toContain('l-avatar--clickable')
    })

    it('COMP_AVT_033: does not have clickable class when clickable is false', () => {
      const wrapper = mountLAvatar({ clickable: false })

      expect(wrapper.classes()).not.toContain('l-avatar--clickable')
    })
  })

  // ==================== Background Color Tests ====================

  describe('Background Color', () => {
    it('COMP_AVT_034: uses custom backgroundColor in DiceBear URL', () => {
      const wrapper = mountLAvatar({ backgroundColor: 'ff5500', username: 'test' })
      const img = wrapper.find('img')

      // Custom backgroundColor is passed to DiceBear API
      expect(img.attributes('src')).toContain('backgroundColor=ff5500')
    })

    it('COMP_AVT_035: generates consistent color from seed', () => {
      const wrapper1 = mountLAvatar({ seed: 'same-seed' })
      const wrapper2 = mountLAvatar({ seed: 'same-seed' })

      expect(wrapper1.find('img').attributes('src')).toBe(wrapper2.find('img').attributes('src'))
    })

    it('COMP_AVT_036: generates different colors for different seeds', () => {
      const wrapper1 = mountLAvatar({ seed: 'seed-one' })
      const wrapper2 = mountLAvatar({ seed: 'seed-two' })

      const url1 = wrapper1.find('img').attributes('src')
      const url2 = wrapper2.find('img').attributes('src')

      // URLs should be different due to different seeds and potentially colors
      expect(url1).not.toBe(url2)
    })

    it('COMP_AVT_037: has transparent background when image is loaded', () => {
      const wrapper = mountLAvatar({ src: 'https://example.com/avatar.png' })

      expect(wrapper.attributes('style')).toContain('background-color: transparent')
    })
  })

  // ==================== Error Handling Tests ====================

  describe('Error Handling', () => {
    it('COMP_AVT_038: falls back to generated avatar when custom src fails', async () => {
      const wrapper = mountLAvatar({ src: 'invalid.jpg', username: 'test' })

      // First error - custom image fails
      await wrapper.find('img').trigger('error')
      await nextTick()

      // Should now show generated avatar
      expect(wrapper.find('img').attributes('src')).toContain('api.dicebear.com')
    })

    it('COMP_AVT_039: shows fallback initial when both images fail', async () => {
      const wrapper = mountLAvatar({ src: 'invalid.jpg', username: 'test' })

      // First error - custom image fails
      await wrapper.find('img').trigger('error')
      await nextTick()

      // Second error - generated avatar fails
      if (wrapper.find('img').exists()) {
        await wrapper.find('img').trigger('error')
        await nextTick()
      }

      expect(wrapper.find('.l-avatar__fallback').exists()).toBe(true)
    })

    it('COMP_AVT_040: resets error state when src changes', async () => {
      const wrapper = mountLAvatar({ src: 'invalid.jpg', username: 'test' })

      await wrapper.find('img').trigger('error')
      await nextTick()

      // Change src
      await wrapper.setProps({ src: 'new-image.jpg' })
      await nextTick()

      // Should show new custom image
      expect(wrapper.find('img').attributes('src')).toBe('new-image.jpg')
    })

    it('COMP_AVT_041: resets generated error when seed changes', async () => {
      const wrapper = mountLAvatar({ username: 'test' })

      await wrapper.find('img').trigger('error')
      await nextTick()
      if (wrapper.find('img').exists()) {
        await wrapper.find('img').trigger('error')
        await nextTick()
      }

      // Should show fallback
      expect(wrapper.find('.l-avatar__fallback').exists()).toBe(true)

      // Change seed
      await wrapper.setProps({ seed: 'new-seed' })
      await nextTick()

      // Should show generated avatar again
      expect(wrapper.find('img').exists()).toBe(true)
    })
  })

  // ==================== Variant Tests ====================

  describe('Variants', () => {
    const variants = ['bottts', 'shapes', 'thumbs', 'fun-emoji', 'lorelei-neutral', 'identicon', 'rings']

    variants.forEach((variant, index) => {
      it(`COMP_AVT_${String(42 + index).padStart(3, '0')}: renders ${variant} variant`, () => {
        const wrapper = mountLAvatar({ variant })
        const img = wrapper.find('img')

        expect(img.attributes('src')).toContain(`/${variant}/`)
      })
    })
  })

  // ==================== Style Tests ====================

  describe('Styles', () => {
    it('COMP_AVT_049: image has l-avatar__image class', () => {
      const wrapper = mountLAvatar({ username: 'test' })

      expect(wrapper.find('img').classes()).toContain('l-avatar__image')
    })

    it('COMP_AVT_050: fallback has l-avatar__fallback class', async () => {
      const wrapper = mountLAvatar({ username: 'test' })

      await wrapper.find('img').trigger('error')
      await nextTick()
      if (wrapper.find('img').exists()) {
        await wrapper.find('img').trigger('error')
        await nextTick()
      }

      expect(wrapper.find('.l-avatar__fallback').exists()).toBe(true)
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('COMP_AVT_051: handles special characters in username', () => {
      const wrapper = mountLAvatar({ username: 'user@example.com' })
      const img = wrapper.find('img')

      expect(img.attributes('src')).toContain(encodeURIComponent('user@example.com'))
    })

    it('COMP_AVT_052: handles unicode in username', () => {
      const wrapper = mountLAvatar({ username: '用户' })
      const img = wrapper.find('img')

      expect(img.attributes('src')).toContain('seed=')
    })

    it('COMP_AVT_053: handles numeric seed', () => {
      const wrapper = mountLAvatar({ seed: '12345' })
      const img = wrapper.find('img')

      expect(img.attributes('src')).toContain('seed=12345')
    })

    it('COMP_AVT_054: handles spaces in username', () => {
      const wrapper = mountLAvatar({ username: 'John Doe' })
      const img = wrapper.find('img')

      expect(img.attributes('src')).toContain(encodeURIComponent('John Doe'))
    })

    it('COMP_AVT_055: seed takes precedence over username', () => {
      const wrapper = mountLAvatar({ seed: 'my-seed', username: 'username' })
      const img = wrapper.find('img')

      expect(img.attributes('src')).toContain('seed=my-seed')
      expect(img.attributes('src')).not.toContain('seed=username')
    })
  })
})
