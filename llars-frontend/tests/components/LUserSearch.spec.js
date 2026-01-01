/**
 * LUserSearch Component Tests
 *
 * Tests for the LLARS user search autocomplete component.
 * Test IDs: COMP_USR_001 - COMP_USR_050
 *
 * Coverage:
 * - Rendering and structure
 * - Props (placeholder, label, density, disabled)
 * - Search functionality
 * - Add button
 * - Events (update:modelValue, select, add)
 * - Exclude usernames
 * - Exposed methods (reset, setAdding)
 * - Edge cases
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref, nextTick } from 'vue'
import LUserSearch from '@/components/common/LUserSearch.vue'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn()
  }
}))

// Mock userUtils
vi.mock('@/utils/userUtils', () => ({
  getAvatarUrl: vi.fn((user) => `https://avatar.test/${user?.username || 'default'}`),
  formatDisplayName: vi.fn((username) => username?.charAt(0).toUpperCase() + username?.slice(1) || '')
}))

// Mock authStorage
vi.mock('@/utils/authStorage', () => ({
  AUTH_STORAGE_KEYS: { token: 'auth_token' },
  getAuthStorageItem: vi.fn(() => 'test-token')
}))

import axios from 'axios'

// Stubs for Vuetify components
const VAutocompleteStub = {
  name: 'VAutocomplete',
  template: `
    <div class="v-autocomplete" :class="{ 'v-autocomplete--disabled': disabled }">
      <input
        :placeholder="placeholder"
        :disabled="disabled"
        data-testid="search-input"
      />
      <div v-if="loading" class="loading-indicator">Loading...</div>
      <div class="suggestions">
        <slot name="item" v-for="item in items" :key="item.username" :props="{}" :item="{ raw: item }" />
      </div>
      <div v-if="items.length === 0" class="no-data">
        <slot name="no-data" />
      </div>
      <div v-if="modelValue" class="selection">
        <slot name="selection" :item="{ raw: modelValue }" />
      </div>
    </div>
  `,
  props: ['modelValue', 'search', 'items', 'loading', 'placeholder', 'label', 'disabled', 'density', 'itemTitle', 'itemValue', 'returnObject', 'variant', 'hideDetails', 'clearable', 'noFilter'],
  emits: ['update:modelValue', 'update:search']
}

const LBtnStub = {
  name: 'LBtn',
  template: '<button class="l-btn" :disabled="disabled" :class="[variant, size]" @click="$emit(\'click\')"><slot /></button>',
  props: ['variant', 'size', 'loading', 'disabled', 'title']
}

function mountLUserSearch(props = {}, options = {}) {
  return mount(LUserSearch, {
    props,
    global: {
      stubs: {
        'v-autocomplete': VAutocompleteStub,
        'v-list-item': { template: '<div class="v-list-item"><slot /><slot name="prepend" /><slot name="title" /></div>' },
        'v-list-item-title': { template: '<span class="v-list-item-title"><slot /></span>' },
        'v-list-item-subtitle': { template: '<span class="v-list-item-subtitle"><slot /></span>' },
        'v-icon': { template: '<i class="v-icon"><slot /></i>' },
        LBtn: LBtnStub
      }
    },
    ...options
  })
}

// Helper to trigger search by setting searchQuery directly
async function triggerSearch(wrapper, query) {
  wrapper.vm.searchQuery = query
  await nextTick()
}

describe('LUserSearch', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_USR_001: renders with default props', () => {
      const wrapper = mountLUserSearch()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-user-search').exists()).toBe(true)
    })

    it('COMP_USR_002: has l-user-search class', () => {
      const wrapper = mountLUserSearch()

      expect(wrapper.find('.l-user-search').exists()).toBe(true)
    })

    it('COMP_USR_003: renders autocomplete input', () => {
      const wrapper = mountLUserSearch()

      expect(wrapper.find('.v-autocomplete').exists()).toBe(true)
    })

    it('COMP_USR_004: uses default placeholder', () => {
      const wrapper = mountLUserSearch()

      expect(wrapper.find('[data-testid="search-input"]').attributes('placeholder')).toBe('Nutzernamen eingeben...')
    })

    it('COMP_USR_005: does not show add button by default', () => {
      const wrapper = mountLUserSearch()

      expect(wrapper.find('.l-btn').exists()).toBe(false)
    })
  })

  // ==================== Props Tests ====================

  describe('Props', () => {
    it('COMP_USR_006: uses custom placeholder', () => {
      const wrapper = mountLUserSearch({ placeholder: 'Search users...' })

      expect(wrapper.find('[data-testid="search-input"]').attributes('placeholder')).toBe('Search users...')
    })

    it('COMP_USR_007: applies disabled state', () => {
      const wrapper = mountLUserSearch({ disabled: true })

      expect(wrapper.find('.v-autocomplete--disabled').exists()).toBe(true)
      expect(wrapper.find('[data-testid="search-input"]').attributes('disabled')).toBeDefined()
    })

    it('COMP_USR_008: shows add button when showAddButton is true', () => {
      const wrapper = mountLUserSearch({ showAddButton: true })

      expect(wrapper.find('.l-btn').exists()).toBe(true)
    })

    it('COMP_USR_009: uses custom addButtonText', () => {
      const wrapper = mountLUserSearch({
        showAddButton: true,
        addButtonText: 'Add User'
      })

      expect(wrapper.find('.l-btn').text()).toContain('Add User')
    })

    it('COMP_USR_010: applies buttonSize prop', () => {
      const wrapper = mountLUserSearch({
        showAddButton: true,
        buttonSize: 'large'
      })

      expect(wrapper.find('.l-btn').classes()).toContain('large')
    })

    it('COMP_USR_011: add button is disabled when no user selected', () => {
      const wrapper = mountLUserSearch({ showAddButton: true })

      expect(wrapper.find('.l-btn').attributes('disabled')).toBeDefined()
    })

    it('COMP_USR_012: add button is disabled when component is disabled', () => {
      const wrapper = mountLUserSearch({
        showAddButton: true,
        disabled: true,
        modelValue: { username: 'test' }
      })

      expect(wrapper.find('.l-btn').attributes('disabled')).toBeDefined()
    })
  })

  // ==================== Search Functionality Tests ====================

  describe('Search Functionality', () => {
    it('COMP_USR_013: does not search with less than 2 characters', async () => {
      const wrapper = mountLUserSearch()

      await triggerSearch(wrapper, 'a')
      vi.advanceTimersByTime(300)
      await flushPromises()

      expect(axios.get).not.toHaveBeenCalled()
    })

    it('COMP_USR_014: searches with 2 or more characters', async () => {
      axios.get.mockResolvedValueOnce({ data: { users: [] } })

      const wrapper = mountLUserSearch()

      await triggerSearch(wrapper, 'ab')
      vi.advanceTimersByTime(300)
      await flushPromises()

      expect(axios.get).toHaveBeenCalled()
    })

    it('COMP_USR_015: debounces search requests', async () => {
      axios.get.mockResolvedValue({ data: { users: [] } })

      const wrapper = mountLUserSearch()

      await triggerSearch(wrapper, 'ab')
      vi.advanceTimersByTime(100)
      await triggerSearch(wrapper, 'abc')
      vi.advanceTimersByTime(100)
      await triggerSearch(wrapper, 'abcd')
      vi.advanceTimersByTime(300)
      await flushPromises()

      // Only one call due to debouncing
      expect(axios.get).toHaveBeenCalledTimes(1)
    })

    it('COMP_USR_016: uses correct search endpoint', async () => {
      axios.get.mockResolvedValueOnce({ data: { users: [] } })

      const wrapper = mountLUserSearch({ searchEndpoint: '/api/custom/search' })

      await triggerSearch(wrapper, 'test')
      vi.advanceTimersByTime(300)
      await flushPromises()

      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/custom/search'),
        expect.any(Object)
      )
    })

    it('COMP_USR_017: includes auth header in request', async () => {
      axios.get.mockResolvedValueOnce({ data: { users: [] } })

      const wrapper = mountLUserSearch()

      await triggerSearch(wrapper, 'test')
      vi.advanceTimersByTime(300)
      await flushPromises()

      expect(axios.get).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token'
          })
        })
      )
    })

    it('COMP_USR_018: handles search error gracefully', async () => {
      axios.get.mockRejectedValueOnce(new Error('Network error'))
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const wrapper = mountLUserSearch()

      await triggerSearch(wrapper, 'test')
      vi.advanceTimersByTime(300)
      await flushPromises()

      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })
  })

  // ==================== Exclude Usernames Tests ====================

  describe('Exclude Usernames', () => {
    it('COMP_USR_019: filters out excluded usernames', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          users: [
            { username: 'alice' },
            { username: 'bob' },
            { username: 'charlie' }
          ]
        }
      })

      const wrapper = mountLUserSearch({
        excludeUsernames: ['bob']
      })

      await triggerSearch(wrapper, 'test')
      vi.advanceTimersByTime(300)
      await flushPromises()

      // Verify suggestions don't include bob
      expect(wrapper.vm.suggestions.map(s => s.username)).not.toContain('bob')
      expect(wrapper.vm.suggestions.length).toBe(2)
    })

    it('COMP_USR_020: exclude comparison is case-insensitive', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          users: [
            { username: 'Alice' },
            { username: 'BOB' }
          ]
        }
      })

      const wrapper = mountLUserSearch({
        excludeUsernames: ['alice', 'bob']
      })

      await triggerSearch(wrapper, 'test')
      vi.advanceTimersByTime(300)
      await flushPromises()

      expect(wrapper.vm.suggestions.length).toBe(0)
    })

    it('COMP_USR_021: works with empty excludeUsernames', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          users: [{ username: 'test' }]
        }
      })

      const wrapper = mountLUserSearch({ excludeUsernames: [] })

      await triggerSearch(wrapper, 'test')
      vi.advanceTimersByTime(300)
      await flushPromises()

      expect(wrapper.vm.suggestions.length).toBe(1)
    })
  })

  // ==================== Events Tests ====================

  describe('Events', () => {
    it('COMP_USR_022: emits update:modelValue when user selected', async () => {
      const wrapper = mountLUserSearch()
      const user = { username: 'testuser' }

      wrapper.vm.selectedUser = user
      await nextTick()

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')[0]).toEqual([user])
    })

    it('COMP_USR_023: emits select when user selected', async () => {
      const wrapper = mountLUserSearch()
      const user = { username: 'testuser' }

      wrapper.vm.selectedUser = user
      await nextTick()

      expect(wrapper.emitted('select')).toBeTruthy()
      expect(wrapper.emitted('select')[0]).toEqual([user])
    })

    it('COMP_USR_024: emits add when add button clicked', async () => {
      const wrapper = mountLUserSearch({ showAddButton: true })
      const user = { username: 'testuser' }

      wrapper.vm.selectedUser = user
      await nextTick()

      await wrapper.find('.l-btn').trigger('click')

      expect(wrapper.emitted('add')).toBeTruthy()
      expect(wrapper.emitted('add')[0]).toEqual([user])
    })

    it('COMP_USR_025: does not emit add when no user selected', async () => {
      const wrapper = mountLUserSearch({ showAddButton: true })

      wrapper.vm.handleAdd()
      await nextTick()

      expect(wrapper.emitted('add')).toBeFalsy()
    })

    it('COMP_USR_026: does not emit select when user cleared', async () => {
      const wrapper = mountLUserSearch({
        modelValue: { username: 'test' }
      })

      wrapper.vm.selectedUser = null
      await nextTick()

      // Should emit update:modelValue but not select
      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      const selectEvents = wrapper.emitted('select') || []
      expect(selectEvents.length).toBe(0)
    })
  })

  // ==================== Exposed Methods Tests ====================

  describe('Exposed Methods', () => {
    it('COMP_USR_027: reset() clears selectedUser', async () => {
      const wrapper = mountLUserSearch()
      wrapper.vm.selectedUser = { username: 'test' }

      wrapper.vm.reset()
      await nextTick()

      expect(wrapper.vm.selectedUser).toBe(null)
    })

    it('COMP_USR_028: reset() clears searchQuery', async () => {
      const wrapper = mountLUserSearch()
      wrapper.vm.searchQuery = 'test'

      wrapper.vm.reset()
      await nextTick()

      expect(wrapper.vm.searchQuery).toBe('')
    })

    it('COMP_USR_029: reset() clears suggestions', async () => {
      const wrapper = mountLUserSearch()
      wrapper.vm.suggestions = [{ username: 'test' }]

      wrapper.vm.reset()
      await nextTick()

      expect(wrapper.vm.suggestions).toEqual([])
    })

    it('COMP_USR_030: reset() clears adding state', async () => {
      const wrapper = mountLUserSearch()
      wrapper.vm.adding = true

      wrapper.vm.reset()
      await nextTick()

      expect(wrapper.vm.adding).toBe(false)
    })

    it('COMP_USR_031: setAdding() sets adding state', async () => {
      const wrapper = mountLUserSearch()

      wrapper.vm.setAdding(true)
      await nextTick()

      expect(wrapper.vm.adding).toBe(true)
    })

    it('COMP_USR_032: setAdding(false) clears adding state', async () => {
      const wrapper = mountLUserSearch()
      wrapper.vm.adding = true

      wrapper.vm.setAdding(false)
      await nextTick()

      expect(wrapper.vm.adding).toBe(false)
    })
  })

  // ==================== v-model Tests ====================

  describe('v-model', () => {
    it('COMP_USR_033: initializes with modelValue', () => {
      const user = { username: 'initial' }
      const wrapper = mountLUserSearch({ modelValue: user })

      expect(wrapper.vm.selectedUser).toEqual(user)
    })

    it('COMP_USR_034: updates when modelValue changes', async () => {
      const wrapper = mountLUserSearch({ modelValue: null })

      await wrapper.setProps({ modelValue: { username: 'updated' } })

      expect(wrapper.vm.selectedUser).toEqual({ username: 'updated' })
    })

    it('COMP_USR_035: handles null modelValue', () => {
      const wrapper = mountLUserSearch({ modelValue: null })

      expect(wrapper.vm.selectedUser).toBe(null)
    })
  })

  // ==================== Loading State Tests ====================

  describe('Loading State', () => {
    it('COMP_USR_036: shows loading during search', async () => {
      let resolveSearch
      axios.get.mockImplementationOnce(() => new Promise(resolve => {
        resolveSearch = resolve
      }))

      const wrapper = mountLUserSearch()

      await triggerSearch(wrapper, 'test')
      vi.advanceTimersByTime(300)
      await nextTick()

      expect(wrapper.vm.loading).toBe(true)

      resolveSearch({ data: { users: [] } })
      await flushPromises()

      expect(wrapper.vm.loading).toBe(false)
    })

    it('COMP_USR_037: clears loading after search error', async () => {
      axios.get.mockRejectedValueOnce(new Error('Error'))
      vi.spyOn(console, 'error').mockImplementation(() => {})

      const wrapper = mountLUserSearch()

      await triggerSearch(wrapper, 'test')
      vi.advanceTimersByTime(300)
      await flushPromises()

      expect(wrapper.vm.loading).toBe(false)
    })

    it('COMP_USR_038: clears loading when query becomes too short', async () => {
      const wrapper = mountLUserSearch()

      wrapper.vm.loading = true
      await triggerSearch(wrapper, 'a')
      await nextTick()

      expect(wrapper.vm.loading).toBe(false)
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('COMP_USR_039: handles empty search results', async () => {
      axios.get.mockResolvedValueOnce({ data: { users: [] } })

      const wrapper = mountLUserSearch()

      await triggerSearch(wrapper, 'nonexistent')
      vi.advanceTimersByTime(300)
      await flushPromises()

      expect(wrapper.vm.suggestions).toEqual([])
    })

    it('COMP_USR_040: handles missing users in response', async () => {
      axios.get.mockResolvedValueOnce({ data: {} })

      const wrapper = mountLUserSearch()

      await triggerSearch(wrapper, 'test')
      vi.advanceTimersByTime(300)
      await flushPromises()

      expect(wrapper.vm.suggestions).toEqual([])
    })

    it('COMP_USR_041: handles whitespace-only query', async () => {
      const wrapper = mountLUserSearch()

      await triggerSearch(wrapper, '   ')
      vi.advanceTimersByTime(300)
      await flushPromises()

      expect(axios.get).not.toHaveBeenCalled()
    })

    it('COMP_USR_042: handles null query', async () => {
      const wrapper = mountLUserSearch()

      await triggerSearch(wrapper, null)
      vi.advanceTimersByTime(300)
      await flushPromises()

      expect(axios.get).not.toHaveBeenCalled()
    })

    it('COMP_USR_043: handles special characters in query', async () => {
      axios.get.mockResolvedValueOnce({ data: { users: [] } })

      const wrapper = mountLUserSearch()

      await triggerSearch(wrapper, 'test@user.com')
      vi.advanceTimersByTime(300)
      await flushPromises()

      expect(axios.get).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          params: expect.objectContaining({ q: 'test@user.com' })
        })
      )
    })

    it('COMP_USR_044: handles unicode in query', async () => {
      axios.get.mockResolvedValueOnce({ data: { users: [] } })

      const wrapper = mountLUserSearch()

      await triggerSearch(wrapper, '用户名')
      vi.advanceTimersByTime(300)
      await flushPromises()

      expect(axios.get).toHaveBeenCalled()
    })

    it('COMP_USR_045: component works without any props', () => {
      const wrapper = mount(LUserSearch, {
        global: {
          stubs: {
            'v-autocomplete': VAutocompleteStub,
            'v-list-item': { template: '<div><slot /></div>' },
            'v-list-item-title': { template: '<span><slot /></span>' },
            'v-list-item-subtitle': { template: '<span><slot /></span>' },
            'v-icon': { template: '<i><slot /></i>' },
            LBtn: LBtnStub
          }
        }
      })

      expect(wrapper.exists()).toBe(true)
    })

    it('COMP_USR_046: clears previous timer on new search', async () => {
      axios.get.mockResolvedValue({ data: { users: [] } })

      const wrapper = mountLUserSearch()

      await triggerSearch(wrapper, 'aa')
      vi.advanceTimersByTime(100)

      await triggerSearch(wrapper, 'bb')
      vi.advanceTimersByTime(300)
      await flushPromises()

      // Should only search for 'bb', not 'aa'
      expect(axios.get).toHaveBeenCalledTimes(1)
      expect(axios.get).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          params: expect.objectContaining({ q: 'bb' })
        })
      )
    })

    it('COMP_USR_047: sets adding state on handleAdd', async () => {
      const wrapper = mountLUserSearch({ showAddButton: true })
      wrapper.vm.selectedUser = { username: 'test' }
      await nextTick()

      await wrapper.find('.l-btn').trigger('click')

      expect(wrapper.vm.adding).toBe(true)
    })

    it('COMP_USR_048: multiple instances are independent', () => {
      const wrapper1 = mountLUserSearch({ placeholder: 'Search 1' })
      const wrapper2 = mountLUserSearch({ placeholder: 'Search 2' })

      expect(wrapper1.find('[data-testid="search-input"]').attributes('placeholder')).toBe('Search 1')
      expect(wrapper2.find('[data-testid="search-input"]').attributes('placeholder')).toBe('Search 2')
    })

    it('COMP_USR_049: handles rapid enable/disable', async () => {
      const wrapper = mountLUserSearch({ disabled: false })

      await wrapper.setProps({ disabled: true })
      await wrapper.setProps({ disabled: false })
      await wrapper.setProps({ disabled: true })

      expect(wrapper.find('.v-autocomplete--disabled').exists()).toBe(true)
    })

    it('COMP_USR_050: passes limit param to search endpoint', async () => {
      axios.get.mockResolvedValueOnce({ data: { users: [] } })

      const wrapper = mountLUserSearch()

      await triggerSearch(wrapper, 'test')
      vi.advanceTimersByTime(300)
      await flushPromises()

      expect(axios.get).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          params: expect.objectContaining({ limit: 10 })
        })
      )
    })
  })
})
