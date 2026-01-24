/**
 * LLARS Global Components
 *
 * This file exports all common/global components that can be used
 * throughout the application. Components are registered globally
 * in main.js for easy access without imports.
 *
 * Usage (after global registration):
 *   <LBtn variant="primary">Click me</LBtn>
 *   <LIcon icon="mdi-information" />
 *   <LIconBtn icon="mdi-delete" variant="danger" tooltip="Löschen" />
 */

// Button Components
export { default as LBtn } from './LBtn.vue'
export { default as LIcon } from './LIcon.vue'
export { default as LIconBtn } from './LIconBtn.vue'
export { default as LInfoTooltip } from './LInfoTooltip.vue'
export { default as LActionGroup } from './LActionGroup.vue'
export { default as LLoading } from './LLoading.vue'

// Form Components
export { default as LSlider } from './LSlider.vue'

// Message Components
export { default as LMessage } from './LMessage.vue'
export { default as LMessageList } from './LMessageList.vue'

// Evaluation Components
export { default as LEvaluationLayout } from './LEvaluationLayout.vue'
export { default as LEvaluationStatus } from './LEvaluationStatus.vue'
export { default as LConfusionMatrix } from './LConfusionMatrix.vue'
export { default as LRatingDistribution } from './LRatingDistribution.vue'

// Other Common Components
export { default as KatexFormula } from './KatexFormula.vue'
export { default as LCardSkeleton } from './LCardSkeleton.vue'

/**
 * Plugin for global registration
 * Import in main.js: import { LlarsComponents } from '@/components/common'
 * Use: app.use(LlarsComponents)
 */
export const LlarsComponents = {
  install(app) {
    // Register all components globally
    app.component('LBtn', () => import('./LBtn.vue'))
    app.component('LIcon', () => import('./LIcon.vue'))
    app.component('LIconBtn', () => import('./LIconBtn.vue'))
    app.component('LInfoTooltip', () => import('./LInfoTooltip.vue'))
    app.component('LActionGroup', () => import('./LActionGroup.vue'))
    app.component('LLoading', () => import('./LLoading.vue'))
    app.component('LSlider', () => import('./LSlider.vue'))
    app.component('LMessage', () => import('./LMessage.vue'))
    app.component('LMessageList', () => import('./LMessageList.vue'))
    app.component('LEvaluationLayout', () => import('./LEvaluationLayout.vue'))
    app.component('LEvaluationStatus', () => import('./LEvaluationStatus.vue'))
    app.component('LConfusionMatrix', () => import('./LConfusionMatrix.vue'))
    app.component('LRatingDistribution', () => import('./LRatingDistribution.vue'))
    app.component('KatexFormula', () => import('./KatexFormula.vue'))
    app.component('LCardSkeleton', () => import('./LCardSkeleton.vue'))
  }
}

// Default export for convenience
export default LlarsComponents
