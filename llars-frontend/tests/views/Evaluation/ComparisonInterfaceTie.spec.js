/**
 * ComparisonInterface — tie option config resolution
 *
 * Test IDs: CMP_TIE_001 - CMP_TIE_006
 *
 * Regression coverage for a production bug: the tie ("both equally good")
 * button was only rendered when the config carried `allowTie` (camelCase, the
 * spelling the Scenario Wizard writes). The v1 REST API validates comparison
 * configs through Pydantic's `ComparisonConfig`, which spells the field
 * `allow_tie` (snake_case) and defaults it to true.
 *
 * Consequence on production: every API-created comparison scenario silently
 * lost the tie option. The KIESA Sprachvereinfachung studies (scenarios
 * 819/820/824/855) collected 359 A/B votes and exactly 0 ties, while the
 * wizard-created scenario 442 — same UI, camelCase key — recorded 83 ties.
 *
 * Both spellings and both nesting levels must now resolve.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { createVuetify } from 'vuetify'
import * as vuetifyComponents from 'vuetify/components'
import * as vuetifyDirectives from 'vuetify/directives'
import ComparisonInterface from '@/views/Evaluation/interfaces/ComparisonInterface.vue'

const vuetify = createVuetify({ components: vuetifyComponents, directives: vuetifyDirectives })

vi.mock('axios', () => ({ default: { get: vi.fn(), post: vi.fn() } }))
import axios from 'axios'

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ push: vi.fn() }),
}))

vi.mock('@/composables/usePanelResize', () => ({
  usePanelResize: () => ({
    containerRef: ref(null),
    leftPanelStyle: () => ({}),
    rightPanelStyle: () => ({}),
    startResize: vi.fn(),
    isResizing: ref(false),
  }),
}))

vi.mock('@/composables/useMobile', () => ({
  useMobile: () => ({ isMobile: ref(false) }),
}))

const SCENARIO_ID = 855

const ITEMS = [
  {
    thread_id: 1,
    evaluated: false,
    evaluation: null,
    option_a: { content: 'Variante A' },
    option_b: { content: 'Variante B' },
  },
]

beforeEach(() => {
  vi.clearAllMocks()
  axios.get.mockImplementation(() =>
    Promise.resolve({ data: { items: JSON.parse(JSON.stringify(ITEMS)) } })
  )
  axios.post.mockResolvedValue({ data: { success: true } })
})

async function mountWithConfig(config) {
  const wrapper = mount(ComparisonInterface, {
    props: { scenarioId: SCENARIO_ID, config, scenario: { id: SCENARIO_ID, config_json: config } },
    global: {
      plugins: [vuetify],
      stubs: {
        ComparisonRewardDialog: true,
        ComparisonHistoryDrawer: true,
        LMarkdownContent: true,
        teleport: true,
      },
      mocks: { $t: (key) => key },
    },
  })
  await flushPromises()
  return wrapper
}

const hasTieButton = (wrapper) => wrapper.find('.tie-btn').exists()

describe('ComparisonInterface tie option', () => {
  it('CMP_TIE_001: renders the tie button for wizard configs (allowTie, nested)', async () => {
    const wrapper = await mountWithConfig({ eval_config: { config: { allowTie: true } } })
    expect(hasTieButton(wrapper)).toBe(true)
  })

  it('CMP_TIE_002: renders the tie button for v1-API configs (allow_tie, nested)', async () => {
    // This is the exact shape api_v1_scenario_service._build_config_json writes.
    const wrapper = await mountWithConfig({ eval_config: { config: { allow_tie: true } } })
    expect(hasTieButton(wrapper)).toBe(true)
  })

  it('CMP_TIE_003: renders the tie button for top-level allow_tie', async () => {
    // _build_config_json also hoists the flag to the top level.
    const wrapper = await mountWithConfig({ allow_tie: true })
    expect(hasTieButton(wrapper)).toBe(true)
  })

  it('CMP_TIE_004: hides the tie button when allow_tie is explicitly false', async () => {
    const wrapper = await mountWithConfig({ eval_config: { config: { allow_tie: false } } })
    expect(hasTieButton(wrapper)).toBe(false)
  })

  it('CMP_TIE_005: hides the tie button when allowTie is explicitly false', async () => {
    const wrapper = await mountWithConfig({ eval_config: { config: { allowTie: false } } })
    expect(hasTieButton(wrapper)).toBe(false)
  })

  it('CMP_TIE_006: stays off by default when neither spelling is present', async () => {
    const wrapper = await mountWithConfig({ eval_config: { config: {} } })
    expect(hasTieButton(wrapper)).toBe(false)
  })
})
