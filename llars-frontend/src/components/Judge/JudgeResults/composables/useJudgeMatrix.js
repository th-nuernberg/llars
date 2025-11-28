/**
 * Judge Matrix Composable
 *
 * Handles win matrix display and calculations.
 * Extracted from JudgeResults.vue for better maintainability.
 */

export function useJudgeMatrix(resultsRef) {
  const getMatrixValue = (pillarA, pillarB) => {
    if (pillarA === pillarB) return '-';
    if (!resultsRef.value?.win_matrix) return '0';

    const key = `${pillarA}_vs_${pillarB}`;
    return resultsRef.value.win_matrix[key] || 0;
  };

  const getMatrixCellClass = (pillarA, pillarB) => {
    if (pillarA === pillarB) return 'diagonal-cell';
    return '';
  };

  const getMatrixCellStyle = (pillarA, pillarB) => {
    if (pillarA === pillarB) return {};

    const value = getMatrixValue(pillarA, pillarB);
    const maxValue = Math.max(
      ...Object.values(resultsRef.value?.win_matrix || {})
    );

    if (maxValue === 0) return {};

    const intensity = value / maxValue;
    const hue = 120; // Green hue
    const saturation = 60;
    const lightness = 90 - (intensity * 40); // Lighter = less wins

    return {
      backgroundColor: `hsl(${hue}, ${saturation}%, ${lightness}%)`,
      fontWeight: intensity > 0.5 ? 'bold' : 'normal'
    };
  };

  return {
    getMatrixValue,
    getMatrixCellClass,
    getMatrixCellStyle
  };
}
