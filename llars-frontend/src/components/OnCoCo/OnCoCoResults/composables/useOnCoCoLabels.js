/**
 * Composable for OnCoCo label configuration and helpers
 *
 * Provides label metadata, display names, colors, and categorization
 * for the OnCoCo (Interpersonal Communication Coding) system.
 */

/**
 * Label categories grouped by theme
 */
export const LABEL_CATEGORIES = {
  COUNSELOR_IMPACT_FACTORS: {
    name: 'Berater: Impact Factors',
    prefix: 'CO-IF',
    description: 'Wirkfaktoren des Beraters',
    labels: [
      'CO-IF-AC', // Appreciation & Clarification
      'CO-IF-RE', // Resource Activation
      'CO-IF-PA', // Problem Actualization
      'CO-IF-MA'  // Motivation Activation
    ]
  },
  COUNSELOR_BASIC_VARIABLES: {
    name: 'Berater: Grundvariablen',
    prefix: 'CO-BV',
    description: 'Basisvariablen der Beraterkommunikation',
    labels: [
      'CO-BV-PS', // Psychosocial
      'CO-BV-EM', // Emotional
      'CO-BV-CO', // Cognitive
      'CO-BV-MO'  // Motivational
    ]
  },
  CLIENT_RESPONSES: {
    name: 'Klient: Reaktionen',
    prefix: 'CL',
    description: 'Klient-Reaktionen und -Äußerungen',
    labels: [
      'CL-RE', // Resource Expression
      'CL-PE', // Problem Expression
      'CL-NE', // Neutral Expression
      'CL-RE-PO', // Resource Expression Positive
      'CL-RE-NE', // Resource Expression Negative
      'CL-PE-EM', // Problem Expression Emotional
      'CL-PE-CO'  // Problem Expression Cognitive
    ]
  },
  META: {
    name: 'Meta-Kommunikation',
    prefix: 'META',
    description: 'Kommunikation über Kommunikation',
    labels: [
      'META-OR', // Organizational
      'META-PR', // Process
      'META-RE'  // Relational
    ]
  }
};

/**
 * Complete label definitions with display names and descriptions
 */
export const LABEL_DEFINITIONS = {
  // Counselor Impact Factors
  'CO-IF-AC': {
    display: 'Wertschätzung & Klärung',
    shortDisplay: 'AC',
    category: 'COUNSELOR_IMPACT_FACTORS',
    role: 'counselor',
    description: 'Appreciation & Clarification - Wertschätzende und klärende Aussagen',
    color: '#4CAF50'
  },
  'CO-IF-RE': {
    display: 'Ressourcenaktivierung',
    shortDisplay: 'RE',
    category: 'COUNSELOR_IMPACT_FACTORS',
    role: 'counselor',
    description: 'Resource Activation - Aktivierung von Stärken und Ressourcen',
    color: '#2196F3'
  },
  'CO-IF-PA': {
    display: 'Problemaktualisierung',
    shortDisplay: 'PA',
    category: 'COUNSELOR_IMPACT_FACTORS',
    role: 'counselor',
    description: 'Problem Actualization - Vergegenwärtigung von Problemen',
    color: '#FF9800'
  },
  'CO-IF-MA': {
    display: 'Motivationsaktivierung',
    shortDisplay: 'MA',
    category: 'COUNSELOR_IMPACT_FACTORS',
    role: 'counselor',
    description: 'Motivation Activation - Aktivierung von Veränderungsmotivation',
    color: '#9C27B0'
  },

  // Counselor Basic Variables
  'CO-BV-PS': {
    display: 'Psychosozial',
    shortDisplay: 'PS',
    category: 'COUNSELOR_BASIC_VARIABLES',
    role: 'counselor',
    description: 'Psychosocial - Psychosoziale Themen',
    color: '#00BCD4'
  },
  'CO-BV-EM': {
    display: 'Emotional',
    shortDisplay: 'EM',
    category: 'COUNSELOR_BASIC_VARIABLES',
    role: 'counselor',
    description: 'Emotional - Emotionale Aspekte',
    color: '#E91E63'
  },
  'CO-BV-CO': {
    display: 'Kognitiv',
    shortDisplay: 'CO',
    category: 'COUNSELOR_BASIC_VARIABLES',
    role: 'counselor',
    description: 'Cognitive - Kognitive Aspekte',
    color: '#3F51B5'
  },
  'CO-BV-MO': {
    display: 'Motivational',
    shortDisplay: 'MO',
    category: 'COUNSELOR_BASIC_VARIABLES',
    role: 'counselor',
    description: 'Motivational - Motivationale Aspekte',
    color: '#FF5722'
  },

  // Client Responses
  'CL-RE': {
    display: 'Ressourcenäußerung',
    shortDisplay: 'RE',
    category: 'CLIENT_RESPONSES',
    role: 'client',
    description: 'Resource Expression - Äußerung von Ressourcen',
    color: '#8BC34A'
  },
  'CL-PE': {
    display: 'Problemäußerung',
    shortDisplay: 'PE',
    category: 'CLIENT_RESPONSES',
    role: 'client',
    description: 'Problem Expression - Äußerung von Problemen',
    color: '#FFC107'
  },
  'CL-NE': {
    display: 'Neutral',
    shortDisplay: 'NE',
    category: 'CLIENT_RESPONSES',
    role: 'client',
    description: 'Neutral Expression - Neutrale Äußerung',
    color: '#9E9E9E'
  },
  'CL-RE-PO': {
    display: 'Ressource Positiv',
    shortDisplay: 'RE+',
    category: 'CLIENT_RESPONSES',
    role: 'client',
    description: 'Resource Expression Positive - Positive Ressourcenäußerung',
    color: '#66BB6A'
  },
  'CL-RE-NE': {
    display: 'Ressource Negativ',
    shortDisplay: 'RE-',
    category: 'CLIENT_RESPONSES',
    role: 'client',
    description: 'Resource Expression Negative - Negative Ressourcenäußerung',
    color: '#EF5350'
  },
  'CL-PE-EM': {
    display: 'Problem Emotional',
    shortDisplay: 'PE-EM',
    category: 'CLIENT_RESPONSES',
    role: 'client',
    description: 'Problem Expression Emotional - Emotionale Problemäußerung',
    color: '#EC407A'
  },
  'CL-PE-CO': {
    display: 'Problem Kognitiv',
    shortDisplay: 'PE-CO',
    category: 'CLIENT_RESPONSES',
    role: 'client',
    description: 'Problem Expression Cognitive - Kognitive Problemäußerung',
    color: '#5C6BC0'
  },

  // Meta Communication
  'META-OR': {
    display: 'Organisatorisch',
    shortDisplay: 'OR',
    category: 'META',
    role: 'both',
    description: 'Organizational - Organisatorische Meta-Kommunikation',
    color: '#607D8B'
  },
  'META-PR': {
    display: 'Prozess',
    shortDisplay: 'PR',
    category: 'META',
    role: 'both',
    description: 'Process - Prozessbezogene Meta-Kommunikation',
    color: '#78909C'
  },
  'META-RE': {
    display: 'Relational',
    shortDisplay: 'RE',
    category: 'META',
    role: 'both',
    description: 'Relational - Beziehungsbezogene Meta-Kommunikation',
    color: '#90A4AE'
  }
};

/**
 * Role-specific label colors
 */
export const ROLE_COLORS = {
  counselor: '#5d7a4a',  // Primary green (from theme)
  client: '#757575',     // Secondary grey
  both: '#607D8B'        // Blue grey for meta
};

/**
 * Get label information by label key
 * @param {string} label - The label key (e.g., 'CO-IF-AC')
 * @returns {Object|null} Label info or null if not found
 */
export function getLabelInfo(label) {
  return LABEL_DEFINITIONS[label] || null;
}

/**
 * Get display name for a label
 * @param {string} label - The label key
 * @param {boolean} short - Whether to return short display name
 * @returns {string} Display name or original label if not found
 */
export function getLabelDisplay(label, short = false) {
  const info = getLabelInfo(label);
  if (!info) return label;
  return short ? info.shortDisplay : info.display;
}

/**
 * Get color for a label
 * @param {string} label - The label key
 * @param {boolean} useRoleColor - Whether to use role-based color instead
 * @returns {string} Color hex code
 */
export function getLabelColor(label, useRoleColor = false) {
  const info = getLabelInfo(label);
  if (!info) return '#9E9E9E'; // Default grey

  if (useRoleColor) {
    return ROLE_COLORS[info.role] || '#9E9E9E';
  }

  return info.color;
}

/**
 * Get all labels for a specific category
 * @param {string} categoryKey - The category key
 * @returns {Array<string>} Array of label keys
 */
export function getLabelsByCategory(categoryKey) {
  const category = LABEL_CATEGORIES[categoryKey];
  return category ? category.labels : [];
}

/**
 * Get all labels for a specific role
 * @param {string} role - The role ('counselor', 'client', 'both')
 * @returns {Array<string>} Array of label keys
 */
export function getLabelsByRole(role) {
  return Object.keys(LABEL_DEFINITIONS).filter(
    label => LABEL_DEFINITIONS[label].role === role || LABEL_DEFINITIONS[label].role === 'both'
  );
}

/**
 * Check if a label belongs to a category
 * @param {string} label - The label key
 * @param {string} categoryKey - The category key
 * @returns {boolean} True if label belongs to category
 */
export function isLabelInCategory(label, categoryKey) {
  const category = LABEL_CATEGORIES[categoryKey];
  return category ? category.labels.includes(label) : false;
}

/**
 * Get category info for a label
 * @param {string} label - The label key
 * @returns {Object|null} Category info or null if not found
 */
export function getCategoryForLabel(label) {
  const info = getLabelInfo(label);
  if (!info || !info.category) return null;
  return LABEL_CATEGORIES[info.category] || null;
}

/**
 * Group labels by category
 * @returns {Object} Object with category keys and arrays of labels
 */
export function getLabelsGroupedByCategory() {
  const grouped = {};
  for (const [categoryKey, category] of Object.entries(LABEL_CATEGORIES)) {
    grouped[categoryKey] = {
      ...category,
      labels: category.labels.map(label => ({
        key: label,
        ...LABEL_DEFINITIONS[label]
      }))
    };
  }
  return grouped;
}

/**
 * Get aggregated Level 2 label from full label
 * @param {string} label - The full label key
 * @returns {string} Level 2 aggregated label
 */
export function getLevel2Label(label) {
  // Level 2 aggregation rules
  if (label.startsWith('CO-IF')) return 'CO-IF';
  if (label.startsWith('CO-BV')) return 'CO-BV';
  if (label.startsWith('CL-RE')) return 'CL-RE';
  if (label.startsWith('CL-PE')) return 'CL-PE';
  if (label.startsWith('CL-NE')) return 'CL-NE';
  if (label.startsWith('META')) return 'META';
  return label;
}

/**
 * Check if label is a Level 2 aggregated label
 * @param {string} label - The label key
 * @returns {boolean} True if Level 2 label
 */
export function isLevel2Label(label) {
  const level2Labels = ['CO-IF', 'CO-BV', 'CL-RE', 'CL-PE', 'CL-NE', 'META'];
  return level2Labels.includes(label);
}

/**
 * Composable for label utilities
 * @returns {Object} Label utility functions
 */
export function useOnCoCoLabels() {
  return {
    // Constants
    LABEL_CATEGORIES,
    LABEL_DEFINITIONS,
    ROLE_COLORS,

    // Functions
    getLabelInfo,
    getLabelDisplay,
    getLabelColor,
    getLabelsByCategory,
    getLabelsByRole,
    isLabelInCategory,
    getCategoryForLabel,
    getLabelsGroupedByCategory,
    getLevel2Label,
    isLevel2Label
  };
}
