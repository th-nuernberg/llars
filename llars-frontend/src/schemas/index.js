/**
 * LLARS Evaluation Schemas
 *
 * SCHEMA GROUND TRUTH:
 * -------------------
 * Dieses Modul exportiert die einheitlichen Evaluation-Schemas für LLARS.
 *
 * Synchron mit Backend:
 * - Backend: app/schemas/evaluation_data_schemas.py
 * - Frontend: llars-frontend/src/schemas/evaluationSchemas.js
 *
 * Verwendung:
 *   import { EvaluationType, validateEvaluationData } from '@/schemas'
 *
 * Oder spezifisch:
 *   import { createDefaultRankingBuckets } from '@/schemas/evaluationSchemas'
 *
 * Dokumentation: .claude/plans/evaluation-data-schemas.md
 */

export {
  // Enums
  SchemaVersion,
  EvaluationType,
  SourceType,
  ContentType,
  RankingMode,
  LabelingMode,
  FUNCTION_TYPE_MAP,
  EVALUATION_TYPE_TO_ID,

  // Factory functions
  createDefaultRankingBuckets,
  createDefaultScale,
  createDefaultRatingDimensions,
  createDefaultAuthenticityOptions,
  createSimpleRankingConfig,
  createRatingConfig,

  // Validation
  validateEvaluationData,

  // Helpers
  isMultiGroupRanking,
  getRankingGroups,
  groupItemsByGroup,
  getLocalizedText
} from './evaluationSchemas'

// Default export
export { default } from './evaluationSchemas'
