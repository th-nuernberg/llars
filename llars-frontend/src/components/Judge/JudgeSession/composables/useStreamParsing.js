/**
 * Stream Parsing Composable
 *
 * Handles parsing of LLM stream content for structured display.
 */

import { computed } from 'vue';
import { SCORE_CRITERIA, STEP_DEFINITIONS } from './useSessionConstants';

export function useStreamParsing(state) {
  const { llmStreamContent, workerStreams, isStreaming } = state;

  // Parse stream content incrementally - extracts partial data while streaming
  const parsedStreamJson = computed(() => {
    if (!llmStreamContent.value) return null;

    const content = llmStreamContent.value.trim();
    const result = {
      winner: null,
      confidence: null,
      scores: { A: {}, B: {} },
      final_justification: null,
      criteria_scores: null
    };

    // Try to parse complete JSON first
    try {
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        if (parsed.winner || parsed.criteria_scores || parsed.confidence || parsed.scores) {
          // Convert scores format if needed
          if (parsed.scores) {
            result.scores = parsed.scores;
            // Also build criteria_scores for compatibility
            result.criteria_scores = {};
            for (const criterion of SCORE_CRITERIA) {
              if (parsed.scores.A?.[criterion.key] !== undefined || parsed.scores.B?.[criterion.key] !== undefined) {
                result.criteria_scores[criterion.key] = {
                  score_a: parsed.scores.A?.[criterion.key] || 0,
                  score_b: parsed.scores.B?.[criterion.key] || 0
                };
              }
            }
          }
          if (parsed.criteria_scores) {
            result.criteria_scores = parsed.criteria_scores;
          }
          result.winner = parsed.winner || null;
          result.confidence = parsed.confidence || null;
          result.final_justification = parsed.final_justification || null;
          return result;
        }
      }
    } catch (e) {
      // JSON not complete - try incremental parsing
    }

    // Incremental parsing for partial JSON
    const winnerMatch = content.match(/"winner"\s*:\s*"([AB])"/);
    if (winnerMatch) result.winner = winnerMatch[1];

    const confMatch = content.match(/"confidence"\s*:\s*([\d.]+)/);
    if (confMatch) result.confidence = parseFloat(confMatch[1]);

    // Extract individual scores
    for (const criterion of SCORE_CRITERIA) {
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

    // Build criteria_scores from parsed scores
    if (Object.keys(result.scores.A).length > 0 || Object.keys(result.scores.B).length > 0) {
      result.criteria_scores = {};
      for (const criterion of SCORE_CRITERIA) {
        if (result.scores.A[criterion.key] !== undefined || result.scores.B[criterion.key] !== undefined) {
          result.criteria_scores[criterion.key] = {
            score_a: result.scores.A[criterion.key] || 0,
            score_b: result.scores.B[criterion.key] || 0
          };
        }
      }
    }

    // Extract final_justification
    const justMatch = content.match(/"final_justification"\s*:\s*"([^"]+)"/);
    if (justMatch) result.final_justification = justMatch[1];

    // Only return if we found something
    if (result.winner || result.confidence || Object.keys(result.scores.A).length > 0) {
      return result;
    }

    return null;
  });

  // Parse stream content for Chain of Thought steps incrementally
  const parsedStreamSteps = computed(() => {
    if (!llmStreamContent.value) return [];

    const content = llmStreamContent.value;
    const steps = [];

    for (const [stepKey, stepDef] of Object.entries(STEP_DEFINITIONS)) {
      const stepPattern = new RegExp(`"${stepKey}"\\s*:\\s*"`, 'm');
      const stepMatch = content.match(stepPattern);

      if (stepMatch) {
        const startIdx = content.indexOf(stepMatch[0]) + stepMatch[0].length;
        let endIdx = startIdx;
        let escaped = false;
        let stepContent = '';

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
            endIdx = i;
            break;
          } else {
            stepContent += char;
          }
          endIdx = i;
        }

        const isStepStreaming = endIdx === content.length - 1 && content[endIdx] !== '"';

        steps.push({
          key: stepKey,
          title: stepDef.title,
          icon: stepDef.icon,
          content: stepContent,
          isStreaming: isStepStreaming
        });
      }
    }

    return steps;
  });

  // Get step by key from parsed steps
  const getStepByKey = (stepKey) => {
    return parsedStreamSteps.value.find(s => s.key === stepKey) || null;
  };

  // Parse worker stream content for results
  const getWorkerParsedResult = (workerId) => {
    const content = workerStreams[workerId]?.content;
    if (!content) return null;

    const result = {
      winner: null,
      confidence: null,
      scores: { A: {}, B: {} },
      final_justification: null
    };

    // Try to parse JSON
    try {
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        if (parsed.winner || parsed.confidence || parsed.scores) {
          result.winner = parsed.winner;
          result.confidence = parsed.confidence;
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
    for (const criterion of SCORE_CRITERIA) {
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

    const justMatch = content.match(/"final_justification"\s*:\s*"([^"]+)"/);
    if (justMatch) result.final_justification = justMatch[1];

    return result.winner || result.confidence || Object.keys(result.scores.A).length > 0 ? result : null;
  };

  // Get worker score for A
  const getWorkerScoreA = (workerId, criterionKey) => {
    const parsed = getWorkerParsedResult(workerId);
    return parsed?.scores?.A?.[criterionKey] || 0;
  };

  // Get worker score for B
  const getWorkerScoreB = (workerId, criterionKey) => {
    const parsed = getWorkerParsedResult(workerId);
    return parsed?.scores?.B?.[criterionKey] || 0;
  };

  // Get worker analysis step by key
  const getWorkerStep = (workerId, stepKey) => {
    const content = workerStreams[workerId]?.content;
    if (!content) return null;

    const stepPattern = new RegExp(`"${stepKey}"\\s*:\\s*"`, 'm');
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

      return {
        key: stepKey,
        content: stepContent,
        isStreaming: isStepStreaming
      };
    }

    return null;
  };

  return {
    parsedStreamJson,
    parsedStreamSteps,
    getStepByKey,
    getWorkerParsedResult,
    getWorkerScoreA,
    getWorkerScoreB,
    getWorkerStep
  };
}
