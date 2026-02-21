/**
 * AnalyticsConsentBanner Component Tests
 *
 * Tests for the LLARS analytics consent banner component.
 * Test IDs: COMP_ACB_001 - COMP_ACB_045
 *
 * Coverage:
 * - Rendering and structure
 * - Visibility conditions (shouldShow computed)
 * - Title and body text
 * - Action buttons
 * - Accept/Decline functionality
 * - Privacy link navigation
 * - Reactivity
 * - Edge cases
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import AnalyticsConsentBanner from '@/components/common/AnalyticsConsentBanner.vue'

// Mock router
const mockRouter = {
  push: vi.fn()
}

vi.mock('vue-router', () => ({
  useRouter: () => mockRouter
}))

// Mock analytics config and consent
const mockAnalyticsConfig = ref({})
const mockConsentState = ref(null)
const mockSetAnalyticsConsentState = vi.fn()

vi.mock('@/plugins/llars-metrics', () => ({
  useAnalyticsConfig: () => mockAnalyticsConfig,
  useAnalyticsConsent: () => mockConsentState,
  setAnalyticsConsentState: (...args) => mockSetAnalyticsConsentState(...args)
}))

function mountAnalyticsConsentBanner(options = {}) {
  return mount(AnalyticsConsentBanner, {
    global: {
      stubs: {
        'v-slide-y-reverse-transition': {
          template: '<div class="transition-stub"><slot /></div>'
        },
        'v-card': {
          template: '<div class="v-card" :class="{ [`elevation-${elevation}`]: elevation }"><slot /></div>',
          props: ['elevation']
        },
        'v-btn': {
          template: '<button class="v-btn" :class="[variant, `size-${size}`, color ? `bg-${color}` : \'\']" @click="$emit(\'click\')"><slot /></button>',
          props: ['variant', 'size', 'color']
        }
      }
    },
    ...options
  })
}

describe('AnalyticsConsentBanner', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockAnalyticsConfig.value = {}
    mockConsentState.value = null
  })

  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_ACB_001: renders when conditions are met', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }
      mockConsentState.value = null

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent').exists()).toBe(true)
    })

    it('COMP_ACB_002: has analytics-consent class', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent').exists()).toBe(true)
    })

    it('COMP_ACB_003: renders analytics-consent-card', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent-card').exists()).toBe(true)
    })

    it('COMP_ACB_004: renders analytics-consent-content', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent-content').exists()).toBe(true)
    })

    it('COMP_ACB_005: renders text container', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.text').exists()).toBe(true)
    })

    it('COMP_ACB_006: renders actions container', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.actions').exists()).toBe(true)
    })

    it('COMP_ACB_007: card has elevation 6', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.v-card').classes()).toContain('elevation-6')
    })
  })

  // ==================== Visibility Tests ====================

  describe('Visibility (shouldShow)', () => {
    it('COMP_ACB_008: hidden when matomo_enabled is false', () => {
      mockAnalyticsConfig.value = { matomo_enabled: false, require_consent: true }
      mockConsentState.value = null

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent').exists()).toBe(false)
    })

    it('COMP_ACB_009: hidden when require_consent is false', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: false }
      mockConsentState.value = null

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent').exists()).toBe(false)
    })

    it('COMP_ACB_010: hidden when consent is already granted', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }
      mockConsentState.value = 'granted'

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent').exists()).toBe(false)
    })

    it('COMP_ACB_011: hidden when consent is already denied', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }
      mockConsentState.value = 'denied'

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent').exists()).toBe(false)
    })

    it('COMP_ACB_012: shown when matomo_enabled and require_consent and no consent state', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }
      mockConsentState.value = null

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent').exists()).toBe(true)
    })

    it('COMP_ACB_013: shown with require_cookie_consent instead of require_consent', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_cookie_consent: true }
      mockConsentState.value = null

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent').exists()).toBe(true)
    })

    it('COMP_ACB_014: hidden when config is empty', () => {
      mockAnalyticsConfig.value = {}
      mockConsentState.value = null

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent').exists()).toBe(false)
    })

    it('COMP_ACB_015: hidden when config is null', () => {
      mockAnalyticsConfig.value = null
      mockConsentState.value = null

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent').exists()).toBe(false)
    })
  })

  // ==================== Title and Body Tests ====================

  describe('Title and Body', () => {
    it('COMP_ACB_016: displays correct title', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.title').text()).toBe('Analytics & Datenschutz')
    })

    it('COMP_ACB_017: displays body text', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      const bodyText = wrapper.find('.body').text()
      expect(bodyText).toContain('Matomo')
      expect(bodyText).toContain('Datenschutzerklärung')
    })

    it('COMP_ACB_018: body text mentions consent options', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      const bodyText = wrapper.find('.body').text()
      expect(bodyText).toContain('zustimmen')
      expect(bodyText).toContain('ablehnen')
    })
  })

  // ==================== Action Buttons Tests ====================

  describe('Action Buttons', () => {
    it('COMP_ACB_019: renders three action buttons', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      const buttons = wrapper.findAll('.actions .v-btn')
      expect(buttons.length).toBe(3)
    })

    it('COMP_ACB_020: privacy button has text variant', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      const buttons = wrapper.findAll('.actions .v-btn')
      expect(buttons[0].classes()).toContain('text')
    })

    it('COMP_ACB_021: privacy button has correct label', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      const buttons = wrapper.findAll('.actions .v-btn')
      expect(buttons[0].text()).toBe('Datenschutz')
    })

    it('COMP_ACB_022: decline button has outlined variant', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      const buttons = wrapper.findAll('.actions .v-btn')
      expect(buttons[1].classes()).toContain('outlined')
    })

    it('COMP_ACB_023: decline button has correct label', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      const buttons = wrapper.findAll('.actions .v-btn')
      expect(buttons[1].text()).toBe('Ablehnen')
    })

    it('COMP_ACB_024: accept button has primary color', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      const buttons = wrapper.findAll('.actions .v-btn')
      expect(buttons[2].classes()).toContain('bg-primary')
    })

    it('COMP_ACB_025: accept button has correct label', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      const buttons = wrapper.findAll('.actions .v-btn')
      expect(buttons[2].text()).toBe('Zustimmen')
    })

    it('COMP_ACB_026: all buttons have small size', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      const buttons = wrapper.findAll('.actions .v-btn')
      buttons.forEach(btn => {
        expect(btn.classes()).toContain('size-small')
      })
    })
  })

  // ==================== Accept Functionality Tests ====================

  describe('Accept Functionality', () => {
    it('COMP_ACB_027: clicking accept calls setAnalyticsConsentState with granted', async () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      const buttons = wrapper.findAll('.actions .v-btn')
      await buttons[2].trigger('click')

      expect(mockSetAnalyticsConsentState).toHaveBeenCalledWith('granted')
    })

    it('COMP_ACB_028: accept button calls correct function', async () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      const buttons = wrapper.findAll('.actions .v-btn')
      const acceptButton = buttons[2]

      expect(acceptButton.text()).toBe('Zustimmen')
      await acceptButton.trigger('click')

      expect(mockSetAnalyticsConsentState).toHaveBeenLastCalledWith('granted')
    })
  })

  // ==================== Decline Functionality Tests ====================

  describe('Decline Functionality', () => {
    it('COMP_ACB_029: clicking decline calls setAnalyticsConsentState with denied', async () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      const buttons = wrapper.findAll('.actions .v-btn')
      await buttons[1].trigger('click')

      expect(mockSetAnalyticsConsentState).toHaveBeenCalledWith('denied')
    })

    it('COMP_ACB_030: decline button calls correct function', async () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      const buttons = wrapper.findAll('.actions .v-btn')
      const declineButton = buttons[1]

      expect(declineButton.text()).toBe('Ablehnen')
      await declineButton.trigger('click')

      expect(mockSetAnalyticsConsentState).toHaveBeenLastCalledWith('denied')
    })
  })

  // ==================== Privacy Link Tests ====================

  describe('Privacy Link Navigation', () => {
    it('COMP_ACB_031: clicking privacy button navigates to /datenschutz', async () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      const buttons = wrapper.findAll('.actions .v-btn')
      await buttons[0].trigger('click')

      expect(mockRouter.push).toHaveBeenCalledWith('/datenschutz')
    })

    it('COMP_ACB_032: privacy button does not call setAnalyticsConsentState', async () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      const buttons = wrapper.findAll('.actions .v-btn')
      await buttons[0].trigger('click')

      expect(mockSetAnalyticsConsentState).not.toHaveBeenCalled()
    })
  })

  // ==================== Reactivity Tests ====================

  describe('Reactivity', () => {
    it('COMP_ACB_033: hides when consent state changes to granted', async () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }
      mockConsentState.value = null

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent').exists()).toBe(true)

      mockConsentState.value = 'granted'
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.analytics-consent').exists()).toBe(false)
    })

    it('COMP_ACB_034: hides when consent state changes to denied', async () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }
      mockConsentState.value = null

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent').exists()).toBe(true)

      mockConsentState.value = 'denied'
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.analytics-consent').exists()).toBe(false)
    })

    it('COMP_ACB_035: shows when config changes to enable consent', async () => {
      mockAnalyticsConfig.value = { matomo_enabled: false }
      mockConsentState.value = null

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent').exists()).toBe(false)

      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.analytics-consent').exists()).toBe(true)
    })

    it('COMP_ACB_036: hides when matomo_enabled changes to false', async () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }
      mockConsentState.value = null

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent').exists()).toBe(true)

      mockAnalyticsConfig.value = { matomo_enabled: false, require_consent: true }
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.analytics-consent').exists()).toBe(false)
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('COMP_ACB_037: handles undefined config gracefully', () => {
      mockAnalyticsConfig.value = undefined

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent').exists()).toBe(false)
    })

    it('COMP_ACB_038: handles consent state as empty string (falsy)', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }
      mockConsentState.value = ''

      const wrapper = mountAnalyticsConsentBanner()

      // Empty string is falsy, so banner should show
      expect(wrapper.find('.analytics-consent').exists()).toBe(true)
    })

    it('COMP_ACB_039: both require_consent and require_cookie_consent work', () => {
      mockAnalyticsConfig.value = {
        matomo_enabled: true,
        require_consent: true,
        require_cookie_consent: true
      }
      mockConsentState.value = null

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent').exists()).toBe(true)
    })

    it('COMP_ACB_040: handles multiple button clicks', async () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      const buttons = wrapper.findAll('.actions .v-btn')

      // Click accept
      await buttons[2].trigger('click')
      expect(mockSetAnalyticsConsentState).toHaveBeenLastCalledWith('granted')

      // Click decline
      await buttons[1].trigger('click')
      expect(mockSetAnalyticsConsentState).toHaveBeenLastCalledWith('denied')

      // Click accept again
      await buttons[2].trigger('click')
      expect(mockSetAnalyticsConsentState).toHaveBeenLastCalledWith('granted')
    })

    it('COMP_ACB_041: component uses v-slide-y-reverse-transition', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }

      const wrapper = mountAnalyticsConsentBanner()

      // The transition stub wraps the content
      expect(wrapper.find('.analytics-consent').exists()).toBe(true)
    })

    it('COMP_ACB_042: matomo_enabled false with require_consent true still hidden', () => {
      mockAnalyticsConfig.value = { matomo_enabled: false, require_consent: true }
      mockConsentState.value = null

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent').exists()).toBe(false)
    })

    it('COMP_ACB_043: matomo_enabled true with require_consent false still hidden', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: false }
      mockConsentState.value = null

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent').exists()).toBe(false)
    })

    it('COMP_ACB_044: clicking privacy does not dismiss banner', async () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }
      mockConsentState.value = null

      const wrapper = mountAnalyticsConsentBanner()

      const buttons = wrapper.findAll('.actions .v-btn')
      await buttons[0].trigger('click') // privacy

      // Banner should still be visible (consent state unchanged)
      expect(wrapper.find('.analytics-consent').exists()).toBe(true)
    })

    it('COMP_ACB_045: component works with minimal required config', () => {
      mockAnalyticsConfig.value = { matomo_enabled: true, require_consent: true }
      mockConsentState.value = null

      const wrapper = mountAnalyticsConsentBanner()

      expect(wrapper.find('.analytics-consent').exists()).toBe(true)
      expect(wrapper.find('.title').exists()).toBe(true)
      expect(wrapper.find('.body').exists()).toBe(true)
      expect(wrapper.findAll('.actions .v-btn').length).toBe(3)
    })
  })
})
