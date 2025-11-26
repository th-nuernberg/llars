/**
 * Skeleton Loading Composable
 *
 * Provides a consistent pattern for implementing skeleton loading states
 * across all components in the LLARS application.
 *
 * Usage:
 * ```js
 * import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
 *
 * const { isLoading, setLoading, withLoading } = useSkeletonLoading('mySection')
 *
 * // Option 1: Manual control
 * setLoading('mySection', true)
 * await fetchData()
 * setLoading('mySection', false)
 *
 * // Option 2: Automatic wrapper
 * await withLoading('mySection', async () => {
 *   await fetchData()
 * })
 * ```
 *
 * Template Usage:
 * ```vue
 * <v-skeleton-loader v-if="isLoading('stats')" type="card" />
 * <v-card v-else>...</v-card>
 * ```
 */

import { ref, reactive } from 'vue'

// Global loading states that can be shared across components
const globalLoadingStates = reactive({})

export function useSkeletonLoading(defaultSections = []) {
  // Local loading states for this component instance
  const loadingStates = reactive({})

  // Initialize default sections
  if (Array.isArray(defaultSections)) {
    defaultSections.forEach(section => {
      loadingStates[section] = true
    })
  }

  /**
   * Check if a section is currently loading
   * @param {string} section - The section identifier
   * @returns {boolean} Whether the section is loading
   */
  const isLoading = (section) => {
    return loadingStates[section] ?? false
  }

  /**
   * Set loading state for a section
   * @param {string} section - The section identifier
   * @param {boolean} loading - Whether the section is loading
   */
  const setLoading = (section, loading) => {
    loadingStates[section] = loading
  }

  /**
   * Start loading for a section
   * @param {string} section - The section identifier
   */
  const startLoading = (section) => {
    loadingStates[section] = true
  }

  /**
   * Stop loading for a section
   * @param {string} section - The section identifier
   */
  const stopLoading = (section) => {
    loadingStates[section] = false
  }

  /**
   * Wrap an async function with loading state management
   * @param {string} section - The section identifier
   * @param {Function} asyncFn - The async function to wrap
   * @returns {Promise} The result of the async function
   */
  const withLoading = async (section, asyncFn) => {
    loadingStates[section] = true
    try {
      return await asyncFn()
    } finally {
      loadingStates[section] = false
    }
  }

  /**
   * Initialize multiple sections as loading
   * @param {string[]} sections - Array of section identifiers
   */
  const initLoadingSections = (sections) => {
    sections.forEach(section => {
      loadingStates[section] = true
    })
  }

  /**
   * Check if any section is still loading
   * @returns {boolean} Whether any section is loading
   */
  const anyLoading = () => {
    return Object.values(loadingStates).some(v => v === true)
  }

  /**
   * Check if all sections have finished loading
   * @returns {boolean} Whether all sections have finished loading
   */
  const allLoaded = () => {
    return Object.values(loadingStates).every(v => v === false)
  }

  return {
    loadingStates,
    isLoading,
    setLoading,
    startLoading,
    stopLoading,
    withLoading,
    initLoadingSections,
    anyLoading,
    allLoaded
  }
}

/**
 * Skeleton loader types reference (Vuetify v-skeleton-loader)
 *
 * Common types:
 * - 'card' - Card placeholder
 * - 'card-avatar' - Card with avatar
 * - 'table' - Full table
 * - 'table-heading' - Table heading only
 * - 'table-thead' - Table header row
 * - 'table-tbody' - Table body rows
 * - 'table-tfoot' - Table footer
 * - 'table-row' - Single table row
 * - 'list-item' - List item
 * - 'list-item-avatar' - List item with avatar
 * - 'list-item-two-line' - Two-line list item
 * - 'list-item-three-line' - Three-line list item
 * - 'text' - Text block
 * - 'paragraph' - Paragraph (3 lines)
 * - 'sentences' - Multiple sentences
 * - 'chip' - Chip placeholder
 * - 'button' - Button placeholder
 * - 'avatar' - Avatar placeholder
 * - 'image' - Image placeholder
 * - 'heading' - Heading placeholder
 * - 'article' - Article layout
 * - 'actions' - Action buttons
 * - 'divider' - Divider line
 * - 'subtitle' - Subtitle text
 *
 * Multiple types can be combined with comma:
 * type="card-avatar, list-item-two-line, actions"
 */

export const SKELETON_TYPES = {
  // Stats cards
  STAT_CARD: 'card',

  // Tables
  TABLE_FULL: 'table-heading, table-thead, table-tbody, table-tfoot',
  TABLE_SIMPLE: 'table-thead, table-tbody',

  // Cards
  CARD_SIMPLE: 'card',
  CARD_WITH_AVATAR: 'card-avatar',
  CARD_WITH_ACTIONS: 'card, actions',

  // Lists
  LIST_SIMPLE: 'list-item@3',
  LIST_WITH_AVATAR: 'list-item-avatar@3',
  LIST_DETAILED: 'list-item-two-line@3',

  // Content
  ARTICLE: 'article',
  PARAGRAPH: 'paragraph',
  TEXT: 'text',

  // Charts/Graphs (use card with specific height)
  CHART: 'card'
}

export default useSkeletonLoading
