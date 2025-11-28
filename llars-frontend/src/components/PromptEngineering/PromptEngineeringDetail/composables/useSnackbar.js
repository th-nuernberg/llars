/**
 * Snackbar Composable
 *
 * Simple snackbar/toast notification utility.
 * Extracted from PromptEngineeringDetail.vue for better maintainability.
 */

import { ref } from 'vue';

export function useSnackbar() {
  const showSnackbar = ref(false);
  const snackbarMessage = ref('');

  const showSnackbarMessage = (message) => {
    snackbarMessage.value = message;
    showSnackbar.value = true;

    // Reset visibility after animation duration
    setTimeout(() => {
      showSnackbar.value = false;
    }, 3000);
  };

  return {
    showSnackbar,
    snackbarMessage,
    showSnackbarMessage
  };
}
