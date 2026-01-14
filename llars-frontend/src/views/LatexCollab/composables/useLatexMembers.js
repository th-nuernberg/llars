/**
 * useLatexMembers.js
 *
 * Composable for LaTeX workspace member/sharing management.
 * This is a wrapper around the generic useCollabMembers composable.
 *
 * @deprecated Use useCollabMembers from '@/composables/useCollabMembers' directly
 */

import { useCollabMembers } from '@/composables/useCollabMembers'

/**
 * Create LaTeX members composable
 * @param {Object} options - Configuration options
 * @param {Ref<number>} options.workspaceId - Workspace ID ref
 * @param {Ref<Object>} options.workspace - Workspace object ref
 * @param {Function} options.hasPermission - Permission check function
 * @param {Ref<string>} options.currentUsername - Current user's username
 * @param {Ref<boolean>} options.isAdmin - Whether current user is admin
 * @returns {Object} Composable state and methods
 */
export function useLatexMembers({
  workspaceId,
  workspace,
  hasPermission,
  currentUsername,
  isAdmin
}) {
  return useCollabMembers({
    workspaceId,
    workspace,
    hasPermission,
    currentUsername,
    isAdmin,
    apiPrefix: '/api/latex-collab',
    permissionKey: 'feature:latex_collab:share',
    i18nPrefix: 'latexCollab'
  })
}
