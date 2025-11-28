/**
 * Stream Parser Composable
 *
 * Parses streaming JSON content from LLM judge responses.
 * Handles incremental parsing for live updates.
 * Extracted from WorkerLane.vue for better maintainability.
 */

import { computed } from 'vue';
import { CRITERIA_CONFIG, STEP_CONFIG } from './useWorkerState';

export function useStreamParser(props) {
  // Parse stream content for results
  const parsedResult = computed(() => {
    if (!props.streamContent) return null;

    const content = props.streamContent.trim();
    const result = {
      winner: null,
      confidence: null,
      criteria_scores: null,
      scores: { A: {}, B: {} },
      final_justification: null
    };

    // Try to parse JSON
    try {
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        if (parsed.winner || parsed.criteria_scores || parsed.confidence || parsed.scores) {
          result.winner = parsed.winner;
          result.confidence = parsed.confidence;
          result.criteria_scores = parsed.criteria_scores;
          result.final_justification = parsed.final_justification;
          if (parsed.scores) {
            result.scores = parsed.scores;
          }
          return result;
        }
      }
    } catch (e) {
      // JSON not complete - try incremental parsing
    }

    // Incremental parsing
    const winnerMatch = content.match(/"winner"\s*:\s*"([AB])"/);
    if (winnerMatch) result.winner = winnerMatch[1];

    const confMatch = content.match(/"confidence"\s*:\s*([\d.]+)/);
    if (confMatch) result.confidence = parseFloat(confMatch[1]);

    // Extract individual scores
    for (const criterion of CRITERIA_CONFIG) {
      const scoreAPattern = new RegExp(`"A"[\\s\\S]*?"${criterion.key}"\\s*:\\s*(\\d+)`, 'm');
      const scoreAMatch = content.match(scoreAPattern);
      if (scoreAMatch) {
        result.scores.A[criterion.key] = parseInt(scoreAMatch[1]);
      }

      const scoreBPattern = new RegExp(`"B"[\\s\\S]*?"${criterion.key}"\\s*:\\s*(\\d+)`, 'm');
      const scoreBMatch = content.match(scoreBPattern);
      if (scoreBMatch) {
        result.scores.B[criterion.key] = parseInt(scoreBMatch[1]);
      }
    }

    // Extract final_justification
    const justMatch = content.match(/"final_justification"\s*:\s*"([^"]+)"/);
    if (justMatch) result.final_justification = justMatch[1];

    return result.winner || result.confidence || Object.keys(result.scores.A).length > 0 ? result : null;
  });

  // Parse stream steps
  const parsedStreamSteps = computed(() => {
    if (!props.streamContent) return [];

    const content = props.streamContent;
    const steps = [];

    for (const step of STEP_CONFIG) {
      const stepPattern = new RegExp(`"${step.key}"\\s*:\\s*"`, 'm');
      const stepMatch = content.match(stepPattern);

      if (stepMatch) {
        const startIdx = content.indexOf(stepMatch[0]) + stepMatch[0].length;
        let stepContent = '';
        let escaped = false;

        for (let i = startIdx; i < content.length; i++) {
          const char = content[i];
          if (escaped) {
            if (char === 'n') stepContent += '\n';
            else if (char === '"') stepContent += '"';
            else if (char === '\\') stepContent += '\\';
            else stepContent += char;
            escaped = false;
          } else if (char === '\\') {
            escaped = true;
          } else if (char === '"') {
            break;
          } else {
            stepContent += char;
          }
        }

        const isStepStreaming = !content.slice(startIdx).includes('"');

        steps.push({
          key: step.key,
          title: step.title,
          content: stepContent,
          isStreaming: isStepStreaming
        });
      }
    }

    return steps;
  });

  const getStepByKey = (stepKey) => {
    return parsedStreamSteps.value.find(s => s.key === stepKey);
  };

  const completedSteps = computed(() => {
    return parsedStreamSteps.value.filter(s => !s.isStreaming).length;
  });

  const currentActiveStep = computed(() => {
    return parsedStreamSteps.value.find(s => s.isStreaming);
  });

  // Score helpers
  const getScoreA = (criterionKey) => {
    return parsedResult.value?.scores?.A?.[criterionKey] ||
           parsedResult.value?.criteria_scores?.[criterionKey]?.score_a ||
           0;
  };

  const getScoreB = (criterionKey) => {
    return parsedResult.value?.scores?.B?.[criterionKey] ||
           parsedResult.value?.criteria_scores?.[criterionKey]?.score_b ||
           0;
  };

  const totalScoreA = computed(() => {
    return CRITERIA_CONFIG.reduce((sum, c) => sum + getScoreA(c.key), 0);
  });

  const totalScoreB = computed(() => {
    return CRITERIA_CONFIG.reduce((sum, c) => sum + getScoreB(c.key), 0);
  });

  const scoreDiff = computed(() => totalScoreA.value - totalScoreB.value);

  const dominanceA = computed(() => {
    const total = totalScoreA.value + totalScoreB.value;
    return total > 0 ? (totalScoreA.value / total * 100) : 50;
  });

  const dominanceB = computed(() => {
    const total = totalScoreA.value + totalScoreB.value;
    return total > 0 ? (totalScoreB.value / total * 100) : 50;
  });

  const getDiffClass = (criterionKey) => {
    const diff = getScoreA(criterionKey) - getScoreB(criterionKey);
    if (diff > 0) return 'diff-positive';
    if (diff < 0) return 'diff-negative';
    return 'diff-neutral';
  };

  const getDiffText = (criterionKey) => {
    const diff = getScoreA(criterionKey) - getScoreB(criterionKey);
    if (diff > 0) return `+${diff}`;
    if (diff < 0) return `${diff}`;
    return '0';
  };

  return {
    // Parsed data
    parsedResult,
    parsedStreamSteps,

    // Step helpers
    getStepByKey,
    completedSteps,
    currentActiveStep,

    // Score helpers
    getScoreA,
    getScoreB,
    totalScoreA,
    totalScoreB,
    scoreDiff,
    dominanceA,
    dominanceB,
    getDiffClass,
    getDiffText
  };
}
