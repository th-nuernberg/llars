/**
 * LLARS Global Components
 *
 * This file exports all common/global components that can be used
 * throughout the application. Components are registered globally
 * in main.js for easy access without imports.
 *
 * Usage (after global registration):
 *   <LBtn variant="primary">Click me</LBtn>
 *   <LIconBtn icon="mdi-delete" variant="danger" tooltip="Löschen" />
 */

// Button Components
export { default as LBtn } from './LBtn.vue'
export { default as LIconBtn } from './LIconBtn.vue'

// Other Common Components
export { default as KatexFormula } from './KatexFormula.vue'

/**
 * Plugin for global registration
 * Import in main.js: import { LlarsComponents } from '@/components/common'
 * Use: app.use(LlarsComponents)
 */
export const LlarsComponents = {
  install(app) {
    // Register all components globally
    app.component('LBtn', () => import('./LBtn.vue'))
    app.component('LIconBtn', () => import('./LIconBtn.vue'))
    app.component('KatexFormula', () => import('./KatexFormula.vue'))
  }
}

// Default export for convenience
export default LlarsComponents
