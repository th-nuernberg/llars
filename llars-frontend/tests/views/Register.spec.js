/**
 * Register.vue (/join/:code) Tests
 *
 * Covers the existing-account referral flow:
 *  - An ALREADY-authenticated visitor on /join/:code is auto-redeemed and
 *    routed straight to /scenarios/<target_scenario_id>/evaluate (no form).
 *  - already_enrolled still routes into the evaluation (idempotent).
 *  - Redeem failure falls back to /Home.
 *  - The "already registered" login link carries the referral code so the
 *    user returns to /join/<code> after authenticating.
 *
 * Test IDs: REG_JOIN_001 - REG_JOIN_006
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

// --- Router mock: configurable route + push spy -------------------------
const pushSpy = vi.fn()
const currentRoute = { params: {}, query: {} }
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: pushSpy }),
  useRoute: () => currentRoute,
}))

// --- Vuetify theme mock (avoid pulling a full Vuetify instance) ---------
vi.mock('vuetify', () => ({
  useTheme: () => ({ global: { current: { value: { dark: false } } } }),
}))

// --- Auth mock: toggle authentication per-test --------------------------
import { ref } from 'vue'
const isAuthenticatedRef = ref(false)
vi.mock('@/composables/useAuth', () => ({
  useAuth: () => ({ isAuthenticated: isAuthenticatedRef }),
}))

// --- Redeem mock --------------------------------------------------------
const redeemSpy = vi.fn()
vi.mock('@/composables/useReferralRedeem', () => ({
  useReferralRedeem: () => ({
    loading: ref(false),
    error: ref(''),
    result: ref(null),
    redeem: redeemSpy,
  }),
}))

// --- Referral system mock (registration form path) ----------------------
vi.mock('@/composables/useReferralSystem', () => ({
  useReferralSystem: () => ({
    checkRegistrationStatus: vi.fn().mockResolvedValue(true),
    validateReferralCode: vi.fn().mockResolvedValue({ valid: true }),
  }),
}))

// --- Study consent mock -------------------------------------------------
vi.mock('@/composables/useStudyConsent', () => ({
  useStudyConsent: () => ({
    consent: ref(null),
    clearConsent: vi.fn(),
    setConsent: vi.fn(),
  }),
}))

// --- Mobile mock --------------------------------------------------------
vi.mock('@/composables/useMobile', () => ({
  useMobile: () => ({ isMobile: ref(false), isIOS: ref(false) }),
}))

import Register from '@/views/Register.vue'

function mountRegister() {
  return mount(Register, {
    global: {
      // Stub Vuetify + L-components so we don't pull the whole framework in.
      // Any Vuetify/L component left unstubbed renders for real and throws
      // "[Vuetify] Could not find defaults instance" without a Vuetify plugin.
      // Register.vue uses the L-wrappers (LBtn/LCheckbox/LIcon) and the
      // enrollment confirmation v-dialog — all must be stubbed here.
      stubs: {
        'v-form': { template: '<form><slot /></form>' },
        'v-text-field': { template: '<div class="v-text-field-stub"><slot name="append-inner" /></div>' },
        'v-alert': { template: '<div class="v-alert-stub"><slot /></div>' },
        'v-icon': { template: '<i class="v-icon-stub"><slot /></i>' },
        'v-progress-linear': { template: '<div class="v-progress-linear-stub" />' },
        // The confirmation pop-up: only render its content when open
        // (modelValue), mirroring v-dialog so the success CTA is present
        // exactly when redeemSucceeded is true.
        'v-dialog': {
          props: ['modelValue'],
          template: '<div class="v-dialog-stub" v-if="modelValue"><slot /></div>',
        },
        // L-wrappers. data-testid and @click fall through to the root element
        // (Vue 3 attribute fallthrough), so trigger('click') fires goToStudy.
        'LBtn': { template: '<button><slot /></button>' },
        'LCheckbox': { template: '<div class="l-checkbox-stub" />' },
        'LIcon': { template: '<i class="l-icon-stub"><slot /></i>' },
        'router-link': {
          template: '<a :data-to="JSON.stringify(to)"><slot /></a>',
          props: ['to'],
        },
      },
      mocks: {
        $t: (k) => k,
      },
    },
  })
}

describe('Register.vue (/join/:code)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    isAuthenticatedRef.value = false
    currentRoute.params = {}
    currentRoute.query = {}
  })

  it('REG_JOIN_001: authenticated visitor with code → confirmation pop-up, then routes to evaluation on CTA', async () => {
    isAuthenticatedRef.value = true
    currentRoute.params = { code: 'kann-ki-beratung-test' }
    redeemSpy.mockResolvedValue({
      success: true,
      data: { success: true, target_scenario_id: 42, already_enrolled: false },
    })

    const wrapper = mountRegister()
    await flushPromises()

    expect(redeemSpy).toHaveBeenCalledWith('kann-ki-beratung-test')
    // The registration form must NOT render for an authenticated joiner.
    expect(wrapper.find('[data-testid="register-form"]').exists()).toBe(false)
    // The enrollment confirmation pop-up ("Sie sind in der Studie eingetragen")
    // is shown; routing into the evaluation happens only when the user clicks
    // "Zur Studie" (goToStudy), not automatically.
    const cta = wrapper.find('[data-testid="join-success-cta"]')
    expect(cta.exists()).toBe(true)
    expect(pushSpy).not.toHaveBeenCalled()

    await cta.trigger('click')
    expect(pushSpy).toHaveBeenCalledWith('/scenarios/42/evaluate')
  })

  it('REG_JOIN_002: already_enrolled still routes into the evaluation (via confirmation pop-up)', async () => {
    isAuthenticatedRef.value = true
    currentRoute.params = { code: 'study-code' }
    redeemSpy.mockResolvedValue({
      success: true,
      data: { success: true, target_scenario_id: 7, already_enrolled: true },
    })

    const wrapper = mountRegister()
    await flushPromises()

    const cta = wrapper.find('[data-testid="join-success-cta"]')
    expect(cta.exists()).toBe(true)
    await cta.trigger('click')
    expect(pushSpy).toHaveBeenCalledWith('/scenarios/7/evaluate')
  })

  it('REG_JOIN_003: redeem failure falls back to /Home', async () => {
    isAuthenticatedRef.value = true
    currentRoute.params = { code: 'bad-code' }
    redeemSpy.mockResolvedValue({ success: false, error: 'Ungültiger Einladungscode' })

    mountRegister()
    await flushPromises()

    expect(pushSpy).toHaveBeenCalledWith('/Home')
  })

  it('REG_JOIN_004: redeem success without target scenario routes to /Home', async () => {
    isAuthenticatedRef.value = true
    currentRoute.params = { code: 'no-scenario' }
    redeemSpy.mockResolvedValue({
      success: true,
      data: { success: true, target_scenario_id: null },
    })

    mountRegister()
    await flushPromises()

    expect(pushSpy).toHaveBeenCalledWith('/Home')
  })

  it('REG_JOIN_005: anonymous visitor with code does NOT auto-redeem; login link carries the code', async () => {
    isAuthenticatedRef.value = false
    currentRoute.params = { code: 'kann-ki-beratung-test' }

    const wrapper = mountRegister()
    await flushPromises()

    expect(redeemSpy).not.toHaveBeenCalled()
    // Registration form is shown for the anonymous visitor.
    expect(wrapper.find('[data-testid="register-form"]').exists()).toBe(true)

    const link = wrapper.find('[data-testid="login-link"]')
    expect(link.exists()).toBe(true)
    const to = JSON.parse(link.attributes('data-to'))
    expect(to).toEqual({
      path: '/login',
      query: { redirect: '/join/kann-ki-beratung-test' },
    })
  })

  it('REG_JOIN_006: no code → plain /login link', async () => {
    isAuthenticatedRef.value = false
    currentRoute.params = {}

    const wrapper = mountRegister()
    await flushPromises()

    const link = wrapper.find('[data-testid="login-link"]')
    expect(link.attributes('data-to')).toBe(JSON.stringify('/login'))
  })
})
