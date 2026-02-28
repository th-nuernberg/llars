/**
 * Conference Manager configuration constants
 */

export const CORE_RANKINGS = [
  { value: 'A*', label: 'A*', color: '#e8a087' },
  { value: 'A', label: 'A', color: '#D1BC8A' },
  { value: 'B', label: 'B', color: '#b0ca97' },
  { value: 'C', label: 'C', color: '#88c4c8' },
  { value: 'Unranked', label: 'Unranked', color: '#9e9e9e' },
]

export const PAPER_STATUSES = [
  { value: 'planning', labelKey: 'conferenceManager.paper.statuses.planning', color: '#9e9e9e', icon: 'mdi-lightbulb-outline' },
  { value: 'in_progress', labelKey: 'conferenceManager.paper.statuses.inProgress', color: '#88c4c8', icon: 'mdi-pencil-outline' },
  { value: 'submitted', labelKey: 'conferenceManager.paper.statuses.submitted', color: '#D1BC8A', icon: 'mdi-send-outline' },
  { value: 'accepted', labelKey: 'conferenceManager.paper.statuses.accepted', color: '#98d4bb', icon: 'mdi-check-circle-outline' },
  { value: 'rejected', labelKey: 'conferenceManager.paper.statuses.rejected', color: '#e8a087', icon: 'mdi-close-circle-outline' },
]

export function getRankingColor(ranking) {
  return CORE_RANKINGS.find(r => r.value === ranking)?.color || '#9e9e9e'
}

export function getStatusConfig(status) {
  return PAPER_STATUSES.find(s => s.value === status) || PAPER_STATUSES[0]
}
