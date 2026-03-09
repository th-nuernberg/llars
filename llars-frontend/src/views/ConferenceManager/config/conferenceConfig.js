/**
 * Conference Manager configuration constants
 *
 * Colors are tuned for good contrast on light backgrounds.
 * The LLARS design palette originals (pastel) are kept as chip backgrounds (with alpha),
 * while these darker variants are used for text, borders, and dots.
 */

export const CORE_RANKINGS = [
  { value: 'A*', label: 'A*', color: '#8B7D3C' },
  { value: 'A', label: 'A', color: '#4A7C59' },
  { value: 'B', label: 'B', color: '#6B8F71' },
  { value: 'C', label: 'C', color: '#6B8CA3' },
  { value: 'Unranked', label: 'U', color: '#808080' },
]

export const PAPER_STATUSES = [
  { value: 'planning', labelKey: 'conferenceManager.paper.statuses.planning', color: '#808080', icon: 'mdi-lightbulb-outline' },
  { value: 'in_progress', labelKey: 'conferenceManager.paper.statuses.inProgress', color: '#4a8e93', icon: 'mdi-pencil-outline' },
  { value: 'submitted', labelKey: 'conferenceManager.paper.statuses.submitted', color: '#a08840', icon: 'mdi-send-outline' },
  { value: 'accepted', labelKey: 'conferenceManager.paper.statuses.accepted', color: '#4a9e7e', icon: 'mdi-check-circle-outline' },
  { value: 'rejected', labelKey: 'conferenceManager.paper.statuses.rejected', color: '#c4735a', icon: 'mdi-close-circle-outline' },
  { value: 'published', labelKey: 'conferenceManager.paper.statuses.published', color: '#6b9a45', icon: 'mdi-book-check-outline' },
]

export const SUBMISSION_STATUSES = [
  { value: 'submitted', labelKey: 'conferenceManager.paper.submissionStatuses.submitted', color: '#a08840', icon: 'mdi-send-outline' },
  { value: 'accepted', labelKey: 'conferenceManager.paper.submissionStatuses.accepted', color: '#4a9e7e', icon: 'mdi-check-circle-outline' },
  { value: 'rejected', labelKey: 'conferenceManager.paper.submissionStatuses.rejected', color: '#c4735a', icon: 'mdi-close-circle-outline' },
  { value: 'withdrawn', labelKey: 'conferenceManager.paper.submissionStatuses.withdrawn', color: '#808080', icon: 'mdi-undo' },
]

export function getSubmissionStatusConfig(status) {
  return SUBMISSION_STATUSES.find(s => s.value === status) || SUBMISSION_STATUSES[0]
}

export function getRankingColor(ranking) {
  return CORE_RANKINGS.find(r => r.value === ranking)?.color || '#808080'
}

export function getStatusConfig(status) {
  return PAPER_STATUSES.find(s => s.value === status) || PAPER_STATUSES[0]
}
