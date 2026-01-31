/**
 * FloatingAIAssistant - Draggable AI Assistant Panel for LaTeX Collab
 *
 * A document-aware AI assistant that uses LFloatingWindow and can:
 * - Automatically detect document structure (title, sections, abstract)
 * - Insert changes directly into the document
 * - Provide quick actions for common writing tasks
 */

export { default as FloatingAIAssistant } from './FloatingAIAssistant.vue'
export { default as AIAssistantChat } from './AIAssistantChat.vue'
export { default as AIAssistantInput } from './AIAssistantInput.vue'

// Composables
export { useDocumentContext } from './composables/useDocumentContext'
export { useAIAgentActions } from './composables/useAIAgentActions'
